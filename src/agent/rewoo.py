"""
Niveau 3 (extension) : agent « planifier puis exécuter » (ReWOO), écrit sans framework.

Différence avec le ReAct du niveau 2 :
1. PLANIFICATEUR : un seul appel LLM produit le plan complet en JSON. Une étape peut réutiliser
   le résultat d'une autre par référence (« #E1.total_points_charge ») au lieu de deviner la valeur.
2. EXÉCUTEUR (code, sans LLM) : résout les références et exécute les étapes par vagues ; les étapes
   indépendantes d'une même vague tournent en parallèle. Une étape WRITE met l'exécution en pause
   jusqu'à la confirmation de l'étudiant (même mécanisme qu'au niveau 2).
3. SOLVEUR : un appel LLM rédige la réponse à partir des résultats.
=> 2 appels LLM par requête, quel que soit le nombre d'outils, contre 1 par tour pour ReAct.
Limite connue : pas de re-planification si une étape échoue (le solveur voit l'erreur et l'explique).
"""
import json
import re
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List

from src.agent.common import AGENT_RULES, AgentSession, build_result, confirmation_message, is_write
from src.agent.tools import ToolExecutor, describe_tools_for_prompt, TOOL_SPECS
from src.config import LLM_TEMPERATURE, LLM_SEED
from src.llm_client import UnifiedLLMClient
from src.rag.retriever import Retriever
from src.tracker import ExecutionTrace

MAX_PLAN_STEPS = 6
REF_RE = re.compile(r"^#(E\d+)(?:\.([\w.]+))?$")

PLANNER_PROMPT = """Tu es le planificateur d'un assistant pour les aides étudiantes. Tu ne réponds pas toi-même : tu écris le plan des outils à appeler.

Outils disponibles :
{tools}

Règles :
- Question factuelle (montant, condition, date, démarche) : une étape rechercher_documents.
- Calculs : utilise les outils de calcul. Si une étape a besoin du résultat d'une autre, écris une référence au lieu d'une valeur : "#E1.total_points_charge" (identifiant de l'étape, puis champ du résultat).
- enregistrer_simulation : seulement si l'étudiant demande explicitement de sauvegarder, enregistrer ou générer son dossier, sa fiche ou son récapitulatif ; en dernière étape, avec "points_charge": "#E1.total_points_charge" et un "resume" court. Le système demandera la confirmation à l'étudiant.
- Demande hors du champ des aides étudiantes, illégale ou trop vague : plan vide.
- Au plus {max_steps} étapes.

Réponds UNIQUEMENT avec un objet JSON de la forme :
{{"plan": [{{"id": "E1", "outil": "nom_outil", "arguments": {{...}}}}, ...]}}

Exemple pour « 40 km, 1 frère à la fac, revenu 20 000 €, calcule mon échelon et enregistre » :
{{"plan": [
 {{"id": "E1", "outil": "calculer_points_charge", "arguments": {{"distance_km": 40, "freres_superieur": 1, "freres_charge": 0}}}},
 {{"id": "E2", "outil": "estimer_echelon_bourse", "arguments": {{"points_charge": "#E1.total_points_charge", "revenu_fiscal": 20000}}}},
 {{"id": "E3", "outil": "enregistrer_simulation", "arguments": {{"points_charge": "#E1.total_points_charge", "echelon_estime": "#E2.echelon_estime", "montant_annuel_euros": "#E2.montant_annuel_euros", "resume": "Simulation : points de charge et échelon estimé"}}}}
]}}

Exemple pour « 10 km, 2 sœurs au lycée, loyer 500 €, calcule mes points et mon aide au logement » (pas de demande d'enregistrement, donc pas d'étape enregistrer_simulation) :
{{"plan": [
 {{"id": "E1", "outil": "calculer_points_charge", "arguments": {{"distance_km": 10, "freres_superieur": 0, "freres_charge": 2}}}},
 {{"id": "E2", "outil": "estimer_aide_logement", "arguments": {{"loyer": 500}}}}
]}}

Exemple pour « J'ai un souci, tu peux regarder ? » (trop vague) : {{"plan": []}}"""

SOLVER_PROMPT = AGENT_RULES + """

Tu reçois la demande de l'étudiant et les résultats des outils déjà exécutés (tu ne peux plus en appeler). Rédige la réponse finale à partir de ces résultats uniquement. Si aucun outil n'a été exécuté, applique la règle 5. Si une étape a échoué, dis-le simplement."""


NO_TOOL_PROMPT = """Tu es un assistant spécialisé dans les aides étudiantes en France. La demande ci-dessous est hors de ton champ, illégale ou trop vague, et aucun outil n'a été exécuté.
- Si elle est illégale ou hors sujet : refuse poliment en une phrase et rappelle que tu traites les aides étudiantes.
- Si elle est trop vague : pose une question de précision (bourse, logement, APL, aide d'urgence, mobilité ?).
N'invente aucune information. Réponds en français, en deux phrases au plus."""


def _lookup(results: Dict[str, Any], ref: str):
    m = REF_RE.match(ref.strip())
    step, path = m.group(1), m.group(2)
    if step not in results:
        raise KeyError(f"référence à une étape inconnue ou pas encore exécutée : {step}")
    value = results[step]
    if isinstance(value, dict) and "erreur" in value:
        raise KeyError(f"l'étape {step} dont dépend cette étape a échoué")
    for key in (path.split(".") if path else []):
        if not isinstance(value, dict) or key not in value:
            raise KeyError(f"champ « {key} » absent du résultat de {step}")
        value = value[key]
    return value


def _deps(args: Dict[str, Any]) -> List[str]:
    return [REF_RE.match(v.strip()).group(1) for v in args.values()
            if isinstance(v, str) and REF_RE.match(v.strip())]


def _resolve(args: Dict[str, Any], results: Dict[str, Any]) -> Dict[str, Any]:
    return {k: (_lookup(results, v) if isinstance(v, str) and REF_RE.match(v.strip()) else v)
            for k, v in args.items()}


class ReWOOAgent:
    level = 3

    def __init__(self, client: UnifiedLLMClient, retriever: Retriever):
        self.client, self.retriever = client, retriever

    def process(self, query: str, temperature: float = LLM_TEMPERATURE, seed: int = LLM_SEED) -> Dict[str, Any]:
        session = AgentSession(
            query=query, executor=ToolExecutor(self.retriever), level=self.level,
            trace=ExecutionTrace(level=self.level, query=query, model=f"{self.client.provider}:{self.client.model}"))
        session.extra.update(temperature=temperature, seed=seed, results={}, done=set())

        # 1. Planification (1 appel LLM)
        planner = PLANNER_PROMPT.format(tools=describe_tools_for_prompt(), max_steps=MAX_PLAN_STEPS)
        resp = self.client.chat([{"role": "system", "content": planner}, {"role": "user", "content": query}],
                                temperature=temperature, seed=seed, json_mode=True)
        session.count(resp)
        plan, plan_error = self._parse_plan(resp.content)
        session.extra["plan"] = plan
        session.trace.add_step("plan", {"plan": plan, "erreur": plan_error, "prompt_tokens": resp.prompt_tokens,
                                        "completion_tokens": resp.completion_tokens})
        if plan_error:
            session.extra["results"]["PLAN"] = {"erreur": plan_error}
        return self._execute(session)

    def resume(self, session: AgentSession, approved: bool) -> Dict[str, Any]:
        step, session.pending = session.pending, None
        if step is None:
            raise ValueError("Aucune action en attente de confirmation.")
        session.confirmations.append({"tool": step["name"], "approved": approved})
        session.trace.add_step("confirmation", {"tool": step["name"], "approved": approved})
        if approved:
            result = session.executor.execute(step["name"], step["arguments"], confirmed=True)
        else:
            result = {"refus": "L'étudiant a refusé cette action."}
        session.extra["results"][step["id"]] = result
        session.extra["done"].add(step["id"])
        session.trace.add_step("tool_call", {"id": step["id"], "tool": step["name"],
                                             "arguments": step["arguments"], "result": result})
        return self._execute(session)

    def _parse_plan(self, content: str):
        try:
            data = json.loads(content)
            raw = data.get("plan", []) if isinstance(data, dict) else []
            plan = []
            for i, s in enumerate(raw[:MAX_PLAN_STEPS]):
                plan.append({"id": str(s.get("id") or f"E{i + 1}"), "outil": s.get("outil") or s.get("tool"),
                             "arguments": s.get("arguments") or s.get("args") or {}})
            return plan, None
        except Exception as e:
            return [], f"plan illisible : {e}"

    def _execute(self, session: AgentSession) -> Dict[str, Any]:
        results, done, ex = session.extra["results"], session.extra["done"], session.executor
        plan = session.extra["plan"]
        while True:
            pending = [s for s in plan if s["id"] not in done]
            if not pending:
                break
            ready = [s for s in pending if all(d in done for d in _deps(s["arguments"]))]
            if not ready:  # dépendance circulaire ou vers une étape inexistante
                for s in pending:
                    results[s["id"]] = {"erreur": "dépendance impossible à résoudre"}
                    done.add(s["id"])
                break
            # Étapes WRITE : une à la fois, après celles de lecture/calcul de la vague
            normal = [s for s in ready if not is_write(s["outil"])]
            writes = [s for s in ready if is_write(s["outil"])]
            wave = normal or writes[:1]
            resolved = []
            for s in wave:
                try:
                    resolved.append((s, _resolve(s["arguments"], results)))
                except KeyError as e:
                    results[s["id"]] = {"erreur": str(e)}
                    done.add(s["id"])
                    session.trace.add_step("tool_call", {"id": s["id"], "tool": s["outil"], "erreur": str(e)})
            if not normal and resolved:
                s, args = resolved[0]
                error = ex.precheck(s["outil"], args)
                if error:
                    results[s["id"]] = {"erreur": error}
                    done.add(s["id"])
                    session.trace.add_step("tool_call", {"id": s["id"], "tool": s["outil"], "arguments": args,
                                                         "result": results[s["id"]], "stage": "precheck"})
                    continue
                session.pending = {"id": s["id"], "name": s["outil"], "arguments": args}
                session.trace.add_step("confirmation_requested", session.pending)
                return build_result(session, confirmation_message(session.pending), "WAITING_CONFIRMATION")
            # Lecture / calcul : en parallèle
            with ThreadPoolExecutor(max_workers=4) as pool:
                outs = list(pool.map(lambda sa: ex.execute(sa[0]["outil"], sa[1]), resolved))
            for (s, args), out in zip(resolved, outs):
                results[s["id"]] = out
                done.add(s["id"])
                session.trace.add_step("tool_call", {"id": s["id"], "tool": s["outil"], "arguments": args,
                                                     "result": out, "parallel_wave_size": len(resolved)})
            session.steps += 1

        # 3. Rédaction (1 appel LLM)
        evidence = [{"etape": s["id"], "outil": s["outil"], "resultat": results.get(s["id"])} for s in plan]
        if "PLAN" in results:
            evidence.append({"etape": "PLAN", "resultat": results["PLAN"]})
        if evidence:
            system = SOLVER_PROMPT
            user = f"Demande de l'étudiant : {session.query}\n\nRésultats des outils :\n{json.dumps(evidence, ensure_ascii=False, indent=1)}"
        else:
            system, user = NO_TOOL_PROMPT, f"Demande de l'étudiant : {session.query}"
        resp = self.client.chat([{"role": "system", "content": system}, {"role": "user", "content": user}],
                                temperature=session.extra["temperature"], seed=session.extra["seed"])
        session.count(resp)
        session.trace.add_step("solver", {"prompt_tokens": resp.prompt_tokens, "completion_tokens": resp.completion_tokens})
        return build_result(session, resp.content.strip(), "SUCCESS")
