"""Pure fixtures and verdict logic for the Gemma 3 P7 admission bench (banc A).

The matrix reuses the frozen Qwen 3.8 admission cells verbatim (same seed
20260817): every panel candidate takes exactly the same exam. Only the
deterministic call order is salted with the Gemma 3 digest, and the identity
and GPU guards pin the Gemma 3 artifact.
"""
from __future__ import annotations

import hashlib
from typing import Any

from eval.p7_evidence import pack_sha256
from eval.p7_qwen38_admission import (
    EXPECTED_CALLS,
    REPETITIONS,
    AdmissionJob,
    admission_cells,
    summarize_records,
)

__all__ = [
    "CANDIDATE_MODEL",
    "CANDIDATE_DIGEST",
    "CANDIDATE_FAMILY",
    "CANDIDATE_QUANTIZATION",
    "EXPECTED_CALLS",
    "REPETITIONS",
    "admission_cells",
    "admission_jobs",
    "summarize_records",
    "verify_candidate_identity",
    "verify_candidate_fully_loaded_on_gpu",
]

CANDIDATE_MODEL = "gemma3:27b"
CANDIDATE_DIGEST = "a418f5838eaf7fe2cfe0a3046c8384b68ba43a4435542c942f9db00a5f342203"
CANDIDATE_FAMILY = "gemma3"
CANDIDATE_QUANTIZATION = "Q4_K_M"
ADMISSION_SEED = 20260829


def admission_jobs() -> tuple[AdmissionJob, ...]:
    jobs = [
        AdmissionJob(cell, repetition)
        for cell in admission_cells()
        for repetition in range(1, REPETITIONS + 1)
    ]

    def order_key(job: AdmissionJob) -> str:
        material = (
            f"{ADMISSION_SEED}\0gemma3-admission\0{CANDIDATE_DIGEST}\0"
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


def verify_candidate_fully_loaded_on_gpu(runtime: dict[str, Any]) -> None:
    observed = runtime.get("loaded_models", {}).get(CANDIDATE_MODEL)
    if not isinstance(observed, dict):
        raise RuntimeError("candidate must be loaded before the admission lock is acquired")
    if observed.get("digest") != CANDIDATE_DIGEST:
        raise RuntimeError("loaded candidate digest differs from the frozen artifact")
    size = observed.get("size")
    size_vram = observed.get("size_vram")
    if not isinstance(size, int) or size <= 0 or size_vram != size:
        raise RuntimeError(
            f"candidate is not fully loaded on GPU: size={size}, size_vram={size_vram}"
        )
