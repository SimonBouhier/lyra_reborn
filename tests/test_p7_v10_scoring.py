"""Offline checks for the V10 scorer — gates C0-C12 and frozen verdict order."""
from __future__ import annotations

import pytest

from eval.p7_v10_scoring import (
    EFFECT_GATE,
    JUDGE_GATES,
    OPERATIONAL_GATES,
    STRUCTURAL_GATES,
    arm_outcome,
    global_verdict,
    score_producer,
)


def _pair(index: int, *, winner: str = "ADAPTIVE") -> dict:
    return {
        "case_id": f"case-{index:02d}",
        "source": ("arxiv", "github", "hackernews")[index % 3],
        "order": "ABBA" if index < 30 else "BAAB",
        "producer_calls": 5,
        "complete": True,
        "common_t1_identical": True,
        "option_changed_t2_or_t3": True,
        "adaptive_objective_failure": False,
        "static_objective_failure": False,
        "adaptive_timeout_or_error": False,
        "static_timeout_or_error": False,
        "adaptive_tokens_t23": 400,
        "static_tokens_t23": 400,
        "adaptive_latencies_t23": [900.0, 950.0],
        "static_latencies_t23": [900.0, 950.0],
        "judged": True,
        "pack_blind_ok": True,
        "pack_integrity_ok": True,
        "judge": {
            "forward": {"valid": True, "arm": winner},
            "reverse": {"valid": True, "arm": winner},
        },
    }


def _producer(name: str = "mistral:latest", *, adaptive_wins: int = 45) -> dict:
    pairs = []
    for index in range(60):
        winner = "ADAPTIVE" if index < adaptive_wins else "STATIC_BEST"
        pairs.append(_pair(index, winner=winner))
    return {
        "producer": name,
        "seal": {
            "count": 60,
            "sealed_before_common_t1": True,
            "all_hashes_present": True,
        },
        "pairs": pairs,
    }


def test_arm_outcome_follows_the_frozen_resolution_rule():
    assert arm_outcome("ADAPTIVE", "ADAPTIVE")["winner"] == "ADAPTIVE"
    assert arm_outcome("TIE", "TIE") == {"stable": True, "resolved": False, "winner": None}
    assert arm_outcome("ADAPTIVE", "STATIC_BEST")["stable"] is False
    assert arm_outcome("INVALID", "INVALID")["stable"] is False


def test_perfect_producer_is_supported_with_exact_counters():
    result = score_producer(_producer())
    assert result["verdict"] == "H10_SUPPORTED_FOR_MODEL"
    assert (result["W"], result["L"], result["U"]) == (45, 15, 0)
    assert result["win_rate"] == 0.75
    assert result["wilson_low_95"] > 0.50
    assert result["net_advantage"] == 0.5
    assert all(result["gates"].values())
    assert "juge unique" in result["independence_note"]
    assert "instrument gele" in result["scope_note"]


def test_effect_gate_requires_wilson_low_and_net_advantage():
    # 34 W / 26 L : Wilson bas < 0,50 -> C5 échoue, tout le reste passe.
    result = score_producer(_producer(adaptive_wins=34))
    assert result["gates"]["C5"] is False
    assert result["verdict"] == "H10_NOT_SUPPORTED_FOR_MODEL"

    # 33 W / 27 L : NA = 0,10 tout juste, mais Wilson bas < 0,50.
    result = score_producer(_producer(adaptive_wins=33))
    assert result["net_advantage"] == pytest.approx(0.1)
    assert result["gates"]["C5"] is False

    # 41 W / 19 L : Wilson bas > 0,50 et NA > 0,10 -> soutenu.
    result = score_producer(_producer(adaptive_wins=41))
    assert result["gates"]["C5"] is True
    assert result["verdict"] == "H10_SUPPORTED_FOR_MODEL"


def test_structural_failure_dominates_and_gives_inconclusive():
    data = _producer()
    data["pairs"][0]["pack_integrity_ok"] = False  # C11
    data["pairs"][1]["option_changed_t2_or_t3"] = False  # affaiblit C2 sans la casser
    result = score_producer(data)
    assert result["gates"]["C11"] is False
    assert result["verdict"] == "H10_INCONCLUSIVE_FOR_MODEL"


def test_operational_failure_gives_not_supported_even_if_judge_undecided():
    data = _producer()
    for pair in data["pairs"]:
        pair["adaptive_tokens_t23"] = 600  # C7 : 1,5x les tokens statiques
        pair["judge"]["forward"]["arm"] = "TIE"  # et le juge devient indécis
        pair["judge"]["reverse"]["arm"] = "TIE"
    result = score_producer(data)
    assert result["gates"]["C7"] is False
    assert result["gates"]["C3"] is False
    # V8 : l'échec opérationnel prime « même si le panel est ensuite trop
    # indécis pour mesurer la qualité ».
    assert result["verdict"] == "H10_NOT_SUPPORTED_FOR_MODEL"


def test_judge_gates_failure_after_clean_operations_gives_inconclusive():
    data = _producer()
    for index, pair in enumerate(data["pairs"]):
        if index % 2 == 0:  # 50 % d'instabilité -> C4 < 75 %, C3 = 50 % tient
            pair["judge"]["reverse"]["arm"] = "STATIC_BEST"
    result = score_producer(data)
    assert result["gates"]["C4"] is False
    assert result["gates"]["C3"] is True
    assert result["verdict"] == "H10_INCONCLUSIVE_FOR_MODEL"


def test_c8_gap_and_c10_counterbalance():
    data = _producer()
    data["pairs"][0]["adaptive_timeout_or_error"] = True
    data["pairs"][1]["adaptive_timeout_or_error"] = True  # 2/60 vs 0/60 : écart > 2 pts
    result = score_producer(data)
    assert result["gates"]["C8"] is False

    data = _producer()
    data["pairs"][0]["order"] = "BAAB"  # 29/31
    assert score_producer(data)["gates"]["C10"] is False


def test_gate_partition_matches_the_frozen_verdict_logic():
    assert set(STRUCTURAL_GATES + OPERATIONAL_GATES + JUDGE_GATES + (EFFECT_GATE,)) == {
        f"C{i}" for i in range(13)
    }


def test_global_verdict_thresholds_and_untested_guard():
    supported = score_producer(_producer("mistral:latest"))
    not_supported = score_producer(_producer("gemma3:latest", adaptive_wins=34))

    verdict = global_verdict(
        [supported, supported | {"producer": "granite3.3:latest"}, not_supported],
        q0_passed=True,
        q1_passed=True,
    )
    assert verdict["status"] == "H10_SUPPORTED_IN_V10"

    verdict = global_verdict(
        [not_supported, not_supported | {"producer": "x"}, supported],
        q0_passed=True,
        q1_passed=True,
    )
    assert verdict["status"] == "H10_NOT_SUPPORTED_IN_V10"

    inconclusive = dict(supported, verdict="H10_INCONCLUSIVE_FOR_MODEL")
    verdict = global_verdict(
        [supported, inconclusive | {"producer": "y"}, not_supported],
        q0_passed=True,
        q1_passed=True,
    )
    assert verdict["status"] == "H10_INCONCLUSIVE_IN_V10"

    verdict = global_verdict([], q0_passed=False, q1_passed=True)
    assert verdict["status"] == "H10_UNTESTED_IN_V10"
    with pytest.raises(ValueError):
        global_verdict([supported], q0_passed=True, q1_passed=True)
