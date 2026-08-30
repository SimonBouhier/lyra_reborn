"""Scoreur V10 — portes C0–C12 transposées juge unique, verdicts H10.

Transcription de PREREGISTRATION_v8.md §« Falsification thresholds » et
§« Verdict logic » (incorporés par V10, gel bc8497f), avec la seule
transposition gelée par PREREGISTRATION_v10.md : partout où V8 exige l'accord
du panel de deux juges, V10 exige la même propriété du juge unique sur ses
deux orientations. Les juges préfèrent localement ; ce scoreur déterministe
agrège seul et produit seul le verdict scientifique.

Entrée : un dict par producteur, assemblé par l'exécuteur (couches 3b/4) —
schéma documenté sur `score_producer`. Aucune E/S ici.

Conventions d'agrégation C7 (V8 dit « médiane tokens » et « p95 latence »
sans fixer le grain ; fixé ici, journalisé) : tokens = somme T2+T3 par cas et
par bras, médiane sur les cas complets ; latence = échantillons individuels
des appels T2 et T3 du bras, p95 nearest-rank sur les cas complets.
"""
from __future__ import annotations

from statistics import median
from typing import Any, Iterable, Mapping

from agency.tools.vigie.campaign import nearest_rank, wilson_interval
from eval.p7_v11 import INDEPENDENCE_NOTE

__all__ = [
    "SCOPE_NOTE",
    "STRUCTURAL_GATES",
    "OPERATIONAL_GATES",
    "JUDGE_GATES",
    "EFFECT_GATE",
    "arm_outcome",
    "score_producer",
    "global_verdict",
]

# Portée liée par docs/P7_V10_PRERUN_AMENDMENT.md — reprise sur chaque verdict.
SCOPE_NOTE = (
    "avantage mesure selon cet instrument gele (juge unique qualifie, contrat "
    "reduit, portes C0-C12) - aucune revendication de qualite editoriale "
    "objective ni de preference humaine"
)

STRUCTURAL_GATES = ("C0", "C1", "C9", "C10", "C11", "C12")
OPERATIONAL_GATES = ("C2", "C6", "C7", "C8")
JUDGE_GATES = ("C3", "C4")
EFFECT_GATE = "C5"

HELDOUT_CASES = 60
PRODUCER_CALLS_PER_CASE = 5


def arm_outcome(
    forward_arm: str,
    reverse_arm: str,
) -> dict[str, Any]:
    """Résolution juge unique dans l'espace des bras (après dé-inversion et
    dé-aveuglement par le mapping scellé) : ADAPTIVE / STATIC_BEST / TIE /
    INVALID. Résolu = stable ET non-TIE (transposition gelée de O9)."""
    stable = (
        forward_arm == reverse_arm
        and forward_arm in {"ADAPTIVE", "STATIC_BEST", "TIE"}
    )
    resolved = stable and forward_arm != "TIE"
    return {
        "stable": stable,
        "resolved": resolved,
        "winner": forward_arm if resolved else None,
    }


def _ratio_ok(adaptive: float, static: float, limit: float) -> bool:
    if static <= 0:
        return adaptive <= 0
    return adaptive <= limit * static


def _rate(count: int, total: int) -> float:
    return count / total if total else 0.0


def score_producer(data: Mapping[str, Any]) -> dict[str, Any]:
    """Calcule O1–O3, les portes C0–C12 et le verdict H10 d'un producteur.

    Schéma d'entrée (assemblé par l'exécuteur, un élément de `pairs` par cas
    tenu, exactement 60) :

    - `producer` : nom du modèle producteur ;
    - `seal` : `{count, sealed_before_common_t1, all_hashes_present}` (C0) ;
    - `pairs[i]` :
      - `case_id`, `source` ;
      - `order` : "ABBA" | "BAAB" (C10) ;
      - `producer_calls` : appels producteur réellement émis pour le cas ;
      - `complete` : les deux traces ont 3 tours et une décision valide ;
      - `common_t1_identical` : prompt/options/graine/sortie/SHA T1 (C1) ;
      - `option_changed_t2_or_t3` : au moins une option diffère (C2) ;
      - `adaptive_objective_failure`, `static_objective_failure` : échec
        objectif du bras sur ce cas — trace incomplète, JSON/schéma, décision,
        champ vide, ancre absente ou dépassement (O4 → C6) ;
      - `adaptive_timeout_or_error`, `static_timeout_or_error` (C8) ;
      - `adaptive_tokens_t23`, `static_tokens_t23` : somme des tokens de
        sortie T2+T3 du bras (cas complets, C7) ;
      - `adaptive_latencies_t23`, `static_latencies_t23` : latences ms des
        appels T2 et T3 du bras (C7) ;
      - `judged` : pack envoyé (uniquement si `complete`) ;
      - `pack_blind_ok` (C9), `pack_integrity_ok` (C11) — pour les packs
        envoyés ;
      - `judge` (si `judged`) : `{"forward": {"valid": bool, "arm": …},
        "reverse": {"valid": bool, "arm": …}}` où `arm` est la préférence
        dans l'espace des bras après dé-inversion, ou "INVALID".
    """
    pairs = list(data["pairs"])
    seal = data["seal"]
    complete = [pair for pair in pairs if pair["complete"]]
    judged = [pair for pair in pairs if pair.get("judged")]

    # O1 — W, L, U : une paire non complète ou non résolue donne U.
    wins = losses = 0
    resolved_cases = 0
    stable_denominator = 0  # comparaisons où les deux réponses sont valides
    stable_count = 0
    valid_judge_calls = 0
    for pair in judged:
        forward = pair["judge"]["forward"]
        reverse = pair["judge"]["reverse"]
        valid_judge_calls += int(forward["valid"]) + int(reverse["valid"])
        outcome = arm_outcome(forward["arm"], reverse["arm"])
        if outcome["resolved"]:
            resolved_cases += 1
            if outcome["winner"] == "ADAPTIVE":
                wins += 1
            else:
                losses += 1
        if forward["valid"] and reverse["valid"]:
            stable_denominator += 1
            if forward["arm"] == reverse["arm"]:
                stable_count += 1
    undecided = HELDOUT_CASES - wins - losses

    # O2/O3 — WR, Wilson bilatéral 95 %, NA.
    decided = wins + losses
    win_rate = wins / decided if decided else None
    wilson_low = wilson_interval(wins, decided)[0] if decided else None
    net_advantage = (wins - losses) / HELDOUT_CASES

    gates: dict[str, bool] = {}
    gates["C0"] = bool(
        seal["count"] == HELDOUT_CASES
        and seal["sealed_before_common_t1"]
        and seal["all_hashes_present"]
    )
    gates["C1"] = (
        len(pairs) == HELDOUT_CASES
        and all(pair["common_t1_identical"] for pair in pairs)
    )
    gates["C2"] = bool(complete) and _rate(
        sum(bool(pair["option_changed_t2_or_t3"]) for pair in complete),
        len(complete),
    ) >= 0.90
    gates["C3"] = resolved_cases / HELDOUT_CASES >= 0.50
    gates["C4"] = stable_denominator > 0 and (
        stable_count / stable_denominator >= 0.75
    )
    gates["C5"] = (
        decided > 0
        and wilson_low is not None
        and wilson_low > 0.50
        and net_advantage >= 0.10
    )

    adaptive_failure = _rate(
        sum(bool(pair["adaptive_objective_failure"]) for pair in pairs), len(pairs)
    )
    static_failure = _rate(
        sum(bool(pair["static_objective_failure"]) for pair in pairs), len(pairs)
    )
    gates["C6"] = adaptive_failure <= 0.10 and adaptive_failure <= static_failure + 0.05

    if complete:
        adaptive_tokens = median(pair["adaptive_tokens_t23"] for pair in complete)
        static_tokens = median(pair["static_tokens_t23"] for pair in complete)
        adaptive_latencies = [
            value for pair in complete for value in pair["adaptive_latencies_t23"]
        ]
        static_latencies = [
            value for pair in complete for value in pair["static_latencies_t23"]
        ]
        adaptive_p95 = nearest_rank(adaptive_latencies, 0.95)
        static_p95 = nearest_rank(static_latencies, 0.95)
        gates["C7"] = _ratio_ok(adaptive_tokens, static_tokens, 1.10) and _ratio_ok(
            adaptive_p95, static_p95, 1.25
        )
    else:
        adaptive_tokens = static_tokens = adaptive_p95 = static_p95 = None
        gates["C7"] = False

    adaptive_errors = _rate(
        sum(bool(pair["adaptive_timeout_or_error"]) for pair in pairs), len(pairs)
    )
    static_errors = _rate(
        sum(bool(pair["static_timeout_or_error"]) for pair in pairs), len(pairs)
    )
    gates["C8"] = (
        adaptive_errors <= 0.05
        and static_errors <= 0.05
        and abs(adaptive_errors - static_errors) <= 0.02
    )

    gates["C9"] = bool(judged) and all(pair["pack_blind_ok"] for pair in judged)
    orders = [pair["order"] for pair in pairs]
    gates["C10"] = (
        orders.count("ABBA") == 30
        and orders.count("BAAB") == 30
        and all(
            pair["producer_calls"] == PRODUCER_CALLS_PER_CASE
            for pair in complete
        )
    )
    gates["C11"] = bool(judged) and all(pair["pack_integrity_ok"] for pair in judged)
    planned_judge_calls = 2 * len(judged)
    gates["C12"] = planned_judge_calls > 0 and (
        valid_judge_calls / planned_judge_calls >= 0.95
    )

    # Verdict par producteur — ordre gelé V8.
    if not all(gates[name] for name in STRUCTURAL_GATES):
        verdict = "H10_INCONCLUSIVE_FOR_MODEL"
    elif not all(gates[name] for name in OPERATIONAL_GATES):
        verdict = "H10_NOT_SUPPORTED_FOR_MODEL"
    elif not all(gates[name] for name in JUDGE_GATES):
        verdict = "H10_INCONCLUSIVE_FOR_MODEL"
    elif gates[EFFECT_GATE]:
        verdict = "H10_SUPPORTED_FOR_MODEL"
    else:
        verdict = "H10_NOT_SUPPORTED_FOR_MODEL"

    return {
        "producer": data["producer"],
        "W": wins,
        "L": losses,
        "U": undecided,
        "win_rate": win_rate,
        "wilson_low_95": wilson_low,
        "net_advantage": round(net_advantage, 6),
        "resolved_cases": resolved_cases,
        "judge_stability": {
            "stable": stable_count,
            "denominator": stable_denominator,
        },
        "objective_failure_rates": {
            "adaptive": round(adaptive_failure, 6),
            "static": round(static_failure, 6),
        },
        "cost": {
            "median_tokens_t23": {"adaptive": adaptive_tokens, "static": static_tokens},
            "p95_latency_ms_t23": {"adaptive": adaptive_p95, "static": static_p95},
        },
        "gates": gates,
        "verdict": verdict,
        "independence_note": INDEPENDENCE_NOTE,
        "scope_note": SCOPE_NOTE,
    }


def global_verdict(
    producer_results: Iterable[Mapping[str, Any]],
    *,
    q0_passed: bool,
    q1_passed: bool,
) -> dict[str, Any]:
    """Verdict global gelé : N = 3 producteurs, seuil M = 2. Q0 et Q1 sont
    des portes globales préalables — leur échec laisse H10 UNTESTED."""
    results = list(producer_results)
    if not q0_passed or not q1_passed:
        status = "H10_UNTESTED_IN_V10"
    else:
        if len(results) != 3:
            raise ValueError("the frozen design evaluates exactly three producers")
        supported = sum(
            1 for item in results if item["verdict"] == "H10_SUPPORTED_FOR_MODEL"
        )
        not_supported = sum(
            1 for item in results if item["verdict"] == "H10_NOT_SUPPORTED_FOR_MODEL"
        )
        if supported >= 2:
            status = "H10_SUPPORTED_IN_V10"
        elif not_supported >= 2:
            status = "H10_NOT_SUPPORTED_IN_V10"
        else:
            status = "H10_INCONCLUSIVE_IN_V10"
    return {
        "status": status,
        "q0_passed": bool(q0_passed),
        "q1_passed": bool(q1_passed),
        "per_producer": {item["producer"]: item["verdict"] for item in results},
        "independence_note": INDEPENDENCE_NOTE,
        "scope_note": SCOPE_NOTE,
    }
