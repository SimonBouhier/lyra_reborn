"""Logique pure partagée par les deux exécuteurs V10 (calibration et tenu).

Ce module ne fait aucune E/S et ne connaît ni corpus ni transport. Il porte
les règles que la calibration et le jeu tenu appliquent à l'identique :

- l'ordre gelé des appels juge (prérég v10 §Instrument.4, mot pour mot) ;
- la construction du matériel de pack à partir d'une trajectoire complète ;
- le dé-aveuglement d'une préférence `A`/`B` selon l'orientation du pack et le
  mapping scellé À PART (jamais dans le pack — C9) ;
- les contrôles d'intégrité (C11) et d'aveuglement (C9) d'un pack ;
- la lecture de l'échec objectif d'une trajectoire (O4 → C6) ;
- le scellement du mapping candidat -> politique, hashé avant tout jugement.

Les règles de résolution restent celles des modules gelés : la calibration
passe par `eval.p7_v10.resolve_single_judge_pair` (espace `A`/`B` de la paire
lexicale), le tenu par `eval.p7_v10_scoring.arm_outcome` (espace des bras).
Aucune troisième copie de la règle n'est écrite ici.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Iterable, Literal, Mapping, Sequence

from eval.p7_evidence import (
    CandidateMaterial,
    EvidencePack,
    canonical_json_bytes,
    invert_evidence_pack,
    sha256_bytes,
)
from eval.p7_trajectory import ARM_ADAPTIVE, ARM_STATIC, PolicyTrace
from eval.p7_v10 import JUDGE
from eval.p7_v7_q0 import GLOBAL_SEED

__all__ = [
    "ORIENTATIONS",
    "POLICY_IDENTIFIERS",
    "JudgeCall",
    "judge_call_sort_key",
    "order_judge_calls",
    "candidate_material",
    "deblind",
    "pair_position",
    "pack_integrity",
    "pack_blindness",
    "objective_failure",
    "seal_blind_mapping",
]

ORIENTATIONS: tuple[str, ...] = ("forward", "reverse")

# Identifiants de politique qui ne doivent jamais atteindre le juge.
POLICY_IDENTIFIERS: tuple[str, ...] = (ARM_ADAPTIVE, ARM_STATIC)


def judge_call_sort_key(pack_sha256: str, orientation: str) -> str:
    """`sha256(seed || "judge_order" || judge_digest || pack_sha256 || orientation)`.

    Formule gelée de la prérég v10 §Instrument.4. Q0 y ajoute la répétition
    (`eval.p7_v10._q0_sort_key`) ; calibration et tenu n'en ont pas.
    """
    if orientation not in ORIENTATIONS:
        raise ValueError(f"unknown orientation: {orientation}")
    material = (
        f"{GLOBAL_SEED}\0judge_order\0{JUDGE.digest}\0{pack_sha256}\0{orientation}"
    ).encode("utf-8")
    return hashlib.sha256(material).hexdigest()


@dataclass(frozen=True)
class JudgeCall:
    """Un appel juge planifié : un pack, une orientation, une identité de paire."""

    comparison_id: str
    orientation: Literal["forward", "reverse"]
    pack: EvidencePack
    pack_sha256: str
    context: Mapping[str, Any]

    @property
    def sort_key(self) -> str:
        return judge_call_sort_key(self.pack_sha256, self.orientation)


def order_judge_calls(calls: Iterable[JudgeCall]) -> tuple[JudgeCall, ...]:
    """Bloc unique, tri croissant de la clé gelée ; égalité levée par identité."""
    return tuple(
        sorted(calls, key=lambda call: (call.sort_key, call.comparison_id, call.orientation))
    )


def candidate_material(trace: PolicyTrace) -> CandidateMaterial:
    """Matériel de pack d'une trajectoire complète — refuse tout le reste."""
    if not trace.complete or trace.decision is None:
        raise ValueError(f"incomplete trajectory cannot be packed: {trace.case_id}")
    outputs = tuple(turn.output for turn in trace.turns)
    if len(outputs) != 3:
        raise ValueError("a packed trajectory must have exactly three turns")
    return CandidateMaterial(outputs=outputs, decision=trace.decision)


def deblind(preference: str, orientation: str, mapping: Mapping[str, str]) -> str:
    """Ramène une préférence du juge à l'espace des politiques.

    `mapping` décrit l'orientation *forward* : `{"A": politique_a, "B":
    politique_b}`. Le pack inverse échange les deux candidats, donc son `A`
    montre la politique placée en `B` à l'aller.
    """
    if preference in {"TIE", "INVALID"}:
        return preference
    if preference not in {"A", "B"}:
        raise ValueError(f"unknown preference: {preference}")
    if orientation == "forward":
        return mapping[preference]
    if orientation == "reverse":
        return mapping["B" if preference == "A" else "A"]
    raise ValueError(f"unknown orientation: {orientation}")


def pair_position(label: str, pair: Sequence[str]) -> str:
    """Projette une politique sur la position `A`/`B` de la paire lexicale.

    Permet de réutiliser la règle de résolution gelée juge unique sans en
    écrire une variante dans l'espace des presets.
    """
    if label in {"TIE", "INVALID"}:
        return label
    if label == pair[0]:
        return "A"
    if label == pair[1]:
        return "B"
    raise ValueError(f"{label} does not belong to the compared pair {tuple(pair)}")


def pack_integrity(pack: EvidencePack) -> dict[str, Any]:
    """C11 : octets reproductibles et inversion involutive, hors payload."""
    raw = canonical_json_bytes(pack)
    rebuilt = canonical_json_bytes(EvidencePack.model_validate_json(raw))
    restored = canonical_json_bytes(invert_evidence_pack(invert_evidence_pack(pack)))
    deterministic = raw == rebuilt
    involutive = raw == restored
    return {
        "sha256": sha256_bytes(raw),
        "bytes": len(raw),
        "deterministic": deterministic,
        "inversion_involutive": involutive,
        "ok": deterministic and involutive,
    }


def pack_blindness(pack: EvidencePack, *, forbidden: Iterable[str]) -> dict[str, Any]:
    """C9 : structure fermée, étiquettes A puis B, aucun identifiant de politique.

    La recherche porte sur les octets canoniques entiers, sorties de modèle
    comprises : un producteur qui recopie le nom de son bras ou de son modèle
    dans une trajectoire lève l'aveuglement pour de bon, quelle qu'en soit
    l'origine. Les identifiants de *cas* (case_id, external_id, source_name)
    ne sont pas cherchés : le pack n'a aucun champ pour les porter et ils sont
    communs aux deux candidats, donc non discriminants.
    """
    raw = canonical_json_bytes(pack).decode("utf-8")
    tokens = tuple(dict.fromkeys(item for item in forbidden if item))
    found = sorted({token for token in tokens if token in raw})
    labels = [candidate.candidate for candidate in pack.candidates]
    labels_ok = labels == ["A", "B"]
    return {
        "forbidden_found": found,
        "labels_ok": labels_ok,
        "ok": not found and labels_ok,
    }


def objective_failure(trace: PolicyTrace) -> dict[str, Any]:
    """O4 : trace incomplète, contrat violé ou dépassement du budget de tokens."""
    truncated = any(
        float(turn.metrics.get("truncated", 0.0)) >= 1.0 for turn in trace.turns
    )
    incomplete = not trace.complete
    return {
        "incomplete": incomplete,
        "contract_error": trace.contract_error,
        "truncated": truncated,
        "failed": incomplete or truncated,
    }


def seal_blind_mapping(
    entries: Iterable[Mapping[str, Any]], *, phase: str
) -> dict[str, Any]:
    """Scelle le mapping candidat -> politique, hors du pack et avant jugement."""
    rows = [
        {
            "comparison_id": str(entry["comparison_id"]),
            "candidate_a": str(entry["candidate_a"]),
            "candidate_b": str(entry["candidate_b"]),
        }
        for entry in entries
    ]
    rows.sort(key=lambda row: row["comparison_id"])
    if len({row["comparison_id"] for row in rows}) != len(rows):
        raise ValueError("blind mapping comparison identifiers must be unique")
    payload = {
        "schema_version": "lyra.p7.v10-blind-mapping.v1",
        "phase": phase,
        "count": len(rows),
        "entries": rows,
    }
    raw = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    payload["seal_sha256"] = hashlib.sha256(raw).hexdigest()
    return payload
