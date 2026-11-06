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

# Paramètres RAG
RAG_CHUNK_SIZE = 500          # Caractères par chunk
RAG_CHUNK_OVERLAP = 80        # Chevauchement pour préserver le contexte
RAG_TOP_K = 3                 # Nombre de passages récupérés
RAG_SIMILARITY_THRESHOLD = 0.12 # Seuil minimal de pertinence pour éviter les hallucinations

# Paramètres Agent
AGENT_MAX_STEPS = 5           # Nombre maximal de tours dans la boucle ReAct
MAX_TOKENS_PER_CALL = 1000

# Paramètres LLM
DEFAULT_PROVIDER = os.getenv("LLM_PROVIDER", "mock") # "mock", "gemini", "openai", "groq", "ollama"
DEFAULT_MODEL = os.getenv("LLM_MODEL", "gemini-2.5-flash")
