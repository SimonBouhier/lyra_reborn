"""Choix du moteur pour la porte : Ollama s'il est là, sinon essai silencieux."""
from __future__ import annotations
import json
import os
import urllib.error
import urllib.request
from typing import Any, List, Optional, Tuple

PREFERRED = (
    "gemma3:latest",
    "gemma3",
    "mistral:latest",
    "llama3.1:8b",
    "granite3.3:latest",
    "gpt-oss:20b",
    "qwen3.8:27b",
)


def _live_flag() -> Optional[bool]:
    raw = os.getenv("LYRA_LIVE", "").strip().lower()
    if raw in {"0", "false", "no", "off"}:
        return False
    if raw in {"1", "true", "yes", "on"}:
        return True
    return None


def list_ollama_models(base: str = "http://127.0.0.1:11434", timeout: float = 1.5) -> List[str]:
    try:
        with urllib.request.urlopen(f"{base.rstrip('/')}/api/tags", timeout=timeout) as r:
            data = json.loads(r.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
        return []
    names = []
    for m in data.get("models") or []:
        name = m.get("name") or ""
        if name and "embed" not in name.lower():
            names.append(name)
    return names


def pick_model(available: List[str]) -> Optional[str]:
    forced = os.getenv("LYRA_MODEL", "").strip()
    if forced:
        return forced
    for name in PREFERRED:
        if name in available:
            return name
    return available[0] if available else None


def make_llm(*, live: bool = False) -> Tuple[Any, str]:
    """Retourne (client, étiquette).

    Par défaut : premières couches (EchoClient). Une voix réelle n'est
    branchée que si `live=True` ou `LYRA_LIVE=1` — jamais par simple
    présence d'Ollama (effet ≠ consigne).
    """
    from core.llm import EchoClient, OllamaClient

    flag = _live_flag()
    want_live = live or (flag is True)
    if flag is False:
        want_live = False
    if not want_live:
        return EchoClient(), "premières couches"

    models = list_ollama_models()
    if not models:
        raise RuntimeError("Une voix est demandée mais Ollama ne répond pas.")
    model = pick_model(models)
    if not model:
        raise RuntimeError("Une voix est demandée mais aucun modèle n'est installé.")
    return OllamaClient(model=model), model
