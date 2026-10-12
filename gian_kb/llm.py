"""LLM provider for answer generation: a local model served by Ollama.

The model returns JSON that follows ANSWER_SCHEMA (Ollama structured outputs), temperature 0.
Default model: qwen2.5:7b-instruct (Q4_K_M); override with LLM_MODEL in .env.
"""
from __future__ import annotations

import requests

from .config import LLM_MODEL, OLLAMA_URL

ANSWER_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {"type": "string", "enum": ["answered", "partial", "insufficient"]},
        "answer": {"type": "string"},
        "citations": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["status", "answer", "citations"],
    "additionalProperties": False,
}


class OllamaLLM:
    def __init__(self, model: str | None = None):
        self.model = model or LLM_MODEL
        self.label = f"{self.model} (local, via Ollama)"

    def generate(self, system: str, user: str) -> str:
        r = requests.post(f"{OLLAMA_URL}/api/chat", json={
            "model": self.model, "stream": False, "format": ANSWER_SCHEMA,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "options": {"temperature": 0, "seed": 7, "num_ctx": 6144, "num_predict": 1200},
            "keep_alive": "30m",
        }, timeout=600)
        r.raise_for_status()
        return r.json()["message"]["content"]


def get_llm(model: str | None = None):
    return OllamaLLM(model)
