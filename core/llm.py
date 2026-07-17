"""Clients LLM pour Lyra.

⭐ Correctif P0 (« patch options{} ») : les paramètres de génération d'Ollama
DOIVENT être imbriqués sous la clé "options" du payload. Le canon `conscious`
(lot 1, conscious/adapters/ollama.py) les plaçait à la racine → Ollama les
IGNORAIT silencieusement, donc la modulation n'avait aucun effet. Le correctif
vient de session_2/bundle_lyra/gemma_bridge_v2.py. On l'inscrit ici, une fois.

Deux clients partageant l'interface `generate(prompt, options) -> str` :
  - OllamaClient : appelle un serveur Ollama réel.
  - EchoClient   : hors-ligne, DÉTERMINISTE. N'invente aucun « résultat » : il
    renvoie une trace des options reçues. Sert à PROUVER que la modulation
    change bien ce qui atteint le modèle (test de la charte §3), sans dépendre
    d'un Ollama vivant. À ne jamais confondre avec une vraie génération.
"""
from __future__ import annotations
from typing import Dict, Any, Optional
import os


def build_ollama_payload(model: str, prompt: str, options: Dict[str, Any],
                         stream: bool = False) -> Dict[str, Any]:
    """Construit le payload /api/generate d'Ollama avec les options AU BON ENDROIT.

    C'est l'unité testable du correctif P0 : `options` est imbriqué, jamais
    étalé à la racine.
    """
    return {
        "model": model,
        "prompt": prompt,
        "stream": bool(stream),
        "options": dict(options) if options else {},
    }


class OllamaClient:
    """Client Ollama natif (/api/generate). `requests` importé paresseusement."""

    def __init__(self, model: Optional[str] = None, base_url: Optional[str] = None,
                 timeout: int = 120):
        self.model = model or os.getenv("LYRA_MODEL", "gpt-oss:20b")
        self.base_url = (base_url or os.getenv("OLLAMA_NATIVE_BASE",
                                               "http://127.0.0.1:11434")).rstrip("/")
        self.timeout = timeout

    def generate(self, prompt: str, options: Optional[Dict[str, Any]] = None) -> str:
        import requests  # paresseux : les tests hors-ligne n'en ont pas besoin
        payload = build_ollama_payload(self.model, prompt, options or {})
        r = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=self.timeout)
        r.raise_for_status()
        data = r.json()
        return data.get("response", "") or ""


class EchoClient:
    """Client hors-ligne déterministe : renvoie une trace des options reçues.

    Utilité : prouver la chaîne de modulation de bout en bout dans les tests et
    la démo, sans Ollama. Ce n'est PAS un générateur de texte crédible.
    """

    def __init__(self, model: str = "echo"):
        self.model = model

    def generate(self, prompt: str, options: Optional[Dict[str, Any]] = None) -> str:
        opts = options or {}
        t = opts.get("temperature")
        p = opts.get("top_p")
        rp = opts.get("repeat_penalty")
        n = opts.get("num_predict")
        head = (prompt or "").strip().replace("\n", " ")[:48]
        return (f"[echo temperature={t} top_p={p} repeat_penalty={rp} "
                f"num_predict={n}] {head}")
