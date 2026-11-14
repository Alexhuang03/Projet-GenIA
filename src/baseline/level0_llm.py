"""
Niveau 0 : LLM Seul (Baseline de référence)
Un prompt soigné définissant l'assistant étudiant, mais SANS accès aux documents officiels (pas de RAG)
et SANS outils d'action ou de calcul (pas d'agent).
Référence à battre pour prouver l'apport du RAG et de l'Agent.
"""
from typing import Dict, Any
from src.llm_client import UnifiedLLMClient
from src.tracker import ExecutionTrace


SYSTEM_PROMPT_LEVEL_0 = """Tu es un assistant virtuel généraliste d'orientation et de vie étudiante en France.
Ton objectif est d'aider les étudiants dans leurs questionnements du quotidien (bourses, logement, budget, démarches).
Réponds avec bienveillance, clarté et concision. 
Note : Tu réponds uniquement avec tes connaissances générales, sans base documentaire externe ni outil de calcul."""


class Level0LLM:
    def __init__(self, client: UnifiedLLMClient):
        self.client = client

    def process(self, query: str) -> Dict[str, Any]:
        trace = ExecutionTrace(level=0, query=query, model=f"{self.client.provider}:{self.client.model}")
        trace.add_step("prompt_preparation", {"system_prompt": SYSTEM_PROMPT_LEVEL_0})
        
        # Appel LLM pur
        response = self.client.generate(prompt=query, system_prompt=SYSTEM_PROMPT_LEVEL_0)
        
        trace.add_step("llm_generation", {
            "model": self.client.model,
            "prompt_tokens": response.prompt_tokens,
            "completion_tokens": response.completion_tokens
        })
        
        trace.finalize(
            response=response.content,
            status="SUCCESS",
            prompt_tokens=response.prompt_tokens,
            completion_tokens=response.completion_tokens
        )
        
        return {
            "level": 0,
            "query": query,
            "response": response.content,
            "sources": [],
            "trace": trace.to_dict()
        }
