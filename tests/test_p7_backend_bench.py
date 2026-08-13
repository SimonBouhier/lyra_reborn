"""Banc des backends P7 : tests hors modèle et sans corpus."""
from __future__ import annotations

import json

import pytest

from eval.p7_judge_backend import (
    JudgeBackendRequest,
    OllamaJudgeBackend,
    OpenAICompatibleJudgeBackend,
    canonical_payload_bytes,
)
from eval.p7_judge_prompt import judge_prompt_with_contract
from eval.p7_v7_judge import judgment_schema
from eval.p7_v9_judge import wire_judgment_schema
from scripts.p7_backend_bench import (
    EXPECTED_CALLS,
    PROTOCOL_COMMIT,
    _acquire_lock,
    _diagnose_invalid,
    bench_cells,
)


def _request():
    pack = bench_cells()[0].pack
    return pack, JudgeBackendRequest(
        model="judge",
        prompt=judge_prompt_with_contract(pack),
        full_schema=judgment_schema(pack),
        wire_schema=wire_judgment_schema(pack),
    )


def test_protocol_and_four_development_cells_are_frozen():
    assert PROTOCOL_COMMIT == "69e34deab012895caf4f0b377d8622f942febb86"
    cells = bench_cells()
    assert EXPECTED_CALLS == 16
    assert [(item.cell_id, item.expected_preference) for item in cells] == [
        ("TRANSPORT_PARITY", "TIE"),
        ("SEMANTIC_DOMINANCE", "B"),
        ("STYLE_PARITY", "TIE"),
        ("INJECTION_RESISTANCE", "B"),
    ]


def test_prompt_places_full_contract_before_untrusted_evidence():
    pack, request = _request()
    prompt = request.prompt
    contract_at = prompt.index("<JUDGE_CONTRACT_JSON>")
    evidence_at = prompt.index("<EVIDENCE_PACK_JSON>")
    assert contract_at < evidence_at
    assert json.dumps(
        judgment_schema(pack), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ) in prompt
    assert "Each claim must be a substantive complete statement" in prompt
    assert "cite candidate A, candidate B" in prompt


def test_ollama_modes_change_only_the_format_constraint():
    _, request = _request()
    plain = OllamaJudgeBackend("http://localhost", "JSON_ONLY_PROMPTED").build_payload(request)
    wire = OllamaJudgeBackend("http://localhost", "WIRE_SCHEMA_PROMPTED").build_payload(request)
    assert plain["format"] == "json"
    assert wire["format"] == request.wire_schema
    assert plain["think"] is wire["think"] is False
    plain["format"] = wire["format"]
    assert plain == wire


def test_openai_backend_uses_the_full_schema_without_ollama_translation():
    _, request = _request()
    payload = OpenAICompatibleJudgeBackend("http://localhost:8080").build_payload(request)
    wrapped = payload["response_format"]
    assert wrapped["type"] == "json_schema"
    assert wrapped["json_schema"]["strict"] is True
    assert wrapped["json_schema"]["schema"] == request.full_schema
    assert payload["messages"] == [{"role": "user", "content": request.prompt}]


class _FakeResponse:
    status_code = 200

    def __init__(self, body):
        self._body = body
        self.content = json.dumps(body, separators=(",", ":")).encode("utf-8")

    def raise_for_status(self):
        return None

    def json(self):
        return self._body


@pytest.mark.parametrize(
    ("backend", "body", "expected_url", "expected_text"),
    [
        (
            OllamaJudgeBackend("http://localhost:11434", "JSON_ONLY_PROMPTED"),
            {"response": "{}", "thinking": "", "done_reason": "stop"},
            "http://localhost:11434/api/generate",
            "{}",
        ),
        (
            OpenAICompatibleJudgeBackend("http://localhost:8080"),
            {
                "choices": [
                    {"message": {"content": "{}"}, "finish_reason": "stop"}
                ]
            },
            "http://localhost:8080/v1/chat/completions",
            "{}",
        ),
    ],
)
def test_generate_sends_the_exact_archived_payload(
    monkeypatch, backend, body, expected_url, expected_text
):
    _, request = _request()
    captured = {}

    def fake_post(url, *, data, headers, timeout):
        captured.update(url=url, data=data, headers=headers, timeout=timeout)
        return _FakeResponse(body)

    monkeypatch.setattr("eval.p7_judge_backend.requests.post", fake_post)
    response = backend.generate(request, timeout=17)

    assert captured["url"] == expected_url
    assert captured["data"] == canonical_payload_bytes(backend, request)
    assert captured["headers"]["Content-Type"] == "application/json"
    assert captured["timeout"] == 17
    assert response.text == expected_text


def test_invalid_diagnostics_preserve_pydantic_paths_and_codes():
    pack = bench_cells()[0].pack
    raw = json.dumps({"preference": "TIE", "rationale": "short", "criteria": []})
    errors = _diagnose_invalid(raw, pack)
    assert {tuple(item["path"]) for item in errors} >= {("rationale",), ("criteria",)}
    assert {item["type"] for item in errors} >= {"string_too_short", "too_short"}


def test_bench_lock_is_exclusive(tmp_path):
    first = _acquire_lock(tmp_path, "first")
    assert first.exists()
    with pytest.raises(FileExistsError):
        _acquire_lock(tmp_path, "replay")
