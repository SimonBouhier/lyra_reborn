const test = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const path = require('node:path');
const {JournalClient} = require('../app/static/journal-client.js');

class Element {
  constructor(tag = 'div') { this.tag = tag; this.children = []; this.ownText = ''; this.value = ''; }
  set textContent(value) { this.ownText = value; this.children = []; }
  get textContent() { return this.ownText + this.children.map(x => x.textContent).join(''); }
  appendChild(child) {
    if (child.parent) child.parent.children = child.parent.children.filter(x => x !== child);
    child.parent = this; this.children.push(child); return child;
  }
  append(...children) { children.forEach(x => this.appendChild(x)); }
  replaceChildren() { this.children.forEach(x => x.parent = null); this.children = []; this.ownText = ''; }
  addEventListener() {}
  focus() {}
  showModal() { this.open = true; }
  close() { this.open = false; }
}

function setup(fetch, dialogue = false) {
  const values = new Map(), elements = new Map();
  const storage = {get length() { return values.size; }, key: i => [...values.keys()][i],
    getItem: k => values.get(k) ?? null, setItem: (k,v) => values.set(k,v), removeItem: k => values.delete(k)};
  const document = {createElement: tag => new Element(tag), getElementById: id => {
    if (!elements.has(id)) elements.set(id, new Element());
    return elements.get(id);
  }};
  let identities = 0;
  const context = vm.createContext({JournalClient, document, window: {
    localStorage: storage, fetch, crypto: {randomUUID: () => dialogue ? 'client-' + (++identities) : 'client-id'}, addEventListener() {}
  }});
  if (dialogue) vm.runInContext(fs.readFileSync(path.join(__dirname, '../app/static/dialogue-ui.js'), 'utf8'), context);
  vm.runInContext(fs.readFileSync(path.join(__dirname, '../app/static/p6-ui.js'), 'utf8'), context);
  return {context, document, storage};
}

for (const phase of ['acceptation', 'generation']) {
  test('a late ' + phase + ' cannot replace the newly selected conversation', async () => {
    let release, entered;
    const ready = new Promise(resolve => entered = resolve);
    const pause = new Promise(resolve => release = resolve);
    let completed = false, calls = 0;
    const row = () => ({demande: 'client-id', session: 'originale', position: 1, texte: 'Texte initial',
      statut: completed ? 'termine' : 'en_attente', reponse: completed ? {reponse: 'Réponse tardive'} : null});
    const fetch = async (url) => {
      if (url === '/api/demandes') {
        if (phase === 'acceptation' && !completed) { entered(); await pause; }
      } else {
        calls++;
        if (phase === 'generation') { entered(); await pause; }
        completed = true;
      }
      return {ok: true, json: async () => row()};
    };
    const {context, document, storage} = setup(fetch);
    document.getElementById('parole').value = 'Texte initial';
    const sending = context.envoyer(false);
    await ready;
    context.nouvelleSession();
    assert.equal(document.getElementById('envoyer').disabled, false);
    release(); await sending;
    assert.equal(storage.getItem('lyra.session.v1'), null);
    assert.ok(!document.getElementById('fil').textContent.includes('Réponse tardive'));
    const button = document.getElementById('envois').children.find(x => x.tag === 'button');
    assert.ok(button.textContent.includes('Ouvrir'));
    await button.onclick();
    assert.equal(storage.getItem('lyra.session.v1'), 'originale');
    assert.ok(document.getElementById('fil').textContent.includes('Réponse tardive'));
    assert.equal(calls, 1);
  });
}

test('loading older pages after a new answer preserves request order', () => {
  const {context, document} = setup(async () => { throw Error('aucun réseau prévu'); });
  const row = position => ({demande: 'r-' + position, position, texte: 'Texte ' + position,
    statut: 'termine', reponse: {reponse: 'Réponse ' + position}});
  context.afficheDemande(row(1));
  context.afficheDemande(row(53));
  context.afficheDemande(row(51));
  const text = document.getElementById('fil').textContent;
  assert.ok(text.indexOf('Réponse 51') < text.indexOf('Réponse 53'));
});

for (const incident of ['lost acknowledgement', 'concurrent correction']) {
  test('a correction recovers from ' + incident + ' only on a new explicit click', async () => {
    let correction = null, postCount = 0;
    const bodies = [];
    const {context, document, storage} = setup(async (url, options) => {
      if (url === '/api/sessions') return {ok: true, json: async () => ({sessions: []})};
      if (options.method === 'POST') {
        const body = JSON.parse(options.body); bodies.push(body); postCount++;
        if (postCount === 1) {
          if (incident === 'lost acknowledgement') {
            correction = {id: body.correction, text: body.texte};
            throw new Error('network interrupted');
          }
          correction = {id: 'other', text: 'Version concurrente'};
          return {ok: false, status: 409, json: async () => ({detail: 'Conflit'})};
        }
        correction = {id: body.correction, text: body.texte};
        return {ok: true, json: async () => correction};
      }
      return {ok: true, json: async () => ({session: 'a', request: 'r1', role: 'user',
        text: 'Original', correction, revisions: correction ? [correction] : []})};
    }, true);
    await context.ouvrirPassage('r1', 'user');
    document.getElementById('passage-correction').value = 'Mon texte corrigé';
    await context.enregistrerCorrection();
    assert.equal(postCount, 1);
    assert.ok(storage.getItem('lyra.correction.v1.r1.user'));
    if (incident === 'concurrent correction') {
      assert.ok(document.getElementById('passage-revisions').textContent.includes('Version concurrente'));
      assert.equal(document.getElementById('passage-correction').value, 'Mon texte corrigé');
    }
    await context.enregistrerCorrection();
    assert.equal(postCount, 2);
    if (incident === 'lost acknowledgement') assert.deepEqual(bodies[0], bodies[1]);
    else {
      assert.equal(bodies[1].precedente, 'other');
      assert.notEqual(bodies[0].correction, bodies[1].correction);
    }
    assert.equal(storage.getItem('lyra.correction.v1.r1.user'), null);
  });
}

test('a busy session still restores its durable request when the local copy is missing', async () => {
  const payload = {demande: 'en-cours', texte: 'Texte conservé', session: 'active', voix: false};
  const {context, document, storage} = setup(async url => {
    if (url === '/api/session/active') {
      return {ok: false, status: 409, json: async () => ({detail: 'Conversation occupée.'})};
    }
    assert.equal(url, '/api/session/active/journal?apres=0');
    return {ok: true, json: async () => ({curseur: 1, demandes: [{
      demande: payload.demande, session: 'active', position: 1, texte: payload.texte,
      intention: {texte: payload.texte, session: 'active', voix: false},
      statut: 'en_cours', reponse: null, tentatives: [{}]
    }]})};
  });
  context.nouvelleVue('active');
  await context.reprendreSession();
  assert.ok(document.getElementById('fil').textContent.includes('Texte conservé'));
  assert.ok(document.getElementById('fil').textContent.includes('Calcul en cours'));
  assert.deepEqual(JSON.parse(storage.getItem('lyra.demande.v1.en-cours')).payload, payload);
});
