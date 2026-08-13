"""Cycle de vie du runner P7 V8, sans Ollama ni donnée de campagne."""
from __future__ import annotations

import json
import os

import pytest

from scripts.p7_v8 import PREREG_FREEZE_COMMIT, _acquire_q0_lock, run_lifecycle_smoke


def test_runner_targets_the_frozen_v8_commit():
    assert PREREG_FREEZE_COMMIT == "88590fcc59dc1845a4e747b7160da2f68d54afb5"


def test_lifecycle_smoke_writes_start_and_finish_for_the_same_child(tmp_path):
    output = tmp_path / "lifecycle"
    assert run_lifecycle_smoke(output, 0.001) == 0
    started = json.loads((output / "started.json").read_text(encoding="utf-8"))
    finished = json.loads((output / "finished.json").read_text(encoding="utf-8"))
    assert started["pid"] == finished["pid"] == os.getpid()
    assert finished["status"] == "PASS"


def test_v8_phase_lock_is_exclusive(tmp_path):
    lock = _acquire_q0_lock(tmp_path, "v8-first")
    assert lock.name == f"p7_v8_q0_{PREREG_FREEZE_COMMIT}.lock"
    with pytest.raises(FileExistsError):
        _acquire_q0_lock(tmp_path, "v8-second")
