#!/usr/bin/env python
"""Run the diagnostic-only P7 V10 Q-1 judge qualification bench."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import time
from typing import Any

import requests

from eval.p7_evidence import EvidencePack, canonical_json_bytes, pack_sha256
from eval.p7_judge_backend import JudgeBackendRequest, OllamaJudgeBackend, canonical_payload_bytes
from eval.p7_v10_q1 import (
    EXPECTED_CALLS,
    JUDGES,
    REPETITIONS,
    JudgeSpec,
    compact_judge_prompt,
    compact_judgment_schema,
    q1_cells,
    q1_jobs_for_judge,
    summarize_records,
    validate_compact_judgment,
    verify_judge_fully_loaded_on_gpu,
    verify_judge_identities,
)
from eval.p7_v7_judge import JudgeContractError


PROTOCOL_COMMIT = "7540912d57ba1a113e1af7f2d43cec261f0834d8"


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
    loaded_items = _api_get(base_url, "/api/ps", timeout).get("models", [])
    if not isinstance(loaded_items, list):
        raise ValueError("Ollama /api/ps models field is not a list")
    loaded_models = {
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
        "models": {judge.model: models.get(judge.model) for judge in JUDGES},
        "loaded_models": {
            judge.model: loaded_models.get(judge.model) for judge in JUDGES
        },
    }


def _judge_slug(judge: JudgeSpec) -> str:
    return re.sub(r"[^a-z0-9]+", "-", judge.model.lower()).strip("-")


def _acquire_phase_lock(output_root: Path, run_id: str, judge: JudgeSpec) -> Path:
    output_root.mkdir(parents=True, exist_ok=True)
    path = output_root / f"p7_v10_q1_{PROTOCOL_COMMIT}_{_judge_slug(judge)}.lock"
    payload = {
        "schema_version": "lyra.p7.v10-q1-phase-lock.v1",
        "protocol_commit": PROTOCOL_COMMIT,
        "run_id": run_id,
        "judge_model": judge.model,
        "judge_digest": judge.digest,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    with path.open("xb") as handle:
        handle.write(_canonical(payload))
        handle.flush()
        os.fsync(handle.fileno())
    return path


def _warm_model(
    base_url: str,
    timeout: int,
    run_dir: Path,
    judge: JudgeSpec,
) -> dict[str, Any]:
    """Load one frozen model without exposing a qualification fixture."""
    payload = {
        "model": judge.model,
        "prompt": 'Return exactly this JSON object: {"ok":true}',
        "stream": False,
        "think": False,
        "format": "json",
        "keep_alive": "30m",
        "options": {
            "temperature": 0,
            "num_predict": 32,
            "num_ctx": 2048,
        },
    }
    request_raw = _canonical(payload)
    prefix = f"preflight-{_judge_slug(judge)}"
    (run_dir / f"{prefix}.request.json").write_bytes(request_raw)
    response = requests.post(
        f"{base_url}/api/generate",
        data=request_raw,
        headers={"Content-Type": "application/json"},
        timeout=timeout,
    )
    raw = response.content
    (run_dir / f"{prefix}.response.json").write_bytes(raw)
    response.raise_for_status()
    body = response.json()
    if not isinstance(body, dict):
        raise ValueError("Ollama preflight response is not an object")
    return {
        "request_sha256": _sha(request_raw),
        "response_sha256": _sha(raw),
        "status_code": response.status_code,
        "done_reason": body.get("done_reason"),
        "response_chars": len(body.get("response", ""))
        if isinstance(body.get("response"), str)
        else None,
        "thinking_chars": len(body.get("thinking", ""))
        if isinstance(body.get("thinking", ""), str)
        else None,
    }


def _validate_matrix() -> None:
    cells = q1_cells()
    if len(cells) != 6 or EXPECTED_CALLS != 36:
        raise RuntimeError("Q-1 matrix differs from the frozen 2 x 6 x 3 design")
    if any(len(q1_jobs_for_judge(judge)) != len(cells) * REPETITIONS for judge in JUDGES):
        raise RuntimeError("judge job matrix is incomplete")
    for cell in cells:
        raw = canonical_json_bytes(cell.pack)
        if raw != canonical_json_bytes(EvidencePack.model_validate_json(raw)):
            raise RuntimeError(f"non-deterministic pack: {cell.fixture_id}:{cell.orientation}")
        raw.decode("ascii")
        compact_judge_prompt(cell.pack).encode("ascii")


def _write_summary(
    run_dir: Path,
    records: list[dict[str, Any]],
    phase_runtime: dict[str, Any],
    journal: Path,
    *,
    abort_error: str | None = None,
) -> dict[str, Any]:
    result = summarize_records(records)
    if abort_error is not None:
        result["qualified_for_v10_preregistration"] = False
        result["status"] = "Q1_ABORTED"
    summary = {
        "schema_version": "lyra.p7.v10-q1-summary.v1",
        "run_id": run_dir.name,
        "protocol_commit": PROTOCOL_COMMIT,
        **result,
        "phase_runtime": phase_runtime,
        "abort_error": abort_error,
        "journal_sha256": _sha(journal.read_bytes()) if journal.exists() else None,
    }
    (run_dir / "summary.json").write_bytes(_canonical(summary))
    return summary


def run(base_url: str, timeout: int, output_root: Path) -> int:
    if PROTOCOL_COMMIT == "TO_BE_STAMPED":
        raise RuntimeError("Q-1 protocol must be committed and stamped before a live run")
    _validate_matrix()
    runtime_initial = runtime_manifest(base_url, timeout)
    verify_judge_identities(runtime_initial)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    run_dir = output_root / f"p7_v10_q1_{stamp}"
    (run_dir / "calls").mkdir(parents=True, exist_ok=False)
    journal = run_dir / "journal.jsonl"
    manifest = {
        "schema_version": "lyra.p7.v10-q1-run.v1",
        "run_id": run_dir.name,
        "protocol": "docs/P7_V10_Q1.md",
        "protocol_commit": PROTOCOL_COMMIT,
        "diagnostic_only": True,
        "synthetic_only": True,
        "language": "en",
        "mode": "JSON_ONLY_PROMPTED",
        "parameters": {
            "temperature": 0,
            "max_tokens": 512,
            "context_tokens": 32768,
            "think": False,
            "repetitions": REPETITIONS,
        },
        "calls_planned": EXPECTED_CALLS,
        "preflight_calls_planned": len(JUDGES),
        "runtime_initial": runtime_initial,
        "judges": [judge.__dict__ for judge in JUDGES],
        "cells": [
            {
                "fixture_id": cell.fixture_id,
                "orientation": cell.orientation,
                "expected_preference": cell.expected_preference,
                "pack_sha256": pack_sha256(cell.pack),
                "pack_bytes": len(canonical_json_bytes(cell.pack)),
                "schema_sha256": _sha(_canonical(compact_judgment_schema(cell.pack))),
                "prompt_sha256": _sha(compact_judge_prompt(cell.pack).encode("utf-8")),
            }
            for cell in q1_cells()
        ],
    }
    (run_dir / "manifest.json").write_bytes(_canonical(manifest))

    backend = OllamaJudgeBackend(base_url, "JSON_ONLY_PROMPTED")
    records: list[dict[str, Any]] = []
    phase_runtime: dict[str, Any] = {}
    call_number = 0
    try:
        for judge in JUDGES:
            preflight = _warm_model(base_url, timeout, run_dir, judge)
            runtime_before = runtime_manifest(base_url, timeout)
            verify_judge_identities(runtime_before)
            verify_judge_fully_loaded_on_gpu(runtime_before, judge)
            lock_path = _acquire_phase_lock(output_root, run_dir.name, judge)
            phase_runtime[judge.model] = {
                "preflight": preflight,
                "runtime_before": runtime_before,
                "lock": lock_path.name,
            }

            for job in q1_jobs_for_judge(judge):
                call_number += 1
                cell = job.cell
                schema = compact_judgment_schema(cell.pack)
                request = JudgeBackendRequest(
                    model=judge.model,
                    prompt=compact_judge_prompt(cell.pack),
                    full_schema=schema,
                    wire_schema=schema,
                    max_tokens=512,
                    context_tokens=32768,
                )
                call_id = f"q1-{call_number:03d}"
                request_raw = canonical_payload_bytes(backend, request)
                (run_dir / "calls" / f"{call_id}.request.json").write_bytes(request_raw)
                _append_jsonl(
                    journal,
                    {
                        "event": "call_started",
                        "call_id": call_id,
                        "run_id": run_dir.name,
                        "judge_model": judge.model,
                        "judge_digest": judge.digest,
                        "fixture_id": cell.fixture_id,
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
                    verdict = validate_compact_judgment(text, cell.pack)
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
                    "judge_model": judge.model,
                    "judge_digest": judge.digest,
                    "fixture_id": cell.fixture_id,
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
                    "criterion_directions": (
                        verdict.criteria.model_dump(mode="json") if verdict is not None else None
                    ),
                    "source_span_ids": verdict.source_span_ids if verdict is not None else None,
                    "turn_refs": (
                        [item.value for item in verdict.turn_refs] if verdict is not None else None
                    ),
                    "correct": valid and observed == cell.expected_preference,
                    "error": error,
                }
                _append_jsonl(journal, record)
                records.append(record)
                print(
                    json.dumps(
                        {
                            "call": call_number,
                            "of": EXPECTED_CALLS,
                            "judge": judge.model,
                            "fixture": cell.fixture_id,
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
            verify_judge_identities(runtime_after)
            verify_judge_fully_loaded_on_gpu(runtime_after, judge)
            phase_runtime[judge.model]["runtime_after"] = runtime_after

    except Exception as exc:
        abort_error = f"{type(exc).__name__}: {exc}"
        summary = _write_summary(
            run_dir,
            records,
            phase_runtime,
            journal,
            abort_error=abort_error,
        )
        print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)
        raise

    summary = _write_summary(run_dir, records, phase_runtime, journal)
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)
    return 0 if summary["qualified_for_v10_preregistration"] else 2


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
