"""Evidence pack déterministe et aveugle gelé par P7 V7."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from eval.p7_contracts import EditorialDecision, segment_source


PACK_SCHEMA_VERSION = "lyra.p7.evidence-pack.v1"


class PackSegment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_span_id: str = Field(pattern=r"^S[0-9]{3}$")
    text: str = Field(min_length=1)


class PackSource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    segments: list[PackSegment] = Field(min_length=1, max_length=999)


class PackTurn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    turn: int = Field(ge=1, le=3)
    output: str = Field(min_length=1)


class SpanCheck(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_span_id: str = Field(pattern=r"^S[0-9]{3}$")
    found: Literal[True]
    text: str = Field(min_length=1)


class PackCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    candidate: Literal["A", "B"]
    turns: list[PackTurn] = Field(min_length=3, max_length=3)
    decision: EditorialDecision
    span_checks: list[SpanCheck] = Field(min_length=1, max_length=3)

    @model_validator(mode="after")
    def validate_candidate(self) -> "PackCandidate":
        if [item.turn for item in self.turns] != [1, 2, 3]:
            raise ValueError("candidate turns must be exactly 1, 2, 3")
        try:
            final_payload = json.loads(self.turns[-1].output)
        except json.JSONDecodeError as exc:
            raise ValueError("candidate turn 3 must be strict JSON") from exc
        if final_payload != self.decision.model_dump(mode="json"):
            raise ValueError("candidate decision must equal the parsed turn 3 output")
        evidence_ids = {item.source_span_id for item in self.decision.evidence}
        check_ids = {item.source_span_id for item in self.span_checks}
        if evidence_ids != check_ids:
            raise ValueError("span checks must cover exactly the decision evidence")
        return self


class EvidencePack(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[PACK_SCHEMA_VERSION]
    source: PackSource
    candidates: list[PackCandidate] = Field(min_length=2, max_length=2)

    @model_validator(mode="after")
    def validate_pack(self) -> "EvidencePack":
        if [item.candidate for item in self.candidates] != ["A", "B"]:
            raise ValueError("candidates must be ordered and labelled A then B")
        source = {item.source_span_id: item.text for item in self.source.segments}
        if len(source) != len(self.source.segments):
            raise ValueError("source segment identifiers must be unique")
        for candidate in self.candidates:
            for check in candidate.span_checks:
                if source.get(check.source_span_id) != check.text:
                    raise ValueError("span check does not resolve to the packed source")
        return self


@dataclass(frozen=True)
class CandidateMaterial:
    outputs: tuple[str, str, str]
    decision: EditorialDecision


def canonical_json_bytes(value: BaseModel | dict | list) -> bytes:
    payload = value.model_dump(mode="json") if isinstance(value, BaseModel) else value
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _pack_candidate(
    label: Literal["A", "B"],
    material: CandidateMaterial,
    source_map: dict[str, str],
) -> PackCandidate:
    evidence_ids = tuple(dict.fromkeys(item.source_span_id for item in material.decision.evidence))
    checks = [
        SpanCheck(source_span_id=span_id, found=True, text=source_map[span_id])
        for span_id in evidence_ids
    ]
    return PackCandidate(
        candidate=label,
        turns=[PackTurn(turn=index, output=output) for index, output in enumerate(material.outputs, 1)],
        decision=material.decision,
        span_checks=checks,
    )


def build_evidence_pack(
    source_text: str,
    first: CandidateMaterial,
    second: CandidateMaterial,
) -> EvidencePack:
    segments = segment_source(source_text)
    source_map = {item.span_id: item.text for item in segments}
    return EvidencePack(
        schema_version=PACK_SCHEMA_VERSION,
        source=PackSource(
            segments=[PackSegment(source_span_id=item.span_id, text=item.text) for item in segments]
        ),
        candidates=[
            _pack_candidate("A", first, source_map),
            _pack_candidate("B", second, source_map),
        ],
    )


def invert_evidence_pack(pack: EvidencePack) -> EvidencePack:
    payload = pack.model_dump(mode="json")
    right, left = payload["candidates"][1], payload["candidates"][0]
    right["candidate"] = "A"
    left["candidate"] = "B"
    payload["candidates"] = [right, left]
    return EvidencePack.model_validate(payload)


def pack_sha256(pack: EvidencePack) -> str:
    return sha256_bytes(canonical_json_bytes(pack))
