/* Copie locale avant envoi ; aucune relance automatique après un échec. */
(function (root) {
  class JournalClient {
    constructor({storage, fetch, uuid}) {
      this.storage = storage;
      this.fetch = fetch;
      this.uuid = uuid;
      this.prefix = "lyra.demande.v1.";
    }
    save(entry) {
      this.storage.setItem(this.prefix + entry.payload.demande, JSON.stringify(entry));
    }
    prepare(texte, session, voix) {
      const entry = {payload: {demande: this.uuid(), texte, session, voix: !!voix},
                     statut: "local", relance: null};
      this.save(entry); // Si le stockage échoue, aucun appel réseau ne commence.
      return entry;
    }
    pending() {
      const entries = [];
      for (let i = 0; i < this.storage.length; i++) {
        const key = this.storage.key(i);
        if (key && key.startsWith(this.prefix)) {
          const entry = JSON.parse(this.storage.getItem(key));
          if (!entry || !entry.payload || key !== this.prefix + entry.payload.demande) {
            throw new Error("Une copie locale de demande est illisible.");
          }
          entries.push(entry);
        }
      }
      return entries;
    }
    async call(path, payload) {
      const options = payload === undefined ? {} : {
        method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(payload)
      };
      const response = await this.fetch(path, options);
      const data = await response.json();
      if (!response.ok) {
        const error = new Error(typeof data.detail === "string" ? data.detail : "Demande refusée.");
        error.status = response.status;
        throw error;
      }
      return data;
    }
    async inspect(entry) {
      const row = await this.call("/api/demandes/" + encodeURIComponent(entry.payload.demande));
      entry.session = row.session;
      entry.statut = row.statut;
      // Ne pas effacer une identité de relance dont la réponse réseau est inconnue.
      this.save(entry);
      return row;
    }
    async continue(entry, onAccepted = () => {}) {
      const row = await this.call("/api/demandes", entry.payload);
      entry.session = row.session;
      entry.statut = row.statut;
      this.save(entry);
      onAccepted(row);
      const path = "/api/demandes/" + encodeURIComponent(entry.payload.demande);
      let result = row;
      if (entry.relance) {
        result = await this.call(path + "/relancer", {relance: entry.relance});
      } else if (row.statut === "en_attente") {
        result = await this.call(path + "/executer", {});
      }
      entry.statut = result.statut;
      entry.relance = null;
      this.save(entry);
      return result;
    }
    async retry(entry, onAccepted = () => {}) {
      // L'appelant réserve ce geste à un clic volontaire sur « Relancer ».
      if (!entry.relance) entry.relance = this.uuid();
      this.save(entry);
      return this.continue(entry, onAccepted);
    }
    acknowledge(entry, row) {
      if (row.statut !== "termine" || row.demande !== entry.payload.demande) {
        throw new Error("Une demande sans résultat validé reste à reprendre.");
      }
      this.storage.removeItem(this.prefix + entry.payload.demande);
    }
  }
  if (typeof module !== "undefined" && module.exports) module.exports = {JournalClient};
  else root.JournalClient = JournalClient;
})(globalThis);
