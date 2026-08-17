#!/usr/bin/env python
"""Run the diagnostic-only Qwen 3.8 admission bench for P7."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import time
from typing import Any

import requests

from eval.p7_evidence import EvidencePack, canonical_json_bytes, pack_sha256
from eval.p7_judge_backend import JudgeBackendRequest, OllamaJudgeBackend, canonical_payload_bytes
from eval.p7_judge_prompt import judge_prompt_with_contract
from eval.p7_qwen38_admission import (
    CANDIDATE_DIGEST,
    CANDIDATE_FAMILY,
    CANDIDATE_MODEL,
    CANDIDATE_QUANTIZATION,
    EXPECTED_CALLS,
    admission_cells,
    admission_jobs,
    summarize_records,
    verify_candidate_identity,
)
from eval.p7_v7_judge import JudgeContractError, judgment_schema, validate_judgment
from eval.p7_v9_judge import wire_judgment_schema


PROTOCOL_COMMIT = "TO_BE_STAMPED"


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _append_jsonl(path: Path, value: dict[str, Any]) -> None:
    with path.open("ab") as handle:
        handle.write(_canonical(value) + b"\n")
        handle.flush()
        os.fsync(handle.fileno())


def _api_get(base_url: str, path: str, timeout: int) -> dict[str, Any]:
    response = requests.get(f"{base_url}{path}", timeout=timeout)
    response.raise_for_status()
    body = response.json()
    if not isinstance(body, dict):
        raise ValueError(f"Ollama {path} response is not an object")
    return body


def runtime_manifest(base_url: str, timeout: int) -> dict[str, Any]:
    version = _api_get(base_url, "/api/version", timeout).get("version")
    tags = _api_get(base_url, "/api/tags", timeout).get("models", [])
    if not isinstance(tags, list):
        raise ValueError("Ollama /api/tags models field is not a list")
    models = {
        item.get("name"): item.get("digest")
        for item in tags
        if isinstance(item, dict) and isinstance(item.get("name"), str)
    }
    return {"ollama": version, "models": {CANDIDATE_MODEL: models.get(CANDIDATE_MODEL)}}


def _acquire_lock(output_root: Path, run_id: str) -> Path:
    output_root.mkdir(parents=True, exist_ok=True)
    path = output_root / f"p7_qwen38_admission_{PROTOCOL_COMMIT}.lock"
    payload = {
        "schema_version": "lyra.p7.qwen38-admission-lock.v1",
        "protocol_commit": PROTOCOL_COMMIT,
        "run_id": run_id,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    with path.open("xb") as handle:
        handle.write(_canonical(payload))
        handle.flush()
        os.fsync(handle.fileno())
    return path


def run(base_url: str, timeout: int, output_root: Path) -> int:
    if PROTOCOL_COMMIT == "TO_BE_STAMPED":
        raise RuntimeError("admission protocol must be committed and stamped before a live run")
    cells = admission_cells()
    jobs = admission_jobs()
    if len(cells) != 8 or len(jobs) != EXPECTED_CALLS:
        raise RuntimeError("admission matrix differs from the frozen 8 x 3 design")
    for cell in cells:
        raw = canonical_json_bytes(cell.pack)
        if raw != canonical_json_bytes(EvidencePack.model_validate_json(raw)):
            raise RuntimeError(f"non-deterministic pack: {cell.cell_id}:{cell.orientation}")
        raw.decode("ascii")  # frozen admission material is English and ASCII-only

    runtime_before = runtime_manifest(base_url, timeout)
    verify_candidate_identity(runtime_before)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    run_dir = output_root / f"p7_qwen38_admission_{stamp}"
    _acquire_lock(output_root, run_dir.name)
    (run_dir / "calls").mkdir(parents=True, exist_ok=False)
    journal = run_dir / "journal.jsonl"
    manifest = {
        "schema_version": "lyra.p7.qwen38-admission-run.v1",
        "run_id": run_dir.name,
        "protocol": "docs/P7_QWEN38_ADMISSION.md",
        "protocol_commit": PROTOCOL_COMMIT,
        "diagnostic_only": True,
        "synthetic_only": True,
        "language": "en",
        "candidate": {
            "model": CANDIDATE_MODEL,
            "digest": CANDIDATE_DIGEST,
            "family": CANDIDATE_FAMILY,
            "quantization": CANDIDATE_QUANTIZATION,
        },
        "mode": "JSON_ONLY_PROMPTED",
        "calls_planned": EXPECTED_CALLS,
        "runtime_before": runtime_before,
        "cells": [
            {
                "cell_id": cell.cell_id,
                "orientation": cell.orientation,
                "expected_preference": cell.expected_preference,
                "pack_sha256": pack_sha256(cell.pack),
                "pack_bytes": len(canonical_json_bytes(cell.pack)),
                "full_schema_sha256": _sha(_canonical(judgment_schema(cell.pack))),
            }
            for cell in cells
        ],
    }
    (run_dir / "manifest.json").write_bytes(_canonical(manifest))

    backend = OllamaJudgeBackend(base_url, "JSON_ONLY_PROMPTED")
    records: list[dict[str, Any]] = []
    for number, job in enumerate(jobs, start=1):
        cell = job.cell
        request = JudgeBackendRequest(
            model=CANDIDATE_MODEL,
            prompt=judge_prompt_with_contract(cell.pack),
            full_schema=judgment_schema(cell.pack),
            wire_schema=wire_judgment_schema(cell.pack),
        )
        call_id = f"admission-{number:03d}"
        request_raw = canonical_payload_bytes(backend, request)
        (run_dir / "calls" / f"{call_id}.request.json").write_bytes(request_raw)
        _append_jsonl(
            journal,
            {
                "event": "call_started",
                "call_id": call_id,
                "run_id": run_dir.name,
                "cell_id": cell.cell_id,
                "orientation": cell.orientation,
                "repetition": job.repetition,
                "pack_sha256": pack_sha256(cell.pack),
                "prompt_sha256": _sha(request.prompt.encode("utf-8")),
                "request_sha256": _sha(request_raw),
            },
        )
        started = time.perf_counter()
        status_code = None
        response_sha = None
        text = ""
        reasoning = ""
        done_reason = None
        api_meta: dict[str, Any] = {}
        error = None
        verdict = None
        try:
            response = backend.generate(request, timeout)
            status_code = response.status_code
            response_sha = _sha(response.raw)
            (run_dir / "calls" / f"{call_id}.response.json").write_bytes(response.raw)
            text = response.text
            reasoning = response.reasoning
            done_reason = response.done_reason
            api_meta = response.api_meta
            if reasoning:
                raise JudgeContractError("thinking channel must be empty")
            verdict = validate_judgment(text, cell.pack)
        except (requests.RequestException, ValueError, json.JSONDecodeError) as exc:
            error = f"{type(exc).__name__}: {exc}"
        observed = verdict.preference.value if verdict is not None else "INVALID"
        valid = verdict is not None
        wire_clean = (
            status_code == 200
            and bool(text.strip())
            and not reasoning
            and done_reason == "stop"
        )
        record = {
            "event": "call_finished",
            "call_id": call_id,
            "run_id": run_dir.name,
            "cell_id": cell.cell_id,
            "orientation": cell.orientation,
            "repetition": job.repetition,
            "pack_sha256": pack_sha256(cell.pack),
            "request_sha256": _sha(request_raw),
            "response_sha256": response_sha,
            "status_code": status_code,
            "response_chars": len(text),
            "reasoning_chars": len(reasoning),
            "done_reason": done_reason,
            "elapsed_ms": round((time.perf_counter() - started) * 1000, 3),
            "api_meta": api_meta,
            "wire_clean": wire_clean,
            "valid": valid,
            "expected_preference": cell.expected_preference,
            "observed_preference": observed,
            "correct": valid and observed == cell.expected_preference,
            "error": error,
        }
        _append_jsonl(journal, record)
        records.append(record)
        print(
            json.dumps(
                {
                    "call": number,
                    "of": EXPECTED_CALLS,
                    "cell": cell.cell_id,
                    "orientation": cell.orientation,
                    "repetition": job.repetition,
                    "valid": valid,
                    "observed": observed,
                    "expected": cell.expected_preference,
                },
                ensure_ascii=False,
            ),
            flush=True,
        )

    runtime_after = runtime_manifest(base_url, timeout)
    verify_candidate_identity(runtime_after)
    summary = {
        "schema_version": "lyra.p7.qwen38-admission-summary.v1",
        "run_id": run_dir.name,
        "protocol_commit": PROTOCOL_COMMIT,
        "candidate_model": CANDIDATE_MODEL,
        "candidate_digest": CANDIDATE_DIGEST,
        **summarize_records(records),
        "runtime_after": runtime_after,
        "journal_sha256": _sha(journal.read_bytes()),
    }
    (run_dir / "summary.json").write_bytes(_canonical(summary))
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)
    return 0 if summary["qualified_for_v10_design"] else 2


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:11434")
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--output-root", type=Path, default=Path("data/runs"))
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    return run(args.base_url.rstrip("/"), args.timeout, args.output_root)


if __name__ == "__main__":
    raise SystemExit(main())
