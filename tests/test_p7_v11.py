"""Offline checks for the V10 single-judge campaign core and runner shell."""
from __future__ import annotations

import json

import pytest

from eval.p7_judge_backend import OllamaJudgeBackend, canonical_payload_bytes
from eval.p7_v11 import (
    CALL_CEILINGS,
    CONTEXT_TOKENS,
    JUDGE,
    MAX_TOKENS,
    PREREGISTRATION,
    Q0_EXPECTED_CALLS,
    Q0_REPETITIONS,
    REQUIRED_PHASES,
    evaluate_q0_records,
    judge_request,
    logical_preference,
    q0_jobs,
    q0_orientations,
    q0_preflight,
    resolve_single_judge_pair,
    verify_judge_identity,
)
from scripts.p7_v11 import IMPLEMENTED_PHASES, assert_runner_complete, run


def _perfect_records():
    records = []
    for job in q0_jobs():
        orientation = job.orientation
        expected = orientation.expected_preference
        records.append(
            {
                "fixture_id": orientation.fixture_id,
                "orientation": orientation.orientation,
                "repetition": job.repetition,
                "valid": True,
                "wire_clean": True,
                "observed_preference": expected,
                "expected_preference": expected,
                "observed_logical": logical_preference(expected, orientation.mapping),
            }
        )
    return records


def test_constants_match_frozen_preregistration():
    assert PREREGISTRATION == "PREREGISTRATION_v11.md"
    assert JUDGE.model == "qwen3.8:27b"
    assert JUDGE.digest == (
        "22130167c4c20e20c7b71454612966ca8e8171e9b3cc8ab6ce8aa6cbfec79643"
    )
    assert MAX_TOKENS == 512
    assert CONTEXT_TOKENS == 32768
    assert Q0_REPETITIONS == 3
    assert Q0_EXPECTED_CALLS == 18
    assert CALL_CEILINGS == {
        "q0_judge": 18,
        "calibration_producer": 432,
        "calibration_judge": 432,
        "heldout_producer": 900,
        "heldout_judge": 360,
        "total": 2142,
    }
    components = sum(v for k, v in CALL_CEILINGS.items() if k != "total")
    assert components == CALL_CEILINGS["total"]


def test_q0_matrix_is_six_cells_times_three_repetitions():
    jobs = q0_jobs()
    assert len(jobs) == Q0_EXPECTED_CALLS
    cells = {(job.orientation.fixture_id, job.orientation.orientation) for job in jobs}
    assert len(cells) == 6
    q0_preflight()  # ASCII + déterminisme des packs et des prompts, sans réseau


def test_judge_request_matches_the_frozen_reduced_transport():
    pack = q0_orientations()[0].pack
    request = judge_request(pack)
    payload = json.loads(
        canonical_payload_bytes(OllamaJudgeBackend("http://x", "JSON_ONLY_PROMPTED"), request)
    )
    assert payload["model"] == JUDGE.model
    assert payload["think"] is False
    assert payload["stream"] is False
    assert payload["format"] == "json"
    assert payload["options"] == {
        "temperature": 0.0,
        "num_predict": 512,
        "num_ctx": 32768,
    }


def test_q0_evaluation_passes_only_a_perfect_matrix():
    assert evaluate_q0_records(_perfect_records())["status"] == "Q0_PASSED"

    wrong = _perfect_records()
    flipped = "TIE" if wrong[0]["observed_preference"] != "TIE" else "A"
    wrong[0] = {
        **wrong[0],
        "observed_preference": flipped,
        "observed_logical": logical_preference(flipped, q0_jobs()[0].orientation.mapping),
    }
    assert evaluate_q0_records(wrong)["status"] == "V10_ABORTED_BEFORE_CALIBRATION"

    invalid = _perfect_records()
    invalid[5] = {
        **invalid[5],
        "valid": False,
        "observed_preference": "INVALID",
        "observed_logical": "INVALID",
    }
    assert evaluate_q0_records(invalid)["passed"] is False

    dirty = _perfect_records()
    dirty[9] = {**dirty[9], "wire_clean": False}
    assert evaluate_q0_records(dirty)["passed"] is False

    short = _perfect_records()[:-1]
    assert evaluate_q0_records(short)["passed"] is False


def test_single_judge_resolution_rule():
    assert resolve_single_judge_pair("A", "A") == {
        "stable": True,
        "resolved": True,
        "winner": "A",
    }
    assert resolve_single_judge_pair("TIE", "TIE") == {
        "stable": True,
        "resolved": False,
        "winner": None,
    }
    assert resolve_single_judge_pair("A", "B")["stable"] is False
    assert resolve_single_judge_pair("A", "TIE")["resolved"] is False
    assert resolve_single_judge_pair("INVALID", "INVALID")["stable"] is False


def test_judge_identity_is_pinned_exactly():
    verify_judge_identity({"models": {JUDGE.model: JUDGE.digest}})
    with pytest.raises(RuntimeError, match="digest mismatch"):
        verify_judge_identity({"models": {JUDGE.model: "moving-tag"}})


def test_the_complete_chain_lifts_the_guard():
    assert set(IMPLEMENTED_PHASES) == set(REQUIRED_PHASES)
    assert_runner_complete()  # ne lève plus : les quatre phases existent


def test_runner_refuses_to_run_while_any_phase_is_missing(monkeypatch, tmp_path):
    for missing in REQUIRED_PHASES:
        monkeypatch.setattr(
            "scripts.p7_v11.IMPLEMENTED_PHASES",
            tuple(phase for phase in REQUIRED_PHASES if phase != missing),
        )
        with pytest.raises(RuntimeError, match="incomplete"):
            assert_runner_complete()
        # run() doit refuser AVANT tout réseau et tout verrou : l'URL invalide
        # et le répertoire vide ne doivent jamais être touchés.
        with pytest.raises(RuntimeError, match="incomplete"):
            run("http://invalid.invalid", 1, tmp_path / "runs")
        assert not (tmp_path / "runs").exists()
