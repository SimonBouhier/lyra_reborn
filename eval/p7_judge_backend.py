"""Frontière de transport pour les juges structurés P7."""
from __future__ import annotations

from dataclasses import dataclass, field
import json
from typing import Any, Literal, Protocol

import requests


OllamaMode = Literal["JSON_ONLY_PROMPTED", "WIRE_SCHEMA_PROMPTED"]


@dataclass(frozen=True)
class JudgeBackendRequest:
    model: str
    prompt: str
    full_schema: dict[str, Any]
    wire_schema: dict[str, Any]
    temperature: float = 0.0
    max_tokens: int = 2048
    context_tokens: int = 32768


@dataclass(frozen=True)
class JudgeBackendResponse:
    status_code: int
    text: str
    reasoning: str
    done_reason: str | None
    raw: bytes
    api_meta: dict[str, Any] = field(default_factory=dict)


class StructuredJudgeBackend(Protocol):
    name: str

    def build_payload(self, request: JudgeBackendRequest) -> dict[str, Any]: ...

    def generate(self, request: JudgeBackendRequest, timeout: int) -> JudgeBackendResponse: ...


class OllamaJudgeBackend:
    def __init__(self, base_url: str, mode: OllamaMode):
        self.base_url = base_url.rstrip("/")
        self.mode = mode
        self.name = f"ollama:{mode}"

    def build_payload(self, request: JudgeBackendRequest) -> dict[str, Any]:
        output_format: Any = "json" if self.mode == "JSON_ONLY_PROMPTED" else request.wire_schema
        return {
            "model": request.model,
            "prompt": request.prompt,
            "stream": False,
            "think": False,
            "format": output_format,
            "options": {
                "temperature": request.temperature,
                "num_predict": request.max_tokens,
                "num_ctx": request.context_tokens,
            },
        }

    def generate(self, request: JudgeBackendRequest, timeout: int) -> JudgeBackendResponse:
        payload = canonical_payload_bytes(self, request)
        response = requests.post(
            f"{self.base_url}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            timeout=timeout,
        )
        raw = response.content
        response.raise_for_status()
        body = response.json()
        if not isinstance(body, dict):
            raise ValueError("Ollama response body is not an object")
        text = body.get("response")
        reasoning = body.get("thinking")
        if not isinstance(text, str):
            raise ValueError("Ollama response field is not a string")
        if reasoning is None:
            reasoning = ""
        if not isinstance(reasoning, str):
            raise ValueError("Ollama thinking field is not a string")
        meta = {
            key: body.get(key)
            for key in (
                "total_duration",
                "load_duration",
                "prompt_eval_count",
                "prompt_eval_duration",
                "eval_count",
                "eval_duration",
            )
        }
        return JudgeBackendResponse(
            status_code=response.status_code,
            text=text,
            reasoning=reasoning,
            done_reason=body.get("done_reason"),
            raw=raw,
            api_meta=meta,
        )


class OpenAICompatibleJudgeBackend:
    """Adaptateur futur pour llama-server, LM Studio ou vLLM."""

    name = "openai:OPENAI_FULL_SCHEMA"

    def __init__(self, base_url: str, api_key: str = "local"):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    def build_payload(self, request: JudgeBackendRequest) -> dict[str, Any]:
        return {
            "model": request.model,
            "messages": [{"role": "user", "content": request.prompt}],
            "stream": False,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "lyra_judge_verdict",
                    "strict": True,
                    "schema": request.full_schema,
                },
            },
        }

    def generate(self, request: JudgeBackendRequest, timeout: int) -> JudgeBackendResponse:
        payload = canonical_payload_bytes(self, request)
        response = requests.post(
            f"{self.base_url}/v1/chat/completions",
            data=payload,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=timeout,
        )
        raw = response.content
        response.raise_for_status()
        body = response.json()
        try:
            choice = body["choices"][0]
            message = choice["message"]
            text = message["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ValueError("OpenAI-compatible response shape is invalid") from exc
        if not isinstance(text, str):
            raise ValueError("OpenAI-compatible content is not a string")
        reasoning = message.get("reasoning_content", message.get("reasoning", "")) or ""
        if not isinstance(reasoning, str):
            raise ValueError("OpenAI-compatible reasoning field is not a string")
        usage = body.get("usage") if isinstance(body.get("usage"), dict) else {}
        return JudgeBackendResponse(
            status_code=response.status_code,
            text=text,
            reasoning=reasoning,
            done_reason=choice.get("finish_reason"),
            raw=raw,
            api_meta={"usage": usage},
        )


def canonical_payload_bytes(backend: StructuredJudgeBackend, request: JudgeBackendRequest) -> bytes:
    return json.dumps(
        backend.build_payload(request),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
