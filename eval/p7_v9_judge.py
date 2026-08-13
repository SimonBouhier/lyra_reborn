"""Compatibilité Ollama V9 sans relâcher le contrat juge Pydantic."""
from __future__ import annotations

from typing import Any

from eval.p7_contracts import EditorialDecision
from eval.p7_evidence import CandidateMaterial, EvidencePack, build_evidence_pack
from eval.p7_v7_judge import judgment_schema


WIRE_ONLY_REMOVED_KEYWORDS = frozenset({"minLength", "maxLength"})


def _strip_unsupported_string_bounds(value: Any) -> Any:
    """Copie un schéma en retirant uniquement les deux bornes non compilées."""
    if isinstance(value, dict):
        return {
            key: _strip_unsupported_string_bounds(item)
            for key, item in value.items()
            if key not in WIRE_ONLY_REMOVED_KEYWORDS
        }
    if isinstance(value, list):
        return [_strip_unsupported_string_bounds(item) for item in value]
    return value


def wire_judgment_schema(pack: EvidencePack) -> dict:
    """Schéma envoyé à Ollama ; l'acceptation reste faite par Pydantic."""
    return _strip_unsupported_string_bounds(judgment_schema(pack))


def qminus1_evidence_pack() -> EvidencePack:
    """Pack diagnostique déterministe, indépendant des trois fixtures Q0."""
    source = (
        "The diagnostic note reports that a parser accepted four structured records "
        "and rejected one malformed record. It does not compare model quality, and it "
        "recommends inspecting the rejected record before changing the parser."
    )
    decision = EditorialDecision.model_validate(
        {
            "decision": "AUDIT",
            "rationale": (
                "The note establishes a transport observation rather than a model-quality "
                "comparison, so the malformed record should be inspected before changing the parser."
            ),
            "evidence": [
                {
                    "source_span_id": "S001",
                    "why": (
                        "The source reports four accepted records, one malformed rejection, "
                        "and explicitly recommends inspection first."
                    ),
                }
            ],
            "uncertainty": (
                "The cause of the malformed record is not supplied, and no conclusion about "
                "comparative model quality is supported."
            ),
            "next_step": (
                "Inspect the rejected record and reproduce the parser result before modifying its contract."
            ),
        }
    )
    final = decision.model_dump_json()
    candidate_a = CandidateMaterial(
        outputs=(
            "The note is about parser transport: four records passed and one malformed record failed.",
            "It contains no model-quality comparison, so the failed record is the immediate object of inspection.",
            final,
        ),
        decision=decision,
    )
    candidate_b = CandidateMaterial(
        outputs=(
            "Four structured records were accepted while one malformed record was rejected by the parser.",
            "Because the failure cause is absent, inspect and reproduce that record before altering the contract.",
            final,
        ),
        decision=decision,
    )
    return build_evidence_pack(source, candidate_a, candidate_b)
