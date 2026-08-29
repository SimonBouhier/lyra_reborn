"""Calibration V10 — logique pure : plan des comparaisons, sélection, porte Q1.

Implémente PREREGISTRATION_v8.md §« Calibration et jeu tenu » (incorporé par
V10) : quatre presets statiques par cas et producteur, les six paires non
ordonnées jugées dans les deux ordres (72 comparaisons par producteur avant
inversion), STATIC_BEST par victoires résolues puis départages gelés, recalcul
sous trois retraits de source. Aucune E/S ici ; l'exécuteur fournit les
verdicts et les métriques de départage.

Formules propres à V10 (V8 est morte avant d'implémenter cette couche ; elles
sont déterministes, journalisées au manifeste et fixées ici) :
- graine producteur : sha256(seed \\0 case_id::preset \\0 model_digest \\0 turn),
  extension par le preset de la formule gelée de eval/p7_trajectory._seed ;
- bit de position A/B : sha256(seed \\0 calibration_pair \\0 case_id \\0 p1 \\0 p2)
  avec p1 < p2 lexical — bit pair : A = p1 ; bit impair : A = p2 ;
- ordre des comparaisons : tri croissant du même matériel.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Any, Iterable, Mapping

from core.knobs import Knobs
from core.control.reactive import apply_task_overrides
from eval.p7_v10_corpus import CORPUS_SEED

__all__ = [
    "PRESETS",
    "PRESET_PAIRS",
    "CALIBRATION_CASES",
    "CALIBRATION_COMPARISONS",
    "preset_knobs",
    "trajectory_seed",
    "PlannedComparison",
    "plan_comparisons",
    "select_static_best",
    "ablation_winners",
    "q1_gate",
]

PRESETS = ("default", "creative", "focused", "strict")
PRESET_PAIRS = tuple(
    (first, second)
    for index, first in enumerate(PRESETS)
    for second in PRESETS[index + 1 :]
)
CALIBRATION_CASES = 12
CALIBRATION_COMPARISONS = CALIBRATION_CASES * len(PRESET_PAIRS)  # 72 / producteur


def preset_knobs(name: str) -> Knobs:
    """`default` = les Knobs de base ; les autres = overrides gelés du canon."""
    if name == "default":
        return Knobs()
    if name not in PRESETS:
        raise ValueError(f"unknown preset: {name}")
    return apply_task_overrides(Knobs(), name)


def trajectory_seed(case_id: str, preset: str, model_digest: str, turn: int) -> int:
    material = f"{CORPUS_SEED}\0{case_id}::{preset}\0{model_digest}\0{turn}".encode("utf-8")
    return int(hashlib.sha256(material).hexdigest()[:8], 16) % 2_147_483_647


@dataclass(frozen=True)
class PlannedComparison:
    case_id: str
    source: str
    pair: tuple[str, str]  # ordre lexical
    candidate_a: str  # preset joué comme A dans l'orientation forward
    candidate_b: str


def _pair_material(case_id: str, pair: tuple[str, str]) -> str:
    return f"{CORPUS_SEED}\0calibration_pair\0{case_id}\0{pair[0]}\0{pair[1]}"


def plan_comparisons(cases: Iterable[tuple[str, str]]) -> tuple[PlannedComparison, ...]:
    """`cases` = (case_id, source). Retourne les 72 comparaisons ordonnées."""
    planned = []
    for case_id, source in cases:
        for pair in PRESET_PAIRS:
            digest = hashlib.sha256(_pair_material(case_id, pair).encode("utf-8")).hexdigest()
            swap = int(digest[-1], 16) % 2 == 1
            candidate_a, candidate_b = (pair[1], pair[0]) if swap else pair
            planned.append(
                PlannedComparison(
                    case_id=case_id,
                    source=source,
                    pair=pair,
                    candidate_a=candidate_a,
                    candidate_b=candidate_b,
                )
            )
    planned.sort(
        key=lambda item: hashlib.sha256(
            _pair_material(item.case_id, item.pair).encode("utf-8")
        ).hexdigest()
    )
    expected = len(list(planned))
    if expected and expected % len(PRESET_PAIRS) != 0:
        raise RuntimeError("comparison plan must cover every preset pair per case")
    return tuple(planned)


def _scores(
    outcomes: Iterable[Mapping[str, Any]],
) -> dict[str, dict[str, int]]:
    scores = {preset: {"wins": 0, "losses": 0} for preset in PRESETS}
    for outcome in outcomes:
        if not outcome.get("resolved"):
            continue
        winner = outcome["winner_preset"]
        first, second = outcome["pair"]
        loser = second if winner == first else first
        scores[winner]["wins"] += 1
        scores[loser]["losses"] += 1
    return scores


def select_static_best(
    outcomes: Iterable[Mapping[str, Any]],
    *,
    failure_rates: Mapping[str, float],
    output_tokens: Mapping[str, int],
) -> dict[str, Any]:
    """Score primaire = victoires résolues ; départages gelés V8 dans l'ordre :
    moins de défaites, plus faible taux d'échec objectif, moins de tokens de
    sortie, puis ordre lexical (journalisé — Q1 échoue s'il est nécessaire).
    """
    scores = _scores(outcomes)

    def sort_key(preset: str):
        return (
            -scores[preset]["wins"],
            scores[preset]["losses"],
            failure_rates[preset],
            output_tokens[preset],
            preset,
        )

    ranked = sorted(PRESETS, key=sort_key)
    winner, runner_up = ranked[0], ranked[1]
    lexical_needed = sort_key(winner)[:-1] == sort_key(runner_up)[:-1]
    return {
        "winner": winner,
        "ranking": ranked,
        "scores": scores,
        "failure_rates": dict(failure_rates),
        "output_tokens": dict(output_tokens),
        "lexical_tiebreak_needed": lexical_needed,
    }


def ablation_winners(
    outcomes: Iterable[Mapping[str, Any]],
    *,
    failure_rates: Mapping[str, float],
    output_tokens: Mapping[str, int],
) -> dict[str, str]:
    """Recalcule le gagnant en retirant successivement chaque source (V8 :
    mêmes règles ; les métriques de départage globales restent celles du
    calcul principal, seuls les verdicts de la source retirée sortent)."""
    materialized = list(outcomes)
    winners: dict[str, str] = {}
    for removed in ("arxiv", "github", "hackernews"):
        subset = [item for item in materialized if item["source"] != removed]
        winners[removed] = select_static_best(
            subset, failure_rates=failure_rates, output_tokens=output_tokens
        )["winner"]
    return winners


def q1_gate(
    outcomes: Iterable[Mapping[str, Any]],
    selection: Mapping[str, Any],
    ablations: Mapping[str, str],
) -> dict[str, Any]:
    """Q1 gelée : résolution >= 50 % des comparaisons complètes ; gagnant non
    dépendant du départage lexical ; même gagnant dans au moins deux des trois
    retraits de source."""
    materialized = list(outcomes)
    complete = [item for item in materialized if item.get("complete")]
    resolved = sum(bool(item.get("resolved")) for item in complete)
    resolution_rate = resolved / len(complete) if complete else 0.0
    agreement = sum(
        1 for winner in ablations.values() if winner == selection["winner"]
    )
    passed = (
        resolution_rate >= 0.5
        and not selection["lexical_tiebreak_needed"]
        and agreement >= 2
    )
    return {
        "complete_comparisons": len(complete),
        "resolved_comparisons": resolved,
        "resolution_rate": round(resolution_rate, 6),
        "lexical_tiebreak_needed": bool(selection["lexical_tiebreak_needed"]),
        "ablation_winners": dict(ablations),
        "ablation_agreement": agreement,
        "static_best": selection["winner"],
        "passed": passed,
    }
