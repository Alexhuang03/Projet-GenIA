"""
Définition et registre des outils de l'agent
Chaque outil est décrit par un schéma JSON conforme à la spécification des API génératives.
Les outils sont classés par effet :
- Lecture / Calcul : sans effet de bord
- Action / Écriture : mutation d'état ou écriture disque, requérant une validation humaine
"""
from typing import Dict, Any, List, Callable
from src.agent.business_rules import (
    calculer_points_charge,
    estimer_bourse_et_apl,
    enregistrer_dossier_simulation
)

TOOLS_REGISTRY: Dict[str, Dict[str, Any]] = {
    "calculer_points_charge": {
        "name": "calculer_points_charge",
        "description": "Calcule les points de charge officiels du CROUS pour la bourse selon la distance en km et la composition de la fratrie.",
        "effect": "READ_ONLY",
        "requires_confirmation": False,
        "function": calculer_points_charge,
        "parameters": {
            "type": "object",
            "properties": {
                "distance_km": {
                    "type": "number",
                    "description": "Distance en kilomètres entre le domicile familial et l'établissement d'études."
                },
                "freres_superieur": {
                    "type": "integer",
                    "description": "Nombre de frères ou sœurs également étudiants dans l'enseignement supérieur (2 points par frère/sœur).",
                    "default": 0
                },
                "freres_charge": {
                    "type": "integer",
                    "description": "Nombre d'autres frères ou sœurs à charge dans le secondaire ou mineurs (1 point par frère/sœur).",
                    "default": 0
                }
            },
            "required": ["distance_km"]
        }
    },
    
    "estimer_bourse_et_apl": {
        "name": "estimer_bourse_et_apl",
        "description": "Estime l'échelon de bourse sur critères sociaux et les droits APL mensuels à partir des points de charge, du revenu fiscal et éventuellement du loyer.",
        "effect": "READ_ONLY",
        "requires_confirmation": False,
        "function": estimer_bourse_et_apl,
        "parameters": {
            "type": "object",
            "properties": {
                "points_charge": {
                    "type": "integer",
                    "description": "Nombre total de points de charge calculé précédemment."
                },
                "revenu_fiscal": {
                    "type": "number",
                    "description": "Revenu Brut Global / Revenu Fiscal de Référence N-2 de l'avis d'imposition familial en euros."
                },
                "loyer": {
                    "type": "number",
                    "description": "Montant mensuel du loyer hors charges en euros (facultatif).",
                    "default": None
                }
            },
            "required": ["points_charge", "revenu_fiscal"]
        }
    },
    
    "sauvegarder_dossier_etudiant": {
        "name": "sauvegarder_dossier_etudiant",
        "description": "Action irréversible qui génère et enregistre définitivement l'attestation officielle de simulation au format JSON et Markdown dans le système d'archivage.",
        "effect": "STATE_MUTATION",
        "requires_confirmation": True,
        "function": enregistrer_dossier_simulation,
        "parameters": {
            "type": "object",
            "properties": {
                "donnees": {
                    "type": "object",
                    "description": "Dictionnaire complet contenant les résultats de la simulation (points, échelon, montants)."
                }
            },
            "required": ["donnees"]
        }
    }
}


def get_tools_schema() -> List[Dict[str, Any]]:
    """Retourne la liste des schémas JSON pour le LLM."""
    schemas = []
    for tool_name, tool_data in TOOLS_REGISTRY.items():
        schemas.append({
            "name": tool_data["name"],
            "description": tool_data["description"],
            "parameters": tool_data["parameters"]
        })
    return schemas
