"""P0 — le correctif options{} : les params de génération sont imbriqués."""
from core.llm import build_ollama_payload, EchoClient


def test_options_are_nested_not_at_root():
    opts = {"temperature": 0.9, "top_p": 0.8, "repeat_penalty": 1.2, "num_predict": 512}
    payload = build_ollama_payload("m", "hello", opts)
    # options bien imbriquées
    assert payload["options"] == opts
    # et surtout PAS étalées à la racine (le bug du canon conscious)
    for k in opts:
        assert k not in payload
    assert set(payload) == {"model", "prompt", "stream", "options"}


def test_echo_client_reflects_options():
    e = EchoClient()
    out = e.generate("prompt", {"temperature": 0.42, "top_p": 0.7,
                                "repeat_penalty": 1.1, "num_predict": 256})
    assert "temperature=0.42" in out


def test_structured_output_schema_is_at_payload_root():
    schema = {"type": "object", "properties": {"answer": {"type": "string"}}}
    payload = build_ollama_payload("m", "hello", {"temperature": 0.0},
                                   response_format=schema)
    assert payload["format"] == schema
    assert "format" not in payload["options"]
