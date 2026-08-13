"""Q0 et evidence pack P7 V7 — tests synthétiques, aucune donnée tenue."""
from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from eval.p7_evidence import EvidencePack, canonical_json_bytes, invert_evidence_pack
from eval.p7_v7_judge import JudgeContractError, validate_judgment
from eval.p7_v7_q0 import fixture_orientations, q0_fixtures
from scripts.p7_v7 import _acquire_q0_lock


def _valid_judgment(pack, preference="TIE") -> str:
    span = pack.source.segments[0].source_span_id
    criteria = []
    names = ["fidelity", "uncertainty", "salience", "contradiction", "utility", "economy"]
    for index, name in enumerate(names):
        criteria.append(
            {
                "criterion": name,
                "direction": preference,
                "claim": f"Criterion {name} is substantively equivalent or follows the cited evidence in both candidates.",
                "source_span_ids": [span] if index == 0 else [],
                "turn_refs": ["A.T1", "B.T1"] if index == 0 else ["A.T2", "B.T2"],
            }
        )
    return json.dumps(
        {
            "preference": preference,
            "rationale": (
                "The global preference follows the source-grounded comparison across both complete trajectories. "
                "Formatting is not treated as evidence, uncertainty is checked against the source, and no substantive "
                "difference is inferred without a cited turn or segment."
            ),
            "criteria": criteria,
        }
    )


def test_q0_has_three_frozen_controls_and_six_deterministic_packs():
    fixtures = q0_fixtures()
    assert [item.fixture_id for item in fixtures] == [
        "SEMANTIC_DOMINANCE",
        "STYLE_PARITY",
        "INJECTION_RESISTANCE",
    ]
    orientations = [orientation for fixture in fixtures for orientation in fixture_orientations(fixture)]
    assert len(orientations) == 6
    for item in orientations:
        first = canonical_json_bytes(item.pack)
        second = canonical_json_bytes(EvidencePack.model_validate_json(first))
        assert first == second
        assert not first.endswith(b"\n")


def test_inversion_swaps_only_candidates_and_relabels_them():
    forward, reverse = fixture_orientations(q0_fixtures()[0])
    rebuilt = invert_evidence_pack(forward.pack)
    assert canonical_json_bytes(rebuilt) == canonical_json_bytes(reverse.pack)
    assert rebuilt.candidates[0].candidate == "A"
    assert rebuilt.candidates[1].candidate == "B"
    assert rebuilt.candidates[0].turns == forward.pack.candidates[1].turns
    assert rebuilt.source == forward.pack.source


def test_pack_is_closed_and_all_span_checks_resolve():
    pack = fixture_orientations(q0_fixtures()[0])[0].pack
    payload = pack.model_dump(mode="json")
    payload["arm"] = "ADAPTIVE"
    with pytest.raises(ValidationError):
        EvidencePack.model_validate(payload)
    source = {item.source_span_id: item.text for item in pack.source.segments}
    for candidate in pack.candidates:
        assert all(check.found and source[check.source_span_id] == check.text for check in candidate.span_checks)


def test_style_parity_differs_only_in_form_and_stays_within_five_percent_length():
    fixture = next(item for item in q0_fixtures() if item.fixture_id == "STYLE_PARITY")
    assert fixture.candidate_1.decision == fixture.candidate_2.decision
    assert fixture.candidate_1.outputs != fixture.candidate_2.outputs
    left = sum(len(item) for item in fixture.candidate_1.outputs)
    right = sum(len(item) for item in fixture.candidate_2.outputs)
    assert abs(left - right) / max(left, right) <= 0.05


def test_judge_contract_requires_order_coverage_and_resolved_spans():
    pack = fixture_orientations(q0_fixtures()[1])[0].pack
    verdict = validate_judgment(_valid_judgment(pack), pack)
    assert verdict.preference.value == "TIE"

    payload = json.loads(_valid_judgment(pack))
    payload["criteria"][0]["criterion"] = "economy"
    with pytest.raises(JudgeContractError):
        validate_judgment(json.dumps(payload), pack)

    payload = json.loads(_valid_judgment(pack))
    payload["criteria"][0]["source_span_ids"] = ["S999"]
    with pytest.raises(JudgeContractError, match="unresolved"):
        validate_judgment(json.dumps(payload), pack)


def test_q0_phase_lock_is_exclusive_and_cannot_be_replayed(tmp_path):
    first = _acquire_q0_lock(tmp_path, "run-first")
    assert first.exists()
    with pytest.raises(FileExistsError):
        _acquire_q0_lock(tmp_path, "run-second")
