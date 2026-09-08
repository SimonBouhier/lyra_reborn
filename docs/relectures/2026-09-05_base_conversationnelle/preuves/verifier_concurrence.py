"""Reproduction documentaire : chevauchement + rollback, sans Ollama.

Exécuter depuis la racine de lyra_reborn avec son Python, option -B.
Le client est explicitement factice ; seules des bases temporaires sont ouvertes.
Ce fichier ne corrige et ne modifie aucun fichier applicatif.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
from threading import Event


ROOT = Path(__file__).resolve().parents[4]
EXPECTED_COMMIT = "788971a00f4303d2ba24cc671f4c0049fab772f9"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    head = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
    if head != EXPECTED_COMMIT:
        raise RuntimeError(f"Commit différent de la référence : {head}")
    diff = subprocess.check_output(["git", "-C", str(ROOT), "diff", "HEAD", "--", "app", "core", "memory"])
    if diff:
        raise RuntimeError("Le code applicatif diffère du commit de référence.")
    sys.path.insert(0, str(ROOT))
    scratch = ROOT.parent / "tmp" / "verification_relectures"
    scratch.mkdir(parents=True, exist_ok=True)
    results = []
    with tempfile.TemporaryDirectory(prefix="concurrence-", dir=scratch) as temp_dir:
        temporary = Path(temp_dir).resolve()
        if not temporary.is_relative_to(scratch.resolve()):
            raise RuntimeError("Dossier temporaire hors du périmètre prévu.")
        os.environ["LYRA_DB_PATH"] = str(temporary / "unused_default.sqlite3")
        os.environ["LYRA_LIVE"] = "0"
        from fastapi.testclient import TestClient
        import app.main as application
        from app.session import SessionBook
        from app.storage import SQLiteSessionStore

        for overlap in (False, True):
            entered_failure = Event()
            release_failure = Event()
            class ScriptedClient:
                model = "verification-factice"
                def generate(self, prompt, options, response_format=None):
                    if prompt.endswith("BFAIL"):
                        entered_failure.set()
                        if overlap and not release_failure.wait(15):
                            raise AssertionError("Synchronisation de la sonde expirée")
                        raise RuntimeError("Échec factice de B")
                    if prompt.endswith("AOK"):
                        return "- REPONSE_A_A_CONSERVER"
                    if prompt.endswith("COK"):
                        return "- REPONSE_C_SUIVANTE"
                    return "- REPONSE_INITIALE"

            store = SQLiteSessionStore(temporary / ("overlap.sqlite3" if overlap else "serial.sqlite3"))
            book = SessionBook(
                llm_factory=lambda: (ScriptedClient(), "verification-factice"),
                backend_resolver=lambda label: (ScriptedClient(), label),
                storage=store,
            )
            application.book = book
            client_a = TestClient(application.app)
            client_b = TestClient(application.app)
            initial = client_a.post("/api/parler", json={"texte": "INITIAL"})
            assert initial.status_code == 200
            sid = initial.json()["session"]

            def fail_request():
                return client_b.post("/api/parler", json={"session": sid, "texte": "BFAIL"})

            if overlap:
                with ThreadPoolExecutor(max_workers=1) as pool:
                    failed_future = pool.submit(fail_request)
                    try:
                        assert entered_failure.wait(15), "B n'est pas entré dans la génération"
                        success = client_a.post("/api/parler", json={"session": sid, "texte": "AOK"})
                        assert success.status_code == 200
                    finally:
                        release_failure.set()
                    failed = failed_future.result(timeout=15)
            else:
                failed = fail_request()
                success = client_a.post("/api/parler", json={"session": sid, "texte": "AOK"})

            assert success.status_code == 200 and failed.status_code == 502
            assert success.json()["reponse"] == "- REPONSE_A_A_CONSERVER"

            def state_view(state):
                return {"turns": state["turns"], "outputs": [x["output"] for x in state["cognitive_state"]["history"]]}

            disk_before = state_view(store.load(sid))
            memory_before = state_view(book.require(sid).to_state())
            after = client_a.post("/api/parler", json={"session": sid, "texte": "COK"})
            assert after.status_code == 200
            disk_after = state_view(store.load(sid))
            restarted = SessionBook(storage=store, backend_resolver=lambda label: (ScriptedClient(), label))
            after_restart = state_view(restarted.require(sid).to_state())
            assert disk_after == after_restart
            kept_a = "- REPONSE_A_A_CONSERVER" in disk_after["outputs"]
            assert kept_a is (not overlap)
            results.append({
                "case": "chevauchement" if overlap else "temoin_sequentiel",
                "http_A": success.status_code,
                "http_B": failed.status_code,
                "http_C": after.status_code,
                "disk_after_A_B": disk_before,
                "memory_after_A_B": memory_before,
                "disk_after_C": disk_after,
                "state_after_new_registry": after_restart,
                "accepted_A_preserved": kept_a,
            })
            client_a.close()
            client_b.close()

    output = Path(args.output).resolve()
    evidence = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "commit": head,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "scope": "FastAPI TestClient, client factice, deux scénarios déterministes, SQLite temporaire ; aucun réseau, Ollama, corpus P7 ou session réelle",
        "results": results,
        "conclusion": "Perte du tour A accepté reproduite avec chevauchement et échec B ; absente dans le témoin séquentiel. Ce test ne mesure pas la fréquence en usage réel.",
    }
    output.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(evidence, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
