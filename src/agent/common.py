"""
Éléments partagés par les agents des niveaux 2 (ReAct) et 3 (ReWOO) :
session (état d'une requête, y compris pendant l'attente de confirmation), prompt et résultat.
"""
import json
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from src.agent.tools import ToolExecutor, TOOL_SPECS
from src.rag.engine import ABSTENTION_SENTENCE, extract_citations
from src.metrics import is_abstention
from src.tracker import ExecutionTrace

AGENT_RULES = f"""Tu es un assistant spécialisé dans les aides étudiantes en France (bourses CROUS, logement, APL, aides d'urgence, mobilité, restauration, santé). Tu réponds en français, de façon concise.

Règles impératives :
1. Questions factuelles (montant, condition, date, démarche) : appelle TOUJOURS rechercher_documents avant de répondre, même si tu penses connaître la réponse. Réponds ensuite UNIQUEMENT à partir des passages obtenus, en citant chaque information au format [Source: nom_du_fichier.md].
2. Si, après la recherche, les passages ne contiennent pas la réponse, réponds exactement : « {ABSTENTION_SENTENCE} »
3. Calculs (points de charge, échelon, aide au logement) : utilise TOUJOURS les outils de calcul, ne calcule jamais toi-même. Quand un outil a besoin du résultat d'un autre (ex. l'échelon a besoin des points de charge), attends ce résultat avant de l'appeler : n'invente jamais une valeur intermédiaire. Reprends les chiffres renvoyés par les outils et cite leur champ "source".
4. Si l'étudiant demande explicitement de sauvegarder, enregistrer ou générer son dossier, sa fiche ou son récapitulatif : une fois les calculs faits, appelle enregistrer_simulation. Ne demande pas toi-même la confirmation dans ton texte : le système la demande automatiquement à l'étudiant avant d'exécuter l'action. Sans demande explicite, n'appelle jamais cet outil.
5. Demande hors du champ des aides étudiantes, illégale ou trop vague : n'appelle aucun outil ; refuse poliment ou pose une question de précision."""


@dataclass
class AgentSession:
    query: str
    executor: ToolExecutor
    trace: ExecutionTrace
    level: int
    session_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    messages: List[Dict[str, Any]] = field(default_factory=list)
    llm_calls: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    steps: int = 0
    pending: Optional[Dict[str, Any]] = None   # appel WRITE en attente de confirmation
    confirmations: List[Dict[str, Any]] = field(default_factory=list)
    extra: Dict[str, Any] = field(default_factory=dict)  # état propre à ReWOO (plan, résultats)

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens

    def count(self, resp) -> None:
        self.llm_calls += 1
        self.prompt_tokens += resp.prompt_tokens
        self.completion_tokens += resp.completion_tokens


def confirmation_message(call: Dict[str, Any]) -> str:
    a = call["arguments"]
    lines = [f"⚠️ **Action irréversible à confirmer** : `{call['name']}`", ""]
    for k, v in a.items():
        lines.append(f"- **{k}** : {v}")
    lines += ["", "Confirmez-vous cette action ? (oui / non)"]
    return "\n".join(lines)


def valid_sources(executor: ToolExecutor) -> List[str]:
    """Fichiers qu'une réponse a le droit de citer : ceux renvoyés par les outils pendant la session."""
    docs = list(executor.search_docs)
    for entry in executor.log:
        src = (entry.get("result") or {}).get("source")
        if src:
            docs.append(src)
    return list(dict.fromkeys(docs))


def build_result(session: AgentSession, response: str, status: str) -> Dict[str, Any]:
    ex = session.executor
    allowed = valid_sources(ex)
    cited = extract_citations(response)
    tr = session.trace
    tr.tools_used = [e["tool"] for e in ex.log]
    tr.sources = [c for c in cited if c in allowed]
    tr.add_step("final", {"status": status, "llm_calls": session.llm_calls, "steps": session.steps})
    tr.finalize(response=response, status=status, prompt_tokens=session.prompt_tokens,
                completion_tokens=session.completion_tokens)
    return {
        "level": session.level,
        "query": session.query,
        "response": response,
        "status": status,
        "session": session if status == "WAITING_CONFIRMATION" else None,
        "abstained": is_abstention(response),
        "citations": cited,
        "citations_valides": [c for c in cited if c in allowed],
        "citations_invalides": [c for c in cited if c not in allowed],
        "retrieved_docs": list(dict.fromkeys(ex.last_search["docs"])) if ex.last_search else [],
        "retrieved_chunks": ([{"rank": i + 1, "doc": d, "content": t, "chunk_id": f"{d}@{i + 1}"}
                              for i, (d, t) in enumerate(zip(ex.last_search["docs"], ex.last_search["texts"]))]
                             if ex.last_search else []),
        "tool_log": ex.log,
        "writes": ex.writes,
        "confirmations": session.confirmations,
        "llm_calls": session.llm_calls,
        "trace": tr.to_dict(),
    }


def tool_message(name: str, result: Dict[str, Any]) -> Dict[str, Any]:
    return {"role": "tool", "tool_name": name, "content": json.dumps(result, ensure_ascii=False)}


def is_write(name: str) -> bool:
    spec = TOOL_SPECS.get(name)
    return bool(spec and spec["effect"] == "WRITE")
