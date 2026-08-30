"""Offline checks for the shared V10 execution logic (calibration and held-out)."""
from __future__ import annotations

import hashlib
import json

import pytest

from eval.p7_contracts import validate_editorial_decision
from eval.p7_evidence import (
    CandidateMaterial,
    build_evidence_pack,
    canonical_json_bytes,
    invert_evidence_pack,
    pack_sha256,
)
from eval.p7_trajectory import ARM_ADAPTIVE, ARM_STATIC, EvaluationCase, PolicyTrace, TraceTurn
from eval.p7_v11 import JUDGE, resolve_single_judge_pair
from eval.p7_v10_execution import (
    POLICY_IDENTIFIERS,
    JudgeCall,
    candidate_material,
    deblind,
    judge_call_sort_key,
    objective_failure,
    order_judge_calls,
    pack_blindness,
    pack_integrity,
    pair_position,
    seal_blind_mapping,
)
from eval.p7_v7_q0 import GLOBAL_SEED
from tests.p7_v10_fakes import decision_payload

SOURCE = (
    "A registry received 12 submissions. Ten passed the required schema and two "
    "were rejected because a mandatory field was missing. The registry did not "
    "score or rank the accepted submissions."
)


def _trace(arm: str, marker: str, *, truncated: bool = False, complete: bool = True):
    final = json.dumps(decision_payload(320), ensure_ascii=False)
    outputs = [f"First analysis {marker}", f"Best objection {marker}", final]
    if not complete:
        outputs[-1] = "not json"
    turns = tuple(
        TraceTurn(
            turn=index,
            prompt=f"prompt {index}",
            output=output,
            options={"num_predict": 320, "seed": 1},
            knobs_used={},
            knobs_next={},
            metrics={"truncated": 1.0 if truncated and index == 2 else 0.0},
        )
        for index, output in enumerate(outputs, start=1)
    )
    decision = None
    error = None
    try:
        decision = validate_editorial_decision(turns[-1].output, SOURCE)
    except Exception as exc:  # noqa: BLE001 - le test veut la trace incomplète
        error = str(exc)
    return PolicyTrace(
        arm=arm,
        case_id="synthetic:1",
        model_digest="digest",
        turns=turns,
        decision=decision,
        contract_error=error,
    )


def _pack(marker_a: str = "alpha", marker_b: str = "beta"):
    return build_evidence_pack(
        SOURCE,
        candidate_material(_trace(ARM_ADAPTIVE, marker_a)),
        candidate_material(_trace(ARM_STATIC, marker_b)),
    )


def test_judge_order_reproduces_the_frozen_preregistration_formula():
    pack = _pack()
    sha = pack_sha256(pack)
    expected = hashlib.sha256(
        f"{GLOBAL_SEED}\0judge_order\0{JUDGE.digest}\0{sha}\0forward".encode("utf-8")
    ).hexdigest()
    assert judge_call_sort_key(sha, "forward") == expected
    assert judge_call_sort_key(sha, "reverse") != expected
    with pytest.raises(ValueError):
        judge_call_sort_key(sha, "sideways")


def test_judge_calls_form_one_deterministic_block():
    calls = []
    for index in range(4):
        pack = _pack(f"a{index}", f"b{index}")
        for orientation, oriented in (("forward", pack), ("reverse", invert_evidence_pack(pack))):
            calls.append(
                JudgeCall(
                    comparison_id=f"cmp-{index}",
                    orientation=orientation,
                    pack=oriented,
                    pack_sha256=pack_sha256(oriented),
                    context={},
                )
            )
    ordered = order_judge_calls(calls)
    assert len(ordered) == 8
    assert ordered == order_judge_calls(reversed(calls))  # ordre indépendant de l'entrée
    keys = [call.sort_key for call in ordered]
    assert keys == sorted(keys)
    # Les deux orientations d'une même comparaison ne sont pas contiguës par
    # construction : le tri gelé les disperse dans le bloc.
    assert {(call.comparison_id, call.orientation) for call in ordered} == {
        (f"cmp-{index}", orientation)
        for index in range(4)
        for orientation in ("forward", "reverse")
    }


def test_material_refuses_an_incomplete_trajectory():
    with pytest.raises(ValueError, match="incomplete"):
        candidate_material(_trace(ARM_ADAPTIVE, "x", complete=False))


def test_deblinding_follows_the_orientation_of_the_pack():
    mapping = {"A": ARM_ADAPTIVE, "B": ARM_STATIC}
    assert deblind("A", "forward", mapping) == ARM_ADAPTIVE
    assert deblind("B", "forward", mapping) == ARM_STATIC
    # Le pack inverse échange les candidats : son A montre le B de l'aller.
    assert deblind("A", "reverse", mapping) == ARM_STATIC
    assert deblind("B", "reverse", mapping) == ARM_ADAPTIVE
    for passthrough in ("TIE", "INVALID"):
        assert deblind(passthrough, "forward", mapping) == passthrough
        assert deblind(passthrough, "reverse", mapping) == passthrough
    with pytest.raises(ValueError):
        deblind("C", "forward", mapping)
    with pytest.raises(ValueError):
        deblind("A", "sideways", mapping)


def test_a_stable_judge_resolves_to_the_same_policy_in_both_orientations():
    pair = ("creative", "strict")
    mapping = {"A": "strict", "B": "creative"}  # position tirée par le plan
    forward = deblind("A", "forward", mapping)
    reverse = deblind("B", "reverse", mapping)
    assert forward == reverse == "strict"
    resolution = resolve_single_judge_pair(
        pair_position(forward, pair), pair_position(reverse, pair)
    )
    assert resolution == {"stable": True, "resolved": True, "winner": "B"}
    assert pair[1] == "strict"

    # Un juge qui suit la position et non le contenu ne résout rien.
    unstable = resolve_single_judge_pair(
        pair_position(deblind("A", "forward", mapping), pair),
        pair_position(deblind("A", "reverse", mapping), pair),
    )
    assert unstable["resolved"] is False
    with pytest.raises(ValueError, match="does not belong"):
        pair_position("focused", pair)


def test_pack_integrity_reports_deterministic_bytes_and_involutive_inversion():
    pack = _pack()
    report = pack_integrity(pack)
    assert report["ok"] is True
    assert report["sha256"] == pack_sha256(pack)
    assert report["bytes"] == len(canonical_json_bytes(pack))
    assert pack_integrity(invert_evidence_pack(pack))["ok"] is True


def test_pack_blindness_catches_a_policy_identifier_anywhere_in_the_pack():
    clean = pack_blindness(_pack(), forbidden=(*POLICY_IDENTIFIERS, "mistral:latest"))
    assert clean == {"forbidden_found": [], "labels_ok": True, "ok": True}

    leaking = _pack(marker_a=f"produced by the {ARM_ADAPTIVE} policy")
    report = pack_blindness(leaking, forbidden=(*POLICY_IDENTIFIERS, "mistral:latest"))
    assert report["forbidden_found"] == [ARM_ADAPTIVE]
    assert report["ok"] is False

    # Le nom du modèle producteur est tout aussi interdit que celui du bras.
    named = _pack(marker_b="answer generated with mistral:latest")
    assert pack_blindness(named, forbidden=("mistral:latest",))["ok"] is False


def test_objective_failure_covers_contract_and_truncation():
    assert objective_failure(_trace(ARM_STATIC, "ok"))["failed"] is False

    broken = objective_failure(_trace(ARM_STATIC, "ok", complete=False))
    assert broken["incomplete"] is True and broken["failed"] is True
    assert broken["contract_error"]

    truncated = objective_failure(_trace(ARM_STATIC, "ok", truncated=True))
    assert truncated["incomplete"] is False
    assert truncated["truncated"] is True and truncated["failed"] is True


def test_blind_mapping_is_sealed_sorted_and_unique():
    entries = [
        {"comparison_id": "m|c2|focused|strict", "candidate_a": "strict", "candidate_b": "focused"},
        {"comparison_id": "m|c1|creative|default", "candidate_a": "creative", "candidate_b": "default"},
    ]
    seal = seal_blind_mapping(entries, phase="calibration")
    assert seal["count"] == 2
    assert [row["comparison_id"] for row in seal["entries"]] == sorted(
        row["comparison_id"] for row in entries
    )
    assert len(seal["seal_sha256"]) == 64
    assert seal_blind_mapping(reversed(entries), phase="calibration") == seal

    with pytest.raises(ValueError, match="unique"):
        seal_blind_mapping([entries[0], entries[0]], phase="calibration")
