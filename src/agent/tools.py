"""
Registre des outils de l'agent (schémas JSON) et exécuteur commun aux niveaux 2 et 3.

Outils classés par effet :
- READ    : lecture sans effet de bord (recherche documentaire)
- COMPUTE : calcul déterministe par une règle métier
- WRITE   : action irréversible, exécutée UNIQUEMENT après confirmation de l'étudiant

L'exécuteur (écrit sans framework) :
- vérifie les arguments contre le schéma (champs requis, types) ;
- renvoie toute erreur au modèle sous forme d'observation, au lieu de planter ;
- refuse d'exécuter un outil WRITE sans jeton de confirmation ;
- applique une règle de cohérence : on ne peut enregistrer que des points de charge
  réellement calculés par l'outil pendant la session (pas un chiffre inventé par le modèle).
"""
import time
from typing import Any, Callable, Dict, List, Optional

from src.agent import business_rules as br
from src.rag.retriever import Retriever

READ, COMPUTE, WRITE = "READ", "COMPUTE", "WRITE"


def _schema(name: str, description: str, properties: Dict[str, Any], required: List[str]) -> Dict[str, Any]:
    return {"type": "function", "function": {
        "name": name, "description": description,
        "parameters": {"type": "object", "properties": properties, "required": required}}}


TOOL_SPECS: Dict[str, Dict[str, Any]] = {
    "rechercher_documents": {
        "effect": READ,
        "schema": _schema(
            "rechercher_documents",
            "Recherche dans les fiches officielles (bourses CROUS, logement, Visale, APL, aides d'urgence, mobilité, "
            "restauration, santé). Renvoie les 5 passages les plus pertinents avec leur fichier source. "
            "À utiliser pour toute question factuelle (montant, condition, date, démarche).",
            {"question": {"type": "string", "description": "La question à rechercher, en français."}},
            ["question"]),
    },
    "calculer_points_charge": {
        "effect": COMPUTE,
        "schema": _schema(
            "calculer_points_charge",
            "Calcule les points de charge de la bourse CROUS (barème officiel) à partir de la distance "
            "domicile familial - établissement et de la fratrie.",
            {"distance_km": {"type": "number", "description": "Distance en km entre le domicile familial et l'établissement."},
             "freres_superieur": {"type": "integer", "description": "Nombre de frères et sœurs inscrits dans l'enseignement supérieur (université, fac, école)."},
             "freres_charge": {"type": "integer", "description": "Nombre d'autres frères et sœurs à charge (mineurs, collège, lycée)."}},
            ["distance_km", "freres_superieur", "freres_charge"]),
    },
    "estimer_echelon_bourse": {
        "effect": COMPUTE,
        "schema": _schema(
            "estimer_echelon_bourse",
            "Estime l'échelon de bourse (0bis à 7) et son montant à partir des points de charge "
            "(calculés au préalable avec calculer_points_charge) et du revenu fiscal de référence de la famille.",
            {"points_charge": {"type": "integer", "description": "Total des points de charge."},
             "revenu_fiscal": {"type": "number", "description": "Revenu fiscal de référence de la famille, en euros par an."}},
            ["points_charge", "revenu_fiscal"]),
    },
    "estimer_aide_logement": {
        "effect": COMPUTE,
        "schema": _schema(
            "estimer_aide_logement",
            "Donne la fourchette indicative de l'aide au logement (APL) d'un étudiant à partir de son loyer mensuel.",
            {"loyer": {"type": "number", "description": "Loyer mensuel en euros."}},
            ["loyer"]),
    },
    "enregistrer_simulation": {
        "effect": WRITE,
        "schema": _schema(
            "enregistrer_simulation",
            "ACTION IRRÉVERSIBLE : enregistre définitivement le dossier de simulation de l'étudiant. "
            "À appeler uniquement si l'étudiant demande explicitement de sauvegarder, enregistrer ou générer "
            "son dossier, et après avoir calculé ses points de charge. L'étudiant devra confirmer.",
            {"points_charge": {"type": "integer", "description": "Points de charge calculés par calculer_points_charge."},
             "resume": {"type": "string", "description": "Résumé de la simulation en une ou deux phrases."},
             "echelon_estime": {"type": "string", "description": "Échelon estimé (0bis à 7), si calculé."},
             "montant_annuel_euros": {"type": "number", "description": "Montant annuel de bourse estimé, si calculé."}},
            ["points_charge", "resume"]),
    },
}

TOOL_SCHEMAS = [spec["schema"] for spec in TOOL_SPECS.values()]
_JSON_TYPES = {"string": str, "integer": int, "number": (int, float), "object": dict}


def describe_tools_for_prompt() -> str:
    """Description textuelle des outils (utilisée par le planificateur ReWOO, niveau 3)."""
    lines = []
    for name, spec in TOOL_SPECS.items():
        params = spec["schema"]["function"]["parameters"]
        args = ", ".join(f"{p}: {d['type']}" + ("" if p in params["required"] else " (optionnel)")
                         for p, d in params["properties"].items())
        lines.append(f"- {name}({args}) [{spec['effect']}] : {spec['schema']['function']['description']}")
    return "\n".join(lines)


class ToolExecutor:
    def __init__(self, retriever: Retriever):
        self.retriever = retriever
        self.computed_points: List[int] = []    # points renvoyés par calculer_points_charge
        self.last_search: Optional[Dict[str, Any]] = None  # pour Recall@5 / MRR et les citations
        self.search_docs: List[str] = []        # tous les fichiers renvoyés par les recherches
        self.writes: List[Dict[str, Any]] = []  # actions WRITE réellement exécutées
        self.log: List[Dict[str, Any]] = []     # journal de tous les appels (pour la trace)

    def effect(self, name: str) -> Optional[str]:
        spec = TOOL_SPECS.get(name)
        return spec["effect"] if spec else None

    def _validate(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        params = TOOL_SPECS[name]["schema"]["function"]["parameters"]
        if not isinstance(args, dict):
            raise br.BusinessRuleError("les arguments doivent être un objet JSON.")
        unknown = set(args) - set(params["properties"])
        if unknown:
            raise br.BusinessRuleError(f"arguments inconnus : {sorted(unknown)}.")
        missing = [p for p in params["required"] if args.get(p) is None]
        if missing:
            raise br.BusinessRuleError(f"arguments manquants : {missing}.")
        clean = {}
        for key, value in args.items():
            if value is None:
                continue
            expected = params["properties"][key]["type"]
            # Tolérance : un modèle envoie parfois "310" au lieu de 310
            if expected in ("integer", "number") and isinstance(value, str):
                try:
                    value = float(value.replace(",", ".").replace(" ", ""))
                except ValueError:
                    raise br.BusinessRuleError(f"{key} doit être un nombre (reçu : {value!r}).")
            if expected == "integer" and isinstance(value, float) and value.is_integer():
                value = int(value)
            if not isinstance(value, _JSON_TYPES[expected]) or isinstance(value, bool):
                raise br.BusinessRuleError(f"{key} doit être de type {expected} (reçu : {value!r}).")
            clean[key] = value
        return clean

    def execute(self, name: str, args: Dict[str, Any], confirmed: bool = False) -> Dict[str, Any]:
        """Exécute un outil et renvoie toujours une observation (jamais d'exception vers la boucle)."""
        t0 = time.time()
        entry: Dict[str, Any] = {"tool": name, "arguments": args, "effect": self.effect(name)}
        try:
            if name not in TOOL_SPECS:
                raise br.BusinessRuleError(f"outil inconnu : {name}. Outils disponibles : {list(TOOL_SPECS)}.")
            clean = self._validate(name, args)
            if TOOL_SPECS[name]["effect"] == WRITE and not confirmed:
                raise PermissionError("action irréversible non confirmée par l'étudiant.")
            result = self._dispatch(name, clean)
            entry.update(ok=True, result=result)
        except Exception as e:
            result = {"erreur": str(e)}
            entry.update(ok=False, error=str(e))
        entry["duree_s"] = round(time.time() - t0, 3)
        self.log.append(entry)
        return result

    def _check_points(self, points: int) -> None:
        """Règle de cohérence : seuls des points réellement calculés par l'outil peuvent être réutilisés."""
        if points not in self.computed_points:
            raise br.BusinessRuleError(
                f"points_charge={points} n'a pas été calculé : appelle d'abord calculer_points_charge et "
                f"réutilise sa valeur (calculés dans cette session : {self.computed_points or 'aucun'}).")

    def precheck(self, name: str, args: Dict[str, Any]) -> Optional[str]:
        """Vérifie un appel WRITE AVANT de demander la confirmation (on ne fait pas confirmer une action
        invalide). Renvoie le message d'erreur, ou None si l'appel est recevable."""
        try:
            clean = self._validate(name, args)
            if name == "enregistrer_simulation":
                self._check_points(clean["points_charge"])
            return None
        except Exception as e:
            self.log.append({"tool": name, "arguments": args, "effect": self.effect(name), "ok": False,
                             "error": str(e), "stage": "precheck", "duree_s": 0.0})
            return str(e)

    def _dispatch(self, name: str, a: Dict[str, Any]) -> Dict[str, Any]:
        if name == "rechercher_documents":
            hits = self.retriever.retrieve(a["question"])
            res = {"passages": [{"rang": h.rank, "source": h.chunk.doc_name, "texte": h.chunk.content} for h in hits]}
            if self.last_search is None:
                self.last_search = {"docs": [h.chunk.doc_name for h in hits], "texts": [h.chunk.content for h in hits]}
            self.search_docs.extend(h.chunk.doc_name for h in hits)
            return res
        if name == "calculer_points_charge":
            res = br.calculer_points_charge(**a)
            self.computed_points.append(res["total_points_charge"])
            return res
        if name == "estimer_echelon_bourse":
            self._check_points(a["points_charge"])
            return br.estimer_echelon_bourse(**a)
        if name == "estimer_aide_logement":
            return br.estimer_aide_logement(**a)
        if name == "enregistrer_simulation":
            self._check_points(a["points_charge"])
            res = br.enregistrer_simulation(**a)
            self.writes.append({"arguments": a, "result": res})
            return res
        raise br.BusinessRuleError(f"outil non implémenté : {name}")
