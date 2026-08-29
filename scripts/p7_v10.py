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

from core.knobs import KnobMapping
from eval.p7_contracts import decision_schema
from eval.p7_evidence import (
    build_evidence_pack,
    canonical_json_bytes,
    invert_evidence_pack,
    pack_sha256,
)
from eval.p7_judge_backend import OllamaJudgeBackend, canonical_payload_bytes
from eval.p7_trajectory import (
    _finish_trace,
    _make_loop,
    _prompt,
    _trace_turn,
)
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
    resolve_single_judge_pair,
    validate_compact_judgment,
    verify_judge_gpu,
    verify_judge_identity,
)
from eval.p7_v10_calibration import (
    CALIBRATION_CASES,
    CALIBRATION_COMPARISONS,
    PRESETS,
    ablation_winners,
    plan_comparisons,
    preset_knobs,
    q1_gate,
    select_static_best,
    trajectory_seed,
)
from eval.p7_v10_corpus import CORPUS_SEED, calibration_cases, seal_manifest
from eval.p7_v10_execution import (
    POLICY_IDENTIFIERS,
    JudgeCall,
    candidate_material,
    deblind,
    objective_failure,
    order_judge_calls,
    pack_blindness,
    pack_integrity,
    pair_position,
    seal_blind_mapping,
)
from eval.p7_v10_producer import (
    PRODUCERS,
    OllamaProducerClient,
    load_model,
    models_runtime,
    unload_model,
    verify_fully_loaded_on_gpu,
    verify_identity,
)
from eval.p7_v7_judge import JudgeContractError

# Retirer un nom de cette liste exige d'implémenter sa phase et ses tests.
IMPLEMENTED_PHASES = ("Q0", "CALIBRATION")

ROOT = Path(__file__).resolve().parents[1]

# Mapping producteur gelé V8 (« mapping 128-768 ») et résidence du bloc.
PRODUCER_MAPPING = KnobMapping(num_predict_min=128, num_predict_max=768)
BLOCK_KEEP_ALIVE = "30m"
TRAJECTORY_TURNS = (1, 2, 3)


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


def runtime_manifest(base_url: str, timeout: int) -> dict[str, Any]:
    """Manifeste runtime du juge seul — forme inchangée depuis la couche 1."""
    return models_runtime(base_url, timeout, (JUDGE.model,))


def _phase_models() -> tuple[str, ...]:
    return tuple(spec.model for spec in PRODUCERS) + (JUDGE.model,)


def _verify_phase_catalog(runtime: dict[str, Any]) -> None:
    for spec in PRODUCERS:
        verify_identity(runtime, spec)
    verify_judge_identity(runtime)


def _prove_gpu_residency(base_url: str, timeout: int) -> list[dict[str, Any]]:
    """Preuve GPU de la phase, AVANT son verrou : chaque modèle, seul, entier.

    Un modèle à la fois — charger, constater `size_vram == size`, décharger —
    parce que les blocs de la campagne sont séquentiels (VRAM 24 Go) et qu'un
    modèle partiellement déporté en RAM invaliderait ses mesures de latence.
    Ces requêtes de résidence ont un prompt vide : elles ne produisent aucun
    token et n'entrent dans aucun plafond d'appels.
    """
    proofs: list[dict[str, Any]] = []
    for spec in (*PRODUCERS, JUDGE):
        load_model(base_url, spec.model, timeout, keep_alive=BLOCK_KEEP_ALIVE)
        runtime = models_runtime(base_url, timeout, (spec.model,))
        verify_identity(runtime, spec)
        verify_fully_loaded_on_gpu(runtime, spec)
        proofs.append(
            {
                "model": spec.model,
                "digest": spec.digest,
                "loaded": runtime["loaded_models"][spec.model],
            }
        )
        unload_model(base_url, spec.model, timeout)
    return proofs


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


def _run_trajectory(
    *,
    base_url: str,
    timeout: int,
    case: Any,
    policy: str,
    knobs: Any,
    spec: Any,
    seeds: dict[int, int],
    adaptive: bool = False,
):
    """Trajectoire de trois tours d'une politique statique sur un cas.

    Un client producteur par trajectoire : l'attribution des appels aux tours
    est alors exacte, sans dépendre d'un ordre positionnel. Les helpers gelés
    de `eval.p7_trajectory` fabriquent prompt, boucle, trace et clôture — ce
    module ne réécrit aucun d'entre eux.
    """
    client = OllamaProducerClient(base_url, spec.model, timeout)
    loop = _make_loop(client, PRODUCER_MAPPING, knobs, adaptive=adaptive)
    turns = []
    prior: list[str] = []
    for turn in TRAJECTORY_TURNS:
        prompt = _prompt(case, turn, tuple(prior))
        result = loop.generate(
            prompt,
            task_type="general",
            generation_options={"seed": seeds[turn]},
            response_format=decision_schema(case.source_text) if turn == 3 else None,
        )
        turns.append(_trace_turn(turn, prompt, result))
        prior.append(result.output)
    trace = _finish_trace(
        arm=policy, case=case, model_digest=spec.digest, turns=turns
    )
    return trace, tuple(client.calls)


def _judge_block(
    *,
    base_url: str,
    timeout: int,
    run_dir: Path,
    journal: Path,
    phase: str,
    calls: list[JudgeCall],
) -> dict[tuple[str, str], dict[str, Any]]:
    """Bloc juge unique : ordre gelé, requêtes sans historique, digest encadré.

    La requête est fabriquée par `eval.p7_v10.judge_request`, seule autorité du
    transport : elle est octet-identique à celle de Q-1 et de Q0.
    """
    ordered = order_judge_calls(calls)
    load_model(base_url, JUDGE.model, timeout, keep_alive=BLOCK_KEEP_ALIVE)
    runtime_before = models_runtime(base_url, timeout, (JUDGE.model,))
    verify_judge_identity(runtime_before)
    verify_judge_gpu(runtime_before)
    _append_jsonl(
        journal,
        {
            "event": "judge_block_started",
            "run_id": run_dir.name,
            "phase": phase,
            "calls_planned": len(ordered),
            "runtime": runtime_before,
        },
    )

    backend = OllamaJudgeBackend(base_url, "JSON_ONLY_PROMPTED")
    results: dict[tuple[str, str], dict[str, Any]] = {}
    for number, call in enumerate(ordered, start=1):
        request = judge_request(call.pack)
        call_id = f"{phase.lower()}-judge-{number:04d}"
        request_raw = canonical_payload_bytes(backend, request)
        (run_dir / "calls" / f"{call_id}.request.json").write_bytes(request_raw)
        _append_jsonl(
            journal,
            {
                "event": "call_started",
                "call_id": call_id,
                "run_id": run_dir.name,
                "phase": phase,
                "comparison_id": call.comparison_id,
                "orientation": call.orientation,
                "pack_sha256": call.pack_sha256,
                "request_sha256": _sha(request_raw),
                **dict(call.context),
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
            verdict = validate_compact_judgment(text, call.pack)
        except (requests.RequestException, ValueError, json.JSONDecodeError) as exc:
            error = f"{type(exc).__name__}: {exc}"
        observed = verdict.preference if verdict is not None else "INVALID"
        observed = observed.value if hasattr(observed, "value") else observed
        record = {
            "event": "call_finished",
            "call_id": call_id,
            "run_id": run_dir.name,
            "phase": phase,
            "comparison_id": call.comparison_id,
            "orientation": call.orientation,
            "pack_sha256": call.pack_sha256,
            "request_sha256": _sha(request_raw),
            "response_sha256": response_sha,
            "status_code": status_code,
            "response_chars": len(text),
            "reasoning_chars": len(reasoning),
            "done_reason": done_reason,
            "elapsed_ms": round((time.perf_counter() - started) * 1000, 3),
            "api_meta": api_meta,
            "wire_clean": (
                status_code == 200
                and bool(text.strip())
                and not reasoning
                and done_reason == "stop"
            ),
            "valid": verdict is not None,
            "observed_preference": observed,
            "error": error,
            **dict(call.context),
        }
        _append_jsonl(journal, record)
        results[(call.comparison_id, call.orientation)] = {
            "valid": verdict is not None,
            "preference": observed,
            "wire_clean": record["wire_clean"],
        }
        print(
            json.dumps(
                {
                    "phase": phase,
                    "call": number,
                    "of": len(ordered),
                    "comparison": call.comparison_id,
                    "orientation": call.orientation,
                    "valid": verdict is not None,
                    "observed": observed,
                },
                ensure_ascii=False,
            ),
            flush=True,
        )

    runtime_after = models_runtime(base_url, timeout, (JUDGE.model,))
    verify_judge_identity(runtime_after)
    verify_judge_gpu(runtime_after)
    _append_jsonl(
        journal,
        {
            "event": "judge_block_finished",
            "run_id": run_dir.name,
            "phase": phase,
            "calls_recorded": len(results),
            "runtime": runtime_after,
        },
    )
    unload_model(base_url, JUDGE.model, timeout)
    return results


def run_calibration(
    base_url: str, timeout: int, output_root: Path
) -> tuple[int, dict[str, Any]]:
    """Calibration V8 incorporée : 4 presets par cas, 6 paires, porte Q1.

    Blocs séquentiels : les trois producteurs d'abord, un par un, puis le juge
    seul. Tout ce qui est vérifiable — corpus, plan, mapping, digests, preuve
    GPU de chaque modèle — l'est AVANT le verrou de phase.
    """
    cases = calibration_cases(ROOT)
    if len(cases) != CALIBRATION_CASES:
        raise RuntimeError(f"calibration must hold {CALIBRATION_CASES} sealed cases")
    corpus_seal = seal_manifest(cases, phase="calibration")
    plan = plan_comparisons(tuple((case.case_id, case.source_name) for case in cases))
    if len(plan) != CALIBRATION_COMPARISONS:
        raise RuntimeError("comparison plan differs from the frozen 72 per producer")

    def comparison_id(model: str, item) -> str:
        return f"{model}|{item.case_id}|{item.pair[0]}|{item.pair[1]}"

    mapping_seal = seal_blind_mapping(
        (
            {
                "comparison_id": comparison_id(spec.model, item),
                "candidate_a": item.candidate_a,
                "candidate_b": item.candidate_b,
            }
            for spec in PRODUCERS
            for item in plan
        ),
        phase="calibration",
    )

    planned_producer_calls = (
        len(cases) * len(PRESETS) * len(TRAJECTORY_TURNS) * len(PRODUCERS)
    )
    planned_judge_calls = len(plan) * len(PRODUCERS) * 2
    if planned_producer_calls > CALL_CEILINGS["calibration_producer"]:
        raise RuntimeError("calibration producer plan exceeds the frozen ceiling")
    if planned_judge_calls > CALL_CEILINGS["calibration_judge"]:
        raise RuntimeError("calibration judge plan exceeds the frozen ceiling")

    runtime_before = models_runtime(base_url, timeout, _phase_models())
    _verify_phase_catalog(runtime_before)
    gpu_proofs = _prove_gpu_residency(base_url, timeout)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    run_dir = output_root / f"p7_v10_calibration_{stamp}"
    _acquire_phase_lock(output_root, "calibration", run_dir.name)
    (run_dir / "calls").mkdir(parents=True, exist_ok=False)
    journal = run_dir / "journal.jsonl"
    (run_dir / "corpus_seal.json").write_bytes(_canonical(corpus_seal))
    (run_dir / "blind_mapping.json").write_bytes(_canonical(mapping_seal))
    sealed_at = datetime.now(timezone.utc).isoformat()

    manifest = {
        "schema_version": "lyra.p7.v10-calibration-run.v1",
        "run_id": run_dir.name,
        "phase": "CALIBRATION",
        "preregistration": PREREGISTRATION,
        "preregistration_freeze_commit": PREREG_FREEZE_COMMIT,
        "prerun_amendment": PRERUN_AMENDMENT,
        "independence_note": INDEPENDENCE_NOTE,
        "seed": CORPUS_SEED,
        "judge": {"model": JUDGE.model, "digest": JUDGE.digest},
        "producers": [
            {"model": spec.model, "digest": spec.digest, "family": spec.family}
            for spec in PRODUCERS
        ],
        "presets": list(PRESETS),
        "knob_mapping": {
            "num_predict_min": PRODUCER_MAPPING.num_predict_min,
            "num_predict_max": PRODUCER_MAPPING.num_predict_max,
        },
        "corpus_seal_sha256": corpus_seal["seal_sha256"],
        "blind_mapping_sha256": mapping_seal["seal_sha256"],
        "sealed_at_utc": sealed_at,
        "calls_planned": {
            "producer": planned_producer_calls,
            "judge": planned_judge_calls,
        },
        "call_ceilings": CALL_CEILINGS,
        "content_handling": (
            "journal sans contenu (comptes et hashes) ; les payloads de requete "
            "et de reponse sont conserves sous calls/ comme preuve d appel"
        ),
        "runtime_before": runtime_before,
        "gpu_residency_proofs": gpu_proofs,
    }
    (run_dir / "manifest.json").write_bytes(_canonical(manifest))

    traces: dict[tuple[str, str, str], Any] = {}
    trajectory_calls: dict[tuple[str, str, str], tuple] = {}
    producer_calls_emitted = 0
    for spec in PRODUCERS:
        load_model(base_url, spec.model, timeout, keep_alive=BLOCK_KEEP_ALIVE)
        block_runtime = models_runtime(base_url, timeout, (spec.model,))
        verify_identity(block_runtime, spec)
        verify_fully_loaded_on_gpu(block_runtime, spec)
        _append_jsonl(
            journal,
            {
                "event": "producer_block_started",
                "run_id": run_dir.name,
                "phase": "CALIBRATION",
                "producer": spec.model,
                "runtime": block_runtime,
            },
        )
        for case in cases:
            for preset in PRESETS:
                seeds = {
                    turn: trajectory_seed(case.case_id, preset, spec.digest, turn)
                    for turn in TRAJECTORY_TURNS
                }
                trace, calls = _run_trajectory(
                    base_url=base_url,
                    timeout=timeout,
                    case=case,
                    policy=preset,
                    knobs=preset_knobs(preset),
                    spec=spec,
                    seeds=seeds,
                )
                key = (spec.model, case.case_id, preset)
                traces[key] = trace
                trajectory_calls[key] = calls
                producer_calls_emitted += len(calls)
                failure = objective_failure(trace)
                for call in calls:
                    _append_jsonl(
                        journal,
                        {
                            "event": "producer_call",
                            "run_id": run_dir.name,
                            "phase": "CALIBRATION",
                            "producer": spec.model,
                            "case_id": case.case_id,
                            "source": case.source_name,
                            "preset": preset,
                            **call.as_record(),
                        },
                    )
                _append_jsonl(
                    journal,
                    {
                        "event": "trajectory_finished",
                        "run_id": run_dir.name,
                        "phase": "CALIBRATION",
                        "producer": spec.model,
                        "case_id": case.case_id,
                        "source": case.source_name,
                        "preset": preset,
                        "complete": trace.complete,
                        "objective_failure": failure,
                        "output_tokens": sum(call.output_tokens for call in calls),
                        "calls": len(calls),
                    },
                )
                print(
                    json.dumps(
                        {
                            "phase": "CALIBRATION",
                            "producer": spec.model,
                            "case": case.case_id,
                            "preset": preset,
                            "complete": trace.complete,
                            "producer_calls": producer_calls_emitted,
                            "of": planned_producer_calls,
                        },
                        ensure_ascii=False,
                    ),
                    flush=True,
                )
        after = models_runtime(base_url, timeout, (spec.model,))
        verify_identity(after, spec)
        _append_jsonl(
            journal,
            {
                "event": "producer_block_finished",
                "run_id": run_dir.name,
                "phase": "CALIBRATION",
                "producer": spec.model,
                "runtime": after,
            },
        )
        unload_model(base_url, spec.model, timeout)

    if producer_calls_emitted > CALL_CEILINGS["calibration_producer"]:
        raise RuntimeError("calibration exceeded the frozen producer call ceiling")

    judge_calls: list[JudgeCall] = []
    comparisons: dict[str, dict[str, Any]] = {}
    for spec in PRODUCERS:
        forbidden = (*POLICY_IDENTIFIERS, spec.model)
        for item in plan:
            identifier = comparison_id(spec.model, item)
            trace_a = traces[(spec.model, item.case_id, item.candidate_a)]
            trace_b = traces[(spec.model, item.case_id, item.candidate_b)]
            complete = trace_a.complete and trace_b.complete
            entry: dict[str, Any] = {
                "comparison_id": identifier,
                "producer": spec.model,
                "case_id": item.case_id,
                "source": item.source,
                "pair": item.pair,
                "candidate_a": item.candidate_a,
                "candidate_b": item.candidate_b,
                "complete": complete,
                "judged": False,
                "pack_error": None,
            }
            if complete:
                try:
                    case = next(c for c in cases if c.case_id == item.case_id)
                    forward = build_evidence_pack(
                        case.source_text,
                        candidate_material(trace_a),
                        candidate_material(trace_b),
                    )
                    reverse = invert_evidence_pack(forward)
                except (ValueError, TypeError) as exc:
                    entry["pack_error"] = f"{type(exc).__name__}: {exc}"
                else:
                    integrity = pack_integrity(forward)
                    blindness = pack_blindness(forward, forbidden=forbidden)
                    entry["pack_sha256"] = integrity["sha256"]
                    entry["pack_integrity"] = integrity
                    entry["pack_blindness"] = blindness
                    entry["judged"] = True
                    for orientation, pack in (("forward", forward), ("reverse", reverse)):
                        judge_calls.append(
                            JudgeCall(
                                comparison_id=identifier,
                                orientation=orientation,
                                pack=pack,
                                pack_sha256=pack_sha256(pack),
                                context={
                                    "producer": spec.model,
                                    "case_id": item.case_id,
                                    "source": item.source,
                                },
                            )
                        )
            comparisons[identifier] = entry
            _append_jsonl(
                journal,
                {
                    "event": "comparison_prepared",
                    "run_id": run_dir.name,
                    "phase": "CALIBRATION",
                    **{k: v for k, v in entry.items() if k != "pair"},
                    "pair": list(item.pair),
                },
            )

    if len(judge_calls) > CALL_CEILINGS["calibration_judge"]:
        raise RuntimeError("calibration exceeded the frozen judge call ceiling")

    verdicts = _judge_block(
        base_url=base_url,
        timeout=timeout,
        run_dir=run_dir,
        journal=journal,
        phase="CALIBRATION",
        calls=judge_calls,
    )

    outcomes: list[dict[str, Any]] = []
    for identifier, entry in sorted(comparisons.items()):
        mapping = {"A": entry["candidate_a"], "B": entry["candidate_b"]}
        forward = verdicts.get((identifier, "forward"))
        reverse = verdicts.get((identifier, "reverse"))
        forward_preset = (
            deblind(forward["preference"], "forward", mapping) if forward else "INVALID"
        )
        reverse_preset = (
            deblind(reverse["preference"], "reverse", mapping) if reverse else "INVALID"
        )
        resolution = resolve_single_judge_pair(
            pair_position(forward_preset, entry["pair"]),
            pair_position(reverse_preset, entry["pair"]),
        )
        winner = resolution["winner"]
        outcome = {
            "comparison_id": identifier,
            "producer": entry["producer"],
            "case_id": entry["case_id"],
            "source": entry["source"],
            "pair": entry["pair"],
            "complete": entry["complete"],
            "judged": entry["judged"],
            "forward_preset": forward_preset,
            "reverse_preset": reverse_preset,
            "stable": resolution["stable"],
            "resolved": resolution["resolved"],
            "winner_preset": (
                entry["pair"][0] if winner == "A" else entry["pair"][1] if winner == "B" else None
            ),
        }
        outcomes.append(outcome)
        _append_jsonl(
            journal,
            {
                "event": "comparison_resolved",
                "run_id": run_dir.name,
                "phase": "CALIBRATION",
                **outcome,
                "pair": list(entry["pair"]),
            },
        )

    failure_counts = {preset: 0 for preset in PRESETS}
    failure_totals = {preset: 0 for preset in PRESETS}
    output_tokens = {preset: 0 for preset in PRESETS}
    for (model, case_id, preset), trace in traces.items():
        failure_totals[preset] += 1
        if objective_failure(trace)["failed"]:
            failure_counts[preset] += 1
        output_tokens[preset] += sum(
            call.output_tokens for call in trajectory_calls[(model, case_id, preset)]
        )
    failure_rates = {
        preset: (failure_counts[preset] / failure_totals[preset])
        if failure_totals[preset]
        else 0.0
        for preset in PRESETS
    }

    selection = select_static_best(
        outcomes, failure_rates=failure_rates, output_tokens=output_tokens
    )
    ablations = ablation_winners(
        outcomes, failure_rates=failure_rates, output_tokens=output_tokens
    )
    gate = q1_gate(outcomes, selection, ablations)

    # Q1 gelée V8, première clause : « le round-robin gelé est complet sans
    # relance sélective ». Elle ne porte pas sur les verdicts mais sur la
    # conduite du run, donc elle se constate ici et non dans `q1_gate`.
    expected_ids = {
        comparison_id(spec.model, item) for spec in PRODUCERS for item in plan
    }
    round_robin_complete = (
        {item["comparison_id"] for item in outcomes} == expected_ids
        and len(outcomes) == len(expected_ids)
        and producer_calls_emitted == planned_producer_calls
    )
    q1_passed = bool(gate["passed"] and round_robin_complete)

    summary = {
        "schema_version": "lyra.p7.v10-calibration-summary.v1",
        "run_id": run_dir.name,
        "phase": "CALIBRATION",
        "preregistration_freeze_commit": PREREG_FREEZE_COMMIT,
        "independence_note": INDEPENDENCE_NOTE,
        "h10": "UNTESTED",
        "producer_calls": producer_calls_emitted,
        "judge_calls": len(judge_calls),
        "comparisons": len(outcomes),
        "complete_comparisons": sum(1 for item in outcomes if item["complete"]),
        "judged_comparisons": sum(1 for item in outcomes if item["judged"]),
        "objective_failure_rates": failure_rates,
        "output_tokens": output_tokens,
        "selection": selection,
        "ablation_winners": ablations,
        "q1": gate,
        "round_robin_complete": round_robin_complete,
        "q1_passed": q1_passed,
        "static_best": selection["winner"] if q1_passed else None,
        "status": "Q1_PASSED" if q1_passed else "V10_ABORTED_BEFORE_HELDOUT",
        "journal_sha256": _sha(journal.read_bytes()),
    }
    (run_dir / "summary.json").write_bytes(_canonical(summary))
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)
    return (0 if q1_passed else 2), summary


def run_heldout(base_url: str, timeout: int, output_root: Path, static_best: str) -> int:
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
    status, calibration = run_calibration(base_url, timeout, output_root)
    if status != 0:
        return status
    status = run_heldout(base_url, timeout, output_root, calibration["static_best"])
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
