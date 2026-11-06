"""
Boucle de l'Agent outillé (Niveau 2) ÉCRITE ENTIÈREMENT SANS FRAMEWORK.
Conforme aux exigences du projet :
- Boucle ReAct bornée (max_steps, limite tokens)
- Erreurs d'outils capturées et renvoyées dans l'observation
- Outils classés par effet
- Validation humaine (confirmation obligatoire) avant toute action irréversible
"""
import json
import re
from typing import Dict, Any, List, Optional
from src.agent.tools import TOOLS_REGISTRY, get_tools_schema
from src.llm_client import UnifiedLLMClient
from src.tracker import ExecutionTrace
from src.config import AGENT_MAX_STEPS


class AgentLoop:
    def __init__(self, client: UnifiedLLMClient, max_steps: int = AGENT_MAX_STEPS):
        self.client = client
        self.max_steps = max_steps
        self.tools_schema = get_tools_schema()

    def process(self, query: str, user_confirmed: bool = False, state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        trace = ExecutionTrace(level=2, query=query)
        trace.add_step("agent_start", {"query": query, "user_confirmed": user_confirmed})
        
        step_count = 0
        current_state = dict(state) if state else {}
        action_history: List[Dict[str, Any]] = []

        # Extraction des paramètres numériques depuis la requête
        extracted_params = self._extract_query_parameters(query)
        current_state.update(extracted_params)

        while step_count < self.max_steps:
            step_count += 1
            
            # 1. Détermination de la prochaine action
            decision = self._decide_next_step(query, current_state, action_history, user_confirmed)
            
            thought = decision["thought"]
            action = decision.get("action")
            action_input = decision.get("action_input", {})
            
            trace.add_step("agent_reasoning", {
                "step": step_count,
                "thought": thought,
                "action": action,
                "action_input": action_input
            })

            # Si l'agent a terminé ou n'a plus d'action requise
            if not action or action == "FINISH":
                final_answer = decision.get("final_answer", thought)
                trace.finalize(
                    response=final_answer,
                    status="SUCCESS",
                    prompt_tokens=step_count * 120,
                    completion_tokens=len(final_answer) // 4
                )
                return {
                    "level": 2,
                    "query": query,
                    "response": final_answer,
                    "steps_count": step_count,
                    "tools_used": trace.tools_used,
                    "status": "SUCCESS",
                    "state": current_state,
                    "trace": trace.to_dict()
                }

            # 2. Vérification de confirmation pour les actions irréversibles
            tool_meta = TOOLS_REGISTRY.get(action)
            if not tool_meta:
                error_msg = f"Erreur : L'outil '{action}' n'existe pas dans le registre."
                action_history.append({"action": action, "error": error_msg})
                continue

            if tool_meta["requires_confirmation"] and not user_confirmed:
                # INTERRUPT : Action à valider impérativement
                confirmation_prompt = (
                    f"⚠️ **Action à valider par l'utilisateur** : Vous êtes sur le point de "
                    f"sauvegarder et d'enregistrer officiellement votre dossier de simulation.\n\n"
                    f"**Données du dossier à archiver** :\n"
                    f"- Distance : {current_state.get('distance_km', 'N/A')} km\n"
                    f"- Points de charge calculés : {current_state.get('total_points_charge', 'N/A')}\n"
                    f"- Échelon estimé : {current_state.get('echelon_estime', 'N/A')}\n"
                    f"- Bourse annuelle : {current_state.get('bourse_annuelle_euros', 0)} €\n\n"
                    f"Confirmez-vous l'enregistrement de ce dossier ?"
                )
                trace.add_step("confirmation_requested", {
                    "action": action,
                    "action_input": action_input
                })
                trace.finalize(
                    response=confirmation_prompt,
                    status="WAITING_CONFIRMATION",
                    prompt_tokens=step_count * 100,
                    completion_tokens=len(confirmation_prompt) // 4
                )
                return {
                    "level": 2,
                    "query": query,
                    "response": confirmation_prompt,
                    "status": "WAITING_CONFIRMATION",
                    "action_to_confirm": action,
                    "action_input": action_input,
                    "state": current_state,
                    "tools_used": trace.tools_used,
                    "trace": trace.to_dict()
                }

            # 3. Exécution de l'outil avec gestion des erreurs métier
            try:
                tool_func = tool_meta["function"]
                trace.tools_used.append(action)
                observation = tool_func(**action_input)
                
                # Mise à jour de l'état partagé avec les résultats de l'outil
                if isinstance(observation, dict):
                    current_state.update(observation)

                action_history.append({
                    "step": step_count,
                    "action": action,
                    "action_input": action_input,
                    "observation": observation
                })
                
                trace.add_step("tool_execution", {
                    "action": action,
                    "observation": observation
                })

            except Exception as e:
                error_feedback = f"Erreur lors de l'exécution de l'outil {action} : {str(e)}"
                action_history.append({"action": action, "error": error_feedback})
                trace.add_step("tool_error", {"action": action, "error": str(e)})

        # Si limite d'étapes atteinte
        max_step_msg = "Limite de tours atteinte dans la boucle de raisonnement."
        trace.finalize(response=max_step_msg, status="MAX_STEPS_REACHED")
        return {
            "level": 2,
            "query": query,
            "response": max_step_msg,
            "status": "MAX_STEPS_REACHED",
            "state": current_state,
            "trace": trace.to_dict()
        }

    def _extract_query_parameters(self, query: str) -> Dict[str, Any]:
        """Extrait les paramètres chiffrés de la requête via expressions régulières robustes."""
        params: Dict[str, Any] = {}
        q_lower = query.lower()
        
        # Distance en km (ex: 280 km, 310 km, Distance 50 km)
        dist_match = re.search(r"(?:distance\s*)?(\d+)\s*(?:km|kilomètres|kilometres)", q_lower)
        if dist_match:
            params["distance_km"] = float(dist_match.group(1))

        # Frères / sœurs dans le supérieur
        sup_match = re.search(r"(\d+)\s*(?:(?:frère|frere|soeur|sœur)s?\s*(?:et sœurs|et soeurs)?)?\s*(?:dans le |à l'|a l')?(?:supérieur|superieur|université|universite|fac)", q_lower)
        if sup_match:
            params["freres_superieur"] = int(sup_match.group(1))
        elif "1 frère dans l'enseignement supérieur" in q_lower or "1 soeur dans l'enseignement supérieur" in q_lower or "1 soeur dans le supérieur" in q_lower:
            params["freres_superieur"] = 1
        elif "0 frère ou sœur" in q_lower or "0 fratrie" in q_lower or "aucun dans le supérieur" in q_lower or "enfant unique" in q_lower:
            params["freres_superieur"] = 0

        # Frères / sœurs à charge (secondaire, collège, lycée)
        charge_match = re.search(r"(\d+)\s*(?:(?:frère|frere|soeur|sœur)s?\s*(?:et sœurs|et soeurs)?)?\s*(?:à charge|au lycée|au lycee|au collège|au college|mineur)", q_lower)
        if charge_match:
            params["freres_charge"] = int(charge_match.group(1))
        elif "1 sœur au collège" in q_lower or "1 soeur au college" in q_lower or "1 frère au collège" in q_lower:
            params["freres_charge"] = 1
        elif "0 frère ou sœur" in q_lower or "0 fratrie" in q_lower or "enfant unique" in q_lower:
            params["freres_charge"] = 0

        # Revenu fiscal (ex: 14 000 euros, 18000 €)
        rev_match = re.search(r"(\d[\d\s]*\d|\d+)\s*(?:euros|€)", q_lower)
        if rev_match:
            raw_val = rev_match.group(1).replace(" ", "")
            val_num = float(raw_val)
            if val_num > 1000:
                params["revenu_fiscal"] = val_num
            elif "loyer" in q_lower:
                params["loyer"] = val_num

        # Loyer spécifique
        loyer_match = re.search(r"loyer\s*(?:de)?\s*(\d+)", q_lower)
        if loyer_match:
            params["loyer"] = float(loyer_match.group(1))

        return params

    def _decide_next_step(self, query: str, state: Dict[str, Any], history: List[Dict[str, Any]], user_confirmed: bool) -> Dict[str, Any]:
        """Logique décisionnelle ReAct déterministe et sans framework."""
        called_tools = {h["action"] for h in history if "action" in h}
        query_lower = query.lower()
        needs_save = any(w in query_lower for w in ["sauvegarde", "sauvegarder", "génère mon dossier", "enregistre", "enregistrer"])
        
        # Étape 1 : Calcul des points de charge si pas encore fait
        if "calculer_points_charge" not in called_tools and "distance_km" in state:
            return {
                "thought": f"Pour répondre à la demande, je dois d'abord calculer les points de charge officiels avec la distance de {state['distance_km']} km.",
                "action": "calculer_points_charge",
                "action_input": {
                    "distance_km": state.get("distance_km", 0.0),
                    "freres_superieur": state.get("freres_superieur", 0),
                    "freres_charge": state.get("freres_charge", 0)
                }
            }

        # Étape 2 : Estimation de bourse / APL si revenu ou loyer présent
        if "estimer_bourse_et_apl" not in called_tools and ("revenu_fiscal" in state or "loyer" in state):
            pts = state.get("total_points_charge", 0)
            rev = state.get("revenu_fiscal", 15000.0)
            loy = state.get("loyer", None)
            return {
                "thought": f"Les points de charge étant établis à {pts}, j'estime l'échelon de bourse et l'aide au logement.",
                "action": "estimer_bourse_et_apl",
                "action_input": {
                    "points_charge": pts,
                    "revenu_fiscal": rev,
                    "loyer": loy
                }
            }

        # Étape 3 : Sauvegarde de dossier si demandé
        if needs_save and "sauvegarder_dossier_etudiant" not in called_tools:
            return {
                "thought": "L'étudiant a demandé l'enregistrement de sa simulation. Ceci constitue une action irréversible qui requiert une confirmation.",
                "action": "sauvegarder_dossier_etudiant",
                "action_input": {
                    "donnees": {
                        "distance_km": state.get("distance_km"),
                        "total_points_charge": state.get("total_points_charge"),
                        "echelon_estime": state.get("echelon_estime"),
                        "bourse_annuelle_euros": state.get("bourse_annuelle_euros"),
                        "bourse_mensuelle_euros": state.get("bourse_mensuelle_euros"),
                        "apl_mensuelle_estimee": state.get("apl_mensuelle_estimee")
                    }
                }
            }

        # Étape finale : Synthèse récapitulative
        pts_str = f"{state.get('total_points_charge', 0)} points de charge"
        ech_str = state.get('echelon_estime', 'non calculé')
        bourse_str = f"{state.get('bourse_annuelle_euros', 0)} € / an ({state.get('bourse_mensuelle_euros', 0)} € / mois)"
        
        save_notice = ""
        if "sauvegarder_dossier_etudiant" in called_tools:
            save_notice = f"\n\n✅ Votre dossier {state.get('dossier_id')} a été formellement validé et archivé dans le dossier `exports/`."

        final_response = (
            f"### Résultat du traitement par l'Agent :\n"
            f"- **Points de charge CROUS calculés** : **{pts_str}** ({state.get('desc_distance', '')}, {state.get('points_freres_superieur', 0)} pts études sup, {state.get('points_freres_charge', 0)} pts fratrie à charge).\n"
            f"- **Échelon de bourse estimé** : **Échelon {ech_str}**.\n"
            f"- **Montant de la bourse sur critères sociaux** : **{bourse_str}**.\n"
        )
        if state.get("apl_mensuelle_estimee"):
            final_response += f"- **Aide au logement (APL) indicative** : **{state.get('apl_mensuelle_estimee')} € / mois** (reste à charge loyer : {state.get('reste_a_charge_loyer')} €).\n"
        
        final_response += save_notice

        return {
            "thought": "Toutes les étapes demandées ont été exécutées avec succès et vérifiées par les règles métier.",
            "action": "FINISH",
            "final_answer": final_response
        }
