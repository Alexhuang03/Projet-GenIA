"""
Configuration globale du projet - Assistant IA Générative pour les Aides Étudiantes
"""
import os
from pathlib import Path

# Chemins de base
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CORPUS_DIR = DATA_DIR / "corpus"
TESTS_PATH = DATA_DIR / "tests.jsonl"
TRACES_PATH = DATA_DIR / "traces.jsonl"
EXPORTS_DIR = BASE_DIR / "exports"

EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

INDEX_DIR = DATA_DIR / "index"     # cache des embeddings du corpus
RESULTS_DIR = BASE_DIR / "results" # sorties de eval.py (résumé + détail par cas)
INDEX_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Paramètres RAG (Niveau 1)
RAG_CHUNK_SIZE = 500          # Taille cible (caractères) avant de couper une longue section
RAG_TOP_K = 5                 # Passages injectés dans le prompt (= k du Recall@5)
RAG_RETRIEVER = os.getenv("RAG_RETRIEVER", "hybrid")  # "bm25", "dense" ou "hybrid"
RAG_RRF_K = 60                # Constante de la fusion Reciprocal Rank Fusion
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "bge-m3")

# Paramètres Agent
AGENT_MAX_STEPS = 5           # Nombre maximal de tours dans la boucle ReAct
MAX_TOKENS_PER_CALL = 1000

# Paramètres LLM
DEFAULT_PROVIDER = os.getenv("LLM_PROVIDER", "ollama") # "ollama", "gemini", "openai", "groq", "mock"
DEFAULT_MODEL = os.getenv("LLM_MODEL", "default")      # "default" = modèle par défaut du fournisseur
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
LLM_TEMPERATURE = 0.0         # Déterminisme maximal pour des mesures reproductibles
LLM_SEED = 42
