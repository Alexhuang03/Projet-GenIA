# Résultats · 20261121_144514

LLM `ollama:qwen2.5:7b` · retriever `hybrid` · top-5 · cas : {'in_corpus': 20, 'out_of_corpus': 5, 'multi_step_task': 10, 'ambiguous_or_out_of_scope': 5} · tâches : 3 essais à température 0.7 (graines (1, 2, 3))

| Niveau | Recall@5 | MRR | Exactitude | Abstention | Cadrage (amb.) | Citation correcte | Fidélité | Succès tâches | pass^3 | Appels LLM / req | Tokens / req | Latence |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **0 · LLM seul** | — | — | 5.0% | 20.0% | 80.0% | — | — | — | — | 1.0 | 245 | 4.09s |
| **1 · RAG** | 100.0% | 1.00 | 100.0% | 100.0% | 0.0% | 95.0% | 100.0% | — | — | 1.0 | 1220 | 5.25s |
| **2 · Agent ReAct** | 100.0% | 1.00 | 90.0% | 100.0% | 100.0% | 61.1% | 100.0% | 60.0% | 50.0% | 2.3 | 3574 | 9.11s |
| **3 · Extension ReWOO** | 100.0% | 1.00 | 95.0% | 100.0% | 100.0% | 89.5% | 100.0% | 80.0% | 80.0% | 2.0 | 2282 | 8.54s |

## Agents sur les 10 tâches

| Niveau | Succès tâches | pass^3 | Appels LLM / tâche | Tokens / tâche | Latence / tâche | Écritures sans confirmation |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **2 · Agent ReAct** | 60.0% | 50.0% | 2.7 | 4016 | 10.5s | 0 |
| **3 · Extension ReWOO** | 80.0% | 80.0% | 2.0 | 2149 | 9.0s | 0 |

## Ablation du retriever

| Retriever | Recall@1 (doc) | Recall@5 (doc) | MRR | Recall@5 (passage) |
|:---|:---:|:---:|:---:|:---:|
| bm25 | 100.0% | 100.0% | 1.00 | 100.0% |
| dense | 95.0% | 100.0% | 0.97 | 100.0% |
| hybrid | 100.0% | 100.0% | 1.00 | 100.0% |
