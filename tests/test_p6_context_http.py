from fastapi.testclient import TestClient
import app.main as main
from tests.test_p6_context import runtime, ask


def test_passage_correction_recall_navigation_and_context_are_connected(tmp_path, monkeypatch):
    service, chat = runtime(tmp_path / 'http.db')
    monkeypatch.setattr(main, 'book', service.book)
    monkeypatch.setattr(main, 'request_service', service)
    with TestClient(main.app) as client:
        source = ask(service, 'source', 'Le jour est mardi.')
        new = client.post('/api/conversations', json={'conversation': 'destination'})
        assert new.status_code == 200
        assert client.post('/api/conversations', json={'conversation': 'destination'}).json() == new.json()
        assert len(client.get('/api/sessions').json()['sessions']) == 2
        passage = client.get('/api/passages/source/user').json()
        assert passage['text'] == 'Le jour est mardi.' and passage['correction'] is None
        payload = {'correction': 'c1', 'texte': 'Le jour est jeudi.', 'precedente': None}
        assert client.post('/api/passages/source/user/corrections', json=payload).status_code == 200
        assert client.get('/api/passages/source/user').json()['revisions'][0]['id'] == 'c1'
        assert client.post('/api/session/destination/rappels', json={'rappel': 'r1', 'source': 'source', 'role': 'user'}).status_code == 200
        reply = ask(service, 'question', 'Quel jour ?', 'destination')
        assert reply['statut'] == 'termine'
        assert 'jeudi' in str(reply['reponse']['context']['messages'])
        assert client.get('/api/session/destination/rappels').json()['rappels'][0]['id'] == 'r1'
        assert client.post('/api/session/destination/rappels/r1/retirer').status_code == 200
        assert client.get('/api/session/destination/rappels').json()['rappels'] == []
