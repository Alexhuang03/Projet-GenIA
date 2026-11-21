"""
Règles métier vérifiées par du code (sans LLM ni framework).
Les calculs ne sont pas laissés au modèle : il appelle ces fonctions, qui valident leurs entrées
et appliquent les barèmes du corpus. Chaque résultat indique sa source.

Hypothèse documentée : la fiche 01 ne donne les plafonds de ressources que pour 0 et 4 points
de charge, et seulement pour les échelons 0bis et 7. L'estimation d'échelon interpole donc
linéairement (1) entre 0 et 4 points, prolongée au-delà, et (2) entre l'échelon 7 et l'échelon 0bis.
C'est une estimation indicative, présentée comme telle à l'étudiant.
"""
import json
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from src.config import EXPORTS_DIR

SOURCE_BOURSES = "01_bourses_crous_criteres_sociaux.md"
SOURCE_APL = "03_aide_personnalisee_logement_apl.md"

# Fiche 01, section 4 : montants annuels 2024-2025, du plus élevé au plus faible
ECHELONS = [("7", 6335), ("6", 5612), ("5", 5212), ("4", 4587), ("3", 3828), ("2", 3071), ("1", 2163), ("0bis", 1454)]
# Fiche 01, section 5 : plafonds indicatifs (RFR N-2) à 0 et 4 points de charge
PLAFOND_0BIS = {0: 35800, 4: 46000}
PLAFOND_7 = {0: 6800, 4: 12500}


class BusinessRuleError(ValueError):
    """Entrée refusée par une règle métier ; le message est renvoyé tel quel au modèle."""


def _check_int(name: str, value: Any, low: int, high: int) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or int(value) != value:
        raise BusinessRuleError(f"{name} doit être un entier (reçu : {value!r}).")
    if not low <= value <= high:
        raise BusinessRuleError(f"{name} doit être compris entre {low} et {high} (reçu : {value}).")
    return int(value)


def _check_number(name: str, value: Any, low: float, high: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise BusinessRuleError(f"{name} doit être un nombre (reçu : {value!r}).")
    if not low <= value <= high:
        raise BusinessRuleError(f"{name} doit être compris entre {low} et {high} (reçu : {value}).")
    return float(value)


def calculer_points_charge(distance_km: float, freres_superieur: int = 0, freres_charge: int = 0) -> Dict[str, Any]:
    """Fiche 01, section 3 : barème d'éloignement et de fratrie."""
    d = _check_number("distance_km", distance_km, 0, 20000)
    sup = _check_int("freres_superieur", freres_superieur, 0, 15)
    chg = _check_int("freres_charge", freres_charge, 0, 15)
    if d < 30:
        pts_distance, tranche = 0, "moins de 30 km"
    elif d < 250:
        pts_distance, tranche = 1, "de 30 à 249 km"
    else:
        pts_distance, tranche = 2, "250 km et plus"
    total = pts_distance + 2 * sup + chg
    return {
        "total_points_charge": total,
        "detail": {"eloignement": f"{pts_distance} point(s) ({tranche})",
                   "fratrie_superieur": f"{2 * sup} point(s) ({sup} × 2)",
                   "fratrie_a_charge": f"{chg} point(s) ({chg} × 1)"},
        "source": SOURCE_BOURSES,
    }


def _plafond(table: Dict[int, int], points: int) -> float:
    return table[0] + (table[4] - table[0]) / 4 * points


def estimer_echelon_bourse(points_charge: int, revenu_fiscal: float) -> Dict[str, Any]:
    """Estimation indicative de l'échelon à partir des plafonds de la fiche 01 (voir hypothèse en tête)."""
    pts = _check_int("points_charge", points_charge, 0, 40)
    rfr = _check_number("revenu_fiscal", revenu_fiscal, 0, 1_000_000)
    p7, p0 = _plafond(PLAFOND_7, pts), _plafond(PLAFOND_0BIS, pts)
    for i, (echelon, montant) in enumerate(ECHELONS):
        plafond = p7 + (p0 - p7) * i / (len(ECHELONS) - 1)
        if rfr <= plafond:
            return {"eligible": True, "echelon_estime": echelon, "montant_annuel_euros": montant,
                    "montant_mensuel_euros": round(montant / 10, 2), "plafond_estime_euros": round(plafond),
                    "avertissement": "Estimation indicative interpolée à partir des plafonds de la fiche ; "
                                     "seul le CROUS fixe l'échelon définitif.",
                    "source": SOURCE_BOURSES}
    return {"eligible": False, "echelon_estime": None, "plafond_0bis_estime_euros": round(p0),
            "avertissement": "Revenu supérieur au plafond indicatif de l'échelon 0bis.", "source": SOURCE_BOURSES}


def estimer_aide_logement(loyer: float) -> Dict[str, Any]:
    """Fiche 03, section 3 : fourchette indicative pour un étudiant isolé sans revenus d'activité."""
    loyer = _check_number("loyer", loyer, 1, 5000)
    return {"apl_mensuelle_min_euros": min(100, loyer), "apl_mensuelle_max_euros": min(250, loyer),
            "valeur_frequente_residence_conventionnee": "180 à 220 €",
            "loyer_mensuel_euros": loyer,
            "facteurs": ["zone géographique", "loyer hors charges", "situation d'occupation", "ressources des 12 derniers mois"],
            "avertissement": "Fourchette indicative ; simuler sur caf.fr. Une demande en son nom avant 25 ans "
                             "fait perdre aux parents l'enfant à charge pour les prestations familiales.",
            "source": SOURCE_APL}


def enregistrer_simulation(points_charge: int, resume: str, echelon_estime: Optional[str] = None,
                           montant_annuel_euros: Optional[float] = None) -> Dict[str, Any]:
    """ACTION IRRÉVERSIBLE : écrit le dossier de simulation dans exports/.
    N'est jamais appelée directement par le modèle : l'agent exige d'abord la confirmation de l'étudiant."""
    pts = _check_int("points_charge", points_charge, 0, 40)
    if not isinstance(resume, str) or not resume.strip():
        raise BusinessRuleError("resume doit être un texte non vide.")
    if echelon_estime is not None and echelon_estime not in {e for e, _ in ECHELONS}:
        raise BusinessRuleError(f"echelon_estime inconnu : {echelon_estime!r}.")
    dossier_id = f"SIMU-{datetime.now():%Y%m%d}-{uuid.uuid4().hex[:6].upper()}"
    record = {"dossier_id": dossier_id, "cree_le": datetime.now().isoformat(timespec="seconds"),
              "points_charge": pts, "echelon_estime": echelon_estime,
              "montant_annuel_euros": montant_annuel_euros, "resume": resume.strip()}
    path = EXPORTS_DIR / f"{dossier_id}.json"
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"dossier_id": dossier_id, "fichier": str(path), "statut": "ENREGISTRE"}
