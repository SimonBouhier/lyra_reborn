"""Copie explicite v1/v2 -> v3. Les conversations historiques gardent leur profil."""
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

from app.dialogue_store import DialogueStore
from app.journal import SQLiteJournalStore
from app.session import LyraConversation
from core.llm import EchoClient
from scripts.migrate_p6_journal import migrate as migrate_v1


def migrate(source, destination):
    source, destination = Path(source).resolve(strict=True), Path(destination).resolve()
    report_path = destination.with_suffix('.dialogue-migration.json')
    if destination.exists() or report_path.exists() or destination.with_suffix('.migration.json').exists():
        raise FileExistsError('La copie et ses rapports doivent être nouveaux.')
    with closing(sqlite3.connect(source.as_uri() + '?mode=ro', uri=True)) as incoming:
        version = incoming.execute('PRAGMA user_version').fetchone()[0]
        if version not in (1, 2):
            raise ValueError('Source attendue : sessions v1 ou journal v2.')
        if version == 2:
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open('xb'):
                pass
            with closing(sqlite3.connect(destination)) as copied:
                incoming.backup(copied)
    legacy = migrate_v1(source, destination) if version == 1 else None
    old = SQLiteJournalStore(destination)
    summaries = old.list_summaries()
    for summary in summaries:
        state = old.load(summary['id'])
        LyraConversation.from_state(state, backend=(EchoClient(), state['backend_label']))
        after = 0
        while True:
            page = old.history(summary['id'], after, 100)
            if not page:
                break
            after = page[-1]['position']
    with closing(sqlite3.connect(destination)) as connection:
        with connection:
            connection.execute('PRAGMA foreign_keys=ON')
            connection.execute('BEGIN IMMEDIATE')
            DialogueStore(destination)._create_tables(connection)
            connection.execute('PRAGMA user_version=3')
            if connection.execute('PRAGMA foreign_key_check').fetchall():
                raise ValueError('Références invalides dans la copie.')
    report = {'source': str(source), 'destination': str(destination), 'source_schema': version,
              'schema': 3, 'sessions_preservees': len(summaries), 'profils_historiques_convertis': 0,
              'source_ouverte_en_lecture_seule': True, 'legacy_import': legacy, 'created': time.time()}
    with report_path.open('x', encoding='utf-8') as output:
        json.dump(report, output, ensure_ascii=False, indent=2)
        output.write('\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--destination', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(migrate(args.source, args.destination), ensure_ascii=False, indent=2))
