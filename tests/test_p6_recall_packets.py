"""Exports documentaires P6 : sélection explicite, intégrité et rapport vide."""
import hashlib
import json
import zipfile

import pytest

from experiments.p6_recall.packets import build_packet, review_form, render_markdown_pdf


@pytest.fixture
def pieces(tmp_path):
    source = tmp_path / "inputs"
    source.mkdir()
    protocol = source / "protocol.md"
    protocol.write_text("# Protocole exemple\n\nFixture technique, aucune mesure réelle.\n", encoding="utf-8")
    (source / "unlisted.txt").write_text("EXCLU_NON_LISTE", encoding="utf-8")
    return {"protocol.md": protocol}


def test_packet_is_nonempty_self_contained_and_verifiable(tmp_path, pieces):
    archive = build_packet(tmp_path / "protocol-review", pieces)
    assert archive == tmp_path / "protocol-review.zip"
    with zipfile.ZipFile(archive) as zipped:
        assert zipped.testzip() is None
        names = set(zipped.namelist())
        assert {"pieces/protocol.md", "README_RELECTURE.md", "CONTEXTE_AUTONOME.md",
                "FORMULAIRE_RELECTURE.md", "FORMULAIRE_RELECTURE.json", "FICHE_RELECTURE.pdf",
                "export_trace.jsonl", "manifest.json", "manifest.sha256"} == names
        assert all(zipped.read(name) for name in names)
        assert zipped.read("FICHE_RELECTURE.pdf").startswith(b"%PDF-")
        assert b"EXCLU_NON_LISTE" not in b"".join(zipped.read(name) for name in names)
        manifest = json.loads(zipped.read("manifest.json"))
        assert manifest["stage"] == "protocol"
        assert manifest["review_performed"] is False
        assert {row["path"] for row in manifest["files"]} == names - {"manifest.json", "manifest.sha256"}
        for row in manifest["files"]:
            data = zipped.read(row["path"])
            assert row["sha256"] == hashlib.sha256(data).hexdigest()
            assert row["bytes"] == len(data)
        hashes = zipped.read("manifest.sha256").decode().splitlines()
        assert len(hashes) == len(names) - 1
        for line in hashes:
            digest, name = line.split("  ", 1)
            assert digest == hashlib.sha256(zipped.read(name)).hexdigest()
        trace = [json.loads(line) for line in zipped.read("export_trace.jsonl").decode().splitlines()]
        assert trace[0]["kind"] == "packet_assembly"
        assert trace[0]["experimental_evidence"] is False
        assert str(tmp_path) not in zipped.read("manifest.json").decode()
    checksum = archive.with_name(archive.name + ".sha256").read_text().strip()
    assert checksum == f"{hashlib.sha256(archive.read_bytes()).hexdigest()}  {archive.name}"


@pytest.mark.parametrize("existing", ["directory", "archive", "checksum"])
def test_no_existing_destination_is_overwritten(tmp_path, pieces, existing):
    destination = tmp_path / "review"
    if existing == "directory":
        destination.mkdir()
        sentinel = destination / "keep.txt"
    else:
        sentinel = tmp_path / ("review.zip" if existing == "archive" else "review.zip.sha256")
    sentinel.write_text("KEEP", encoding="utf-8")
    with pytest.raises(FileExistsError):
        build_packet(destination, pieces)
    assert sentinel.read_text() == "KEEP"


@pytest.mark.parametrize("alias", ["../escape.md", "/absolute.md", "C:/drive.md", "a\\b.md",
                                  "a/../b.md", "a//b.md", "./b.md", "con.md", "x:stream",
                                  "bad\nname.md", "a/trailing.md.", "a/space .md "])
def test_rejects_unsafe_archive_paths(tmp_path, pieces, alias):
    with pytest.raises(ValueError):
        build_packet(tmp_path / "review", {alias: pieces["protocol.md"]})
    assert not (tmp_path / "review").exists()


def test_rejects_case_collisions_and_empty_selection(tmp_path, pieces):
    with pytest.raises(ValueError):
        build_packet(tmp_path / "collision", {"A.md": pieces["protocol.md"], "a.md": pieces["protocol.md"]})
    with pytest.raises(ValueError):
        build_packet(tmp_path / "empty", {})
    empty = tmp_path / "empty.md"
    empty.write_text("")
    with pytest.raises(ValueError):
        build_packet(tmp_path / "empty-file", {"empty.md": empty})


def test_rejects_file_directory_collisions(tmp_path, pieces):
    with pytest.raises(ValueError):
        build_packet(tmp_path / "collision", {"code": pieces["protocol.md"], "code/file.py": pieces["protocol.md"]})
    assert not (tmp_path / "collision").exists()


def test_protocol_stage_rejects_result_paths(tmp_path, pieces):
    with pytest.raises(ValueError):
        build_packet(tmp_path / "review", {"results/raw.jsonl": pieces["protocol.md"]})
    assert not (tmp_path / "review").exists()


@pytest.mark.parametrize("forbidden", ["P7/design.md", "data/user/history.json", "data/users/history.json", "confirmation/case.json",
                                      "holdout/case.json", "reviews/other.md", "author_synthesis.md",
                                      "conclusions.md", "dialogue.db"])
def test_obvious_exclusions_cannot_be_renamed_into_packet(tmp_path, pieces, forbidden):
    source = tmp_path / forbidden
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("EXCLUDED", encoding="utf-8")
    with pytest.raises(ValueError):
        build_packet(tmp_path / "review", {"innocent.txt": source})
    assert not (tmp_path / "review").exists()


def test_form_has_no_verdict_or_invented_execution():
    form = review_form("protocol")
    assert form["reviewer"]["role"] is None
    assert form["conditions"]["execution_performed"] is False
    assert form["conditions"]["tools_used"] == []
    assert form["findings"] == []
    assert form["alternative_hypotheses"] == []
    assert form["limitations"] == []
    assert form["proposals"] == []
    assert form["verdict"]["value"] is None
    assert form["verdict"]["scope"] is None
    assert form["evidence_citation_example"]["path"] is None
    assert form["conditions"]["authorizations_received"] == []


def test_results_packet_copies_selected_raw_traces_and_custom_context(tmp_path, pieces):
    raw = tmp_path / "raw.jsonl"
    raw.write_text('{"fixture":true,"status":"UNTESTED"}\n', encoding="utf-8")
    pieces["runs/raw.jsonl"] = raw
    archive = build_packet(tmp_path / "results", pieces, stage="results",
                           context_markdown="# Contexte joint\n\nInformation de fixture autonome.\n")
    with zipfile.ZipFile(archive) as zipped:
        assert zipped.read("pieces/runs/raw.jsonl") == raw.read_bytes()
        assert "Information de fixture autonome" in zipped.read("CONTEXTE_AUTONOME.md").decode()
        intro = zipped.read("README_RELECTURE.md").decode()
        assert "résultats" in intro and "synthèse" in intro
        assert json.loads(zipped.read("FORMULAIRE_RELECTURE.json"))["stage"] == "results"


def test_pdf_renderer_is_public_and_exclusive(tmp_path):
    pdf = render_markdown_pdf("# Fiche autonome\n\nÉléments vérifiables.\n\n- Document\n- Preuve\n", tmp_path / "fiche.pdf")
    assert pdf.read_bytes().startswith(b"%PDF-")
    with pytest.raises(FileExistsError):
        render_markdown_pdf("# Remplacement", pdf)


def test_invalid_stage_and_directory_sources_fail_before_writes(tmp_path, pieces):
    with pytest.raises(ValueError):
        build_packet(tmp_path / "bad-stage", pieces, stage="other")
    with pytest.raises(ValueError):
        build_packet(tmp_path / "bad-source", {"folder": tmp_path / "inputs"})
    assert not (tmp_path / "bad-stage").exists()
    assert not (tmp_path / "bad-source").exists()


def test_empty_package_initializers_are_preserved(tmp_path, pieces):
    initializer = tmp_path / "__init__.py"
    initializer.write_bytes(b"")
    pieces["app/__init__.py"] = initializer
    archive = build_packet(tmp_path / "review", pieces)
    with zipfile.ZipFile(archive) as zipped:
        assert zipped.read("pieces/app/__init__.py") == b""


def test_full_protocol_pdf_is_derived_from_selected_markdown(tmp_path, pieces):
    archive = build_packet(tmp_path / "review", pieces, protocol_alias="protocol.md")
    with zipfile.ZipFile(archive) as zipped:
        assert zipped.read("PROTOCOLE_COMPLET.pdf").startswith(b"%PDF-")
        provenance = json.loads(zipped.read("manifest.json"))["full_protocol_pdf"]
        assert provenance["source"] == "pieces/protocol.md"
        assert provenance["source_sha256"] == hashlib.sha256(pieces["protocol.md"].read_bytes()).hexdigest()
    with pytest.raises(ValueError):
        build_packet(tmp_path / "wrong-protocol", pieces, protocol_alias="unlisted.md")


@pytest.fixture
def export_repository(tmp_path):
    from scripts import export_p6_recall_packets as exporter
    repository = tmp_path / "repository"
    for name in exporter.REPOSITORY_FILES:
        path = repository / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# Fixture technique\n", encoding="utf-8")
    protocol = repository / exporter.PROTOCOL
    protocol.parent.mkdir(parents=True)
    protocol.write_text("# Plan de fixture\n\nAucune donnée réelle.\n", encoding="utf-8")
    protocol.with_suffix(".sha256").write_text(exporter._digest(protocol) + "  " + protocol.name + "\n")
    campaign = repository / exporter.CAMPAIGN
    campaign.mkdir(parents=True)
    for path in (protocol, protocol.with_suffix(".sha256")):
        (campaign / path.name).write_bytes(path.read_bytes())
    for name in exporter.PREPARED_FILES[:4]:
        (campaign / name).write_text("[]\n")
    manifest = {"protocol": protocol.name, "protocol_sha256": exporter._digest(protocol),
                "sources": {"experiments/p6_recall/study.py": exporter._digest(repository / "experiments/p6_recall/study.py")},
                "files": {path.name: exporter._digest(path) for path in campaign.iterdir()}}
    (campaign / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (campaign / "manifest.json.sha256").write_text(exporter._digest(campaign / "manifest.json") + "  manifest.json\n")
    return repository, campaign


def test_protocol_recipe_never_reads_results_and_preserves_repository_paths(tmp_path, export_repository):
    from scripts import export_p6_recall_packets as exporter
    repository, campaign = export_repository
    (campaign / "analyse.json").write_text("EXCLU_AGREGATS")
    (campaign / "qualification").mkdir()
    (campaign / "qualification/verification.json").write_text("NON_LISIBLE_POUR_METHODE")
    archive = exporter.export_packet(tmp_path / "review", "protocol", repository=repository)
    with zipfile.ZipFile(archive) as zipped:
        assert "pieces/experiments/p6_recall/study.py" in zipped.namelist()
        assert "pieces/app/context.py" in zipped.namelist()
        assert "pieces/data/runs/p6-recall/v1/jobs.json" in zipped.namelist()
        assert "PROTOCOLE_COMPLET.pdf" in zipped.namelist()
        assert all("qualification/" not in name and "analyse.json" not in name for name in zipped.namelist())
        assert json.loads(zipped.read("pieces/SOURCES_EXPORT.json"))["qualification_included"] is False


def test_results_recipe_preserves_full_raw_and_pdf_channels_without_scoring(tmp_path, export_repository):
    from scripts import export_p6_recall_packets as exporter
    repository, campaign = export_repository
    job_id = "a" * 24
    case = {"id": "fixture", "question": "Valeur ?", "old_value": "ambre", "current_value": "jade", "source_role": "user"}
    condition = {"id": "A0_B0_C0_D0", "A": False, "B": False, "C": False, "D": False}
    job = {"id": job_id, "case": case, "condition": condition["id"], "kind": "factorial",
           "expected": "jade", "messages": [{"role": "system", "content": "SYSTEM de fixture"},
                                              {"role": "user", "content": "Valeur ? Réponse seule."}]}
    (campaign / "jobs.json").write_text(json.dumps([job]), encoding="utf-8")
    (campaign / "cases.json").write_text(json.dumps([case]), encoding="utf-8")
    (campaign / "conditions.json").write_text(json.dumps([condition]), encoding="utf-8")
    manifest = exporter._json(campaign / "manifest.json")
    for name in ("cases.json", "conditions.json", "jobs.json"):
        manifest["files"][name] = exporter._digest(campaign / name)
    (campaign / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (campaign / "manifest.json.sha256").write_text(exporter._digest(campaign / "manifest.json") + "  manifest.json\n")
    qualification = campaign / "qualification"
    qualification.mkdir()
    (qualification / "verification.json").write_text('{"files":{},"passed":false}')
    (qualification / "verification.json.sha256").write_text(exporter._digest(qualification / "verification.json") + "  verification.json\n")
    records = campaign / "records"
    records.mkdir()
    request = records / (job_id + ".request.json")
    request.write_text('{"payload":{"fixture":true}}')
    result = records / (job_id + ".json")
    row = {"job_id": job_id, "case_id": "fixture", "condition": "fixture", "model": "fake:test",
           "seed": 1, "technical_status": "valid", "request_sha256": exporter._digest(request),
           "response": {"message": {"content": "Texte de fixture intégral. **Fin** ``` incluse."}}}
    result.write_text(json.dumps(row), encoding="utf-8")
    result.with_suffix(".json.sha256").write_text(exporter._digest(result) + "  " + result.name + "\n")
    (campaign / "analyse.json").write_text("EXCLU_ANALYSE")
    archive = exporter.export_packet(tmp_path / "review", "results", repository=repository, include_raw_jsonl=True)
    with zipfile.ZipFile(archive) as zipped:
        raw = [json.loads(line) for line in zipped.read("pieces/raw.jsonl").decode().splitlines()]
        assert len(raw) == 2
        assert next(item["record"] for item in raw if item["source"].endswith(job_id + ".json")) == row
        assert all("score" not in item and "success" not in item for item in raw)
        assert zipped.read("pieces/lectures/SORTIES_01_fake_test_001.pdf").startswith(b"%PDF-")
        assert "**Fin** ``` incluse." in zipped.read("pieces/lectures/SORTIES_01_fake_test_001.md").decode()
        assert "pieces/lectures/SORTIES_INDEX.pdf" in zipped.namelist()
        reference = zipped.read("pieces/lectures/REFERENCE_CORPUS.md").decode()
        assert "SYSTEM de fixture" in reference and "Valeur ? Réponse seule." in reference
        assert "Valeur attendue pour ce stimulus : jade" in reference
        assert all("analyse.json" not in name for name in zipped.namelist())
