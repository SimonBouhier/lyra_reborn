"""Schéma v3 : corrections immuables et rappels limités à un message choisi."""
import re
import time

from app.dialogue import DialogueConversation
from app.journal import SQLiteJournalStore, RequestConflict
from app.storage import SessionStorageError


def valid_id(value):
    if not isinstance(value, str) or re.fullmatch(r"[A-Za-z0-9_-]{1,128}", value) is None:
        raise ValueError("identifiant invalide")


class DialogueStore(SQLiteJournalStore):
    schema_version = 3
    state_versions = (1, 2)

    def _create_tables(self, connection):
        super()._create_tables(connection)
        connection.execute("""CREATE TABLE IF NOT EXISTS corrections (
            id TEXT PRIMARY KEY, request_id TEXT NOT NULL REFERENCES requests(request_id),
            role TEXT NOT NULL CHECK(role IN ('user','assistant')), text TEXT NOT NULL,
            previous_id TEXT REFERENCES corrections(id), created REAL NOT NULL)""")
        connection.execute("""CREATE TABLE IF NOT EXISTS correction_heads (
            request_id TEXT NOT NULL REFERENCES requests(request_id), role TEXT NOT NULL,
            correction_id TEXT NOT NULL REFERENCES corrections(id), PRIMARY KEY(request_id,role))""")
        connection.execute("""CREATE TABLE IF NOT EXISTS recalls (
            id TEXT PRIMARY KEY, destination TEXT NOT NULL REFERENCES sessions(session_id),
            source_request TEXT NOT NULL REFERENCES requests(request_id),
            role TEXT NOT NULL CHECK(role IN ('user','assistant')),
            active INTEGER NOT NULL CHECK(active IN (0,1)), created REAL NOT NULL)""")

    def _write_state(self, connection, state):
        if state.get("schema_version") == 2:
            try:
                DialogueConversation.from_state(state)
            except ValueError as exc:
                raise SessionStorageError(str(exc)) from exc
        super()._write_state(connection, state)

    def load(self, session_id):
        state = super().load(session_id)
        if state is not None and state.get("schema_version") == 2:
            try:
                DialogueConversation.from_state(state)
            except ValueError as exc:
                raise SessionStorageError(str(exc)) from exc
        return state

    def _passage(self, connection, rid, role):
        if role not in ("user", "assistant"):
            raise ValueError("rôle de passage invalide")
        row = self._record(connection, rid)
        if row["statut"] != "termine":
            raise RequestConflict("Choisis un message d'un échange terminé ; les entrées importées incomplètes ne sont pas rappelables.")
        head = connection.execute("""SELECT c.* FROM corrections c JOIN correction_heads h
            ON c.id=h.correction_id WHERE h.request_id=? AND h.role=?""", (rid, role)).fetchone()
        return {"session": row["session"], "request": rid, "role": role,
                "text": row["texte"] if role == "user" else row["reponse"]["reponse"],
                "correction": self._correction(head) if head else None}

    @staticmethod
    def _correction(row):
        return {"id": row["id"], "request": row["request_id"], "role": row["role"],
                "text": row["text"], "previous": row["previous_id"], "created": row["created"]}

    def passage(self, rid, role):
        with self.transaction(write=False) as connection:
            passage = self._passage(connection, rid, role)
            passage["revisions"] = [self._correction(r) for r in connection.execute(
                "SELECT * FROM corrections WHERE request_id=? AND role=? ORDER BY rowid", (rid, role))]
            return passage

    def correct(self, cid, rid, role, text, previous):
        valid_id(cid)
        if not isinstance(text, str) or not text.strip() or len(text) > 100000:
            raise ValueError("correction vide ou trop longue")
        with self.transaction() as connection:
            existing = connection.execute("SELECT * FROM corrections WHERE id=?", (cid,)).fetchone()
            if existing:
                row = self._correction(existing)
                if (row["request"], row["role"], row["text"], row["previous"]) != (rid, role, text, previous):
                    raise RequestConflict("Identité de correction déjà utilisée autrement.")
                return row
            passage = self._passage(connection, rid, role)
            current = passage["correction"]["id"] if passage["correction"] else None
            if current != previous:
                raise RequestConflict("Une autre correction existe ; relis-la avant de la remplacer.")
            connection.execute("INSERT INTO corrections VALUES (?,?,?,?,?,?)", (cid, rid, role, text, previous, time.time()))
            connection.execute("""INSERT INTO correction_heads VALUES (?,?,?) ON CONFLICT(request_id,role)
                DO UPDATE SET correction_id=excluded.correction_id""", (rid, role, cid))
            self._event(connection, rid, 0, "correction:" + cid)
            return self._correction(connection.execute("SELECT * FROM corrections WHERE id=?", (cid,)).fetchone())

    def add_recall(self, recall_id, destination, rid, role):
        valid_id(recall_id)
        with self.transaction() as connection:
            self._passage(connection, rid, role)
            target = connection.execute("SELECT schema_version FROM sessions WHERE session_id=?", (destination,)).fetchone()
            if target is None:
                raise KeyError(destination)
            if target[0] != 2:
                raise RequestConflict("Les rappels nécessitent une conversation de référence.")
            existing = connection.execute("SELECT * FROM recalls WHERE id=?", (recall_id,)).fetchone()
            if existing:
                if (existing["destination"], existing["source_request"], existing["role"]) != (destination, rid, role):
                    raise RequestConflict("Identité de rappel déjà utilisée autrement.")
                return dict(existing)
            connection.execute("INSERT INTO recalls VALUES (?,?,?,?,1,?)", (recall_id, destination, rid, role, time.time()))
            self._event(connection, rid, 0, "rappel:" + recall_id)
            return dict(connection.execute("SELECT * FROM recalls WHERE id=?", (recall_id,)).fetchone())

    def remove_recall(self, recall_id, destination):
        with self.transaction() as connection:
            row = connection.execute("SELECT * FROM recalls WHERE id=? AND destination=?", (recall_id, destination)).fetchone()
            if row is None:
                raise KeyError(recall_id)
            if row["active"]:
                connection.execute("UPDATE recalls SET active=0 WHERE id=?", (recall_id,))
                self._event(connection, row["source_request"], 0, "rappel_retire:" + recall_id)
            return {"id": recall_id, "active": False}

    def _recalls(self, connection, sid):
        rows = connection.execute("SELECT * FROM recalls WHERE destination=? AND active=1 ORDER BY rowid", (sid,))
        return [{"id": r["id"], "passage": self._passage(connection, r["source_request"], r["role"])} for r in rows]

    def recalls(self, sid):
        with self.transaction(write=False) as connection:
            return self._recalls(connection, sid)

    def context_source(self, rid):
        # Snapshot cohérent de toutes les sources ; la transaction se ferme
        # avant l'assemblage et l'inférence. Les corrections restent possibles.
        with self.transaction(write=False) as connection:
            row = self._record(connection, rid)
            prior = connection.execute("SELECT request_id FROM requests WHERE session_id=? AND position<? ORDER BY position",
                                       (row["session"], row["position"])).fetchall()
            history, omissions = [], []
            for item in prior:
                old = self._record(connection, item[0])
                if old["statut"] != "termine" or old["reponse"].get("demonstration"):
                    omissions.append({"request": old["demande"], "reason": "échange sans réponse conversationnelle validée"})
                    continue
                history.append({"user": self._passage(connection, item[0], "user"),
                                "assistant": self._passage(connection, item[0], "assistant")})
            return {"request": row, "history": history, "omissions": omissions,
                    "recalls": self._recalls(connection, row["session"])}
