"""
Évaluation reproductible du système (python eval.py)
Parcours Texte : Assistant Aides Étudiantes & CROUS

Mesure sur le jeu de test figé data/tests.jsonl :
- Niveau 0 (LLM seul) et Niveau 1 (RAG) sur les 20 questions « dans les documents »
  et les 5 questions « hors documents » ;
- une ablation du retriever (BM25 / dense / hybride), sans appel au LLM.
Les tâches multi-étapes (Niveau 2, agent) seront ajoutées en semaine 3.

Sorties : tableau Markdown à l'écran, results/latest.md, et results/eval_<horodatage>.json
(résumé + détail de chaque cas : réponse, passages récupérés, citations), pour l'analyse d'échecs.

Usage :
    python eval.py                       # niveaux 0 et 1, retriever hybride
    python eval.py --levels 1 --retriever bm25
    python eval.py --limit 5             # essai rapide sur 5 cas par catégorie
"""
import argparse
import json
import time
from datetime import datetime
from typing import Any, Dict, List

from src.config import TESTS_PATH, RESULTS_DIR, RAG_TOP_K
from src.llm_client import UnifiedLLMClient
from src.baseline.level0_llm import Level0LLM
from src.rag.retriever import Retriever
from src.rag.engine import RAGEngine
from src.metrics import contains_keyword, is_abstention, mean


def load_test_cases() -> List[Dict[str, Any]]:
    with open(TESTS_PATH, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def pct(x: float) -> str:
    return f"{100 * x:.1f}%"


# --------------------------------------------------------------------------- retriever
def retrieval_ablation(client, cases) -> Dict[str, Dict[str, float]]:
    """Recall@5 de chaque mode de recherche, sans LLM.
    - niveau document : le fichier attendu figure parmi les 5 passages ;
    - niveau passage  : un des 5 passages contient la réponse attendue (mot-clé de référence)."""
    out = {}
    for mode in ("bm25", "dense", "hybrid"):
        r = Retriever(client, mode=mode)
        doc_hits, passage_hits, top1 = [], [], []
        for c in cases:
            res = r.retrieve(c["query"], top_k=RAG_TOP_K)
            docs = [x.chunk.doc_name for x in res]
            doc_hits.append(c["expected_source"] in docs)
            top1.append(docs[0] == c["expected_source"])
            passage_hits.append(any(contains_keyword(x.chunk.content, c["expected_keywords"]) for x in res))
        out[mode] = {"recall_doc@1": mean(top1), "recall_doc@5": mean(doc_hits),
                     "recall_passage@5": mean(passage_hits)}
    return out


# --------------------------------------------------------------------------- niveaux
def run_level(level: int, system, doc_cases, abs_cases) -> Dict[str, Any]:
    details = []
    for case in doc_cases + abs_cases:
        t0 = time.time()
        res = system.process(case["query"])
        latency = time.time() - t0
        text = res["response"]
        abstained = is_abstention(text)
        row = {
            "id": case["id"], "category": case["category"], "query": case["query"],
            "response": text, "abstained": abstained, "latency_s": round(latency, 3),
            "tokens": res["trace"]["total_tokens"],
        }
        if case["category"] == "in_corpus":
            row["expected_source"] = case["expected_source"]
            row["correct"] = (not abstained) and contains_keyword(text, case["expected_keywords"])
            if level >= 1:
                row["retrieved_docs"] = res["retrieved_docs"]
                row["recall_doc@5"] = case["expected_source"] in res["retrieved_docs"]
                row["recall_passage@5"] = any(contains_keyword(ch["content"], case["expected_keywords"])
                                              for ch in res["retrieved_chunks"])
                row["cites_expected_source"] = case["expected_source"] in res["citations_valides"]
        if level >= 1:
            row["citations"] = res["citations"]
            row["citations_invalides"] = res["citations_invalides"]
            row["retrieved_chunks"] = [ch["chunk_id"] for ch in res["retrieved_chunks"]]
        details.append(row)
        status = "abst." if abstained else ("OK" if row.get("correct") else ("--" if "correct" in row else "rép."))
        print(f"  [N{level}] {case['id']:<7} {status:<5} {latency:5.1f}s  {text[:70]!r}")

    docs = [d for d in details if d["category"] == "in_corpus"]
    outs = [d for d in details if d["category"] == "out_of_corpus"]
    answered = [d for d in docs if not d["abstained"]]
    summary = {
        "exactitude": mean([d["correct"] for d in docs]),
        "abstention": mean([d["abstained"] for d in outs]),
        "fausses_abstentions": mean([d["abstained"] for d in docs]),
        "tokens_req": mean([d["tokens"] for d in details]),
        "latence_s": mean([d["latency_s"] for d in details]),
    }
    if level >= 1:
        summary["recall_doc@5"] = mean([d["recall_doc@5"] for d in docs])
        summary["recall_passage@5"] = mean([d["recall_passage@5"] for d in docs])
        # parmi les réponses données, part qui cite le bon document
        summary["citation_correcte"] = mean([d["cites_expected_source"] for d in answered])
        # part des réponses (toutes catégories) contenant au moins une source inventée
        summary["citation_inventee"] = mean([bool(d["citations_invalides"]) for d in details])
    return {"summary": summary, "details": details}


# --------------------------------------------------------------------------- tableau
def markdown_table(results: Dict[int, Dict[str, Any]]) -> str:
    lines = [
        "| Niveau | Recall@5 (doc / passage) | Exactitude | Abstention | Fausses abst. | Citation correcte | Source inventée | Succès tâches | pass^3 | Tokens / req | Latence |",
        "|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|",
    ]
    names = {0: "0 · LLM seul", 1: "1 · RAG"}
    for level in (0, 1):
        if level not in results:
            continue
        s = results[level]["summary"]
        recall = f"{pct(s['recall_doc@5'])} / {pct(s['recall_passage@5'])}" if level >= 1 else "—"
        cit = pct(s["citation_correcte"]) if level >= 1 else "—"
        inv = pct(s["citation_inventee"]) if level >= 1 else "—"
        lines.append(
            f"| **{names[level]}** | {recall} | {pct(s['exactitude'])} | {pct(s['abstention'])} | "
            f"{pct(s['fausses_abstentions'])} | {cit} | {inv} | — | — | {s['tokens_req']:.0f} | {s['latence_s']:.2f}s |")
    lines.append("| **2 · Agent** | … | … | … | … | … | … | … | … | … | … |")
    lines.append("| **3 · Extension** | … | … | … | … | … | … | … | … | … | … |")
    return "\n".join(lines)


def ablation_table(abl: Dict[str, Dict[str, float]]) -> str:
    lines = ["| Retriever | Recall@1 (doc) | Recall@5 (doc) | Recall@5 (passage) |", "|:---|:---:|:---:|:---:|"]
    for mode, m in abl.items():
        lines.append(f"| {mode} | {pct(m['recall_doc@1'])} | {pct(m['recall_doc@5'])} | {pct(m['recall_passage@5'])} |")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--levels", default="0,1", help="niveaux à évaluer, ex. 0,1")
    ap.add_argument("--retriever", default="hybrid", choices=["bm25", "dense", "hybrid"])
    ap.add_argument("--limit", type=int, default=0, help="nombre max de cas par catégorie (0 = tous)")
    args = ap.parse_args()
    levels = [int(x) for x in args.levels.split(",") if x.strip()]

    client = UnifiedLLMClient()
    if client.is_mock:
        raise SystemExit("Refus : le mode mock ne produit pas de vraies réponses. "
                         "Lancez Ollama (LLM_PROVIDER=ollama) ou configurez une clé d'API.")

    cases = load_test_cases()
    doc_cases = [c for c in cases if c["category"] == "in_corpus"]
    abs_cases = [c for c in cases if c["category"] == "out_of_corpus"]
    if args.limit:
        doc_cases, abs_cases = doc_cases[:args.limit], abs_cases[:args.limit]

    print("=" * 90)
    print(f"Évaluation · LLM {client.provider}:{client.model} · retriever {args.retriever} · top-{RAG_TOP_K}")
    print(f"{len(doc_cases)} questions dans les documents, {len(abs_cases)} hors documents")
    print("=" * 90)

    client.generate("Bonjour", system_prompt="Réponds en un mot.")  # chargement du modèle hors chrono

    print("\nAblation du retriever (sans LLM)...")
    ablation = retrieval_ablation(client, doc_cases)

    results: Dict[int, Dict[str, Any]] = {}
    if 0 in levels:
        print("\nNiveau 0 · LLM seul")
        results[0] = run_level(0, Level0LLM(client), doc_cases, abs_cases)
    if 1 in levels:
        print(f"\nNiveau 1 · RAG ({args.retriever})")
        engine = RAGEngine(client, Retriever(client, mode=args.retriever))
        results[1] = run_level(1, engine, doc_cases, abs_cases)

    table, abl = markdown_table(results), ablation_table(ablation)
    print("\n" + table + "\n\n" + abl)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    meta = {"date": stamp, "provider": client.provider, "model": client.model,
            "retriever": args.retriever, "top_k": RAG_TOP_K,
            "n_in_corpus": len(doc_cases), "n_out_of_corpus": len(abs_cases)}
    payload = {"meta": meta, "retrieval_ablation": ablation,
               "levels": {str(k): v for k, v in results.items()}}
    (RESULTS_DIR / f"eval_{stamp}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    (RESULTS_DIR / "latest.md").write_text(
        f"# Résultats · {stamp}\n\nLLM : `{client.provider}:{client.model}` · retriever : `{args.retriever}` · "
        f"top-{RAG_TOP_K} · {len(doc_cases)} questions dans les documents, {len(abs_cases)} hors documents\n\n"
        f"{table}\n\n## Ablation du retriever\n\n{abl}\n", encoding="utf-8")
    print(f"\nRésultats enregistrés dans results/eval_{stamp}.json et results/latest.md")


if __name__ == "__main__":
    main()
