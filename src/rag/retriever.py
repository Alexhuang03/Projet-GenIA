"""
Retriever Hybride (Dense TF-IDF + BM25) avec vérification thématique et lexicale (Groundedness)
Détection fiable de l'abstention sur les requêtes hors domaine.
"""
import math
import re
from typing import List, Tuple, Dict, Any, Set
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from src.rag.chunking import DocumentChunk, DocumentChunker
from src.config import CORPUS_DIR, RAG_TOP_K, RAG_SIMILARITY_THRESHOLD

FRENCH_STOPWORDS: Set[str] = {
    "le", "la", "les", "un", "une", "des", "du", "de", "d", "en", "pour", "par",
    "dans", "sur", "sous", "vers", "chez", "avec", "sans", "est", "sont", "ete",
    "etre", "avoir", "a", "au", "aux", "ce", "cet", "cette", "ces", "qui", "que",
    "quoi", "dont", "ou", "mais", "donc", "or", "ni", "car", "quel", "quelle",
    "quels", "quelles", "comment", "combien", "pourquoi", "quand", "je", "tu",
    "il", "elle", "on", "nous", "vous", "ils", "elles", "mon", "ma", "mes",
    "ton", "ta", "tes", "son", "sa", "ses", "notre", "nos", "votre", "vos",
    "leur", "leurs", "se", "si", "fait", "peut", "on", "tout", "tous"
}

# Concepts thématiques du domaine des aides étudiantes
STUDENT_DOMAIN_CONCEPTS: Set[str] = {
    "bourse", "bourses", "crous", "logement", "logements", "visale", "apl",
    "caf", "dse", "mobilité", "mobilite", "parcoursup", "master", "urgence",
    "fnausu", "asaa", "repas", "restauration", "transport", "transports",
    "santé", "sante", "psy", "charge", "échelon", "echelons", "échelons",
    "echelon", "cvec", "loca-pass", "locapass", "avance", "caution", "social",
    "sociale", "sociales", "résidence", "residence", "izly", "imagine", "ami"
}


class BM25Scorer:
    def __init__(self, corpus: List[str], k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus_size = len(corpus)
        self.tokenized_corpus = [self._tokenize(doc) for doc in corpus]
        self.doc_lens = [len(doc) for doc in self.tokenized_corpus]
        self.avg_doc_len = sum(self.doc_lens) / (self.corpus_size or 1)
        
        self.df: Dict[str, int] = {}
        for doc in self.tokenized_corpus:
            for term in set(doc):
                self.df[term] = self.df.get(term, 0) + 1
        
        self.idf: Dict[str, float] = {}
        for term, freq in self.df.items():
            self.idf[term] = math.log(1 + (self.corpus_size - freq + 0.5) / (freq + 0.5))

    def _tokenize(self, text: str) -> List[str]:
        tokens = re.findall(r"\b[a-zA-ZÀ-ÿ0-9_-]+\b", text.lower())
        return [t for t in tokens if t not in FRENCH_STOPWORDS and len(t) > 1]

    def get_scores(self, query: str) -> np.ndarray:
        query_tokens = self._tokenize(query)
        scores = np.zeros(self.corpus_size)
        if not query_tokens:
            return scores

        for idx, doc_tokens in enumerate(self.tokenized_corpus):
            doc_len = self.doc_lens[idx]
            token_counts: Dict[str, int] = {}
            for token in doc_tokens:
                token_counts[token] = token_counts.get(token, 0) + 1
            
            score = 0.0
            for q_term in query_tokens:
                if q_term in token_counts:
                    freq = token_counts[q_term]
                    idf = self.idf.get(q_term, 0.1)
                    denom = freq + self.k1 * (1 - self.b + self.b * (doc_len / self.avg_doc_len))
                    score += idf * (freq * (self.k1 + 1)) / (denom or 1)
            scores[idx] = score
        
        max_possible_idf = sum(self.idf.get(t, 1.0) for t in query_tokens) or 1.0
        return scores / (max_possible_idf * (self.k1 + 1))


class HybridRetriever:
    def __init__(self, top_k: int = RAG_TOP_K, threshold: float = RAG_SIMILARITY_THRESHOLD):
        self.top_k = top_k
        self.threshold = threshold
        self.chunker = DocumentChunker()
        self.chunks: List[DocumentChunk] = []
        self.tfidf_vectorizer: TfidfVectorizer = None
        self.dense_matrix = None
        self.bm25: BM25Scorer = None
        self._index_corpus()

    def _index_corpus(self):
        self.chunks = self.chunker.process_directory(CORPUS_DIR)
        texts = [c.content for c in self.chunks]
        
        if not texts:
            raise ValueError(f"Le dossier de corpus {CORPUS_DIR} est vide !")
        
        self.tfidf_vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            stop_words=list(FRENCH_STOPWORDS),
            sublinear_tf=True
        )
        self.dense_matrix = self.tfidf_vectorizer.fit_transform(texts)
        self.bm25 = BM25Scorer(texts)

    def extract_keywords(self, text: str) -> List[str]:
        tokens = re.findall(r"\b[a-zA-ZÀ-ÿ0-9_-]+\b", text.lower())
        return [t for t in tokens if t not in FRENCH_STOPWORDS and len(t) > 2]

    def is_in_domain(self, query: str) -> bool:
        """Vérifie si la requête aborde les thématiques d'aides étudiantes couvertes par le corpus."""
        tokens = set(self.extract_keywords(query))
        return len(tokens.intersection(STUDENT_DOMAIN_CONCEPTS)) > 0

    def compute_groundedness(self, query: str, top_chunks: List[DocumentChunk]) -> float:
        keywords = self.extract_keywords(query)
        if not keywords:
            return 1.0
        combined_text = " ".join(c.content.lower() for c in top_chunks)
        matched = [k for k in keywords if k in combined_text]
        return len(matched) / len(keywords)

    def retrieve(self, query: str) -> Tuple[List[Tuple[DocumentChunk, float]], bool]:
        # Score Dense
        q_vec = self.tfidf_vectorizer.transform([query])
        dense_scores = cosine_similarity(q_vec, self.dense_matrix)[0]
        
        # Score BM25
        bm25_scores = self.bm25.get_scores(query)
        
        # Score Hybride
        hybrid_scores = 0.5 * dense_scores + 0.5 * bm25_scores
        ranked_indices = np.argsort(hybrid_scores)[::-1]
        
        best_results: List[Tuple[DocumentChunk, float]] = []
        for idx in ranked_indices[:self.top_k]:
            best_results.append((self.chunks[idx], float(hybrid_scores[idx])))
        
        top_chunks = [item[0] for item in best_results]
        max_score = best_results[0][1] if best_results else 0.0
        groundedness = self.compute_groundedness(query, top_chunks)
        in_domain = self.is_in_domain(query)
        
        # Détection d'abstention : hors domaine OU score faible OU faible ancrage lexical
        should_abstain = (not in_domain) or (max_score < self.threshold) or (groundedness < 0.40)
        
        return best_results, should_abstain
