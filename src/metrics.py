"""
Fonctions de mesure partagées par eval.py (et réutilisables par les niveaux suivants).
Toutes les décisions sont automatiques et déterministes : pas de jugement « à l'œil ».
"""
import re
import unicodedata
from typing import Iterable, List, Set

# Formulations d'abstention reconnues (les mêmes pour tous les niveaux, pour comparer à
# critère égal). La première est la phrase imposée au Niveau 1 ; les autres couvrent les
# façons naturelles dont un LLM sans consigne dit qu'il ne sait pas.
ABSTENTION_PATTERNS = [
    "je ne dispose pas de cette information",
    "ne dispose pas d'information",
    "je ne dispose pas d'informations",
    "je n'ai pas d'information",
    "je n'ai pas cette information",
    "je n'ai pas trouve",
    "aucune information",
    "je ne sais pas",
    "je ne connais pas",
    "n'existe pas",
    "ne figure pas",
    "pas mentionne",
    "pas en mesure de",
    "hors de mon champ",
]


def _fold(text: str) -> str:
    """Minuscules, sans accents, espaces insécables normalisés, espaces internes aux nombres retirés
    (« 1 454 € » et « 1454 € » deviennent identiques), apostrophes typographiques unifiées."""
    text = unicodedata.normalize("NFKD", text.lower())
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.replace("’", "'").replace(" ", " ").replace(" ", " ")
    text = re.sub(r"(?<=\d) (?=\d{3}\b)", "", text)
    return re.sub(r"\s+", " ", text)


def contains_keyword(text: str, keywords: Iterable[str]) -> bool:
    """Vrai si au moins un mot-clé attendu apparaît comme mot entier (« 36 » ne matche pas « 360 »)."""
    folded = _fold(text)
    for kw in keywords:
        k = _fold(kw)
        if re.search(rf"(?<![\w]){re.escape(k)}(?![\w])", folded):
            return True
    return False


def is_abstention(text: str) -> bool:
    folded = _fold(text)
    return any(_fold(p) in folded for p in ABSTENTION_PATTERNS)


REFUSAL_PATTERNS = [
    "je ne peux pas", "je ne suis pas en mesure", "ne peux pas vous", "pas autorise", "illegal",
    "je suis specialise", "je suis un assistant", "je suis concu", "uniquement", "en dehors de mon",
    "hors de mon", "ne fait pas partie", "je suis desole", "ne permet pas",
]


def fold(text: str) -> str:
    return _fold(text)


def is_refusal_or_clarification(text: str) -> bool:
    """Refus explicite, ou question adressée à l'étudiant (« pouvez-vous préciser… ? »).
    Un simple « ? » ne suffit pas : une blague peut en contenir un."""
    folded = _fold(text)
    asks_user = any(s.strip().endswith("?") and re.search(r"\b(vous|tu|votre|vos|ton|tes)\b", s)
                    for s in re.findall(r"[^.!?]+[.!?]+", folded))
    return asks_user or any(p in folded for p in REFUSAL_PATTERNS)


def numbers_in(text: str) -> Set[str]:
    """Nombres d'au moins deux chiffres, normalisés (les noms de fichiers cités sont retirés)."""
    text = re.sub(r"\[\s*source\s*:[^\]]*\]|[\w-]+\.md", " ", _fold(text))
    return {n.replace(",", ".") for n in re.findall(r"\d+(?:[.,]\d+)?", text) if sum(c.isdigit() for c in n) >= 2}


def is_faithful(answer: str, evidence: str) -> bool:
    """Fidélité (règle) : tout nombre de la réponse figure dans les passages, les résultats d'outils
    ou la question. Détecte les montants inventés, pas les reformulations fausses sans chiffre."""
    return numbers_in(answer) <= numbers_in(evidence)


def mean(values: List[float]) -> float:
    return sum(values) / len(values) if values else 0.0
