"""Persistance SQLite bornée des sessions P6.

Le stockage ne connaît pas les objets vivants de Lyra : il conserve un état
JSON versionné dans une transaction SQLite. La reconstruction et la validation
du contrat appartiennent à :mod:`app.session`.
"""
from __future__ import annotations

from contextlib import closing, contextmanager
import json
import math
import sqlite3
import threading
import time
from collections.abc import Iterator
from pathlib import Path
from typing import Any, Dict, List


STORAGE_SCHEMA_VERSION = 1


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"constante JSON interdite : {value}")


def _require_finite_json(value: Any) -> None:
    """Refuse aussi les exposants JSON qui débordent silencieusement vers inf."""
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("nombre JSON non fini")
    if isinstance(value, dict):
        for nested in value.values():
            _require_finite_json(nested)
    elif isinstance(value, list):
        for nested in value:
            _require_finite_json(nested)


class SessionStorageError(RuntimeError):
    """Le stockage durable est indisponible, incompatible ou corrompu."""


class SQLiteSessionStore:
    """Dépôt SQLite local, sans suppression ni repli silencieux."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self._initialized = False
        self._initialization_lock = threading.Lock()

    def _open(self) -> sqlite3.Connection:
        connection = sqlite3.connect(str(self.path), timeout=5.0)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 5000")
        return connection

    def _initialize(self) -> None:
        if self._initialized:
            return
        with self._initialization_lock:
            if self._initialized:
                return
            try:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                with closing(self._open()) as connection:
                    with connection:
                        version = int(
                            connection.execute("PRAGMA user_version").fetchone()[0]
                        )
                        if version not in (0, STORAGE_SCHEMA_VERSION):
                            raise SessionStorageError(
                                f"version SQLite non supportée : {version}"
                            )
                        connection.execute(
                            """
                            CREATE TABLE IF NOT EXISTS sessions (
                                session_id TEXT PRIMARY KEY,
                                schema_version INTEGER NOT NULL,
                                backend_label TEXT NOT NULL,
                                turns INTEGER NOT NULL CHECK (turns >= 0),
                                created_at REAL NOT NULL,
                                updated_at REAL NOT NULL,
                                state_json TEXT NOT NULL
                            )
                            """
                        )
                        if version == 0:
                            connection.execute(
                                f"PRAGMA user_version = {STORAGE_SCHEMA_VERSION}"
                            )
                        connection.execute("PRAGMA journal_mode = WAL")
                self._initialized = True
            except SessionStorageError:
                raise
            except (OSError, sqlite3.Error) as exc:
                raise SessionStorageError(
                    f"impossible d'initialiser le stockage SQLite : {exc}"
                ) from exc

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        """Ouvre une transaction et ferme toujours son handle Windows."""
        self._initialize()
        try:
            connection = self._open()
        except sqlite3.Error as exc:
            raise SessionStorageError(
                f"impossible d'ouvrir le stockage SQLite : {exc}"
            ) from exc
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def save(self, state: Dict[str, Any]) -> None:
        """Insère ou remplace atomiquement l'état complet d'une session."""
        try:
            session_id = state["id"]
            schema_version = int(state["schema_version"])
            backend_label = state["backend_label"]
            turns = int(state["turns"])
            created_at = float(state["created"])
            if not isinstance(session_id, str) or not session_id:
                raise ValueError("identifiant de session vide")
            if not isinstance(backend_label, str) or not backend_label:
                raise ValueError("étiquette de moteur vide")
            if schema_version != STORAGE_SCHEMA_VERSION:
                raise ValueError(f"version d'état non supportée : {schema_version}")
            if turns < 0:
                raise ValueError("nombre de tours négatif")
            payload = json.dumps(
                state,
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
                allow_nan=False,
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise SessionStorageError(f"état de session invalide : {exc}") from exc

        updated_at = time.time()
        try:
            with self._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO sessions
                        (session_id, schema_version, backend_label, turns,
                         created_at, updated_at, state_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(session_id) DO UPDATE SET
                        schema_version = excluded.schema_version,
                        backend_label = excluded.backend_label,
                        turns = excluded.turns,
                        created_at = excluded.created_at,
                        updated_at = excluded.updated_at,
                        state_json = excluded.state_json
                    """,
                    (
                        session_id,
                        schema_version,
                        backend_label,
                        turns,
                        created_at,
                        updated_at,
                        payload,
                    ),
                )
        except SessionStorageError:
            raise
        except sqlite3.Error as exc:
            raise SessionStorageError(
                f"impossible d'enregistrer la session : {exc}"
            ) from exc

    def load(self, session_id: str) -> Dict[str, Any] | None:
        """Retourne l'état durable, sans créer de ligne lors d'une lecture."""
        try:
            with self._connect() as connection:
                row = connection.execute(
                    """
                    SELECT schema_version, backend_label, turns, created_at,
                           state_json
                    FROM sessions
                    WHERE session_id = ?
                    """,
                    (session_id,),
                ).fetchone()
        except SessionStorageError:
            raise
        except sqlite3.Error as exc:
            raise SessionStorageError(
                f"impossible de lire la session : {exc}"
            ) from exc

        if row is None:
            return None
        if int(row["schema_version"]) != STORAGE_SCHEMA_VERSION:
            raise SessionStorageError(
                f"version de session non supportée : {row['schema_version']}"
            )
        try:
            state = json.loads(
                row["state_json"],
                parse_constant=_reject_json_constant,
            )
            _require_finite_json(state)
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            raise SessionStorageError(
                f"état durable illisible pour la session {session_id}"
            ) from exc
        if not isinstance(state, dict) or state.get("id") != session_id:
            raise SessionStorageError(
                f"identité durable incohérente pour la session {session_id}"
            )
        try:
            metadata_matches = (
                int(state["schema_version"]) == int(row["schema_version"])
                and state["backend_label"] == row["backend_label"]
                and int(state["turns"]) == int(row["turns"])
                and float(state["created"]) == float(row["created_at"])
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise SessionStorageError(
                f"métadonnées durables invalides pour la session {session_id}"
            ) from exc
        if not metadata_matches:
            raise SessionStorageError(
                f"métadonnées durables incohérentes pour la session {session_id}"
            )
        return state

    def list_summaries(self) -> List[Dict[str, Any]]:
        """Liste les sessions durables sans charger leur contenu conversationnel."""
        try:
            with self._connect() as connection:
                rows = connection.execute(
                    """
                    SELECT session_id, backend_label, turns, created_at, updated_at
                    FROM sessions
                    ORDER BY updated_at DESC, session_id ASC
                    """
                ).fetchall()
        except SessionStorageError:
            raise
        except sqlite3.Error as exc:
            raise SessionStorageError(
                f"impossible de lister les sessions : {exc}"
            ) from exc
        return [
            {
                "id": row["session_id"],
                "moteur": row["backend_label"],
                "tours": int(row["turns"]),
                "created": float(row["created_at"]),
                "updated": float(row["updated_at"]),
            }
            for row in rows
        ]
