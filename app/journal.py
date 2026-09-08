"""Journal SQLite v2. Les états de contrôle conservent leur contrat v1.

Transactions courtes : acceptation, début de tentative, puis publication
atomique état/réponse. Aucun appel au modèle dans ce module.
"""
from contextlib import contextmanager
import json
import sqlite3
import time

from app.storage import SQLiteSessionStore, SessionStorageError, _reject_json_constant, _require_finite_json


class RequestConflict(ValueError):
    """Identité, ordre ou état incompatible avec l'opération demandée."""


def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def decode(value):
    if value is None:
        return None
    try:
        result = json.loads(value, parse_constant=_reject_json_constant)
        _require_finite_json(result)
        return result
    except (TypeError, ValueError) as exc:
        raise SessionStorageError("contenu du journal illisible") from exc


class SQLiteJournalStore(SQLiteSessionStore):
    schema_version = 2

    def _create_tables(self, connection):
        super()._create_tables(connection)
        connection.execute("""CREATE TABLE IF NOT EXISTS requests (
            request_id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL REFERENCES sessions(session_id),
            position INTEGER NOT NULL CHECK(position > 0),
            intent_json TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN
                ('en_attente','en_cours','echoue','interrompu','termine','importe')),
            attempt INTEGER NOT NULL DEFAULT 0 CHECK(attempt >= 0),
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL,
            response_json TEXT,
            error_json TEXT,
            legacy_json TEXT,
            UNIQUE(session_id, position),
            CHECK((status = 'termine') = (response_json IS NOT NULL))
        )""")
        connection.execute("""CREATE TABLE IF NOT EXISTS attempts (
            request_id TEXT NOT NULL REFERENCES requests(request_id),
            number INTEGER NOT NULL CHECK(number > 0),
            retry_id TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('en_cours','echoue','interrompu','termine')),
            started_at REAL NOT NULL,
            ended_at REAL,
            execution_json TEXT,
            error_json TEXT,
            PRIMARY KEY(request_id, number),
            UNIQUE(request_id, retry_id)
        )""")
        connection.execute("""CREATE TABLE IF NOT EXISTS request_events (
            event_id INTEGER PRIMARY KEY,
            request_id TEXT NOT NULL REFERENCES requests(request_id),
            attempt INTEGER NOT NULL,
            kind TEXT NOT NULL,
            at REAL NOT NULL
        )""")
        connection.execute("""CREATE UNIQUE INDEX IF NOT EXISTS one_pending_per_session
            ON requests(session_id) WHERE status IN ('en_attente','en_cours')""")

    @contextmanager
    def transaction(self, *, write=True):
        try:
            with self._connect() as connection:
                connection.execute("BEGIN IMMEDIATE" if write else "BEGIN")
                yield connection
        except sqlite3.Error as exc:
            raise SessionStorageError(f"opération du journal impossible : {exc}") from exc

    @staticmethod
    def _event(connection, request_id, attempt, kind):
        connection.execute(
            "INSERT INTO request_events(request_id, attempt, kind, at) VALUES (?,?,?,?)",
            (request_id, attempt, kind, time.time()),
        )

    def _record(self, connection, request_id):
        row = connection.execute("SELECT * FROM requests WHERE request_id=?", (request_id,)).fetchone()
        if row is None:
            raise KeyError(request_id)
        intent, response = decode(row["intent_json"]), decode(row["response_json"])
        if not isinstance(intent, dict) or not isinstance(intent.get("texte"), str):
            raise SessionStorageError("intention du journal invalide")
        if row["status"] == "termine" and not isinstance(response, dict):
            raise SessionStorageError("réponse enregistrée invalide")
        attempts = connection.execute(
            "SELECT * FROM attempts WHERE request_id=? ORDER BY number", (request_id,)
        ).fetchall()
        if len(attempts) != row["attempt"]:
            raise SessionStorageError("historique des tentatives incohérent")
        return {
            "demande": request_id, "session": row["session_id"], "position": row["position"],
            "texte": intent["texte"], "intention": intent, "statut": row["status"],
            "cree": row["created_at"], "modifie": row["updated_at"], "reponse": response,
            "erreur": decode(row["error_json"]), "historique_importe": decode(row["legacy_json"]),
            "tentatives": [{
                "numero": a["number"], "relance": None if a["retry_id"] == "initial" else a["retry_id"],
                "statut": a["status"], "debut": a["started_at"], "fin": a["ended_at"],
                "execution": decode(a["execution_json"]), "erreur": decode(a["error_json"]),
            } for a in attempts],
        }

    def get(self, request_id):
        with self.transaction(write=False) as connection:
            return self._record(connection, request_id)

    def history(self, session_id, after=0, limit=100):
        if not 1 <= limit <= 100 or after < 0:
            raise ValueError("pagination invalide")
        with self.transaction(write=False) as connection:
            if connection.execute("SELECT 1 FROM sessions WHERE session_id=?", (session_id,)).fetchone() is None:
                raise KeyError(session_id)
            rows = connection.execute(
                "SELECT request_id FROM requests WHERE session_id=? AND position>? ORDER BY position LIMIT ?",
                (session_id, after, limit),
            ).fetchall()
            return [self._record(connection, row[0]) for row in rows]

    def accept(self, request_id, intent, initial_state):
        with self.transaction() as connection:
            existing = connection.execute("SELECT request_id FROM requests WHERE request_id=?", (request_id,)).fetchone()
            if existing is not None:
                record = self._record(connection, request_id)
                if record["intention"] != intent:
                    raise RequestConflict("Cet identifiant désigne une autre demande.")
                return record
            sid = initial_state["id"]
            if connection.execute(
                "SELECT 1 FROM requests WHERE session_id=? AND status IN ('en_attente','en_cours')", (sid,)
            ).fetchone():
                raise RequestConflict("Une demande attend déjà dans cette conversation.")
            # L'état initial est enregistré avec la première demande, jamais après la génération.
            if connection.execute("SELECT 1 FROM sessions WHERE session_id=?", (sid,)).fetchone() is None:
                self._write_state(connection, initial_state)
            position = connection.execute(
                "SELECT COALESCE(MAX(position),0)+1 FROM requests WHERE session_id=?", (sid,)
            ).fetchone()[0]
            now = time.time()
            connection.execute(
                "INSERT INTO requests(request_id, session_id, position, intent_json, status, created_at, updated_at) VALUES (?,?,?,?,?,?,?)",
                (request_id, sid, position, encode(intent), "en_attente", now, now),
            )
            self._event(connection, request_id, 0, "acceptee")
            return self._record(connection, request_id)

    def previous_execution(self, session_id, position):
        """Configuration du dernier résultat admis avant cette demande."""
        with self.transaction(write=False) as connection:
            row = connection.execute(
                """SELECT a.execution_json FROM requests r JOIN attempts a
                   ON a.request_id=r.request_id AND a.number=r.attempt
                   WHERE r.session_id=? AND r.position<? AND r.status='termine'
                   ORDER BY r.position DESC LIMIT 1""", (session_id, position),
            ).fetchone()
            return decode(row[0]) if row is not None else None

    def begin(self, request_id, retry_id):
        """Retourne un numéro nouveau, ou None si l'appel doit seulement relire."""
        with self.transaction() as connection:
            row = self._record(connection, request_id)
            status = row["statut"]
            if status in ("termine", "en_cours"):
                return None
            if status == "importe":
                raise RequestConflict("Une entrée importée ne se réexécute pas.")
            token = retry_id if retry_id is not None else "initial"
            if connection.execute(
                "SELECT 1 FROM attempts WHERE request_id=? AND retry_id=?", (request_id, token)
            ).fetchone():
                return None
            if status in ("echoue", "interrompu") and retry_id is None:
                return None
            if status == "en_attente" and retry_id is not None:
                raise RequestConflict("La première tentative n'est pas une relance.")
            # Une relance tardive modifierait le contexte de tours déjà ordonnés.
            if connection.execute(
                "SELECT 1 FROM requests WHERE session_id=? AND position>?", (row["session"], row["position"])
            ).fetchone():
                raise RequestConflict("Une demande suivante existe. Crée un nouvel envoi pour reprendre ce texte.")
            number, now = len(row["tentatives"]) + 1, time.time()
            connection.execute("UPDATE requests SET status='en_cours', attempt=?, updated_at=?, error_json=NULL WHERE request_id=?",
                               (number, now, request_id))
            connection.execute("INSERT INTO attempts(request_id, number, retry_id, status, started_at) VALUES (?,?,?,'en_cours',?)",
                               (request_id, number, token, now))
            self._event(connection, request_id, number, "demarree")
            return number

    def record_execution(self, request_id, attempt, execution):
        with self.transaction() as connection:
            changed = connection.execute(
                "UPDATE attempts SET execution_json=? WHERE request_id=? AND number=? AND status='en_cours'",
                (encode(execution), request_id, attempt),
            ).rowcount
            if changed != 1:
                raise RequestConflict("Tentative non active.")

    def complete(self, request_id, attempt, state, response):
        with self.transaction() as connection:
            row = self._record(connection, request_id)
            if row["statut"] != "en_cours" or len(row["tentatives"]) != attempt:
                raise RequestConflict("La tentative ne peut plus publier.")
            if state["id"] != row["session"] or response["session"] != row["session"]:
                raise RequestConflict("Identité de publication incohérente.")
            self._write_state(connection, state)
            now = time.time()
            connection.execute("UPDATE requests SET status='termine', response_json=?, error_json=NULL, updated_at=? WHERE request_id=?",
                               (encode(response), now, request_id))
            connection.execute("UPDATE attempts SET status='termine', ended_at=? WHERE request_id=? AND number=?",
                               (now, request_id, attempt))
            self._event(connection, request_id, attempt, "terminee")

    def fail(self, request_id, attempt, error, *, status="echoue"):
        if status not in ("echoue", "interrompu"):
            raise ValueError("statut d'échec invalide")
        with self.transaction() as connection:
            changed = connection.execute(
                "UPDATE requests SET status=?, error_json=?, updated_at=? WHERE request_id=? AND attempt=? AND status='en_cours'",
                (status, encode(error), time.time(), request_id, attempt),
            ).rowcount
            if changed != 1:
                raise RequestConflict("La tentative ne peut plus échouer.")
            connection.execute("UPDATE attempts SET status=?, ended_at=?, error_json=? WHERE request_id=? AND number=?",
                               (status, time.time(), encode(error), request_id, attempt))
            self._event(connection, request_id, attempt, status)

    def recover_interrupted(self):
        """Démarrage d'un unique serveur : les calculs antérieurs ne reprennent pas."""
        with self.transaction() as connection:
            rows = connection.execute("SELECT request_id, attempt FROM requests WHERE status='en_cours'").fetchall()
            error = encode({"phase": "interruption", "message": "Le serveur a redémarré avant la validation du résultat."})
            now = time.time()
            for row in rows:
                connection.execute("UPDATE requests SET status='interrompu', error_json=?, updated_at=? WHERE request_id=?",
                                   (error, now, row["request_id"]))
                connection.execute("UPDATE attempts SET status='interrompu', ended_at=?, error_json=? WHERE request_id=? AND number=?",
                                   (now, error, row["request_id"], row["attempt"]))
                self._event(connection, row["request_id"], row["attempt"], "interrompu")
