#!/usr/bin/env python
"""Commande unique de la campagne V10 (PREREGISTRATION_v10.md, gel bc8497f).

Q0 -> calibration -> tenu -> scoreur, un verrou exclusif par phase créé après
la preuve GPU de la phase. La garde de complétude interdit tout run vivant
tant que la chaîne entière n'est pas implémentée : aucune phase ne peut se
consommer contre un runner à moitié construit.
"""
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

from eval.p7_evidence import canonical_json_bytes, pack_sha256
from eval.p7_judge_backend import OllamaJudgeBackend, canonical_payload_bytes
from eval.p7_v10 import (
    CALL_CEILINGS,
    CONTEXT_TOKENS,
    INDEPENDENCE_NOTE,
    JUDGE,
    MAX_TOKENS,
    PREREG_FREEZE_COMMIT,
    PREREGISTRATION,
    PRERUN_AMENDMENT,
    Q0_EXPECTED_CALLS,
    REQUIRED_PHASES,
    evaluate_q0_records,
    judge_request,
    logical_preference,
    q0_jobs,
    q0_preflight,
    validate_compact_judgment,
    verify_judge_gpu,
    verify_judge_identity,
)
from eval.p7_v7_judge import JudgeContractError

# Retirer un nom de cette liste exige d'implémenter sa phase et ses tests.
IMPLEMENTED_PHASES = ("Q0",)


def assert_runner_complete() -> None:
    missing = [phase for phase in REQUIRED_PHASES if phase not in IMPLEMENTED_PHASES]
    if missing:
        raise RuntimeError(
            "V10 runner incomplete - missing phases "
            f"{missing}; the single frozen command must implement the full "
            "chain before any live run (PREREGISTRATION_v10.md, Execution)"
        )


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
    models = {
        item.get("name"): item.get("digest")
        for item in tags
        if isinstance(item, dict) and isinstance(item.get("name"), str)
    }
    loaded_items = _api_get(base_url, "/api/ps", timeout).get("models", [])
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
        "models": {JUDGE.model: models.get(JUDGE.model)},
        "loaded_models": {JUDGE.model: loaded_models.get(JUDGE.model)},
    }


def _acquire_phase_lock(output_root: Path, phase_slug: str, run_id: str) -> Path:
    output_root.mkdir(parents=True, exist_ok=True)
    lock_path = output_root / f"p7_v10_{phase_slug}_{PREREG_FREEZE_COMMIT}.lock"
    payload = {
        "schema_version": "lyra.p7.v10-phase-lock.v1",
        "phase": phase_slug,
        "preregistration": PREREGISTRATION,
        "preregistration_freeze_commit": PREREG_FREEZE_COMMIT,
        "prerun_amendment": PRERUN_AMENDMENT,
        "run_id": run_id,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    with lock_path.open("xb") as handle:
        handle.write(_canonical(payload))
        handle.flush()
        os.fsync(handle.fileno())
    return lock_path


def run_q0(base_url: str, timeout: int, output_root: Path) -> int:
    jobs = q0_jobs()
    q0_preflight()

    runtime_before = runtime_manifest(base_url, timeout)
    verify_judge_identity(runtime_before)
    verify_judge_gpu(runtime_before)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    run_dir = output_root / f"p7_v10_q0_{stamp}"
    _acquire_phase_lock(output_root, "q0", run_dir.name)
    (run_dir / "calls").mkdir(parents=True, exist_ok=False)
    journal = run_dir / "journal.jsonl"

    manifest = {
        "schema_version": "lyra.p7.v10-q0-run.v1",
        "run_id": run_dir.name,
        "phase": "Q0",
        "synthetic_only": True,
        "language": "en",
        "preregistration": PREREGISTRATION,
        "preregistration_freeze_commit": PREREG_FREEZE_COMMIT,
        "prerun_amendment": PRERUN_AMENDMENT,
        "independence_note": INDEPENDENCE_NOTE,
        "judge": {
            "model": JUDGE.model,
            "digest": JUDGE.digest,
            "family": JUDGE.family,
            "quantization": JUDGE.quantization,
        },
        "mode": "JSON_ONLY_PROMPTED",
        "parameters": {
            "temperature": 0,
            "max_tokens": MAX_TOKENS,
            "context_tokens": CONTEXT_TOKENS,
            "think": False,
        },
        "calls_planned": Q0_EXPECTED_CALLS,
        "call_ceilings": CALL_CEILINGS,
        "runtime_before": runtime_before,
        "pack_manifest": [
            {
                "fixture_id": job.orientation.fixture_id,
                "orientation": job.orientation.orientation,
                "repetition": job.repetition,
                "pack_sha256": pack_sha256(job.orientation.pack),
                "pack_bytes": len(canonical_json_bytes(job.orientation.pack)),
            }
            for job in jobs
        ],
    }
    (run_dir / "manifest.json").write_bytes(_canonical(manifest))

    backend = OllamaJudgeBackend(base_url, "JSON_ONLY_PROMPTED")
    records: list[dict[str, Any]] = []
    for number, job in enumerate(jobs, start=1):
        orientation = job.orientation
        request = judge_request(orientation.pack)
        call_id = f"q0-{number:03d}"
        request_raw = canonical_payload_bytes(backend, request)
        (run_dir / "calls" / f"{call_id}.request.json").write_bytes(request_raw)
        _append_jsonl(
            journal,
            {
                "event": "call_started",
                "call_id": call_id,
                "run_id": run_dir.name,
                "phase": "Q0",
                "fixture_id": orientation.fixture_id,
                "orientation": orientation.orientation,
                "repetition": job.repetition,
                "pack_sha256": pack_sha256(orientation.pack),
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
            verdict = validate_compact_judgment(text, orientation.pack)
        except (requests.RequestException, ValueError, json.JSONDecodeError) as exc:
            error = f"{type(exc).__name__}: {exc}"
        observed = verdict.preference if verdict is not None else "INVALID"
        observed = observed.value if hasattr(observed, "value") else observed
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
            "phase": "Q0",
            "fixture_id": orientation.fixture_id,
            "orientation": orientation.orientation,
            "repetition": job.repetition,
            "pack_sha256": pack_sha256(orientation.pack),
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
            "expected_preference": orientation.expected_preference,
            "observed_preference": observed,
            "observed_logical": (
                logical_preference(observed, orientation.mapping)
                if observed != "INVALID"
                else "INVALID"
            ),
            "error": error,
        }
        _append_jsonl(journal, record)
        records.append(record)
        print(
            json.dumps(
                {
                    "phase": "Q0",
                    "call": number,
                    "of": Q0_EXPECTED_CALLS,
                    "fixture": orientation.fixture_id,
                    "orientation": orientation.orientation,
                    "repetition": job.repetition,
                    "valid": valid,
                    "observed": observed,
                    "expected": orientation.expected_preference,
                },
                ensure_ascii=False,
            ),
            flush=True,
        )

    runtime_after = runtime_manifest(base_url, timeout)
    verify_judge_identity(runtime_after)
    verify_judge_gpu(runtime_after)
    evaluation = evaluate_q0_records(records)
    summary = {
        "schema_version": "lyra.p7.v10-q0-summary.v1",
        "run_id": run_dir.name,
        "preregistration_freeze_commit": PREREG_FREEZE_COMMIT,
        "independence_note": INDEPENDENCE_NOTE,
        "h10": "UNTESTED",
        **evaluation,
        "runtime_after": runtime_after,
        "journal_sha256": _sha(journal.read_bytes()),
    }
    (run_dir / "summary.json").write_bytes(_canonical(summary))
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)
    return 0 if evaluation["passed"] else 2


def run_calibration(base_url: str, timeout: int, output_root: Path) -> int:
    raise NotImplementedError(
        "V10 calibration phase is not implemented yet - see docs/P7_V10_RUNNER_PLAN.md layer 3"
    )


def run_heldout(base_url: str, timeout: int, output_root: Path) -> int:
    raise NotImplementedError(
        "V10 held-out phase is not implemented yet - see docs/P7_V10_RUNNER_PLAN.md layer 4"
    )


def run_scoring(output_root: Path) -> int:
    raise NotImplementedError(
        "V10 scoring phase is not implemented yet - see docs/P7_V10_RUNNER_PLAN.md layer 5"
    )


def run(base_url: str, timeout: int, output_root: Path) -> int:
    assert_runner_complete()
    status = run_q0(base_url, timeout, output_root)
    if status != 0:
        return status
    status = run_calibration(base_url, timeout, output_root)
    if status != 0:
        return status
    status = run_heldout(base_url, timeout, output_root)
    if status != 0:
        return status
    return run_scoring(output_root)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("run",))
    parser.add_argument("--base-url", default="http://127.0.0.1:11434")
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--output-root", type=Path, default=Path("data/runs"))
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    return run(args.base_url.rstrip("/"), args.timeout, args.output_root)


if __name__ == "__main__":
    raise SystemExit(main())
