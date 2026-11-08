# Un système génératif qui se mesure : Assistant Aides Étudiantes & CROUS
**Projet Mineur IA Générative 2026 · Dr. Issam Falih**  
**Parcours : Texte · SEMAINE 1 (2 – 8 nov.)**

---

## 1. Objectif et Règle du Jeu de la Semaine 1

> *« Le projet n’est pas jugé sur le nombre de techniques empilées, mais sur votre capacité à montrer, mesures à l’appui, ce que chaque technique apporte, ce qu’elle coûte et où elle échoue. Commencer simple, et ne passer au niveau suivant que lorsqu’une mesure montre qu’il aide. »*  
> — Dr. Issam Falih

Conformément au calendrier officiel, la **Semaine 1** établit les fondations rigoureuses du projet :
1. **Le Thème** et le cas d'usage retenus.
2. **Le Corpus** documentaire de référence.
3. **Le Jeu de test standardisé** de 40 cas (`data/tests.jsonl`).
4. **Le Niveau 0 (LLM seul)** : la référence à battre, avec son évaluation chiffrée.

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

---

## 5. Niveau 0 : LLM seul (Baseline de Référence)

### Conception
Le Niveau 0 s'appuie sur un **prompt système soigné** définissant le rôle de l'assistant étudiant, mais **sans accès aux documents officiels et sans outils**.

### Résultats Mesurés (`python eval.py`)

| Niveau | Recall@5 | Exactitude | Abstention | Succès tâches | pass^3 | Tokens / req | Latence |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **0 · LLM seul** | — | **5.0%** | **0.0%** | — | — | **86.1** | **0.001s** |
| **1 · RAG** | … | … | … | — | — | … | … |
| **2 · Agent** | … | … | … | … | … | … | … |
| **3 · Extension** | … | … | … | … | … | … | … |

### Analyse d'échec du Niveau 0 (Justification du passage au RAG en Semaine 2)
1. **Faible exactitude (5.0%)** : Le LLM seul donne des approximations plausibles mais fausses sur les montants exacts (ex: il ignore le montant exact de 1 454 € pour l'échelon 0bis ou de 3 070 € pour l'aide d'urgence).
2. **Absence totale d'abstention (0.0%)** : Lorsqu'on l'interroge sur une subvention fictive de voilier, il tente d'inventer une réponse au lieu de s'abstenir formellement.
3. **Sources absentes** : Aucune affirmation ne peut être vérifiée par l'étudiant.

**Conclusion de la Semaine 1** : Ces faiblesses quantifiées justifient pleinement l'introduction du RAG (Niveau 1) dès la Semaine 2.

---

## 6. Utilisation

### 1. Installation
```bash
pip install -r requirements.txt
```

### 2. Reproduire l'évaluation de la Semaine 1
```bash
python eval.py
```

### 3. Lancer l'interface Streamlit (Niveau 0)
```bash
streamlit run app.py
```

*(Note : Les développements des semaines 2 et 3 sont conservés et sauvegardés sur la branche `avance-semaines-2-3`).*
