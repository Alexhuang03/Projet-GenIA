# Résultats · 20261114_091407

LLM : `ollama:qwen2.5:7b` · retriever : `hybrid` · top-5 · 20 questions dans les documents, 5 hors documents

| Niveau | Recall@5 (doc / passage) | Exactitude | Abstention | Fausses abst. | Citation correcte | Source inventée | Succès tâches | pass^3 | Tokens / req | Latence |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **0 · LLM seul** | — | 5.0% | 20.0% | 0.0% | — | — | — | — | 253 | 4.29s |
| **1 · RAG** | 100.0% / 100.0% | 100.0% | 100.0% | 0.0% | 95.0% | 0.0% | — | — | 1225 | 5.44s |
| **2 · Agent** | … | … | … | … | … | … | … | … | … | … |
| **3 · Extension** | … | … | … | … | … | … | … | … | … | … |

## Ablation du retriever

| Retriever | Recall@1 (doc) | Recall@5 (doc) | Recall@5 (passage) |
|:---|:---:|:---:|:---:|
| bm25 | 100.0% | 100.0% | 100.0% |
| dense | 95.0% | 100.0% | 100.0% |
| hybrid | 100.0% | 100.0% | 100.0% |
