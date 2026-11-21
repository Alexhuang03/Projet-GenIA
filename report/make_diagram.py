"""Génère le schéma d'architecture du rapport (report/architecture.png)."""
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

OUT = Path(__file__).resolve().parent / "architecture.png"
BLUE, GREEN, ORANGE, GREY, RED, WHITE = "#dbe8f6", "#dff0df", "#fbe8d3", "#eeeeee", "#f6d6d6", "#fafafa"


def box(ax, x, y, w, h, text, color, size=8.5, bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.008,rounding_size=0.015",
                                fc=color, ec="#555555", lw=0.9))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=size,
            fontweight="bold" if bold else "normal")


def arrow(ax, x1, y1, x2, y2):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color="#444444", lw=1.0, shrinkA=1, shrinkB=1))


def note(ax, x, y, text, ha="left"):
    ax.text(x, y, text, fontsize=7, color="#333333", ha=ha, va="center", style="italic")


fig, ax = plt.subplots(figsize=(11, 5), dpi=200)
ax.set_xlim(-0.01, 1.02)
ax.set_ylim(0, 1)
ax.axis("off")

# Ligne du haut : utilisateur et niveaux
box(ax, 0.00, 0.82, 0.14, 0.12, "Étudiant\n(Streamlit)", GREY, bold=True)
box(ax, 0.20, 0.82, 0.17, 0.12, "Niveau 0\nLLM seul", BLUE, bold=True)
box(ax, 0.40, 0.82, 0.17, 0.12, "Niveau 1\nRAG", BLUE, bold=True)
box(ax, 0.61, 0.82, 0.17, 0.12, "Niveau 2\nAgent ReAct", BLUE, bold=True)
box(ax, 0.81, 0.82, 0.19, 0.12, "Niveau 3 (extension)\nAgent ReWOO", BLUE, bold=True)
arrow(ax, 0.14, 0.88, 0.20, 0.88)
note(ax, 0.145, 0.95, "choix du niveau")

# LLM
box(ax, 0.20, 0.60, 0.37, 0.12, "LLM local qwen2.5:7b via Ollama\n(température 0, appel d'outils natif)", ORANGE)
arrow(ax, 0.285, 0.82, 0.285, 0.72)
arrow(ax, 0.485, 0.82, 0.485, 0.72)

# Recherche et corpus
box(ax, 0.20, 0.31, 0.37, 0.17,
    "Recherche hybride, top-5\nBM25 + embeddings bge-m3, fusion RRF\n40 passages découpés par section", GREEN)
box(ax, 0.20, 0.05, 0.37, 0.15,
    "Corpus : 6 fiches Markdown\nbourses, logement / Visale, APL,\nurgence, transport / santé, mobilité", GREEN)
arrow(ax, 0.385, 0.20, 0.385, 0.31)
arrow(ax, 0.30, 0.48, 0.30, 0.60)
note(ax, 0.31, 0.54, "passages injectés dans le prompt (niveau 1)")

# Exécuteur d'outils
box(ax, 0.61, 0.28, 0.39, 0.44, "", WHITE)
ax.text(0.805, 0.69, "Exécuteur d'outils (écrit sans framework)", ha="center", fontsize=8.2, fontweight="bold")
box(ax, 0.625, 0.565, 0.36, 0.085, "READ : rechercher_documents", GREEN, size=8)
box(ax, 0.625, 0.455, 0.36, 0.09, "COMPUTE : points de charge, échelon, APL\nrègles métier codées, sources citées", ORANGE, size=7.6)
box(ax, 0.625, 0.30, 0.36, 0.135, "WRITE : enregistrer_simulation\nvérification préalable puis\nCONFIRMATION de l'étudiant", RED, size=7.6)
arrow(ax, 0.695, 0.82, 0.695, 0.72)
arrow(ax, 0.905, 0.82, 0.905, 0.72)
arrow(ax, 0.625, 0.607, 0.57, 0.43)
note(ax, 0.805, 0.765, "appels d'outils ; boucle bornée (8 appels LLM, 30 000 tokens)", ha="center")

box(ax, 0.61, 0.05, 0.39, 0.13, "exports/ : dossiers de simulation\nécrits seulement après confirmation", GREY, size=8)
arrow(ax, 0.805, 0.30, 0.805, 0.18)

# Traces et évaluation
box(ax, 0.00, 0.05, 0.14, 0.17, "Traces JSONL\n+ eval.py\n40 cas, pass^3", GREY)
arrow(ax, 0.07, 0.82, 0.07, 0.22)
note(ax, 0.075, 0.52, "chaque\nrequête")

plt.savefig(OUT, bbox_inches="tight", facecolor="white")
print(f"Schéma écrit : {OUT}")
