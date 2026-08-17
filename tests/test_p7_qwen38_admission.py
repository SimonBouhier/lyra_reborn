"""Offline checks for the diagnostic Qwen 3.8 admission matrix."""
from __future__ import annotations

import pytest

from eval.p7_evidence import canonical_json_bytes
from eval.p7_qwen38_admission import (
    CANDIDATE_DIGEST,
    CANDIDATE_MODEL,
    EXPECTED_CALLS,
    REPETITIONS,
    admission_cells,
    admission_jobs,
    summarize_records,
    verify_candidate_identity,
)
from scripts.p7_qwen38_admission import PROTOCOL_COMMIT


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
    assert PROTOCOL_COMMIT == "876d13f5cf8eac6bb863ee1205a5f172c824919d"
    cells = admission_cells()
    assert len(cells) == 8
    assert REPETITIONS == 3
    assert EXPECTED_CALLS == 24
    assert len(admission_jobs()) == EXPECTED_CALLS
    assert len({(cell.cell_id, cell.orientation) for cell in cells}) == 8
    for cell in cells:
        canonical_json_bytes(cell.pack).decode("ascii")


def test_forward_reverse_expectations_track_candidate_identity():
    by_fixture = {}
    for cell in admission_cells():
        by_fixture.setdefault(cell.cell_id, {})[cell.orientation] = cell.expected_preference
    assert by_fixture["TRANSPORT_PARITY"] == {"forward": "TIE", "reverse": "TIE"}
    assert by_fixture["STYLE_PARITY"] == {"forward": "TIE", "reverse": "TIE"}
    for fixture_id in ("SEMANTIC_DOMINANCE", "INJECTION_RESISTANCE"):
        assert {by_fixture[fixture_id]["forward"], by_fixture[fixture_id]["reverse"]} == {"A", "B"}


def test_summary_qualifies_only_a_complete_unanimous_matrix():
    records = _records()
    assert summarize_records(records)["qualified_for_v10_design"] is True
    records[0] = {**records[0], "observed_preference": "INVALID", "valid": False, "correct": False}
    failed = summarize_records(records)
    assert failed["qualified_for_v10_design"] is False
    assert failed["status"] == "NOT_QUALIFIED_FOR_V10_DESIGN"


def test_candidate_digest_is_pinned_exactly():
    verify_candidate_identity({"models": {CANDIDATE_MODEL: CANDIDATE_DIGEST}})
    with pytest.raises(RuntimeError, match="digest mismatch"):
        verify_candidate_identity({"models": {CANDIDATE_MODEL: "moving-tag"}})
