"""Contrats fermés de la tranche verticale P7.

Les modèles produisent du texte libre aux tours 1 et 2. Le tour 3 est une
décision éditoriale JSON stricte : Pydantic ferme le schéma, puis un contrôle
déterministe vérifie que les citations existent réellement dans la source.
"""
from __future__ import annotations

import json
import unicodedata
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, ValidationError


class EditorialAction(str, Enum):
    IGNORE = "IGNORE"
    DEFER = "DEFER"
    AUDIT = "AUDIT"
    AMPLIFY = "AMPLIFY"


class Evidence(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    quote: str = Field(min_length=20, max_length=240)
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
    """Normalisation unique utilisée pour la source comme pour les citations."""
    return " ".join(unicodedata.normalize("NFC", value or "").split())


def validate_editorial_decision(raw: str, source: str) -> EditorialDecision:
    """Parse un JSON strict et prouve que chaque citation vient de la source.

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

    normalized_source = normalize_evidence_text(source)
    for item in decision.evidence:
        quote = normalize_evidence_text(item.quote)
        if quote not in normalized_source:
            raise DecisionContractError("evidence quote is absent from source")
    return decision


def decision_json_schema() -> str:
    """Schéma compact inclus dans le prompt final, produit par la source canonique."""
    return json.dumps(EditorialDecision.model_json_schema(), ensure_ascii=False)


def decision_schema() -> dict:
    """Objet transmis au champ natif Ollama `format`."""
    return EditorialDecision.model_json_schema()
