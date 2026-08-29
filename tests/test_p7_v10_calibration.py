"""Offline checks for the V10 calibration pure logic."""
from __future__ import annotations

import pytest

from core.knobs import Knobs
from eval.p7_v10_calibration import (
    CALIBRATION_COMPARISONS,
    PRESET_PAIRS,
    PRESETS,
    ablation_winners,
    plan_comparisons,
    preset_knobs,
    q1_gate,
    select_static_best,
    trajectory_seed,
)

_CASES = [
    (f"{source}-case-{index}", source)
    for source in ("arxiv", "github", "hackernews")
    for index in range(1, 5)
]


def _outcome(case_id, source, pair, winner=None, *, resolved=None, complete=True):
    return {
        "case_id": case_id,
        "source": source,
        "pair": pair,
        "winner_preset": winner,
        "resolved": bool(winner) if resolved is None else resolved,
        "complete": complete,
    }


def _uniform_outcomes(winner: str):
    outcomes = []
    for case_id, source in _CASES:
        for pair in PRESET_PAIRS:
            outcomes.append(
                _outcome(case_id, source, pair, winner if winner in pair else pair[0])
            )
    return outcomes


_NO_TIE_METRICS = {
    "failure_rates": {"default": 0.0, "creative": 0.1, "focused": 0.2, "strict": 0.3},
    "output_tokens": {"default": 100, "creative": 200, "focused": 300, "strict": 400},
}


def test_presets_and_pairs_are_the_frozen_four():
    assert PRESETS == ("default", "creative", "focused", "strict")
    assert len(PRESET_PAIRS) == 6
    assert preset_knobs("default").as_dict() == Knobs().as_dict()
    assert preset_knobs("creative").as_dict() != Knobs().as_dict()
    with pytest.raises(ValueError):
        preset_knobs("adaptive")


def test_trajectory_seed_separates_presets_and_turns():
    base = trajectory_seed("case", "default", "digest", 1)
    assert trajectory_seed("case", "default", "digest", 1) == base  # déterminisme
    assert trajectory_seed("case", "creative", "digest", 1) != base
    assert trajectory_seed("case", "default", "digest", 2) != base
    assert 0 <= base < 2_147_483_647


def test_plan_covers_seventy_two_comparisons_with_both_positions():
    plan = plan_comparisons(_CASES)
    assert len(plan) == CALIBRATION_COMPARISONS == 72
    assert plan == plan_comparisons(_CASES)  # ordre déterministe
    for item in plan:
        assert {item.candidate_a, item.candidate_b} == set(item.pair)
    # Le bit de position doit produire les deux affectations sur l'ensemble.
    swapped = sum(1 for item in plan if (item.candidate_a, item.candidate_b) != item.pair)
    assert 0 < swapped < len(plan)


def test_selection_counts_resolved_wins_then_frozen_tiebreaks():
    selection = select_static_best(_uniform_outcomes("focused"), **_NO_TIE_METRICS)
    assert selection["winner"] == "focused"
    assert selection["lexical_tiebreak_needed"] is False
    assert selection["scores"]["focused"]["wins"] == 36  # 3 paires x 12 cas

    # Aucune victoire nulle part : tout se joue aux départages gelés.
    empty = [
        _outcome(case_id, source, pair, None, resolved=False)
        for case_id, source in _CASES
        for pair in PRESET_PAIRS
    ]
    selection = select_static_best(empty, **_NO_TIE_METRICS)
    assert selection["winner"] == "default"  # départage par taux d'échec puis tokens
    assert selection["lexical_tiebreak_needed"] is False

    flat = {
        "failure_rates": {preset: 0.0 for preset in PRESETS},
        "output_tokens": {preset: 100 for preset in PRESETS},
    }
    selection = select_static_best(empty, **flat)
    assert selection["lexical_tiebreak_needed"] is True
    assert selection["winner"] == "creative"  # ordre lexical, journalisé


def test_q1_gate_requires_resolution_stability_and_no_lexical():
    outcomes = _uniform_outcomes("strict")
    selection = select_static_best(outcomes, **_NO_TIE_METRICS)
    ablations = ablation_winners(outcomes, **_NO_TIE_METRICS)
    gate = q1_gate(outcomes, selection, ablations)
    assert gate["static_best"] == "strict"
    assert gate["ablation_agreement"] == 3
    assert gate["resolution_rate"] == 1.0
    assert gate["passed"] is True

    # Résolution insuffisante : moins de 50 % des comparaisons complètes.
    sparse = [
        {**item, "resolved": index % 3 == 0, "winner_preset": "strict" if index % 3 == 0 else None}
        for index, item in enumerate(_uniform_outcomes("strict"))
    ]
    for item in sparse:
        if item["resolved"] and "strict" not in item["pair"]:
            item["winner_preset"] = item["pair"][0]
    selection = select_static_best(sparse, **_NO_TIE_METRICS)
    gate = q1_gate(sparse, selection, ablation_winners(sparse, **_NO_TIE_METRICS))
    assert gate["resolution_rate"] < 0.5
    assert gate["passed"] is False

    # Désaccord d'ablation : le gagnant dépend d'une seule source.
    github_only = [
        _outcome(case_id, source, pair,
                 "strict" if source == "github" and "strict" in pair else None,
                 resolved=source == "github" and "strict" in pair)
        for case_id, source in _CASES
        for pair in PRESET_PAIRS
    ]
    selection = select_static_best(github_only, **_NO_TIE_METRICS)
    assert selection["winner"] == "strict"
    ablations = ablation_winners(github_only, **_NO_TIE_METRICS)
    assert ablations["github"] != "strict"
    gate = q1_gate(github_only, selection, ablations)
    assert gate["ablation_agreement"] == 2  # arxiv et hackernews retirés : strict tient
    assert gate["passed"] is False  # mais la résolution 12/72 < 50 % coupe
