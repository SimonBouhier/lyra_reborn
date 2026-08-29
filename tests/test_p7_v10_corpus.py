"""Offline checks for the V10 corpus selection against the real sealed pools."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from agency.tools.vigie.campaign_v2 import privacy_reason_codes
from eval.p7_v10_corpus import (
    CALIBRATION_PER_SOURCE,
    HELDOUT_PER_SOURCE,
    MAX_CHARS,
    MIN_CHARS,
    SOURCES,
    calibration_cases,
    heldout_cases,
    seal_manifest,
)

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def calibration():
    return calibration_cases(ROOT)


@pytest.fixture(scope="module")
def heldout():
    return heldout_cases(ROOT)


def test_calibration_is_twelve_benign_v2_items_four_per_source(calibration):
    assert len(calibration) == 12
    per_source = {source: 0 for source in SOURCES}
    labels = {}
    for line in (ROOT / "corpora/vigie_shadow_v2/labels.jsonl").read_text(
        encoding="utf-8"
    ).splitlines():
        row = json.loads(line)
        labels[row["item_id"]] = row["label"]
    for case in calibration:
        per_source[case.source_name] += 1
        assert labels[case.case_id] == "BENIGN"
    assert per_source == {source: CALIBRATION_PER_SOURCE for source in SOURCES}
    assert calibration == calibration_cases(ROOT)  # déterminisme


def test_heldout_is_sixty_cases_twenty_per_source(heldout):
    assert len(heldout) == 60
    per_source = {source: 0 for source in SOURCES}
    for case in heldout:
        per_source[case.source_name] += 1
    assert per_source == {source: HELDOUT_PER_SOURCE for source in SOURCES}
    assert heldout == heldout_cases(ROOT)  # déterminisme


def test_heldout_respects_window_privacy_and_exclusions(heldout, calibration):
    v2_ids = set()
    for line in (ROOT / "corpora/vigie_shadow_v2/items.jsonl").read_text(
        encoding="utf-8"
    ).splitlines():
        row = json.loads(line)
        base = row["external_id"].split("::")[0]
        v2_ids.add((row["source"], base))
    calibration_ids = {case.case_id for case in calibration}
    for case in heldout:
        assert MIN_CHARS <= len(case.source_text) <= MAX_CHARS
        assert privacy_reason_codes(case.source_text) == ()
        source, external_id = case.case_id.split(":", 1)
        assert (source, external_id) not in v2_ids
        assert case.case_id not in calibration_ids
    assert len({case.case_id for case in heldout}) == 60
    assert len({case.source_text for case in heldout}) == 60  # pas de doublon


def test_seal_manifest_carries_hashes_and_never_content(heldout):
    seal = seal_manifest(heldout, phase="heldout")
    assert seal["count"] == 60
    assert seal["per_source"] == {source: 20 for source in sorted(SOURCES)}
    assert len(seal["seal_sha256"]) == 64
    dumped = json.dumps(seal, ensure_ascii=False)
    for case in heldout:
        # Aucun fragment substantiel du contenu ne fuit dans le scellement.
        probe = case.source_text.strip()[:60]
        assert probe and probe not in dumped
