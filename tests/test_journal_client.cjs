const test = require('node:test');
const assert = require('node:assert/strict');
const {JournalClient} = require('../app/static/journal-client.js');

function storage() {
  const values = new Map();
  return {get length() { return values.size; }, key: i => [...values.keys()][i],
          getItem: k => values.get(k), setItem: (k,v) => values.set(k,v), removeItem: k => values.delete(k)};
}
const response = row => ({ok: true, json: async () => row});

test('a lost first acknowledgement reuses the exact payload after reload', async () => {
  const local = storage();
  const bodies = [];
  let dropped = false;
  const fetch = async (path, options) => {
    const body = JSON.parse(options.body);
    if (path === '/api/demandes') {
      bodies.push(body);
      if (!dropped) { dropped = true; throw Error('réponse réseau perdue'); }
      return response({demande: body.demande, session: 'server-session', statut: 'en_attente'});
    }
    return response({demande: 'client-id', session: 'server-session', statut: 'termine', reponse: {reponse: 'Texte exact'}});
  };
  const first = new JournalClient({storage: local, fetch, uuid: () => 'client-id'});
  const entry = first.prepare('  Texte exact  ', null, false);
  await assert.rejects(first.continue(entry));
  const reloaded = new JournalClient({storage: local, fetch, uuid: () => { throw Error('nouvelle identité interdite'); }});
  const resumed = reloaded.pending()[0];
  const row = await reloaded.continue(resumed);
  assert.deepEqual(bodies[0], bodies[1]);
  assert.equal(row.statut, 'termine');
  reloaded.acknowledge(resumed, row);
  assert.equal(local.length, 0);
});

test('an uncertain retry retains its token and is not replaced by a new attempt', async () => {
  const local = storage();
  const tokens = [];
  let next = 0;
  const client = new JournalClient({storage: local, uuid: () => 'id-' + (++next), fetch: async (path, options) => {
    if (path === '/api/demandes') return response({demande: 'id-1', session: 'sid', statut: 'echoue'});
    tokens.push(JSON.parse(options.body).relance);
    if (tokens.length === 1) throw Error('réponse perdue');
    return response({demande: 'id-1', session: 'sid', statut: 'termine'});
  }});
  const entry = client.prepare('Texte', null, false);
  await assert.rejects(client.retry(entry));
  await client.continue(client.pending()[0]);
  assert.deepEqual(tokens, ['id-2', 'id-2']);
});

test('a recorded failure is not retried by continue; local storage failure prevents sending', async () => {
  let calls = 0;
  const client = new JournalClient({storage: storage(), uuid: () => 'id', fetch: async () => {
    calls++; return response({demande: 'id', session: 'sid', statut: 'echoue'});
  }});
  const entry = client.prepare('Texte', null, false);
  assert.equal((await client.continue(entry)).statut, 'echoue');
  assert.equal(calls, 1);
  client.storage.setItem = () => { throw Error('quota'); };
  assert.throws(() => client.prepare('Autre', null, false));
  assert.equal(calls, 1);
});
