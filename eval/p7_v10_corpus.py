"""Sélection et scellement du corpus V10 — recette V8 sur les atomes V2 gelés.

Implémente mot pour mot PREREGISTRATION_v8.md §« Calibration et jeu tenu »
(incorporé par V10) : calibration = 12 bénins V2 déjà ouverts, quatre par
source, rang `sha256(seed || "calibration" || item_id)` ; tenu = 60 cas du
pool V1 scellé (20 par source), rang `sha256(seed || "heldout" || source ||
external_id)`, après exclusion des IDs V1/V2/calibration, des doublons, des
filtres PII V2 et hors fenêtre 400–3 000 caractères — aucun filtre sémantique
post-hoc. Aucun contenu n'est affiché ni journalisé : comptes et hashes.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from agency.tools.vigie.campaign_v2 import (
    V1_REVIEW_SHA256,
    normalize_content_v2,
    privacy_reason_codes,
    v1_carriers,
)
from eval.p7_trajectory import EvaluationCase

__all__ = [
    "CORPUS_SEED",
    "POOL_SHA256",
    "SOURCES",
    "CALIBRATION_PER_SOURCE",
    "HELDOUT_PER_SOURCE",
    "MIN_CHARS",
    "MAX_CHARS",
    "calibration_cases",
    "heldout_cases",
    "seal_manifest",
]

CORPUS_SEED = 20260817  # V8 « Seed globale »

POOL_RELPATH = "corpora/vigie_shadow_v1/candidate_pool.jsonl"
POOL_SHA256 = "074e0cecb04a2ca4fb527414abd3307b4d80fe812ac934178a5fd06bcc2ff6f0"
V1_REVIEW_RELPATH = "corpora/vigie_shadow_v1/review_queue.jsonl"
V2_ITEMS_RELPATH = "corpora/vigie_shadow_v2/items.jsonl"
V2_LABELS_RELPATH = "corpora/vigie_shadow_v2/labels.jsonl"

SOURCES = ("arxiv", "github", "hackernews")
CALIBRATION_PER_SOURCE = 4
HELDOUT_PER_SOURCE = 20
MIN_CHARS = 400
MAX_CHARS = 3000

_CONSTRUCTIONS = ("direct", "indirect", "adaptive")


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _verify_file_sha(path: Path, expected: str, label: str) -> None:
    observed = hashlib.sha256(path.read_bytes()).hexdigest()
    if observed != expected:
        raise RuntimeError(
            f"{label} differs from the frozen artifact: expected {expected}, "
            f"observed {observed}"
        )


def _rank(material: str) -> str:
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def _base_external_id(external_id: str) -> str:
    for construction in _CONSTRUCTIONS:
        suffix = f"::{construction}"
        if external_id.endswith(suffix):
            return external_id[: -len(suffix)]
    return external_id


def calibration_cases(root: Path) -> tuple[EvaluationCase, ...]:
    """12 bénins V2 déjà ouverts, quatre par source, rang gelé sur item_id."""
    items = {row["item_id"]: row for row in _read_jsonl(root / V2_ITEMS_RELPATH)}
    labels = _read_jsonl(root / V2_LABELS_RELPATH)
    benign = [row for row in labels if row.get("label") == "BENIGN"]
    if len(benign) != 60:
        raise RuntimeError(f"expected 60 BENIGN V2 labels, found {len(benign)}")

    selected: list[EvaluationCase] = []
    for source in SOURCES:
        candidates = sorted(
            (row for row in benign if row.get("source") == source),
            key=lambda row: _rank(f"{CORPUS_SEED}\0calibration\0{row['item_id']}"),
        )
        if len(candidates) < CALIBRATION_PER_SOURCE:
            raise RuntimeError(f"not enough BENIGN V2 items for source {source}")
        for row in candidates[:CALIBRATION_PER_SOURCE]:
            item = items.get(row["item_id"])
            if item is None:
                raise RuntimeError(f"V2 label without item: {row['item_id']}")
            content = item["content"]
            digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
            if item.get("content_sha256") not in (None, digest):
                raise RuntimeError(f"V2 item content hash mismatch: {row['item_id']}")
            selected.append(
                EvaluationCase(
                    case_id=row["item_id"],
                    source_name=source,
                    source_text=content,
                )
            )
    return tuple(selected)


def heldout_cases(root: Path) -> tuple[EvaluationCase, ...]:
    """60 cas tenus (20 par source) selon la recette V8, sans lecture humaine."""
    pool_path = root / POOL_RELPATH
    _verify_file_sha(pool_path, POOL_SHA256, "candidate pool")
    review_path = root / V1_REVIEW_RELPATH
    _verify_file_sha(review_path, V1_REVIEW_SHA256, "V1 review queue")

    excluded: set[tuple[str, str]] = set(v1_carriers(_read_jsonl(review_path)))
    for row in _read_jsonl(root / V2_ITEMS_RELPATH):
        excluded.add((row["source"], _base_external_id(row["external_id"])))
    # La calibration est un sous-ensemble des items V2 : déjà couverte, mais la
    # prérég la nomme explicitement — on la retire aussi par construction.

    seen_external: set[tuple[str, str]] = set()
    seen_content: set[str] = set()
    eligible: dict[str, list[dict[str, Any]]] = {source: [] for source in SOURCES}
    for row in _read_jsonl(pool_path):
        source = str(row.get("source", "")).strip()
        external_id = str(row.get("external_id", "")).strip()
        if source not in SOURCES or not external_id:
            continue
        key = (source, external_id)
        if key in excluded:
            continue
        content = normalize_content_v2(row["content"])
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        if key in seen_external or content_hash in seen_content:
            continue
        seen_external.add(key)
        seen_content.add(content_hash)
        if privacy_reason_codes(content):
            continue
        if not (MIN_CHARS <= len(content) <= MAX_CHARS):
            continue
        eligible[source].append(
            {
                "source": source,
                "external_id": external_id,
                "content": content,
                "content_sha256": content_hash,
            }
        )

    selected: list[EvaluationCase] = []
    for source in SOURCES:
        ranked = sorted(
            eligible[source],
            key=lambda row: _rank(
                f"{CORPUS_SEED}\0heldout\0{row['source']}\0{row['external_id']}"
            ),
        )
        if len(ranked) < HELDOUT_PER_SOURCE:
            raise RuntimeError(
                f"not enough eligible held-out candidates for source {source}: "
                f"{len(ranked)}"
            )
        for row in ranked[:HELDOUT_PER_SOURCE]:
            selected.append(
                EvaluationCase(
                    case_id=f"{source}:{row['external_id']}",
                    source_name=source,
                    source_text=row["content"],
                )
            )
    return tuple(selected)


def seal_manifest(cases: tuple[EvaluationCase, ...], *, phase: str) -> dict[str, Any]:
    """Scellement : comptes et hashes uniquement — jamais le contenu."""
    per_source: dict[str, int] = {}
    entries = []
    for case in cases:
        per_source[case.source_name] = per_source.get(case.source_name, 0) + 1
        entries.append(
            {
                "case_id": case.case_id,
                "source": case.source_name,
                "content_sha256": hashlib.sha256(
                    case.source_text.encode("utf-8")
                ).hexdigest(),
                "content_chars": len(case.source_text),
            }
        )
    payload = {
        "schema_version": "lyra.p7.v10-corpus-seal.v1",
        "phase": phase,
        "seed": CORPUS_SEED,
        "count": len(cases),
        "per_source": dict(sorted(per_source.items())),
        "cases": entries,
    }
    raw = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    payload["seal_sha256"] = hashlib.sha256(raw).hexdigest()
    return payload
