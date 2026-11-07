"""
Script de génération de la Proposition de Projet en PDF
Pour le dépôt Moodle 'Project Proposal deposit' (Semaine 1 - Due 8 nov. 2026)
"""
import pymupdf

def create_proposal_pdf(output_path="Proposition_Projet_Alex_Huang.pdf"):
    doc = pymupdf.open()
    
    # ------------------ PAGE 1 ------------------
    page1 = doc.new_page(width=595.3, height=841.9) # A4 format
    
    # Header background band
    page1.draw_rect(pymupdf.Rect(0, 0, 595.3, 75), color=None, fill=(0.12, 0.23, 0.36))
    page1.insert_text((45, 32), "MINEUR IA GÉNÉRATIVE 2026 · Dr. Issam Falih", fontsize=10, color=(0.85, 0.9, 0.98), fontname="helv")
    page1.insert_text((45, 55), "PROPOSITION DE PROJET (SEMAINE 1)", fontsize=18, color=(1, 1, 1), fontname="hebo")
    
    # Metadata Box
    page1.draw_rect(pymupdf.Rect(45, 90, 550, 160), color=(0.85, 0.88, 0.92), fill=(0.96, 0.97, 0.99))
    page1.insert_text((55, 110), "Étudiant(s) :", fontsize=10, fontname="hebo", color=(0.12, 0.23, 0.36))
    page1.insert_text((150, 110), "Alex HUANG (ING5)", fontsize=10, fontname="helv", color=(0.1, 0.1, 0.1))
    
    page1.insert_text((55, 126), "Parcours retenu :", fontsize=10, fontname="hebo", color=(0.12, 0.23, 0.36))
    page1.insert_text((150, 126), "Parcours Texte · Chapitres 4 à 6 (Assistant qui lit, agit et se mesure)", fontsize=10, fontname="helv", color=(0.1, 0.1, 0.1))
    
    page1.insert_text((55, 142), "Thème du projet :", fontsize=10, fontname="hebo", color=(0.12, 0.23, 0.36))
    page1.insert_text((150, 142), "Assistant Aides Étudiantes & CROUS (bourses, logement, APL, aides d'urgence)", fontsize=10, fontname="helv", color=(0.1, 0.1, 0.1))
    
    # Section 1 : Proposition de Projet
    page1.insert_text((45, 182), "1. Description du Projet et Cas d'Usage", fontsize=13, fontname="hebo", color=(0.12, 0.23, 0.36))
    page1.draw_line((45, 187), (550, 187), color=(0.12, 0.23, 0.36), width=1)
    
    desc_text = (
        "En France, l'accès aux aides financières et sociales pour les étudiants (Bourses sur critères sociaux du CROUS, "
        "logements universitaires, garantie Visale, APL de la CAF, aides d'urgence FNAU) souffre d'une dispersion "
        "réglementaire majeure. Les étudiants font face à des critères d'éligibilité stricts et des barèmes complexes.\n\n"
        "Ce projet met en œuvre un système génératif modulaire mesurable par niveaux successifs (LLM seul -> RAG -> "
        "Agent outillé -> Extension) capable d'informer sans halluciner, de citer précisément ses sources réglementaires, "
        "et d'exécuter des démarches de simulation vérifiées par le code avec confirmation humaine des actions irréversibles."
    )
    page1.insert_textbox(pymupdf.Rect(45, 195, 550, 275), desc_text, fontsize=9.5, fontname="helv", color=(0.15, 0.15, 0.15))
    
    # Section 2 : Corpus Documentaire
    page1.insert_text((45, 290), "2. Corpus Documentaire de Référence (data/corpus/)", fontsize=13, fontname="hebo", color=(0.12, 0.23, 0.36))
    page1.draw_line((45, 295), (550, 295), color=(0.12, 0.23, 0.36), width=1)
    
    corpus_text = (
        "Le corpus initial regroupe 6 fiches documentaires officielles exhaustives au format Markdown :\n"
        "• 01_bourses_crous_criteres_sociaux.md : conditions, points de charge (éloignement, fratrie), échelons 0bis à 7, plafonds RFR.\n"
        "• 02_logement_crous_et_visale.md : résidences CROUS, indice social, caution gratuite Visale (36 mensualités), Loca-Pass.\n"
        "• 03_aide_personnalisee_logement_apl.md : conditions CAF, non-imposition de la bourse, impact allocations des parents.\n"
        "• 04_aides_urgence_crous_fnausu.md : aide ponctuelle (plafond de 3 070 €/an), allocation annuelle, repas 1 € non boursier.\n"
        "• 05_aides_transport_restauration_sante.md : repas Resto'U (3,30 € / 1 €), Imagine R (374,40 €), Santé Psy (8 séances gratuites).\n"
        "• 06_aide_mobilite_master_parcoursup.md : aide mobilité Master 1 000 €, Parcoursup 500 €, mobilité internationale (400 €/mois)."
    )
    page1.insert_textbox(pymupdf.Rect(45, 305, 550, 405), corpus_text, fontsize=9.2, fontname="helv", color=(0.15, 0.15, 0.15))
    
    # Section 3 : Protocole de Test
    page1.insert_text((45, 420), "3. Protocole de Test Standardisé (data/tests.jsonl)", fontsize=13, fontname="hebo", color=(0.12, 0.23, 0.36))
    page1.draw_line((45, 425), (550, 425), color=(0.12, 0.23, 0.36), width=1)
    
    tests_desc = (
        "Dès cette première semaine, un banc de test de 40 cas a été étalonné pour servir de protocole commun à tous les niveaux :\n"
        "• 20 cas 'in_corpus' : vérification de la véracité des chiffres et de la présence de la citation de source.\n"
        "• 5 cas 'out_of_corpus' : requêtes hors domaine (voilier, lamas, etc.) exigeant une abstention formelle du système.\n"
        "• 10 cas 'multi_step_task' : tâches d'agent avec validation mathématique de l'état final par code Python (pass^3).\n"
        "• 5 cas 'ambiguous_or_out_of_scope' : demandes floues ou illégales nécessitant une clarification ou un refus poli."
    )
    page1.insert_textbox(pymupdf.Rect(45, 435, 550, 520), tests_desc, fontsize=9.2, fontname="helv", color=(0.15, 0.15, 0.15))
    
    # Section 4 : Niveau 0
    page1.insert_text((45, 540), "4. Résultats Mesurés du Niveau 0 (LLM seul / Baseline à battre)", fontsize=13, fontname="hebo", color=(0.12, 0.23, 0.36))
    page1.draw_line((45, 545), (550, 545), color=(0.12, 0.23, 0.36), width=1)
    
    # Table rect
    page1.draw_rect(pymupdf.Rect(45, 560, 550, 645), color=(0.75, 0.8, 0.88), fill=(0.98, 0.99, 1.0))
    page1.draw_rect(pymupdf.Rect(45, 560, 550, 582), color=(0.75, 0.8, 0.88), fill=(0.9, 0.93, 0.97))
    
    headers = ["Niveau", "Recall@5", "Exactitude", "Abstention", "Succès tâches", "pass^3", "Tokens", "Latence"]
    col_x = [50, 130, 200, 270, 350, 430, 480, 520]
    for h, x in zip(headers, col_x):
        page1.insert_text((x, 575), h, fontsize=8.5, fontname="hebo", color=(0.12, 0.23, 0.36))
        
    row_0 = ["0 · LLM seul", "—", "5.0%", "0.0%", "—", "—", "86.1", "0.001s"]
    for val, x in zip(row_0, col_x):
        page1.insert_text((x, 597), val, fontsize=8.5, fontname="helv", color=(0.1, 0.1, 0.1))
        
    row_1 = ["1 · RAG", "...", "...", "...", "—", "—", "...", "..."]
    for val, x in zip(row_1, col_x):
        page1.insert_text((x, 614), val, fontsize=8.5, fontname="helv", color=(0.5, 0.5, 0.5))

    row_2 = ["2 · Agent", "...", "...", "...", "...", "...", "...", "..."]
    for val, x in zip(row_2, col_x):
        page1.insert_text((x, 631), val, fontsize=8.5, fontname="helv", color=(0.5, 0.5, 0.5))

    analysis_text = (
        "Analyse de l'échec du Niveau 0 : Le modèle produit des réponses linguistiquement fluides mais factuellement "
        "fausses (exactitude de 5% sur les barèmes) et ne s'abstient jamais (0%). Cette défaillance mesurée justifie "
        "strictement l'intégration du RAG (Niveau 1) prévue pour la Semaine 2."
    )
    page1.insert_textbox(pymupdf.Rect(45, 655, 550, 715), analysis_text, fontsize=9.2, fontname="helv", color=(0.2, 0.2, 0.2))

    # Section 5 : Dépôt & Instructions
    page1.insert_text((45, 725), "5. Dépôt Git et Reproductibilité", fontsize=13, fontname="hebo", color=(0.12, 0.23, 0.36))
    page1.draw_line((45, 730), (550, 730), color=(0.12, 0.23, 0.36), width=1)
    
    footer_text = (
        "• Dépôt GitHub officiel : https://github.com/Alexhuang03/Projet-GenIA (Tag Git : semaine-1)\n"
        "• Reproduction de l'évaluation : python eval.py (reproduit les métriques ci-dessus en une commande)\n"
        "• Interface Streamlit : streamlit run app.py (dédiée au test interactif et à l'observabilité du Niveau 0)"
    )
    page1.insert_textbox(pymupdf.Rect(45, 740, 550, 810), footer_text, fontsize=9.2, fontname="hebo", color=(0.1, 0.2, 0.4))

    doc.save(output_path)
    doc.close()
    print(f"PDF généré avec succès : {output_path}")

if __name__ == "__main__":
    create_proposal_pdf()
