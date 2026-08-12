"""P7 V3 — preuve synthétique de la tranche verticale, sans cas tenu."""
from __future__ import annotations

import json

import pytest

from core.knobs import Knobs
from core.llm import EchoClient
from core.loop import LyraLoop
from eval.p7_contracts import DecisionContractError, validate_editorial_decision
from eval.p7_judge import (
    JudgeProtocolError,
    PairwiseJudgeAgent,
    judge_in_both_orders,
    judge_system_prompt,
    resolve_panel,
)
from eval.p7_trajectory import (
    ORDER_ABBA,
    ORDER_BAAB,
    EvaluationCase,
    run_policy_pair,
)


SOURCE = (
    "Adaptive policies can change decoding parameters after observing a first "
    "draft, but the resulting decision still requires independent evidence."
)


def _final_json(option_marker: str) -> str:
    return json.dumps(
        {
            "decision": "AUDIT",
            "rationale": (
                "The source states a conditional engineering claim rather than "
                "a demonstrated quality gain; independent comparison remains "
                f"necessary before promotion. Effective marker: {option_marker}."
            ),
            "evidence": [
                {
                    "quote": "the resulting decision still requires independent evidence",
                    "why": "This directly limits what can be concluded from adaptive control alone.",
                }
            ],
            "uncertainty": "The source supplies no measured effect size or held-out comparison.",
            "next_step": "Run the frozen pairwise comparison before accepting the policy.",
        }
    )


class SyntheticProducer:
    """Sortie dépendante des options ; le tour final respecte le contrat."""

    def __init__(self):
        self.calls = []

    def generate(self, prompt, options, response_format=None):
        self.calls.append({"prompt": prompt, "options": dict(options)})
        marker = f"t={options['temperature']};p={options['top_p']};n={options['num_predict']}"
        if "Rends la décision éditoriale finale" in prompt:
            return _final_json(marker)
        return (
            "Analysis grounded in the supplied source. The claim needs an "
            "independent comparison and explicit uncertainty. " + marker
        )


def _case() -> EvaluationCase:
    return EvaluationCase("synthetic:1", "synthetic", SOURCE)


def test_contract_rejects_empty_trivial_and_non_source_evidence():
    with pytest.raises(DecisionContractError, match="empty"):
        validate_editorial_decision("", SOURCE)
    with pytest.raises(DecisionContractError, match="closed schema"):
        validate_editorial_decision(json.dumps({"decision": "AUDIT"}), SOURCE)

    payload = json.loads(_final_json("x"))
    payload["evidence"][0]["quote"] = "This fabricated quotation is definitely absent from the source."
    with pytest.raises(DecisionContractError, match="absent"):
        validate_editorial_decision(json.dumps(payload), SOURCE)


def test_generation_options_cannot_override_knob_controlled_keys():
    loop = LyraLoop(EchoClient())
    with pytest.raises(ValueError, match="controlled keys"):
        loop.generate("test", generation_options={"temperature": 0.0})


def test_pair_is_identical_at_turn_one_then_modulates_options_and_outputs():
    producer = SyntheticProducer()
    pair = run_policy_pair(
        _case(),
        llm_factory=lambda: producer,
        model_digest="synthetic-digest",
        static_best=Knobs(),
        execution_order=ORDER_ABBA,
    )

    a1, s1 = pair.adaptive.turns[0], pair.static.turns[0]
    assert a1.prompt == s1.prompt
    assert a1.options == s1.options
    assert a1.output == s1.output
    assert pair.adaptive.turns[1].prompt == pair.static.turns[1].prompt
    assert all(
        a.options["seed"] == s.options["seed"]
        for a, s in zip(pair.adaptive.turns, pair.static.turns)
    )

    assert any(
        a.options != s.options
        for a, s in zip(pair.adaptive.turns[1:], pair.static.turns[1:])
    ), "la politique prétend s'adapter mais les options effectives restent identiques"
    assert any(
        a.output != s.output
        for a, s in zip(pair.adaptive.turns[1:], pair.static.turns[1:])
    ), "des options différentes doivent produire des sorties différentes dans ce client contrôlé"
    assert pair.adaptive.complete
    assert pair.static.complete
    assert pair.physical_calls == len(producer.calls) == 5
    assert pair.execution_order == ORDER_ABBA
    assert producer.calls[1]["options"] == pair.adaptive.turns[1].options
    assert producer.calls[2]["options"] == pair.static.turns[1].options
    assert producer.calls[3]["options"] == pair.static.turns[2].options
    assert producer.calls[4]["options"] == pair.adaptive.turns[2].options


def test_baab_reverses_branch_execution_without_changing_common_prefix():
    producer = SyntheticProducer()
    pair = run_policy_pair(
        _case(),
        llm_factory=lambda: producer,
        model_digest="synthetic-digest",
        static_best=Knobs(),
        execution_order=ORDER_BAAB,
    )
    assert pair.execution_order == ORDER_BAAB
    assert pair.adaptive.turns[0].output == pair.static.turns[0].output
    assert producer.calls[1]["options"] == pair.static.turns[1].options
    assert producer.calls[2]["options"] == pair.adaptive.turns[1].options
    assert producer.calls[3]["options"] == pair.adaptive.turns[2].options
    assert producer.calls[4]["options"] == pair.static.turns[2].options

    with pytest.raises(ValueError, match="ABBA or BAAB"):
        run_policy_pair(
            _case(),
            llm_factory=SyntheticProducer,
            model_digest="synthetic-digest",
            static_best=Knobs(),
            execution_order="AABB",
        )


class ScriptedJudge:
    def __init__(self, final_preference: str):
        self.final_preference = final_preference
        self.calls = 0

    def generate(self, prompt, options, response_format=None):
        script = [
            {"action": "READ_SOURCE", "start": 0, "end": 4000},
            {"action": "READ_TRACE", "candidate": "A"},
            {"action": "READ_TRACE", "candidate": "B"},
            {
                "action": "VERDICT",
                "preference": self.final_preference,
                "rationale": (
                    "Candidate preference follows the supplied evidence, explicit uncertainty, "
                    "and the actionable next step visible in the inspected final trajectories."
                ),
                "evidence": ["SOURCE passage inspected", "Both final turns inspected"],
            },
        ]
        response = script[self.calls]
        self.calls += 1
        return json.dumps(response)


def _complete_pair():
    return run_policy_pair(
        _case(),
        llm_factory=SyntheticProducer,
        model_digest="synthetic-digest",
        static_best=Knobs(),
    )


def test_judge_is_blind_and_must_gather_evidence_before_verdict():
    prompt = judge_system_prompt()
    for forbidden in ("ADAPTIVE", "STATIC_BEST", "kw_overlap", "knobs_used", "temperature="):
        assert forbidden not in prompt

    pair = _complete_pair()
    premature = ScriptedJudge("A")
    premature.calls = 3
    with pytest.raises(JudgeProtocolError, match="mandatory"):
        PairwiseJudgeAgent(premature).judge(
            SOURCE, {"A": pair.adaptive, "B": pair.static}
        )


def test_order_reversal_and_panel_refuse_to_force_uncertain_result():
    pair = _complete_pair()

    stable_adaptive = judge_in_both_orders(
        source=SOURCE,
        first=pair.adaptive,
        second=pair.static,
        forward_agent=PairwiseJudgeAgent(ScriptedJudge("A")),
        reverse_agent=PairwiseJudgeAgent(ScriptedJudge("B")),
    )
    assert stable_adaptive.stable
    assert stable_adaptive.forward_candidate == "candidate_1"

    unstable = judge_in_both_orders(
        source=SOURCE,
        first=pair.adaptive,
        second=pair.static,
        forward_agent=PairwiseJudgeAgent(ScriptedJudge("A")),
        reverse_agent=PairwiseJudgeAgent(ScriptedJudge("A")),
    )
    assert not unstable.stable

    unresolved = resolve_panel((stable_adaptive, unstable))
    assert not unresolved.resolved
    assert unresolved.winner_candidate is None

    resolved = resolve_panel((stable_adaptive, stable_adaptive))
    assert resolved.resolved
    assert resolved.winner_candidate == "candidate_1"
