#!/usr/bin/env python
"""Smoke live du panel P7 sur une paire synthétique, sans corpus tenu."""
from __future__ import annotations

import argparse
import json

from core.knobs import Knobs
from core.llm import OllamaClient
from eval.p7_judge import PairwiseJudgeAgent, judge_in_both_orders, resolve_panel
from eval.p7_smoke_fixture import MODEL_DIGESTS, SYNTHETIC_SOURCE
from eval.p7_trajectory import ORDER_ABBA, ORDER_BAAB, EvaluationCase, run_policy_pair


def _judgment_summary(judgment) -> dict:
    return {
        "forward_preference": judgment.forward.preference.value,
        "reverse_preference": judgment.reverse.preference.value,
        "forward_candidate": judgment.forward_candidate,
        "reverse_candidate": judgment.reverse_candidate,
        "stable": judgment.stable,
        "forward_steps": judgment.forward.steps,
        "reverse_steps": judgment.reverse.steps,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--producer", choices=sorted(MODEL_DIGESTS), default="mistral:latest")
    parser.add_argument("--execution-order", choices=(ORDER_ABBA, ORDER_BAAB), default=ORDER_ABBA)
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be positive")

    judges = [name for name in MODEL_DIGESTS if name != args.producer]
    if len(judges) != 2:
        raise RuntimeError("the frozen panel requires exactly two other models")

    case = EvaluationCase("synthetic:judge:1", "synthetic", SYNTHETIC_SOURCE)
    pair = run_policy_pair(
        case,
        llm_factory=lambda: OllamaClient(model=args.producer, timeout=args.timeout),
        model_digest=MODEL_DIGESTS[args.producer],
        static_best=Knobs(),
        execution_order=args.execution_order,
    )
    if not pair.adaptive.complete or not pair.static.complete:
        print(json.dumps({"producer_complete": False}, indent=2))
        return 2

    judgments = []
    summaries = {}
    for judge_name in judges:
        judgment = judge_in_both_orders(
            source=SYNTHETIC_SOURCE,
            first=pair.adaptive,
            second=pair.static,
            forward_agent=PairwiseJudgeAgent(
                OllamaClient(model=judge_name, timeout=args.timeout)
            ),
            reverse_agent=PairwiseJudgeAgent(
                OllamaClient(model=judge_name, timeout=args.timeout)
            ),
        )
        judgments.append(judgment)
        summaries[judge_name] = _judgment_summary(judgment)

    panel = resolve_panel(tuple(judgments))
    print(
        json.dumps(
            {
                "schema_version": "lyra.p7.judge-smoke.v1",
                "synthetic_only": True,
                "producer": args.producer,
                "producer_digest": MODEL_DIGESTS[args.producer],
                "execution_order": pair.execution_order,
                "physical_producer_calls": pair.physical_calls,
                "judges": summaries,
                "panel": {
                    "resolved": panel.resolved,
                    "winner_candidate": panel.winner_candidate,
                    "reason": panel.reason,
                },
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    # Un panel non résolu est un résultat valide du protocole, pas une panne.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
