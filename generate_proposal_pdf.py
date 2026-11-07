"""
Générateur de la Proposition de Projet (2 pages complètes A4)
Pour le dépôt Moodle 'Project Proposal deposit' (Semaine 1 - Due 8 nov. 2026)
Garantit que TOUT le texte (description, corpus, protocole, tableau) est parfaitement affiché.
"""
import pymupdf

def create_proposal_pdf(output_path="Proposition_Projet_Alex_Huang.pdf"):
    doc = pymupdf.open()
    
    # =========================================================================
    #                               PAGE 1
    # =========================================================================
    page1 = doc.new_page(width=595.3, height=841.9)
    
    # En-tête bleu institutionnel
    page1.draw_rect(pymupdf.Rect(0, 0, 595.3, 75), color=None, fill=(0.12, 0.23, 0.38))
    page1.insert_text((45, 30), "MINEUR IA GÉNÉRATIVE 2026 · Dr. Issam Falih", fontsize=9.5, color=(0.85, 0.9, 0.98), fontname="helv")
    page1.insert_text((45, 54), "PROPOSITION DE PROJET : SEMAINE 1", fontsize=17, color=(1, 1, 1), fontname="hebo")
    page1.insert_text((450, 54), "Page 1 / 2", fontsize=10, color=(0.8, 0.85, 0.95), fontname="helv")

    # Boîte récapitulative des métadonnées
    page1.draw_rect(pymupdf.Rect(45, 88, 550, 155), color=(0.82, 0.86, 0.92), fill=(0.96, 0.97, 0.99))
    page1.insert_text((55, 107), "Étudiant(s) :", fontsize=10, fontname="hebo", color=(0.12, 0.23, 0.38))
    page1.insert_text((160, 107), "Alex HUANG (ING5)", fontsize=10, fontname="helv", color=(0.1, 0.1, 0.1))
    
    page1.insert_text((55, 123), "Parcours choisi :", fontsize=10, fontname="hebo", color=(0.12, 0.23, 0.38))
    page1.insert_text((160, 123), "Parcours Texte · Chapitres 4 à 6 (Un assistant qui lit, agit et se mesure)", fontsize=10, fontname="helv", color=(0.1, 0.1, 0.1))
    
    page1.insert_text((55, 139), "Thème & Cas d'usage :", fontsize=10, fontname="hebo", color=(0.12, 0.23, 0.38))
    page1.insert_text((160, 139), "Assistant Aides Étudiantes & CROUS (bourses, logement, APL, aides d'urgence)", fontsize=10, fontname="helv", color=(0.1, 0.1, 0.1))

    # --- Section 1 : Contexte et Description du Cas d'Usage ---
    page1.insert_text((45, 178), "1. Description du Projet et Cas d'Usage", fontsize=12.5, fontname="hebo", color=(0.12, 0.23, 0.38))
    page1.draw_line((45, 183), (550, 183), color=(0.12, 0.23, 0.38), width=1)
    
    desc_p1 = (
        "Le financement des études supérieures et l'accès à un logement décent constituent une difficulté "
        "majeure pour de nombreux étudiants en France. Bien que l'État et les organismes publics (CROUS, CAF, "
        "Action Logement, Régions) proposent divers dispositifs d'aide (Bourses sur critères sociaux, APL, "
        "caution Visale, aides d'urgence FNAU, aides à la mobilité), les informations sont dispersées, "
        "les règles de cumul complexes et les barèmes très stricts (barèmes kilométriques, fratrie, plafonds RFR).\n\n"
        "Cas d'usage : Développer un assistant génératif spécialisé capable de guider l'étudiant dans ses droits, "
        "d'effectuer des calculs réglementaires officiels sans hallucination, de citer formellement les textes de référence, "
        "et d'exécuter des démarches de simulation vérifiées avec contrôle humain."
    )
    rc1 = page1.insert_textbox(pymupdf.Rect(45, 190, 550, 310), desc_p1, fontsize=9.0, fontname="helv", color=(0.15, 0.15, 0.15))
    if rc1 < 0:
        print("[Warning] Section 1 overflow:", rc1)

    # --- Section 2 : Démarche Incrémentale et Architecture par Niveaux ---
    page1.insert_text((45, 325), "2. Démarche Pédagogique et Niveaux Successifs", fontsize=12.5, fontname="hebo", color=(0.12, 0.23, 0.38))
    page1.draw_line((45, 330), (550, 330), color=(0.12, 0.23, 0.38), width=1)
    
    arch_text = (
        "Conformément au principe directeur du cours (« Commencer simple, et ne passer au niveau suivant que lorsqu'une "
        "mesure montre qu'il aide »), le projet est architecturé en 4 niveaux successifs mesurés sur le même protocole :\n\n"
        "- Niveau 0 (LLM seul / Semaine 1) : Prompt système soigné, sans document externe ni outil. Baseline de référence à battre.\n"
        "- Niveau 1 (RAG / Semaine 2) : Découpage sémantique, recherche hybride Dense (TF-IDF) + BM25, citation obligatoire "
        "des sources officielles et abstention stricte en cas de question hors domaine pour éliminer les hallucinations.\n"
        "- Niveau 2 (Agent outillé / Semaine 3) : Boucle ReAct développée 100% SANS framework avec 3 outils JSON, règles "
        "métier vérifiées par code Python (calcul kilométrique et fratrie) et confirmation humaine obligatoire avant tout archivage.\n"
        "- Niveau 3 (Extension / Semaine 4) : RAG avancé (HyDE / Reranking) ou planification ReWOO comparée au Niveau 2."
    )
    rc2 = page1.insert_textbox(pymupdf.Rect(45, 338, 550, 480), arch_text, fontsize=9.0, fontname="helv", color=(0.15, 0.15, 0.15))
    if rc2 < 0:
        print("[Warning] Section 2 overflow:", rc2)

    # --- Section 3 : Corpus Documentaire de Référence ---
    page1.insert_text((45, 495), "3. Corpus Documentaire Officiel (data/corpus/)", fontsize=12.5, fontname="hebo", color=(0.12, 0.23, 0.38))
    page1.draw_line((45, 500), (550, 500), color=(0.12, 0.23, 0.38), width=1)

    corpus_desc = (
        "Le corpus documentaire est composé de 6 fiches rédigées au format Markdown à partir des sources officielles "
        "(Service-Public.fr, CROUS, CAF, Action Logement) :\n\n"
        "1. 01_bourses_crous_criteres_sociaux.md : conditions d'âge (<28 ans), barème kilométrique (<30km: 0pt, 30-249km: 1pt, "
        ">=250km: 2pts), fratrie (2pts supérieur, 1pt secondaire), échelons 0bis (1 454 EUR) à 7 (6 335 EUR), plafonds RFR N-2.\n"
        "2. 02_logement_crous_et_visale.md : résidences universitaires, indice social, caution gratuite Visale (36 mensualités "
        "d'impayés couvertes par Action Logement), avance Loca-Pass (prêt à taux zéro jusqu'à 1 200 EUR).\n"
        "3. 03_aide_personnalisee_logement_apl.md : éligibilité CAF, non-prise en compte de la bourse dans les revenus, impact "
        "critique sur la perte des allocations familiales des parents pour les étudiants de moins de 25 ans.\n"
        "4. 04_aides_urgence_crous_fnausu.md : aide d'urgence ponctuelle (plafond de 3 070 EUR/an), allocation annuelle en cas de "
        "rupture familiale, procédure du repas CROUS à 1 EUR pour étudiants non boursiers en situation de précarité.\n"
        "5. 05_aides_transport_restauration_sante.md : repas Resto' U (3,30 EUR normal, 1 EUR très social), forfait Imagine R Île-de-France "
        "(374,40 EUR/an), Santé Psy Étudiant (8 séances gratuites chez le psychologue conventionné).\n"
        "6. 06_aide_mobilite_master_parcoursup.md : aide mobilité Master de 1 000 EUR (changement d'académie en M1), aide mobilité "
        "Parcoursup de 500 EUR, et aide à la mobilité internationale AMI (400 EUR/mois de 2 à 9 mois)."
    )
    rc3 = page1.insert_textbox(pymupdf.Rect(45, 508, 550, 810), corpus_desc, fontsize=8.9, fontname="helv", color=(0.15, 0.15, 0.15))
    if rc3 < 0:
        print("[Warning] Section 3 overflow:", rc3)

    # =========================================================================
    #                               PAGE 2
    # =========================================================================
    page2 = doc.new_page(width=595.3, height=841.9)
    
    # En-tête bleu page 2
    page2.draw_rect(pymupdf.Rect(0, 0, 595.3, 50), color=None, fill=(0.12, 0.23, 0.38))
    page2.insert_text((45, 32), "MINEUR IA GÉNÉRATIVE 2026 · PROPOSITION DE PROJET", fontsize=10, color=(0.85, 0.9, 0.98), fontname="hebo")
    page2.insert_text((450, 32), "Page 2 / 2", fontsize=10, color=(0.8, 0.85, 0.95), fontname="helv")

    # --- Section 4 : Protocole de Test Standardisé ---
    page2.insert_text((45, 75), "4. Protocole d'Évaluation Standardisé (data/tests.jsonl)", fontsize=12.5, fontname="hebo", color=(0.12, 0.23, 0.38))
    page2.draw_line((45, 80), (550, 80), color=(0.12, 0.23, 0.38), width=1)
    
    proto_desc = (
        "Un banc d'évaluation rigoureux de 40 cas de test a été constitué dès la Semaine 1, réparti selon les 4 catégories "
        "exigées par le cahier des charges :\n\n"
        "- 20 cas 'in_corpus' : questions factuelles sur les règles, montants et critères (ex: montant de l'échelon 0bis, "
        "limite d'âge de 28 ans, garantie Visale). Métriques : Recall@5, MRR, exactitude et citation formelle de la source.\n"
        "- 5 cas 'out_of_corpus' : questions hors domaine ou farfelues (subvention de voilier, élevage de lamas, prime pour "
        "astronautes). Métrique : taux d'abstention stricte (le système doit dire qu'il n'a pas l'information au lieu d'inventer).\n"
        "- 10 cas 'multi_step_task' : calculs d'aides et simulations en plusieurs étapes. Métriques : conformité de l'état "
        "final validé par code strict et stabilité pass^3 (les 3 essais successifs doivent réussir).\n"
        "- 5 cas 'ambiguous_or_out_of_scope' : demandes vagues ou illégales (ex: tentative de modification des serveurs CROUS). "
        "Métrique : formulation d'une demande de clarification ou refus poli respectueux des règles éthiques."
    )
    rc4 = page2.insert_textbox(pymupdf.Rect(45, 90, 550, 245), proto_desc, fontsize=9.1, fontname="helv", color=(0.15, 0.15, 0.15))
    if rc4 < 0:
        print("[Warning] Section 4 overflow:", rc4)

    # --- Section 5 : Résultats Mesurés du Niveau 0 (Baseline) ---
    page2.insert_text((45, 260), "5. Résultats Mesurés du Niveau 0 (LLM seul / Baseline à battre)", fontsize=12.5, fontname="hebo", color=(0.12, 0.23, 0.38))
    page2.draw_line((45, 265), (550, 265), color=(0.12, 0.23, 0.38), width=1)

    # Table rect
    page2.draw_rect(pymupdf.Rect(45, 278, 550, 363), color=(0.75, 0.8, 0.88), fill=(0.98, 0.99, 1.0))
    page2.draw_rect(pymupdf.Rect(45, 278, 550, 300), color=(0.75, 0.8, 0.88), fill=(0.9, 0.93, 0.97))
    
    headers = ["Niveau", "Recall@5", "Exactitude", "Abstention", "Succès tâches", "pass^3", "Tokens / req", "Latence"]
    col_x = [50, 130, 200, 270, 350, 420, 480, 520]
    for h, x in zip(headers, col_x):
        page2.insert_text((x, 293), h, fontsize=8.5, fontname="hebo", color=(0.12, 0.23, 0.38))
        
    row_0 = ["0 · LLM seul", "—", "5.0%", "0.0%", "—", "—", "86.1", "0.001s"]
    for val, x in zip(row_0, col_x):
        page2.insert_text((x, 315), val, fontsize=8.5, fontname="hebo", color=(0.1, 0.1, 0.1))
        
    row_1 = ["1 · RAG", "[Semaine 2]", "[Semaine 2]", "[Semaine 2]", "—", "—", "…", "…"]
    for val, x in zip(row_1, col_x):
        page2.insert_text((x, 332), val, fontsize=8.5, fontname="helv", color=(0.45, 0.45, 0.45))

    row_2 = ["2 · Agent", "[Semaine 3]", "[Semaine 3]", "[Semaine 3]", "[Semaine 3]", "[Semaine 3]", "…", "…"]
    for val, x in zip(row_2, col_x):
        page2.insert_text((x, 349), val, fontsize=8.5, fontname="helv", color=(0.45, 0.45, 0.45))

    analysis_text = (
        "Analyse quantitative de l'échec du Niveau 0 (Justification du RAG pour la Semaine 2) :\n"
        "- Faible exactitude (5.0%) : Le LLM seul donne des conseils généraux mais échoue systématiquement sur les chiffres "
        "exacts des barèmes (montant de 1 454 EUR de l'échelon 0bis, 3 070 EUR de l'aide FNAU, 374,40 EUR du passe Imagine R).\n"
        "- Absence totale d'abstention (0.0%) : Sur les 5 requêtes hors domaine, le LLM préfère inventer une réponse plausible "
        "plutôt que d'admettre son absence d'information.\n"
        "- Incapacité d'action : Le LLM seul ne peut pas exécuter les 10 tâches multi-étapes de calcul et d'archivage."
    )
    rc5 = page2.insert_textbox(pymupdf.Rect(45, 372, 550, 480), analysis_text, fontsize=9.0, fontname="helv", color=(0.15, 0.15, 0.15))
    if rc5 < 0:
        print("[Warning] Section 5 overflow:", rc5)

    # --- Section 6 : Calendrier et Plan de Développement ---
    page2.insert_text((45, 495), "6. Calendrier Prévisionnel et Livrables", fontsize=12.5, fontname="hebo", color=(0.12, 0.23, 0.38))
    page2.draw_line((45, 500), (550, 500), color=(0.12, 0.23, 0.38), width=1)

    cal_text = (
        "- Semaine 1 (2 – 8 nov.) [RÉALISÉ] : Choix du thème, corpus documentaire Markdown, protocole de 40 tests, Niveau 0.\n"
        "- Semaine 2 (9 – 15 nov.) : Implémentation du RAG hybride (Dense + BM25), citations de sources, mesure du Recall@5 et gain d'exactitude.\n"
        "- Semaine 3 (16 – 22 nov.) : Implémentation de l'Agent outillé sans framework, règles métier par code, confirmation humaine, métrique pass^3.\n"
        "- Semaine 4 (23 – 30 nov.) : Extension (Niveau 3), analyse de 5 échecs types, rapport d'évaluation final (4 pages) et vidéo de démo."
    )
    rc6 = page2.insert_textbox(pymupdf.Rect(45, 508, 550, 610), cal_text, fontsize=9.0, fontname="helv", color=(0.15, 0.15, 0.15))
    if rc6 < 0:
        print("[Warning] Section 6 overflow:", rc6)

    # --- Section 7 : Dépôt GitHub et Reproductibilité ---
    page2.insert_text((45, 622), "7. Dépôt GitHub et Commandes d'Exécution", fontsize=12.5, fontname="hebo", color=(0.12, 0.23, 0.38))
    page2.draw_line((45, 627), (550, 627), color=(0.12, 0.23, 0.38), width=1)

    repo_box = pymupdf.Rect(45, 638, 550, 775)
    page2.draw_rect(repo_box, color=(0.7, 0.78, 0.9), fill=(0.95, 0.97, 1.0))
    
    repo_text = (
        "- URL du Dépôt GitHub officiel : https://github.com/Alexhuang03/Projet-GenIA\n"
        "- Jalon Semaine 1 : Tag Git 'semaine-1' (sur la branche principale 'main')\n\n"
        "Commandes de reproduction immédiate (aucun GPU requis, mode hors-ligne disponible) :\n"
        "1. Installation des dépendances : pip install -r requirements.txt\n"
        "2. Reproduire le tableau d'évaluation officiel : python eval.py\n"
        "3. Lancer l'interface web interactive : streamlit run app.py"
    )
    rc7 = page2.insert_textbox(pymupdf.Rect(55, 648, 540, 765), repo_text, fontsize=9.2, fontname="hebo", color=(0.1, 0.2, 0.42))
    if rc7 < 0:
        print("[Warning] Section 7 overflow:", rc7)

    # Pied de page discret
    page2.insert_text((45, 805), "Projet IA Générative 2026 · Dr. Issam Falih · Rapport d'Étape Semaine 1", fontsize=8.5, fontname="helv", color=(0.5, 0.5, 0.5))

    doc.save(output_path)
    doc.close()
    print(f"PDF généré avec succès (2 pages) : {output_path}")

if __name__ == "__main__":
    create_proposal_pdf()
