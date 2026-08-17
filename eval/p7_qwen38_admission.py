"""Pure fixtures and verdict logic for the Qwen 3.8 P7 admission bench."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
from typing import Any, Literal

from eval.p7_evidence import EvidencePack, invert_evidence_pack, pack_sha256
from eval.p7_v7_q0 import fixture_orientations, q0_fixtures
from eval.p7_v9_judge import qminus1_evidence_pack


CANDIDATE_MODEL = "qwen3.8:27b"
CANDIDATE_DIGEST = "22130167c4c20e20c7b71454612966ca8e8171e9b3cc8ab6ce8aa6cbfec79643"
CANDIDATE_FAMILY = "qwen35"
CANDIDATE_QUANTIZATION = "Q4_K_M"
ADMISSION_SEED = 20260817
REPETITIONS = 3
EXPECTED_CALLS = 24


@dataclass(frozen=True)
class AdmissionCell:
    cell_id: str
    orientation: Literal["forward", "reverse"]
    pack: EvidencePack
    expected_preference: Literal["A", "B", "TIE"]


@dataclass(frozen=True)
class AdmissionJob:
    cell: AdmissionCell
    repetition: int


def admission_cells() -> tuple[AdmissionCell, ...]:
    parity = qminus1_evidence_pack()
    cells = [
        AdmissionCell("TRANSPORT_PARITY", "forward", parity, "TIE"),
        AdmissionCell("TRANSPORT_PARITY", "reverse", invert_evidence_pack(parity), "TIE"),
    ]
    for fixture in q0_fixtures():
        for oriented in fixture_orientations(fixture, ADMISSION_SEED):
            cells.append(
                AdmissionCell(
                    oriented.fixture_id,
                    oriented.orientation,
                    oriented.pack,
                    oriented.expected_preference,
                )
            )
    return tuple(cells)


def admission_jobs() -> tuple[AdmissionJob, ...]:
    jobs = [
        AdmissionJob(cell, repetition)
        for cell in admission_cells()
        for repetition in range(1, REPETITIONS + 1)
    ]

    def order_key(job: AdmissionJob) -> str:
        material = (
            f"{ADMISSION_SEED}\0qwen38-admission\0{CANDIDATE_DIGEST}\0"
            f"{job.cell.cell_id}\0{job.cell.orientation}\0{job.repetition}\0"
            f"{pack_sha256(job.cell.pack)}"
        ).encode("utf-8")
        return hashlib.sha256(material).hexdigest()

    jobs.sort(key=order_key)
    return tuple(jobs)


def verify_candidate_identity(runtime: dict[str, Any]) -> None:
    observed = runtime.get("models", {}).get(CANDIDATE_MODEL)
    if observed != CANDIDATE_DIGEST:
        raise RuntimeError(
            f"candidate digest mismatch: expected {CANDIDATE_DIGEST}, observed {observed}"
        )


def summarize_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for record in records:
        key = (record["cell_id"], record["orientation"])
        grouped.setdefault(key, []).append(record)

    cell_results: dict[str, dict[str, Any]] = {}
    for cell in admission_cells():
        key = (cell.cell_id, cell.orientation)
        selected = grouped.get(key, [])
        counts = Counter(item["observed_preference"] for item in selected)
        result_key = f"{cell.cell_id}:{cell.orientation}"
        cell_results[result_key] = {
            "expected_preference": cell.expected_preference,
            "calls": len(selected),
            "valid": sum(bool(item["valid"]) for item in selected),
            "correct": sum(bool(item["correct"]) for item in selected),
            "wire_clean": sum(bool(item["wire_clean"]) for item in selected),
            "preference_counts": dict(sorted(counts.items())),
            "unanimous_expected": (
                len(selected) == REPETITIONS
                and all(
                    item["valid"]
                    and item["correct"]
                    and item["wire_clean"]
                    and item["observed_preference"] == cell.expected_preference
                    for item in selected
                )
            ),
        }

    all_cells_present = len(grouped) == len(admission_cells())
    qualified = (
        len(records) == EXPECTED_CALLS
        and all_cells_present
        and all(item["unanimous_expected"] for item in cell_results.values())
    )
    return {
        "calls_planned": EXPECTED_CALLS,
        "calls_recorded": len(records),
        "cell_results": cell_results,
        "qualified_for_v10_design": qualified,
        "status": "QUALIFIED_FOR_V10_DESIGN" if qualified else "NOT_QUALIFIED_FOR_V10_DESIGN",
    }
