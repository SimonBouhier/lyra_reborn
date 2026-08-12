"""Contrats fermés de la tranche verticale P7.

Les modèles produisent du texte libre aux tours 1 et 2. Le tour 3 est une
décision éditoriale JSON stricte : Pydantic ferme le schéma, puis un contrôle
déterministe vérifie que les ancres existent réellement dans la source.
"""
from __future__ import annotations

import json
import hashlib
import unicodedata
from dataclasses import dataclass
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, ValidationError


class EditorialAction(str, Enum):
    IGNORE = "IGNORE"
    DEFER = "DEFER"
    AUDIT = "AUDIT"
    AMPLIFY = "AMPLIFY"


class Evidence(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    source_span_id: str = Field(pattern=r"^S[0-9]{3}$")
    why: str = Field(min_length=30, max_length=400)


class EditorialDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    decision: EditorialAction
    rationale: str = Field(min_length=80, max_length=1200)
    evidence: list[Evidence] = Field(min_length=1, max_length=3)
    uncertainty: str = Field(min_length=30, max_length=600)
    next_step: str = Field(min_length=20, max_length=500)


class DecisionContractError(ValueError):
    """Le tour final ne respecte pas le contrat objectif gelé."""


def normalize_evidence_text(value: str) -> str:
    """Normalisation unique de la source avant segmentation."""
    return " ".join(unicodedata.normalize("NFC", value or "").split())


@dataclass(frozen=True)
class SourceSegment:
    span_id: str
    text: str


def segment_source(source: str, max_chars: int = 220) -> tuple[SourceSegment, ...]:
    """Découpe gloutonnement la source normalisée, selon le gel V5."""
    if max_chars <= 0:
        raise ValueError("max_chars must be positive")
    normalized = normalize_evidence_text(source)
    if not normalized:
        raise DecisionContractError("source has no segment")

    chunks: list[str] = []
    current = ""
    for word in normalized.split(" "):
        candidate = word if not current else f"{current} {word}"
        if current and len(candidate) > max_chars:
            chunks.append(current)
            current = word
        else:
            current = candidate
    if current:
        chunks.append(current)
    if len(chunks) > 999:
        raise DecisionContractError("source exceeds the S001-S999 segment namespace")
    return tuple(
        SourceSegment(span_id=f"S{index:03d}", text=text)
        for index, text in enumerate(chunks, start=1)
    )


def source_segment_map(source: str) -> dict[str, str]:
    return {segment.span_id: segment.text for segment in segment_source(source)}


def render_segmented_source(source: str) -> str:
    return "\n".join(
        f"[{segment.span_id}] {segment.text}" for segment in segment_source(source)
    )


def source_segments_sha256(source: str) -> str:
    wire = json.dumps(
        source_segment_map(source),
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(wire).hexdigest()


def validate_editorial_decision(raw: str, source: str) -> EditorialDecision:
    """Parse un JSON strict et prouve que chaque ancre appartient à la source.

    Aucun retrait de clôture Markdown et aucun appel de réparation : un modèle
    qui entoure le JSON de prose échoue explicitement.
    """
    if not isinstance(raw, str) or not raw.strip():
        raise DecisionContractError("empty final output")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise DecisionContractError("final output is not strict JSON") from exc
    try:
        decision = EditorialDecision.model_validate(payload)
    except ValidationError as exc:
        raise DecisionContractError("final output violates the closed schema") from exc

    allowed = source_segment_map(source)
    for item in decision.evidence:
        if item.source_span_id not in allowed:
            raise DecisionContractError("evidence source_span_id is absent from source")
    return decision


def decision_json_schema(source: str) -> str:
    """Schéma compact inclus dans le prompt final, produit par la source canonique."""
    return json.dumps(decision_schema(source), ensure_ascii=False)


def decision_schema(source: str) -> dict:
    """Schéma Ollama dynamique : l'enum contient seulement les ancres du cas."""
    schema = EditorialDecision.model_json_schema()
    span_property = schema["$defs"]["Evidence"]["properties"]["source_span_id"]
    span_property["enum"] = list(source_segment_map(source))
    return schema
