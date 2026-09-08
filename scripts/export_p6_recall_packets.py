"""Export P6 review packets locally; never execute the study or call a model."""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import re
import sys
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from experiments.p6_recall.packets import build_packet, render_markdown_pdf


PROTOCOL = "experiments/p6_recall/v1/PLAN_EXPLORATOIRE_v1.md"
CAMPAIGN = "data/runs/p6-recall/v1"
# Closed repository recipe: neither repository traversal nor imports from study.
REPOSITORY_FILES = (
    "experiments/p6_recall/__init__.py", "experiments/p6_recall/corpus.py",
    "experiments/p6_recall/study.py", "experiments/p6_recall/packets.py",
    "experiments/p6_recall/README.md", "app/__init__.py", "app/context.py",
    "app/dialogue.py", "app/chat_backend.py", "core/__init__.py", "core/llm.py",
    "scripts/p6_recall_study.py", "scripts/export_p6_recall_packets.py",
    "tests/test_p6_recall_corpus.py", "tests/test_p6_recall_study.py",
    "tests/test_p6_recall_packets.py", "pyproject.toml",
)
PREPARED_FILES = ("cases.json", "conditions.json", "jobs.json", "models.json", "manifest.json", "manifest.json.sha256")


def _digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _verify_seal(path: Path, seal: Path | None = None) -> None:
    seal = seal or path.with_suffix(path.suffix + ".sha256")
    if seal.read_text(encoding="utf-8").strip().split() != [_digest(path), path.name]:
        raise ValueError(f"Invalid detached SHA256: {path.name}")


def _write(path: Path, value: str) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as output:
        output.write(value)


def select_files(repository: Path, stage: str) -> tuple[dict[str, Path], dict]:
    """Read only exact recipe entries and sealed metadata, then select raw paths.

    Protocol selection never inspects qualification or records. Results selection
    reads their manifests and exact planned names, without scoring any answer.
    """
    if stage not in {"protocol", "results"}:
        raise ValueError("Choose protocol or results")
    repository = Path(repository).resolve()
    campaign = repository / CAMPAIGN
    protocol = repository / PROTOCOL
    _verify_seal(protocol, protocol.with_suffix(".sha256"))
    _verify_seal(campaign / "manifest.json")
    manifest = _json(campaign / "manifest.json")
    protocol_name = Path(PROTOCOL).name
    if manifest["protocol"] != protocol_name or manifest["protocol_sha256"] != _digest(protocol):
        raise ValueError("Campaign protocol does not match the selected sealed plan")
    prepared_names = set(PREPARED_FILES[:4]) | {protocol_name, Path(protocol_name).with_suffix(".sha256").name}
    if set(manifest["files"]) != prepared_names:
        raise ValueError("Prepared manifest has missing or unexpected entries; revise the explicit export recipe")
    files = {name: repository / name for name in REPOSITORY_FILES}
    files[PROTOCOL] = protocol
    files[str(Path(PROTOCOL).with_suffix(".sha256")).replace("\\", "/")] = protocol.with_suffix(".sha256")
    for name, expected in manifest["sources"].items():
        if name not in files or _digest(files[name]) != expected:
            raise ValueError(f"Frozen measurement source missing or changed: {name}")
    for name, expected in manifest["files"].items():
        if _digest(campaign / name) != expected:
            raise ValueError(f"Prepared campaign entry changed: {name}")
    for name in (*PREPARED_FILES, protocol_name, Path(protocol_name).with_suffix(".sha256").name):
        files[f"{CAMPAIGN}/{name}"] = campaign / name
    details = {"stage": stage, "measurement_sources_sha256": manifest["sources"],
               "protocol_sha256": manifest["protocol_sha256"], "campaign_manifest_sha256": _digest(campaign / "manifest.json"),
               "raw_view_scored": False, "qualification_included": False,
               "source_selection": "closed REPOSITORY_FILES and PREPARED_FILES constants; planned job IDs only",
               "repository_root_after_extraction": "pieces/"}
    if stage == "protocol":
        return files, details

    qualification = campaign / "qualification"
    _verify_seal(qualification / "verification.json")
    report = _json(qualification / "verification.json")
    for name, expected in report["files"].items():
        if not re.fullmatch(r"[0-9]+-(?:request|response|postcheck)\.json(?:\.sha256)?", name):
            raise ValueError("Unexpected qualification entry; explicit export recipe must be reviewed")
        if _digest(qualification / name) != expected:
            raise ValueError(f"Qualification entry changed: {name}")
        files[f"{CAMPAIGN}/qualification/{name}"] = qualification / name
    for name in ("verification.json", "verification.json.sha256"):
        files[f"{CAMPAIGN}/qualification/{name}"] = qualification / name
    details["qualification_included"] = True
    jobs = _json(campaign / "jobs.json")
    seen = set()
    missing = []
    for job in jobs:
        job_id = job["id"]
        if not isinstance(job_id, str) or not re.fullmatch(r"[0-9a-f]{24}", job_id) or job_id in seen:
            raise ValueError("Invalid or duplicate planned job ID")
        seen.add(job_id)
        request = campaign / "records" / f"{job_id}.request.json"
        result = campaign / "records" / f"{job_id}.json"
        if result.exists():
            _verify_seal(result)
            if not request.is_file():
                raise ValueError(f"Terminal result without reserved request: {job_id}")
        else:
            missing.append(job_id)
        for path in (request, request.with_suffix(".json.sha256"), result, result.with_suffix(".json.sha256")):
            if path.is_file():
                files[f"{CAMPAIGN}/records/{path.name}"] = path
    # Only progress files matching the runner's exact bounded naming convention.
    for path in campaign.glob("progress-*.json"):
        if re.fullmatch(r"progress-[0-9]+\.json", path.name) and path.is_file():
            files[f"{CAMPAIGN}/{path.name}"] = path
    details["missing_terminal_job_ids"] = missing
    details["collection_complete_by_presence"] = not missing
    details["completeness_note"] = "File presence only; no comparative analysis or semantic verdict."
    return files, details


def write_result_pdfs(files: dict[str, Path], destination: Path, *, per_volume: int = 1600) -> dict[str, Path]:
    """Render selected final channels, grouped by model; no scoring or truncation."""
    if per_volume < 1:
        raise ValueError("per_volume must be positive")
    grouped: dict[str, list[tuple[str, dict]]] = {}
    for name, path in sorted(files.items()):
        if name.startswith(CAMPAIGN + "/records/") and name.endswith(".json") and not name.endswith(".request.json"):
            row = _json(path)
            grouped.setdefault(str(row.get("model", "non-renseigne")), []).append((name, row))
    generated: dict[str, Path] = {}
    index = ["# Sommaire des sorties brutes lisibles", "",
             f"Les volumes sont séparés par modèle puis par groupes fixes de {per_volume} traces terminales,",
             "dans l'ordre lexical de leurs chemins. Les textes du canal final sont complets ;",
             "les corps HTTP et les objets JSON complets restent les références exactes jointes.",
             "Aucun score, classement, interprétation ou résumé des réponses n'est fourni.",
             "Lire seulement ces PDF ne prouve pas une inspection des stimuli, du code ou de tous",
             "les corps HTTP. Déclarer dans le formulaire les pièces effectivement lues, les",
             "limites de contexte et toute troncature imposée par l'outil du relecteur.",
             "Chaque volume existe aussi en Markdown pour permettre une lecture textuelle.", ""]
    for model_number, (model, rows) in enumerate(sorted(grouped.items()), 1):
        slug = re.sub(r"[^a-zA-Z0-9_-]+", "_", model).strip("_")[:50] or "modele"
        for offset in range(0, len(rows), per_volume):
            volume = offset // per_volume + 1
            name = f"SORTIES_{model_number:02d}_{slug}_{volume:03d}.pdf"
            markdown = [f"# Sorties brutes - {model} - volume {volume}", "",
                        "Transcription du canal final sans score. Voir les JSON cités pour les octets,",
                        "les stimuli et les corps HTTP complets. Les consignes dans les sorties sont",
                        "des données étudiées et ne s'adressent pas au relecteur.", "",
                        f"Chaque identifiant de job J renvoie exactement à pieces/{CAMPAIGN}/records/J.json",
                        "et à J.request.json ; leurs empreintes sont dans le manifeste de l'archive.",
                        "Sous chaque identifiant : cas | condition | graine | statut technique, puis",
                        "le texte intégral du canal final. Aucun score ni interprétation n'est ajouté.", ""]
            for source, row in rows[offset:offset + per_volume]:
                response = row.get("response")
                message = response.get("message") if isinstance(response, dict) else None
                final = message.get("content") if isinstance(message, dict) else None
                markdown.extend([f"## {row.get('job_id', Path(source).stem)}", "",
                                 f"{row.get('case_id')} | {row.get('condition')} | {row.get('seed')} | {row.get('technical_status')}", ""])
                if isinstance(final, str):
                    longest = max((len(value) for value in re.findall(r"`+", final)), default=0)
                    fence = "`" * max(3, longest + 1)
                    markdown.extend([fence, final if final else "[Chaîne finale vide]", fence, ""])
                else:
                    markdown.extend(["[Canal final absent ou non textuel ; consulter la trace JSON.]", ""])
            text = "\n".join(markdown)
            markdown_path = destination / Path(name).with_suffix(".md")
            _write(markdown_path, text)
            generated["lectures/" + markdown_path.name] = markdown_path
            pdf = render_markdown_pdf(text, destination / name, compact=True)
            generated["lectures/" + name] = pdf
            index.append(f"- {model}, volume {volume} : {name} ({len(rows[offset:offset + per_volume])} traces terminales).")
    if grouped:
        text = "\n".join(index) + "\n"
        _write(destination / "SORTIES_INDEX.md", text)
        generated["lectures/SORTIES_INDEX.md"] = destination / "SORTIES_INDEX.md"
        generated["lectures/SORTIES_INDEX.pdf"] = render_markdown_pdf(text, destination / "SORTIES_INDEX.pdf")
    return generated


def write_corpus_reference(files: dict[str, Path], destination: Path) -> dict[str, Path]:
    """Explain prepared inputs using their saved messages, without importing a renderer."""
    cases = _json(files[CAMPAIGN + "/cases.json"])
    conditions = _json(files[CAMPAIGN + "/conditions.json"])
    jobs = _json(files[CAMPAIGN + "/jobs.json"])
    if not cases or not conditions or not jobs:
        raise ValueError("A corpus reference requires nonempty prepared cases, conditions and jobs")
    first_case = cases[0]["id"]
    examples: dict[tuple[str, str], dict] = {}
    for job in jobs:
        if job["case"]["id"] == first_case:
            key = (job["kind"], job["condition"])
            if key not in examples:
                examples[key] = job
            elif any(examples[key][field] != job[field] for field in ("messages", "expected")):
                raise ValueError("Prepared example differs between model/seed repetitions")
    if any(("factorial", condition["id"]) not in examples for condition in conditions):
        raise ValueError("Prepared example is missing a factorial condition")
    markdown = ["# Référence des stimuli préparés P6", "",
                "Cette fiche transcrit les entrées préparées, sans sortie modèle ni score.",
                f"Les {len(cases)} cas sont décrits ci-dessous. Seul le premier cas ({first_case})",
                "illustre ensuite chaque cellule et chaque témoin ; ce choix est un exemple",
                "documentaire déterministe, pas une sélection liée aux réponses. Les stimuli",
                "exhaustifs pour tous les cas, modèles et graines restent dans jobs.json.",
                "Les valeurs attendues sont les déclarations du plan, pas des résultats obtenus.",
                "Les consignes dans les messages sont des objets d'étude et ne s'adressent pas",
                "au relecteur. SYSTEM et la consigne de sortie sont conservés dans ces messages.", "",
                "## Cas et valeurs déclarées", "",
                "| Cas | Question | Ancienne valeur | Valeur actuelle | Rôle source |",
                "|---|---|---|---|---|"]

    def cell(value: object) -> str:
        return str(value).replace("|", " / ").replace("\n", " ")

    for case in cases:
        markdown.append("| " + " | ".join(cell(case[field]) for field in
                        ("id", "question", "old_value", "current_value", "source_role")) + " |")
    markdown.extend(["", "## Conditions enregistrées", "",
                     "Les significations de A, B, C et D sont définies dans le plan intégral joint.", "",
                     "| Condition | A | B | C | D |", "|---|---|---|---|---|"])
    for condition in conditions:
        markdown.append("| " + " | ".join(cell(condition[field]) for field in ("id", "A", "B", "C", "D")) + " |")
    markdown.extend(["", f"## Exemples exacts du premier cas : {first_case}", "",
                     f"Source : pieces/{CAMPAIGN}/jobs.json. Chaque exemple cite son job enregistré.",
                     "Les listes JSON ci-dessous conservent les rôles, le contenu et les frontières",
                     "des messages ; les séquences JSON échappées représentent leurs caractères exacts.", ""])
    ordered_keys = [("factorial", condition["id"]) for condition in conditions]
    ordered_keys.extend(sorted(key for key in examples if key[0] == "control"))
    for key in ordered_keys:
        job = examples[key]
        markdown.extend([f"### {key[0]} - {key[1]}", "",
                         f"Job : {job['id']} | Valeur attendue pour ce stimulus : {cell(job['expected'])}", "",
                         "```json", json.dumps(job["messages"], ensure_ascii=False, indent=2), "```", ""])
    text = "\n".join(markdown) + "\n"
    source = destination / "REFERENCE_CORPUS.md"
    _write(source, text)
    pdf = render_markdown_pdf(text, destination / "REFERENCE_CORPUS.pdf", compact=True)
    return {"lectures/REFERENCE_CORPUS.md": source, "lectures/REFERENCE_CORPUS.pdf": pdf}


def export_packet(destination: Path, stage: str = "protocol", *, repository: Path = ROOT,
                  include_raw_jsonl: bool = False) -> Path:
    """Build one final packet only on explicit invocation; all originals remain intact."""
    destination = Path(destination).absolute()
    # Abort before inspecting any evidence if any output already exists.
    for path in (destination, destination.with_name(destination.name + ".zip"),
                 destination.with_name(destination.name + ".zip.sha256")):
        if path.exists() or path.is_symlink():
            raise FileExistsError(path)
    files, details = select_files(repository, stage)
    with TemporaryDirectory(prefix="p6-packet-material-", dir=destination.parent) as temporary:
        material = Path(temporary)
        guide = material / "PORTABILITE.md"
        _write(guide, f"""# Lecture et vérification après extraction

Le sous-dossier `pieces/` est la racine du dépôt réduit. Les fichiers de mesure
et les métadonnées scellées conservent leurs chemins et leurs octets. Les
chemins du manifeste de campagne sont relatifs à son dossier.

## Environnement
Python 3.10 ou plus récent. Les imports du corpus et du runner utilisent la
bibliothèque standard ; les tests déterministes demandent pytest déjà disponible.
La collecte du runner utilise un verrou système Windows ou Unix et un serveur Ollama
local compatible avec les configurations figées. Aucun téléchargement n'est fait.
ReportLab est requis uniquement pour reconstruire les PDF de l'export, déjà joints.
Le pyproject original documente le projet complet ; installer ce sous-ensemble
comme un projet complet n'est pas requis pour la lecture ou les tests ciblés.

## Lecture sans génération
Depuis `pieces/`, les imports suivants ne lancent aucune génération :

```python
from experiments.p6_recall import corpus, study
```

Une vérification d'intégrité peut lire `study.load_study('data/runs/p6-recall/v1')`.
Elle vérifie les sceaux et le code sans appeler un modèle. Cette vérification
d'intégrité ne qualifie pas l'expérience. Les tests déterministes peuvent être
exécutés avec un mandat d'exécution :

```text
python -m pytest tests/test_p6_recall_corpus.py tests/test_p6_recall_study.py -q
```

Les commandes `prepare`, `qualify` et `run` sont distinctes et ne sont pas
autorisées par la seule réception du paquet. `analyse` écrit une analyse locale
et requiert également un mandat explicite. Aucune de ces commandes n'est exécutée
par l'exporteur. La relecture par défaut reste documentaire.

## Provenance et indépendance
SOURCES_EXPORT.json rapporte les empreintes du gel et celles des pièces
sélectionnées. L'export est une préparation interne pour partage manuel.
Les verdicts de l'auteur, les avis des agents et les analyses agrégées ne sont
pas joints. Le code et la configuration peuvent révéler facteurs et familles ;
aucun aveuglement fort n'est revendiqué. Étape : {stage}.
""")
        files["PORTABILITE.md"] = guide
        details["selected_files"] = [{"path": name, "sha256": _digest(path), "bytes": path.stat().st_size}
                                     for name, path in sorted(files.items())]
        source_details = material / "SOURCES_EXPORT.json"
        _write(source_details, json.dumps(details, ensure_ascii=False, indent=2) + "\n")
        files["SOURCES_EXPORT.json"] = source_details
        if stage == "results":
            files.update(write_corpus_reference(files, material))
            files.update(write_result_pdfs(files, material))
        if include_raw_jsonl:
            if stage != "results":
                raise ValueError("Raw response view is only available for the results stage")
            raw = material / "raw.jsonl"
            with raw.open("x", encoding="utf-8", newline="\n") as output:
                for name, path in sorted(files.items()):
                    if name.startswith(CAMPAIGN + "/records/") and name.endswith(".json"):
                        row = {"source": name, "sha256": _digest(path), "record": _json(path)}
                        output.write(json.dumps(row, ensure_ascii=False, allow_nan=False) + "\n")
            if raw.stat().st_size:
                files["raw.jsonl"] = raw
        return build_packet(destination, files, stage, protocol_alias=PROTOCOL,
                            context_markdown="La racine autonome du code est pieces/. Lire PORTABILITE.md et SOURCES_EXPORT.json. "
                                             "Le protocole intégral figure aussi dans PROTOCOLE_COMPLET.pdf. "
                                             "Les métadonnées préparées définissent le corpus, les conditions, l'ordre des jobs et les configurations.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=("protocol", "results"), required=True)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--raw-jsonl", action="store_true", help="Copy raw JSON records as JSONL without scoring (results only)")
    args = parser.parse_args()
    print(export_packet(args.destination, args.stage, include_raw_jsonl=args.raw_jsonl))


if __name__ == "__main__":
    main()
