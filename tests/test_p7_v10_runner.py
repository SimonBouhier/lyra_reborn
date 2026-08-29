"""Offline checks for the V10 campaign executors, driven by a fake Ollama."""
from __future__ import annotations

from collections import Counter
import json

import pytest

from eval.p7_v10 import CALL_CEILINGS, CONTEXT_TOKENS, JUDGE, PREREG_FREEZE_COMMIT
from eval.p7_v10_calibration import PRESETS
from eval.p7_v10_corpus import calibration_cases, heldout_cases
from eval.p7_v10_producer import load_model
from eval.p7_v10_scoring import score_producer
from scripts.p7_v10 import (
    PRODUCER_CONTEXT_TOKENS,
    ROOT,
    completed_q0,
    run,
    run_calibration,
    run_heldout,
    run_lifecycle_smoke,
    run_preflight,
    run_scoring,
)
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


# --- jeu tenu -------------------------------------------------------------
#
# Le faux juge préfère le candidat au plus grand `num_predict` : ces tests
# prouvent que la chaîne transporte, attribue, dé-aveugle et assemble
# correctement. Ils ne mesurent RIEN de H10 — aucune de ces sorties n'est une
# évidence d'évaluation.


def _heldout_dir(run_root):
    directories = [path for path in run_root.glob("p7_v10_heldout_*") if path.is_dir()]
    assert len(directories) == 1
    return directories[0]


def test_heldout_runs_the_frozen_design_and_feeds_the_scorer(monkeypatch, tmp_path):
    install(monkeypatch, FakeOllama())
    status, payload = run_heldout(BASE, 30, tmp_path, "creative")
    run_dir = _heldout_dir(tmp_path)
    summary = json.loads((run_dir / "summary.json").read_bytes())

    assert status == 0
    assert summary["status"] == "HELDOUT_COMPLETE"
    assert summary["h10"] == "UNTESTED"  # aucun verdict hors du scoreur
    assert summary["producer_calls"] == CALL_CEILINGS["heldout_producer"] == 900
    assert summary["judge_calls"] == CALL_CEILINGS["heldout_judge"] == 360
    assert summary["complete_pairs"] == summary["judged_pairs"] == 180
    assert summary["sealed_before_common_t1"] is True

    assert [item["producer"] for item in payload["producers"]] == [
        "mistral:latest",
        "gemma3:latest",
        "granite3.3:latest",
    ]
    for producer in payload["producers"]:
        assert len(producer["pairs"]) == 60
        orders = Counter(pair["order"] for pair in producer["pairs"])
        assert orders == {"ABBA": 30, "BAAB": 30}
        assert all(pair["producer_calls"] == 5 for pair in producer["pairs"])
        assert all(pair["common_t1_identical"] for pair in producer["pairs"])
        # Le scoreur gelé accepte l'entrée telle quelle, sans adaptation.
        result = score_producer(producer)
        assert result["W"] + result["L"] + result["U"] == 60
        assert result["gates"]["C0"] and result["gates"]["C1"] and result["gates"]["C10"]


def test_heldout_seals_the_arm_mapping_apart_and_keeps_packs_blind(monkeypatch, tmp_path):
    install(monkeypatch, FakeOllama())
    run_heldout(BASE, 30, tmp_path, "creative")
    run_dir = _heldout_dir(tmp_path)

    manifest = json.loads((run_dir / "manifest.json").read_bytes())
    mapping = json.loads((run_dir / "blind_mapping.json").read_bytes())
    assert manifest["blind_mapping_sha256"] == mapping["seal_sha256"]
    assert mapping["count"] == 180
    assert {row["candidate_a"] for row in mapping["entries"]} == {"ADAPTIVE", "STATIC_BEST"}
    assert manifest["static_best"] == "creative"

    # C9 : rien de ce mapping ne doit atteindre le juge.
    for request in sorted(run_dir.glob("calls/*.request.json")):
        payload = json.loads(request.read_bytes())
        pack = payload["prompt"].split("<EVIDENCE_PACK_JSON>\n", 1)[1]
        assert "ADAPTIVE" not in pack and "STATIC_BEST" not in pack
        for spec in ("mistral:latest", "gemma3:latest", "granite3.3:latest"):
            assert spec not in pack

    journal = (run_dir / "journal.jsonl").read_text(encoding="utf-8")
    for case in heldout_cases(ROOT)[:5]:
        assert case.source_text.strip()[:60] not in journal


def test_heldout_refuses_a_second_attempt_under_the_same_freeze(monkeypatch, tmp_path):
    install(monkeypatch, FakeOllama())
    assert run_heldout(BASE, 30, tmp_path, "creative")[0] == 0
    assert (tmp_path / f"p7_v10_heldout_{PREREG_FREEZE_COMMIT}.lock").exists()
    with pytest.raises(FileExistsError):
        run_heldout(BASE, 30, tmp_path, "creative")


def test_invalid_judge_answers_stay_invalid_in_a_full_denominator(monkeypatch, tmp_path):
    install(monkeypatch, FakeOllama(judge_failures=tuple(range(1, 361))))
    status, payload = run_heldout(BASE, 30, tmp_path, "creative")
    summary = json.loads((_heldout_dir(tmp_path) / "summary.json").read_bytes())

    assert status == 0  # la phase se termine : le verdict appartient au scoreur
    assert summary["judge_calls"] == 360  # aucune relance, aucune réparation
    for producer in payload["producers"]:
        assert all(
            pair["judge"]["forward"]["arm"] == "INVALID"
            and pair["judge"]["reverse"]["arm"] == "INVALID"
            for pair in producer["pairs"]
        )
        result = score_producer(producer)
        # C12 garde son dénominateur : 2 x 60 paires jugées, 0 réponse valide.
        assert result["gates"]["C12"] is False
        assert (result["W"], result["L"], result["U"]) == (0, 0, 60)
        assert result["verdict"] == "H10_INCONCLUSIVE_FOR_MODEL"


def test_heldout_refuses_a_static_best_outside_the_frozen_presets(monkeypatch, tmp_path):
    fake = install(monkeypatch, FakeOllama())
    with pytest.raises(RuntimeError, match="frozen preset"):
        run_heldout(BASE, 30, tmp_path, "adaptive")
    assert list(tmp_path.glob("*.lock")) == []
    assert fake.generate_calls == []


# --- scoreur et cycle de vie ----------------------------------------------


def test_scoring_aggregates_the_heldout_input_and_locks_its_phase(monkeypatch, tmp_path):
    install(monkeypatch, FakeOllama())
    _, heldout = run_heldout(BASE, 30, tmp_path, "creative")
    status, summary = run_scoring(tmp_path, heldout=heldout, q0_passed=True, q1_passed=True)

    # Un verdict produit vaut 0 : un H10 non soutenu est un résultat, pas un
    # échec d'exécution.
    assert status == 0
    assert (tmp_path / f"p7_v10_scoring_{PREREG_FREEZE_COMMIT}.lock").exists()
    assert summary["h10"] == summary["global_verdict"]["status"]
    assert summary["h10"].startswith("H10_")
    assert len(summary["per_producer"]) == 3
    assert summary["static_best"] == "creative"
    assert summary["corpus_seal_sha256"] == heldout["corpus_seal_sha256"]
    assert summary["gpu_proof"] is None and summary["gpu_proof_note"]
    # Chaque énoncé porte les deux mentions liées par l'amendement.
    assert "juge unique" in summary["independence_note"]
    assert "instrument gele" in summary["scope_note"]
    for result in summary["per_producer"]:
        assert "juge unique" in result["independence_note"]
        assert "instrument gele" in result["scope_note"]

    with pytest.raises(FileExistsError):
        run_scoring(tmp_path, heldout=heldout, q0_passed=True, q1_passed=True)


def test_scoring_leaves_h10_untested_when_a_global_gate_failed(monkeypatch, tmp_path):
    install(monkeypatch, FakeOllama())
    _, heldout = run_heldout(BASE, 30, tmp_path, "creative")
    _, summary = run_scoring(tmp_path, heldout=heldout, q0_passed=False, q1_passed=True)
    assert summary["h10"] == "H10_UNTESTED_IN_V10"
    assert summary["q0_passed"] is False


def test_lifecycle_smoke_runs_without_ollama_corpus_or_fixtures(tmp_path):
    # Aucun monkeypatch : toute tentative de contacter Ollama échouerait.
    status = run_lifecycle_smoke(tmp_path / "smoke", 0.01)
    started = json.loads((tmp_path / "smoke" / "started.json").read_bytes())
    finished = json.loads((tmp_path / "smoke" / "finished.json").read_bytes())

    assert status == 0
    assert finished["status"] == "PASS"
    assert started["pid"] == finished["pid"]
    assert started["implemented_phases"] == started["required_phases"]
    assert started["second_attempt_refused"] is True
    assert started["ollama_contacted"] is False
    assert started["corpus_read"] is False
    assert started["q0_fixtures_read"] is False
    assert started["preregistration_freeze_commit"] == PREREG_FREEZE_COMMIT
    # Le verrou de sonde ne peut pas entrer en collision avec ceux des phases.
    probes = list((tmp_path / "smoke" / "lock_probe").glob("*.lock"))
    assert [path.name for path in probes] == [f"p7_v10_smoke_{PREREG_FREEZE_COMMIT}.lock"]

    with pytest.raises(FileExistsError):
        run_lifecycle_smoke(tmp_path / "smoke", 0.01)
    with pytest.raises(ValueError, match="positive"):
        run_lifecycle_smoke(tmp_path / "other", 0)


def test_the_single_command_stops_at_the_first_failed_gate(monkeypatch, tmp_path):
    # Le faux juge n'a aucun marqueur à lire dans les fixtures Q0 : il répond
    # TIE partout, donc Q0 échoue. La commande doit s'arrêter là.
    fake = install(monkeypatch, FakeOllama())
    # Précondition opérateur : juge résident AU contexte de ses appels.
    load_model(BASE, JUDGE.model, 5, options={"num_ctx": CONTEXT_TOKENS})
    assert run(BASE, 30, tmp_path) == 2
    assert fake.reloads == []  # aucun remontage : la preuve GPU reste valide

    q0_dir = [path for path in tmp_path.glob("p7_v10_q0_*") if path.is_dir()][0]
    summary = json.loads((q0_dir / "summary.json").read_bytes())
    assert summary["status"] == "V10_ABORTED_BEFORE_CALIBRATION"
    assert summary["h10"] == "UNTESTED"

    locks = sorted(path.name for path in tmp_path.glob("*.lock"))
    assert locks == [f"p7_v10_q0_{PREREG_FREEZE_COMMIT}.lock"]
    assert not list(tmp_path.glob("p7_v10_calibration_*"))
    assert not list(tmp_path.glob("p7_v10_heldout_*"))
    assert fake.judge_call_count == 18  # Q0 seule a consommé son budget


def test_a_judge_mounted_at_the_wrong_context_aborts_before_any_lock(monkeypatch, tmp_path):
    """Régression : un juge monté hors 32K serait rechargé par son 1ᵉʳ appel.

    Ollama remonte le modèle dès qu'un appel demande un autre `num_ctx`. Ce
    rechargement arriverait APRÈS le verrou et après la preuve GPU, qui ne
    décrirait alors plus la résidence réellement utilisée. La précondition
    « chargé au contexte 32K » doit donc couper avant le verrou.
    """
    # Serveur au defaut d'Ollama : le juge monterait a son contexte maximum.
    fake = install(monkeypatch, FakeOllama(default_context=131072))
    load_model(BASE, JUDGE.model, 5)
    with pytest.raises(RuntimeError, match="resident at context 131072"):
        run(BASE, 30, tmp_path)
    assert list(tmp_path.glob("*.lock")) == []
    assert fake.judge_call_count == 0  # aucun appel de fixture consommé


def test_a_producer_overflowing_vram_aborts_before_the_calibration_lock(monkeypatch, tmp_path):
    """Régression du 29/08 : granite3.3 monté à 131072 pèse 27,7 Go sur 24 Go.

    Ollama monte un modèle à son contexte maximum quand la requête n'en demande
    pas ; `granite3.3:latest` déborde alors en RAM (`size_vram != size`). La
    précondition doit couper AVANT le verrou de calibration, sans rien
    consommer — c'est ce qui s'est produit sur la console de Simon.
    """
    fake = install(monkeypatch, FakeOllama(default_context=131072))
    # Depuis l'amendement, le controle de contexte coupe des gemma3 (2e
    # producteur), donc AVANT meme que granite ne soit monte : le diagnostic
    # arrive plus tot et nomme la valeur attendue. Le debordement VRAM de
    # granite lui-meme est epingle sur ses chiffres reels dans
    # tests/test_p7_v10_producer.py.
    with pytest.raises(RuntimeError, match="resident at context 131072, expected 32768"):
        run_calibration(BASE, 30, tmp_path)

    assert list(tmp_path.glob("*.lock")) == []
    assert [path for path in tmp_path.glob("p7_v10_calibration_*") if path.is_dir()] == []
    assert fake.generate_calls == []  # aucun appel producteur consommé
    assert fake.judge_call_count == 0


def test_the_amended_producer_context_lets_every_model_fit(monkeypatch, tmp_path):
    install(monkeypatch, FakeOllama(default_context=PRODUCER_CONTEXT_TOKENS))
    status, _ = run_calibration(BASE, 30, tmp_path)
    assert status == 0

    run_dir, _ = _summary(tmp_path)
    manifest = json.loads((run_dir / "manifest.json").read_bytes())
    assert manifest["producer_context_tokens"] == PRODUCER_CONTEXT_TOKENS == 32768
    assert manifest["producer_context_amendment"].endswith(
        "P7_V10_PRODUCER_CONTEXT_AMENDMENT.md"
    )
    # La preuve GPU consigne la résidence entière de chacun des quatre modèles.
    proofs = {item["model"]: item["loaded"] for item in manifest["gpu_residency_proofs"]}
    assert set(proofs) == {
        "mistral:latest",
        "gemma3:latest",
        "granite3.3:latest",
        JUDGE.model,
    }
    for model, loaded in proofs.items():
        assert loaded["size"] == loaded["size_vram"]
        expected = CONTEXT_TOKENS if model == JUDGE.model else PRODUCER_CONTEXT_TOKENS
        assert loaded["context_length"] == expected


def _seal_q0(tmp_path, *, status="Q0_PASSED", passed=True):
    """Fabrique un verrou Q0 et son résumé, comme les laisserait un run réel."""
    (tmp_path / f"p7_v10_q0_{PREREG_FREEZE_COMMIT}.lock").write_text("{}", encoding="utf-8")
    run_dir = tmp_path / "p7_v10_q0_20260829T211254.467768Z"
    run_dir.mkdir(parents=True)
    (run_dir / "summary.json").write_text(
        json.dumps(
            {
                "run_id": run_dir.name,
                "status": status,
                "passed": passed,
                "journal_sha256": "6373f4692051162ab34884a1dc90674d74a7cb024ea1e1393bd97ac7a5d60a4a",
            }
        ),
        encoding="utf-8",
    )
    return run_dir


def test_a_passed_q0_is_reused_and_never_replayed(monkeypatch, tmp_path):
    fake = install(monkeypatch, FakeOllama(default_context=PRODUCER_CONTEXT_TOKENS))
    q0_dir = _seal_q0(tmp_path)
    assert completed_q0(tmp_path)["run_id"] == q0_dir.name

    assert run(BASE, 30, tmp_path) == 0  # chaîne complète jusqu'au verdict

    # Q0 n'a pas été rejouée : ses 18 appels ne réapparaissent pas, et son
    # répertoire de run est resté exactement tel quel.
    assert not (q0_dir / "journal.jsonl").exists()
    assert len([p for p in tmp_path.glob("p7_v10_q0_*") if p.is_dir()]) == 1
    assert fake.judge_call_count == 432 + 360  # calibration + tenu, pas Q0

    # La provenance de Q0 est inscrite au manifeste de la calibration.
    run_dir, _ = _summary(tmp_path)
    provenance = json.loads((run_dir / "manifest.json").read_bytes())["q0_provenance"]
    assert provenance["run_id"] == q0_dir.name
    assert provenance["status"] == "Q0_PASSED"
    assert provenance["reused_from_earlier_command"] is True

    # Les trois phases restantes ont bien posé leur verrou, une fois chacune.
    locks = sorted(path.name.split("_")[2] for path in tmp_path.glob("*.lock"))
    assert locks == ["calibration", "heldout", "q0", "scoring"]


def test_a_consumed_q0_that_did_not_pass_refuses_a_second_attempt(monkeypatch, tmp_path):
    fake = install(monkeypatch, FakeOllama(default_context=PRODUCER_CONTEXT_TOKENS))
    _seal_q0(tmp_path, status="V10_ABORTED_BEFORE_CALIBRATION", passed=False)

    with pytest.raises(RuntimeError, match="consumed and did not clear its gate"):
        completed_q0(tmp_path)
    with pytest.raises(RuntimeError, match="consumed and did not clear its gate"):
        run(BASE, 30, tmp_path)
    assert fake.judge_call_count == 0
    assert not [p for p in tmp_path.glob("p7_v10_calibration_*")]


def test_preflight_mounts_the_judge_without_lock_or_fixture_call(monkeypatch, tmp_path):
    fake = install(monkeypatch, FakeOllama())
    assert run_preflight(BASE, 30) == 0

    # Il laisse EXACTEMENT la résidence que Q0 exige, donc `run` enchaîne.
    assert fake.judge_call_count == 0
    assert fake.generate_calls == []
    assert list(tmp_path.glob("*.lock")) == []
    # Le preflight repete la preuve GPU des phases : les quatre modeles ont ete
    # montes entiers, puis le juge est laisse resident pour Q0.
    judge_loads = [
        item for item in fake.residency_calls
        if item["model"] == JUDGE.model and item["keep_alive"] != 0
    ]
    assert judge_loads and all(item["num_ctx"] == CONTEXT_TOKENS for item in judge_loads)
    assert fake.loaded[JUDGE.model] is True

    assert run(BASE, 30, tmp_path) == 2  # Q0 échoue sur le faux juge, sans remontage
    assert fake.reloads == []


def test_preflight_catches_a_server_left_at_the_default_context(monkeypatch):
    fake = install(monkeypatch, FakeOllama(default_context=131072))
    with pytest.raises(RuntimeError, match="resident at context 131072, expected 32768"):
        run_preflight(BASE, 30)
    assert fake.generate_calls == []  # aucun appel de fixture


def test_preflight_refuses_a_drifted_digest_and_loads_nothing(monkeypatch):
    fake = install(monkeypatch, FakeOllama())
    fake.catalog[JUDGE.model] = "0" * 64
    with pytest.raises(RuntimeError, match="digest mismatch"):
        run_preflight(BASE, 30)
    assert fake.residency_calls == []


def test_every_phase_mounts_the_judge_at_the_context_its_calls_use(monkeypatch, tmp_path):
    fake = install(monkeypatch, FakeOllama())
    run_calibration(BASE, 30, tmp_path)
    run_heldout(BASE, 30, tmp_path, "creative")

    # Aucun remontage sur toute la campagne : montage et appels concordent.
    assert fake.reloads == []
    judge_loads = [
        item for item in fake.residency_calls
        if item["model"] == JUDGE.model and item["keep_alive"] != 0
    ]
    assert judge_loads and all(item["num_ctx"] == CONTEXT_TOKENS for item in judge_loads)
    # Les producteurs ne fixent pas num_ctx : leur fenetre vient du serveur,
    # plafonnee par l'amendement, et doit valoir exactement PRODUCER_CONTEXT_TOKENS.
    producer_loads = [
        item for item in fake.residency_calls
        if item["model"] != JUDGE.model and item["keep_alive"] != 0
    ]
    assert producer_loads
    assert all(item["num_ctx"] == PRODUCER_CONTEXT_TOKENS for item in producer_loads)
