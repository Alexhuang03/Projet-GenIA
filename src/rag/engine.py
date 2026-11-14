"""
Niveau 1 : RAG (Retrieval-Augmented Generation)

1. Recherche des RAG_TOP_K passages les plus pertinents (retriever.py).
2. Injection des passages dans le prompt, chacun étiqueté par son fichier source.
3. Génération avec deux règles imposées au LLM :
   - citer la source de chaque information au format [Source: fichier.md] ;
   - si les passages ne contiennent pas la réponse, répondre par une phrase d'abstention fixe.
4. Contrôle a posteriori des citations : on sépare celles qui renvoient bien à un passage
   fourni de celles inventées par le modèle (comptées comme erreurs dans eval.py).
"""
import re
from typing import Any, Dict, List

from src.llm_client import UnifiedLLMClient
from src.metrics import is_abstention
from src.rag.retriever import Retriever
from src.tracker import ExecutionTrace

ABSTENTION_SENTENCE = "Je ne dispose pas de cette information dans les documents officiels à ma disposition."

SYSTEM_PROMPT_RAG = f"""Tu es un conseiller spécialisé dans les aides et démarches étudiantes en France (bourses CROUS, logement, APL, aides d'urgence, mobilité, restauration, santé).
Tu réponds en français, UNIQUEMENT à partir des extraits documentaires fournis dans le message.

Règles impératives :
1. Chaque information (montant, condition, date, barème) doit être suivie de sa source au format exact [Source: nom_du_fichier.md], en reprenant le nom de fichier indiqué dans l'en-tête de l'extrait.
2. Si les extraits ne permettent pas de répondre à la question, réponds exactement et uniquement : « {ABSTENTION_SENTENCE} » Ne complète pas avec tes connaissances générales.
3. N'invente aucun chiffre, aucune règle, aucun nom de dispositif absent des extraits.
4. Si la demande est hors du champ des aides étudiantes, illégale ou trop vague, ne l'exécute pas : explique brièvement ce que tu peux faire ou demande une précision.
5. Sois concis : quelques phrases suffisent."""

CITATION_RE = re.compile(r"\[\s*Source\s*:\s*([^\]]+?)\s*\]", re.IGNORECASE)


def extract_citations(text: str) -> List[str]:
    """Renvoie les noms de fichiers cités (une citation peut en lister plusieurs, séparés par , ou ;)."""
    cited: List[str] = []
    for group in CITATION_RE.findall(text):
        for name in re.split(r"[;,]", group):
            name = name.strip()
            if name and name not in cited:
                cited.append(name)
    return cited


class RAGEngine:
    def __init__(self, client: UnifiedLLMClient, retriever: Retriever):
        self.client = client
        self.retriever = retriever

    def build_prompt(self, query: str, retrieved) -> str:
        blocks = [
            f"--- Extrait {r.rank} | Source: {r.chunk.doc_name} ---\n{r.chunk.content}"
            for r in retrieved
        ]
        return ("Extraits documentaires :\n\n" + "\n\n".join(blocks)
                + f"\n\nQuestion de l'étudiant : {query}")

    def process(self, query: str) -> Dict[str, Any]:
        trace = ExecutionTrace(level=1, query=query, model=f"{self.client.provider}:{self.client.model}")

        retrieved = self.retriever.retrieve(query)
        retrieved_docs = list(dict.fromkeys(r.chunk.doc_name for r in retrieved))
        trace.add_step("retrieval", {
            **self.retriever.describe(),
            "results": [{"rank": r.rank, "chunk_id": r.chunk.chunk_id, "score": round(r.score, 4)}
                        for r in retrieved],
        })

        prompt = self.build_prompt(query, retrieved)
        resp = self.client.generate(prompt=prompt, system_prompt=SYSTEM_PROMPT_RAG)

        cited = extract_citations(resp.content)
        valid = [c for c in cited if c in retrieved_docs]
        invalid = [c for c in cited if c not in retrieved_docs]
        abstained = is_abstention(resp.content)
        trace.sources = valid
        trace.add_step("generation", {
            "prompt_tokens": resp.prompt_tokens,
            "completion_tokens": resp.completion_tokens,
            "citations_valides": valid,
            "citations_invalides": invalid,
            "abstention": abstained,
        })
        trace.finalize(response=resp.content, status="ABSTENTION" if abstained else "SUCCESS",
                       prompt_tokens=resp.prompt_tokens, completion_tokens=resp.completion_tokens)

        return {
            "level": 1,
            "query": query,
            "response": resp.content,
            "abstained": abstained,
            "retrieved_docs": retrieved_docs,
            "retrieved_chunks": [{"rank": r.rank, "chunk_id": r.chunk.chunk_id, "doc": r.chunk.doc_name,
                                  "section": r.chunk.section_title, "content": r.chunk.content,
                                  "score": r.score} for r in retrieved],
            "citations": cited,
            "citations_valides": valid,
            "citations_invalides": invalid,
            "trace": trace.to_dict(),
        }
