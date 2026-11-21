"""
Niveau 2 : agent outillé, boucle ReAct ÉCRITE SANS FRAMEWORK.

À chaque tour, le LLM voit la conversation et les observations des outils, puis :
- soit il appelle un ou plusieurs outils (appel d'outils natif d'Ollama) ;
- soit il donne sa réponse finale.

Garde-fous codés (pas laissés au modèle) :
- une seule action par tour, et pas d'abstention sans recherche préalable ;
- boucle bornée : AGENT_MAX_STEPS appels LLM et AGENT_MAX_TOKENS tokens au plus ;
- erreurs d'outils renvoyées au modèle comme observations, pour qu'il se corrige ;
- tout outil WRITE met la boucle en pause (statut WAITING_CONFIRMATION) ; elle ne reprend
  qu'avec resume(session, approved), et l'outil n'est exécuté que si approved est vrai.
"""
from typing import Any, Dict, Optional

from src.agent.common import (AGENT_RULES, AgentSession, build_result, confirmation_message,
                              is_write, tool_message)
from src.agent.tools import TOOL_SCHEMAS, ToolExecutor
from src.config import AGENT_MAX_STEPS, AGENT_MAX_TOKENS, LLM_TEMPERATURE, LLM_SEED
from src.llm_client import UnifiedLLMClient
from src.metrics import is_abstention
from src.rag.retriever import Retriever
from src.tracker import ExecutionTrace

class ReActAgent:
    level = 2

    def __init__(self, client: UnifiedLLMClient, retriever: Retriever,
                 max_steps: int = AGENT_MAX_STEPS, max_tokens: int = AGENT_MAX_TOKENS):
        self.client, self.retriever = client, retriever
        self.max_steps, self.max_tokens = max_steps, max_tokens

    def process(self, query: str, temperature: float = LLM_TEMPERATURE, seed: int = LLM_SEED) -> Dict[str, Any]:
        session = AgentSession(
            query=query, executor=ToolExecutor(self.retriever), level=self.level,
            trace=ExecutionTrace(level=self.level, query=query, model=f"{self.client.provider}:{self.client.model}"))
        session.extra.update(temperature=temperature, seed=seed)
        session.messages = [{"role": "system", "content": AGENT_RULES}, {"role": "user", "content": query}]
        return self._run(session)

    def resume(self, session: AgentSession, approved: bool) -> Dict[str, Any]:
        call, session.pending = session.pending, None
        if call is None:
            raise ValueError("Aucune action en attente de confirmation.")
        session.confirmations.append({"tool": call["name"], "approved": approved})
        session.trace.add_step("confirmation", {"tool": call["name"], "approved": approved})
        if approved:
            result = session.executor.execute(call["name"], call["arguments"], confirmed=True)
        else:
            result = {"refus": "L'étudiant a refusé cette action. Ne la relance pas ; termine ta réponse."}
        session.trace.add_step("tool_call", {"tool": call["name"], "arguments": call["arguments"], "result": result})
        session.messages.append(tool_message(call["name"], result))
        return self._run(session)

    def _run(self, session: AgentSession) -> Dict[str, Any]:
        temperature, seed = session.extra["temperature"], session.extra["seed"]
        while session.steps < self.max_steps:
            if session.total_tokens > self.max_tokens:
                return build_result(session, "Budget de tokens dépassé : arrêt de l'agent.", "BUDGET_EXCEEDED")
            session.steps += 1
            resp = self.client.chat(session.messages, tools=TOOL_SCHEMAS, temperature=temperature, seed=seed)
            session.count(resp)
            session.trace.add_step("llm", {"step": session.steps, "prompt_tokens": resp.prompt_tokens,
                                           "completion_tokens": resp.completion_tokens,
                                           "tool_calls": resp.tool_calls, "content": resp.content[:500]})

            if not resp.tool_calls:
                text = resp.content.strip()
                # Garde-fou : une abstention n'est recevable qu'après une recherche. Si le modèle n'a pas
                # cherché, le code lance la recherche sur la question et lui redonne la main.
                if is_abstention(text) and not session.executor.search_docs:
                    call = {"name": "rechercher_documents", "arguments": {"question": session.query}}
                    result = session.executor.execute(call["name"], call["arguments"])
                    session.trace.add_step("recherche_forcee", {"raison": "abstention sans recherche", "tool": call["name"]})
                    session.messages.append({"role": "assistant", "content": "", "tool_calls": [{"function": call}]})
                    session.messages.append(tool_message(call["name"], result))
                    continue
                session.messages.append({"role": "assistant", "content": resp.content})
                return build_result(session, text, "SUCCESS")

            # ReAct strict : une seule action par tour. Le modèle voit son résultat avant la suivante,
            # ce qui l'empêche d'enchaîner des outils avec des valeurs intermédiaires devinées.
            call = resp.tool_calls[0]
            if len(resp.tool_calls) > 1:
                session.trace.add_step("ignored_calls", {"calls": resp.tool_calls[1:]})
            session.messages.append({"role": "assistant", "content": resp.content,
                                     "tool_calls": [{"function": call}]})
            if is_write(call["name"]):
                error = session.executor.precheck(call["name"], call["arguments"])
                if not error:
                    session.pending = call
                    session.trace.add_step("confirmation_requested", call)
                    return build_result(session, confirmation_message(call), "WAITING_CONFIRMATION")
                result = {"erreur": error}
                session.trace.add_step("tool_call", {"tool": call["name"], "arguments": call["arguments"],
                                                     "result": result, "stage": "precheck"})
            else:
                result = session.executor.execute(call["name"], call["arguments"])
                session.trace.add_step("tool_call", {"tool": call["name"], "arguments": call["arguments"],
                                                     "result": result})
            session.messages.append(tool_message(call["name"], result))
        return build_result(session, "Limite d'étapes atteinte : arrêt de l'agent.", "MAX_STEPS")
