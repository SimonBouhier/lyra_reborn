"""Offline checks for the V10 campaign executors, driven by a fake Ollama."""
from __future__ import annotations

import json

import pytest

from eval.p7_v10 import CALL_CEILINGS, PREREG_FREEZE_COMMIT
from eval.p7_v10_calibration import PRESETS
from eval.p7_v10_corpus import calibration_cases
from scripts.p7_v10 import ROOT, run_calibration
from tests.p7_v10_fakes import FakeOllama, install

BASE = "http://127.0.0.1:11434"


def _summary(run_root):
    directories = [path for path in run_root.glob("p7_v10_calibration_*") if path.is_dir()]
    assert len(directories) == 1
    return directories[0], json.loads((directories[0] / "summary.json").read_bytes())


def test_calibration_runs_the_frozen_matrix_and_selects_a_static_best(monkeypatch, tmp_path):
    fake = install(monkeypatch, FakeOllama())
    status, summary = run_calibration(BASE, 30, tmp_path)

    assert status == 0
    assert summary["status"] == "Q1_PASSED"
    assert summary["h10"] == "UNTESTED"

    # Matrice gelée : 12 cas x 4 presets x 3 tours x 3 producteurs = 432 ;
    # 72 comparaisons x 3 producteurs x 2 orientations = 432.
    assert summary["producer_calls"] == CALL_CEILINGS["calibration_producer"] == 432
    assert summary["judge_calls"] == CALL_CEILINGS["calibration_judge"] == 432
    assert summary["comparisons"] == 216
    assert summary["complete_comparisons"] == summary["judged_comparisons"] == 216

    # Le faux juge préfère le plus grand num_predict : `creative` (delta_r max).
    assert summary["static_best"] == "creative"
    assert summary["selection"]["lexical_tiebreak_needed"] is False
    assert summary["q1"] == {
        "complete_comparisons": 216,
        "resolved_comparisons": 216,
        "resolution_rate": 1.0,
        "lexical_tiebreak_needed": False,
        "ablation_winners": {"arxiv": "creative", "github": "creative", "hackernews": "creative"},
        "ablation_agreement": 3,
        "static_best": "creative",
        "passed": True,
    }
    assert set(summary["output_tokens"]) == set(PRESETS)
    assert summary["objective_failure_rates"] == {preset: 0.0 for preset in PRESETS}
    # Première clause Q1 de V8 : round-robin complet, aucune relance sélective.
    assert summary["round_robin_complete"] is True
    assert summary["q1_passed"] is True


def test_calibration_seals_the_corpus_and_the_blind_mapping_apart(monkeypatch, tmp_path):
    install(monkeypatch, FakeOllama())
    run_calibration(BASE, 30, tmp_path)
    run_dir, _ = _summary(tmp_path)

    manifest = json.loads((run_dir / "manifest.json").read_bytes())
    corpus_seal = json.loads((run_dir / "corpus_seal.json").read_bytes())
    mapping = json.loads((run_dir / "blind_mapping.json").read_bytes())

    assert manifest["corpus_seal_sha256"] == corpus_seal["seal_sha256"]
    assert manifest["blind_mapping_sha256"] == mapping["seal_sha256"]
    assert corpus_seal["count"] == 12
    assert mapping["count"] == 216

    # C9 : le mapping candidat -> preset vit hors des packs envoyés au juge.
    for request in sorted(run_dir.glob("calls/*.request.json")):
        payload = json.loads(request.read_bytes())
        pack = payload["prompt"].split("<EVIDENCE_PACK_JSON>\n", 1)[1]
        for preset in PRESETS:
            if preset in ("default", "strict", "focused"):
                continue  # mots anglais courants : la garantie est structurelle
            assert preset not in pack
        assert "ADAPTIVE" not in pack and "STATIC_BEST" not in pack


def test_calibration_journal_carries_counts_and_hashes_but_no_content(monkeypatch, tmp_path):
    install(monkeypatch, FakeOllama())
    run_calibration(BASE, 30, tmp_path)
    run_dir, _ = _summary(tmp_path)

    journal = (run_dir / "journal.jsonl").read_text(encoding="utf-8")
    for case in calibration_cases(ROOT):
        probe = case.source_text.strip()[:60]
        assert probe and probe not in journal

    events = [json.loads(line) for line in journal.splitlines() if line.strip()]
    kinds = {event["event"] for event in events}
    assert {"producer_call", "trajectory_finished", "comparison_prepared"} <= kinds
    assert {"judge_block_started", "judge_block_finished", "comparison_resolved"} <= kinds
    producer_calls = [event for event in events if event["event"] == "producer_call"]
    assert len(producer_calls) == 432
    assert all(len(event["prompt_sha256"]) == 64 for event in producer_calls)
    assert all(event["eval_count"] > 0 for event in producer_calls)


def test_calibration_refuses_a_second_attempt_under_the_same_freeze(monkeypatch, tmp_path):
    install(monkeypatch, FakeOllama())
    assert run_calibration(BASE, 30, tmp_path)[0] == 0
    lock = tmp_path / f"p7_v10_calibration_{PREREG_FREEZE_COMMIT}.lock"
    assert lock.exists()
    with pytest.raises(FileExistsError):
        run_calibration(BASE, 30, tmp_path)


def test_a_digest_drift_aborts_before_the_phase_lock(monkeypatch, tmp_path):
    fake = install(monkeypatch, FakeOllama())
    fake.catalog["mistral:latest"] = "0" * 64
    with pytest.raises(RuntimeError, match="digest mismatch"):
        run_calibration(BASE, 30, tmp_path)
    assert list(tmp_path.glob("*.lock")) == []
    assert list(tmp_path.glob("p7_v10_calibration_*")) == []
    assert fake.generate_calls == []  # aucun budget consommé


def test_a_failing_producer_is_never_judged_and_never_relaunched(monkeypatch, tmp_path):
    install(monkeypatch, FakeOllama(producer_failures=("granite3.3:latest",)))
    status, summary = run_calibration(BASE, 30, tmp_path)

    # Les 432 appels producteur sont bien émis — un échec n'est jamais relancé.
    assert summary["producer_calls"] == 432
    # granite ne rend aucune trajectoire complète : ses 72 comparaisons ne sont
    # pas jugées et n'entraînent aucun appel juge.
    assert summary["complete_comparisons"] == 144
    assert summary["judged_comparisons"] == 144
    assert summary["judge_calls"] == 288
    assert summary["objective_failure_rates"] == {preset: pytest.approx(1 / 3) for preset in PRESETS}

    # Seuil Q1 gelé V8 : « au moins 50 % des comparaisons de calibration OÙ LES
    # DEUX TRACES SONT COMPLÈTES ». Un producteur muet ne fait donc pas échouer
    # Q1 par lui-même ; son échec est porté par le taux d'échec objectif, qui
    # entre au départage, et se jugera sur ses portes C0-C12 au jeu tenu.
    assert summary["q1"]["complete_comparisons"] == 144
    assert summary["q1"]["resolution_rate"] == 1.0
    assert summary["round_robin_complete"] is True
    assert status == 0 and summary["static_best"] == "creative"


def test_a_position_following_judge_resolves_nothing_and_fails_q1(monkeypatch, tmp_path):
    # Le juge répond toujours « A » : sa préférence suit la position et non le
    # contenu, donc rien n'est stable après inversion.
    install(monkeypatch, FakeOllama(judge_preference="A"))
    status, summary = run_calibration(BASE, 30, tmp_path)

    assert status == 2
    assert summary["status"] == "V10_ABORTED_BEFORE_HELDOUT"
    assert summary["static_best"] is None
    assert summary["q1"]["resolved_comparisons"] == 0
    assert summary["q1"]["resolution_rate"] == 0.0
    assert summary["q1"]["passed"] is False
    assert summary["q1_passed"] is False
    # Le round-robin reste complet : c'est l'instrument qui échoue, pas le run.
    assert summary["round_robin_complete"] is True
    assert summary["judge_calls"] == 432
