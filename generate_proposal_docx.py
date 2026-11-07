"""
Générateur natif de document Microsoft Word (.docx)
Proposition de Projet - Semaine 1 (Due 8 nov. 2026)
Crée un document Word (.docx) complet, parfaitement stylé et sans dépendance externe.
"""
import zipfile
from pathlib import Path


def generate_docx(output_filename="Proposition_Projet_Alex_Huang.docx"):
    content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
</Types>"""

    rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""

    doc_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink" Target="https://github.com/Alexhuang03/Projet-GenIA" TargetMode="External"/>
</Relationships>"""

    styles_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:docDefaults>
    <w:rPrDefault>
      <w:rPr>
        <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:cs="Calibri"/>
        <w:sz w:val="22"/>
        <w:color w:val="262626"/>
      </w:rPr>
    </w:rPrDefault>
    <w:pPrDefault>
      <w:pPr>
        <w:spacing w:line="276" w:lineRule="auto" w:after="120"/>
      </w:pPr>
    </w:pPrDefault>
  </w:docDefaults>
</w:styles>"""

    # Construction du corps document.xml
    body_elements = []

    def p(text, bold=False, size=22, color="262626", space_after=120, space_before=0, align=None):
        align_tag = f'<w:jc w:val="{align}"/>' if align else ''
        bold_tag = '<w:b/>' if bold else ''
        return f"""
        <w:p>
          <w:pPr>
            <w:spacing w:before="{space_before}" w:after="{space_after}"/>
            {align_tag}
          </w:pPr>
          <w:r>
            <w:rPr>
              {bold_tag}
              <w:sz w:val="{size}"/>
              <w:color w:val="{color}"/>
            </w:rPr>
            <w:t xml:space="preserve">{text}</w:t>
          </w:r>
        </w:p>"""

    def heading(text, level=1):
        size = 28 if level == 1 else 24
        color = "1B365D"
        space_before = 240 if level == 1 else 160
        border_tag = '<w:pBdr><w:bottom w:val="single" w:sz="6" w:space="4" w:color="1B365D"/></w:pBdr>' if level == 1 else ''
        return f"""
        <w:p>
          <w:pPr>
            <w:spacing w:before="{space_before}" w:after="100"/>
            {border_tag}
          </w:pPr>
          <w:r>
            <w:rPr>
              <w:b/>
              <w:sz w:val="{size}"/>
              <w:color w:val="{color}"/>
            </w:rPr>
            <w:t xml:space="preserve">{text}</w:t>
          </w:r>
        </w:p>"""

    def bullet(prefix, text):
        return f"""
        <w:p>
          <w:pPr>
            <w:spacing w:before="40" w:after="80"/>
            <w:ind w:left="360"/>
          </w:pPr>
          <w:r>
            <w:rPr>
              <w:b/>
              <w:color w:val="1B365D"/>
            </w:rPr>
            <w:t xml:space="preserve">{prefix} </w:t>
          </w:r>
          <w:r>
            <w:t xml:space="preserve">{text}</w:t>
          </w:r>
        </w:p>"""

    # 1. En-tête / Titre
    body_elements.append(p("MINEUR IA GÉNÉRATIVE 2026 · Dr. Issam Falih", bold=True, size=20, color="5A6B82", space_after=60))
    body_elements.append(p("PROPOSITION DE PROJET (SEMAINE 1)", bold=True, size=36, color="1B365D", space_after=180))

    # 2. Tableau Métadonnées
    meta_table = """
    <w:tbl>
      <w:tblPr>
        <w:tblW w:w="9600" w:type="dxa"/>
        <w:tblBorders>
          <w:top w:val="single" w:sz="8" w:space="0" w:color="D0D7DE"/>
          <w:left w:val="single" w:sz="8" w:space="0" w:color="D0D7DE"/>
          <w:bottom w:val="single" w:sz="8" w:space="0" w:color="D0D7DE"/>
          <w:right w:val="single" w:sz="8" w:space="0" w:color="D0D7DE"/>
          <w:insideH w:val="single" w:sz="4" w:space="0" w:color="E1E4E8"/>
          <w:insideV w:val="none"/>
        </w:tblBorders>
        <w:tblCellMar>
          <w:top w:w="120" w:type="dxa"/>
          <w:left w:w="160" w:type="dxa"/>
          <w:bottom w:w="120" w:type="dxa"/>
          <w:right w:w="160" w:type="dxa"/>
        </w:tblCellMar>
      </w:tblPr>
      <w:tr>
        <w:tc><w:tcPr><w:tcW w:w="2600" w:type="dxa"/><w:shd w:val="clear" w:color="auto" w:fill="F6F8FA"/></w:tcPr><w:p><w:r><w:rPr><w:b/><w:color w:val="1B365D"/></w:rPr><w:t>Étudiant(s)</w:t></w:r></w:p></w:tc>
        <w:tc><w:tcPr><w:tcW w:w="7000" w:type="dxa"/><w:shd w:val="clear" w:color="auto" w:fill="F6F8FA"/></w:tcPr><w:p><w:r><w:t>Alex HUANG (ING5)</w:t></w:r></w:p></w:tc>
      </w:tr>
      <w:tr>
        <w:tc><w:tcPr><w:tcW w:w="2600" w:type="dxa"/></w:tcPr><w:p><w:r><w:rPr><w:b/><w:color w:val="1B365D"/></w:rPr><w:t>Parcours retenu</w:t></w:r></w:p></w:tc>
        <w:tc><w:tcPr><w:tcW w:w="7000" w:type="dxa"/></w:tcPr><w:p><w:r><w:t>Parcours Texte · Chapitres 4 à 6 (Assistant qui lit, agit et se mesure)</w:t></w:r></w:p></w:tc>
      </w:tr>
      <w:tr>
        <w:tc><w:tcPr><w:tcW w:w="2600" w:type="dxa"/><w:shd w:val="clear" w:color="auto" w:fill="F6F8FA"/></w:tcPr><w:p><w:r><w:rPr><w:b/><w:color w:val="1B365D"/></w:rPr><w:t>Thème &amp; Cas d'usage</w:t></w:r></w:p></w:tc>
        <w:tc><w:tcPr><w:tcW w:w="7000" w:type="dxa"/><w:shd w:val="clear" w:color="auto" w:fill="F6F8FA"/></w:tcPr><w:p><w:r><w:t>Assistant Aides Étudiantes &amp; CROUS (bourses, logement, APL, aides d'urgence)</w:t></w:r></w:p></w:tc>
      </w:tr>
      <w:tr>
        <w:tc><w:tcPr><w:tcW w:w="2600" w:type="dxa"/></w:tcPr><w:p><w:r><w:rPr><w:b/><w:color w:val="1B365D"/></w:rPr><w:t>Dépôt GitHub</w:t></w:r></w:p></w:tc>
        <w:tc><w:tcPr><w:tcW w:w="7000" w:type="dxa"/></w:tcPr><w:p><w:hyperlink r:id="rId2" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><w:r><w:rPr><w:color w:val="0969DA"/><w:u w:val="single"/></w:rPr><w:t>https://github.com/Alexhuang03/Projet-GenIA</w:t></w:r></w:hyperlink><w:r><w:t> (Tag : semaine-1)</w:t></w:r></w:p></w:tc>
      </w:tr>
    </w:tbl>
    """
    body_elements.append(meta_table)

    # 3. Section 1 : Description du Projet et Cas d'Usage
    body_elements.append(heading("1. Description du Projet et Cas d'Usage", 1))
    body_elements.append(p(
        "En France, l'accès aux aides financières et sociales pour les étudiants (Bourses sur critères sociaux du CROUS, "
        "logements universitaires conventionnés, caution locative gratuite Visale, Aide Personnalisée au Logement APL de la CAF, "
        "fonds d'urgence FNAU, aides à la mobilité) souffre d'une dispersion réglementaire majeure. Les étudiants font face à des "
        "conditions d'éligibilité strictes et des barèmes complexes (éloignement kilométrique, fratrie à charge, plafonds de revenus fiscaux). "
        "Les modèles de langage généralistes échouent souvent en inventant des barèmes ou en refusant d'admettre leur ignorance."
    ))
    body_elements.append(p(
        "Cas d'usage : Concevoir un système génératif complet et mesurable dédié aux aides étudiantes. "
        "Le système commence par une référence à battre (Niveau 0), puis intègre une recherche documentaire sourcée avec abstention stricte (Niveau 1 RAG), "
        "avant d'évoluer vers un agent outillé sans framework capable d'exécuter des calculs officiels et de sauvegarder une attestation de simulation "
        "sous le contrôle explicite de l'étudiant (Niveau 2 Agent)."
    ))

    # 4. Section 2 : Démarche Pédagogique et Niveaux Successifs
    body_elements.append(heading("2. Démarche Pédagogique et Niveaux Successifs", 1))
    body_elements.append(p(
        "Conformément à la règle d'or du Dr. Issam Falih (« Commencer simple, et ne passer au niveau suivant que lorsqu'une mesure montre qu'il aide »), "
        "le projet s'articule en 4 niveaux comparés sur le même protocole de test :"
    ))
    body_elements.append(bullet("• Niveau 0 (LLM seul / Semaine 1) :", "Prompt soigné sans document ni outil. Permet de mesurer précisément les défauts du modèle de base (faible exactitude sur les barèmes, zéro abstention)."))
    body_elements.append(bullet("• Niveau 1 (RAG / Semaine 2) :", "Découpage sémantique avec métadonnées, recherche hybride Dense (TF-IDF normalisé) + BM25 Okapi, citation formelle de la source et abstention stricte sur les questions hors corpus."))
    body_elements.append(bullet("• Niveau 2 (Agent outillé / Semaine 3) :", "Boucle ReAct écrite 100% SANS framework avec 3 outils JSON, validation des règles métier par code strict et confirmation humaine obligatoire avant toute action irréversible."))
    body_elements.append(bullet("• Niveau 3 (Extension / Semaine 4) :", "Technique avancée (RAG Hybride avec Reranking / HyDE ou planification ReWOO) comparée au Niveau 2."))

    # 5. Section 3 : Corpus Documentaire
    body_elements.append(heading("3. Corpus Documentaire Officiel (data/corpus/)", 1))
    body_elements.append(p("Le corpus initial réunit 6 fiches réglementaires exhaustives au format Markdown :"))
    body_elements.append(bullet("1. 01_bourses_crous_criteres_sociaux.md :", "conditions d'âge (<28 ans), barème kilométrique (<30km: 0pt, 30-249km: 1pt, >=250km: 2pts), fratrie (2pts supérieur, 1pt secondaire), échelons 0bis (1 454 €) à 7 (6 335 €), plafonds RFR N-2."))
    body_elements.append(bullet("2. 02_logement_crous_et_visale.md :", "résidences CROUS, attribution par indice social, caution gratuite Visale d'Action Logement (36 mensualités couvertes), avance Loca-Pass (prêt à taux zéro jusqu'à 1 200 €)."))
    body_elements.append(bullet("3. 03_aide_personnalisee_logement_apl.md :", "conditions CAF, non-imposition de la bourse dans les ressources, impact sur la perte des allocations familiales des parents pour les moins de 25 ans."))
    body_elements.append(bullet("4. 04_aides_urgence_crous_fnausu.md :", "aide d'urgence ponctuelle (plafond de 3 070 €/an), allocation spécifique annuelle, procédure du repas CROUS à 1 € pour non-boursiers en précarité."))
    body_elements.append(bullet("5. 05_aides_transport_restauration_sante.md :", "restauration universitaire (3,30 € normal / 1,00 € très social), forfait Imagine R Île-de-France (374,40 €/an), dispositif Santé Psy Étudiant (8 séances gratuites)."))
    body_elements.append(bullet("6. 06_aide_mobilite_master_parcoursup.md :", "aide mobilité Master de 1 000 € (mobilité interacadémique en M1), aide Parcoursup de 500 €, et aide à la mobilité internationale AMI (400 €/mois)."))

    # 6. Section 4 : Protocole de Test
    body_elements.append(heading("4. Protocole d'Évaluation Standardisé (data/tests.jsonl)", 1))
    body_elements.append(p(
        "Dès la première semaine, un jeu de test de 40 cas calibrés a été fixé pour évaluer objectivement chaque niveau selon les 4 catégories imposées :"
    ))
    body_elements.append(bullet("• 20 cas 'in_corpus' :", "questions documentaires directes. Mesure : Recall@5, MRR, exactitude et présence obligatoire de la citation de source."))
    body_elements.append(bullet("• 5 cas 'out_of_corpus' :", "questions hors domaine (subvention de voilier, élevage de lamas, etc.). Mesure : taux d'abstention stricte (le système doit s'abstenir au lieu d'halluciner)."))
    body_elements.append(bullet("• 10 cas 'multi_step_task' :", "tâches complexes d'agent. Mesure : vérification de l'état final par code strict et stabilité sous la métrique pass^3 (les 3 essais consécutifs doivent réussir)."))
    body_elements.append(bullet("• 5 cas 'ambiguous_or_out_of_scope' :", "demandes vagues ou proscrites (ex: tentative de piratage du CROUS). Mesure : question de clarification ou refus poli."))

    # 7. Section 5 : Résultats du Niveau 0
    body_elements.append(heading("5. Résultats Mesurés du Niveau 0 (LLM seul / Baseline à battre)", 1))
    body_elements.append(p("Résultats obtenus par l'exécution de la commande officielle python eval.py :"))

    results_table = """
    <w:tbl>
      <w:tblPr>
        <w:tblW w:w="9600" w:type="dxa"/>
        <w:tblBorders>
          <w:top w:val="single" w:sz="6" w:space="0" w:color="CBD5E1"/>
          <w:left w:val="single" w:sz="6" w:space="0" w:color="CBD5E1"/>
          <w:bottom w:val="single" w:sz="6" w:space="0" w:color="CBD5E1"/>
          <w:right w:val="single" w:sz="6" w:space="0" w:color="CBD5E1"/>
          <w:insideH w:val="single" w:sz="4" w:space="0" w:color="E2E8F0"/>
          <w:insideV w:val="single" w:sz="4" w:space="0" w:color="E2E8F0"/>
        </w:tblBorders>
        <w:tblCellMar>
          <w:top w:w="100" w:type="dxa"/><w:left w:w="120" w:type="dxa"/>
          <w:bottom w:w="100" w:type="dxa"/><w:right w:w="120" w:type="dxa"/>
        </w:tblCellMar>
      </w:tblPr>
      <w:tr>
        <w:tc><w:tcPr><w:shd w:val="clear" w:color="auto" w:fill="E2E8F0"/></w:tcPr><w:p><w:r><w:rPr><w:b/><w:sz w:val="18"/><w:color w:val="1B365D"/></w:rPr><w:t>Niveau</w:t></w:r></w:p></w:tc>
        <w:tc><w:tcPr><w:shd w:val="clear" w:color="auto" w:fill="E2E8F0"/></w:tcPr><w:p><w:r><w:rPr><w:b/><w:sz w:val="18"/><w:color w:val="1B365D"/></w:rPr><w:t>Recall@5</w:t></w:r></w:p></w:tc>
        <w:tc><w:tcPr><w:shd w:val="clear" w:color="auto" w:fill="E2E8F0"/></w:tcPr><w:p><w:r><w:rPr><w:b/><w:sz w:val="18"/><w:color w:val="1B365D"/></w:rPr><w:t>Exactitude</w:t></w:r></w:p></w:tc>
        <w:tc><w:tcPr><w:shd w:val="clear" w:color="auto" w:fill="E2E8F0"/></w:tcPr><w:p><w:r><w:rPr><w:b/><w:sz w:val="18"/><w:color w:val="1B365D"/></w:rPr><w:t>Abstention</w:t></w:r></w:p></w:tc>
        <w:tc><w:tcPr><w:shd w:val="clear" w:color="auto" w:fill="E2E8F0"/></w:tcPr><w:p><w:r><w:rPr><w:b/><w:sz w:val="18"/><w:color w:val="1B365D"/></w:rPr><w:t>Succès tâches</w:t></w:r></w:p></w:tc>
        <w:tc><w:tcPr><w:shd w:val="clear" w:color="auto" w:fill="E2E8F0"/></w:tcPr><w:p><w:r><w:rPr><w:b/><w:sz w:val="18"/><w:color w:val="1B365D"/></w:rPr><w:t>pass^3</w:t></w:r></w:p></w:tc>
        <w:tc><w:tcPr><w:shd w:val="clear" w:color="auto" w:fill="E2E8F0"/></w:tcPr><w:p><w:r><w:rPr><w:b/><w:sz w:val="18"/><w:color w:val="1B365D"/></w:rPr><w:t>Tokens / req</w:t></w:r></w:p></w:tc>
        <w:tc><w:tcPr><w:shd w:val="clear" w:color="auto" w:fill="E2E8F0"/></w:tcPr><w:p><w:r><w:rPr><w:b/><w:sz w:val="18"/><w:color w:val="1B365D"/></w:rPr><w:t>Latence</w:t></w:r></w:p></w:tc>
      </w:tr>
      <w:tr>
        <w:tc><w:p><w:r><w:rPr><w:b/><w:sz w:val="18"/></w:rPr><w:t>0 · LLM seul</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:rPr><w:sz w:val="18"/></w:rPr><w:t>—</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:rPr><w:b/><w:sz w:val="18"/><w:color w:val="D9381E"/></w:rPr><w:t>5.0%</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:rPr><w:b/><w:sz w:val="18"/><w:color w:val="D9381E"/></w:rPr><w:t>0.0%</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:rPr><w:sz w:val="18"/></w:rPr><w:t>—</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:rPr><w:sz w:val="18"/></w:rPr><w:t>—</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:rPr><w:sz w:val="18"/></w:rPr><w:t>86.1</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:rPr><w:sz w:val="18"/></w:rPr><w:t>0.001s</w:t></w:r></w:p></w:tc>
      </w:tr>
      <w:tr>
        <w:tc><w:p><w:r><w:rPr><w:color w:val="64748B"/><w:sz w:val="18"/></w:rPr><w:t>1 · RAG</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:rPr><w:color w:val="64748B"/><w:sz w:val="18"/></w:rPr><w:t>[Semaine 2]</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:rPr><w:color w:val="64748B"/><w:sz w:val="18"/></w:rPr><w:t>[Semaine 2]</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:rPr><w:color w:val="64748B"/><w:sz w:val="18"/></w:rPr><w:t>[Semaine 2]</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:rPr><w:color w:val="64748B"/><w:sz w:val="18"/></w:rPr><w:t>—</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:rPr><w:color w:val="64748B"/><w:sz w:val="18"/></w:rPr><w:t>—</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:rPr><w:color w:val="64748B"/><w:sz w:val="18"/></w:rPr><w:t>…</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:rPr><w:color w:val="64748B"/><w:sz w:val="18"/></w:rPr><w:t>…</w:t></w:r></w:p></w:tc>
      </w:tr>
      <w:tr>
        <w:tc><w:p><w:r><w:rPr><w:color w:val="64748B"/><w:sz w:val="18"/></w:rPr><w:t>2 · Agent</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:rPr><w:color w:val="64748B"/><w:sz w:val="18"/></w:rPr><w:t>[Semaine 3]</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:rPr><w:color w:val="64748B"/><w:sz w:val="18"/></w:rPr><w:t>[Semaine 3]</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:rPr><w:color w:val="64748B"/><w:sz w:val="18"/></w:rPr><w:t>[Semaine 3]</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:rPr><w:color w:val="64748B"/><w:sz w:val="18"/></w:rPr><w:t>[Semaine 3]</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:rPr><w:color w:val="64748B"/><w:sz w:val="18"/></w:rPr><w:t>[Semaine 3]</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:rPr><w:color w:val="64748B"/><w:sz w:val="18"/></w:rPr><w:t>…</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:rPr><w:color w:val="64748B"/><w:sz w:val="18"/></w:rPr><w:t>…</w:t></w:r></w:p></w:tc>
      </w:tr>
    </w:tbl>
    """
    body_elements.append(results_table)

    body_elements.append(p(
        "Analyse quantitative de l'échec du Niveau 0 (Justification de l'étape suivante RAG) :\n"
        "1. Faible exactitude factuelle (5.0%) : Le LLM seul donne des réponses d'apparence plausibles mais invente ou arrondit "
        "les montants réglementaires (montant de 1 454 € de l'échelon 0bis, 3 070 € de l'aide FNAU, 374,40 € du forfait Imagine R).\n"
        "2. Absence totale d'abstention (0.0%) : Interrogé sur des aides inexistantes (voiliers, lamas), le modèle répond sans hésiter "
        "au lieu de déclarer qu'il ne dispose pas de l'information.\n"
        "3. Incapacité à accomplir des démarches : Le LLM seul ne peut pas exécuter les 10 tâches de calcul et de simulation d'aides.",
        space_before=140
    ))

    # 8. Section 6 : Calendrier et Livrables
    body_elements.append(heading("6. Calendrier Prévisionnel des 4 Semaines", 1))
    body_elements.append(bullet("• Semaine 1 (2 – 8 nov.) [RÉALISÉ] :", "Thème Aides Étudiantes & CROUS, corpus de 6 fiches, banc de 40 tests, Niveau 0 évalué."))
    body_elements.append(bullet("• Semaine 2 (9 – 15 nov.) :", "Implémentation du RAG hybride (TF-IDF + BM25), citations de sources, gain de Recall@5 et exactitude."))
    body_elements.append(bullet("• Semaine 3 (16 – 22 nov.) :", "Implémentation de l'Agent outillé sans framework, règles métier par code, confirmation humaine, métrique pass^3."))
    body_elements.append(bullet("• Semaine 4 (23 – 30 nov.) :", "Extension (Niveau 3), analyse de 5 échecs types, rapport de synthèse final (4 pages) et vidéo de démo."))

    # 9. Section 7 : Reproductibilité
    body_elements.append(heading("7. Dépôt GitHub et Commandes de Reproduction", 1))
    body_elements.append(p("Le code source complet de la Semaine 1 est accessible sur GitHub :"))
    body_elements.append(bullet("• Dépôt GitHub :", "https://github.com/Alexhuang03/Projet-GenIA"))
    body_elements.append(bullet("• Jalon officiel :", "Tag Git 'semaine-1' sur la branche principale 'main'"))
    body_elements.append(p(
        "Commandes d'exécution (100% reproductible sans GPU, mode hors-ligne inclus) :\n"
        "1. Installation : pip install -r requirements.txt\n"
        "2. Reproduction du tableau d'évaluation : python eval.py\n"
        "3. Lancement de l'interface Streamlit : streamlit run app.py"
    ))

    # Assemblage XML final
    document_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
            xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <w:body>
    {"".join(body_elements)}
    <w:sectPr>
      <w:pgSz w:w="11906" w:h="16838"/>
      <w:pgMar w:top="1134" w:right="1134" w:bottom="1134" w:left="1134" w:header="708" w:footer="708" w:gutter="0"/>
    </w:sectPr>
  </w:body>
</w:document>"""

    # Écriture dans le conteneur ZIP .docx
    with zipfile.ZipFile(output_filename, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types)
        z.writestr("_rels/.rels", rels)
        z.writestr("word/_rels/document.xml.rels", doc_rels)
        z.writestr("word/styles.xml", styles_xml)
        z.writestr("word/document.xml", document_xml)

    print(f"Document Word (.docx) généré avec succès : {output_filename}")


if __name__ == "__main__":
    generate_docx()
