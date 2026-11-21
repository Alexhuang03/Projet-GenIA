"""
Construit report/rapport.pdf à partir de report/rapport.html.
Les marqueurs {{TABLE_NIVEAUX}}, {{TABLE_AGENTS}}, {{TABLE_ABLATION}} et {{META}} sont remplacés
par les chiffres du dernier résultat d'évaluation (results/eval_*.json) : le rapport ne contient
aucun chiffre recopié à la main. Usage : python report/build_report.py
"""
import glob
import json
import re
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parent.parent
HERE = ROOT / "report"
NAMES = {"0": "0 · LLM seul", "1": "1 · RAG", "2": "2 · Agent ReAct", "3": "3 · ReWOO (ext.)"}


def pct(x):
    return "—" if x is None else f"{100 * x:.0f} %"


def table(headers, rows):
    head = "".join(f"<th>{h}</th>" for h in headers)
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f"<table><tr>{head}</tr>{body}</table>"


def build_tables(data):
    lv = data["levels"]
    rows = []
    for k in sorted(lv):
        s = lv[k]["summary"]
        rows.append([f"<b>{NAMES[k]}</b>", pct(s.get("recall_doc5")), f"{s['mrr']:.2f}" if "mrr" in s else "—",
                     pct(s["exactitude"]), pct(s["abstention"]), pct(s["cadrage"]), pct(s.get("citation_correcte")), pct(s.get("fidelite")),
                     pct(s.get("succes_taches")), pct(s.get("pass3")), f"{s['appels_llm_req']:.1f}",
                     f"{s['tokens_req']:.0f}", f"{s['latence_s']:.1f} s"])
    niveaux = table(["Niveau", "Recall@5", "MRR", "Exactitude", "Abstention", "Cadrage", "Citation", "Fidélité",
                     "Succès tâches", "pass^3", "Appels LLM", "Tokens / req", "Latence"], rows)
    rows = []
    for k in ("2", "3"):
        if k in lv and "pass3" in lv[k]["summary"]:
            s = lv[k]["summary"]
            per_task = " ".join(("✓" if t["pass3"] else "✗") for t in lv[k]["tasks"])
            rows.append([f"<b>{NAMES[k]}</b>", pct(s["succes_taches"]), pct(s["pass3"]), per_task,
                         f"{s['appels_llm_tache']:.1f}", f"{s['tokens_tache']:.0f}", f"{s['latence_tache']:.1f} s",
                         str(s["ecritures_sans_confirmation"])])
    agents = table(["Agent", "Succès (30 essais)", "pass^3", "pass^3 par tâche (1→10)", "Appels LLM",
                    "Tokens", "Latence", "Écritures sans confirmation"], rows)
    abl = data["retrieval_ablation"]
    ablation = table(["Retriever", "Recall@1", "Recall@5", "MRR", "Recall@5 passage"],
                     [[m, pct(v["recall_doc@1"]), pct(v["recall_doc@5"]), f"{v['mrr']:.2f}", pct(v["recall_passage@5"])]
                      for m, v in abl.items()])
    m = data["meta"]
    meta = (f"LLM <code>{m['provider']}:{m['model']}</code>, recherche <code>{m['retriever']}</code> top-{m['top_k']}, "
            f"tâches : 3 essais à température {str(m['task_temperature']).replace('.', ',')} (graines {', '.join(map(str, m['task_seeds']))}), "
            f"évaluation du {m['date'][6:8]}/{m['date'][4:6]}/{m['date'][:4]}.")
    return {"TABLE_NIVEAUX": niveaux, "TABLE_AGENTS": agents, "TABLE_ABLATION": ablation, "META": meta}


CSS = """
body { font-family: sans-serif; font-size: 10pt; line-height: 1.32; color: #111; }
h1 { font-size: 16pt; margin: 0 0 2pt 0; }
h2 { font-size: 12pt; margin: 9pt 0 3pt 0; color: #1f3d66; }
h3 { font-size: 10.5pt; margin: 4pt 0 1pt 0; }
p { margin: 0 0 3pt 0; text-align: justify; }
ul { margin: 0 0 3pt 0; padding-left: 12pt; }
li { margin: 0 0 1pt 0; }
table { border-collapse: collapse; margin: 2pt 0 4pt 0; width: 100%; }
th, td { border: 0.5pt solid #999; padding: 2pt 3pt; font-size: 8.2pt; text-align: center; }
th { font-weight: bold; color: #1f3d66; }
code { font-family: monospace; font-size: 9pt; }
.sub { color: #444; font-size: 9pt; }
.small { font-size: 8.8pt; color: #333; }
"""


def main():
    files = sorted(glob.glob(str(ROOT / "results" / "eval_*.json")))
    data = json.loads(Path(files[-1]).read_text(encoding="utf-8"))
    html = (HERE / "rapport.html").read_text(encoding="utf-8")
    for key, value in build_tables(data).items():
        html = html.replace("{{" + key + "}}", value)
    left = re.findall(r"\{\{\w+\}\}", html)
    if left:
        raise SystemExit(f"Marqueurs non remplacés : {left}")

    archive = pymupdf.Archive(str(HERE))
    story = pymupdf.Story(html=html, user_css=CSS, archive=archive)
    out = HERE / "rapport.pdf"
    writer = pymupdf.DocumentWriter(str(out))
    page, rect = pymupdf.paper_rect("a4"), pymupdf.paper_rect("a4") + (36, 34, -36, -34)
    more, pages = True, 0
    while more:
        dev = writer.begin_page(page)
        more, _ = story.place(rect)
        story.draw(dev)
        writer.end_page()
        pages += 1
    writer.close()
    print(f"{out} : {pages} page(s) (source : {Path(files[-1]).name})")
    if pages > 4:
        print("ATTENTION : le sujet limite le rapport à 4 pages.")


if __name__ == "__main__":
    main()
