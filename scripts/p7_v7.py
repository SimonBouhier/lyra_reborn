#!/usr/bin/env python
"""Runner P7 V7. La seule phase actuellement exposée est Q0 synthétique."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import sys
import time
from typing import Any

import pydantic
import requests

from eval.p7_evidence import canonical_json_bytes, invert_evidence_pack, pack_sha256
from eval.p7_v7_judge import JudgeContractError, judge_prompt, judgment_schema, validate_judgment
from eval.p7_v7_q0 import GLOBAL_SEED, Q0Orientation, fixture_orientations, q0_fixtures


PREREG_FREEZE_COMMIT = "3a0be82b923f93198f67613375cf717a70a0522a"
EXPECTED_RUNTIME = {"python": "3.14.7", "pydantic": "2.13.4", "ollama": "0.32.9"}
JUDGES = (
    ("qwen3.6:27b", "a50eda8ed977ab48a12431878896b27ffd5cef552c17af3317d9623b939a7f1e"),
    ("glm-4.7-flash:latest", "4475827791a269b02c8ec49b1c3bc1abb5846bacf3fae015b75d33986322d8f6"),
)


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _append_jsonl(path: Path, value: dict) -> None:
    line = _canonical(value) + b"\n"
    with path.open("ab") as handle:
        handle.write(line)
        handle.flush()
        os.fsync(handle.fileno())


def _acquire_q0_lock(output_root: Path, run_id: str) -> Path:
    """Interdit toute seconde tentative Q0 pour le même gel V7."""
    output_root.mkdir(parents=True, exist_ok=True)
    lock_path = output_root / f"p7_v7_q0_{PREREG_FREEZE_COMMIT}.lock"
    payload = _canonical(
        {
            "schema_version": "lyra.p7.phase-lock.v1",
            "phase": "Q0",
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


def _api_get(base_url: str, endpoint: str, timeout: int) -> dict:
    response = requests.get(f"{base_url}{endpoint}", timeout=timeout)
    response.raise_for_status()
    return response.json()


def _runtime_manifest(base_url: str, timeout: int) -> dict:
    version = _api_get(base_url, "/api/version", timeout)["version"]
    tags = _api_get(base_url, "/api/tags", timeout).get("models", [])
    digests = {item["name"]: item["digest"] for item in tags}
    manifest = {
        "python": platform.python_version(),
        "pydantic": pydantic.__version__,
        "ollama": version,
        "models": {name: digests.get(name) for name, _ in JUDGES},
    }
    errors = []
    for key, expected in EXPECTED_RUNTIME.items():
        if manifest[key] != expected:
            errors.append(f"{key}: expected {expected}, got {manifest[key]}")
    for name, expected in JUDGES:
        if manifest["models"].get(name) != expected:
            errors.append(f"{name}: digest mismatch")
    if errors:
        raise RuntimeError("; ".join(errors))
    return manifest


def _call_sort_key(judge_digest: str, orientation: Q0Orientation) -> str:
    material = (
        f"{GLOBAL_SEED}\0judge_order\0{judge_digest}\0"
        f"{pack_sha256(orientation.pack)}\0{orientation.orientation}"
    ).encode("utf-8")
    return hashlib.sha256(material).hexdigest()


def _logical_preference(preference: str, mapping: dict[str, str]) -> str:
    return "TIE" if preference == "TIE" else mapping[preference]


def _deterministic_preflight(orientations: tuple[Q0Orientation, ...]) -> None:
    for item in orientations:
        first = canonical_json_bytes(item.pack)
        second = canonical_json_bytes(type(item.pack).model_validate_json(first))
        if first != second:
            raise RuntimeError(f"non-deterministic pack: {item.fixture_id}/{item.orientation}")
    by_fixture: dict[str, dict[str, Q0Orientation]] = {}
    for item in orientations:
        by_fixture.setdefault(item.fixture_id, {})[item.orientation] = item
    for fixture_id, pair in by_fixture.items():
        rebuilt = invert_evidence_pack(pair["forward"].pack)
        if canonical_json_bytes(rebuilt) != canonical_json_bytes(pair["reverse"].pack):
            raise RuntimeError(f"inverse mismatch: {fixture_id}")


def _run_call(
    *,
    base_url: str,
    timeout: int,
    run_dir: Path,
    journal: Path,
    call_number: int,
    judge_name: str,
    judge_digest: str,
    item: Q0Orientation,
) -> dict:
    call_id = f"q0-{call_number:03d}"
    pack_hash = pack_sha256(item.pack)
    payload = {
        "model": judge_name,
        "prompt": judge_prompt(item.pack),
        "stream": False,
        "format": judgment_schema(item.pack),
        "options": {"temperature": 0, "num_predict": 2048, "num_ctx": 32768},
    }
    request_raw = _canonical(payload)
    request_path = run_dir / "calls" / f"{call_id}.request.json"
    request_path.write_bytes(request_raw)
    _append_jsonl(
        journal,
        {
            "event": "call_started",
            "call_id": call_id,
            "run_id": run_dir.name,
            "phase": "Q0",
            "fixture_id": item.fixture_id,
            "orientation": item.orientation,
            "judge": judge_name,
            "judge_digest": judge_digest,
            "pack_sha256": pack_hash,
            "request_sha256": _sha(request_raw),
        },
    )
    started = time.perf_counter()
    response_raw = b""
    response_sha = None
    error = None
    verdict = None
    api_meta: dict[str, Any] = {}
    try:
        response = requests.post(f"{base_url}/api/generate", data=request_raw, headers={"Content-Type": "application/json"}, timeout=timeout)
        response_raw = response.content
        response_sha = _sha(response_raw)
        (run_dir / "calls" / f"{call_id}.response.json").write_bytes(response_raw)
        response.raise_for_status()
        body = response.json()
        api_meta = {
            key: body.get(key)
            for key in ("total_duration", "load_duration", "prompt_eval_count", "prompt_eval_duration", "eval_count", "eval_duration")
        }
        verdict = validate_judgment(body.get("response", ""), item.pack)
    except (requests.RequestException, ValueError, JudgeContractError, json.JSONDecodeError) as exc:
        error = f"{type(exc).__name__}: {exc}"
    elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
    observed = verdict.preference.value if verdict is not None else "INVALID"
    observed_logical = _logical_preference(observed, item.mapping) if observed != "INVALID" else "INVALID"
    expected_logical = "TIE" if item.expected_preference == "TIE" else item.mapping[item.expected_preference]
    passed = verdict is not None and observed == item.expected_preference
    record = {
        "event": "call_finished",
        "call_id": call_id,
        "run_id": run_dir.name,
        "phase": "Q0",
        "fixture_id": item.fixture_id,
        "orientation": item.orientation,
        "judge": judge_name,
        "judge_digest": judge_digest,
        "pack_sha256": pack_hash,
        "request_sha256": _sha(request_raw),
        "response_sha256": response_sha,
        "elapsed_ms": elapsed_ms,
        "api_meta": api_meta,
        "expected_preference": item.expected_preference,
        "expected_logical": expected_logical,
        "observed_preference": observed,
        "observed_logical": observed_logical,
        "valid": verdict is not None,
        "passed": passed,
        "error": error,
    }
    _append_jsonl(journal, record)
    return record


def run_q0(base_url: str, timeout: int, output_root: Path) -> int:
    runtime_before = _runtime_manifest(base_url, timeout)
    fixtures = q0_fixtures()
    orientations = tuple(item for fixture in fixtures for item in fixture_orientations(fixture))
    if len(orientations) != 6:
        raise RuntimeError("Q0 must contain exactly six oriented packs")
    _deterministic_preflight(orientations)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    run_dir = output_root / f"p7_v7_q0_{stamp}"
    _acquire_q0_lock(output_root, run_dir.name)
    (run_dir / "calls").mkdir(parents=True, exist_ok=False)
    journal = run_dir / "journal.jsonl"
    manifest = {
        "schema_version": "lyra.p7.q0-run.v1",
        "run_id": run_dir.name,
        "phase": "Q0",
        "synthetic_only": True,
        "preregistration": "PREREGISTRATION_v7.md",
        "preregistration_freeze_commit": PREREG_FREEZE_COMMIT,
        "seed": GLOBAL_SEED,
        "runtime_before": runtime_before,
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
            record = _run_call(
                base_url=base_url,
                timeout=timeout,
                run_dir=run_dir,
                journal=journal,
                call_number=call_number,
                judge_name=judge_name,
                judge_digest=judge_digest,
                item=item,
            )
            records.append(record)
            print(
                json.dumps(
                    {
                        "call": call_number,
                        "of": 12,
                        "judge": judge_name,
                        "fixture": item.fixture_id,
                        "orientation": item.orientation,
                        "result": "PASS" if record["passed"] else "FAIL",
                        "observed": record["observed_preference"],
                        "expected": record["expected_preference"],
                    },
                    ensure_ascii=False,
                ),
                flush=True,
            )
        runtime_after_block = _runtime_manifest(base_url, timeout)
        if runtime_after_block["models"][judge_name] != judge_digest:
            raise RuntimeError(f"judge digest changed during block: {judge_name}")

    runtime_after = _runtime_manifest(base_url, timeout)
    passed = len(records) == 12 and all(item["passed"] for item in records)
    summary = {
        "schema_version": "lyra.p7.q0-summary.v1",
        "run_id": run_dir.name,
        "status": "Q0_PASSED" if passed else "V7_ABORTED_BEFORE_CALIBRATION",
        "h7": "UNTESTED",
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("q0",))
    parser.add_argument("--base-url", default="http://127.0.0.1:11434")
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--output-root", type=Path, default=Path("data/runs"))
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    if args.phase == "q0":
        return run_q0(args.base_url.rstrip("/"), args.timeout, args.output_root)
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
