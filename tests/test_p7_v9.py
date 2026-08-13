"""Contrat instrumental P7 V9, sans appel Ollama ni donnée de campagne."""
from __future__ import annotations

import json

import pytest

from eval.p7_evidence import canonical_json_bytes, pack_sha256
from eval.p7_v7_judge import JudgeContractError, judgment_schema, validate_judgment
from eval.p7_v7_q0 import q0_fixtures
from eval.p7_v9_judge import (
    WIRE_ONLY_REMOVED_KEYWORDS,
    qminus1_evidence_pack,
    wire_judgment_schema,
)
from scripts.p7_v9 import (
    PREREG_FREEZE_COMMIT,
    _acquire_phase_lock,
    _judge_payload,
    _validate_response_body,
    run,
    run_qminus1,
)


def _collect_keys(value):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from _collect_keys(item)
    elif isinstance(value, list):
        for item in value:
            yield from _collect_keys(item)


def _assert_only_string_bounds_removed(full, wire):
    if isinstance(full, dict):
        assert isinstance(wire, dict)
        assert set(full) - set(wire) <= WIRE_ONLY_REMOVED_KEYWORDS
        assert set(wire) == set(full) - (set(full) & WIRE_ONLY_REMOVED_KEYWORDS)
        for key in wire:
            _assert_only_string_bounds_removed(full[key], wire[key])
    elif isinstance(full, list):
        assert isinstance(wire, list)
        assert len(full) == len(wire)
        for left, right in zip(full, wire, strict=True):
            _assert_only_string_bounds_removed(left, right)
    else:
        assert full == wire


def _valid_payload(pack):
    span = pack.source.segments[0].source_span_id
    names = ["fidelity", "uncertainty", "salience", "contradiction", "utility", "economy"]
    criteria = []
    for index, name in enumerate(names):
        criteria.append(
            {
                "criterion": name,
                "direction": "TIE",
                "claim": f"Both candidates remain equivalent for {name} according to the cited source and turns.",
                "source_span_ids": [span] if index == 0 else [],
                "turn_refs": ["A.T1", "B.T1"] if index == 0 else ["A.T2", "B.T2"],
            }
        )
    return {
        "preference": "TIE",
        "rationale": (
            "Both complete trajectories preserve the same source-grounded proposition, calibrated uncertainty, "
            "and next action. Their wording differs without creating a substantive advantage, and each candidate "
            "is checked through explicit source and turn references rather than formatting or confidence alone."
        ),
        "criteria": criteria,
    }


def test_runner_targets_the_frozen_v9_commit():
    assert PREREG_FREEZE_COMMIT == "882f10cc04c7d470191d18a10df8063cd0b07c71"


def test_wire_schema_removes_only_string_bounds_recursively():
    pack = qminus1_evidence_pack()
    full = judgment_schema(pack)
    wire = wire_judgment_schema(pack)
    assert {"minLength", "maxLength"}.issubset(set(_collect_keys(full)))
    assert not (WIRE_ONLY_REMOVED_KEYWORDS & set(_collect_keys(wire)))
    assert "minItems" in set(_collect_keys(wire))
    assert "maxItems" in set(_collect_keys(wire))
    _assert_only_string_bounds_removed(full, wire)


def test_wire_compatibility_does_not_relax_pydantic_acceptance():
    pack = qminus1_evidence_pack()
    payload = _valid_payload(pack)
    payload["rationale"] = "too short"
    payload["criteria"][0]["claim"] = "short"
    with pytest.raises(JudgeContractError, match="closed schema"):
        validate_judgment(json.dumps(payload), pack)


def test_payload_freezes_thinking_off_and_uses_wire_schema():
    pack = qminus1_evidence_pack()
    payload = _judge_payload("qwen3.6:27b", pack)
    assert payload["think"] is False
    assert payload["stream"] is False
    assert payload["format"] == wire_judgment_schema(pack)
    assert payload["options"] == {"temperature": 0, "num_predict": 2048, "num_ctx": 32768}


def test_response_channel_is_exclusive_and_thinking_never_becomes_verdict():
    pack = qminus1_evidence_pack()
    raw = json.dumps(_valid_payload(pack))
    assert _validate_response_body({"response": raw, "thinking": ""}, pack).preference.value == "TIE"
    with pytest.raises(JudgeContractError, match="thinking"):
        _validate_response_body({"response": raw, "thinking": raw}, pack)
    with pytest.raises(JudgeContractError, match="empty judge response"):
        _validate_response_body({"response": "", "thinking": ""}, pack)


def test_qminus1_pack_is_deterministic_and_independent_of_q0():
    first = qminus1_evidence_pack()
    second = qminus1_evidence_pack()
    assert canonical_json_bytes(first) == canonical_json_bytes(second)
    assert pack_sha256(first) == pack_sha256(second)
    q0_sources = {fixture.source for fixture in q0_fixtures()}
    joined_source = " ".join(item.text for item in first.source.segments)
    assert joined_source not in q0_sources
    assert not any(fixture.fixture_id.encode() in canonical_json_bytes(first) for fixture in q0_fixtures())


def test_v9_phase_locks_are_separate_and_exclusive(tmp_path):
    qminus1 = _acquire_phase_lock(tmp_path, "Q-1", "first")
    q0 = _acquire_phase_lock(tmp_path, "Q0", "second")
    assert qminus1 != q0
    with pytest.raises(FileExistsError):
        _acquire_phase_lock(tmp_path, "Q-1", "replay")
    with pytest.raises(FileExistsError):
        _acquire_phase_lock(tmp_path, "Q0", "replay")


def test_run_never_opens_q0_when_qminus1_fails(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr("scripts.p7_v9.run_qminus1", lambda *args: calls.append("Q-1") or 2)
    monkeypatch.setattr("scripts.p7_v9.run_q0", lambda *args: calls.append("Q0") or 0)
    assert run("http://invalid", 1, tmp_path) == 2
    assert calls == ["Q-1"]


def test_qminus1_simulated_transport_writes_two_complete_calls(monkeypatch, tmp_path):
    pack = qminus1_evidence_pack()
    response_body = {
        "response": json.dumps(_valid_payload(pack)),
        "done": True,
        "done_reason": "stop",
        "eval_count": 240,
    }
    response_raw = json.dumps(response_body, separators=(",", ":")).encode()
    requests_seen = []

    class FakeResponse:
        content = response_raw

        @staticmethod
        def raise_for_status():
            return None

        @staticmethod
        def json():
            return response_body

    def fake_post(url, *, data, headers, timeout):
        requests_seen.append(json.loads(data))
        assert url == "http://ollama.test/api/generate"
        assert headers == {"Content-Type": "application/json"}
        assert timeout == 7
        return FakeResponse()

    runtime = {
        "python": "3.14.7",
        "pydantic": "2.13.4",
        "ollama": "0.32.9",
        "models": {},
    }
    monkeypatch.setattr("scripts.p7_v9.requests.post", fake_post)
    monkeypatch.setattr("scripts.p7_v9._runtime_manifest", lambda *_args: runtime)

    assert run_qminus1("http://ollama.test", 7, tmp_path) == 0
    assert len(requests_seen) == 2
    assert all(item["think"] is False and item["stream"] is False for item in requests_seen)
    assert all(item["format"] == wire_judgment_schema(pack) for item in requests_seen)

    run_dirs = [item for item in tmp_path.iterdir() if item.is_dir()]
    assert len(run_dirs) == 1
    run_dir = run_dirs[0]
    assert len(list((run_dir / "calls").glob("*.request.json"))) == 2
    assert len(list((run_dir / "calls").glob("*.response.json"))) == 2
    events = [json.loads(line) for line in (run_dir / "journal.jsonl").read_text().splitlines()]
    assert [item["event"] for item in events].count("call_started") == 2
    assert [item["event"] for item in events].count("call_finished") == 2
    summary = json.loads((run_dir / "summary.json").read_text())
    assert summary["status"] == "Q_MINUS_1_PASSED"
    assert summary["h9"] == "UNTESTED"
    assert summary["calls_planned"] == summary["calls_recorded"] == summary["valid"] == 2
