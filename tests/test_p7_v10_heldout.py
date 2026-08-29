"""Offline checks for the V10 held-out pure logic (counterbalancing, records)."""
from __future__ import annotations

from collections import Counter
import hashlib

import pytest

from core.knobs import Knobs, KnobMapping
from eval.p7_trajectory import (
    ARM_ADAPTIVE,
    ARM_STATIC,
    ORDER_ABBA,
    ORDER_BAAB,
    EvaluationCase,
    run_policy_pair,
)
from eval.p7_v10_heldout import (
    CALL_SLOTS,
    HELDOUT_CASES,
    PRODUCER_CALLS_PER_CASE,
    assign_execution_orders,
    attribute_pair_calls,
    first_arm,
    pair_record,
    producer_scoring_input,
)
from eval.p7_v10_producer import OllamaProducerClient, load_model
from eval.p7_v10_scoring import score_producer
from eval.p7_v7_q0 import GLOBAL_SEED
from tests.p7_v10_fakes import FakeOllama, install

BASE = "http://127.0.0.1:11434"
DIGEST = "6577803aa9a036369e481d648a2baebb381ebc6e897f2bb9a766a2aa7bfbc1cf"
SOURCE = (
    "A registry received 12 submissions. Ten passed the required schema and two "
    "were rejected because a mandatory field was missing. The registry did not "
    "score or rank the accepted submissions, and no quality measure was defined."
)
CASE_IDS = [f"github:{index:03d}" for index in range(HELDOUT_CASES)]


def _case(case_id: str = "github:001") -> EvaluationCase:
    return EvaluationCase(case_id, "github", SOURCE)


def _pair(monkeypatch, order: str = ORDER_ABBA, *, failures: tuple[str, ...] = ()):
    install(monkeypatch, FakeOllama(producer_failures=failures))
    load_model(BASE, "mistral:latest", 5)
    client = OllamaProducerClient(BASE, "mistral:latest", 5)
    pair = run_policy_pair(
        _case(),
        llm_factory=lambda: client,
        model_digest=DIGEST,
        static_best=Knobs(),
        global_seed=GLOBAL_SEED,
        mapping=KnobMapping(num_predict_min=128, num_predict_max=768),
        execution_order=order,
    )
    return pair, client


def test_counterbalancing_is_exactly_half_and_frozen_to_the_v8_formula():
    orders = assign_execution_orders(CASE_IDS, DIGEST)
    assert Counter(orders.values()) == {ORDER_ABBA: 30, ORDER_BAAB: 30}
    assert orders == assign_execution_orders(reversed(CASE_IDS), DIGEST)

    ranked = sorted(
        CASE_IDS,
        key=lambda case_id: hashlib.sha256(
            f"{GLOBAL_SEED}\0execution_order\0{DIGEST}\0{case_id}".encode("utf-8")
        ).hexdigest(),
    )
    assert [orders[case_id] for case_id in ranked[:30]] == [ORDER_ABBA] * 30
    assert [orders[case_id] for case_id in ranked[30:]] == [ORDER_BAAB] * 30

    # Salée par producteur : un autre digest donne une autre affectation.
    assert assign_execution_orders(CASE_IDS, "0" * 64) != orders

    with pytest.raises(ValueError, match="unique"):
        assign_execution_orders(["a", "a"], DIGEST)
    with pytest.raises(ValueError, match="even"):
        assign_execution_orders(["a", "b", "c"], DIGEST)


def test_position_bit_is_deterministic_and_salted_by_producer():
    assert first_arm("github:001", DIGEST) == first_arm("github:001", DIGEST)
    assert {first_arm(case_id, DIGEST) for case_id in CASE_IDS} == {
        ARM_ADAPTIVE,
        ARM_STATIC,
    }
    differing = sum(
        first_arm(case_id, DIGEST) != first_arm(case_id, "0" * 64)
        for case_id in CASE_IDS
    )
    assert 0 < differing < HELDOUT_CASES


def test_call_slots_match_the_frozen_trajectory_order(monkeypatch):
    for order in (ORDER_ABBA, ORDER_BAAB):
        pair, client = _pair(monkeypatch, order)
        assert len(client.calls) == PRODUCER_CALLS_PER_CASE
        attributed = attribute_pair_calls(client.calls, pair)
        assert set(attributed) == set(CALL_SLOTS[order])
        for arm, trace in ((ARM_ADAPTIVE, pair.adaptive), (ARM_STATIC, pair.static)):
            for turn in (2, 3):
                assert attributed[(arm, turn)].options == trace.turns[turn - 1].options
        assert attributed[("COMMON", 1)].options == pair.adaptive.turns[0].options


def test_attribution_refuses_a_pair_that_did_not_emit_five_calls(monkeypatch):
    pair, client = _pair(monkeypatch)
    with pytest.raises(ValueError, match="five|5"):
        attribute_pair_calls(client.calls[:4], pair)


def test_pair_record_matches_the_scorer_schema(monkeypatch):
    pair, client = _pair(monkeypatch)
    attributed = attribute_pair_calls(client.calls, pair)
    record = pair_record(
        case=_case(),
        pair=pair,
        attributed=attributed,
        judged=True,
        judge={
            "forward": {"valid": True, "arm": ARM_ADAPTIVE},
            "reverse": {"valid": True, "arm": ARM_ADAPTIVE},
        },
        pack_blind_ok=True,
        pack_integrity_ok=True,
    )

    assert record["order"] == ORDER_ABBA
    assert record["producer_calls"] == 5
    assert record["complete"] is True
    assert record["common_t1_identical"] is True
    assert record["option_changed_t2_or_t3"] is True  # la politique adapte
    assert record["adaptive_objective_failure"] is False
    assert record["static_objective_failure"] is False
    assert record["adaptive_timeout_or_error"] is False
    assert record["adaptive_tokens_t23"] > 0 and record["static_tokens_t23"] > 0
    assert len(record["adaptive_latencies_t23"]) == 2
    assert record["judge"]["forward"]["arm"] == ARM_ADAPTIVE

    # Le scoreur gelé doit accepter ce record tel quel, sans adaptation.
    data = producer_scoring_input(
        producer="mistral:latest",
        seal={"count": 60, "cases": [{"content_sha256": "f" * 64}] * 60},
        sealed_before_common_t1=True,
        pairs=[
            {**record, "case_id": f"github:{index:03d}", "order": ORDER_ABBA if index < 30 else ORDER_BAAB}
            for index in range(60)
        ],
    )
    result = score_producer(data)
    assert result["W"] == 60 and result["L"] == 0 and result["U"] == 0
    assert result["gates"]["C0"] is True and result["gates"]["C10"] is True
    assert result["verdict"] == "H10_SUPPORTED_FOR_MODEL"


def test_a_failed_producer_marks_both_arms_and_never_widens_the_c8_gap(monkeypatch):
    pair, client = _pair(monkeypatch, failures=("mistral:latest",))
    record = pair_record(
        case=_case(),
        pair=pair,
        attributed=attribute_pair_calls(client.calls, pair),
        judged=False,
    )
    assert record["complete"] is False
    assert record["judged"] is False
    assert "judge" not in record
    assert record["adaptive_objective_failure"] is True
    assert record["static_objective_failure"] is True
    # L'échec du tour commun casse les deux bras symétriquement.
    assert record["adaptive_timeout_or_error"] is True
    assert record["static_timeout_or_error"] is True
    assert record["adaptive_tokens_t23"] == record["static_tokens_t23"] == 0


def test_seal_flags_require_sixty_hashes_and_a_seal_before_common_t1():
    seal = {"count": 60, "cases": [{"content_sha256": "a" * 64} for _ in range(60)]}
    data = producer_scoring_input(
        producer="m", seal=seal, sealed_before_common_t1=True, pairs=[]
    )
    assert data["seal"] == {
        "count": 60,
        "sealed_before_common_t1": True,
        "all_hashes_present": True,
    }

    truncated = {"count": 60, "cases": [{"content_sha256": "short"}]}
    assert (
        producer_scoring_input(
            producer="m", seal=truncated, sealed_before_common_t1=True, pairs=[]
        )["seal"]["all_hashes_present"]
        is False
    )
    assert (
        producer_scoring_input(
            producer="m", seal=seal, sealed_before_common_t1=False, pairs=[]
        )["seal"]["sealed_before_common_t1"]
        is False
    )
