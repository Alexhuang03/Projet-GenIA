"""
Module de traçabilité des exécutions (traces.jsonl)
Enregistre chaque requête, niveau, étapes, outils, tokens et durée.
"""
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from src.config import TRACES_PATH


class ExecutionTrace:
    def __init__(self, level: int, query: str, model: str = ""):
        self.model = model
        self.timestamp = datetime.now().isoformat()
        self.level = level
        self.query = query
        self.start_time = time.time()
        self.end_time: Optional[float] = None
        self.latency_seconds: float = 0.0
        self.steps: List[Dict[str, Any]] = []
        self.tools_used: List[str] = []
        self.sources: List[str] = []
        self.response: str = ""
        self.prompt_tokens: int = 0
        self.completion_tokens: int = 0
        self.total_tokens: int = 0
        self.status: str = "RUNNING" # "SUCCESS", "ABSTENTION", "WAITING_CONFIRMATION", "ERROR"

    def add_step(self, step_type: str, details: Dict[str, Any]):
        self.steps.append({
            "step_index": len(self.steps) + 1,
            "type": step_type,
            "timestamp": datetime.now().isoformat(),
            **details
        })

    def finalize(self, response: str, status: str = "SUCCESS", prompt_tokens: int = 0, completion_tokens: int = 0):
        self.end_time = time.time()
        self.latency_seconds = round(self.end_time - self.start_time, 3)
        self.response = response
        self.status = status
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.total_tokens = prompt_tokens + completion_tokens
        self._save_to_jsonl()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "level": self.level,
            "model": self.model,
            "query": self.query,
            "response": self.response,
            "status": self.status,
            "latency_seconds": self.latency_seconds,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "tools_used": self.tools_used,
            "sources": self.sources,
            "steps": self.steps
        }

    def _save_to_jsonl(self):
        try:
            with open(TRACES_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(self.to_dict(), ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"[Warning] Erreur lors de l'enregistrement de la trace : {e}")
