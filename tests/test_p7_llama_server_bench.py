"""Tests hors modèle du parcours conditionnel llama-server."""
from contextlib import contextmanager
from pathlib import Path

from scripts.p7_llama_server_bench import (
    LLAMA_BUILD,
    LLAMA_COMMIT,
    LlamaModel,
    preflight,
    server_command,
)


def test_llama_server_protocol_constants_are_frozen():
    assert LLAMA_BUILD == 10405
    assert LLAMA_COMMIT == "e79e4bf66"


def test_server_command_disables_reasoning_and_uses_full_context():
    executable = Path("C:/bench/llama-server.exe")
    model = LlamaModel("judge", "digest", Path("C:/models/judge.gguf"))
    command = server_command(executable, model, 18080)

    assert command[0] == str(executable)
    assert command[command.index("--model") + 1] == str(model.gguf)
    assert command[command.index("--alias") + 1] == "judge"
    assert command[command.index("--ctx-size") + 1] == "32768"
    assert command[command.index("--gpu-layers") + 1] == "all"
    assert command[command.index("--reasoning") + 1] == "off"
    assert command[command.index("--port") + 1] == "18080"


def test_preflight_records_one_model_failure_and_continues(monkeypatch, tmp_path):
    executable = tmp_path / "llama-server.exe"
    first = tmp_path / "first.gguf"
    second = tmp_path / "second.gguf"
    executable.write_bytes(b"server")
    first.write_bytes(b"first")
    second.write_bytes(b"second")
    models = (
        LlamaModel("first", "digest-1", first),
        LlamaModel("second", "digest-2", second),
    )

    monkeypatch.setattr(
        "scripts.p7_llama_server_bench.verify_server_binary",
        lambda _: {"version": "test"},
    )

    @contextmanager
    def fake_running_server(_, model, *__):
        if model.name == "first":
            raise RuntimeError("unsupported metadata")
        yield "http://localhost", {"health": {"status": "ok"}}

    monkeypatch.setattr(
        "scripts.p7_llama_server_bench.running_server", fake_running_server
    )
    result = preflight(executable, models, 18080, 5, tmp_path / "logs")

    assert result["compatible"] is False
    assert result["models"]["first"]["compatible"] is False
    assert result["models"]["first"]["error"].startswith("RuntimeError:")
    assert result["models"]["second"]["compatible"] is True
