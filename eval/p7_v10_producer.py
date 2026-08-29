"""Frontière Ollama des modèles locaux V10 : producteurs et résidence GPU.

Le client producteur enveloppe `core.llm.build_ollama_payload` — le correctif
P0 « options imbriquées », source unique du payload — sans le modifier, et
expose exactement l'interface attendue par `core.loop.LyraLoop` :
`generate(prompt, options, response_format=None) -> str`.

Chaque appel est journalisé avec son `eval_count` (tokens de sortie réellement
produits par Ollama) et sa latence : ce sont les grandeurs des départages V8
(« moins de tokens de sortie ») et de la porte C7 (médiane de tokens T2+T3,
p95 de latence). Aucun comptage de tokens n'est estimé côté client.

`think` n'est jamais envoyé : les trois producteurs gelés depuis V6 ne sont pas
des modèles à canal de réflexion et le harnais V6/V7/V8 ne l'a jamais placé
dans leur payload (`core.llm.OllamaClient` l'omet quand il vaut `None`).

Aucune relance, aucune réparation, aucune continuation (prérég §Anti-
confirmation) : un appel qui échoue est enregistré comme erreur et rend une
chaîne vide. La chaîne vide fait échouer le contrat producteur au tour 3 et
donne à la trajectoire un échec objectif — elle n'invente jamais de sortie.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import time
from typing import Any

import requests

from core.llm import build_ollama_payload

__all__ = [
    "PRODUCERS",
    "ProducerSpec",
    "ProducerCall",
    "OllamaProducerClient",
    "models_runtime",
    "load_model",
    "unload_model",
    "verify_identity",
    "verify_fully_loaded_on_gpu",
]


@dataclass(frozen=True)
class ProducerSpec:
    model: str
    digest: str
    family: str
    quantization: str = "Q4_K_M"


# Producteurs gelés — PREREGISTRATION_v8.md §« Modèles et runtime »
# (lignes 258-265), incorporés mot pour mot par V10 §Incorporation.
PRODUCERS = (
    ProducerSpec(
        model="mistral:latest",
        digest="6577803aa9a036369e481d648a2baebb381ebc6e897f2bb9a766a2aa7bfbc1cf",
        family="mistral",
    ),
    ProducerSpec(
        model="gemma3:latest",
        digest="a2af6cc3eb7fa8be8504abaf9b04e88f17a119ec3f04a3addf55f92841195f5a",
        family="gemma3",
    ),
    ProducerSpec(
        model="granite3.3:latest",
        digest="fd429f23b90980ed1bef53b990894e7b0199331f6ae90c5650240a7d5b70f1f7",
        family="granite",
    ),
)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


@dataclass(frozen=True)
class ProducerCall:
    """Preuve d'un appel producteur — jamais son texte, seulement ses mesures."""

    index: int
    model: str
    prompt_sha256: str
    prompt_chars: int
    options: dict[str, Any] = field(default_factory=dict)
    structured: bool = False
    status_code: int | None = None
    eval_count: int | None = None
    prompt_eval_count: int | None = None
    done_reason: str | None = None
    elapsed_ms: float = 0.0
    output_chars: int = 0
    request_sha256: str = ""
    response_sha256: str | None = None
    error: str | None = None

    @property
    def failed(self) -> bool:
        return self.error is not None

    @property
    def output_tokens(self) -> int:
        """`eval_count` absent = 0 tokens comptabilisés, jamais une estimation."""
        return int(self.eval_count) if isinstance(self.eval_count, int) else 0

    def as_record(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "model": self.model,
            "prompt_sha256": self.prompt_sha256,
            "prompt_chars": self.prompt_chars,
            "options": dict(self.options),
            "structured": self.structured,
            "status_code": self.status_code,
            "eval_count": self.eval_count,
            "prompt_eval_count": self.prompt_eval_count,
            "done_reason": self.done_reason,
            "elapsed_ms": self.elapsed_ms,
            "output_chars": self.output_chars,
            "request_sha256": self.request_sha256,
            "response_sha256": self.response_sha256,
            "error": self.error,
        }


class OllamaProducerClient:
    """Client producteur d'un seul modèle, journalisant chacun de ses appels."""

    def __init__(self, base_url: str, model: str, timeout: int):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.calls: list[ProducerCall] = []

    def generate(
        self,
        prompt: str,
        options: dict[str, Any] | None = None,
        response_format: Any = None,
    ) -> str:
        payload = build_ollama_payload(
            self.model,
            prompt,
            options or {},
            response_format=response_format,
        )
        request_raw = _canonical(payload)
        started = time.perf_counter()
        status_code = None
        response_sha = None
        eval_count = None
        prompt_eval_count = None
        done_reason = None
        error = None
        text = ""
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                data=request_raw,
                headers={"Content-Type": "application/json"},
                timeout=self.timeout,
            )
            status_code = response.status_code
            response_sha = _sha(response.content)
            response.raise_for_status()
            body = response.json()
            if not isinstance(body, dict):
                raise ValueError("Ollama response body is not an object")
            value = body.get("response")
            if not isinstance(value, str):
                raise ValueError("Ollama response field is not a string")
            text = value
            eval_count = body.get("eval_count")
            prompt_eval_count = body.get("prompt_eval_count")
            done_reason = body.get("done_reason")
        except (requests.RequestException, ValueError, json.JSONDecodeError) as exc:
            error = f"{type(exc).__name__}: {exc}"
            text = ""
        self.calls.append(
            ProducerCall(
                index=len(self.calls) + 1,
                model=self.model,
                prompt_sha256=_sha(prompt.encode("utf-8")),
                prompt_chars=len(prompt),
                options=dict(options or {}),
                structured=response_format is not None,
                status_code=status_code,
                eval_count=eval_count,
                prompt_eval_count=prompt_eval_count,
                done_reason=done_reason,
                elapsed_ms=round((time.perf_counter() - started) * 1000, 3),
                output_chars=len(text),
                request_sha256=_sha(request_raw),
                response_sha256=response_sha,
                error=error,
            )
        )
        return text


def _api_get(base_url: str, path: str, timeout: int) -> dict[str, Any]:
    response = requests.get(f"{base_url}{path}", timeout=timeout)
    response.raise_for_status()
    body = response.json()
    if not isinstance(body, dict):
        raise ValueError(f"Ollama {path} response is not an object")
    return body


def models_runtime(base_url: str, timeout: int, names: tuple[str, ...]) -> dict[str, Any]:
    """Version d'Ollama, digests catalogués et modèles résidents, pour `names`."""
    version = _api_get(base_url, "/api/version", timeout).get("version")
    tags = _api_get(base_url, "/api/tags", timeout).get("models", [])
    catalog = {
        item.get("name"): item.get("digest")
        for item in tags
        if isinstance(item, dict) and isinstance(item.get("name"), str)
    }
    loaded_items = _api_get(base_url, "/api/ps", timeout).get("models", [])
    loaded = {
        item.get("name"): {
            "digest": item.get("digest"),
            "size": item.get("size"),
            "size_vram": item.get("size_vram"),
            "context_length": item.get("context_length"),
        }
        for item in loaded_items
        if isinstance(item, dict) and isinstance(item.get("name"), str)
    }
    return {
        "ollama": version,
        "models": {name: catalog.get(name) for name in names},
        "loaded_models": {name: loaded.get(name) for name in names},
    }


def _residency_request(base_url: str, model: str, timeout: int, keep_alive: Any) -> None:
    """Charge ou décharge un modèle sans produire un seul token.

    Prompt vide : Ollama monte (ou libère) le modèle et ne génère rien —
    `eval_count` vaut 0. Ces requêtes sont journalisées à part et n'entrent
    dans aucun plafond d'appels de la prérég.
    """
    payload = {
        "model": model,
        "prompt": "",
        "stream": False,
        "keep_alive": keep_alive,
    }
    response = requests.post(
        f"{base_url}/api/generate",
        data=_canonical(payload),
        headers={"Content-Type": "application/json"},
        timeout=timeout,
    )
    response.raise_for_status()


def load_model(base_url: str, model: str, timeout: int, keep_alive: str = "30m") -> None:
    _residency_request(base_url, model, timeout, keep_alive)


def unload_model(base_url: str, model: str, timeout: int) -> None:
    _residency_request(base_url, model, timeout, 0)


def verify_identity(runtime: dict[str, Any], spec: ProducerSpec) -> None:
    observed = runtime.get("models", {}).get(spec.model)
    if observed != spec.digest:
        raise RuntimeError(
            f"model digest mismatch for {spec.model}: expected {spec.digest}, "
            f"observed {observed}"
        )


def verify_fully_loaded_on_gpu(runtime: dict[str, Any], spec: ProducerSpec) -> None:
    """Même précondition que le banc A, appliquée aux producteurs.

    Reproduit `eval.p7_v10_q1.verify_judge_fully_loaded_on_gpu` — digest exact
    et `size_vram == size > 0` — avec la formulation de la phase courante.
    """
    observed = runtime.get("loaded_models", {}).get(spec.model)
    if not isinstance(observed, dict):
        raise RuntimeError(f"{spec.model} must be resident before its phase lock")
    if observed.get("digest") != spec.digest:
        raise RuntimeError(f"loaded digest differs from the frozen artifact for {spec.model}")
    size = observed.get("size")
    size_vram = observed.get("size_vram")
    if not isinstance(size, int) or size <= 0 or size_vram != size:
        raise RuntimeError(
            f"{spec.model} is not fully loaded on GPU: size={size}, size_vram={size_vram}"
        )
