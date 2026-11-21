# Un système génératif qui se mesure : Assistant Aides Étudiantes & CROUS
**Projet Mineur IA Générative 2026 · Dr. Issam Falih**  
**Parcours : Texte · Niveaux 0 à 3**

---

## 1. Objectif et calendrier

> *« Le projet n’est pas jugé sur le nombre de techniques empilées, mais sur votre capacité à montrer, mesures à l’appui, ce que chaque technique apporte, ce qu’elle coûte et où elle échoue. Commencer simple, et ne passer au niveau suivant que lorsqu’une mesure montre qu’il aide. »*  
> — Dr. Issam Falih

| Semaine | Contenu | État |
|:---|:---|:---:|
| S1 (2 – 8 nov.) | Thème, corpus, jeu de test de 40 cas, Niveau 0 (LLM seul) | ✅ |
| S2 (9 – 15 nov.) | Niveau 1 : RAG, sources citées, abstention | ✅ |
| S3 (16 – 22 nov.) | Niveau 2 : agent, confirmation des actions, traces, pass^3 | ✅ |
| S4 (23 – 30 nov.) | Extension ReWOO, analyse des échecs, rapport ✅ · vidéo à enregistrer | ⏳ |

---

## 2. Thème Retenu : Assistant Aides Étudiantes & CROUS

Le système est conçu pour guider les étudiants dans l'évaluation et l'obtention de leurs aides :
- Bourses de l'enseignement supérieur sur critères sociaux (BCS) gérées par le CROUS.
- Logement en résidence universitaire et cautionnement gratuit **Visale** (Action Logement).
- Aide Personnalisée au Logement (**APL**) gérée par la CAF.
- Fonds National d'Aide d'Urgence (**FNAU** / ASAA) pour les situations de rupture.
- Aides à la mobilité (Master 1 000 €, Parcoursup 500 €, mobilité internationale 400 €/mois).
- Restauration (repas à 1 €) et santé étudiante (Santé Psy Étudiant).

---

## 3. Le Corpus Documentaire (`data/corpus/`)

Le corpus est composé de 6 fiches officielles au format Markdown :
- `01_bourses_crous_criteres_sociaux.md` : conditions, barème kilométrique, fratrie, échelons 0bis à 7, plafonds RFR.
- `02_logement_crous_et_visale.md` : résidences universitaires, indice social, garantie Visale (36 mensualités), avance Loca-Pass (1 200 € max).
- `03_aide_personnalisee_logement_apl.md` : éligibilité CAF, non-imposition des bourses, impact direct sur les prestations des parents.
- `04_aides_urgence_crous_fnausu.md` : aide d'urgence ponctuelle (plafond de 3 070 €/an), allocation annuelle, repas à 1 € pour non-boursiers précaires.
- `05_aides_transport_restauration_sante.md` : tarification des repas (3,30 € / 1 €), forfait Imagine R (374,40 €), 8 séances gratuites chez le psychologue.
- `06_aide_mobilite_master_parcoursup.md` : aide Master 1 000 €, Parcoursup 500 €, aide mobilité internationale 400 €/mois.

---

## 4. Protocole de Test et Jeu d'Évaluation (`data/tests.jsonl`)

Un protocole rigoureux de **40 cas de test** a été fixé dès cette première semaine, conforme aux 4 catégories du barème :
- **20 cas "Réponse dans les documents"** : questions précises sur les barèmes, montants et conditions.
- **5 cas "Réponse absente des documents"** : questions hors sujet (ex: achat de voilier, élevage de lamas) pour mesurer l'abstention.
- **10 cas "Tâches en plusieurs étapes"** : cas de calcul et de simulation d'aides.
- **5 cas "Demandes ambiguës ou hors sujet"** : requêtes vagues ou illégales pour tester le cadrage du modèle.

**Correction du protocole en semaine 2.** Six cas avaient des mots-clés attendus trop permissifs, qui validaient presque n'importe quelle réponse (« 1 », « 8 », « non », « charge », « Master », « boursier »). Ils ont été remplacés par le fait discriminant de la fiche (ex. doc_11 : `epu.lescrous` / « demande en ligne » ; doc_16 : « région académique » ; doc_13 : « 8 séances »). La correspondance se fait désormais sur des mots entiers, sans accents, avec les nombres normalisés (« 1 454 » = « 1454 ») : voir [src/metrics.py](src/metrics.py). Les questions elles-mêmes n'ont pas changé, et le Niveau 0 a été réévalué avec ce protocole.

---

## 5. Niveau 0 : LLM seul (Baseline de Référence)

### Conception
Le Niveau 0 s'appuie sur un **prompt système soigné** définissant le rôle de l'assistant étudiant, mais **sans accès aux documents officiels et sans outils**.

### Niveau 0 : résultats et analyse d'échec
Mesuré avec un vrai LLM local (`qwen2.5:7b` via Ollama, température 0). Les chiffres de la semaine 1 avaient été produits en mode « mock » (réponses écrites à la main), qui n'est plus utilisé pour mesurer : `eval.py` le refuse.

1. **Exactitude de 5 % (1/20)** : le modèle produit des montants plausibles mais faux, par exemple « 1 020,50 € » pour l'échelon 0bis (au lieu de 1 454 €), « 12 mensualités » pour Visale (au lieu de 36), « 29,9… € » pour Imagine R (au lieu de 374,40 €). Il affirme aussi qu'il n'y a « pas de limite d'âge » pour la bourse (alors qu'elle est fixée à moins de 28 ans).
2. **Abstention de 20 % (1/5)** : il invente des réponses, par exemple un formulaire « 2042S » qui dispenserait d'impôts. Le détecteur est strict : deux réponses qui démentent correctement (« le CROUS ne propose pas de subvention pour un voilier ») ne sont pas comptées comme des abstentions. Avec un critère plus souple, le score monterait à 60 % au plus.
3. **Aucune source** : rien n'est vérifiable par l'étudiant.

---

## 6. Niveau 1 : RAG (Semaine 2)

### Conception
| Étape | Choix | Justification |
|:---|:---|:---|
| Découpage | Par section Markdown (H1 > H2 > H3), sections longues recoupées à environ 500 caractères ; chaque passage est préfixé par son chemin de titres → **40 passages** | Une section correspond à une règle (un barème, une condition) : on évite de mélanger deux règles dans un passage. |
| Recherche | **Hybride** : BM25 (lexical) + embeddings `bge-m3` (dense, multilingue), fusionnés par **Reciprocal Rank Fusion** ; top-5 | BM25 capte les termes exacts (« Loca-Pass », « 0bis ») ; le dense capte les reformulations ; RRF ne demande aucun calibrage de scores. |
| Génération | Passages étiquetés `Source: fichier.md`, citation obligatoire `[Source: fichier.md]` | Chaque affirmation devient vérifiable. |
| Contrôle des citations | Les sources citées sont comparées aux passages réellement fournis | Une source inventée est détectée et comptée comme erreur. |
| Abstention | Phrase fixe imposée si les passages ne répondent pas ; **aucune liste de mots-clés « du domaine » codée en dur** | La décision reste mesurable et n'est pas ajustée sur le jeu de test. |

Code : [src/rag/chunking.py](src/rag/chunking.py), [src/rag/retriever.py](src/rag/retriever.py), [src/rag/engine.py](src/rag/engine.py).

### Ce que le RAG apporte, ce qu'il coûte, où il échoue
- **Apport** : l'exactitude passe de 5 % à 100 % et l'abstention de 20 % à 100 %. Aucune source n'est inventée.
- **Coût** : environ 5 fois plus de tokens par requête (1 220 contre 245) et 1,2 s de latence en plus.
- **Échecs** : le format de citation n'est pas toujours respecté (doc_05), et le RAG répond par l'abstention aux demandes vagues ou illégales au lieu de refuser ou de demander une précision (cadrage 0 %).

---

## 7. Niveau 2 : agent outillé (ReAct)

La boucle, l'exécuteur et la validation des actions sont écrits **sans framework** : [src/agent/loop.py](src/agent/loop.py), [src/agent/tools.py](src/agent/tools.py), [src/agent/business_rules.py](src/agent/business_rules.py).

| Outil | Effet | Rôle |
|:---|:---:|:---|
| `rechercher_documents` | READ | Recherche hybride dans le corpus (top-5) |
| `calculer_points_charge` | COMPUTE | Barème de la fiche 01 |
| `estimer_echelon_bourse` | COMPUTE | Échelon indicatif, interpolé depuis les plafonds de la fiche 01 |
| `estimer_aide_logement` | COMPUTE | Fourchette d'APL de la fiche 03 |
| `enregistrer_simulation` | **WRITE** | Écrit le dossier dans `exports/`, **après confirmation** |

Garde-fous assurés par le code :
- boucle bornée à 8 appels LLM et 30 000 tokens ;
- erreurs d'outils renvoyées au modèle ;
- une seule action par tour, pour éviter les valeurs intermédiaires devinées ;
- recherche forcée avant toute abstention ;
- arguments et cohérence vérifiés **avant** de demander la confirmation ; sans confirmation, l'écriture est refusée.

## 8. Niveau 3 : extension ReWOO (planifier puis exécuter)

[src/agent/rewoo.py](src/agent/rewoo.py) corrige le symptôme mesuré au niveau 2. Un appel LLM écrit tout le plan, avec des références entre étapes (`#E1.total_points_charge`). Le code l'exécute, en parallèle pour les étapes indépendantes, et s'arrête avant toute écriture pour demander la confirmation. Un second appel LLM rédige la réponse.

---

## 9. Résultats

Une seule commande reproduit le tableau : `python eval.py` (environ 25 minutes sur GPU portable). LLM `qwen2.5:7b`, 40 cas, tâches en 3 essais à température 0,7.

| Niveau | Recall@5 | MRR | Exactitude | Abstention | Cadrage | Citation correcte | Fidélité | Succès tâches | pass^3 | Appels LLM / req | Tokens / req | Latence |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **0 · LLM seul** | — | — | 5 % | 20 % | 80 % | — | — | — | — | 1,0 | 245 | 4,09 s |
| **1 · RAG** | 100 % | 1,00 | 100 % | 100 % | 0 % | 95 % | 100 % | — | — | 1,0 | 1 220 | 5,25 s |
| **2 · Agent ReAct** | 100 % | 1,00 | 90 % | 100 % | 100 % | 61 % | 100 % | 60 % | 50 % | 2,3 | 3 574 | 9,11 s |
| **3 · ReWOO** | 100 % | 1,00 | 95 % | 100 % | 100 % | 89 % | 100 % | 80 % | 80 % | 2,0 | 2 282 | 8,54 s |

Sur les 10 tâches, ReWOO fait **2,0 appels LLM au lieu de 2,7, 46 % de tokens en moins et 14 % de latence en moins** que ReAct. **Aucune écriture n'a eu lieu sans confirmation.**

Le détail est dans `results/` : `latest.md` (tableaux), `eval_20261121_144514.json` (réponses et contrôles de chaque cas), `traces_20261121_144514.jsonl` (étapes, outils, arguments, tokens et durée de chaque exécution).

### Limites à garder en tête
- **Jeu de test facile pour la recherche** : Recall@5 et MRR sont saturés et ne départagent pas les méthodes.
- **Pas de jeu de développement séparé** : prompts et garde-fous ont été ajustés après avoir observé des cas du jeu de test, donc les niveaux 2 et 3 sont probablement optimistes.
- **Petit échantillon** : l'écart de pass^3 entre ReAct et ReWOO représente 3 tâches sur 10.
- **Mesures par règles** : la fidélité contrôle les nombres, pas le sens des reformulations.
- **Échelon indicatif** : les plafonds intermédiaires sont interpolés, et les montants 2024-2025 restent à revérifier auprès du CROUS avant tout usage réel.
- **Une confirmation ne prouve pas la justesse** : sur task_01, ReWOO propose un dossier faux (4 points au lieu de 5) qu'un étudiant pourrait valider.

L'analyse de cinq échecs est dans le rapport : [report/rapport.pdf](report/rapport.pdf).

---

## 10. Utilisation

### Installation
```bash
pip install -r requirements.txt
# LLM local (Ollama, https://ollama.com) :
ollama pull qwen2.5:7b    # génération et appel d'outils
ollama pull bge-m3        # embeddings du retriever dense
```

### Reproduire l'évaluation
```bash
python eval.py                 # niveaux 0 à 3
python eval.py --levels 2,3    # seulement les agents
python eval.py --limit 2       # essai rapide
```

### Interface Streamlit (niveaux 0 à 3)
```bash
streamlit run app.py
```
L'interface montre la réponse, les sources, les coûts et la trace de chaque exécution, et demande une confirmation avant toute action irréversible.

### Régénérer le rapport
```bash
python report/make_diagram.py
python report/build_report.py   # reprend les chiffres du dernier résultat
```
