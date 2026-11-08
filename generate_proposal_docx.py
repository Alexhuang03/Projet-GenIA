"""
Générateur officiel du document Word (.docx) avec python-docx
Garantit une compatibilité 100% native avec Microsoft Word sans aucune erreur d'ouverture.
"""
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn


def set_cell_background(cell, hex_color):
    """Applique une couleur d'arrière-plan à une cellule de tableau."""
    shading_elm = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    cell._tc.get_or_add_tcPr().append(shading_elm)


def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    """Définit les marges internes d'une cellule."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)


def add_heading_with_bottom_border(doc, text, level=1):
    """Ajoute un titre élégant avec bordure inférieure."""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.keep_with_next = True
    
    # Bordure inférieure sous le titre
    pBdr = parse_xml(f'<w:pBdr {nsdecls("w")}><w:bottom w:val="single" w:sz="6" w:space="4" w:color="1B365D"/></w:pBdr>')
    p._p.get_or_add_pPr().append(pBdr)
    
    run = p.add_run(text)
    run.bold = True
    run.font.name = 'Calibri'
    run.font.size = Pt(13)
    run.font.color.rgb = RGBColor(27, 54, 93) # #1B365D
    return p


def create_proposal_docx(output_path="Proposition_Projet_Alex_Huang.docx"):
    doc = docx.Document()
    
    # Marges de la page A4 (2.0 cm partout)
    for section in doc.sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)
        section.page_width = Inches(8.27)
        section.page_height = Inches(11.69)

    # 1. Sous-titre institutionnel
    p_sub = doc.add_paragraph()
    p_sub.paragraph_format.space_before = Pt(0)
    p_sub.paragraph_format.space_after = Pt(2)
    r_sub = p_sub.add_run("MINEUR IA GÉNÉRATIVE 2026 · Dr. Issam Falih")
    r_sub.font.name = 'Calibri'
    r_sub.font.size = Pt(9.5)
    r_sub.font.color.rgb = RGBColor(90, 107, 130)
    r_sub.bold = True

    # 2. Grand Titre
    p_title = doc.add_paragraph()
    p_title.paragraph_format.space_before = Pt(0)
    p_title.paragraph_format.space_after = Pt(12)
    r_title = p_title.add_run("PROPOSITION DE PROJET : SEMAINE 1")
    r_title.font.name = 'Calibri'
    r_title.font.size = Pt(18)
    r_title.font.color.rgb = RGBColor(27, 54, 93)
    r_title.bold = True

    # 3. Tableau Récapitulatif (Métadonnées)
    meta_table = doc.add_table(rows=4, cols=2)
    meta_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_table.autofit = False

    meta_data = [
        ("Étudiant(s) :", "Alex HUANG (ING5)"),
        ("Parcours retenu :", "Parcours Texte · Chapitres 4 à 6 (Assistant qui lit, agit et se mesure)"),
        ("Thème & Cas d'usage :", "Assistant Aides Étudiantes & CROUS (bourses, logement, APL, aides d'urgence)"),
        ("Dépôt GitHub officiel :", "https://github.com/Alexhuang03/Projet-GenIA  (Tag Git : semaine-1)")
    ]

    for i, (label, val) in enumerate(meta_data):
        row = meta_table.rows[i]
        
        # Colonne Label
        cell_lbl = row.cells[0]
        cell_lbl.width = Inches(2.0)
        set_cell_background(cell_lbl, "F0F4F8")
        set_cell_margins(cell_lbl, top=80, bottom=80, left=120, right=120)
        p_lbl = cell_lbl.paragraphs[0]
        p_lbl.paragraph_format.space_after = Pt(0)
        r_l = p_lbl.add_run(label)
        r_l.bold = True
        r_l.font.name = 'Calibri'
        r_l.font.size = Pt(9.5)
        r_l.font.color.rgb = RGBColor(27, 54, 93)

        # Colonne Valeur
        cell_val = row.cells[1]
        cell_val.width = Inches(4.8)
        set_cell_background(cell_val, "FAFBFD")
        set_cell_margins(cell_val, top=80, bottom=80, left=120, right=120)
        p_val = cell_val.paragraphs[0]
        p_val.paragraph_format.space_after = Pt(0)
        r_v = p_val.add_run(val)
        r_v.font.name = 'Calibri'
        r_v.font.size = Pt(9.5)
        if "https://" in val:
            r_v.font.color.rgb = RGBColor(9, 105, 218)
            r_v.underline = True
        else:
            r_v.font.color.rgb = RGBColor(30, 30, 30)

    # Espace après le tableau
    doc.add_paragraph().paragraph_format.space_after = Pt(4)

    # 4. Section 1 : Description du Projet et Cas d'Usage
    add_heading_with_bottom_border(doc, "1. Description du Projet et Cas d'Usage", level=1)
    p_desc1 = doc.add_paragraph()
    p_desc1.paragraph_format.space_after = Pt(6)
    p_desc1.paragraph_format.line_spacing = 1.15
    r = p_desc1.add_run(
        "Le financement des études supérieures et l'accès à un logement décent constituent une difficulté majeure "
        "pour de nombreux étudiants en France. Bien que l'État et les organismes publics (CROUS, CAF, Action Logement, Régions) "
        "proposent divers dispositifs d'aide (Bourses sur critères sociaux, APL, caution Visale, aides d'urgence FNAU, aides à la mobilité), "
        "les informations sont dispersées, les règles de cumul complexes et les barèmes très stricts (barèmes kilométriques, fratrie, "
        "plafonds de revenus fiscaux). Les modèles de langage généralistes échouent fréquemment en inventant des barèmes ou en refusant d'admettre leur ignorance."
    )
    r.font.name = 'Calibri'
    r.font.size = Pt(10)

    p_desc2 = doc.add_paragraph()
    p_desc2.paragraph_format.space_after = Pt(8)
    p_desc2.paragraph_format.line_spacing = 1.15
    r_cu_title = p_desc2.add_run("Cas d'usage : ")
    r_cu_title.bold = True
    r_cu_title.font.name = 'Calibri'
    r_cu_title.font.size = Pt(10)
    r_cu_title.font.color.rgb = RGBColor(27, 54, 93)

    r_cu = p_desc2.add_run(
        "Développer un assistant génératif spécialisé capable de guider l'étudiant dans ses démarches, d'effectuer des calculs réglementaires "
        "officiels sans hallucination, de citer formellement les textes de référence, et d'exécuter des démarches de simulation vérifiées avec contrôle humain."
    )
    r_cu.font.name = 'Calibri'
    r_cu.font.size = Pt(10)

    # 5. Section 2 : Démarche Pédagogique et Niveaux Successifs
    add_heading_with_bottom_border(doc, "2. Démarche Pédagogique et Niveaux Successifs", level=1)
    p_arch_intro = doc.add_paragraph()
    p_arch_intro.paragraph_format.space_after = Pt(4)
    r_ai = p_arch_intro.add_run(
        "Conformément au principe directeur du cours (« Commencer simple, et ne passer au niveau suivant que lorsqu'une mesure montre qu'il aide »), "
        "le système est architecturé en 4 niveaux successifs comparés sur le même protocole de test :"
    )
    r_ai.font.name = 'Calibri'
    r_ai.font.size = Pt(10)

    niveaux = [
        ("Niveau 0 (LLM seul / Semaine 1) : ", "Prompt système soigné, sans document externe ni outil. Baseline de référence à battre permettant de mesurer les lacunes du modèle de base."),
        ("Niveau 1 (RAG / Semaine 2) : ", "Découpage sémantique avec métadonnées, recherche hybride Dense (TF-IDF normalisé) + BM25 Okapi, citation obligatoire des sources officielles et abstention stricte en cas de question hors domaine pour éliminer les hallucinations."),
        ("Niveau 2 (Agent outillé / Semaine 3) : ", "Boucle ReAct développée 100% SANS framework avec 3 outils JSON, règles métier vérifiées par code Python (calculs kilométriques et familiaux stricts) et confirmation humaine obligatoire avant toute action irréversible d'archivage."),
        ("Niveau 3 (Extension / Semaine 4) : ", "Technique avancée (RAG Hybride avec Reranking / HyDE ou planification ReWOO) mesurée et comparée au Niveau 2.")
    ]

    for title, desc in niveaux:
        p_niv = doc.add_paragraph(style='List Bullet')
        p_niv.paragraph_format.space_before = Pt(1)
        p_niv.paragraph_format.space_after = Pt(3)
        r_t = p_niv.add_run(title)
        r_t.bold = True
        r_t.font.name = 'Calibri'
        r_t.font.size = Pt(9.5)
        r_t.font.color.rgb = RGBColor(27, 54, 93)
        r_d = p_niv.add_run(desc)
        r_d.font.name = 'Calibri'
        r_d.font.size = Pt(9.5)

    # 6. Section 3 : Corpus Documentaire Officiel
    add_heading_with_bottom_border(doc, "3. Corpus Documentaire Officiel (data/corpus/)", level=1)
    p_corp_intro = doc.add_paragraph()
    p_corp_intro.paragraph_format.space_after = Pt(4)
    r_ci = p_corp_intro.add_run("Le corpus initial réunit 6 fiches documentaires officielles exhaustives rédigées au format Markdown :")
    r_ci.font.name = 'Calibri'
    r_ci.font.size = Pt(10)

    docs_corpus = [
        ("1. 01_bourses_crous_criteres_sociaux.md : ", "conditions d'âge (<28 ans), barème kilométrique (<30km: 0pt, 30-249km: 1pt, >=250km: 2pts), fratrie (2pts supérieur, 1pt secondaire), échelons 0bis (1 454 €) à 7 (6 335 €), plafonds RFR N-2."),
        ("2. 02_logement_crous_et_visale.md : ", "résidences CROUS, attribution par indice social, caution gratuite Visale d'Action Logement (36 mensualités couvertes), avance Loca-Pass (prêt à taux zéro jusqu'à 1 200 €)."),
        ("3. 03_aide_personnalisee_logement_apl.md : ", "conditions CAF, non-prise en compte de la bourse dans les revenus, impact critique sur la perte des allocations familiales des parents pour les étudiants de moins de 25 ans."),
        ("4. 04_aides_urgence_crous_fnausu.md : ", "aide d'urgence ponctuelle (plafond de 3 070 €/an), allocation spécifique annuelle en cas de rupture familiale, procédure du repas CROUS à 1 € pour non-boursiers en précarité."),
        ("5. 05_aides_transport_restauration_sante.md : ", "restauration universitaire (3,30 € normal / 1,00 € très social), forfait Imagine R Île-de-France (374,40 €/an), dispositif Santé Psy Étudiant (8 séances gratuites chez le psychologue)."),
        ("6. 06_aide_mobilite_master_parcoursup.md : ", "aide mobilité Master de 1 000 € (mobilité interacadémique en M1), aide Parcoursup de 500 €, et aide à la mobilité internationale AMI (400 €/mois de 2 à 9 mois).")
    ]

    for title, desc in docs_corpus:
        p_c = doc.add_paragraph()
        p_c.paragraph_format.space_before = Pt(1)
        p_c.paragraph_format.space_after = Pt(2)
        p_c.paragraph_format.left_indent = Inches(0.2)
        r_t = p_c.add_run(title)
        r_t.bold = True
        r_t.font.name = 'Calibri'
        r_t.font.size = Pt(9.5)
        r_d = p_c.add_run(desc)
        r_d.font.name = 'Calibri'
        r_d.font.size = Pt(9.5)

    # 7. Section 4 : Protocole d'Évaluation Standardisé
    add_heading_with_bottom_border(doc, "4. Protocole d'Évaluation Standardisé (data/tests.jsonl)", level=1)
    p_proto_intro = doc.add_paragraph()
    p_proto_intro.paragraph_format.space_after = Pt(4)
    r_pi = p_proto_intro.add_run("Un banc d'évaluation rigoureux de 40 cas de test a été constitué dès la Semaine 1, réparti selon les 4 catégories exigées par le cahier des charges :")
    r_pi.font.name = 'Calibri'
    r_pi.font.size = Pt(10)

    cats = [
        ("• 20 cas 'in_corpus' : ", "questions factuelles sur les règles, montants et critères (ex: montant de l'échelon 0bis, limite d'âge de 28 ans, garantie Visale). Métriques : Recall@5, MRR, exactitude et citation formelle de la source."),
        ("• 5 cas 'out_of_corpus' : ", "questions hors domaine ou farfelues (subvention de voilier, élevage de lamas, prime pour astronautes). Métrique : taux d'abstention stricte (le système doit s'abstenir formellement au lieu d'inventer)."),
        ("• 10 cas 'multi_step_task' : ", "calculs d'aides et simulations en plusieurs étapes. Métriques : conformité de l'état final validé par code strict et stabilité pass^3 (les 3 essais successifs doivent réussir)."),
        ("• 5 cas 'ambiguous_or_out_of_scope' : ", "demandes vagues ou proscrites (ex: tentative de modification des serveurs CROUS). Métrique : question de clarification ou refus poli respectueux des règles éthiques.")
    ]

    for title, desc in cats:
        p_cat = doc.add_paragraph()
        p_cat.paragraph_format.space_before = Pt(1)
        p_cat.paragraph_format.space_after = Pt(2)
        p_cat.paragraph_format.left_indent = Inches(0.2)
        r_t = p_cat.add_run(title)
        r_t.bold = True
        r_t.font.name = 'Calibri'
        r_t.font.size = Pt(9.5)
        r_t.font.color.rgb = RGBColor(27, 54, 93)
        r_d = p_cat.add_run(desc)
        r_d.font.name = 'Calibri'
        r_d.font.size = Pt(9.5)

    # 8. Section 5 : Résultats Mesurés du Niveau 0 (Baseline)
    add_heading_with_bottom_border(doc, "5. Résultats Mesurés du Niveau 0 (LLM seul / Baseline à battre)", level=1)
    p_res_intro = doc.add_paragraph()
    p_res_intro.paragraph_format.space_after = Pt(4)
    r_ri = p_res_intro.add_run("Tableau officiel des résultats reproduit par la commande python eval.py :")
    r_ri.font.name = 'Calibri'
    r_ri.font.size = Pt(10)

    # Tableau des métriques
    res_table = doc.add_table(rows=4, cols=8)
    res_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    res_table.autofit = False

    t_headers = ["Niveau", "Recall@5", "Exactitude", "Abstention", "Succès tâches", "pass^3", "Tokens / req", "Latence"]
    col_widths = [Inches(1.2), Inches(0.8), Inches(0.8), Inches(0.8), Inches(0.9), Inches(0.7), Inches(0.9), Inches(0.7)]

    # En-tête
    hdr_row = res_table.rows[0]
    for j, (h_text, w) in enumerate(zip(t_headers, col_widths)):
        cell = hdr_row.cells[j]
        cell.width = w
        set_cell_background(cell, "E2E8F0")
        set_cell_margins(cell, top=60, bottom=60, left=60, right=60)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(h_text)
        r.bold = True
        r.font.name = 'Calibri'
        r.font.size = Pt(8.5)
        r.font.color.rgb = RGBColor(27, 54, 93)

    rows_data = [
        ("0 · LLM seul", "—", "5.0%", "0.0%", "—", "—", "86.1", "0.001s", False),
        ("1 · RAG", "[Semaine 2]", "[Semaine 2]", "[Semaine 2]", "—", "—", "…", "…", True),
        ("2 · Agent", "[Semaine 3]", "[Semaine 3]", "[Semaine 3]", "[Semaine 3]", "[Semaine 3]", "…", "…", True)
    ]

    for i, r_data in enumerate(rows_data):
        row = res_table.rows[i + 1]
        is_dim = r_data[8]
        for j, val in enumerate(r_data[:8]):
            cell = row.cells[j]
            cell.width = col_widths[j]
            set_cell_background(cell, "F8FAFC" if i % 2 == 0 else "FFFFFF")
            set_cell_margins(cell, top=50, bottom=50, left=50, right=50)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(val)
            r.font.name = 'Calibri'
            r.font.size = Pt(8.5)
            if is_dim:
                r.font.color.rgb = RGBColor(100, 116, 139)
            elif val in ("5.0%", "0.0%"):
                r.bold = True
                r.font.color.rgb = RGBColor(217, 56, 30)
            else:
                r.font.color.rgb = RGBColor(30, 30, 30)

    # Analyse d'échec
    p_fail = doc.add_paragraph()
    p_fail.paragraph_format.space_before = Pt(8)
    p_fail.paragraph_format.space_after = Pt(6)
    p_fail.paragraph_format.line_spacing = 1.15
    r_f_t = p_fail.add_run("Analyse quantitative de l'échec du Niveau 0 (Justification du RAG pour la Semaine 2) :\n")
    r_f_t.bold = True
    r_f_t.font.name = 'Calibri'
    r_f_t.font.size = Pt(9.5)
    r_f_t.font.color.rgb = RGBColor(27, 54, 93)

    r_f_c = p_fail.add_run(
        "1. Faible exactitude factuelle (5.0%) : Le LLM seul donne des conseils généraux mais échoue systématiquement sur les chiffres "
        "exacts des barèmes (montant de 1 454 € de l'échelon 0bis, 3 070 € de l'aide FNAU, 374,40 € du passe Imagine R).\n"
        "2. Absence totale d'abstention (0.0%) : Sur les 5 requêtes hors domaine, le LLM préfère inventer une réponse plausible plutôt que d'admettre son absence d'information.\n"
        "3. Incapacité d'action : Le LLM seul ne peut pas exécuter les 10 tâches multi-étapes de calcul et d'archivage."
    )
    r_f_c.font.name = 'Calibri'
    r_f_c.font.size = Pt(9.5)

    # 9. Section 6 : Calendrier et Livrables
    add_heading_with_bottom_border(doc, "6. Calendrier Prévisionnel et Livrables", level=1)
    cals = [
        ("• Semaine 1 (2 – 8 nov.) [RÉALISÉ] : ", "Choix du thème, corpus documentaire Markdown, protocole de 40 tests, Niveau 0."),
        ("• Semaine 2 (9 – 15 nov.) : ", "Implémentation du RAG hybride (Dense + BM25), citations de sources, mesure du Recall@5 et gain d'exactitude."),
        ("• Semaine 3 (16 – 22 nov.) : ", "Implémentation de l'Agent outillé sans framework, règles métier par code, confirmation humaine, métrique pass^3."),
        ("• Semaine 4 (23 – 30 nov.) : ", "Extension (Niveau 3), analyse de 5 échecs types, rapport d'évaluation final (4 pages) et vidéo de démo.")
    ]
    for title, desc in cals:
        p_cal = doc.add_paragraph()
        p_cal.paragraph_format.space_before = Pt(1)
        p_cal.paragraph_format.space_after = Pt(2)
        p_cal.paragraph_format.left_indent = Inches(0.2)
        r_t = p_cal.add_run(title)
        r_t.bold = True
        r_t.font.name = 'Calibri'
        r_t.font.size = Pt(9.5)
        r_d = p_cal.add_run(desc)
        r_d.font.name = 'Calibri'
        r_d.font.size = Pt(9.5)

    # 10. Section 7 : Dépôt GitHub et Commandes d'Exécution
    add_heading_with_bottom_border(doc, "7. Dépôt GitHub et Commandes de Reproduction", level=1)
    
    p_box = doc.add_paragraph()
    p_box.paragraph_format.space_before = Pt(4)
    p_box.paragraph_format.space_after = Pt(4)
    p_box.paragraph_format.left_indent = Inches(0.2)
    p_box.paragraph_format.line_spacing = 1.2
    
    r_gh = p_box.add_run("• URL du Dépôt GitHub officiel : https://github.com/Alexhuang03/Projet-GenIA\n")
    r_gh.bold = True
    r_gh.font.name = 'Calibri'
    r_gh.font.size = Pt(9.5)
    r_gh.font.color.rgb = RGBColor(9, 105, 218)
    
    r_tag = p_box.add_run("• Jalon Semaine 1 : Tag Git 'semaine-1' (sur la branche principale 'main')\n\n")
    r_tag.bold = True
    r_tag.font.name = 'Calibri'
    r_tag.font.size = Pt(9.5)
    r_tag.font.color.rgb = RGBColor(27, 54, 93)

    r_cmds = p_box.add_run(
        "Commandes d'exécution (100% reproductible sans GPU, mode hors-ligne disponible) :\n"
        "1. Installation des dépendances : pip install -r requirements.txt\n"
        "2. Reproduire le tableau d'évaluation officiel : python eval.py\n"
        "3. Lancer l'interface web interactive : streamlit run app.py"
    )
    r_cmds.font.name = 'Calibri'
    r_cmds.font.size = Pt(9.5)

    # Sauvegarde du fichier
    doc.save(output_path)
    print(f"Document Word (.docx) généré avec succès via python-docx : {output_path}")


if __name__ == "__main__":
    create_proposal_docx()
