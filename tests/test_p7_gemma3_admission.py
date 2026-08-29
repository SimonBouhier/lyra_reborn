"""Offline checks for the diagnostic Gemma 3 admission matrix (banc A)."""
from __future__ import annotations

import pytest

from eval.p7_evidence import canonical_json_bytes, pack_sha256
from eval.p7_gemma3_admission import (
    CANDIDATE_DIGEST,
    CANDIDATE_MODEL,
    EXPECTED_CALLS,
    REPETITIONS,
    admission_cells,
    admission_jobs,
    summarize_records,
    verify_candidate_fully_loaded_on_gpu,
    verify_candidate_identity,
)
from eval import p7_qwen38_admission
from scripts.p7_gemma3_admission import META_RULE_COMMIT, PROTOCOL_COMMIT


def _records():
    return [
        {
            "cell_id": job.cell.cell_id,
            "orientation": job.cell.orientation,
            "observed_preference": job.cell.expected_preference,
            "valid": True,
            "correct": True,
            "wire_clean": True,
        }
        for job in admission_jobs()
    ]


def test_matrix_is_eight_english_orientations_repeated_three_times():
    assert PROTOCOL_COMMIT == "TO_BE_STAMPED"
    assert META_RULE_COMMIT == "89d22f9b2fa36f3331d855a4288cf06dea888a95"
    cells = admission_cells()
    assert len(cells) == 8
    assert REPETITIONS == 3
    assert EXPECTED_CALLS == 24
    assert len(admission_jobs()) == EXPECTED_CALLS
    assert len({(cell.cell_id, cell.orientation) for cell in cells}) == 8
    for cell in cells:
        canonical_json_bytes(cell.pack).decode("ascii")


def test_exam_is_identical_to_the_qwen_admission_exam():
    """Every panel candidate takes exactly the same frozen exam."""
    ours = {
        (cell.cell_id, cell.orientation): pack_sha256(cell.pack)
        for cell in admission_cells()
    }
    qwen = {
        (cell.cell_id, cell.orientation): pack_sha256(cell.pack)
        for cell in p7_qwen38_admission.admission_cells()
    }
    assert ours == qwen


def test_call_order_is_salted_by_the_gemma3_digest():
    ours = [
        (job.cell.cell_id, job.cell.orientation, job.repetition)
        for job in admission_jobs()
    ]
    qwen = [
        (job.cell.cell_id, job.cell.orientation, job.repetition)
        for job in p7_qwen38_admission.admission_jobs()
    ]
    assert sorted(ours) == sorted(qwen)
    assert ours != qwen


def test_summary_qualifies_only_a_complete_unanimous_matrix():
    records = _records()
    assert summarize_records(records)["qualified_for_v10_design"] is True
    records[0] = {**records[0], "observed_preference": "INVALID", "valid": False, "correct": False}
    failed = summarize_records(records)
    assert failed["qualified_for_v10_design"] is False
    assert failed["status"] == "NOT_QUALIFIED_FOR_V10_DESIGN"


def test_candidate_digest_is_pinned_exactly():
    assert CANDIDATE_MODEL == "gemma3:27b"
    verify_candidate_identity({"models": {CANDIDATE_MODEL: CANDIDATE_DIGEST}})
    with pytest.raises(RuntimeError, match="digest mismatch"):
        verify_candidate_identity({"models": {CANDIDATE_MODEL: "moving-tag"}})


def test_candidate_must_be_fully_loaded_on_gpu_before_lock():
    loaded = {
        "loaded_models": {
            CANDIDATE_MODEL: {
                "digest": CANDIDATE_DIGEST,
                "size": 17_513_379_266,
                "size_vram": 17_513_379_266,
            }
        }
    }
    verify_candidate_fully_loaded_on_gpu(loaded)
    loaded["loaded_models"][CANDIDATE_MODEL]["size_vram"] = 0
    with pytest.raises(RuntimeError, match="not fully loaded on GPU"):
        verify_candidate_fully_loaded_on_gpu(loaded)
