#!/usr/bin/env python
"""Banc synthétique non confirmatoire des transports de juges P7."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import time
from typing import Any, Literal

import requests
from pydantic import ValidationError

from eval.p7_evidence import EvidencePack, canonical_json_bytes, pack_sha256
from eval.p7_judge_backend import (
    JudgeBackendRequest,
    OllamaJudgeBackend,
    canonical_payload_bytes,
)
from eval.p7_judge_prompt import judge_prompt_with_contract
from eval.p7_v7_judge import JudgeContractError, JudgeVerdict, judgment_schema, validate_judgment
from eval.p7_v7_q0 import GLOBAL_SEED, fixture_orientations, q0_fixtures
from eval.p7_v9_judge import qminus1_evidence_pack, wire_judgment_schema
from scripts.p7_v8 import JUDGES, _runtime_manifest


PROTOCOL_COMMIT = "69e34deab012895caf4f0b377d8622f942febb86"
MODES = ("JSON_ONLY_PROMPTED", "WIRE_SCHEMA_PROMPTED")
EXPECTED_CALLS = 16


@dataclass(frozen=True)
class BenchCell:
    cell_id: str
    pack: EvidencePack
    expected_preference: Literal["A", "B", "TIE"]


def bench_cells() -> tuple[BenchCell, ...]:
    cells = [BenchCell("TRANSPORT_PARITY", qminus1_evidence_pack(), "TIE")]
    for fixture in q0_fixtures():
        forward = fixture_orientations(fixture)[0]
        cells.append(BenchCell(fixture.fixture_id, forward.pack, forward.expected_preference))
    return tuple(cells)


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _append_jsonl(path: Path, value: dict[str, Any]) -> None:
    with path.open("ab") as handle:
        handle.write(_canonical(value) + b"\n")
        handle.flush()
        os.fsync(handle.fileno())


def _acquire_lock(output_root: Path, run_id: str) -> Path:
    output_root.mkdir(parents=True, exist_ok=True)
    path = output_root / f"p7_backend_bench_{PROTOCOL_COMMIT}.lock"
    payload = {
        "schema_version": "lyra.p7.backend-bench-lock.v1",
        "protocol_commit": PROTOCOL_COMMIT,
        "run_id": run_id,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    with path.open("xb") as handle:
        handle.write(_canonical(payload))
        handle.flush()
        os.fsync(handle.fileno())
    return path


def _diagnose_invalid(raw: str, pack: EvidencePack) -> list[dict[str, Any]]:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        return [{"path": [], "type": "json_invalid", "message": str(exc)}]
    try:
        verdict = JudgeVerdict.model_validate(payload)
    except ValidationError as exc:
        return [
            {
                "path": list(item["loc"]),
                "type": item["type"],
                "message": item["msg"],
            }
            for item in exc.errors(include_url=False, include_context=False, include_input=False)
        ]
    allowed = {item.source_span_id for item in pack.source.segments}
    observed = {span for item in verdict.criteria for span in item.source_span_ids}
    unresolved = sorted(observed - allowed)
    if unresolved:
        return [{"path": ["criteria", "source_span_ids"], "type": "unresolved", "message": ",".join(unresolved)}]
    return [{"path": [], "type": "unknown_contract_error", "message": "validation failed without detail"}]


def _order_key(judge_digest: str, mode: str, cell: BenchCell) -> str:
    raw = f"{GLOBAL_SEED}\0backend-bench\0{judge_digest}\0{mode}\0{pack_sha256(cell.pack)}".encode()
    return _sha(raw)


def run_ollama(base_url: str, timeout: int, output_root: Path) -> int:
    runtime_before = _runtime_manifest(base_url, timeout)
    cells = bench_cells()
    if len(cells) != 4:
        raise RuntimeError("backend bench must contain exactly four development cells")
    for cell in cells:
        raw = canonical_json_bytes(cell.pack)
        if raw != canonical_json_bytes(EvidencePack.model_validate_json(raw)):
            raise RuntimeError(f"non-deterministic pack: {cell.cell_id}")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    run_dir = output_root / f"p7_backend_bench_{stamp}"
    _acquire_lock(output_root, run_dir.name)
    (run_dir / "calls").mkdir(parents=True, exist_ok=False)
    journal = run_dir / "journal.jsonl"
    manifest = {
        "schema_version": "lyra.p7.backend-bench-run.v1",
        "run_id": run_dir.name,
        "protocol": "docs/P7_JUDGE_BACKEND_BENCH.md",
        "protocol_commit": PROTOCOL_COMMIT,
        "diagnostic_only": True,
        "synthetic_only": True,
        "modes": list(MODES),
        "calls_planned": EXPECTED_CALLS,
        "runtime_before": runtime_before,
        "cells": [
            {
                "cell_id": cell.cell_id,
                "expected_preference": cell.expected_preference,
                "pack_sha256": pack_sha256(cell.pack),
                "pack_bytes": len(canonical_json_bytes(cell.pack)),
                "full_schema_sha256": _sha(_canonical(judgment_schema(cell.pack))),
                "wire_schema_sha256": _sha(_canonical(wire_judgment_schema(cell.pack))),
            }
            for cell in cells
        ],
    }
    (run_dir / "manifest.json").write_bytes(_canonical(manifest))

    records: list[dict[str, Any]] = []
    call_number = 0
    for judge_name, judge_digest in JUDGES:
        jobs = [(mode, cell) for mode in MODES for cell in cells]
        jobs.sort(key=lambda item: _order_key(judge_digest, item[0], item[1]))
        for mode, cell in jobs:
            call_number += 1
            backend = OllamaJudgeBackend(base_url, mode)
            request = JudgeBackendRequest(
                model=judge_name,
                prompt=judge_prompt_with_contract(cell.pack),
                full_schema=judgment_schema(cell.pack),
                wire_schema=wire_judgment_schema(cell.pack),
            )
            call_id = f"bench-{call_number:03d}"
            request_raw = canonical_payload_bytes(backend, request)
            (run_dir / "calls" / f"{call_id}.request.json").write_bytes(request_raw)
            started_record = {
                "event": "call_started",
                "call_id": call_id,
                "run_id": run_dir.name,
                "judge": judge_name,
                "judge_digest": judge_digest,
                "mode": mode,
                "cell_id": cell.cell_id,
                "pack_sha256": pack_sha256(cell.pack),
                "prompt_sha256": _sha(request.prompt.encode("utf-8")),
                "request_sha256": _sha(request_raw),
            }
            _append_jsonl(journal, started_record)
            started = time.perf_counter()
            response_sha = None
            text = ""
            reasoning = ""
            done_reason = None
            status_code = None
            api_meta: dict[str, Any] = {}
            error = None
            contract_errors: list[dict[str, Any]] = []
            verdict = None
            try:
                response = backend.generate(request, timeout)
                response_sha = _sha(response.raw)
                (run_dir / "calls" / f"{call_id}.response.json").write_bytes(response.raw)
                status_code = response.status_code
                text = response.text
                reasoning = response.reasoning
                done_reason = response.done_reason
                api_meta = response.api_meta
                try:
                    verdict = validate_judgment(text, cell.pack)
                except JudgeContractError as exc:
                    error = f"JudgeContractError: {exc}"
                    contract_errors = _diagnose_invalid(text, cell.pack)
            except (requests.RequestException, ValueError, json.JSONDecodeError) as exc:
                error = f"{type(exc).__name__}: {exc}"
            observed = verdict.preference.value if verdict is not None else "INVALID"
            valid = verdict is not None
            correct = valid and observed == cell.expected_preference
            record = {
                "event": "call_finished",
                "call_id": call_id,
                "run_id": run_dir.name,
                "judge": judge_name,
                "judge_digest": judge_digest,
                "mode": mode,
                "cell_id": cell.cell_id,
                "pack_sha256": pack_sha256(cell.pack),
                "prompt_sha256": _sha(request.prompt.encode("utf-8")),
                "request_sha256": _sha(request_raw),
                "response_sha256": response_sha,
                "status_code": status_code,
                "response_chars": len(text),
                "reasoning_chars": len(reasoning),
                "done_reason": done_reason,
                "elapsed_ms": round((time.perf_counter() - started) * 1000, 3),
                "api_meta": api_meta,
                "valid": valid,
                "expected_preference": cell.expected_preference,
                "observed_preference": observed,
                "correct": correct,
                "contract_errors": contract_errors,
                "error": error,
            }
            _append_jsonl(journal, record)
            records.append(record)
            print(
                json.dumps(
                    {
                        "call": call_number,
                        "of": EXPECTED_CALLS,
                        "judge": judge_name,
                        "mode": mode,
                        "cell": cell.cell_id,
                        "valid": valid,
                        "observed": observed,
                        "expected": cell.expected_preference,
                    },
                    ensure_ascii=False,
                ),
                flush=True,
            )

    runtime_after = _runtime_manifest(base_url, timeout)
    mode_results = {}
    for mode in MODES:
        selected = [item for item in records if item["mode"] == mode]
        mode_results[mode] = {
            "calls": len(selected),
            "valid": sum(bool(item["valid"]) for item in selected),
            "correct": sum(bool(item["correct"]) for item in selected),
            "admissible": len(selected) == 8 and all(item["valid"] and item["correct"] for item in selected),
        }
    json_ok = mode_results["JSON_ONLY_PROMPTED"]["admissible"]
    wire_ok = mode_results["WIRE_SCHEMA_PROMPTED"]["admissible"]
    if json_ok:
        selected_mode = "JSON_ONLY_PROMPTED"
        status = "OLLAMA_MODE_SELECTED"
    elif wire_ok:
        selected_mode = "WIRE_SCHEMA_PROMPTED"
        status = "OLLAMA_MODE_SELECTED"
    else:
        selected_mode = None
        status = "OLLAMA_INADMISSIBLE_TEST_LLAMA_SERVER"
    summary = {
        "schema_version": "lyra.p7.backend-bench-summary.v1",
        "run_id": run_dir.name,
        "status": status,
        "diagnostic_only": True,
        "calls_planned": EXPECTED_CALLS,
        "calls_recorded": len(records),
        "mode_results": mode_results,
        "selected_mode": selected_mode,
        "runtime_after": runtime_after,
        "journal_sha256": _sha(journal.read_bytes()),
    }
    (run_dir / "summary.json").write_bytes(_canonical(summary))
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)
    return 0 if selected_mode is not None else 2


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("ollama",))
    parser.add_argument("--base-url", default="http://127.0.0.1:11434")
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--output-root", type=Path, default=Path("data/runs"))
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    return run_ollama(args.base_url.rstrip("/"), args.timeout, args.output_root)


if __name__ == "__main__":
    raise SystemExit(main())
