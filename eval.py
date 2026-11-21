"""
Évaluation reproductible des niveaux 0 à 3 (python eval.py)
Parcours Texte : Assistant Aides Étudiantes & CROUS

Sur le jeu de test figé data/tests.jsonl (40 cas) :
- 20 questions « dans les documents » : Recall@5, MRR, exactitude, citations ;
- 5 questions « hors documents »     : abstention ;
- 5 demandes ambiguës / hors sujet   : cadrage (refus ou question de précision, aucune action) ;
- 10 tâches multi-étapes (niveaux 2 et 3) : succès vérifié par du code sur l'état final
  (résultats des outils, fichier écrit, confirmation), 3 essais à température TASK_TEMPERATURE → pass^3.
Plus une ablation du retriever (BM25 / dense / hybride), sans LLM.

Sorties : tableau Markdown, results/latest.md, results/eval_<horodatage>.json (détail par cas),
et results/traces_<horodatage>.jsonl (une ligne par exécution).

Usage :
    python eval.py                    # tous les niveaux (~25 min sur GPU portable)
    python eval.py --levels 2,3       # seulement les agents
    python eval.py --limit 2          # essai rapide
"""
import argparse
import json
import re
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.config import TESTS_PATH, RESULTS_DIR, RAG_TOP_K, TASK_TEMPERATURE
from src.llm_client import UnifiedLLMClient
from src.baseline.level0_llm import Level0LLM
from src.rag.retriever import Retriever
from src.rag.engine import RAGEngine
from src.agent.loop import ReActAgent
from src.agent.rewoo import ReWOOAgent
import src.tracker
from src.metrics import contains_keyword, is_abstention, is_faithful, is_refusal_or_clarification, mean, fold

LEVEL_NAMES = {0: "0 · LLM seul", 1: "1 · RAG", 2: "2 · Agent ReAct", 3: "3 · Extension ReWOO"}
TASK_SEEDS = (1, 2, 3)


def load_test_cases() -> List[Dict[str, Any]]:
    with open(TESTS_PATH, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def pct(x: Optional[float]) -> str:
    return "—" if x is None else f"{100 * x:.1f}%"


def reciprocal_rank(docs: List[str], expected: str) -> float:
    return next((1.0 / (i + 1) for i, d in enumerate(docs) if d == expected), 0.0)


# --------------------------------------------------------------------------- retriever seul
def retrieval_ablation(client, cases) -> Dict[str, Dict[str, float]]:
    out = {}
    for mode in ("bm25", "dense", "hybrid"):
        r = Retriever(client, mode=mode)
        rows = []
        for c in cases:
            res = r.retrieve(c["query"], top_k=RAG_TOP_K)
            docs = [x.chunk.doc_name for x in res]
            rows.append({"r1": docs[0] == c["expected_source"], "r5": c["expected_source"] in docs,
                         "mrr": reciprocal_rank(docs, c["expected_source"]),
                         "p5": any(contains_keyword(x.chunk.content, c["expected_keywords"]) for x in res)})
        out[mode] = {"recall_doc@1": mean([x["r1"] for x in rows]), "recall_doc@5": mean([x["r5"] for x in rows]),
                     "mrr": mean([x["mrr"] for x in rows]), "recall_passage@5": mean([x["p5"] for x in rows])}
    return out


# --------------------------------------------------------------------------- exécution d'un cas
def run_case(system, query: str, approve, **kw) -> Dict[str, Any]:
    """Exécute une requête ; si l'agent demande une confirmation, `approve(call)` joue l'étudiant."""
    t0 = time.time()
    res = system.process(query, **kw) if kw else system.process(query)
    total_tokens = res["trace"]["total_tokens"]
    while res.get("status") == "WAITING_CONFIRMATION":
        session = res["session"]
        res = system.resume(session, approve(session.pending))
        total_tokens = res["trace"]["total_tokens"]
    res["_latency"] = time.time() - t0
    res["_tokens"] = total_tokens
    return res


def tools_called(res, effects=("COMPUTE", "WRITE")) -> List[str]:
    return [e["tool"] for e in res.get("tool_log", []) if e.get("effect") in effects and e.get("stage") != "precheck"]


def check_task(case, res) -> Dict[str, Any]:
    """Succès vérifié par du code sur l'état final, pas sur la forme du texte."""
    v = case["task_validation"]
    log = [e for e in res.get("tool_log", []) if e.get("ok")]
    points_results = [e["result"]["total_points_charge"] for e in log if e["tool"] == "calculer_points_charge"]
    checks = {"points_corrects": bool(points_results) and points_results[-1] == v["expected_points"]}
    if "revenu_fiscal" in v:
        checks["echelon_estime"] = any(e["tool"] == "estimer_echelon_bourse"
                                       and e["arguments"].get("points_charge") == v["expected_points"]
                                       and float(e["arguments"].get("revenu_fiscal", -1)) == v["revenu_fiscal"]
                                       for e in log)
    if "loyer" in v:
        checks["aide_logement_estimee"] = any(e["tool"] == "estimer_aide_logement"
                                              and float(e["arguments"].get("loyer", -1)) == v["loyer"] for e in log)
    asked = [c["tool"] for c in res.get("confirmations", [])]
    if v["require_write"]:
        writes = res.get("writes", [])
        checks["ecriture_confirmee"] = bool(asked) and any(
            w["arguments"]["points_charge"] == v["expected_points"] for w in writes)
    else:
        checks["aucune_ecriture_demandee"] = not asked
    # aucun outil ne doit recevoir une donnée que l'étudiant n'a pas fournie (revenu ou loyer inventé)
    checks["aucune_valeur_inventee"] = not any(
        (e["tool"] == "estimer_echelon_bourse" and "revenu_fiscal" not in v)
        or (e["tool"] == "estimer_aide_logement" and "loyer" not in v) for e in log)
    # la réponse donne bien le total à l'étudiant (le nombre attendu, pas « 15 » ni « 5,5 »)
    answer = fold(res["response"])
    checks["points_dans_reponse"] = bool(re.search(rf"(?<![\d,.]){v['expected_points']}(?![\d,.]\d|\d)", answer)) or (
        v["expected_points"] == 0 and bool(re.search(r"aucun point|pas de points?", answer)))
    return {"success": all(checks.values()), "checks": checks}


def summarize_row(case, res, level) -> Dict[str, Any]:
    text = res["response"]
    row = {"id": case["id"], "category": case["category"], "query": case["query"], "response": text,
           "abstained": is_abstention(text), "latency_s": round(res["_latency"], 3), "tokens": res["_tokens"],
           "llm_calls": res.get("llm_calls", 1), "status": res.get("status", "SUCCESS")}
    if level >= 1:
        row.update(citations=res.get("citations", []), citations_invalides=res.get("citations_invalides", []),
                   retrieved_docs=res.get("retrieved_docs", []))
    if level >= 2:
        row["tools"] = [(e["tool"], e["arguments"], e.get("ok"), e.get("error")) for e in res.get("tool_log", [])]
        row["confirmations"] = res.get("confirmations", [])
    cat = case["category"]
    if cat == "in_corpus":
        row["correct"] = (not row["abstained"]) and contains_keyword(text, case["expected_keywords"])
        if level >= 1:
            docs = res.get("retrieved_docs", [])
            row["recall_doc@5"] = case["expected_source"] in docs
            row["rr"] = reciprocal_rank(docs, case["expected_source"])
            row["recall_passage@5"] = any(contains_keyword(ch["content"], case["expected_keywords"])
                                          for ch in res.get("retrieved_chunks", []))
            row["cites_expected_source"] = case["expected_source"] in res.get("citations_valides", [])
            evidence = " ".join([case["query"]] + [ch["content"] for ch in res.get("retrieved_chunks", [])]
                                + [json.dumps(e.get("result", {}), ensure_ascii=False) for e in res.get("tool_log", [])])
            row["faithful"] = is_faithful(text, evidence)
    elif cat == "ambiguous_or_out_of_scope":
        row["cadrage_ok"] = (not tools_called(res)) and is_refusal_or_clarification(text)
    return row


def run_level(level: int, system, cases_by_cat, run_tasks: bool) -> Dict[str, Any]:
    details, task_runs = [], []
    refuse_all = lambda call: False  # hors tâches, l'étudiant n'a rien demandé à enregistrer
    for case in cases_by_cat["in_corpus"] + cases_by_cat["out_of_corpus"] + cases_by_cat["ambiguous_or_out_of_scope"]:
        res = run_case(system, case["query"], refuse_all)
        row = summarize_row(case, res, level)
        details.append(row)
        tag = "abst." if row["abstained"] else {True: "OK", False: "--"}.get(row.get("correct", row.get("cadrage_ok")), "rép.")
        print(f"  [N{level}] {case['id']:<7} {tag:<5} {row['latency_s']:5.1f}s {row['llm_calls']} appel(s)  {row['response'][:60]!r}")

    if run_tasks:
        for case in cases_by_cat["multi_step_task"]:
            # L'étudiant simulé confirme seulement ce qu'il a demandé
            approve = (lambda call: True) if case["task_validation"]["require_write"] else (lambda call: False)
            runs = []
            for seed in TASK_SEEDS:
                res = run_case(system, case["query"], approve, temperature=TASK_TEMPERATURE, seed=seed)
                row = summarize_row(case, res, level)
                row.update(seed=seed, **check_task(case, res))
                runs.append(row)
            task_runs.append({"id": case["id"], "runs": runs, "pass3": all(r["success"] for r in runs)})
            marks = "".join("✓" if r["success"] else "✗" for r in runs)
            print(f"  [N{level}] {case['id']:<7} {marks}  {mean([r['latency_s'] for r in runs]):5.1f}s  "
                  f"échecs : {[k for r in runs for k, ok in r['checks'].items() if not ok]}")

    docs = [d for d in details if d["category"] == "in_corpus"]
    outs = [d for d in details if d["category"] == "out_of_corpus"]
    ambs = [d for d in details if d["category"] == "ambiguous_or_out_of_scope"]
    answered = [d for d in docs if not d["abstained"]]
    all_runs = [r for t in task_runs for r in t["runs"]]
    every = details + all_runs
    s: Dict[str, Any] = {
        "exactitude": mean([d["correct"] for d in docs]),
        "abstention": mean([d["abstained"] for d in outs]),
        "fausses_abstentions": mean([d["abstained"] for d in docs]),
        "cadrage": mean([d["cadrage_ok"] for d in ambs]),
        "tokens_req": mean([d["tokens"] for d in every]),
        "latence_s": mean([d["latency_s"] for d in every]),
        "appels_llm_req": mean([d["llm_calls"] for d in every]),
    }
    if level >= 1:
        s.update(recall_doc5=mean([d["recall_doc@5"] for d in docs]), mrr=mean([d["rr"] for d in docs]),
                 recall_passage5=mean([d["recall_passage@5"] for d in docs]),
                 citation_correcte=mean([d["cites_expected_source"] for d in answered]),
                 fidelite=mean([d["faithful"] for d in answered]),
                 citation_inventee=mean([bool(d["citations_invalides"]) for d in every]))
    if task_runs:
        s.update(succes_taches=mean([r["success"] for r in all_runs]), pass3=mean([t["pass3"] for t in task_runs]),
                 tokens_tache=mean([r["tokens"] for r in all_runs]), latence_tache=mean([r["latency_s"] for r in all_runs]),
                 appels_llm_tache=mean([r["llm_calls"] for r in all_runs]),
                 # garde-fou : toute écriture doit avoir été précédée d'une confirmation acceptée
                 ecritures_sans_confirmation=sum(1 for r in every for t in r.get("tools", [])
                                                 if t[0] == "enregistrer_simulation" and t[2]
                                                 and not any(c["approved"] for c in r.get("confirmations", []))))
    return {"summary": s, "details": details, "tasks": task_runs}


# --------------------------------------------------------------------------- tableaux
def markdown_table(results: Dict[int, Dict[str, Any]]) -> str:
    lines = ["| Niveau | Recall@5 | MRR | Exactitude | Abstention | Cadrage (amb.) | Citation correcte | Fidélité | Succès tâches | pass^3 | Appels LLM / req | Tokens / req | Latence |",
             "|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|"]
    for level in sorted(results):
        s = results[level]["summary"]
        lines.append(f"| **{LEVEL_NAMES[level]}** | {pct(s.get('recall_doc5'))} | "
                     f"{'—' if 'mrr' not in s else f'{s['mrr']:.2f}'} | {pct(s['exactitude'])} | {pct(s['abstention'])} | "
                     f"{pct(s['cadrage'])} | {pct(s.get('citation_correcte'))} | {pct(s.get('fidelite'))} | {pct(s.get('succes_taches'))} | "
                     f"{pct(s.get('pass3'))} | {s['appels_llm_req']:.1f} | {s['tokens_req']:.0f} | {s['latence_s']:.2f}s |")
    return "\n".join(lines)


def agent_table(results) -> str:
    lines = ["| Niveau | Succès tâches | pass^3 | Appels LLM / tâche | Tokens / tâche | Latence / tâche | Écritures sans confirmation |",
             "|:---|:---:|:---:|:---:|:---:|:---:|:---:|"]
    for level in (2, 3):
        if level in results and "pass3" in results[level]["summary"]:
            s = results[level]["summary"]
            lines.append(f"| **{LEVEL_NAMES[level]}** | {pct(s['succes_taches'])} | {pct(s['pass3'])} | "
                         f"{s['appels_llm_tache']:.1f} | {s['tokens_tache']:.0f} | {s['latence_tache']:.1f}s | "
                         f"{s['ecritures_sans_confirmation']} |")
    return "\n".join(lines)


def ablation_table(abl) -> str:
    lines = ["| Retriever | Recall@1 (doc) | Recall@5 (doc) | MRR | Recall@5 (passage) |", "|:---|:---:|:---:|:---:|:---:|"]
    for mode, m in abl.items():
        lines.append(f"| {mode} | {pct(m['recall_doc@1'])} | {pct(m['recall_doc@5'])} | {m['mrr']:.2f} | {pct(m['recall_passage@5'])} |")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--levels", default="0,1,2,3")
    ap.add_argument("--retriever", default="hybrid", choices=["bm25", "dense", "hybrid"])
    ap.add_argument("--limit", type=int, default=0, help="nombre max de cas par catégorie (0 = tous)")
    args = ap.parse_args()
    levels = [int(x) for x in args.levels.split(",") if x.strip()]

    client = UnifiedLLMClient()
    if client.is_mock:
        raise SystemExit("Refus : le mode mock ne produit pas de vraies réponses. Lancez Ollama (LLM_PROVIDER=ollama).")

    cases = load_test_cases()
    by_cat: Dict[str, List[Dict[str, Any]]] = {}
    for c in cases:
        by_cat.setdefault(c["category"], []).append(c)
    if args.limit:
        by_cat = {k: v[:args.limit] for k, v in by_cat.items()}

    print("=" * 100)
    print(f"Évaluation · LLM {client.provider}:{client.model} · retriever {args.retriever} · top-{RAG_TOP_K} · "
          + ", ".join(f"{k}={len(v)}" for k, v in by_cat.items()))
    print("=" * 100)
    run_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    src.tracker.TRACES_PATH = RESULTS_DIR / f"traces_{run_stamp}.jsonl"  # traces brutes de cette évaluation
    client.generate("Bonjour", system_prompt="Réponds en un mot.")  # chargement du modèle hors chrono

    print("\nAblation du retriever (sans LLM)...")
    ablation = retrieval_ablation(client, by_cat["in_corpus"])
    retriever = Retriever(client, mode=args.retriever)
    systems = {0: Level0LLM(client), 1: RAGEngine(client, retriever),
               2: ReActAgent(client, retriever), 3: ReWOOAgent(client, retriever)}

    results: Dict[int, Dict[str, Any]] = {}
    for level in levels:
        print(f"\n{LEVEL_NAMES[level]}")
        results[level] = run_level(level, systems[level], by_cat, run_tasks=level >= 2)

    table, agents, abl = markdown_table(results), agent_table(results), ablation_table(ablation)
    print("\n" + table + "\n\n" + agents + "\n\n" + abl)

    stamp = run_stamp
    meta = {"date": stamp, "provider": client.provider, "model": client.model, "retriever": args.retriever,
            "top_k": RAG_TOP_K, "task_temperature": TASK_TEMPERATURE, "task_seeds": TASK_SEEDS,
            "n_cases": {k: len(v) for k, v in by_cat.items()}}
    payload = {"meta": meta, "retrieval_ablation": ablation, "levels": {str(k): v for k, v in results.items()}}
    (RESULTS_DIR / f"eval_{stamp}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str),
                                                     encoding="utf-8")
    (RESULTS_DIR / "latest.md").write_text(
        f"# Résultats · {stamp}\n\nLLM `{client.provider}:{client.model}` · retriever `{args.retriever}` · top-{RAG_TOP_K} · "
        f"cas : {meta['n_cases']} · tâches : 3 essais à température {TASK_TEMPERATURE} (graines {TASK_SEEDS})\n\n"
        f"{table}\n\n## Agents sur les 10 tâches\n\n{agents}\n\n## Ablation du retriever\n\n{abl}\n", encoding="utf-8")
    print(f"\nRésultats enregistrés dans results/eval_{stamp}.json et results/latest.md")


if __name__ == "__main__":
    main()
