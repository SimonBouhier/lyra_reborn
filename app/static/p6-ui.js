const cleSession = "lyra.session.v1";
let session = null;
let vue = 0;
let curseur = 0;
const operations = new Set();
const affiches = new Set();
const groupes = new Map();
const fil = document.getElementById("fil");
const zone = document.getElementById("parole");
const echo = document.getElementById("echo");
let journal;
try {
  session = window.localStorage.getItem(cleSession);
  journal = new JournalClient({storage: window.localStorage,
    fetch: (...args) => window.fetch(...args), uuid: () => window.crypto.randomUUID()});
} catch (err) {
  echo.textContent = "Le navigateur ne peut pas conserver les envois avant leur enregistrement.";
}

function bulle(qui, texte, classe) {
  const d = document.createElement("div");
  d.className = "bulle " + (classe || "");
  const titre = document.createElement("div");
  titre.className = "qui"; titre.textContent = qui;
  const corps = document.createElement("div");
  corps.className = "txt"; corps.textContent = texte;
  d.append(titre, corps); fil.appendChild(d); fil.scrollTop = fil.scrollHeight;
  return d;
}

function afficheEtat(data) {
  document.getElementById("indicateurs-controle").hidden = !!data.profil;
  if (data.profil) {
    for (const id of ["rho", "deltar", "tauc", "kappa"]) document.getElementById(id).textContent = "—";
    document.getElementById("meta").textContent = "Conversation de référence · réglages fixes · graphe non injecté";
    document.getElementById("moteur").textContent = "Modèle : " + data.moteur;
    return;
  }
  const b = data.boutons_suivants || data.boutons || {};
  const fmt = x => x == null ? "—" : Number(x).toFixed(2);
  for (const [id, key] of [["rho", "rho"], ["deltar", "delta_r"], ["tauc", "tau_c"], ["kappa", "kappa"]]) {
    document.getElementById(id).textContent = fmt(b[key]);
  }
  const g = data.graphe || {}, m = data.memoire || {};
  document.getElementById("meta").textContent =
    "Graphe : " + (g.nodes || 0) + " concepts, " + (g.edges || 0) + " liens · Mémoire : "
    + (m.pouponniere || 0) + " actifs, " + (m.oubli || 0) + " différés, " + (m.compost || 0) + " au repos";
  if (data.moteur) document.getElementById("moteur").textContent = "Modèle : " + data.moteur;
}

function memoriseSession(id) {
  session = id;
  if (id === null) window.localStorage.removeItem(cleSession);
  else window.localStorage.setItem(cleSession, id);
}

function boutons() {
  for (const id of ["envoyer", "voix"]) document.getElementById(id).disabled = operations.has(vue);
}

function nouvelleVue(id) {
  vue++;
  memoriseSession(id);
  curseur = 0; affiches.clear(); groupes.clear(); fil.replaceChildren();
  document.getElementById("rappels-actifs").replaceChildren();
  document.getElementById("indicateurs-controle").hidden = true;
  document.getElementById("charger-journal").hidden = true;
  for (const id of ["rho", "deltar", "tauc", "kappa"]) document.getElementById(id).textContent = "—";
  document.getElementById("meta").textContent = "Conversations séparées · rappels choisis par toi";
  document.getElementById("moteur").textContent = "Modèle : à retrouver au prochain enregistrement.";
  echo.textContent = ""; boutons();
}

function nouvelleSession() {
  try {
    nouvelleVue(null);
    bulle("Lyra", "Nouvelle session. Les précédentes et les envois en attente restent conservés.", "lyra");
    zone.value = ""; zone.focus();
  } catch (err) { echo.textContent = err.message; }
}

function groupeDemande(id, position) {
  if (!groupes.has(id)) {
    const element = document.createElement("div");
    groupes.set(id, {element, position: Infinity}); fil.appendChild(element);
  }
  const groupe = groupes.get(id);
  if (position !== undefined) {
    groupe.position = position;
    for (const item of [...groupes.values()].sort((a, b) => a.position - b.position)) {
      fil.appendChild(item.element);
    }
  }
  return groupe.element;
}

function texteDemande(id, texte) {
  if (!affiches.has(id + ":texte")) {
    groupeDemande(id).appendChild(bulle("Toi", texte)); affiches.add(id + ":texte");
  }
}

function afficheDemande(row) {
  const groupe = groupeDemande(row.demande, row.position);
  texteDemande(row.demande, row.historique_importe?.prompt_absent ? "(Texte d'origine absent)" : row.texte);
  const key = row.demande + ":" + row.statut + ":" + (row.tentatives?.length || 0);
  if (affiches.has(key)) return;
  if (row.statut === "termine") {
    groupe.appendChild(bulle("Lyra", row.reponse.reponse, "lyra"));
    if (typeof ajouteActionsPassage === "function") ajouteActionsPassage(groupe, row);
  } else if (row.statut === "importe") {
    const raw = row.historique_importe.sortie_moteur;
    groupe.appendChild(bulle("Archive v1", raw === null ? "Réponse ancienne absente de l'archive." :
      "Sortie moteur conservée ; affichage d'origine indisponible.\n" + raw, "lyra"));
  } else {
    const labels = {en_attente: "Demande enregistrée, à lancer.", en_cours: "Calcul en cours.",
                    echoue: "Tentative échouée.", interrompu: "Tentative interrompue."};
    groupe.appendChild(bulle("Lyra", (labels[row.statut] || row.statut) + " " + (row.erreur?.message || ""), "lyra attente"));
  }
  affiches.add(key);
}

function envoisAReprendre() {
  const area = document.getElementById("envois");
  area.replaceChildren();
  if (!journal) return;
  try {
    const entries = journal.pending();
    if (entries.length) {
      const title = document.createElement("p");
      title.textContent = "Envois à reprendre ou réponses à retrouver"; area.appendChild(title);
    }
    for (const entry of entries) {
      const button = document.createElement("button");
      button.type = "button";
      const retry = ["echoue", "interrompu"].includes(entry.statut) && !entry.relance;
      const label = entry.statut === "termine" ? "Ouvrir la réponse" : retry ? "Relancer" : "Vérifier / reprendre";
      button.textContent = label + " · " + entry.payload.texte.slice(0, 55);
      button.onclick = async () => {
        button.disabled = true;
        try {
          nouvelleVue(entry.session || entry.payload.session);
          texteDemande(entry.payload.demande, entry.payload.texte);
          await traiteEnvoi(entry, retry, vue);
        } catch (err) { echo.textContent = err.message; }
        finally { envoisAReprendre(); }
      };
      area.appendChild(button);
    }
  } catch (err) { echo.textContent = "Copie locale à vérifier : " + err.message; }
}

async function traiteEnvoi(entry, retry, origine) {
  operations.add(origine); boutons();
  try {
    const accepted = row => {
      if (vue !== origine) return;
      memoriseSession(row.session);
      groupeDemande(row.demande, row.position);
      echo.textContent = "Demande enregistrée · " + row.demande;
    };
    const row = retry ? await journal.retry(entry, accepted) : await journal.continue(entry, accepted);
    if (vue === origine) {
      afficheDemande(row);
      if (row.statut === "termine") {
        afficheEtat(row.reponse);
        journal.acknowledge(entry, row);
        echo.textContent = "Réponse enregistrée.";
        if (row.reponse.finish_reason === "length") echo.textContent += " La réponse a atteint sa limite de génération.";
        if (typeof actualiseConversations === "function") actualiseConversations();
      } else {
        echo.textContent = "Statut : " + row.statut + ". L'envoi reste disponible ci-dessous.";
      }
    }
  } catch (err) {
    if (vue === origine) echo.textContent = err.message + " La copie locale de l'envoi est conservée.";
  } finally {
    operations.delete(origine); boutons(); envoisAReprendre();
    if (vue === origine) zone.focus();
  }
}

async function envoyer(voix) {
  if (operations.has(vue)) return;
  if (!journal) { echo.textContent = "Le stockage local du navigateur est nécessaire avant l'envoi."; return; }
  const texte = zone.value; // Le journal conserve aussi les espaces et retours initiaux.
  if (!texte.trim()) { echo.textContent = "Écris un mot."; return; }
  let entry;
  try { entry = journal.prepare(texte, session, voix); }
  catch (err) { echo.textContent = "Envoi conservé dans la zone de texte : " + err.message; return; }
  const origine = vue;
  zone.value = ""; texteDemande(entry.payload.demande, texte); envoisAReprendre();
  await traiteEnvoi(entry, false, origine);
}

async function chargerJournal() {
  if (!session || !journal) return;
  const origine = vue, sid = session;
  try {
    const page = await journal.call("/api/session/" + encodeURIComponent(sid) + "/journal?apres=" + curseur);
    if (origine !== vue || sid !== session) return;
    const copies = new Set(journal.pending().map(entry => entry.payload.demande));
    for (const row of page.demandes) {
      afficheDemande(row);
      if (!["termine", "importe"].includes(row.statut) && !copies.has(row.demande)) {
        journal.save({payload: {demande: row.demande, ...row.intention},
                      session: row.session, statut: row.statut, relance: null});
      }
    }
    curseur = page.curseur; envoisAReprendre();
    document.getElementById("charger-journal").hidden = page.demandes.length < 50;
  } catch (err) { if (origine === vue) echo.textContent = err.message; }
}

async function reprendreSession() {
  if (!session || !journal) return;
  const origine = vue, sid = session;
  try {
    const data = await journal.call("/api/session/" + encodeURIComponent(sid));
    if (origine !== vue || sid !== session) return;
    afficheEtat(data);
  } catch (err) { if (origine === vue) echo.textContent = err.message; }
  // La lecture de l'état vivant peut recevoir 409 pendant un calcul. Le
  // journal durable reste alors consultable et doit restituer l'envoi en cours.
  if (origine === vue && sid === session) await chargerJournal();
  if (origine === vue && sid === session && typeof actualiseRappels === "function") await actualiseRappels();
}

zone.addEventListener("keydown", event => {
  if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); envoyer(false); }
});
window.addEventListener("storage", envoisAReprendre);
envoisAReprendre();
reprendreSession();
