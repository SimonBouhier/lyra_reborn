"""Migration explicite v1 -> journal v2, dans un fichier nouveau uniquement.

L'original est ouvert en lecture seule. En cas d'échec la copie reste sur disque
pour inspection ; elle n'est pas annoncée comme un journal prêt à l'emploi.
"""
from contextlib import closing
import argparse
import json
from pathlib import Path
import sqlite3
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.journal import SQLiteJournalStore, encode
from app.session import LyraConversation
from app.storage import SQLiteSessionStore
from core.llm import EchoClient


def migrate(source, destination):
    source, destination = Path(source).resolve(strict=True), Path(destination).resolve()
    manifest = destination.with_suffix(".migration.json")
    if source == destination or destination.exists() or manifest.exists():
        raise FileExistsError("La destination et son rapport doivent être nouveaux.")
    if not source.is_file():
        raise ValueError("La source doit être une base SQLite existante.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(source.as_uri() + "?mode=ro", uri=True)) as incoming:
        if incoming.execute("PRAGMA user_version").fetchone()[0] != 1:
            raise ValueError("La source n'est pas une base de sessions v1.")
        with destination.open("xb"):
            pass
        with closing(sqlite3.connect(destination)) as copied:
            incoming.backup(copied)

    old = SQLiteSessionStore(destination)
    states = []
    for summary in old.list_summaries():
        state = old.load(summary["id"])
        # Validation intégrale v1, sans accès à un moteur réel.
        LyraConversation.from_state(state, backend=(EchoClient(), state["backend_label"]))
        states.append(state)
    report = {"source": str(source), "destination": str(destination), "schema": 2,
              "sessions": len(states), "entrees_importees": 0, "prompts_absents": 0,
              "sorties_moteur_absentes": 0, "reponses_affichees_non_reconstructibles": 0,
              "source_ouverte_en_lecture_seule": True, "importe_le": time.time()}
    new = SQLiteJournalStore(destination)
    with closing(sqlite3.connect(destination)) as connection:
        connection.execute("PRAGMA foreign_keys=ON")
        with connection:
            connection.execute("BEGIN IMMEDIATE")
            new._create_tables(connection)
            for state in states:
                count, sid = state["turns"], state["id"]
                history = state["cognitive_state"]["history"]
                first_history = count - len(history) + 1
                ecology = {item["id"]: item for item in state["ecology"]["items"]}
                for number in range(1, count + 1):
                    content = ecology.get(f"tour_{number}", {}).get("content", {})
                    prompt = content.get("prompt") if isinstance(content, dict) else None
                    if not isinstance(prompt, str):
                        prompt = None
                    historic = history[number - first_history] if number >= first_history else None
                    raw_output = historic["output"] if historic is not None else None
                    legacy = {"tour_v1": number, "prompt_absent": prompt is None,
                              "prompt_normalise_v1": True, "sortie_moteur": raw_output,
                              "reponse_affichee_absente": True, "horodatage_tour_inconnu": True}
                    rid = f"legacy-{sid}-{number}"
                    intent = {"texte": prompt if prompt is not None else "",
                              "session": sid, "voix": None, "origine": "migration_v1"}
                    now = time.time()
                    connection.execute(
                        "INSERT INTO requests(request_id, session_id, position, intent_json, status, created_at, updated_at, legacy_json) VALUES (?,?,?,?,'importe',?,?,?)",
                        (rid, sid, number, encode(intent), now, now, encode(legacy)),
                    )
                    new._event(connection, rid, 0, "importe_v1")
                    report["entrees_importees"] += 1
                    report["prompts_absents"] += int(prompt is None)
                    report["sorties_moteur_absentes"] += int(raw_output is None)
                    report["reponses_affichees_non_reconstructibles"] += 1
            connection.execute("PRAGMA user_version=2")
            if connection.execute("PRAGMA foreign_key_check").fetchall():
                raise ValueError("Liens incohérents après migration.")
    with manifest.open("x", encoding="utf-8") as output:
        json.dump(report, output, ensure_ascii=False, indent=2)
        output.write("\n")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--destination", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(migrate(args.source, args.destination), ensure_ascii=False, indent=2))
