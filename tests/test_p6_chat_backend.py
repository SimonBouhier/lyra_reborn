import pytest
from app.chat_backend import OllamaChatAdapter, BackendCompatibilityError
from app.dialogue import default_profile
from core.llm import OllamaClient


def test_adapter_pins_runtime_digest_and_preserves_roles(monkeypatch):
    adapter = OllamaChatAdapter()
    calls, version, digest = [], ['0.33.3'], ['digest1']

    def api(base, path, payload=None, timeout=5):
        calls.append((path, payload))
        if path == '/api/version': return {'version': version[0]}
        if path == '/api/tags': return {'models': [{'name': 'local:1', 'digest': digest[0]}]}
        return {'done': True, 'message': {'role': 'assistant', 'content': '  Réponse exacte\n'},
                'done_reason': 'stop', 'prompt_eval_count': 7, 'eval_count': 3}

    monkeypatch.setattr(adapter, '_json', api)
    engine = adapter.freeze(OllamaClient(model='local:1', think=False))
    messages = [{'role': 'user', 'content': 'Bonjour'}]
    result = adapter.chat(engine, messages, default_profile())
    assert result['text'] == '  Réponse exacte\n'
    payload = calls[-1][1]
    assert payload['messages'] == messages
    assert payload['truncate'] is False and payload['shift'] is False
    assert payload['options'] == default_profile()['options']
    for drift in ('version', 'digest'):
        calls.clear()
        if drift == 'version': version[0] = '0.33.4'
        else: version[0], digest[0] = '0.33.3', 'digest2'
        with pytest.raises(BackendCompatibilityError, match='changé'):
            adapter.chat(engine, messages, default_profile())
        assert '/api/chat' not in [c[0] for c in calls]


def test_unknown_runtime_is_not_upgraded_or_substituted(monkeypatch):
    adapter = OllamaChatAdapter()
    monkeypatch.setattr(adapter, '_json', lambda *args: {'version': '0.32.14'})
    with pytest.raises(BackendCompatibilityError, match='0.32.14'):
        adapter.freeze(OllamaClient(model='qwen3.8:27b', think=False))


def test_remote_backend_is_outside_this_local_adapter():
    with pytest.raises(BackendCompatibilityError, match='local'):
        OllamaChatAdapter._json('https://example.com', '/api/version')
