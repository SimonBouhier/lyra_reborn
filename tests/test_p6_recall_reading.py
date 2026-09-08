"""Compact reading export tests use fabricated outputs, never a live model."""
import json

import pytest

from scripts.export_p6_recall_reading import decode_row, encode_row, validate_rows


def fixture(kind="factorial", condition="A0_B1_C1_D0", status="valid", final="jade"):
    job = {"id": "long-job-id", "model": "fake-model", "case": {"id": "case-one", "template_id": "template-one"},
           "condition": condition, "kind": kind, "seed": 1002}
    record = {"job_id": job["id"], "model": job["model"], "case_id": "case-one",
              "template_id": "template-one", "condition": condition, "kind": kind,
              "seed": 1002, "technical_status": status, "response": {"message": {"content": final}}}
    return job, record


@pytest.mark.parametrize("final", ["jade", "", "a;b\n\r\t\"x\"\\end", "**jade**", "😀 é—…", "A\u2028B\u2029C", " a  b ", None])
def test_json_tail_round_trip_preserves_final_text_without_normalization(final):
    job, record = fixture(final=final)
    line = encode_row(1, job, record, {"case-one": "C01"})
    assert line.startswith("r0001;C01;0110;2;V;")
    assert "\n" not in line and "\r" not in line
    assert " " not in line
    assert decode_row(line)["final"] == final
    assert validate_rows([("fake-model", line)], [job], {"long-job-id": record}, {"case-one": "C01"}) == 1


@pytest.mark.parametrize("condition,code", [("current_only", "T1"), ("old_only", "T2"), ("unchanged", "T3"), ("unknown", "T4"), ("other_subject", "T5"), ("multiple_updates", "T6")])
def test_control_codes_do_not_reuse_factorial_bits(condition, code):
    job, record = fixture(kind="control", condition=condition, status="output_truncated")
    decoded = decode_row(encode_row(1, job, record, {"case-one": "C01"}))
    assert decoded["condition_code"] == code
    assert decoded["status"] == "output_truncated"


@pytest.mark.parametrize("field", ["job_id", "model", "case_id", "condition", "kind", "seed", "template_id"])
def test_record_metadata_mismatch_is_rejected(field):
    job, record = fixture()
    record[field] = "mismatch"
    with pytest.raises(ValueError, match="metadata"):
        encode_row(1, job, record, {"case-one": "C01"})


def test_omissions_duplicates_changed_output_and_wrong_model_are_rejected():
    job, record = fixture()
    aliases = {"case-one": "C01"}
    row = encode_row(1, job, record, aliases)
    for rows in ([], [("fake-model", row)] * 2, [("different-model", row)], [("fake-model", row.rsplit(";", 1)[0] + ';"altered"')]):
        with pytest.raises(ValueError):
            validate_rows(rows, [job], {"long-job-id": record}, aliases)


def test_unknown_factor_syntax_and_seed_are_rejected():
    job, record = fixture(condition="A0_B1_C1_D0_extra")
    with pytest.raises(ValueError, match="condition"):
        encode_row(1, job, record, {"case-one": "C01"})
    job, record = fixture()
    job["seed"] = record["seed"] = 42
    with pytest.raises(ValueError, match="seed"):
        encode_row(1, job, record, {"case-one": "C01"})
