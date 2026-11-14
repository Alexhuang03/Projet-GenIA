# Un système génératif qui se mesure : Assistant Aides Étudiantes & CROUS
**Projet Mineur IA Générative 2026 · Dr. Issam Falih**  
**Parcours : Texte · Avancement : Semaine 2 (9 – 15 nov.) — Niveaux 0 et 1**

---

## 1. Objectif et calendrier

> *« Le projet n’est pas jugé sur le nombre de techniques empilées, mais sur votre capacité à montrer, mesures à l’appui, ce que chaque technique apporte, ce qu’elle coûte et où elle échoue. Commencer simple, et ne passer au niveau suivant que lorsqu’une mesure montre qu’il aide. »*  
> — Dr. Issam Falih

| Semaine | Contenu | État |
|:---|:---|:---:|
| S1 (2 – 8 nov.) | Thème, corpus, jeu de test de 40 cas, Niveau 0 (LLM seul) | ✅ |
| S2 (9 – 15 nov.) | Niveau 1 : RAG, sources citées, abstention | ✅ |
| S3 (16 – 22 nov.) | Niveau 2 : agent, confirmation des actions, traces, pass^3 | ⏳ |
| S4 (23 – 30 nov.) | Extension, analyse des échecs, rapport et vidéo | ⏳ |

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

### Résultats mesurés (`python eval.py`)
LLM `ollama:qwen2.5:7b`, température 0, 20 questions dans les documents et 5 hors documents. Le détail de chaque cas (réponse, passages, citations) est dans `results/eval_*.json`.

| Niveau | Recall@5 (doc / passage) | Exactitude | Abstention | Fausses abst. | Citation correcte | Source inventée | Succès tâches | pass^3 | Tokens / req | Latence |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **0 · LLM seul** | — | 5.0% | 20.0% | 0.0% | — | — | — | — | 253 | 4.29s |
| **1 · RAG** | 100.0% / 100.0% | **100.0%** | **100.0%** | 0.0% | 95.0% | 0.0% | — | — | 1225 | 5.44s |
| **2 · Agent** | … | … | … | … | … | … | … | … | … | … |
| **3 · Extension** | … | … | … | … | … | … | … | … | … | … |

Définitions :
- **Recall@5 doc** : le fichier attendu figure parmi les 5 passages récupérés.
- **Recall@5 passage** : un des 5 passages contient la réponse attendue.
- **Exactitude** : la réponse contient le fait attendu et ne s'abstient pas.
- **Fausses abst.** : abstentions sur des questions qui ont une réponse dans le corpus.
- **Citation correcte** : la réponse cite le bon fichier.
- **Source inventée** : la réponse cite un fichier qui n'a pas été fourni.

**Ablation du retriever** (sans LLM, 20 questions dans les documents) :

| Retriever | Recall@1 (doc) | Recall@5 (doc) | Recall@5 (passage) |
|:---|:---:|:---:|:---:|
| BM25 | 100.0% | 100.0% | 100.0% |
| Dense (bge-m3) | 95.0% | 100.0% | 100.0% |
| Hybride (RRF) | 100.0% | 100.0% | 100.0% |

### Ce que le RAG apporte, ce qu'il coûte, où il échoue
- **Apport** : l'exactitude passe de 5 % à 100 % et l'abstention de 20 % à 100 %, sans aucune fausse abstention. Les réponses citent leur source et aucune source n'est inventée.
- **Coût** : environ **4,8 fois plus de tokens** par requête (1 225 contre 253, à cause des 5 passages injectés) et **+1,2 s** de latence (5,4 s contre 4,3 s, sur GPU local).
- **Échec observé** : sur doc_05, le modèle écrit `Source: …` sans les crochets. Le format n'est donc pas toujours respecté, et la citation n'est pas reconnue (95 % de citations correctes).
- **Limite du protocole, à dire clairement** : les scores de 100 % montrent surtout que **le jeu de test est saturé** pour ce niveau. Les 20 questions reprennent presque mot pour mot le vocabulaire des fiches, et le corpus ne compte que 40 passages. Le Recall@5 au niveau document est presque garanti avec 6 fichiers, et l'ablation ne départage pas BM25 et l'hybride. Les questions hors documents sont, elles, très éloignées du domaine (astronautes, lamas). Il reste à mesurer des **paraphrases**, des questions qui croisent **plusieurs fiches** et des questions **proches du domaine mais absentes du corpus** (ex. « bourse au mérite », « prime d'activité »), qui sont le vrai test de l'abstention.

---

## 7. Utilisation

### Installation
```bash
pip install -r requirements.txt
# LLM local (Ollama, https://ollama.com) :
ollama pull qwen2.5:7b    # génération
ollama pull bge-m3        # embeddings du retriever dense
```
Un autre fournisseur (Groq, Gemini, OpenAI) peut être choisi via `LLM_PROVIDER` : voir `.env.example`.

### Reproduire l'évaluation
```bash
python eval.py                          # niveaux 0 et 1, retriever hybride
python eval.py --levels 1 --retriever bm25
python eval.py --limit 3                # essai rapide
```
Les résultats sont écrits dans `results/latest.md` et `results/eval_<horodatage>.json`, et chaque requête est tracée dans `data/traces.jsonl`.

### Interface Streamlit (Niveaux 0 et 1)
```bash
streamlit run app.py
```
L'interface affiche les passages récupérés, les sources citées et la trace de chaque requête.
