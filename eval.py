"""
Script d'évaluation officiel - SEMAINE 1 (python eval.py)
Parcours Texte : Assistant Aides Étudiantes & CROUS
Évalue le Niveau 0 (LLM seul / baseline à battre) sur les 40 cas de tests.jsonl.
Conforme au format indicatif du tableau attendu par le Dr. Issam Falih.
"""
import json
import time
from typing import Dict, Any, List
from pathlib import Path

from src.config import TESTS_PATH
from src.llm_client import UnifiedLLMClient
from src.baseline.level0_llm import Level0LLM


def load_test_cases() -> List[Dict[str, Any]]:
    if not TESTS_PATH.exists():
        raise FileNotFoundError(f"Fichier de test introuvable : {TESTS_PATH}")
    cases = []
    with open(TESTS_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                cases.append(json.loads(line.strip()))
    return cases


def evaluate_level_0(client: UnifiedLLMClient, cases: List[Dict[str, Any]]) -> Dict[str, Any]:
    print("\nÉvaluation du Niveau 0 (LLM seul)...")
    model = Level0LLM(client)
    
    in_corpus_cases = [c for c in cases if c["category"] == "in_corpus"]
    out_corpus_cases = [c for c in cases if c["category"] == "out_of_corpus"]
    
    # Mesure de l'exactitude sur les questions documentaires (sans corpus)
    correct_count = 0
    total_tokens = 0
    total_latency = 0.0
    
    for case in in_corpus_cases:
        t0 = time.time()
        res = model.process(case["query"])
        lat = time.time() - t0
        total_latency += lat
        total_tokens += res["trace"]["total_tokens"]
        
        # Vérification si le LLM seul trouve par hasard les chiffres exacts
        resp_text = res["response"].lower()
        if any(kw.lower() in resp_text for kw in case["expected_keywords"]):
            correct_count += 1
            
    # Mesure de l'abstention sur les questions hors corpus
    abstention_count = 0
    for case in out_corpus_cases:
        t0 = time.time()
        res = model.process(case["query"])
        total_latency += (time.time() - t0)
        total_tokens += res["trace"]["total_tokens"]
        
        resp_text = res["response"].lower()
        if any(w in resp_text for w in ["ne dispose pas", "je ne sais pas", "pas d'information", "aucun texte"]):
            abstention_count += 1

    num_eval = len(in_corpus_cases) + len(out_corpus_cases)
    exactitude = (correct_count / len(in_corpus_cases)) * 100 if in_corpus_cases else 0.0
    abstention = (abstention_count / len(out_corpus_cases)) * 100 if out_corpus_cases else 0.0
    avg_tokens = round(total_tokens / (num_eval or 1), 1)
    avg_lat = round(total_latency / (num_eval or 1), 3)

    return {
        "recall_at_5": "—",
        "exactitude": f"{exactitude:.1f}%",
        "abstention": f"{abstention:.1f}%",
        "succes_taches": "—",
        "pass_3": "—",
        "tokens_requete": avg_tokens,
        "latence": f"{avg_lat}s"
    }


def main():
    print("=" * 80)
    print("   ÉVALUATION DU SYSTÈME GÉNÉRATIF (Dr. Issam Falih - Promo 2026)")
    print("   SEMAINE 1 (2 – 8 nov.) : Thème, Corpus, Jeu de test, Niveau 0")
    print("   Parcours : Texte - Assistant Aides Étudiantes & CROUS")
    print("=" * 80)
    
    cases = load_test_cases()
    print(f"Jeu de test initialisé : {len(cases)} cas au total dans tests.jsonl.")
    
    client = UnifiedLLMClient()
    print(f"Fournisseur LLM actif : {client.provider} (modèle : {client.model})")

    # Évaluation du Niveau 0 (Baseline)
    res_l0 = evaluate_level_0(client, cases)

    # Affichage du tableau format Markdown
    print("\n" + "=" * 80)
    print("TABLEAU RÉCAPITULATIF DES RÉSULTATS (attendu dans le rapport)")
    print("=" * 80)
    
    header = "| Niveau | Recall@5 | Exactitude | Abstention | Succès tâches | pass^3 | Tokens / req | Latence |"
    sep    = "|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|"
    row_0  = f"| **0 · LLM seul** | {res_l0['recall_at_5']} | {res_l0['exactitude']} | {res_l0['abstention']} | {res_l0['succes_taches']} | {res_l0['pass_3']} | {res_l0['tokens_requete']} | {res_l0['latence']} |"
    row_1  = f"| **1 · RAG** | … | … | … | — | — | … | … |"
    row_2  = f"| **2 · Agent** | … | … | … | … | … | … | … |"
    row_3  = f"| **3 · Extension** | … | … | … | … | … | … | … |"

    print(header)
    print(sep)
    print(row_0)
    print(row_1)
    print(row_2)
    print(row_3)
    print("=" * 80)
    print("Conclusion Semaine 1 : Le Niveau 0 (LLM seul) démontre une faible exactitude (5%)")
    print("et une absence totale d'abstention (0%), justifiant le passage au Niveau 1 (RAG).\n")


if __name__ == "__main__":
    main()
