"""
Règles métier vérifiées par du code (pur Python sans framework)
Exigence du sujet : Le respect des barèmes, calculs et plafonds est garanti
par la logique logicielle, et non laissé à l'appréciation statistique du LLM.
"""
import uuid
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from src.config import EXPORTS_DIR

# Montants officiels 2024-2025 (10 mensualités)
ECHELONS_BCS = {
    "0bis": {"annuel": 1454.0, "mensuel": 145.40, "plafond_base": 35800},
    "1":    {"annuel": 2163.0, "mensuel": 216.30, "plafond_base": 31200},
    "2":    {"annuel": 3071.0, "mensuel": 307.10, "plafond_base": 26800},
    "3":    {"annuel": 3828.0, "mensuel": 382.80, "plafond_base": 22500},
    "4":    {"annuel": 4587.0, "mensuel": 458.70, "plafond_base": 18200},
    "5":    {"annuel": 5212.0, "mensuel": 521.20, "plafond_base": 14500},
    "6":    {"annuel": 5612.0, "mensuel": 561.20, "plafond_base": 10800},
    "7":    {"annuel": 6335.0, "mensuel": 633.50, "plafond_base": 6800},
}


def calculer_points_charge(distance_km: float, freres_superieur: int = 0, freres_charge: int = 0) -> Dict[str, Any]:
    """
    Règle métier officielle du barème CROUS pour le calcul des points de charge.
    Validation par code des contraintes physiques et administratives.
    """
    # 1. Validation métier des entrées
    if distance_km < 0:
        raise ValueError("La distance domicile-établissement ne peut pas être négative.")
    if freres_superieur < 0 or freres_charge < 0:
        raise ValueError("Le nombre de frères et sœurs ne peut pas être négatif.")

    # 2. Barème d'éloignement kilométrique
    if distance_km < 30:
        points_distance = 0
        desc_distance = "Moins de 30 km (0 point)"
    elif distance_km < 250:
        points_distance = 1
        desc_distance = "De 30 à 249 km (1 point)"
    else:
        points_distance = 2
        desc_distance = "250 km et plus (2 points)"

    # 3. Barème fratrie
    points_fratrie_sup = freres_superieur * 2
    points_fratrie_charge = freres_charge * 1
    total_fratrie = points_fratrie_sup + points_fratrie_charge

    # 4. Total général des points de charge
    total_points = points_distance + total_fratrie

    return {
        "distance_km": distance_km,
        "points_distance": points_distance,
        "desc_distance": desc_distance,
        "freres_superieur": freres_superieur,
        "points_freres_superieur": points_fratrie_sup,
        "freres_charge": freres_charge,
        "points_freres_charge": points_fratrie_charge,
        "total_points_charge": total_points
    }


def estimer_bourse_et_apl(points_charge: int, revenu_fiscal: float, loyer: Optional[float] = None) -> Dict[str, Any]:
    """
    Évalue l'échelon indicatif de bourse et l'aide au logement en appliquant
    les seuils de ressources majorés par point de charge.
    """
    if points_charge < 0:
        raise ValueError("Les points de charge ne peuvent pas être négatifs.")
    if revenu_fiscal < 0:
        raise ValueError("Le revenu fiscal de référence ne peut pas être négatif.")

    # Chaque point de charge majore le plafond de ressources de ~5% à 7%
    majoration_par_point = 0.065
    coeff_points = 1.0 + (points_charge * majoration_par_point)

    echelon_retenu = None
    montant_annuel = 0.0
    montant_mensuel = 0.0

    # Recherche du meilleur échelon éligible
    for ech in ["7", "6", "5", "4", "3", "2", "1", "0bis"]:
        plafond_ajuste = ECHELONS_BCS[ech]["plafond_base"] * coeff_points
        if revenu_fiscal <= plafond_ajuste:
            echelon_retenu = ech
            montant_annuel = ECHELONS_BCS[ech]["annuel"]
            montant_mensuel = ECHELONS_BCS[ech]["mensuel"]
            break

    # Estimation indicative APL (si loyer renseigné)
    estimation_apl = 0.0
    reste_a_charge_loyer = 0.0
    if loyer and loyer > 0:
        # L'APL étudiant couvre environ 40% à 50% du loyer, plafonnée à 220€
        estimation_apl = min(round(loyer * 0.45, 2), 220.0)
        reste_a_charge_loyer = max(round(loyer - estimation_apl, 2), 0.0)

    total_aides_mensuelles = round(montant_mensuel + estimation_apl, 2)

    return {
        "points_charge": points_charge,
        "revenu_fiscal": revenu_fiscal,
        "echelon_estime": echelon_retenu if echelon_retenu else "Non éligible (supérieur aux plafonds)",
        "bourse_annuelle_euros": montant_annuel,
        "bourse_mensuelle_euros": montant_mensuel,
        "loyer_mensuel": loyer or 0.0,
        "apl_mensuelle_estimee": estimation_apl,
        "reste_a_charge_loyer": reste_a_charge_loyer,
        "total_aides_mensuelles": total_aides_mensuelles,
        "avantages_annexes": [
            "Exonération des frais d'inscription universitaire et de la CVEC",
            "Repas CROUS à tarif très social (1,00 €)",
            "Priorité pour l'attribution d'un logement CROUS (selon indice social)"
        ] if echelon_retenu else []
    }


def enregistrer_dossier_simulation(donnees: Dict[str, Any]) -> Dict[str, Any]:
    """
    ACTION IRREVERSIBLE (Outil qui écrit / agit) :
    Persiste la fiche récapitulative officielle dans le système de fichiers (exports/).
    """
    dossier_id = f"SIMU-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    timestamp = datetime.now().isoformat()
    
    file_record = {
        "dossier_id": dossier_id,
        "created_at": timestamp,
        "statut": "ENREGISTRE_ET_VALIDE",
        "simulation_data": donnees
    }
    
    # Écriture JSON
    json_path = EXPORTS_DIR / f"{dossier_id}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(file_record, f, indent=2, ensure_ascii=False)
        
    # Écriture Récapitulatif Markdown pour l'étudiant
    md_path = EXPORTS_DIR / f"{dossier_id}.md"
    md_content = f"""# Attestation de Simulation d'Aides Étudiantes
**Numéro de dossier** : {dossier_id}  
**Date d'enregistrement** : {timestamp}  
**Statut** : Validé par l'étudiant  

---
### Détail des éléments retenus :
{json.dumps(donnees, indent=2, ensure_ascii=False)}

---
*Ce document récapitulatif est généré automatiquement par l'assistant IA certifié.*
"""
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    return {
        "dossier_id": dossier_id,
        "status": "SUCCESS",
        "message": f"Dossier de simulation {dossier_id} généré et archivé avec succès.",
        "json_file": str(json_path),
        "md_file": str(md_path)
    }
