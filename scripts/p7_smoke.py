#!/usr/bin/env python
"""Smoke-test live P7 sur une source synthétique, sans ouvrir le jeu tenu."""
from __future__ import annotations

import argparse
import hashlib
import json

from core.knobs import Knobs
from core.llm import OllamaClient
from eval.p7_smoke_fixture import MODEL_DIGESTS, SYNTHETIC_SOURCE
from eval.p7_trajectory import (
    ORDER_ABBA,
    ORDER_BAAB,
    EvaluationCase,
    PolicyTrace,
    run_policy_pair,
)


def _summary(trace: PolicyTrace) -> dict:
    return {
        "complete": trace.complete,
        "contract_error": trace.contract_error,
        "options": [turn.options for turn in trace.turns],
        "output_sha256": [
            hashlib.sha256(turn.output.encode("utf-8")).hexdigest()
            for turn in trace.turns
        ],
        "output_chars": [len(turn.output) for turn in trace.turns],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", choices=sorted(MODEL_DIGESTS), default="mistral:latest")
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--execution-order", choices=(ORDER_ABBA, ORDER_BAAB), default=ORDER_ABBA)
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be positive")

    case = EvaluationCase("synthetic:live:1", "synthetic", SYNTHETIC_SOURCE)
    pair = run_policy_pair(
        case,
        llm_factory=lambda: OllamaClient(model=args.model, timeout=args.timeout),
        model_digest=MODEL_DIGESTS[args.model],
        static_best=Knobs(),
        execution_order=args.execution_order,
    )
    a1 = pair.adaptive.turns[0]
    s1 = pair.static.turns[0]
    invariants = {
        "turn1_prompt_equal": a1.prompt == s1.prompt,
        "turn1_options_equal": a1.options == s1.options,
        "turn1_output_equal": a1.output == s1.output,
    }
    print(
        json.dumps(
            {
                "schema_version": "lyra.p7.smoke.v1",
                "model": args.model,
                "model_digest": MODEL_DIGESTS[args.model],
                "execution_order": pair.execution_order,
                "physical_calls": pair.physical_calls,
                "synthetic_source_sha256": hashlib.sha256(
                    SYNTHETIC_SOURCE.encode("utf-8")
                ).hexdigest(),
                "turn1_invariants": invariants,
                "adaptive": _summary(pair.adaptive),
                "static": _summary(pair.static),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    if not invariants["turn1_prompt_equal"] or not invariants["turn1_options_equal"]:
        return 3
    if not invariants["turn1_output_equal"]:
        return 4
    return 0 if pair.adaptive.complete and pair.static.complete else 2


if __name__ == "__main__":
    raise SystemExit(main())
