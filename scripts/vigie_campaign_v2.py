#!/usr/bin/env python
"""CLI reproductible pour la campagne shadow V2 de La Vigie."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import time
from typing import Any, Mapping, Sequence
from urllib.request import Request, urlopen

from agency.tools.vigie.campaign import MODEL_DIGESTS, PANELS, CampaignError, read_jsonl, sha256_file, write_jsonl
from agency.tools.vigie.campaign_v2 import (
    FROZEN_COMMIT_V2,
    prepare_v2_corpus,
    rebuild_after_audit,
    score_campaign_v2,
    seal_v2,
    validate_prediction_inputs_v2,
)
from agency.tools.vigie.quarantine import (
    EPPQuarantineBridge,
    QuarantineDecision,
    QuarantineItem,
)
ROOT = Path(__file__).resolve().parent.parent
DEFAULT_V1_DIR = ROOT / "corpora" / "vigie_shadow_v1"
DEFAULT_CORPUS_DIR = ROOT / "corpora" / "vigie_shadow_v2"
DEFAULT_RUN_DIR = ROOT / "data" / "runs" / "vigie_shadow_v2"


def _ollama_tags() -> dict[str, str]:
    request = Request(
        "http://127.0.0.1:11434/api/tags",
        headers={"Accept": "application/json"},
        method="GET",
    )
    with urlopen(request, timeout=10) as response:
        payload = json.loads(
            response.read(2_000_001).decode("utf-8", errors="strict")
        )
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


def _existing_predictions(
    path: Path,
) -> dict[tuple[str, str], Mapping[str, Any]]:
    if not path.exists():
        return {}
    result: dict[tuple[str, str], Mapping[str, Any]] = {}
    for row in read_jsonl(path):
        key = (row.get("panel"), row.get("item_id"))
        if not all(isinstance(value, str) for value in key) or key in result:
            raise CampaignError("prediction file contains an invalid or duplicate key")
        result[(str(key[0]), str(key[1]))] = row
    return result


def _append_jsonl(path: Path, row: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        handle.flush()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus-dir", type=Path, default=DEFAULT_CORPUS_DIR)
    parser.add_argument(
        "--source-pool",
        type=Path,
        default=DEFAULT_V1_DIR / "candidate_pool.jsonl",
    )
    parser.add_argument(
        "--v1-review",
        type=Path,
        default=DEFAULT_V1_DIR / "review_queue.jsonl",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser(
        "prepare", help="build V2 locally from the frozen V1 capture"
    )
    subparsers.add_parser(
        "annotate", help="resume the reduced stratified human audit"
    )
    subparsers.add_parser(
        "rebuild-audit",
        help="exclude disagreements, expand affected strata, and rebuild",
    )
    subparsers.add_parser(
        "seal", help="seal construction, silver, and human-audited labels"
    )
    subparsers.add_parser(
        "verify-models", help="verify frozen Ollama model digests"
    )

    run = subparsers.add_parser("run", help="run the three blind EPP panels")
    run.add_argument(
        "--epp-root",
        type=Path,
        default=ROOT.parent / "EPP_Verdict",
    )
    run.add_argument(
        "--output", type=Path, default=DEFAULT_RUN_DIR / "predictions.jsonl"
    )

    score = subparsers.add_parser(
        "score", help="score complete predictions after the blind run"
    )
    score.add_argument(
        "--predictions",
        type=Path,
        default=DEFAULT_RUN_DIR / "predictions.jsonl",
    )
    score.add_argument("--output-dir", type=Path, default=DEFAULT_RUN_DIR)
    return parser


def _prepare(
    corpus_dir: Path, source_pool_path: Path, v1_review_path: Path
) -> None:
    summary = prepare_v2_corpus(
        corpus_dir, source_pool_path, v1_review_path
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))


def _annotate(corpus_dir: Path) -> None:
    queue = read_jsonl(corpus_dir / "audit_queue.jsonl")
    annotations_path = corpus_dir / "audit_annotations.jsonl"
    existing_rows = read_jsonl(annotations_path) if annotations_path.exists() else []
    existing: dict[str, str] = {}
    for row in existing_rows:
        if set(row) != {"item_id", "label"}:
            raise CampaignError("audit annotation does not match the closed schema")
        if row["label"] not in {"BENIGN", "UNSAFE", "EXCLUDE"}:
            raise CampaignError("invalid audit annotation")
        existing[row["item_id"]] = row["label"]

    total = len(queue)
    for index, item in enumerate(queue, 1):
        item_id = item["item_id"]
        if item_id in existing:
            continue
        print("\n" + "=" * 79)
        print(
            f"[{index}/{total}] {item_id} | {item['audit_stratum']} | "
            f"{item['canonical_url']}"
        )
        print("-" * 79)
        print(item["content"])
        print("-" * 79)
        while True:
            answer = input(
                "Label [b]enign / [u]nsafe / e[x]clude / [q]uit: "
            ).strip().lower()
            if answer == "q":
                return
            label = {"b": "BENIGN", "u": "UNSAFE", "x": "EXCLUDE"}.get(answer)
            if label:
                break
        existing[item_id] = label
        write_jsonl(
            annotations_path,
            (
                {"item_id": row["item_id"], "label": existing[row["item_id"]]}
                for row in queue
                if row["item_id"] in existing
            ),
        )
        print(f"saved={len(existing)}/{total}")

    disagreements = sum(label != "BENIGN" for label in existing.values())
    if disagreements:
        print(
            f"audit_complete={total} disagreements={disagreements} "
            "next=rebuild-audit"
        )
    else:
        print(f"audit_complete={total} disagreements=0 next=seal")


def _rebuild(
    corpus_dir: Path, source_pool_path: Path, v1_review_path: Path
) -> None:
    summary = rebuild_after_audit(
        corpus_dir, source_pool_path, v1_review_path
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))


def _seal(
    corpus_dir: Path, source_pool_path: Path, v1_review_path: Path
) -> None:
    manifest = seal_v2(corpus_dir, source_pool_path, v1_review_path)
    print(json.dumps(manifest, ensure_ascii=False, sort_keys=True))


def _validate_existing_predictions(
    existing: Mapping[tuple[str, str], Mapping[str, Any]],
    items: Sequence[Mapping[str, Any]],
) -> None:
    item_by_id = {row["item_id"]: row for row in items}
    for (panel, item_id), row in existing.items():
        if panel not in PANELS or item_id not in item_by_id:
            raise CampaignError("existing V2 prediction has an unknown key")
        if row.get("schema_version") != "vigie.shadow.prediction.v2":
            raise CampaignError("existing V2 prediction schema mismatch")
        if row.get("frozen_commit") != FROZEN_COMMIT_V2:
            raise CampaignError("existing V2 prediction frozen commit mismatch")
        if row.get("models") != list(PANELS[panel]):
            raise CampaignError("existing V2 prediction panel mismatch")
        if row.get("model_digests") != {
            model: MODEL_DIGESTS[model] for model in PANELS[panel]
        }:
            raise CampaignError("existing V2 prediction digest mismatch")
        if row.get("content_sha256") != item_by_id[item_id]["content_sha256"]:
            raise CampaignError("existing V2 prediction content hash mismatch")
        decision = row.get("decision")
        if decision not in {"PASS", "QUARANTINE", "REJECT", "ESCALATE"}:
            raise CampaignError("existing V2 prediction decision is invalid")
        if row.get("action") != ("PASS" if decision == "PASS" else "HOLD"):
            raise CampaignError("existing V2 prediction action contradicts decision")
        if not isinstance(row.get("degraded"), bool):
            raise CampaignError("existing V2 prediction degraded flag is invalid")
        duration = row.get("duration_ms")
        if (
            isinstance(duration, bool)
            or not isinstance(duration, (int, float))
            or duration < 0
        ):
            raise CampaignError("existing V2 prediction duration is invalid")
        votes = row.get("votes")
        if not isinstance(votes, list) or len(votes) != 2:
            raise CampaignError("existing V2 prediction must contain two votes")
        vote_models = {
            vote.get("model_id")
            for vote in votes
            if isinstance(vote, dict)
            and vote.get("decision")
            in {"PASS", "QUARANTINE", "REJECT", "ESCALATE"}
        }
        if vote_models != set(PANELS[panel]):
            raise CampaignError("existing V2 prediction votes are invalid")


def _run(corpus_dir: Path, epp_root: Path, output: Path) -> None:
    items, manifest = validate_prediction_inputs_v2(corpus_dir)
    _verify_models()
    epp_root = epp_root.resolve()
    _verify_epp_checkout(epp_root)
    sidecar = epp_root / "epp_quarantine_sidecar.py"
    if not sidecar.is_file():
        raise CampaignError(f"missing sidecar: {sidecar}")

    existing = _existing_predictions(output)
    _validate_existing_predictions(existing, items)
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
                "schema_version": "vigie.shadow.prediction.v2",
                "frozen_commit": manifest["frozen_commit"],
                "panel": panel,
                "models": list(models),
                "model_digests": {
                    model: MODEL_DIGESTS[model] for model in models
                },
                "item_id": item.item_id,
                "content_sha256": item.content_sha256,
                "decision": verdict.decision.value,
                "action": (
                    "PASS"
                    if verdict.decision is QuarantineDecision.PASS
                    else "HOLD"
                ),
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
                "measured_at": datetime.now(timezone.utc)
                .isoformat()
                .replace("+00:00", "Z"),
            }
            _append_jsonl(output, row)
            completed += 1
            print(
                f"progress={completed}/{total} panel={panel} "
                f"item_id={item.item_id}",
                flush=True,
            )


def _score(
    corpus_dir: Path, predictions_path: Path, output_dir: Path
) -> None:
    _, manifest = validate_prediction_inputs_v2(corpus_dir)
    items_path = corpus_dir / "items.jsonl"
    labels_path = corpus_dir / "labels.jsonl"
    if manifest.get("items_sha256") != sha256_file(items_path):
        raise CampaignError("V2 items changed after sealing")
    if manifest.get("labels_sha256") != sha256_file(labels_path):
        raise CampaignError("V2 labels changed after sealing")
    report = score_campaign_v2(
        read_jsonl(items_path),
        read_jsonl(labels_path),
        read_jsonl(predictions_path),
        audit_gate_c7=manifest.get("audit_gate_c7") is True,
    )
    report.update(
        {
            "frozen_commit": manifest["frozen_commit"],
            "items_sha256": manifest["items_sha256"],
            "labels_sha256": manifest["labels_sha256"],
            "label_provenance_counts": manifest["label_provenance_counts"],
            "predictions_sha256": sha256_file(predictions_path),
            "scored_at": datetime.now(timezone.utc)
            .isoformat()
            .replace("+00:00", "Z"),
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
    print(
        json.dumps(
            {
                "global_verdict": report["global_verdict"],
                "report": str(markdown_path),
            },
            sort_keys=True,
        )
    )


def _display_rate(value: Any) -> str:
    return "n/a" if value is None else f"{float(value):.3f}"


def _markdown_report(report: Mapping[str, Any]) -> str:
    provenance = report["label_provenance_counts"]
    lines = [
        "# Vigie shadow V2 — résultat pré-enregistré",
        "",
        f"- Verdict global : **{report['global_verdict']}**",
        f"- Jurys soutenus : {report['supported_panels']}/{len(PANELS)}",
        f"- Commit de gel : {report['frozen_commit']}",
        "- Portée : qualification exploratoire sur provenance mixte ; "
        "**aucun déploiement autorisé**.",
        "- Labels : "
        f"{provenance['construction']} construction, "
        f"{provenance['human_audit']} audités humains, "
        f"{provenance['silver_source']} silver non audités.",
        "",
        "| Politique | UER construction | BRR total | BRR audité | "
        "BRR silver | AER | Perte | Dégradé | Soutenu |",
        "|---|---:|---:|---:|---:|---:|---:|---:|:---:|",
    ]
    baseline = report["baseline"]
    lines.append(
        f"| baseline | {baseline['unsafe_escape_rate']:.3f} | "
        f"{baseline['benign_retention_rate']:.3f} | "
        f"{baseline['benign_retention_audited']:.3f} | "
        f"{_display_rate(baseline['benign_retention_silver_only'])} | "
        f"{baseline['adaptive_escape_rate']:.3f} | "
        f"{baseline['weighted_loss']:.3f} | 0.000 | — |"
    )
    for panel, metrics in report["panels"].items():
        lines.append(
            f"| {panel} | {metrics['unsafe_escape_rate']:.3f} | "
            f"{metrics['benign_retention_rate']:.3f} | "
            f"{metrics['benign_retention_audited']:.3f} | "
            f"{_display_rate(metrics['benign_retention_silver_only'])} | "
            f"{metrics['adaptive_escape_rate']:.3f} | "
            f"{metrics['weighted_loss']:.3f} | "
            f"{metrics['degraded_rate']:.3f} | "
            f"{'oui' if metrics['supported_in_v2'] else 'non'} |"
        )
    lines.extend(
        [
            "",
            "Les seuils et la logique viennent de PREREGISTRATION_v2.md.",
            "Les labels silver interdisent d'interpréter ce rapport comme un "
            "benchmark gold, une preuve hors distribution ou une autorisation S1.",
            "",
        ]
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    corpus_dir = args.corpus_dir.resolve()
    source_pool_path = args.source_pool.resolve()
    v1_review_path = args.v1_review.resolve()
    try:
        if args.command == "prepare":
            _prepare(corpus_dir, source_pool_path, v1_review_path)
        elif args.command == "annotate":
            _annotate(corpus_dir)
        elif args.command == "rebuild-audit":
            _rebuild(corpus_dir, source_pool_path, v1_review_path)
        elif args.command == "seal":
            _seal(corpus_dir, source_pool_path, v1_review_path)
        elif args.command == "verify-models":
            _verify_models()
        elif args.command == "run":
            _run(corpus_dir, args.epp_root, args.output.resolve())
        elif args.command == "score":
            _score(
                corpus_dir,
                args.predictions.resolve(),
                args.output_dir.resolve(),
            )
        else:
            raise CampaignError(f"unknown command: {args.command}")
    except (CampaignError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"campaign_error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
