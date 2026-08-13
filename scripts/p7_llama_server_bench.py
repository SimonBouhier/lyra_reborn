#!/usr/bin/env python
"""Préflight sans inférence des GGUF gelés sur llama-server."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import time
from typing import Any, Iterator

import requests

from scripts.p7_v8 import JUDGES


LLAMA_BUILD = 10405
LLAMA_COMMIT = "e79e4bf66"


@dataclass(frozen=True)
class LlamaModel:
    name: str
    ollama_digest: str
    gguf: Path


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def server_command(executable: Path, model: LlamaModel, port: int) -> list[str]:
    return [
        str(executable),
        "--model",
        str(model.gguf),
        "--alias",
        model.name,
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
        "--ctx-size",
        "32768",
        "--gpu-layers",
        "all",
        "--reasoning",
        "off",
        "--no-webui",
    ]


def verify_server_binary(executable: Path) -> dict[str, Any]:
    if not executable.is_file():
        raise FileNotFoundError(f"llama-server executable not found: {executable}")
    completed = subprocess.run(
        [str(executable), "--version"],
        cwd=executable.parent,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=True,
        timeout=30,
    )
    version = completed.stdout.strip()
    if f"build {LLAMA_BUILD}" not in version or LLAMA_COMMIT not in version:
        raise RuntimeError(f"unexpected llama-server version: {version}")
    return {
        "version": version,
        "executable_sha256": file_sha256(executable),
    }


def _wait_healthy(
    base_url: str,
    process: subprocess.Popen[bytes],
    timeout: int,
) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    last_error = "not contacted"
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(
                f"llama-server exited during startup with code {process.returncode}"
            )
        try:
            response = requests.get(f"{base_url}/health", timeout=2)
            if response.status_code == 200:
                body = response.json()
                if isinstance(body, dict) and body.get("status") == "ok":
                    return body
            last_error = f"HTTP {response.status_code}: {response.text[:200]}"
        except (requests.RequestException, ValueError) as exc:
            last_error = f"{type(exc).__name__}: {exc}"
        time.sleep(1)
    raise TimeoutError(f"llama-server did not become healthy: {last_error}")


@contextmanager
def running_server(
    executable: Path,
    model: LlamaModel,
    port: int,
    startup_timeout: int,
    stdout_path: Path,
    stderr_path: Path,
) -> Iterator[dict[str, Any]]:
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
        process = subprocess.Popen(
            server_command(executable, model, port),
            cwd=executable.parent,
            stdin=subprocess.DEVNULL,
            stdout=stdout,
            stderr=stderr,
            creationflags=flags,
        )
        base_url = f"http://127.0.0.1:{port}"
        try:
            health = _wait_healthy(base_url, process, startup_timeout)
            models_response = requests.get(f"{base_url}/v1/models", timeout=10)
            models_response.raise_for_status()
            yield {
                "health": health,
                "models": models_response.json(),
                "pid": process.pid,
            }
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=30)


def preflight(
    executable: Path,
    models: tuple[LlamaModel, ...],
    port: int,
    startup_timeout: int,
    log_root: Path,
) -> dict[str, Any]:
    log_root.mkdir(parents=True, exist_ok=True)
    result: dict[str, Any] = {
        "schema_version": "lyra.p7.backend-bench-llama-preflight.v1",
        "server": verify_server_binary(executable),
        "models": {},
    }
    for index, model in enumerate(models):
        stdout_path = log_root / f"preflight-{index + 1}.stdout.log"
        stderr_path = log_root / f"preflight-{index + 1}.stderr.log"
        record = {
            "ollama_digest": model.ollama_digest,
            "gguf_path": str(model.gguf),
            "gguf_sha256_from_filename": model.gguf.name.removeprefix("sha256-"),
            "compatible": False,
            "server": None,
            "error": None,
        }
        try:
            if not model.gguf.is_file():
                raise FileNotFoundError(f"GGUF not found: {model.gguf}")
            with running_server(
                executable,
                model,
                port,
                startup_timeout,
                stdout_path,
                stderr_path,
            ) as meta:
                record["compatible"] = True
                record["server"] = meta
        except (OSError, RuntimeError, TimeoutError, requests.RequestException, ValueError) as exc:
            record["error"] = f"{type(exc).__name__}: {exc}"
        result["models"][model.name] = record
    result["compatible"] = all(
        item["compatible"] for item in result["models"].values()
    )
    return result


def _models_from_args(args: argparse.Namespace) -> tuple[LlamaModel, ...]:
    return (
        LlamaModel(JUDGES[0][0], JUDGES[0][1], args.qwen_gguf.resolve()),
        LlamaModel(JUDGES[1][0], JUDGES[1][1], args.glm_gguf.resolve()),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("preflight",))
    parser.add_argument("--llama-server", type=Path, required=True)
    parser.add_argument("--qwen-gguf", type=Path, required=True)
    parser.add_argument("--glm-gguf", type=Path, required=True)
    parser.add_argument("--port", type=int, default=18080)
    parser.add_argument("--startup-timeout", type=int, default=300)
    parser.add_argument("--output-root", type=Path, default=Path("data/runs"))
    args = parser.parse_args()
    if args.startup_timeout <= 0:
        parser.error("--startup-timeout must be positive")
    models = _models_from_args(args)
    executable = args.llama_server.resolve()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    log_root = args.output_root / f"p7_backend_llama_preflight_{stamp}"
    result = preflight(executable, models, args.port, args.startup_timeout, log_root)
    (log_root / "preflight.json").write_bytes(_canonical(result))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["compatible"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
