"""Embeddings via Ollama — modèle historique de Lyra : mxbai-embed-large.

Client minimal ; `requests` importé paresseusement (comme OllamaClient). L'API
moderne est POST /api/embed {"input": [...]} ; repli sur /api/embeddings
(ancienne, un texte à la fois) si indisponible.
"""
from __future__ import annotations
from typing import Dict, List, Optional
import math
import os


def cosine(a: List[float], b: List[float]) -> float:
    num = sum(x * y for x, y in zip(a, b))
    da = math.sqrt(sum(x * x for x in a)) + 1e-9
    db = math.sqrt(sum(y * y for y in b)) + 1e-9
    return num / (da * db)


class OllamaEmbedder:
    def __init__(self, model: Optional[str] = None, base_url: Optional[str] = None,
                 timeout: int = 120):
        self.model = model or os.getenv("LYRA_EMBED_MODEL", "mxbai-embed-large:latest")
        self.base_url = (base_url or os.getenv("OLLAMA_NATIVE_BASE",
                                               "http://127.0.0.1:11434")).rstrip("/")
        self.timeout = timeout
        self._cache: Dict[str, List[float]] = {}

    def embed(self, texts: List[str]) -> List[List[float]]:
        import requests
        missing = [t for t in texts if t not in self._cache]
        if missing:
            r = requests.post(f"{self.base_url}/api/embed",
                              json={"model": self.model, "input": missing},
                              timeout=self.timeout)
            if r.status_code == 404:   # ancienne API : un texte à la fois
                for t in missing:
                    r1 = requests.post(f"{self.base_url}/api/embeddings",
                                       json={"model": self.model, "prompt": t},
                                       timeout=self.timeout)
                    r1.raise_for_status()
                    self._cache[t] = r1.json()["embedding"]
            else:
                r.raise_for_status()
                for t, v in zip(missing, r.json()["embeddings"]):
                    self._cache[t] = v
        return [self._cache[t] for t in texts]

    def similarity(self, a: str, b: str) -> float:
        va, vb = self.embed([a, b])
        return cosine(va, vb)
