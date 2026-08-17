"""Offline checks for the fresh P7 V10 Q-1 judge qualification."""
from __future__ import annotations

import json
import subprocess
import sys

import pytest

from eval.p7_evidence import canonical_json_bytes
from eval.p7_v10_q1 import (
    EXPECTED_CALLS,
    JUDGES,
    REPETITIONS,
    compact_judge_prompt,
    compact_judgment_schema,
    q1_cells,
    q1_fixtures,
    q1_jobs_for_judge,
    summarize_records,
    validate_compact_judgment,
    verify_judge_fully_loaded_on_gpu,
    verify_judge_identities,
)
from eval.p7_v7_judge import JudgeContractError
from eval.p7_v7_q0 import q0_fixtures
from scripts.p7_v10_q1 import PROTOCOL_COMMIT


def _valid_payload(pack, preference="A"):
    return {
        "preference": preference,
        "criteria": {
            "fidelity": preference,
            "uncertainty": preference,
            "salience": preference,
            "contradiction": preference,
            "utility": preference,
            "economy": preference,
        },
        "source_span_ids": [pack.source.segments[0].source_span_id],
        "turn_refs": ["A.T1", "B.T1"],
    }


def _passing_records():
    return [
        {
            "judge_model": judge.model,
            "fixture_id": job.cell.fixture_id,
            "orientation": job.cell.orientation,
            "observed_preference": job.cell.expected_preference,
            "valid": True,
            "correct": True,
            "wire_clean": True,
        }
        for judge in JUDGES
        for job in q1_jobs_for_judge(judge)
    ]


def test_matrix_is_fresh_english_ascii_two_family_design():
    assert PROTOCOL_COMMIT == "7540912d57ba1a113e1af7f2d43cec261f0834d8"
    assert len(JUDGES) == 2
    assert len({judge.family for judge in JUDGES}) == 2
    assert len(q1_fixtures()) == 3
    assert len(q1_cells()) == 6
    assert REPETITIONS == 3
    assert EXPECTED_CALLS == 36
    assert {item.fixture_id for item in q1_fixtures()}.isdisjoint(
        {item.fixture_id for item in q0_fixtures()}
    )
    assert {item.source for item in q1_fixtures()}.isdisjoint(
        {item.source for item in q0_fixtures()}
    )
    for cell in q1_cells():
        canonical_json_bytes(cell.pack).decode("ascii")
        compact_judge_prompt(cell.pack).encode("ascii")
    for judge in JUDGES:
        assert len(q1_jobs_for_judge(judge)) == 18


def test_forward_reverse_expectations_track_candidate_identity():
    by_fixture = {}
    for cell in q1_cells():
        by_fixture.setdefault(cell.fixture_id, {})[cell.orientation] = cell.expected_preference
    assert by_fixture["FORM_PARITY"] == {"forward": "TIE", "reverse": "TIE"}
    for fixture_id in ("TRADEOFF_AND_LIMITS", "UNTRUSTED_CONFLICT"):
        assert by_fixture[fixture_id] == {"forward": "A", "reverse": "B"}


def test_compact_contract_removes_generated_explanations_but_keeps_rubric_and_refs():
    pack = q1_cells()[0].pack
    schema = compact_judgment_schema(pack)
    serialized = json.dumps(schema, sort_keys=True)
    assert "rationale" not in serialized
    assert "claim" not in serialized
    assert set(schema["$defs"]["CompactCriterionDirections"]["required"]) == {
        "fidelity",
        "uncertainty",
        "salience",
        "contradiction",
        "utility",
        "economy",
    }
    assert schema["properties"]["source_span_ids"]["items"]["enum"] == [
        item.source_span_id for item in pack.source.segments
    ]
    verdict = validate_compact_judgment(json.dumps(_valid_payload(pack)), pack)
    assert verdict.preference.value == "A"


def test_compact_contract_rejects_missing_candidate_or_unknown_span():
    pack = q1_cells()[0].pack
    missing_candidate = _valid_payload(pack)
    missing_candidate["turn_refs"] = ["A.T1", "A.T2"]
    with pytest.raises(JudgeContractError, match="compact closed schema"):
        validate_compact_judgment(json.dumps(missing_candidate), pack)

    unknown_span = _valid_payload(pack)
    unknown_span["source_span_ids"] = ["S999"]
    with pytest.raises(JudgeContractError, match="unresolved source"):
        validate_compact_judgment(json.dumps(unknown_span), pack)


def test_summary_qualifies_only_a_complete_unanimous_panel():
    records = _passing_records()
    passed = summarize_records(records)
    assert passed["calls_recorded"] == EXPECTED_CALLS
    assert passed["qualified_for_v10_preregistration"] is True
    records[0] = {
        **records[0],
        "observed_preference": "INVALID",
        "valid": False,
        "correct": False,
    }
    failed = summarize_records(records)
    assert failed["qualified_for_v10_preregistration"] is False
    assert failed["status"] == "NOT_QUALIFIED_FOR_V10_PREREGISTRATION"


def test_judge_digests_and_gpu_residency_are_closed_preconditions():
    runtime = {
        "models": {judge.model: judge.digest for judge in JUDGES},
        "loaded_models": {
            JUDGES[0].model: {
                "digest": JUDGES[0].digest,
                "size": 17_399_745_083,
                "size_vram": 17_399_745_083,
            }
        },
    }
    verify_judge_identities(runtime)
    verify_judge_fully_loaded_on_gpu(runtime, JUDGES[0])
    bad_runtime = {
        **runtime,
        "models": {**runtime["models"], JUDGES[1].model: "moving-tag"},
    }
    with pytest.raises(RuntimeError, match="digest mismatch"):
        verify_judge_identities(bad_runtime)
    runtime["loaded_models"][JUDGES[0].model]["size_vram"] = 0
    with pytest.raises(RuntimeError, match="not fully loaded on GPU"):
        verify_judge_fully_loaded_on_gpu(runtime, JUDGES[0])


def test_published_module_entrypoint_imports_from_repository_root():
    completed = subprocess.run(
        [sys.executable, "-m", "scripts.p7_v10_q1", "--help"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    assert "diagnostic-only P7 V10 Q-1" in completed.stdout
