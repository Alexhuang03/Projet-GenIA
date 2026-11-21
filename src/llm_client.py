"""
Client LLM unifié multi-fournisseurs :
- Ollama local (par défaut, modèle qwen2.5:7b) : gratuit, reproductible, latence réelle
- Google Gemini (API REST)
- Groq / OpenAI (format compatible OpenAI)
- Mock hors-ligne : UNIQUEMENT pour tester la plomberie de l'interface. Ses réponses sont
  écrites à la main et ne doivent jamais servir à produire une mesure (eval.py le refuse).

Choix important : une erreur d'appel lève une exception au lieu de basculer silencieusement
sur le mock, pour qu'une panne réseau ne puisse pas fausser une évaluation.
"""
import json
import os
import re
from typing import Any, Dict, List, Optional

import httpx

from src.config import (
    DEFAULT_PROVIDER, DEFAULT_MODEL, OLLAMA_URL, EMBEDDING_MODEL, LLM_TEMPERATURE, LLM_SEED,
)


class LLMError(RuntimeError):
    pass


class LLMResponse:
    def __init__(self, content: str, prompt_tokens: int = 0, completion_tokens: int = 0,
                 tool_calls: Optional[List[Dict[str, Any]]] = None):
        self.content = content
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.total_tokens = prompt_tokens + completion_tokens
        self.tool_calls = tool_calls or []


def _parse_text_tool_call(content: str) -> Optional[Dict[str, Any]]:
    """Récupère un appel d'outil écrit en JSON dans le texte de la réponse, s'il y en a un."""
    m = re.search(r'\{\s*"name"\s*:\s*"\w+"\s*,\s*"arguments"\s*:', content)
    if not m:
        return None
    try:
        obj, _ = json.JSONDecoder().raw_decode(content[m.start():])
    except ValueError:
        return None
    return {"name": obj["name"], "arguments": obj.get("arguments") or {}}


class UnifiedLLMClient:
    def __init__(self, provider: Optional[str] = None, model: Optional[str] = None):
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.groq_key = os.getenv("GROQ_API_KEY")
        self.provider = provider or DEFAULT_PROVIDER
        self.model = model or self._default_model()

    def _default_model(self) -> str:
        if DEFAULT_MODEL and DEFAULT_MODEL != "default":
            return DEFAULT_MODEL
        return {
            "ollama": "qwen2.5:7b",
            "gemini": "gemini-2.5-flash",
            "groq": "llama-3.3-70b-versatile",
            "openai": "gpt-4o-mini",
        }.get(self.provider, "mock")

    @property
    def is_mock(self) -> bool:
        return self.provider == "mock"

    # ------------------------------------------------------------------ génération
    def generate(self, prompt: str, system_prompt: Optional[str] = None,
                 temperature: float = LLM_TEMPERATURE) -> LLMResponse:
        if self.provider == "ollama":
            return self._call_ollama(prompt, system_prompt, temperature)
        if self.provider == "gemini":
            return self._call_gemini_api(prompt, system_prompt, temperature)
        if self.provider in ("openai", "groq"):
            return self._call_openai_compatible_api(prompt, system_prompt, temperature)
        if self.provider == "mock":
            return self._call_mock_llm(prompt, system_prompt)
        raise LLMError(f"Fournisseur inconnu : {self.provider}")

    def _call_ollama(self, prompt: str, system_prompt: Optional[str], temperature: float) -> LLMResponse:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature, "seed": LLM_SEED, "num_ctx": 8192},
        }
        try:
            with httpx.Client(timeout=300.0) as client:
                res = client.post(f"{OLLAMA_URL}/api/chat", json=payload)
                res.raise_for_status()
                data = res.json()
        except Exception as e:
            raise LLMError(f"Appel Ollama échoué ({self.model}) : {e}") from e
        return LLMResponse(
            content=data["message"]["content"],
            prompt_tokens=data.get("prompt_eval_count", 0),
            completion_tokens=data.get("eval_count", 0),
        )

    def _call_gemini_api(self, prompt: str, system_prompt: Optional[str], temperature: float) -> LLMResponse:
        if not self.gemini_key:
            raise LLMError("GEMINI_API_KEY manquante")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        payload: Dict[str, Any] = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": temperature},
        }
        if system_prompt:
            payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}
        try:
            with httpx.Client(timeout=60.0) as client:
                res = client.post(url, json=payload, headers={"x-goog-api-key": self.gemini_key})
                res.raise_for_status()
                data = res.json()
        except Exception as e:
            raise LLMError(f"Appel Gemini échoué : {e}") from e
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        usage = data.get("usageMetadata", {})
        return LLMResponse(text, usage.get("promptTokenCount", 0), usage.get("candidatesTokenCount", 0))

    def _call_openai_compatible_api(self, prompt: str, system_prompt: Optional[str], temperature: float) -> LLMResponse:
        if self.provider == "groq":
            url, key = "https://api.groq.com/openai/v1/chat/completions", self.groq_key
        else:
            url, key = "https://api.openai.com/v1/chat/completions", self.openai_key
        if not key:
            raise LLMError(f"Clé API {self.provider.upper()} manquante")
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        try:
            with httpx.Client(timeout=60.0) as client:
                res = client.post(url, json={"model": self.model, "messages": messages, "temperature": temperature},
                                  headers={"Authorization": f"Bearer {key}"})
                res.raise_for_status()
                data = res.json()
        except Exception as e:
            raise LLMError(f"Appel {self.provider} échoué : {e}") from e
        usage = data.get("usage", {})
        return LLMResponse(data["choices"][0]["message"]["content"],
                           usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0))

    # ------------------------------------------------------------------ appel d'outils
    def chat(self, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None,
             temperature: float = LLM_TEMPERATURE, seed: int = LLM_SEED, json_mode: bool = False) -> LLMResponse:
        """Conversation multi-tours avec appel d'outils natif (Ollama). Utilisé par les niveaux 2 et 3.
        Les tool_calls sont renvoyés au format {"name": str, "arguments": dict}."""
        if self.provider != "ollama":
            raise LLMError("Les niveaux 2 et 3 sont implémentés pour Ollama (appel d'outils natif).")
        payload: Dict[str, Any] = {
            "model": self.model, "messages": messages, "stream": False,
            "options": {"temperature": temperature, "seed": seed, "num_ctx": 8192},
        }
        if tools:
            payload["tools"] = tools
        if json_mode:
            payload["format"] = "json"
        try:
            with httpx.Client(timeout=300.0) as client:
                res = client.post(f"{OLLAMA_URL}/api/chat", json=payload)
                res.raise_for_status()
                data = res.json()
        except Exception as e:
            raise LLMError(f"Appel Ollama échoué ({self.model}) : {e}") from e
        msg = data["message"]
        calls = [{"name": c["function"]["name"], "arguments": c["function"].get("arguments") or {}}
                 for c in msg.get("tool_calls") or []]
        content = msg.get("content", "")
        if tools and not calls:
            recovered = _parse_text_tool_call(content)
            if recovered:  # le modèle a écrit son appel d'outil dans le texte au lieu du champ prévu
                calls, content = [recovered], ""
        return LLMResponse(content, data.get("prompt_eval_count", 0), data.get("eval_count", 0), tool_calls=calls)

    # ------------------------------------------------------------------ embeddings
    def embed(self, texts: List[str], model: str = EMBEDDING_MODEL) -> List[List[float]]:
        """Embeddings via Ollama (utilisés par le retriever dense du Niveau 1)."""
        try:
            with httpx.Client(timeout=300.0) as client:
                res = client.post(f"{OLLAMA_URL}/api/embed", json={"model": model, "input": texts})
                res.raise_for_status()
                return res.json()["embeddings"]
        except Exception as e:
            raise LLMError(f"Calcul d'embeddings échoué ({model}) : {e}") from e

    # ------------------------------------------------------------------ mock
    def _call_mock_llm(self, prompt: str, system_prompt: Optional[str]) -> LLMResponse:
        """Réponse factice générique : sert seulement à faire tourner l'interface sans modèle."""
        if "Extraits documentaires" in prompt:
            ans = ("[MODE MOCK] Réponse factice : aucun modèle n'a été appelé. "
                   "Configurez LLM_PROVIDER=ollama pour obtenir une vraie réponse.")
        else:
            ans = "[MODE MOCK] Réponse factice : aucun modèle n'a été appelé."
        return LLMResponse(ans, len(prompt) // 4, len(ans) // 4)
