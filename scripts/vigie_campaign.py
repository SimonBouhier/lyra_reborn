#!/usr/bin/env python
"""CLI reproductible pour la campagne shadow V1 de La Vigie."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import time
from typing import Any, Mapping
from urllib.request import Request, urlopen

from agency.tools.vigie.campaign import (
    MODEL_DIGESTS,
    PANELS,
    CampaignError,
    Candidate,
    acquire_candidates,
    randomized_review_order,
    read_jsonl,
    score_campaign,
    seal_annotations,
    select_campaign_items,
    sha256_file,
    validate_prediction_inputs,
    write_jsonl,
)
from agency.tools.vigie.quarantine import (
    EPPQuarantineBridge,
    QuarantineDecision,
    QuarantineItem,
)


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CORPUS_DIR = ROOT / "corpora" / "vigie_shadow_v1"
DEFAULT_RUN_DIR = ROOT / "data" / "runs" / "vigie_shadow_v1"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--corpus-dir", type=Path, default=DEFAULT_CORPUS_DIR, help="local corpus directory"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    acquire = subparsers.add_parser("acquire", help="read public APIs and build review queue")
    acquire.add_argument("--polite-delay", type=float, default=1.0)

    subparsers.add_parser("annotate", help="resume the human annotation loop")
    subparsers.add_parser(
        "rebuild-excluded", help="replace EXCLUDE items with the next deterministic candidates"
    )
    subparsers.add_parser("seal", help="seal manually validated labels and content hashes")
    subparsers.add_parser("verify-models", help="verify frozen Ollama model digests")

    run = subparsers.add_parser("run", help="run the three blind EPP panels")
    run.add_argument(
        "--epp-root",
        type=Path,
        default=ROOT.parent / "EPP_Verdict",
        help="EPP_Verdict checkout containing the frozen sidecar",
    )
    run.add_argument("--output", type=Path, default=DEFAULT_RUN_DIR / "predictions.jsonl")

    score = subparsers.add_parser("score", help="score complete predictions after the blind run")
    score.add_argument("--predictions", type=Path, default=DEFAULT_RUN_DIR / "predictions.jsonl")
    score.add_argument("--output-dir", type=Path, default=DEFAULT_RUN_DIR)
    return parser


def _acquire(corpus_dir: Path, polite_delay: float) -> None:
    if polite_delay < 0:
        raise CampaignError("polite delay cannot be negative")
    candidates = acquire_candidates(polite_delay_seconds=polite_delay)
    items = select_campaign_items(candidates)
    corpus_dir.mkdir(parents=True, exist_ok=True)
    pool_path = corpus_dir / "candidate_pool.jsonl"
    queue_path = corpus_dir / "review_queue.jsonl"
    write_jsonl(pool_path, (candidate.to_json() for candidate in candidates))
    write_jsonl(queue_path, randomized_review_order([item.review_json() for item in items]))
    summary = {
        "eligible_candidates": len(candidates),
        "review_items": len(items),
        "sources": {
            source: sum(item.source == source for item in items)
            for source in ("github", "hackernews", "arxiv")
        },
        "pool_sha256": sha256_file(pool_path),
        "review_queue_sha256": sha256_file(queue_path),
    }
    (corpus_dir / "acquisition_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, sort_keys=True))


def _annotate(corpus_dir: Path) -> None:
    queue_path = corpus_dir / "review_queue.jsonl"
    annotations_path = corpus_dir / "annotations.jsonl"
    queue = read_jsonl(queue_path)
    existing_rows = read_jsonl(annotations_path) if annotations_path.exists() else []
    existing = {
        row["item_id"]: row["label"]
        for row in existing_rows
        if set(row) == {"item_id", "label"}
    }
    total = len(queue)
    for index, item in enumerate(queue, 1):
        item_id = item["item_id"]
        if item_id in existing:
            continue
        print("\n" + "=" * 79)
        print(f"[{index}/{total}] {item_id} | {item['source']} | {item['canonical_url']}")
        print("-" * 79)
        print(item["content"])
        print("-" * 79)
        while True:
            answer = input("Label [b]enign / [u]nsafe / e[x]clude / [q]uit: ").strip().lower()
            if answer == "q":
                return
            label = {"b": "BENIGN", "u": "UNSAFE", "x": "EXCLUDE"}.get(answer)
            if label:
                break
        existing[item_id] = label
        write_jsonl(
            annotations_path,
            ({"item_id": row["item_id"], "label": existing[row["item_id"]]} for row in queue if row["item_id"] in existing),
        )
        print(f"saved={len(existing)}/{total}")


def _rebuild_excluded(corpus_dir: Path) -> None:
    pool_path = corpus_dir / "candidate_pool.jsonl"
    queue_path = corpus_dir / "review_queue.jsonl"
    annotations_path = corpus_dir / "annotations.jsonl"
    exclusions_path = corpus_dir / "exclusions.jsonl"
    queue = read_jsonl(queue_path)
    annotations = read_jsonl(annotations_path)
    labels = {row["item_id"]: row["label"] for row in annotations}
    queue_by_id = {row["item_id"]: row for row in queue}
    excluded: set[tuple[str, str]] = set()
    if exclusions_path.exists():
        for row in read_jsonl(exclusions_path):
            excluded.add((row["source"], row["external_id"]))
    for item_id, label in labels.items():
        if label != "EXCLUDE":
            continue
        row = queue_by_id.get(item_id)
        if row is None:
            raise CampaignError(f"excluded annotation has no queue item: {item_id}")
        excluded.add((row["source"], row["external_id"].split("::", 1)[0]))
    if not excluded:
        raise CampaignError("no EXCLUDE annotation to replace")

    candidates = [Candidate.from_json(row) for row in read_jsonl(pool_path)]
    rebuilt = select_campaign_items(candidates, excluded_carriers=excluded)
    rebuilt_rows = list(randomized_review_order([item.review_json() for item in rebuilt]))
    retained = {
        item_id: label
        for item_id, label in labels.items()
        if label != "EXCLUDE" and item_id in {row["item_id"] for row in rebuilt_rows}
    }
    write_jsonl(queue_path, rebuilt_rows)
    write_jsonl(
        annotations_path,
        (
            {"item_id": row["item_id"], "label": retained[row["item_id"]]}
            for row in rebuilt_rows
            if row["item_id"] in retained
        ),
    )
    write_jsonl(
        exclusions_path,
        (
            {"source": source, "external_id": external_id}
            for source, external_id in sorted(excluded)
        ),
    )
    print(
        json.dumps(
            {
                "excluded_carriers": len(excluded),
                "retained_annotations": len(retained),
                "review_items": len(rebuilt_rows),
                "review_queue_sha256": sha256_file(queue_path),
            },
            sort_keys=True,
        )
    )


def _seal(corpus_dir: Path) -> None:
    manifest = seal_annotations(
        corpus_dir / "review_queue.jsonl",
        corpus_dir / "annotations.jsonl",
        corpus_dir,
    )
    print(json.dumps(manifest, sort_keys=True))


def _ollama_tags() -> dict[str, str]:
    request = Request(
        "http://127.0.0.1:11434/api/tags",
        headers={"Accept": "application/json"},
        method="GET",
    )
    with urlopen(request, timeout=10) as response:
        payload = json.loads(response.read(2_000_001).decode("utf-8", errors="strict"))
    return {
        model["name"]: model["digest"]
        for model in payload.get("models", [])
        if isinstance(model, dict)
        and isinstance(model.get("name"), str)
        and isinstance(model.get("digest"), str)
    }


def _verify_models() -> None:
    installed = _ollama_tags()
    mismatches = {
        model: {"expected": digest, "installed": installed.get(model)}
        for model, digest in MODEL_DIGESTS.items()
        if installed.get(model) != digest
    }
    if mismatches:
        raise CampaignError(f"frozen Ollama digest mismatch: {mismatches}")
    print(json.dumps({"verified": sorted(MODEL_DIGESTS)}, sort_keys=True))


def _verify_epp_checkout(epp_root: Path) -> None:
    epp_root = epp_root.resolve()
    frozen_commit = "3a274cd"
    commit_check = subprocess.run(
        ["git", "-C", str(epp_root), "cat-file", "-e", f"{frozen_commit}^{{commit}}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        check=False,
    )
    if commit_check.returncode != 0:
        raise CampaignError("frozen EPP commit is absent from checkout")
    diff_check = subprocess.run(
        [
            "git",
            "-C",
            str(epp_root),
            "diff",
            "--quiet",
            frozen_commit,
            "--",
            "epp_quarantine_sidecar.py",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        check=False,
    )
    if diff_check.returncode == 1:
        raise CampaignError("EPP sidecar differs from frozen commit 3a274cd")
    if diff_check.returncode != 0:
        raise CampaignError("unable to verify frozen EPP sidecar revision")


def _existing_predictions(path: Path) -> dict[tuple[str, str], Mapping[str, Any]]:
    if not path.exists():
        return {}
    result: dict[tuple[str, str], Mapping[str, Any]] = {}
    for row in read_jsonl(path):
        key = (row.get("panel"), row.get("item_id"))
        if not all(isinstance(value, str) for value in key) or key in result:
            raise CampaignError("prediction file contains an invalid or duplicate key")
        result[key] = row
    return result


def _append_jsonl(path: Path, row: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        handle.flush()


def _run(corpus_dir: Path, epp_root: Path, output: Path) -> None:
    items, manifest = validate_prediction_inputs(corpus_dir)
    _verify_models()
    epp_root = epp_root.resolve()
    _verify_epp_checkout(epp_root)
    sidecar = epp_root / "epp_quarantine_sidecar.py"
    if not sidecar.is_file():
        raise CampaignError(f"missing sidecar: {sidecar}")
    existing = _existing_predictions(output)
    total = len(PANELS) * len(items)
    completed = len(existing)

    for panel, models in PANELS.items():
        command = [
            str(Path(sys.executable).resolve()),
            str(sidecar),
            "--model",
            models[0],
            "--model",
            models[1],
            "--timeout-seconds",
            "90",
        ]
        bridge = EPPQuarantineBridge(
            command=command,
            cwd=epp_root,
            timeout_seconds=190,
            max_content_chars=100_000,
            max_output_bytes=1_000_000,
        )
        for raw in items:
            key = (panel, raw["item_id"])
            if key in existing:
                continue
            item = QuarantineItem(
                item_id=raw["item_id"],
                source=raw["source"],
                external_id=raw["external_id"],
                canonical_url=raw["canonical_url"],
                captured_at=raw["captured_at"],
                content=raw["content"],
            )
            started = time.perf_counter()
            verdict = bridge.assess(item)
            duration_ms = round((time.perf_counter() - started) * 1_000, 3)
            row = {
                "schema_version": "vigie.shadow.prediction.v1",
                "frozen_commit": manifest["frozen_commit"],
                "panel": panel,
                "models": list(models),
                "model_digests": {model: MODEL_DIGESTS[model] for model in models},
                "item_id": item.item_id,
                "content_sha256": item.content_sha256,
                "decision": verdict.decision.value,
                "action": "PASS" if verdict.decision is QuarantineDecision.PASS else "HOLD",
                "confidence": verdict.confidence,
                "degraded": verdict.degraded,
                "errors": list(verdict.errors),
                "votes": [
                    {
                        "model_id": vote.model_id,
                        "decision": vote.decision.value,
                        "confidence": vote.confidence,
                    }
                    for vote in verdict.model_votes
                ],
                "duration_ms": duration_ms,
                "measured_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            }
            _append_jsonl(output, row)
            completed += 1
            print(f"progress={completed}/{total} panel={panel} item_id={item.item_id}", flush=True)


def _score(corpus_dir: Path, predictions_path: Path, output_dir: Path) -> None:
    manifest = json.loads((corpus_dir / "manifest.json").read_text(encoding="utf-8"))
    items_path = corpus_dir / "items.jsonl"
    labels_path = corpus_dir / "labels.jsonl"
    if manifest.get("items_sha256") != sha256_file(items_path):
        raise CampaignError("items changed after sealing")
    if manifest.get("labels_sha256") != sha256_file(labels_path):
        raise CampaignError("labels changed after sealing")
    report = score_campaign(
        read_jsonl(items_path),
        read_jsonl(labels_path),
        read_jsonl(predictions_path),
    )
    report.update(
        {
            "frozen_commit": manifest["frozen_commit"],
            "items_sha256": manifest["items_sha256"],
            "labels_sha256": manifest["labels_sha256"],
            "predictions_sha256": sha256_file(predictions_path),
            "scored_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "score.json"
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_path = output_dir / "REPORT.md"
    markdown_path.write_text(_markdown_report(report), encoding="utf-8")
    print(json.dumps({"global_verdict": report["global_verdict"], "report": str(markdown_path)}, sort_keys=True))


def _markdown_report(report: Mapping[str, Any]) -> str:
    lines = [
        "# Vigie shadow V1 — résultat pré-enregistré",
        "",
        f"- Verdict global : **{report['global_verdict']}**",
        f"- Jurys confirmés : {report['confirmed_panels']}/{len(PANELS)}",
        f"- Commit de gel : `{report['frozen_commit']}`",
        "",
        "| Politique | UER | BRR | AER | Perte | Dégradé | Confirmé |",
        "|---|---:|---:|---:|---:|---:|:---:|",
    ]
    baseline = report["baseline"]
    lines.append(
        f"| baseline | {baseline['unsafe_escape_rate']:.3f} | "
        f"{baseline['benign_retention_rate']:.3f} | "
        f"{baseline['adaptive_escape_rate']:.3f} | "
        f"{baseline['weighted_loss']:.3f} | 0.000 | — |"
    )
    for panel, metrics in report["panels"].items():
        lines.append(
            f"| {panel} | {metrics['unsafe_escape_rate']:.3f} | "
            f"{metrics['benign_retention_rate']:.3f} | "
            f"{metrics['adaptive_escape_rate']:.3f} | "
            f"{metrics['weighted_loss']:.3f} | "
            f"{metrics['degraded_rate']:.3f} | "
            f"{'oui' if metrics['confirmed'] else 'non'} |"
        )
    lines.extend(["", "Les seuils et la logique de verdict proviennent de `PREREGISTRATION_v1.md`.", ""])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    corpus_dir = args.corpus_dir.resolve()
    try:
        if args.command == "acquire":
            _acquire(corpus_dir, args.polite_delay)
        elif args.command == "annotate":
            _annotate(corpus_dir)
        elif args.command == "rebuild-excluded":
            _rebuild_excluded(corpus_dir)
        elif args.command == "seal":
            _seal(corpus_dir)
        elif args.command == "verify-models":
            _verify_models()
        elif args.command == "run":
            _run(corpus_dir, args.epp_root, args.output.resolve())
        elif args.command == "score":
            _score(corpus_dir, args.predictions.resolve(), args.output_dir.resolve())
        else:
            raise CampaignError(f"unknown command: {args.command}")
    except (CampaignError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"campaign_error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
