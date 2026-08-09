"""Frontière de quarantaine entre La Vigie et un sidecar EPP.

Ce module ne décide pas si un contenu mérite AUDIT ou AMPLIFICATION. Il applique
la décision de sécurité antérieure : PASS / QUARANTINE / REJECT / ESCALATE.

Le sidecar est un processus séparé et sans shell. Il reçoit un unique document
JSON sur stdin et doit rendre un unique verdict JSON sur stdout. La moindre
anomalie de transport ou de schéma produit une QUARANTINE explicite. Ce pont ne
possède aucune référence vers Nemeton, Memento, une base EPP ou un outil réseau.

Limite honnête : l'environnement épuré retire les secrets et contraint le
contrat, mais ne constitue pas à lui seul une sandbox réseau/OS. Le sidecar EPP
devra être lancé avec une base éphémère et un provider Ollama local explicite.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
from typing import Any, Mapping, Sequence, Tuple


SCHEMA_VERSION = "vigie.quarantine.v1"
ENGINE_ID = "epp_esmm_quarantine"

_VERDICT_KEYS = {
    "schema_version",
    "engine",
    "item_id",
    "content_sha256",
    "decision",
    "confidence",
    "flags",
    "reasons",
    "model_votes",
    "degraded",
    "errors",
}
_VOTE_KEYS = {"model_id", "decision", "confidence"}


class QuarantineDecision(str, Enum):
    PASS = "PASS"
    QUARANTINE = "QUARANTINE"
    REJECT = "REJECT"
    ESCALATE = "ESCALATE"


@dataclass(frozen=True)
class QuarantineItem:
    """Capture immuable soumise à la frontière de sécurité."""

    item_id: str
    source: str
    external_id: str
    canonical_url: str
    captured_at: str
    content: str
    content_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        for name in ("item_id", "source", "external_id", "captured_at"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if not isinstance(self.canonical_url, str):
            raise TypeError("canonical_url must be a string")
        if not isinstance(self.content, str) or not self.content:
            raise ValueError("content must be a non-empty string")
        digest = hashlib.sha256(self.content.encode("utf-8")).hexdigest()
        object.__setattr__(self, "content_sha256", digest)

    def to_wire(self) -> dict[str, str]:
        return {
            "item_id": self.item_id,
            "source": self.source,
            "external_id": self.external_id,
            "canonical_url": self.canonical_url,
            "captured_at": self.captured_at,
            "content": self.content,
            "content_sha256": self.content_sha256,
        }


@dataclass(frozen=True)
class ModelVote:
    model_id: str
    decision: QuarantineDecision
    confidence: float


@dataclass(frozen=True)
class QuarantineVerdict:
    schema_version: str
    engine: str
    item_id: str
    content_sha256: str
    decision: QuarantineDecision
    confidence: float
    flags: Tuple[str, ...]
    reasons: Tuple[str, ...]
    model_votes: Tuple[ModelVote, ...]
    degraded: bool
    errors: Tuple[str, ...]


class _IdentityMismatch(ValueError):
    pass


def _probability(value: Any, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field_name} must be a number")
    number = float(value)
    if not math.isfinite(number) or not 0.0 <= number <= 1.0:
        raise ValueError(f"{field_name} must be finite and in [0, 1]")
    return number


def _string_tuple(value: Any, field_name: str, limit: int) -> Tuple[str, ...]:
    if not isinstance(value, list) or len(value) > limit:
        raise ValueError(f"{field_name} must be a bounded list")
    if any(not isinstance(item, str) or not item for item in value):
        raise ValueError(f"{field_name} entries must be non-empty strings")
    return tuple(value)


def _parse_verdict(payload: Any, expected: QuarantineItem) -> QuarantineVerdict:
    if not isinstance(payload, dict) or set(payload) != _VERDICT_KEYS:
        raise ValueError("verdict keys do not match the closed schema")
    if payload["schema_version"] != SCHEMA_VERSION:
        raise ValueError("unsupported schema_version")
    if payload["engine"] != ENGINE_ID:
        raise ValueError("unexpected engine")
    if payload["item_id"] != expected.item_id:
        raise _IdentityMismatch("item_id mismatch")
    if payload["content_sha256"] != expected.content_sha256:
        raise _IdentityMismatch("content_sha256 mismatch")
    if not isinstance(payload["degraded"], bool):
        raise ValueError("degraded must be a boolean")

    try:
        decision = QuarantineDecision(payload["decision"])
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid decision") from exc

    votes_raw = payload["model_votes"]
    if not isinstance(votes_raw, list) or len(votes_raw) > 32:
        raise ValueError("model_votes must be a bounded list")
    votes = []
    for raw in votes_raw:
        if not isinstance(raw, dict) or set(raw) != _VOTE_KEYS:
            raise ValueError("model vote keys do not match the closed schema")
        if not isinstance(raw["model_id"], str) or not raw["model_id"]:
            raise ValueError("model_id must be a non-empty string")
        try:
            vote_decision = QuarantineDecision(raw["decision"])
        except (TypeError, ValueError) as exc:
            raise ValueError("invalid model vote decision") from exc
        votes.append(
            ModelVote(
                model_id=raw["model_id"],
                decision=vote_decision,
                confidence=_probability(raw["confidence"], "vote confidence"),
            )
        )

    errors = _string_tuple(payload["errors"], "errors", 32)
    degraded = payload["degraded"]
    if not degraded and errors:
        raise ValueError("non-degraded verdict cannot contain errors")
    if not degraded and not votes:
        raise ValueError("non-degraded verdict requires model votes")

    return QuarantineVerdict(
        schema_version=SCHEMA_VERSION,
        engine=ENGINE_ID,
        item_id=expected.item_id,
        content_sha256=expected.content_sha256,
        decision=decision,
        confidence=_probability(payload["confidence"], "confidence"),
        flags=_string_tuple(payload["flags"], "flags", 64),
        reasons=_string_tuple(payload["reasons"], "reasons", 32),
        model_votes=tuple(votes),
        degraded=degraded,
        errors=errors,
    )


class EPPQuarantineBridge:
    """Exécute un sidecar EPP strict et transforme tout défaut en quarantaine."""

    def __init__(
        self,
        command: Sequence[str],
        *,
        cwd: str | os.PathLike[str] | None = None,
        timeout_seconds: float = 180.0,
        max_content_chars: int = 100_000,
        max_output_bytes: int = 1_000_000,
    ) -> None:
        if isinstance(command, (str, bytes)) or not isinstance(command, Sequence):
            raise TypeError("command must be an argv sequence, never a shell string")
        if not command or any(not isinstance(arg, str) or not arg for arg in command):
            raise ValueError("command must contain non-empty string arguments")
        executable = Path(command[0])
        if not executable.is_absolute():
            raise ValueError("sidecar executable must use an absolute path")
        if not executable.is_file():
            raise FileNotFoundError(executable)
        if timeout_seconds <= 0 or max_content_chars <= 0 or max_output_bytes <= 0:
            raise ValueError("timeout and size limits must be positive")

        resolved_cwd = None
        if cwd is not None:
            resolved_cwd = Path(cwd).resolve()
            if not resolved_cwd.is_dir():
                raise NotADirectoryError(resolved_cwd)

        self.command = tuple(command)
        self.cwd = resolved_cwd
        self.timeout_seconds = float(timeout_seconds)
        self.max_content_chars = int(max_content_chars)
        self.max_output_bytes = int(max_output_bytes)

    @staticmethod
    def _safe_environment() -> Mapping[str, str]:
        # Les variables nécessaires à Windows survivent ; aucun environnement
        # fournisseur, token ou PYTHONPATH parent ne franchit la frontière.
        env = {
            name: os.environ[name]
            for name in ("SYSTEMROOT", "WINDIR", "TEMP", "TMP", "COMSPEC")
            if name in os.environ
        }
        env.update(
            {
                "PYTHONUTF8": "1",
                "PYTHONIOENCODING": "utf-8",
                "EPP_QUARANTINE_MODE": "1",
                "OLLAMA_HOST": "http://127.0.0.1:11434",
                "NO_PROXY": "127.0.0.1,localhost",
            }
        )
        return env

    @staticmethod
    def _failure(item: QuarantineItem, code: str) -> QuarantineVerdict:
        return QuarantineVerdict(
            schema_version=SCHEMA_VERSION,
            engine=ENGINE_ID,
            item_id=item.item_id,
            content_sha256=item.content_sha256,
            decision=QuarantineDecision.QUARANTINE,
            confidence=0.0,
            flags=("bridge_failure", code),
            reasons=("La frontière EPP a échoué ; quarantaine imposée.",),
            model_votes=(),
            degraded=True,
            errors=(code,),
        )

    def assess(self, item: QuarantineItem) -> QuarantineVerdict:
        if not isinstance(item, QuarantineItem):
            raise TypeError("item must be a QuarantineItem")
        if len(item.content) > self.max_content_chars:
            return self._failure(item, "content_too_large")

        request = {
            "schema_version": SCHEMA_VERSION,
            "isolation": {
                "persistence": "ephemeral",
                "network": "local_model_only",
                "follow_links": False,
                "tools": [],
            },
            "item": item.to_wire(),
        }
        wire = json.dumps(
            request, ensure_ascii=False, separators=(",", ":")
        ).encode("utf-8")

        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        try:
            result = subprocess.run(
                self.command,
                input=wire,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(self.cwd) if self.cwd else None,
                env=dict(self._safe_environment()),
                shell=False,
                check=False,
                timeout=self.timeout_seconds,
                creationflags=creationflags,
            )
        except subprocess.TimeoutExpired:
            return self._failure(item, "sidecar_timeout")
        except OSError:
            return self._failure(item, "sidecar_launch")

        if result.returncode != 0:
            return self._failure(item, "sidecar_exit")
        if len(result.stdout) > self.max_output_bytes or len(result.stderr) > self.max_output_bytes:
            return self._failure(item, "output_too_large")
        if result.stderr.strip():
            return self._failure(item, "unexpected_stderr")

        try:
            decoded = result.stdout.decode("utf-8", errors="strict")
        except UnicodeDecodeError:
            return self._failure(item, "invalid_encoding")
        try:
            payload = json.loads(decoded)
        except json.JSONDecodeError:
            return self._failure(item, "invalid_json")

        try:
            verdict = _parse_verdict(payload, item)
        except _IdentityMismatch:
            return self._failure(item, "identity_mismatch")
        except (TypeError, ValueError, KeyError):
            return self._failure(item, "invalid_schema")

        if verdict.degraded or verdict.errors:
            return self._failure(item, "sidecar_degraded")
        return verdict
