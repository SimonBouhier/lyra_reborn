"""Contrôle local explicite de l'adaptateur ; modèle installé obligatoire, aucun pull."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
from datetime import datetime, timezone
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.chat_backend import OllamaChatAdapter, BackendCompatibilityError
from app.dialogue import DialogueConversation, default_profile
from app.dialogue_store import DialogueStore
from app.requests import RequestService
from app.session import SessionBook
from core.llm import OllamaClient


def check(model):
    output = ROOT / 'data/runs/p6-conversation' / ('live-' + uuid4().hex)
    output.mkdir(parents=True, exist_ok=False)
    report = {'started_utc': datetime.now(timezone.utc).isoformat(), 'model_requested': model,
              'scope': 'Synthetic local integration check; not a model-quality evaluation or a P7 campaign.',
              'expected': ['completed dialogue requests with usage', 'latest declared correction in recalled context',
                           'oversized input refused by server without truncation'], 'checks': []}
    print(str(output), flush=True)
    try:
        adapter = OllamaChatAdapter()
        client = OllamaClient(model=model, timeout=90, think=False)
        report['engine'] = adapter.freeze(client)
        store = DialogueStore(output / 'dialogue.sqlite3')
        service = RequestService(SessionBook(storage=store, conversation_factory=DialogueConversation), store,
                                 voice_factory=lambda: (client, model), chat_adapter=adapter)

        def ask(rid, text, sid=None):
            service.accept(rid, {'texte': text, 'session': sid, 'voix': True})
            row = service.run(rid)
            report['checks'].append({'request': rid, 'row': row})
            assert row['statut'] == 'termine', row.get('erreur')
            assert row['reponse']['usage']['prompt_tokens'] > 0
            print(rid + ': ' + row['reponse']['reponse'], flush=True)
            return row

        first = ask('source', 'Notre rendez-vous est mardi. Réponds simplement : noté.')
        store.correct('correction', 'source', 'user', 'Notre rendez-vous est jeudi.', None)
        ask('suite', 'Quel est le jour corrigé du rendez-vous ? Réponds en une phrase.', first['session'])
        destination = service.book.create()
        store.save(destination.to_state())
        store.add_recall('rappel', destination.id, 'source', 'user')
        recalled = ask('rappel-demande', 'Quel jour indique le passage rappelé après correction ?', destination.id)
        assert recalled['reponse']['context']['recalls'][0]['correction']['id'] == 'correction'
        assert not recalled['reponse']['context']['history']
        try:
            adapter.chat(report['engine'], [{'role': 'user', 'content': 'mot ' * 20000}], default_profile())
        except BackendCompatibilityError as exc:
            report['oversized_error'] = str(exc)
            assert '400' in str(exc) and ('context' in str(exc).lower() or 'length' in str(exc).lower()), str(exc)
        else:
            raise AssertionError('Le serveur a accepté une entrée surdimensionnée malgré truncate=false.')
        report['engine_after'] = adapter.freeze(client)
        assert report['engine_after'] == report['engine']
        report['status'] = 'passed'
    except Exception as exc:
        report['status'] = 'failed'
        report['error'] = {'type': type(exc).__name__, 'message': str(exc)}
        raise
    finally:
        report['completed_utc'] = datetime.now(timezone.utc).isoformat()
        report['files'] = [{'path': str(p.relative_to(ROOT)), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
                           for p in [Path(__file__), ROOT / 'app/chat_backend.py', ROOT / 'app/context.py',
                                     ROOT / 'app/dialogue.py', ROOT / 'app/dialogue_store.py', ROOT / 'app/requests.py']]
        (output / 'verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', required=True, help='Nom exact déjà présent dans Ollama ; aucune substitution.')
    check(parser.parse_args().model)
