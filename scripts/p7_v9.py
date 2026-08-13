#!/usr/bin/env python
"""Runner au premier plan des portes synthétiques Q-1 puis Q0 de P7 V9."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import time
from typing import Any

import requests

from eval.p7_evidence import canonical_json_bytes, pack_sha256
from eval.p7_v7_judge import (
    JudgeContractError,
    judge_prompt,
    judgment_schema,
    validate_judgment,
)
from eval.p7_v7_q0 import GLOBAL_SEED, Q0Orientation, fixture_orientations, q0_fixtures
from eval.p7_v9_judge import qminus1_evidence_pack, wire_judgment_schema
from scripts.p7_v8 import (
    JUDGES,
    _append_jsonl,
    _call_sort_key,
    _canonical,
    _deterministic_preflight,
    _logical_preference,
    _runtime_manifest,
    _sha,
)


PREREG_FREEZE_COMMIT = "882f10cc04c7d470191d18a10df8063cd0b07c71"
PREREGISTRATION = "PREREGISTRATION_v9.md"


def _acquire_phase_lock(output_root: Path, phase: str, run_id: str) -> Path:
    """Un verrou par porte et par gel ; toute seconde tentative est interdite."""
    if phase not in {"Q-1", "Q0"}:
        raise ValueError(f"unsupported phase: {phase}")
    output_root.mkdir(parents=True, exist_ok=True)
    slug = "qminus1" if phase == "Q-1" else "q0"
    lock_path = output_root / f"p7_v9_{slug}_{PREREG_FREEZE_COMMIT}.lock"
    payload = _canonical(
        {
            "schema_version": "lyra.p7.v9-phase-lock.v1",
            "phase": phase,
            "preregistration_freeze_commit": PREREG_FREEZE_COMMIT,
            "run_id": run_id,
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
        }
    )
    with lock_path.open("xb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    return lock_path


def _judge_payload(judge_name: str, pack: Any) -> dict:
    return {
        "model": judge_name,
        "prompt": judge_prompt(pack),
        "stream": False,
        "think": False,
        "format": wire_judgment_schema(pack),
        "options": {"temperature": 0, "num_predict": 2048, "num_ctx": 32768},
    }


def _validate_response_body(body: dict, pack: Any):
    """Valide exclusivement `response` et refuse tout canal thinking non vide."""
    thinking = body.get("thinking")
    if thinking not in (None, ""):
        raise JudgeContractError("non-empty thinking channel")
    return validate_judgment(body.get("response", ""), pack)


def _run_judge_call(
    *,
    base_url: str,
    timeout: int,
    run_dir: Path,
    journal: Path,
    call_id: str,
    phase: str,
    judge_name: str,
    judge_digest: str,
    pack: Any,
    context: dict[str, Any],
) -> tuple[dict, Any | None]:
    payload = _judge_payload(judge_name, pack)
    request_raw = _canonical(payload)
    pack_hash = pack_sha256(pack)
    (run_dir / "calls" / f"{call_id}.request.json").write_bytes(request_raw)
    _append_jsonl(
        journal,
        {
            "event": "call_started",
            "call_id": call_id,
            "run_id": run_dir.name,
            "phase": phase,
            "judge": judge_name,
            "judge_digest": judge_digest,
            "pack_sha256": pack_hash,
            "request_sha256": _sha(request_raw),
            **context,
        },
    )
    started = time.perf_counter()
    response_sha = None
    error = None
    verdict = None
    response_present = False
    response_chars = 0
    thinking_present = False
    thinking_chars = 0
    done_reason = None
    api_meta: dict[str, Any] = {}
    try:
        response = requests.post(
            f"{base_url}/api/generate",
            data=request_raw,
            headers={"Content-Type": "application/json"},
            timeout=timeout,
        )
        response_raw = response.content
        response_sha = _sha(response_raw)
        (run_dir / "calls" / f"{call_id}.response.json").write_bytes(response_raw)
        response.raise_for_status()
        body = response.json()
        if not isinstance(body, dict):
            raise JudgeContractError("Ollama response body is not an object")
        response_present = "response" in body
        response_value = body.get("response")
        response_chars = len(response_value) if isinstance(response_value, str) else 0
        thinking_present = "thinking" in body
        thinking_value = body.get("thinking")
        thinking_chars = len(thinking_value) if isinstance(thinking_value, str) else 0
        done_reason = body.get("done_reason")
        api_meta = {
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
        verdict = _validate_response_body(body, pack)
    except (requests.RequestException, ValueError, JudgeContractError, json.JSONDecodeError) as exc:
        error = f"{type(exc).__name__}: {exc}"
    elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
    record = {
        "event": "call_finished",
        "call_id": call_id,
        "run_id": run_dir.name,
        "phase": phase,
        "judge": judge_name,
        "judge_digest": judge_digest,
        "pack_sha256": pack_hash,
        "request_sha256": _sha(request_raw),
        "response_sha256": response_sha,
        "response_present": response_present,
        "response_chars": response_chars,
        "thinking_present": thinking_present,
        "thinking_chars": thinking_chars,
        "done_reason": done_reason,
        "elapsed_ms": elapsed_ms,
        "api_meta": api_meta,
        "valid": verdict is not None,
        "error": error,
        **context,
    }
    _append_jsonl(journal, record)
    return record, verdict


def _schema_manifest(pack: Any) -> dict:
    validation_raw = _canonical(judgment_schema(pack))
    wire_raw = _canonical(wire_judgment_schema(pack))
    return {
        "validation_schema_sha256": _sha(validation_raw),
        "wire_schema_sha256": _sha(wire_raw),
        "wire_removed_keywords": ["maxLength", "minLength"],
    }


def run_qminus1(base_url: str, timeout: int, output_root: Path) -> int:
    runtime_before = _runtime_manifest(base_url, timeout)
    pack = qminus1_evidence_pack()
    first = canonical_json_bytes(pack)
    second = canonical_json_bytes(type(pack).model_validate_json(first))
    if first != second:
        raise RuntimeError("non-deterministic Q-1 pack")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    run_dir = output_root / f"p7_v9_qminus1_{stamp}"
    _acquire_phase_lock(output_root, "Q-1", run_dir.name)
    (run_dir / "calls").mkdir(parents=True, exist_ok=False)
    journal = run_dir / "journal.jsonl"
    manifest = {
        "schema_version": "lyra.p7.v9-qminus1-run.v1",
        "run_id": run_dir.name,
        "phase": "Q-1",
        "synthetic_only": True,
        "independent_of_q0": True,
        "preregistration": PREREGISTRATION,
        "preregistration_freeze_commit": PREREG_FREEZE_COMMIT,
        "runtime_before": runtime_before,
        "pack_sha256": pack_sha256(pack),
        "pack_bytes": len(first),
        **_schema_manifest(pack),
    }
    (run_dir / "manifest.json").write_bytes(_canonical(manifest))

    records = []
    for number, (judge_name, judge_digest) in enumerate(JUDGES, start=1):
        record, _ = _run_judge_call(
            base_url=base_url,
            timeout=timeout,
            run_dir=run_dir,
            journal=journal,
            call_id=f"qminus1-{number:03d}",
            phase="Q-1",
            judge_name=judge_name,
            judge_digest=judge_digest,
            pack=pack,
            context={},
        )
        records.append(record)
        print(
            json.dumps(
                {
                    "phase": "Q-1",
                    "call": number,
                    "of": 2,
                    "judge": judge_name,
                    "result": "PASS" if record["valid"] else "FAIL",
                },
                ensure_ascii=False,
            ),
            flush=True,
        )

    runtime_after = _runtime_manifest(base_url, timeout)
    passed = len(records) == 2 and all(item["valid"] for item in records)
    summary = {
        "schema_version": "lyra.p7.v9-qminus1-summary.v1",
        "run_id": run_dir.name,
        "status": "Q_MINUS_1_PASSED" if passed else "V9_ABORTED_BEFORE_Q0",
        "h9": "UNTESTED",
        "calls_planned": 2,
        "calls_recorded": len(records),
        "valid": sum(bool(item["valid"]) for item in records),
        "runtime_after": runtime_after,
        "journal_sha256": _sha(journal.read_bytes()),
    }
    (run_dir / "summary.json").write_bytes(_canonical(summary))
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)
    return 0 if passed else 2


def run_q0(base_url: str, timeout: int, output_root: Path) -> int:
    runtime_before = _runtime_manifest(base_url, timeout)
    fixtures = q0_fixtures()
    orientations = tuple(item for fixture in fixtures for item in fixture_orientations(fixture))
    if len(orientations) != 6:
        raise RuntimeError("Q0 must contain exactly six oriented packs")
    _deterministic_preflight(orientations)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    run_dir = output_root / f"p7_v9_q0_{stamp}"
    _acquire_phase_lock(output_root, "Q0", run_dir.name)
    (run_dir / "calls").mkdir(parents=True, exist_ok=False)
    journal = run_dir / "journal.jsonl"
    manifest = {
        "schema_version": "lyra.p7.v9-q0-run.v1",
        "run_id": run_dir.name,
        "phase": "Q0",
        "synthetic_only": True,
        "preregistration": PREREGISTRATION,
        "preregistration_freeze_commit": PREREG_FREEZE_COMMIT,
        "seed": GLOBAL_SEED,
        "runtime_before": runtime_before,
        **_schema_manifest(orientations[0].pack),
        "pack_manifest": [
            {
                "fixture_id": item.fixture_id,
                "orientation": item.orientation,
                "sha256": pack_sha256(item.pack),
                "bytes": len(canonical_json_bytes(item.pack)),
            }
            for item in orientations
        ],
    }
    (run_dir / "manifest.json").write_bytes(_canonical(manifest))

    records = []
    call_number = 0
    for judge_name, judge_digest in JUDGES:
        block = sorted(orientations, key=lambda item: _call_sort_key(judge_digest, item))
        for item in block:
            call_number += 1
            record, verdict = _run_judge_call(
                base_url=base_url,
                timeout=timeout,
                run_dir=run_dir,
                journal=journal,
                call_id=f"q0-{call_number:03d}",
                phase="Q0",
                judge_name=judge_name,
                judge_digest=judge_digest,
                pack=item.pack,
                context={
                    "fixture_id": item.fixture_id,
                    "orientation": item.orientation,
                },
            )
            observed = verdict.preference.value if verdict is not None else "INVALID"
            observed_logical = (
                _logical_preference(observed, item.mapping) if observed != "INVALID" else "INVALID"
            )
            expected_logical = (
                "TIE" if item.expected_preference == "TIE" else item.mapping[item.expected_preference]
            )
            record.update(
                {
                    "expected_preference": item.expected_preference,
                    "expected_logical": expected_logical,
                    "observed_preference": observed,
                    "observed_logical": observed_logical,
                    "passed": verdict is not None and observed == item.expected_preference,
                }
            )
            _append_jsonl(journal, {**record, "event": "q0_evaluation"})
            records.append(record)
            print(
                json.dumps(
                    {
                        "phase": "Q0",
                        "call": call_number,
                        "of": 12,
                        "judge": judge_name,
                        "fixture": item.fixture_id,
                        "orientation": item.orientation,
                        "result": "PASS" if record["passed"] else "FAIL",
                        "observed": observed,
                        "expected": item.expected_preference,
                    },
                    ensure_ascii=False,
                ),
                flush=True,
            )

    runtime_after = _runtime_manifest(base_url, timeout)
    passed = len(records) == 12 and all(item["passed"] for item in records)
    summary = {
        "schema_version": "lyra.p7.v9-q0-summary.v1",
        "run_id": run_dir.name,
        "status": "Q0_PASSED" if passed else "V9_ABORTED_BEFORE_CALIBRATION",
        "h9": "UNTESTED",
        "calls_planned": 12,
        "calls_recorded": len(records),
        "valid": sum(bool(item["valid"]) for item in records),
        "passed": sum(bool(item["passed"]) for item in records),
        "runtime_after": runtime_after,
        "journal_sha256": _sha(journal.read_bytes()),
    }
    (run_dir / "summary.json").write_bytes(_canonical(summary))
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)
    return 0 if passed else 2


def run(base_url: str, timeout: int, output_root: Path) -> int:
    qminus1_status = run_qminus1(base_url, timeout, output_root)
    if qminus1_status != 0:
        return qminus1_status
    return run_q0(base_url, timeout, output_root)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("run",))
    parser.add_argument("--base-url", default="http://127.0.0.1:11434")
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--output-root", type=Path, default=Path("data/runs"))
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    base_url = args.base_url.rstrip("/")
    return run(base_url, args.timeout, args.output_root)


if __name__ == "__main__":
    raise SystemExit(main())
