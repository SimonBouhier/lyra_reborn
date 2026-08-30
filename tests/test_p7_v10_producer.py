"""Offline checks for the V10 producer boundary and GPU residency helpers."""
from __future__ import annotations

import json

import pytest

from core.knobs import Knobs, KnobMapping
from core.loop import LyraLoop
from eval.p7_v11 import JUDGE
from eval.p7_v10_producer import (
    PRODUCERS,
    OllamaProducerClient,
    load_model,
    models_runtime,
    unload_model,
    verify_context_length,
    verify_fully_loaded_on_gpu,
    verify_identity,
)
from eval.p7_v10_q1 import verify_judge_fully_loaded_on_gpu
from tests.p7_v10_fakes import FakeOllama, install

BASE = "http://127.0.0.1:11434"


@pytest.fixture
def fake(monkeypatch):
    return install(monkeypatch, FakeOllama())


def test_producers_are_the_three_frozen_v8_models():
    assert [spec.model for spec in PRODUCERS] == [
        "mistral:latest",
        "gemma3:latest",
        "granite3.3:latest",
    ]
    assert [spec.digest for spec in PRODUCERS] == [
        "6577803aa9a036369e481d648a2baebb381ebc6e897f2bb9a766a2aa7bfbc1cf",
        "a2af6cc3eb7fa8be8504abaf9b04e88f17a119ec3f04a3addf55f92841195f5a",
        "fd429f23b90980ed1bef53b990894e7b0199331f6ae90c5650240a7d5b70f1f7",
    ]
    # Le juge doit rester d'une famille distincte de celles des producteurs.
    assert JUDGE.family not in {spec.family for spec in PRODUCERS}
    assert all(spec.quantization == "Q4_K_M" for spec in PRODUCERS)


def test_payload_nests_options_and_never_sends_think(fake):
    load_model(BASE, "mistral:latest", 5)
    client = OllamaProducerClient(BASE, "mistral:latest", 5)
    options = {"temperature": 0.4, "top_p": 0.7, "num_predict": 320, "seed": 11}
    client.generate("Identifie le noyau du contenu, reste ancré.", options)

    sent = json.loads(fake.last_request)
    assert sent["options"] == options  # correctif P0 : jamais à la racine
    assert "think" not in sent
    assert sent["stream"] is False
    assert sent["model"] == "mistral:latest"
    assert "format" not in sent


def test_structured_turn_carries_the_dynamic_schema(fake):
    load_model(BASE, "mistral:latest", 5)
    client = OllamaProducerClient(BASE, "mistral:latest", 5)
    schema = {"type": "object"}
    client.generate("Rends la décision éditoriale finale.", {"num_predict": 320}, schema)
    sent = json.loads(fake.last_request)
    assert sent["format"] == schema
    assert client.calls[-1].structured is True


def test_call_journal_carries_eval_count_and_never_the_text(fake):
    load_model(BASE, "granite3.3:latest", 5)
    client = OllamaProducerClient(BASE, "granite3.3:latest", 5)
    text = client.generate("Identifie le noyau du contenu.", {"num_predict": 640})
    assert text

    call = client.calls[-1]
    assert call.index == 1
    assert call.eval_count == 80  # marqueur du faux : num_predict // 8
    assert call.output_tokens == 80
    assert call.done_reason == "stop"
    assert call.status_code == 200
    assert call.failed is False
    assert call.output_chars == len(text)
    record = call.as_record()
    assert text not in json.dumps(record, ensure_ascii=False)
    assert len(record["prompt_sha256"]) == 64


def test_a_failed_call_is_recorded_and_returns_empty_without_retry(monkeypatch):
    fake = install(monkeypatch, FakeOllama(producer_failures=("mistral:latest",)))
    load_model(BASE, "mistral:latest", 5)
    client = OllamaProducerClient(BASE, "mistral:latest", 5)
    assert client.generate("Identifie le noyau du contenu.", {"num_predict": 320}) == ""

    call = client.calls[-1]
    assert call.failed and call.error and "HTTPError" in call.error
    assert call.output_tokens == 0
    # Une seule requête a été émise : aucune relance, aucune réparation.
    assert len(client.calls) == 1
    assert len(fake.generate_calls) == 1


def test_client_drives_the_real_loop_and_receives_mapped_options(fake):
    load_model(BASE, "gemma3:latest", 5)
    client = OllamaProducerClient(BASE, "gemma3:latest", 5)
    loop = LyraLoop(
        client,
        mapping=KnobMapping(num_predict_min=128, num_predict_max=768),
        state=None,
        enable_modulation=False,
    )
    result = loop.generate(
        "Identifie le noyau du contenu.",
        task_type="general",
        generation_options={"seed": 7},
    )
    expected = int(128 + (768 - 128) * Knobs().delta_r)
    assert result.options["num_predict"] == expected
    assert client.calls[-1].options == result.options
    assert f"np={expected}" in result.output


def test_residency_requests_generate_nothing_and_toggle_the_catalogue(fake):
    load_model(BASE, "mistral:latest", 5)
    runtime = models_runtime(BASE, 5, ("mistral:latest",))
    verify_identity(runtime, PRODUCERS[0])
    verify_fully_loaded_on_gpu(runtime, PRODUCERS[0])

    unload_model(BASE, "mistral:latest", 5)
    after = models_runtime(BASE, 5, ("mistral:latest",))
    assert after["loaded_models"]["mistral:latest"] is None
    assert after["models"]["mistral:latest"] == PRODUCERS[0].digest  # toujours catalogué
    assert [item["keep_alive"] for item in fake.residency_calls] == ["30m", 0]
    assert fake.generate_calls == []  # aucune génération facturée


def test_gpu_verification_mirrors_the_frozen_judge_precondition():
    spec = PRODUCERS[0]
    resident = {
        "loaded_models": {spec.model: {"digest": spec.digest, "size": 10, "size_vram": 10}}
    }
    verify_fully_loaded_on_gpu(resident, spec)
    verify_judge_fully_loaded_on_gpu(resident, spec)  # même sémantique, autre libellé

    for broken in (
        {"loaded_models": {}},
        {"loaded_models": {spec.model: {"digest": "other", "size": 10, "size_vram": 10}}},
        {"loaded_models": {spec.model: {"digest": spec.digest, "size": 10, "size_vram": 4}}},
        {"loaded_models": {spec.model: {"digest": spec.digest, "size": 0, "size_vram": 0}}},
    ):
        with pytest.raises(RuntimeError):
            verify_fully_loaded_on_gpu(broken, spec)
        with pytest.raises(RuntimeError):
            verify_judge_fully_loaded_on_gpu(broken, spec)


def test_the_observed_granite_overflow_is_refused():
    """Chiffres reels de la console du 29/08 : granite3.3 monte a 131072.

    27,70 Go au total dont 22,77 Go seulement en VRAM sur une carte de 24 Go :
    la trajectoire aurait tourne sur un modele partiellement en RAM, aux
    latences inexploitables pour C7.
    """
    spec = PRODUCERS[2]
    assert spec.model == "granite3.3:latest"
    overflowed = {
        "loaded_models": {
            spec.model: {
                "digest": spec.digest,
                "size": 27698082609,
                "size_vram": 22765916651,
                "context_length": 131072,
            }
        }
    }
    with pytest.raises(RuntimeError, match="not fully loaded on GPU"):
        verify_fully_loaded_on_gpu(overflowed, spec)
    with pytest.raises(RuntimeError, match="resident at context 131072"):
        verify_context_length(overflowed, spec, 32768)


def test_identity_verification_pins_the_digest():
    spec = PRODUCERS[1]
    verify_identity({"models": {spec.model: spec.digest}}, spec)
    with pytest.raises(RuntimeError, match="digest mismatch"):
        verify_identity({"models": {spec.model: "moving-tag"}}, spec)
