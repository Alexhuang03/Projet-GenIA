"""
Niveau 1 : RAG (Retrieval-Augmented Generation)
Recherche documentaire hybride (Dense + BM25), injection du contexte,
citation obligatoire des sources et abstention formelle si les informations sont absentes.
"""
from typing import Dict, Any, List
from src.rag.retriever import HybridRetriever
from src.llm_client import UnifiedLLMClient
from src.tracker import ExecutionTrace


SYSTEM_PROMPT_RAG = """Tu es un conseiller expert des aides et démarches étudiantes en France.
Tu réponds aux questions des étudiants STRICTEMENT en t'appuyant sur les extraits documentaires fournis ci-dessous.

Règles impératives :
1. Chaque information ou chiffre clé doit citer son document source entre crochets, sous la forme : [Source: nom_du_fichier.md].
2. Si le contexte documentaire fourni ne contient pas la réponse exacte ou s'il est insuffisant, tu DOIS t'abstenir en déclarant explicitement :
« D'après les documents officiels disponibles, je ne dispose pas de cette information. »
3. N'invente aucune règle, aucun chiffre, aucun barème non présent dans les extraits."""


class RAGEngine:
    def __init__(self, client: UnifiedLLMClient, retriever: HybridRetriever):
        self.client = client
        self.retriever = retriever

    def process(self, query: str) -> Dict[str, Any]:
        trace = ExecutionTrace(level=1, query=query)
        trace.add_step("query_received", {"query": query})
        
        # 1. Étape de recherche documentaire hybride
        top_chunks, should_abstain = self.retriever.retrieve(query)
        sources_found = list({chunk.doc_name for chunk, _ in top_chunks})
        trace.sources = sources_found
        
        trace.add_step("retrieval", {
            "top_chunks": [{"chunk_id": c.chunk_id, "doc": c.doc_name, "score": round(s, 4)} for c, s in top_chunks],
            "should_abstain": should_abstain
        })
        
        # 2. Gestion de l'abstention si hors corpus
        if should_abstain:
            abstention_message = (
                "D'après les documents officiels du corpus, je ne dispose pas des informations nécessaires "
                "pour répondre à votre demande. Aucune mention correspondante n'a été trouvée dans les règlements."
            )
            trace.finalize(
                response=abstention_message,
                status="ABSTENTION",
                prompt_tokens=10,
                completion_tokens=25
            )
            return {
                "level": 1,
                "query": query,
                "response": abstention_message,
                "sources": [],
                "abstained": True,
                "retrieved_chunks": [c.content for c, _ in top_chunks],
                "trace": trace.to_dict()
            }
        
        # 3. Construction du prompt augmenté
        context_blocks = []
        for chunk, score in top_chunks:
            context_blocks.append(f"--- Document: {chunk.doc_name} | Section: {chunk.section_title} (score: {score:.3f}) ---\n{chunk.content}")
        
        context_text = "\n\n".join(context_blocks)
        augmented_prompt = f"""Contexte documentaire fourni :
{context_text}

Question de l'étudiant : {query}

Rappel : Réponds précisément en citant la source [Source: nom_du_fichier.md]."""
        
        trace.add_step("prompt_augmentation", {
            "num_chunks_injected": len(top_chunks),
            "sources": sources_found
        })
        
        # 4. Génération LLM avec grounding
        llm_resp = self.client.generate(prompt=augmented_prompt, system_prompt=SYSTEM_PROMPT_RAG)
        
        trace.finalize(
            response=llm_resp.content,
            status="SUCCESS",
            prompt_tokens=llm_resp.prompt_tokens,
            completion_tokens=llm_resp.completion_tokens
        )
        
        return {
            "level": 1,
            "query": query,
            "response": llm_resp.content,
            "sources": sources_found,
            "abstained": False,
            "retrieved_chunks": [c.content for c, _ in top_chunks],
            "trace": trace.to_dict()
        }
