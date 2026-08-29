"""Jeu tenu V10 — logique pure : contre-balancement, attribution, scellement.

Aucune E/S, aucun réseau. Ce module fixe ce que l'exécuteur du tenu doit
calculer avant et après `eval.p7_trajectory.run_policy_pair`, et il assemble
EXACTEMENT le schéma d'entrée documenté par
`eval.p7_v10_scoring.score_producer` — ce schéma est le contrat, il n'est pas
renégocié ici.

Formules :

- **contre-balancement** (gelé V8, §« Calibration et jeu tenu ») : tri croissant
  de `sha256(seed || "execution_order" || model_digest || case_id)`, première
  moitié `ABBA`, seconde `BAAB`, soit exactement 30/30 par producteur ;
- **position A/B de la paire** (propre à V10 ; V8 est morte avant d'implémenter
  cette couche) : `sha256(seed || "heldout_pair" || model_digest || case_id)`,
  dernier chiffre hexadécimal pair -> `ADAPTIVE` joue `A`, impair -> `STATIC_BEST`
  joue `A`. Déterministe, salée par producteur, journalisée au manifeste et
  scellée hors du pack. Elle n'est pas porteuse scientifiquement — les deux
  orientations sont jugées et la résolution exige la stabilité après inversion —
  mais elle doit être fixée et vérifiable ;
- **attribution des cinq appels** : `run_policy_pair` émet COMMON T1 puis les
  branches dans l'ordre d'exécution ; la table ci-dessous transcrit cet ordre
  gelé, et chaque appel attribué est revérifié contre les options de la trace.
"""
from __future__ import annotations

import hashlib
from typing import Any, Iterable, Mapping, Sequence

from eval.p7_trajectory import (
    ARM_ADAPTIVE,
    ARM_STATIC,
    ORDER_ABBA,
    ORDER_BAAB,
    EvaluationCase,
    PolicyPair,
)
from eval.p7_v10_execution import objective_failure
from eval.p7_v7_q0 import GLOBAL_SEED

__all__ = [
    "HELDOUT_CASES",
    "PRODUCER_CALLS_PER_CASE",
    "CALL_SLOTS",
    "assign_execution_orders",
    "first_arm",
    "attribute_pair_calls",
    "pair_record",
    "producer_scoring_input",
]

HELDOUT_CASES = 60
PRODUCER_CALLS_PER_CASE = 5
COMMON_SLOT = ("COMMON", 1)

# Ordre d'émission gelé de `run_policy_pair` : COMMON T1, puis T2 et T3 dans
# l'ordre du contre-balancement (ABBA : A puis B au tour 2, B puis A au tour 3).
CALL_SLOTS: dict[str, tuple[tuple[str, int], ...]] = {
    ORDER_ABBA: (
        COMMON_SLOT,
        (ARM_ADAPTIVE, 2),
        (ARM_STATIC, 2),
        (ARM_STATIC, 3),
        (ARM_ADAPTIVE, 3),
    ),
    ORDER_BAAB: (
        COMMON_SLOT,
        (ARM_STATIC, 2),
        (ARM_ADAPTIVE, 2),
        (ARM_ADAPTIVE, 3),
        (ARM_STATIC, 3),
    ),
}


def _rank(material: str) -> str:
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def assign_execution_orders(
    case_ids: Iterable[str], model_digest: str, *, seed: int = GLOBAL_SEED
) -> dict[str, str]:
    """Contre-balancement gelé V8 : exactement la moitié ABBA, la moitié BAAB."""
    identifiers = list(case_ids)
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("held-out case identifiers must be unique")
    if len(identifiers) % 2:
        raise ValueError("counterbalancing requires an even number of cases")
    ranked = sorted(
        identifiers,
        key=lambda case_id: _rank(
            f"{seed}\0execution_order\0{model_digest}\0{case_id}"
        ),
    )
    half = len(ranked) // 2
    return {
        case_id: (ORDER_ABBA if index < half else ORDER_BAAB)
        for index, case_id in enumerate(ranked)
    }


def first_arm(case_id: str, model_digest: str, *, seed: int = GLOBAL_SEED) -> str:
    """Bras placé en `A` dans l'orientation aller — mapping scellé à part."""
    digest = _rank(f"{seed}\0heldout_pair\0{model_digest}\0{case_id}")
    return ARM_ADAPTIVE if int(digest[-1], 16) % 2 == 0 else ARM_STATIC


def attribute_pair_calls(
    calls: Sequence[Any], pair: PolicyPair
) -> dict[tuple[str, int], Any]:
    """Rattache les cinq appels physiques aux (bras, tour) de la paire.

    L'ordre est celui, gelé, de `run_policy_pair` ; l'attribution est ensuite
    confrontée aux options réellement tracées. Un désaccord signalerait que la
    trajectoire gelée a changé sous le runner : on lève plutôt que d'attribuer
    des mesures de coût au mauvais bras.
    """
    slots = CALL_SLOTS.get(pair.execution_order)
    if slots is None:
        raise ValueError(f"unknown execution order: {pair.execution_order}")
    if len(calls) != PRODUCER_CALLS_PER_CASE:
        raise ValueError(
            f"a policy pair must emit {PRODUCER_CALLS_PER_CASE} producer calls, "
            f"got {len(calls)}"
        )
    traces = {ARM_ADAPTIVE: pair.adaptive, ARM_STATIC: pair.static}
    attributed: dict[tuple[str, int], Any] = {}
    for slot, call in zip(slots, calls):
        arm, turn = slot
        expected = (
            [traces[ARM_ADAPTIVE].turns[0].options, traces[ARM_STATIC].turns[0].options]
            if arm == "COMMON"
            else [traces[arm].turns[turn - 1].options]
        )
        if all(call.options != options for options in expected):
            raise ValueError(
                f"call {call.index} does not match the frozen slot {arm}.T{turn}"
            )
        attributed[slot] = call
    return attributed


def _arm_calls(attributed: Mapping[tuple[str, int], Any], arm: str) -> list[Any]:
    return [attributed[(arm, turn)] for turn in (2, 3)]


def pair_record(
    *,
    case: EvaluationCase,
    pair: PolicyPair,
    attributed: Mapping[tuple[str, int], Any],
    judged: bool = False,
    judge: Mapping[str, Any] | None = None,
    pack_blind_ok: bool = False,
    pack_integrity_ok: bool = False,
    pack_error: str | None = None,
) -> dict[str, Any]:
    """Un élément de `pairs` au schéma exact de `score_producer`."""
    adaptive_t1, static_t1 = pair.adaptive.turns[0], pair.static.turns[0]
    common_identical = (
        adaptive_t1.prompt == static_t1.prompt
        and adaptive_t1.options == static_t1.options
        and adaptive_t1.output == static_t1.output
        and _rank(adaptive_t1.output) == _rank(static_t1.output)
    )
    option_changed = any(
        pair.adaptive.turns[index].options != pair.static.turns[index].options
        for index in (1, 2)
        if index < len(pair.adaptive.turns) and index < len(pair.static.turns)
    )
    common_call = attributed[COMMON_SLOT]
    adaptive_calls = _arm_calls(attributed, ARM_ADAPTIVE)
    static_calls = _arm_calls(attributed, ARM_STATIC)
    adaptive_failure = objective_failure(pair.adaptive)
    static_failure = objective_failure(pair.static)
    record = {
        "case_id": case.case_id,
        "source": case.source_name,
        "order": pair.execution_order,
        "producer_calls": len(attributed),
        "complete": pair.adaptive.complete and pair.static.complete,
        "common_t1_identical": common_identical,
        "option_changed_t2_or_t3": option_changed,
        "adaptive_objective_failure": adaptive_failure["failed"],
        "static_objective_failure": static_failure["failed"],
        # Un échec du tour commun casse les deux bras : il est compté des deux
        # côtés, ce qui laisse l'écart de C8 inchangé au lieu de le creuser.
        "adaptive_timeout_or_error": common_call.failed
        or any(call.failed for call in adaptive_calls),
        "static_timeout_or_error": common_call.failed
        or any(call.failed for call in static_calls),
        "adaptive_tokens_t23": sum(call.output_tokens for call in adaptive_calls),
        "static_tokens_t23": sum(call.output_tokens for call in static_calls),
        "adaptive_latencies_t23": [call.elapsed_ms for call in adaptive_calls],
        "static_latencies_t23": [call.elapsed_ms for call in static_calls],
        "judged": bool(judged),
        "pack_blind_ok": bool(pack_blind_ok),
        "pack_integrity_ok": bool(pack_integrity_ok),
        "objective_failure_detail": {
            "adaptive": adaptive_failure,
            "static": static_failure,
        },
        "pack_error": pack_error,
    }
    if judged:
        if judge is None:
            raise ValueError("a judged pair must carry its two judge answers")
        record["judge"] = dict(judge)
    return record


def producer_scoring_input(
    *,
    producer: str,
    seal: Mapping[str, Any],
    sealed_before_common_t1: bool,
    pairs: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Entrée complète d'un producteur pour `score_producer`, C0 comprise."""
    entries = seal.get("cases", [])
    all_hashes_present = bool(entries) and all(
        isinstance(entry.get("content_sha256"), str)
        and len(entry["content_sha256"]) == 64
        for entry in entries
    )
    return {
        "producer": producer,
        "seal": {
            "count": seal.get("count"),
            "sealed_before_common_t1": bool(sealed_before_common_t1),
            "all_hashes_present": all_hashes_present,
        },
        "pairs": list(pairs),
    }
