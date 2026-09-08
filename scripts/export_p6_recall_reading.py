"""Create a compact reversible reading companion from one finished P6 packet.

Only transcription and integrity checks: no scorer, analysis, model calls,
network, campaign changes or modifications to the source archive.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.p6_recall.packets import render_markdown_pdf

CAMPAIGN = "pieces/data/runs/p6-recall/v1"
CONTROL_CODES = {name: f"T{index}" for index, name in enumerate(
    ("current_only", "old_only", "unchanged", "unknown", "other_subject", "multiple_updates"), 1)}
SEEDS = {1001: "1", 1002: "2", 1003: "3"}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def final_value(record: dict):
    response = record.get("response")
    message = response.get("message") if isinstance(response, dict) else None
    value = message.get("content") if isinstance(message, dict) else None
    if value is not None and not isinstance(value, str):
        raise ValueError("Final output must be text or absent/null; consult source record")
    return value


def encode_row(index: int, job: dict, record: dict, aliases: dict[str, str]) -> str:
    expected_metadata = {"job_id": job["id"], "model": job["model"], "case_id": job["case"]["id"],
                         "template_id": job["case"]["template_id"], "condition": job["condition"],
                         "kind": job["kind"], "seed": job["seed"]}
    if any(record.get(key) != value for key, value in expected_metadata.items()):
        raise ValueError(f"Record/job metadata mismatch for global index {index}")
    if job["kind"] == "factorial":
        match = re.fullmatch(r"A([01])_B([01])_C([01])_D([01])", job["condition"])
        if not match:
            raise ValueError("Invalid factorial condition")
        code = "".join(match.groups())
    elif job["kind"] == "control" and job["condition"] in CONTROL_CODES:
        code = CONTROL_CODES[job["condition"]]
    else:
        raise ValueError("Unknown condition or job kind")
    if job["seed"] not in SEEDS:
        raise ValueError("Unknown seed")
    status = record["technical_status"]
    if not isinstance(status, str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", status):
        raise ValueError("Unsafe technical status")
    if status == "V":
        raise ValueError("Source status V would collide with the valid alias")
    # Paragraph-based PDF renderers collapse repeated literal spaces. Escaping
    # even U+0020 keeps the visible JSON lossless when extracted from the PDF.
    final_json = json.dumps(final_value(record), ensure_ascii=True).replace(" ", r"\u0020")
    return ";".join((f"r{index:04d}", aliases[job["case"]["id"]], code, SEEDS[job["seed"]],
                     "V" if status == "valid" else status, final_json))


def decode_row(line: str) -> dict:
    """Five semicolon-delimited fields followed by one whole JSON value."""
    reference, case, condition, seed, status, value = line.split(";", 5)
    if not re.fullmatch(r"r[0-9]{4,}", reference):
        raise ValueError("Invalid global row reference")
    return {"index": int(reference[1:]), "case_alias": case, "condition_code": condition,
            "seed_alias": seed, "status": "valid" if status == "V" else status,
            "final": json.loads(value)}


def validate_rows(rows: list[tuple[str, str]], jobs: list[dict], records: dict[str, dict], aliases: dict) -> int:
    if len(rows) != len(jobs):
        raise ValueError("Row count differs from planned jobs")
    seen = set()
    for model, line in rows:
        decoded = decode_row(line)
        index = decoded["index"]
        if index in seen or not 1 <= index <= len(jobs):
            raise ValueError("Duplicate or invalid global reference")
        seen.add(index)
        job = jobs[index - 1]
        record = records[job["id"]]
        if model != job["model"] or line != encode_row(index, job, record, aliases):
            raise ValueError("Compact row metadata or output differs from source")
        if decoded["final"] != final_value(record):
            raise ValueError("JSON output round trip differs from source")
    return len(seen)


def build_companion(source: Path, destination: Path, *, expected_records: int = 6336) -> dict:
    source, destination = source.resolve(), destination.resolve()
    if destination.exists():
        raise FileExistsError(destination)
    archive = source.with_suffix(".zip")
    archive_sha = digest(archive.read_bytes())
    stated_archive_sha = archive.with_suffix(".zip.sha256").read_text(encoding="utf-8").split()[0]
    if archive_sha != stated_archive_sha:
        raise ValueError("Source archive SHA256 mismatch")
    source_manifest = json.loads((source / "manifest.json").read_text(encoding="utf-8"))
    entries = {entry["path"]: entry for entry in source_manifest["files"]}
    consumed = {}
    with zipfile.ZipFile(archive) as zipped:
        if zipped.read("manifest.json") != (source / "manifest.json").read_bytes():
            raise ValueError("Source manifest differs from archived manifest")

        def read(name: str) -> bytes:
            data = (source / name).read_bytes()
            if digest(data) != entries[name]["sha256"] or data != zipped.read(name):
                raise ValueError(f"Source file is not the archived manifest member: {name}")
            consumed[name] = digest(data)
            return data

        jobs = json.loads(read(CAMPAIGN + "/jobs.json"))
        cases = json.loads(read(CAMPAIGN + "/cases.json"))
        if len(jobs) != expected_records or len({job["id"] for job in jobs}) != len(jobs):
            raise ValueError("Wrong number of jobs or duplicate job identifiers")
        aliases = {case["id"]: f"C{index:02d}" for index, case in enumerate(cases, 1)}
        if len(aliases) != len(cases):
            raise ValueError("Duplicate case identifiers")
        records = {job["id"]: json.loads(read(CAMPAIGN + f"/records/{job['id']}.json")) for job in jobs}
        intro = read("README_RELECTURE.md").decode("utf-8").split("## Pièces et intégrité", 1)[0].rstrip()
        context = read("CONTEXTE_AUTONOME.md").decode("utf-8")
        form = read("FORMULAIRE_RELECTURE.md").decode("utf-8")
        plan = read(CAMPAIGN + "/PLAN_EXPLORATOIRE_v1.md").decode("utf-8")
        plan_seal = read(CAMPAIGN + "/PLAN_EXPLORATOIRE_v1.sha256").decode("utf-8")
        if digest(plan.encode("utf-8")) != plan_seal.split()[0]:
            raise ValueError("Plan seal mismatch")
        corpus = read("pieces/lectures/REFERENCE_CORPUS.md").decode("utf-8")

    model_order = list(dict.fromkeys(job["model"] for job in jobs))
    grouped = {model: [] for model in model_order}
    for index, job in enumerate(jobs, 1):
        grouped[job["model"]].append(encode_row(index, job, records[job["id"]], aliases))
    rows = [(model, row) for model, lines in grouped.items() for row in lines]
    validate_rows(rows, jobs, records, aliases)
    description = [
        "# Compagnon de lecture LLM P6 - v1", "",
        "Ce fichier réunit la fiche commune, le plan intégral, la référence des stimuli et toutes les sorties finales.",
        "Il ne contient aucun score, agrégat de performance, classement ni interprétation des réponses.",
        "Les sorties sont transcrites sans normalisation. Le regroupement par modèle sert uniquement à la lecture.",
        "Le fichier Markdown est la transcription canonique ; le PDF est sa vue de lecture, avec retours visuels à la ligne.", "",
        "## Provenance et pièces complémentaires", "",
        f"Archive source : {archive.name}", f"SHA256 de l'archive : {archive_sha}",
        "Le manifeste compagnon lie ce document à cette archive. Les fichiers HTTP, métadonnées complètes, code,",
        "stimuli exhaustifs et formulaire JSON restent dans l'archive source ; ils ne sont pas reproduits ici.",
        "Lire ce compagnon ne prouve donc pas l'inspection des corps HTTP, du code ou de toutes les métadonnées.", "",
        intro, "", context, "", form, "",
        "# Plan intégral - copie sans modification", "", plan, "",
        "# Référence du corpus - copie de la pièce source", "", corpus, "",
        "# Contrat de lecture des sorties", "",
        "Chaque ligne contient cinq champs séparés par point-virgule, suivis d'une valeur JSON complète.",
        "Ce format est un texte délimité avec suffixe JSON, pas un CSV RFC 4180 : séparer au maximum cinq fois.",
        "Les points-virgules contenus dans le suffixe font partie du JSON. Le suffixe est une chaîne intégrale,",
        "ou null si le canal final est absent/null. Une chaîne vide reste \"\". Les retours, tabulations et caractères",
        "non ASCII sont échappés par JSON ; décoder le JSON restitue exactement la chaîne source, sans trim ni correction.",
        "Les espaces simples sont aussi écrits \\u0020 pour résister à leur contraction typographique dans le PDF.",
        "Le statut V signifie uniquement technical_status=valid, jamais une réponse sémantiquement correcte.",
        "Tout autre statut est recopié textuellement. Les avertissements et erreurs détaillés restent dans la trace source.", "",
        "```text", "reference;cas;condition;graine;statut;final_json", "```", "",
        f"La référence rNNNN est l'index global 1-based dans {CAMPAIGN}/jobs.json.",
        "La ligne r0001 se résout donc par jobs[0] ; son identifiant long est jobs[index-1]['id'].",
        f"La trace correspondante est {CAMPAIGN}/records/<id>.json.",
        "Le modèle est indiqué par le titre du bloc. L'index global conserve l'ordre préparé ; il n'est pas renuméroté par modèle.",
        "Les tableaux regroupent les sorties par modèle en conservant, dans chaque bloc, leur ordre global d'origine.", "",
        "Conditions factorielles : quatre bits, dans l'ordre A B C D du plan (0 absent/rendu de référence, 1 intervention).",
        "Les témoins ont des codes distincts : " + "; ".join(f"{code}={name}" for name, code in CONTROL_CODES.items()) + ".",
        "Graines : 1=1001 ; 2=1002 ; 3=1003. Les aliases de cas suivent l'ordre de cases.json.", "",
        "| Alias | Identifiant exact du cas |", "|---|---|",
        *(f"| {alias} | {case_id} |" for case_id, alias in aliases.items()), "",
    ]
    for model, lines in grouped.items():
        description.extend([f"# Sorties finales - {model}", "", "```text", *lines, "```", ""])
    markdown = "\n".join(description)
    # Re-parse the final serialized document, not merely the intermediate rows.
    reread_rows = []
    current_model = None
    for line in markdown.splitlines():
        if line.startswith("# Sorties finales - "):
            current_model = line.removeprefix("# Sorties finales - ")
        elif current_model and re.match(r"^r[0-9]{4,};", line):
            reread_rows.append((current_model, line))
    checked = validate_rows(reread_rows, jobs, records, aliases)
    if plan not in markdown or corpus not in markdown:
        raise ValueError("Complete plan or corpus reference missing")
    destination.mkdir(parents=True)
    stem = "COMPAGNON_LLM_v1"
    md_path = destination / (stem + ".md")
    md_path.write_bytes(markdown.encode("utf-8"))
    render_markdown_pdf(markdown, destination / (stem + ".pdf"), compact=True)
    source_record_digests = {name: sha for name, sha in consumed.items() if "/records/" in name}
    manifest = {
        "schema_version": "p6-compact-reading-v1", "purpose": "lossless_transcription_no_analysis",
        "source_archive": {"name": archive.name, "bytes": archive.stat().st_size, "sha256": archive_sha},
        "source_manifest_sha256": digest((source / "manifest.json").read_bytes()),
        "source_documents": {name: sha for name, sha in consumed.items() if "/records/" not in name},
        "record_set_sha256": digest(json.dumps(source_record_digests, sort_keys=True).encode("utf-8")),
        "record_count": checked, "round_trip_verified_rows": checked, "global_index_base": 1,
        "case_aliases": aliases, "control_codes": CONTROL_CODES, "seed_aliases": SEEDS,
        "markdown_characters": len(markdown), "markdown_utf8_bytes": len(markdown.encode("utf-8")),
        "llm_tokens": None, "token_note": "No provider tokenizer used; character count is not a token count.",
        "files": [],
    }
    for path in (md_path, destination / (stem + ".pdf")):
        manifest["files"].append({"path": path.name, "bytes": path.stat().st_size, "sha256": digest(path.read_bytes())})
    (destination / "SOURCE_ARCHIVE.sha256").write_text(f"{archive_sha}  {archive.name}\n", encoding="utf-8")
    manifest_path = destination / "manifest_compagnon.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (destination / "manifest_compagnon.sha256").write_text(f"{digest(manifest_path.read_bytes())}  {manifest_path.name}\n", encoding="utf-8")
    return {"destination": str(destination), "records": checked, "markdown_characters": len(markdown),
            "markdown_utf8_bytes": len(markdown.encode("utf-8")), "source_archive_sha256": archive_sha}


def verify_pdf(destination: Path) -> dict:
    """Extract PDF body text and verify every reconstructed row against Markdown.

    Requires existing pdfplumber/pypdfium2, available in the bundled runtime.
    This reads and transcribes existing outputs only; it computes no score.
    """
    import pdfplumber
    import pypdfium2

    stem = "COMPAGNON_LLM_v1"
    markdown = (destination / (stem + ".md")).read_text(encoding="utf-8")
    expected = {decode_row(line)["index"]: line for line in markdown.splitlines() if re.match(r"^r[0-9]{4,};", line)}
    actual, row_pages, pending = {}, {}, None
    page_lengths, model_last_pages, model_first_pages = [], [], []

    def finish() -> None:
        nonlocal pending
        if pending is None:
            return
        index, text = pending
        if index in actual:
            raise ValueError("Duplicate reference in PDF extraction")
        actual[index] = text
        pending = None

    with pdfplumber.open(destination / (stem + ".pdf")) as pdf:
        for page_index, page in enumerate(pdf.pages, 1):
            # Crop only the footer and outer margin, never body content.
            page_text = page.crop((40, 30, float(page.width) - 40, float(page.height) - 40)).extract_text(x_tolerance=1, y_tolerance=3) or ""
            page_lengths.append(len(page_text))
            for char in page.chars:
                if char["x0"] < 0 or char["x1"] > page.width + 0.5 or char["top"] < 0 or char["bottom"] > page.height + 0.5:
                    raise ValueError(f"Glyph outside PDF page {page_index}")
            for line in page_text.splitlines():
                if line.startswith("Sorties finales - "):
                    if pending is not None:
                        model_last_pages.append(max(row_pages[pending[0]]))
                    finish()
                    model_first_pages.append(page_index)
                elif re.match(r"^r[0-9]{4,};", line):
                    finish()
                    index = int(line.split(";", 1)[0][1:])
                    pending = (index, line)
                    row_pages[index] = [page_index]
                elif pending is not None:
                    pending = (pending[0], pending[1] + line.strip())
                    if page_index not in row_pages[pending[0]]:
                        row_pages[pending[0]].append(page_index)
        if pending is not None:
            model_last_pages.append(max(row_pages[pending[0]]))
        finish()
        total_pages = len(pdf.pages)
    if set(actual) != set(expected):
        raise ValueError(f"PDF row IDs differ: expected {len(expected)}, extracted {len(actual)}")
    mismatches = [index for index in expected if actual[index] != expected[index]]
    if mismatches:
        raise ValueError(f"PDF row text differs at global references: {mismatches[:12]}")
    longest = sorted(expected, key=lambda index: len(expected[index]), reverse=True)[:5]
    selected_pages = {1, total_pages, *model_first_pages, *model_last_pages}
    selected_pages.update(page for index in longest for page in row_pages[index])
    selected_pages.add(1 + max(range(total_pages), key=page_lengths.__getitem__))
    image_directory = ROOT / "tmp/pdfs/p6_recall_compacte_v1"
    image_directory.mkdir(parents=True, exist_ok=True)
    pdf = pypdfium2.PdfDocument(destination / (stem + ".pdf"))
    for page in sorted(selected_pages):
        pdf[page - 1].render(scale=1.6).to_pil().save(image_directory / f"page-{page:03d}.png")
    report = {"purpose": "transcription_and_layout_integrity_only", "pdf_pages": total_pages,
              "markdown_rows": len(expected), "pdf_round_trip_verified_rows": len(actual),
              "body_glyphs_inside_page": True, "rendered_for_visual_inspection": sorted(selected_pages),
              "visual_inspection_completed": False, "image_directory": str(image_directory),
              "llm_tokens": None, "token_note": "No provider tokenizer used; exact character/byte counts are in the manifest."}
    report_path = destination / "verification_lecture.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest_path = destination / "manifest_compagnon.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["pdf_pages"] = total_pages
    manifest["pdf_round_trip_verified_rows"] = len(actual)
    manifest["files"] = [entry for entry in manifest["files"] if entry["path"] != report_path.name]
    manifest["files"].append({"path": report_path.name, "bytes": report_path.stat().st_size, "sha256": digest(report_path.read_bytes())})
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (destination / "manifest_compagnon.sha256").write_text(f"{digest(manifest_path.read_bytes())}  {manifest_path.name}\n", encoding="utf-8")
    return report


def finalize_after_visual_review(destination: Path) -> dict:
    """Record the caller's completed visual review, then create a new ZIP."""
    archive = destination.with_suffix(".zip")
    checksum = archive.with_suffix(".zip.sha256")
    if archive.exists() or checksum.exists():
        raise FileExistsError(archive)
    report_path = destination / "verification_lecture.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if report["pdf_round_trip_verified_rows"] != report["markdown_rows"]:
        raise ValueError("PDF round trip verification is incomplete")
    report["visual_inspection_completed"] = True
    report["visual_inspection_note"] = "The calling agent visually inspected every page listed in rendered_for_visual_inspection; no clipping or overlap observed."
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest_path = destination / "manifest_compagnon.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    names = ["COMPAGNON_LLM_v1.md", "COMPAGNON_LLM_v1.pdf", "SOURCE_ARCHIVE.sha256", "verification_lecture.json"]
    manifest["files"] = [{"path": name, "bytes": (destination / name).stat().st_size,
                          "sha256": digest((destination / name).read_bytes())} for name in names]
    manifest["exporter"] = {"path": "scripts/export_p6_recall_reading.py", "sha256": digest(Path(__file__).read_bytes())}
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (destination / "manifest_compagnon.sha256").write_text(f"{digest(manifest_path.read_bytes())}  {manifest_path.name}\n", encoding="utf-8")
    names.extend(["manifest_compagnon.json", "manifest_compagnon.sha256"])
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zipped:
        for name in sorted(names):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            zipped.writestr(info, (destination / name).read_bytes())
    with zipfile.ZipFile(archive) as zipped:
        if zipped.testzip() is not None:
            raise ValueError("Companion ZIP CRC failed")
        if any(zipped.read(name) != (destination / name).read_bytes() for name in names):
            raise ValueError("Companion ZIP content differs from final files")
    archive_sha = digest(archive.read_bytes())
    checksum.write_text(f"{archive_sha}  {archive.name}\n", encoding="utf-8")
    return {"archive": str(archive), "archive_bytes": archive.stat().st_size, "archive_sha256": archive_sha,
            "pdf_pages": report["pdf_pages"], "pdf_round_trip_verified_rows": report["pdf_round_trip_verified_rows"],
            "inspected_pages": report["rendered_for_visual_inspection"]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--verify-pdf", action="store_true")
    parser.add_argument("--finalize-after-visual-review", action="store_true")
    args = parser.parse_args()
    if args.finalize_after_visual_review:
        result = finalize_after_visual_review(args.destination)
    elif args.verify_pdf:
        result = verify_pdf(args.destination)
    else:
        if args.source is None:
            parser.error("--source is required for creation")
        result = build_companion(args.source, args.destination)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
