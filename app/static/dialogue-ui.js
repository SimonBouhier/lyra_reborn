/* Contrôles du dialogue ; tous les contenus de journal sont rendus en texte. */
let passageOuvert = null;
let chargementPassage = 0;
const elementDialogue = id => document.getElementById(id);

function boutonDialogue(parent, label, action) {
  const button = document.createElement("button");
  button.type = "button"; button.textContent = label;
  button.onclick = action; parent.appendChild(button); return button;
}

function ajouteActionsPassage(parent, row) {
  const actions = document.createElement("div"); actions.className = "actions-message";
  for (const [role, label] of [["user", "Ton message"], ["assistant", "Réponse de Lyra"]]) {
    boutonDialogue(actions, label + " · corriger / rappeler", () => ouvrirPassage(row.demande, role));
  }
  boutonDialogue(actions, "Voir le contexte", () => {
    elementDialogue("contexte-contenu").textContent = JSON.stringify(row.tentatives, null, 2);
    elementDialogue("contexte-dialogue").showModal();
  });
  parent.appendChild(actions);
}

async function actualiseConversations() {
  if (typeof journal === "undefined" || !journal) return;
  const current = vue;
  try {
    const data = await journal.call("/api/sessions");
    if (vue !== current) return;
    const select = elementDialogue("conversations"); select.replaceChildren();
    for (const row of data.sessions) {
      const option = document.createElement("option"); option.value = row.id;
      option.textContent = row.id.slice(0, 12) + " · " + row.tours + " échanges · " + row.moteur;
      option.selected = row.id === session; select.appendChild(option);
    }
  } catch (err) { if (vue === current) echo.textContent = err.message; }
}

async function ouvrirConversation() {
  const id = elementDialogue("conversations").value;
  if (!id) return;
  nouvelleVue(id); await reprendreSession();
}

async function ouvrirPassage(rid, role) {
  const loading = ++chargementPassage;
  try {
    const [passage, list] = await Promise.all([
      journal.call("/api/passages/" + rid + "/" + role), journal.call("/api/sessions")]);
    if (loading !== chargementPassage) return;
    passageOuvert = passage;
    elementDialogue("passage-source").textContent = "Conversation " + passage.session + " · message " + rid + " · " + role;
    elementDialogue("passage-original").textContent = passage.text;
    elementDialogue("passage-revisions").textContent = passage.revisions.length
      ? passage.revisions.map(c => "Correction " + c.id + " : " + c.text).join("\n")
      : "Aucune correction enregistrée.";
    const draft = window.localStorage.getItem("lyra.correction.v1." + rid + "." + role);
    elementDialogue("passage-correction").value = draft ? JSON.parse(draft).texte : passage.correction?.text || "";
    const select = elementDialogue("rappel-destination"); select.replaceChildren();
    const fresh = document.createElement("option"); fresh.value = "__new__";
    fresh.textContent = "Nouvelle conversation"; select.appendChild(fresh);
    for (const row of list.sessions) {
      const option = document.createElement("option"); option.value = row.id;
      option.textContent = row.id.slice(0, 12) + " · " + row.moteur;
      select.appendChild(option);
    }
    elementDialogue("passage-statut").textContent = "";
    if (!elementDialogue("passage-dialogue").open) elementDialogue("passage-dialogue").showModal();
  } catch (err) { echo.textContent = err.message; }
}

async function enregistrerCorrection() {
  const p = passageOuvert;
  if (!p) return;
  const text = elementDialogue("passage-correction").value;
  if (!text.trim()) return;
  const key = "lyra.correction.v1." + p.request + "." + p.role;
  try {
    const saved = window.localStorage.getItem(key);
    let body = saved ? JSON.parse(saved) : null;
    if (!body || body.texte !== text) body = {correction: window.crypto.randomUUID(), texte: text, precedente: p.correction?.id || null};
    window.localStorage.setItem(key, JSON.stringify(body));
    await journal.call("/api/passages/" + p.request + "/" + p.role + "/corrections", body);
    window.localStorage.removeItem(key);
    if (passageOuvert === p) {
      await ouvrirPassage(p.request, p.role);
      elementDialogue("passage-statut").textContent = "Correction enregistrée. Les tentatives déjà lancées gardent leur contexte initial.";
    }
    await actualiseRappels();
  } catch (err) {
    if (err.status === 409 && passageOuvert === p) {
      try {
        // Un refus explicite est différent d'un accusé perdu : relire la tête,
        // conserver le texte, puis attendre un nouveau clic avant de proposer.
        const latest = await journal.call("/api/passages/" + p.request + "/" + p.role);
        window.localStorage.setItem(key, JSON.stringify({correction: window.crypto.randomUUID(),
          texte: text, precedente: latest.correction?.id || null}));
        await ouvrirPassage(p.request, p.role);
        elementDialogue("passage-statut").textContent = "Une autre correction a été enregistrée. Relis les versions ci-dessus ; ton texte est conservé. Un nouveau clic proposera ta correction après cette version.";
        return;
      } catch (_) { /* conserver la copie existante si la relecture échoue */ }
    }
    elementDialogue("passage-statut").textContent = err.message + " La copie locale de la correction est conservée.";
  }
}

async function enregistrerRappel() {
  const p = passageOuvert;
  if (!p) return;
  const selected = elementDialogue("rappel-destination").value;
  const key = "lyra.rappel.v1." + p.request + "." + p.role + "." + selected;
  try {
    const saved = window.localStorage.getItem(key);
    const action = saved ? JSON.parse(saved) : {destination: selected === "__new__" ? window.crypto.randomUUID() : selected,
      newConversation: selected === "__new__", body: {rappel: window.crypto.randomUUID(), source: p.request, role: p.role}};
    window.localStorage.setItem(key, JSON.stringify(action));
    if (action.newConversation) await journal.call("/api/conversations", {conversation: action.destination});
    await journal.call("/api/session/" + action.destination + "/rappels", action.body);
    window.localStorage.removeItem(key);
    elementDialogue("passage-statut").textContent = "Rappel enregistré dans " + action.destination + ". Ouvre cette conversation pour poursuivre.";
    await actualiseConversations(); await actualiseRappels();
  } catch (err) { elementDialogue("passage-statut").textContent = err.message; }
}

async function actualiseRappels() {
  const area = elementDialogue("rappels-actifs"); area.replaceChildren();
  if (!session || !journal) return;
  const origin = vue, sid = session;
  try {
    const data = await journal.call("/api/session/" + sid + "/rappels");
    if (vue !== origin || session !== sid) return;
    for (const row of data.rappels) {
      const p = document.createElement("p");
      p.textContent = "Rappel : " + row.passage.text.slice(0, 140) + (row.passage.correction ? " · correction : " + row.passage.correction.text : "");
      boutonDialogue(p, "Retirer du contexte", async () => {
        try {
          await journal.call("/api/session/" + sid + "/rappels/" + row.id + "/retirer", {});
          if (vue === origin) await actualiseRappels();
        } catch (err) { if (vue === origin) echo.textContent = err.message; }
      });
      area.appendChild(p);
    }
  } catch (err) { if (vue === origin) echo.textContent = err.message; }
}

window.addEventListener("DOMContentLoaded", actualiseConversations);
