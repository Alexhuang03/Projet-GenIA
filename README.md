# Un système génératif qui se mesure : Assistant Aides Étudiantes & CROUS
**Projet Mineur IA Générative 2026 · Dr. Issam Falih**  
**Parcours : Texte · Chapitres 4 à 6**

---

## 1. Présentation du Projet et Cas d'Usage

Ce projet met en œuvre un assistant intelligent dédié à l'information, au calcul et à l'orientation pour les aides étudiantes en France (Bourses CROUS sur critères sociaux, Logement universitaire, Garantie Visale, APL / CAF, Aides d'urgence FNAU, Santé et Mobilité).

Conformément à la consigne du cours, le système est construit par **niveaux successifs**, où chaque niveau prouve rigoureusement ce qu'il apporte, ce qu'il coûte et où il échoue, mesuré sur un protocole de test standardisé :

```
Niveau 0 (LLM seul)  --->  Niveau 1 (RAG Hybride)  --->  Niveau 2 (Agent Outillé)  --->  Niveau 3 (Extension)
(Baseline à battre)       (Sources + Abstention)        (Actions + Contrôle Code)       (Planification / HyDE)
```

---

## 2. Architecture par Niveaux

### • Niveau 0 : LLM seul (Baseline)
- **Principe** : Un prompt système soigné définissant le rôle de l'assistant étudiant, mais **sans aucun document externe** et **sans outil de calcul**.
- **Comportement mesuré** : Réponses plausibles mais souvent imprécises sur les barèmes exacts (montants, distances, seuils kilométriques), aucune citation de source officielle et incapacité à s'abstenir formellement ou à accomplir une démarche.

### • Niveau 1 : RAG (Retrieval-Augmented Generation)
- **Découpage (Chunking)** : Segmentation par paragraphes et sections Markdown préservant la hiérarchie des titres (`[Nom de Section]`).
  - *Justification* : Les règles administratives associent strictement les chiffres (montant d'un échelon, seuil de distance) au titre de la condition.
- **Recherche Hybride (Dense + BM25)** :
  - **Dense TF-IDF normalisé avec n-grammes (1, 2)** pour capturer les expressions composées ("points de charge", "échelon 0bis", "dossier social étudiant").
  - **BM25 Okapi** pour la correspondance lexicale stricte des valeurs numériques.
- **Citations et Abstention** :
  - Chaque affirmation cite explicitement son document source : `[Source: nom_fichier.md]`.
  - **Groundedness & Détection d'abstention** : Si le score de pertinence est insuffisant ou si la question ne relève pas du corpus, le modèle s'abstient formellement au lieu d'halluciner.

### • Niveau 2 : Agent outillé
- **Conception SANS framework** : La boucle ReAct, l'ordonnancement des outils et la gestion des observations sont développés en pur Python, sans dépendance à LangChain ou LangGraph.
- **Registre des 3 outils (Schéma JSON)** :
  1. `calculer_points_charge` *(Lecture / Calcul)* : Calcule la distance kilométrique et les points fratrie.
  2. `estimer_bourse_et_apl` *(Lecture / Simulation)* : Détermine l'échelon indicatif et l'aide mensuelle.
  3. `sauvegarder_dossier_etudiant` *(Action / Écriture irréversible)* : Exporte et archive la synthèse au format JSON et Markdown dans `exports/`.
- **Règles métier vérifiées par du code** : Les barèmes kilométriques (<30km = 0pt, 30-249km = 1pt, >=250km = 2pts) et les plafonds sont garantis par le code Python et non confiés au LLM.
- **Validation humaine obligatoire** : Toute action irréversible (`sauvegarder_dossier_etudiant`) interrompt la boucle et exige la confirmation explicite de l'utilisateur (`WAITING_CONFIRMATION`).

---

## 3. Protocole de Test et Évaluation (`eval.py`)

Le jeu de test `data/tests.jsonl` contient **40 cas rigoureusement calibrés** :
- **20 cas "Réponse dans les documents"** : Vérifie l'exactitude de la réponse et la présence de la citation de source.
- **5 cas "Réponse absente des documents"** : Vérifie l'abstention formelle du système sans hallucination.
- **10 cas "Tâches en plusieurs étapes"** : État final (points de charge, échelon, archivage) validé par du code strict, mesuré avec la métrique **pass^3** (3 exécutions consécutives réussies).
- **5 cas "Demandes ambiguës ou hors sujet"** : Demande de clarification ou refus poli.

### Tableau comparatif des résultats (généré par `python eval.py`)

| Niveau | Recall@5 | Exactitude | Abstention | Succès tâches | pass^3 | Tokens / req | Latence |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **0 · LLM seul** | — | 5.0% | 0.0% | — | — | 86.1 | 0.000s |
| **1 · RAG** | 100.0% (MRR: 1.00) | 100.0% | 100.0% | — | — | 517.5 | 0.001s |
| **2 · Agent** | 100.0% | 95.0% | 100.0% | 100.0% | 100.0% | 437.7 | 0.002s |

---

## 4. Installation et Prise en Main

### Prérequis
- Python 3.10 ou supérieur.
- Aucun GPU n'est requis.
- Fonctionne immédiatement hors-ligne grâce au mode Mock déterministe intégré, ou avec des clés API en ligne (Gemini, Groq, OpenAI).

### 1. Installation des dépendances
```bash
pip install -r requirements.txt
```

### 2. Configuration des clés (optionnel)
Copiez `.env.example` en `.env` si vous souhaitez utiliser une clé d'API réelle :
```bash
cp .env.example .env
```

### 3. Reproduire le tableau d'évaluation (commande unique)
```bash
python eval.py
```

### 4. Lancer l'interface utilisateur Streamlit
```bash
streamlit run app.py
```

---

## 5. Structure du Dépôt

```
Projet/
├── data/
│   ├── corpus/                # Documents réglementaires officiels (.md)
│   ├── tests.jsonl            # Protocole des 40 cas de test calibrés
│   └── traces.jsonl           # Traces de chaque exécution (tokens, étapes, durée)
├── src/
│   ├── baseline/
│   │   └── level0_llm.py      # Niveau 0 : LLM seul sans documents ni outils
│   ├── rag/
│   │   ├── chunking.py        # Découpage avec métadonnées de section
│   │   ├── retriever.py       # Recherche hybride Dense + BM25 avec seuil d'abstention
│   │   └── engine.py          # Niveau 1 : RAG avec citations et abstention
│   ├── agent/
│   │   ├── business_rules.py  # Règles métier strictes vérifiées par le code
│   │   ├── tools.py           # Schémas JSON des 3 outils classés par effet
│   │   └── loop.py            # Boucle ReAct bornée SANS framework avec validation
│   ├── config.py              # Chemins et paramètres globaux
│   ├── llm_client.py          # Client multi-providers (Mock, Gemini, Groq, OpenAI)
│   └── tracker.py             # Enregistrement des traces JSONL
├── exports/                   # Dossiers étudiants générés par l'agent
├── app.py                     # Interface interactive Streamlit
├── eval.py                    # Script d'évaluation unifié
├── requirements.txt           # Dépendances Python
├── .env.example               # Modèle de configuration des variables d'environnement
└── README.md                  # Documentation du projet
```
