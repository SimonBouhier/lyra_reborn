"""P6 diagnostic safeguards exercised with synthetic cases and no live client."""
from copy import deepcopy
from io import BytesIO
import json
from types import SimpleNamespace
import urllib.error

import pytest

from experiments.p6_recall import study
from experiments.p6_recall.corpus import build_cases, conditions, control_conditions


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def valid_result(payload, text="jade"):
    response = {
        "done": True,
        "done_reason": "stop",
        "message": {"role": "assistant", "content": text},
        "prompt_eval_count": 20,
        "eval_count": 2,
    }
    return {
        "request_body": json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
        "response_body": json.dumps(response, ensure_ascii=False),
        "response": response,
        "http_status": 200,
        "technical_status": "valid",
        "started_utc": "2026-09-08T10:00:00+00:00",
        "completed_utc": "2026-09-08T10:00:01+00:00",
        "elapsed_seconds": 1.0,
    }


@pytest.fixture
def small_study(tmp_path, monkeypatch):
    """Use the real lifecycle while every server operation is intercepted."""
    source_root = tmp_path / "source"
    source_root.mkdir()
    source = source_root / "measure.py"
    source.write_text("# fixed measurement source\n", encoding="utf-8")
    monkeypatch.setattr(study, "ROOT", source_root)
    monkeypatch.setattr(study, "SOURCE_PATHS", ("measure.py",))
    monkeypatch.setattr(study, "DEFAULT_MODELS", ("fake:test",))
    monkeypatch.setattr(study, "SEEDS", (11, 22))
    cases = build_cases()[:2]
    monkeypatch.setattr(study, "build_cases", lambda: deepcopy(cases))
    original_make_jobs = study.make_jobs
    monkeypatch.setattr(study, "make_jobs", lambda: original_make_jobs(("fake:test",)))

    def no_network(*args, **kwargs):
        pytest.fail("A deterministic study test attempted a network call")

    monkeypatch.setattr(study.urllib.request, "urlopen", no_network)
    metadata_calls = []

    def api(base, path, payload=None, timeout=5):
        metadata_calls.append((path, deepcopy(payload)))
        if path == "/api/version":
            return {"version": "0.33.3"}
        if path == "/api/tags":
            return {"models": [{"name": "fake:test", "digest": "fake-digest"}]}
        if path == "/api/show":
            return {"template": "fixed fake template", "parameters": "fixed fake defaults"}
        if path == "/api/ps":
            return {"models": [{"name": "fake:test", "size_vram": 1}]}
        pytest.fail("Unexpected metadata endpoint: " + path)

    monkeypatch.setattr(study.OllamaChatAdapter, "_json", staticmethod(api))
    monkeypatch.setattr(study, "invoke", lambda engine, payload: valid_result(payload))
    protocol = tmp_path / "PREREGISTRATION_v1.md"
    protocol.write_text("# Synthetic protocol\n2026-09-08\n", encoding="utf-8")
    protocol.with_suffix(".sha256").write_text(
        study.digest(protocol) + "  " + protocol.name + "\n", encoding="utf-8"
    )
    folder = tmp_path / "study"
    study.prepare(protocol, folder)
    study.qualify(folder)
    manifest, jobs = study.load_study(folder)
    return SimpleNamespace(
        folder=folder, protocol=protocol, source=source, manifest=manifest,
        jobs=jobs, cases=cases, metadata_calls=metadata_calls,
    )


@pytest.mark.parametrize("target", ["protocol", "source", "jobs", "manifest"])
def test_modified_seal_source_or_prepared_piece_is_refused(small_study, target):
    fixture = small_study
    path = {
        "protocol": fixture.folder / fixture.manifest["protocol"],
        "source": fixture.source,
        "jobs": fixture.folder / "jobs.json",
        "manifest": fixture.folder / "manifest.json",
    }[target]
    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(ValueError):
        study.load_study(fixture.folder)


def test_partial_collection_cannot_produce_analysis(small_study):
    fixture = small_study
    progress = study.run(fixture.folder, max_calls=1)
    assert progress["completed"] == 1
    assert progress["collection_complete"] is False
    destination = fixture.folder / "analysis.json"
    with pytest.raises(ValueError, match="incomplète"):
        study.analyse(fixture.folder, destination)
    assert not destination.exists()


@pytest.mark.parametrize("part", ["payload", "request_body", "response_body", "response", "technical_status"])
def test_modified_request_or_response_trace_is_refused(small_study, part):
    fixture = small_study
    assert study.run(fixture.folder)["collection_complete"]
    job = fixture.jobs[0]
    path = fixture.folder / "records" / (job["id"] + (".request.json" if part == "payload" else ".json"))
    record = read_json(path)
    if part == "payload":
        record["payload"]["messages"][-1]["content"] += " altered"
    elif part == "request_body":
        body = json.loads(record[part])
        body["messages"][-1]["content"] += " altered"
        record[part] = json.dumps(body)
    elif part == "response_body":
        body = json.loads(record[part])
        body["message"]["content"] = "altered"
        record[part] = json.dumps(body)
    elif part == "response":
        record[part]["message"]["content"] = "altered"
    else:
        record[part] = "transport_error"
    path.write_bytes(study.encoded(record))
    destination = fixture.folder / "analysis.json"
    with pytest.raises(ValueError):
        study.analyse(fixture.folder, destination)
    assert not destination.exists()


@pytest.mark.parametrize("durable_result", [False, True])
def test_resume_never_replays_a_call_when_final_acknowledgment_was_lost(small_study, monkeypatch, durable_result):
    fixture = small_study
    invoked = []

    def invoke(engine, payload):
        invoked.append(deepcopy(payload))
        return valid_result(payload)

    monkeypatch.setattr(study, "invoke", invoke)
    write_new = study.write_new
    final_path = fixture.folder / "records" / (fixture.jobs[0]["id"] + ".json")

    def interrupted_write(path, value):
        if path == final_path:
            if durable_result:
                write_new(path, value)
            raise RuntimeError("simulated lost final acknowledgment")
        return write_new(path, value)

    monkeypatch.setattr(study, "write_new", interrupted_write)
    with pytest.raises(RuntimeError, match="lost final"):
        study.run(fixture.folder, max_calls=1)
    assert len(invoked) == 1
    assert (fixture.folder / "records" / (fixture.jobs[0]["id"] + ".request.json")).exists()
    monkeypatch.setattr(study, "write_new", write_new)
    if durable_result:
        # The JSON was durable, but its seal was never created. Do not silently
        # bless that incomplete evidence or spend another model call on it.
        with pytest.raises((ValueError, FileNotFoundError)):
            study.run(fixture.folder, max_calls=1)
    else:
        study.run(fixture.folder, max_calls=1)
    first_payload = study.payload_for(fixture.jobs[0], fixture.manifest)
    assert invoked.count(first_payload) == 1
    row = read_json(final_path)
    assert row["technical_status"] == ("valid" if durable_result else "uncertain_execution")
    if not durable_result:
        assert len(invoked) == 1
        assert row["response"] is None


def test_modified_existing_result_is_refused_before_next_call(small_study, monkeypatch):
    fixture = small_study
    study.run(fixture.folder, max_calls=1)
    path = fixture.folder / "records" / (fixture.jobs[0]["id"] + ".json")
    path.write_bytes(path.read_bytes() + b"\n")
    monkeypatch.setattr(study, "invoke", lambda *args: pytest.fail("Resumed after altered evidence"))
    with pytest.raises(ValueError):
        study.run(fixture.folder, max_calls=1)


@pytest.mark.parametrize("error", [
    urllib.error.URLError("offline"), TimeoutError("timeout"), OSError("socket closed"),
])
def test_invoke_retains_transport_failure_and_exact_request(monkeypatch, error):
    def fail(request, timeout):
        raise error

    monkeypatch.setattr(study.urllib.request, "urlopen", fail)
    payload = {"model": "fake:test", "messages": [{"role": "user", "content": "État ?"}]}
    result = study.invoke({"base_url": "http://127.0.0.1:1", "timeout": 1}, payload)
    assert result["technical_status"] == "transport_error"
    assert result["http_status"] is None
    assert type(error).__name__ in result["transport_error"]
    assert result["response"] is None
    assert json.loads(result["request_body"]) == payload
    assert result["elapsed_seconds"] >= 0


def test_invoke_retains_http_error_body(monkeypatch):
    body = b'{"error":"context overflow"}'

    def fail(request, timeout):
        raise urllib.error.HTTPError(request.full_url, 400, "Bad Request", {}, BytesIO(body))

    monkeypatch.setattr(study.urllib.request, "urlopen", fail)
    result = study.invoke({"base_url": "http://127.0.0.1:1", "timeout": 1}, {"model": "fake:test"})
    assert result["technical_status"] == "transport_error"
    assert result["http_status"] == 400
    assert result["response_body"].encode() == body
    assert result["response"] == {"error": "context overflow"}


def test_failed_transport_is_durable_stops_block_and_is_not_retried(small_study, monkeypatch):
    fixture = small_study
    calls = []

    def fail(engine, payload):
        calls.append(deepcopy(payload))
        return {
            "technical_status": "transport_error", "response": None,
            "request_body": json.dumps(payload), "response_body": None,
            "http_status": None, "transport_error": "TimeoutError: deliberate fixture",
        }

    monkeypatch.setattr(study, "invoke", fail)
    progress = study.run(fixture.folder)
    assert progress["completed"] == 1
    assert progress["collection_complete"] is False
    first = fixture.jobs[0]
    path = fixture.folder / "records" / (first["id"] + ".json")
    retained = path.read_bytes()
    assert read_json(path)["transport_error"] == "TimeoutError: deliberate fixture"
    assert len(calls) == 1
    study.run(fixture.folder, max_calls=1)
    assert len(calls) == 2
    assert calls[0] != calls[1]
    assert path.read_bytes() == retained


@pytest.mark.parametrize("failure", ["transport_error", "invalid_array", "invalid_message", "output_truncated"])
def test_technical_failures_remain_in_planned_denominator(small_study, monkeypatch, failure):
    fixture = small_study
    lookup = {study.encoded(study.payload_for(job, fixture.manifest)): job for job in fixture.jobs}
    bad_job = next(job for job in fixture.jobs if job["kind"] == "factorial")
    invoked = []
    expected_status = "invalid_response" if failure.startswith("invalid_") else failure

    def outcome(engine, payload):
        job = lookup[study.encoded(payload)]
        invoked.append(job["id"])
        result = valid_result(payload, job["expected"])
        if job["id"] != bad_job["id"]:
            return result
        result["technical_status"] = expected_status
        if failure == "transport_error":
            result.update(http_status=None, response_body=None, response=None, transport_error="TimeoutError: fixture")
        else:
            if failure == "invalid_array":
                result["response"] = ["non-object server JSON"]
            elif failure == "invalid_message":
                result["response"]["message"] = "non-object message"
            else:
                result["response"]["done_reason"] = "length"
            result["response_body"] = json.dumps(result["response"])
        return result

    monkeypatch.setattr(study, "invoke", outcome)
    progress = study.run(fixture.folder)
    if not progress["collection_complete"]:
        assert study.run(fixture.folder)["collection_complete"]
    assert invoked.count(bad_job["id"]) == 1
    analysis = study.analyse(fixture.folder, fixture.folder / "analysis.json")
    model = analysis["models"]["fake:test"]
    assert model["planned"] == 64
    assert model["valid"] == 63
    assert model["success_over_planned"] == pytest.approx(63 / 64)
    assert model["success_over_valid"] == 1
    row = next(row for row in analysis["scores"] if row["job_id"] == bad_job["id"])
    assert row["technical_status"] == row["category"] == expected_status
    assert row["success"] is False


def test_qualification_keeps_received_response_when_postcheck_fails(small_study, monkeypatch):
    fixture = small_study
    other = fixture.folder.parent / "other-study"
    study.prepare(fixture.protocol, other)
    original_api = study.OllamaChatAdapter._json

    def api(base, path, payload=None, timeout=5):
        if path == "/api/ps":
            raise RuntimeError("postcheck unavailable")
        return original_api(base, path, payload, timeout)

    monkeypatch.setattr(study.OllamaChatAdapter, "_json", staticmethod(api))
    report = study.qualify(other)
    assert report["passed"] is False
    responses = list((other / "qualification").glob("*-response.json"))
    assert len(responses) == 1, "A received response must survive a failed metadata postcheck"
    assert read_json(responses[0])["response"]["message"]["content"] == "jade"
    postchecks = list((other / "qualification").glob("*-postcheck.json"))
    assert len(postchecks) == 1
    assert "postcheck unavailable" in read_json(postchecks[0])["error"]
    monkeypatch.setattr(study, "invoke", lambda *args: pytest.fail("A failed qualification was admitted"))
    with pytest.raises(ValueError, match="technique incomplète"):
        study.run(other)


def test_exact_effects_and_interactions_exclude_controls_and_weight_repetitions(small_study, monkeypatch):
    fixture = small_study
    lookup = {study.encoded(study.payload_for(job, fixture.manifest)): job for job in fixture.jobs}
    first_case = fixture.cases[0]["id"]

    def outcome(engine, payload):
        job = lookup[study.encoded(payload)]
        if job["kind"] == "control":
            success = False
        elif job["case"]["id"] == first_case:
            success = job["factors"]["A"] and (job["seed"] == 22 or job["factors"]["B"])
        else:
            success = job["seed"] == 22 or job["factors"]["B"]
        return valid_result(payload, job["expected"] if success else "incorrect")

    monkeypatch.setattr(study, "invoke", outcome)
    assert study.run(fixture.folder)["collection_complete"]
    analysis = study.analyse(fixture.folder, fixture.folder / "analysis.json")
    model = analysis["models"]["fake:test"]
    assert model["planned"] == model["valid"] == 64
    assert analysis["all_planned_jobs"] == 88
    assert model["success_over_planned"] == pytest.approx(9 / 16)
    assert model["success_over_valid"] == pytest.approx(9 / 16)
    assert model["main_effects"] == pytest.approx({"A": 3 / 8, "B": 3 / 8, "C": 0, "D": 0})
    assert model["two_factor_interactions"] == pytest.approx({"AB": 1 / 4, "AC": 0, "AD": 0, "BC": 0, "BD": 0, "CD": 0})
    assert set(model["controls"]) == set(control_conditions())
    assert all(control == {"planned": 4, "successes": 0} for control in model["controls"].values())


def test_jobs_are_paired_complete_and_deterministically_ordered(monkeypatch):
    cases = build_cases()[:2]
    monkeypatch.setattr(study, "build_cases", lambda: deepcopy(cases))
    monkeypatch.setattr(study, "SEEDS", (11, 22, 33))
    models = ("fake:a", "fake:b", "fake:c", "fake:d")
    jobs = study.make_jobs(models)
    assert jobs == study.make_jobs(models)
    assert len({job["id"] for job in jobs}) == len(jobs)
    blocks = list(dict.fromkeys(job["block"] for job in jobs))
    assert blocks == [
        f"r{repetition}-{model}"
        for repetition in range(3)
        for model in models[repetition:] + models[:repetition]
    ]
    for model in models:
        for seed in (11, 22, 33):
            for case in cases:
                group = [job for job in jobs if job["model"] == model and job["seed"] == seed and job["case"]["id"] == case["id"]]
                assert len(group) == len(conditions()) + len(control_conditions())
                assert {job["condition"] for job in group if job["kind"] == "factorial"} == {condition["id"] for condition in conditions()}
                assert all(job["case"] == case for job in group)


def test_engine_change_stops_before_any_model_call(small_study, monkeypatch):
    fixture = small_study

    def drift(client):
        return dict(fixture.manifest["engines"]["fake:test"], digest="changed")

    monkeypatch.setattr(study.OllamaChatAdapter, "freeze", lambda self, client: drift(client))
    monkeypatch.setattr(study, "invoke", lambda *args: pytest.fail("A changed engine was invoked"))
    with pytest.raises(ValueError, match="modifié"):
        study.run(fixture.folder)
    assert not list((fixture.folder / "records").glob("*.request.json"))


def test_complete_collection_can_be_moved_and_analysed_without_original_paths(small_study, tmp_path, monkeypatch):
    fixture = small_study
    assert study.run(fixture.folder)["collection_complete"]
    relocation = tmp_path / "another-root"
    relocation.mkdir()
    moved_study = relocation / "campaign"
    moved_sources = relocation / "sources"
    moved_original_protocol = relocation / "unused-original-protocol.md"

    # Only move this test's own temporary paths, all within its resolved root.
    temporary_root = tmp_path.resolve()
    moves = (
        (fixture.folder, moved_study),
        (fixture.source.parent, moved_sources),
        (fixture.protocol, moved_original_protocol),
    )
    for source, destination in moves:
        assert source.resolve().is_relative_to(temporary_root)
        assert destination.resolve().is_relative_to(temporary_root)
        source.rename(destination)
        assert not source.exists()

    monkeypatch.setattr(study, "ROOT", moved_sources)
    metadata_calls_before = list(fixture.metadata_calls)
    manifest, jobs = study.load_study(moved_study)
    assert manifest["protocol"] == fixture.manifest["protocol"]
    assert (moved_study / manifest["protocol"]).is_file()
    assert jobs == fixture.jobs
    destination = moved_study / "analysis.json"
    analysis = study.analyse(moved_study, destination)
    assert destination.is_file()
    assert analysis["all_planned_jobs"] == len(fixture.jobs) == 88
    assert analysis["models"]["fake:test"]["planned"] == 64
    assert analysis["models"]["fake:test"]["valid"] == 64
    assert analysis["models"]["fake:test"]["success_over_planned"] == 1
    assert fixture.metadata_calls == metadata_calls_before
