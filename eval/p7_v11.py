"""Noyau pur de la campagne V11 — juge unique sous contrat réduit.

Toutes les constantes reproduisent `PREREGISTRATION_v11.md` ; le design est
celui de V10/V8 incorporé, seul le runtime change (V10 arrêtée sur dérive
d'Ollama, cf. docs/P7_V10_STATUS.md).
les briques gelées (contrat réduit, fixtures Q0, packs) sont consommées sans
modification. Aucune E/S ici : le runner `scripts/p7_v11.py` orchestre.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Any, Literal

from eval.p7_evidence import EvidencePack, canonical_json_bytes, pack_sha256
from eval.p7_judge_backend import JudgeBackendRequest
from eval.p7_v10_q1 import (
    JUDGES as _Q1_JUDGES,
    compact_judge_prompt,
    compact_judgment_schema,
    validate_compact_judgment,
    verify_judge_fully_loaded_on_gpu,
)
from eval.p7_v7_q0 import GLOBAL_SEED, Q0Orientation, fixture_orientations, q0_fixtures

__all__ = [
    "PREREGISTRATION",
    "PREREG_FREEZE_COMMIT",
    "PRERUN_AMENDMENT",
    "PRODUCER_CONTEXT_AMENDMENT",
    "PREDECESSOR_STATUS",
    "INDEPENDENCE_NOTE",
    "JUDGE",
    "MAX_TOKENS",
    "CONTEXT_TOKENS",
    "Q0_REPETITIONS",
    "Q0_EXPECTED_CALLS",
    "CALL_CEILINGS",
    "REQUIRED_PHASES",
    "Q0Job",
    "judge_request",
    "q0_orientations",
    "q0_jobs",
    "logical_preference",
    "evaluate_q0_records",
    "resolve_single_judge_pair",
    "verify_judge_identity",
    "verify_judge_gpu",
    "validate_compact_judgment",
]

PREREGISTRATION = "PREREGISTRATION_v11.md"

# Renseigné par le commit d'estampille, jamais à la main avant le gel : la
# garde de `scripts/p7_v11.py` refuse tout run tant que ce littéral est présent.
PREREG_FREEZE_COMMIT = "TO_BE_STAMPED"

# Amendements incorporés au gel V11 (prérég §Incorporation).
PRERUN_AMENDMENT = "docs/P7_V10_PRERUN_AMENDMENT.md"
PRODUCER_CONTEXT_AMENDMENT = "docs/P7_V10_PRODUCER_CONTEXT_AMENDMENT.md"
PREDECESSOR_STATUS = "docs/P7_V10_STATUS.md"
INDEPENDENCE_NOTE = "juge unique - independance inter-famille non disponible"

# Le juge unique est l'artefact qwen3.8 gelé par Q-1, référencé sans copie.
JUDGE = next(judge for judge in _Q1_JUDGES if judge.model == "qwen3.8:27b")
if JUDGE.digest != "22130167c4c20e20c7b71454612966ca8e8171e9b3cc8ab6ce8aa6cbfec79643":
    raise RuntimeError("frozen judge digest drifted from the Q-1 artifact")

MAX_TOKENS = 512
CONTEXT_TOKENS = 32768
Q0_REPETITIONS = 3
Q0_EXPECTED_CALLS = 18

# Plafonds gelés (prérég §Données et budget) — contrôles, pas des quotas.
CALL_CEILINGS = {
    "q0_judge": 18,
    "calibration_producer": 432,
    "calibration_judge": 432,
    "heldout_producer": 900,
    "heldout_judge": 360,
    "total": 2142,
}

# La commande unique doit implémenter toute la chaîne avant tout run vivant.
REQUIRED_PHASES = ("Q0", "CALIBRATION", "HELDOUT", "SCORING")


@dataclass(frozen=True)
class Q0Job:
    orientation: Q0Orientation
    repetition: int


def judge_request(pack: EvidencePack) -> JudgeBackendRequest:
    """Requête octet-identique à celle du runner Q-1 (scripts/p7_v10_q1.py)."""
    schema = compact_judgment_schema(pack)
    return JudgeBackendRequest(
        model=JUDGE.model,
        prompt=compact_judge_prompt(pack),
        full_schema=schema,
        wire_schema=schema,
        max_tokens=MAX_TOKENS,
        context_tokens=CONTEXT_TOKENS,
    )


def q0_orientations() -> tuple[Q0Orientation, ...]:
    items = tuple(
        oriented for fixture in q0_fixtures() for oriented in fixture_orientations(fixture)
    )
    if len(items) != 6:
        raise RuntimeError("Q0 must contain exactly six oriented packs")
    return items


def _q0_sort_key(job: Q0Job) -> str:
    # Formule de la prérég (§Instrument.4) étendue de la répétition pour Q0.
    material = (
        f"{GLOBAL_SEED}\0judge_order\0{JUDGE.digest}\0"
        f"{pack_sha256(job.orientation.pack)}\0{job.orientation.orientation}\0"
        f"{job.repetition}"
    ).encode("utf-8")
    return hashlib.sha256(material).hexdigest()


def q0_jobs() -> tuple[Q0Job, ...]:
    jobs = [
        Q0Job(orientation, repetition)
        for orientation in q0_orientations()
        for repetition in range(1, Q0_REPETITIONS + 1)
    ]
    jobs.sort(key=_q0_sort_key)
    if len(jobs) != Q0_EXPECTED_CALLS:
        raise RuntimeError("Q0 matrix differs from the frozen 3 x 2 x 3 design")
    return tuple(jobs)


def logical_preference(preference: str, mapping: dict[str, str]) -> str:
    """Ramène une préférence A/B/TIE de l'espace des labels à l'espace logique."""
    if preference == "TIE":
        return "TIE"
    return mapping[preference]


def evaluate_q0_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Verdict Q0 gelé : 18 appels, cellules unanimes, invariance logique.

    Chaque record doit porter : fixture_id, orientation, repetition, valid,
    wire_clean, observed_preference, expected_preference, observed_logical.
    """
    cells: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for record in records:
        cells.setdefault((record["fixture_id"], record["orientation"]), []).append(record)

    cell_results: dict[str, dict[str, Any]] = {}
    for orientation in q0_orientations():
        key = (orientation.fixture_id, orientation.orientation)
        selected = cells.get(key, [])
        cell_results[f"{key[0]}:{key[1]}"] = {
            "expected_preference": orientation.expected_preference,
            "calls": len(selected),
            "valid": sum(bool(item["valid"]) for item in selected),
            "wire_clean": sum(bool(item["wire_clean"]) for item in selected),
            "unanimous_expected": (
                len(selected) == Q0_REPETITIONS
                and all(
                    item["valid"]
                    and item["wire_clean"]
                    and item["observed_preference"] == orientation.expected_preference
                    for item in selected
                )
            ),
        }

    fixture_invariance: dict[str, bool] = {}
    by_fixture: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        by_fixture.setdefault(record["fixture_id"], []).append(record)
    for fixture_id, selected in sorted(by_fixture.items()):
        logicals = {item["observed_logical"] for item in selected}
        fixture_invariance[fixture_id] = (
            all(item["valid"] for item in selected) and len(logicals) == 1
        )

    passed = (
        len(records) == Q0_EXPECTED_CALLS
        and len(cells) == 6
        and all(item["unanimous_expected"] for item in cell_results.values())
        and len(fixture_invariance) == 3
        and all(fixture_invariance.values())
    )
    return {
        "calls_planned": Q0_EXPECTED_CALLS,
        "calls_recorded": len(records),
        "cell_results": cell_results,
        "fixture_logical_invariance": fixture_invariance,
        "passed": passed,
        "status": "Q0_PASSED" if passed else "V10_ABORTED_BEFORE_CALIBRATION",
    }


def resolve_single_judge_pair(
    forward_logical: Literal["A", "B", "TIE", "INVALID"],
    reverse_logical: Literal["A", "B", "TIE", "INVALID"],
) -> dict[str, Any]:
    """Règle gelée : résolu = stable après inversion ET non-TIE.

    Les préférences arrivent déjà ramenées à l'espace logique (désinversées).
    Un appel INVALID ne peut ni stabiliser ni résoudre.
    """
    stable = (
        forward_logical == reverse_logical
        and forward_logical in {"A", "B", "TIE"}
    )
    resolved = stable and forward_logical != "TIE"
    return {
        "stable": stable,
        "resolved": resolved,
        "winner": forward_logical if resolved else None,
    }


def verify_judge_identity(runtime: dict[str, Any]) -> None:
    observed = runtime.get("models", {}).get(JUDGE.model)
    if observed != JUDGE.digest:
        raise RuntimeError(
            f"judge digest mismatch: expected {JUDGE.digest}, observed {observed}"
        )


def verify_judge_gpu(runtime: dict[str, Any]) -> None:
    verify_judge_fully_loaded_on_gpu(runtime, JUDGE)


def q0_preflight() -> None:
    """Vérifications déterministes sans réseau — jamais après un verrou."""
    for job in q0_jobs():
        raw = canonical_json_bytes(job.orientation.pack)
        if raw != canonical_json_bytes(EvidencePack.model_validate_json(raw)):
            raise RuntimeError(
                f"non-deterministic pack: {job.orientation.fixture_id}"
                f":{job.orientation.orientation}"
            )
        raw.decode("ascii")
        compact_judge_prompt(job.orientation.pack).encode("ascii")
