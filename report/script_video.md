# Script de la vidéo de démonstration (environ 4 minutes)

**Avant d'enregistrer**

1. Lancer Ollama, puis `streamlit run app.py`.
2. Faire une requête d'essai pour charger le modèle en mémoire (la première réponse est plus lente).
3. Cliquer sur **Réinitialiser** dans la barre latérale.
4. Garder ouverts `results/latest.md` et le dossier `exports/`.

Le sujet impose quatre séquences : **un cas réussi, une abstention, une tâche en plusieurs étapes avec sa trace, une action validée**. Les séquences 3 et 4 se font sur la même demande.

---

## 0. Introduction (20 s)

*À l'écran : l'interface, barre latérale visible.*

> « Voici notre assistant pour les aides étudiantes : bourses CROUS, logement, APL, aides d'urgence et mobilité. Il est construit en quatre niveaux, du LLM seul jusqu'à un agent qui planifie, tous évalués sur les mêmes 40 cas. Tout tourne en local avec Qwen 2.5 via Ollama. »

## 1. Cas réussi : niveau 0 contre niveau 1 (50 s)

*Choisir **Niveau 0**, cliquer sur l'exemple « Question documentaire » (échelon 0bis).*

> « Sans documents, le modèle donne un montant plausible, mais faux ou invérifiable. »

*Choisir **Niveau 1**, cliquer sur le même exemple. Ouvrir la trace.*

> « Avec le RAG, il retrouve la fiche des bourses et répond 1 454 euros en citant sa source. Dans la trace, on voit les cinq passages récupérés, les tokens et la latence. »

## 2. Abstention (30 s)

*Rester au **Niveau 1**, cliquer sur l'exemple « Hors corpus (voilier) ».*

> « On demande une subvention pour un voilier, qui n'existe dans aucune fiche. Le système ne l'invente pas : il dit qu'il ne dispose pas de cette information. »

## 3. Tâche en plusieurs étapes avec sa trace (70 s)

*Choisir **Niveau 3**, cliquer sur l'exemple « Tâche + enregistrement ».*

> « Une vraie tâche : 260 km, deux frères dans le supérieur, un revenu de 12 000 euros. L'étudiant veut ses points de charge, son échelon et son dossier. »

*Ouvrir la trace de la réponse et montrer le tableau des outils.*

> « L'agent a d'abord fait un plan. Il calcule 6 points de charge avec une règle métier écrite en code, pas par le LLM, puis réutilise ce résultat pour estimer l'échelon. Chaque outil, ses arguments et sa durée sont tracés. »

## 4. Action validée (40 s)

*Montrer le message « Action irréversible à confirmer ».*

> « Enregistrer le dossier est irréversible. L'agent s'arrête donc et demande une confirmation : sans elle, le code refuse d'écrire. »

*Cliquer sur **Confirmer l'action**, puis ouvrir le dossier `exports/` et le nouveau fichier.*

> « Après validation, le dossier est écrit, avec les bons points de charge. »

## 5. Résultats et limites (40 s)

*Afficher `results/latest.md`.*

> « Une seule commande, `python eval.py`, reproduit ce tableau. Lisez-le niveau par niveau : ce que chaque technique apporte, ce qu'elle coûte en tokens et en latence, et le pass^3, où les trois essais d'une tâche doivent réussir. »

> « ReWOO, notre extension, utilise 2 appels LLM par tâche contre 2,7 pour ReAct, 46 % de tokens en moins, avec un pass^3 de 80 % contre 50 %. Sa principale limite : le planificateur peut recopier une valeur de son exemple, et un étudiant pourrait alors valider un dossier faux. »

---

**Si le modèle se trompe pendant l'enregistrement :** relancer la prise. Les niveaux 0 à 3 de l'interface tournent à température 0, donc une même demande donne en général la même réponse.
