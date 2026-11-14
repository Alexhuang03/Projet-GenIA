"""
Recherche documentaire du Niveau 1, avec trois modes comparables par eval.py :
- "bm25"   : lexical (Okapi BM25, accents normalisés). Fort sur les termes exacts
             (« Loca-Pass », « 0bis », « Visale »).
- "dense"  : sémantique (embeddings bge-m3 via Ollama, similarité cosinus). Fort sur les
             reformulations (« frère à la fac » ~ « inscrit dans l'enseignement supérieur »).
- "hybrid" : fusion des deux classements par Reciprocal Rank Fusion (RRF), qui ne demande
             aucun calibrage des scores entre les deux méthodes.

Aucune liste de mots-clés « du domaine » n'est codée en dur : la décision d'abstention est
laissée au LLM (voir engine.py), et mesurée.
"""
import hashlib
import math
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np

from src.config import CORPUS_DIR, INDEX_DIR, RAG_TOP_K, RAG_RRF_K, RAG_RETRIEVER, EMBEDDING_MODEL
from src.rag.chunking import DocumentChunk, DocumentChunker

FRENCH_STOPWORDS = {
    "le", "la", "les", "un", "une", "des", "du", "de", "d", "l", "en", "pour", "par", "dans",
    "sur", "sous", "vers", "chez", "avec", "sans", "est", "sont", "etre", "avoir", "a", "au",
    "aux", "ce", "cet", "cette", "ces", "qui", "que", "qu", "quoi", "dont", "ou", "mais", "donc",
    "or", "ni", "car", "quel", "quelle", "quels", "quelles", "comment", "combien", "pourquoi",
    "quand", "je", "j", "tu", "il", "elle", "on", "nous", "vous", "ils", "elles", "mon", "ma",
    "mes", "ton", "ta", "tes", "son", "sa", "ses", "notre", "nos", "votre", "vos", "leur",
    "leurs", "se", "s", "si", "y", "peut", "tout", "tous", "et", "ne", "pas", "plus", "c", "n",
}


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.lower())
    return "".join(ch for ch in text if not unicodedata.combining(ch))


def tokenize(text: str) -> List[str]:
    tokens = re.findall(r"[a-z0-9]+", normalize(text))
    return [t for t in tokens if t not in FRENCH_STOPWORDS]


@dataclass
class RetrievedChunk:
    chunk: DocumentChunk
    score: float
    rank: int


class BM25:
    def __init__(self, docs: List[str], k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self.docs = [Counter(tokenize(d)) for d in docs]
        self.lens = [sum(c.values()) for c in self.docs]
        self.avg_len = sum(self.lens) / max(len(self.docs), 1)
        df = Counter(term for c in self.docs for term in c)
        n = len(self.docs)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}

    def scores(self, query: str) -> np.ndarray:
        q = tokenize(query)
        out = np.zeros(len(self.docs))
        for i, (counts, length) in enumerate(zip(self.docs, self.lens)):
            s = 0.0
            for term in q:
                f = counts.get(term, 0)
                if f:
                    s += self.idf[term] * f * (self.k1 + 1) / (
                        f + self.k1 * (1 - self.b + self.b * length / self.avg_len))
            out[i] = s
        return out


class DenseIndex:
    """Embeddings du corpus, mis en cache sur disque (clé = hash du contenu + modèle)."""

    def __init__(self, client, texts: List[str], model: str = EMBEDDING_MODEL):
        self.client, self.model = client, model
        key = hashlib.sha256((model + "\x00".join(texts)).encode("utf-8")).hexdigest()[:16]
        cache = INDEX_DIR / f"emb_{model.replace(':', '_')}_{key}.npy"
        if cache.exists():
            self.matrix = np.load(cache)
        else:
            self.matrix = self._normalize(np.array(client.embed(texts, model=model), dtype=np.float32))
            np.save(cache, self.matrix)

    @staticmethod
    def _normalize(m: np.ndarray) -> np.ndarray:
        return m / np.clip(np.linalg.norm(m, axis=-1, keepdims=True), 1e-12, None)

    def scores(self, query: str) -> np.ndarray:
        q = self._normalize(np.array(self.client.embed([query], model=self.model)[0], dtype=np.float32))
        return self.matrix @ q


class Retriever:
    def __init__(self, client=None, mode: str = RAG_RETRIEVER, top_k: int = RAG_TOP_K):
        if mode not in ("bm25", "dense", "hybrid"):
            raise ValueError(f"Mode de recherche inconnu : {mode}")
        self.mode, self.top_k = mode, top_k
        self.chunks = DocumentChunker().process_directory(CORPUS_DIR)
        if not self.chunks:
            raise ValueError(f"Corpus vide : {CORPUS_DIR}")
        texts = [c.content for c in self.chunks]
        self.bm25 = BM25(texts) if mode in ("bm25", "hybrid") else None
        self.dense: Optional[DenseIndex] = None
        if mode in ("dense", "hybrid"):
            if client is None:
                raise ValueError("Le mode dense/hybride a besoin d'un client pour les embeddings")
            self.dense = DenseIndex(client, texts)

    def retrieve(self, query: str, top_k: Optional[int] = None) -> List[RetrievedChunk]:
        k = top_k or self.top_k
        if self.mode == "bm25":
            final = self.bm25.scores(query)
        elif self.mode == "dense":
            final = self.dense.scores(query)
        else:
            # RRF : score = somme des 1 / (k_rrf + rang) sur les deux classements
            final = np.zeros(len(self.chunks))
            for s in (self.bm25.scores(query), self.dense.scores(query)):
                ranks = np.empty(len(s), dtype=int)
                ranks[np.argsort(-s, kind="stable")] = np.arange(1, len(s) + 1)
                final += 1.0 / (RAG_RRF_K + ranks)
        order = np.argsort(-final, kind="stable")[:k]
        return [RetrievedChunk(self.chunks[i], float(final[i]), r + 1) for r, i in enumerate(order)]

    def describe(self) -> Dict[str, str]:
        return {"mode": self.mode, "top_k": str(self.top_k), "n_chunks": str(len(self.chunks)),
                "embedding_model": self.dense.model if self.dense else "-"}
