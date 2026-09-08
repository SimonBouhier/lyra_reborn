"""Fixtures de développement seulement : aucun service ni modèle n'est appelé."""
from collections import Counter
from itertools import product

import pytest

from app.context import SYSTEM, assemble_context
from experiments.p6_recall.corpus import (
    RESPONSE_INSTRUCTION,
    build_cases,
    conditions,
    control_conditions,
    render,
    render_control,
    score,
)


def test_corpus_is_deterministic_unique_and_balanced_with_six_template_groups():
    cases = build_cases()
    assert cases == build_cases()
    assert len(cases) == 24
    assert len({case["id"] for case in cases}) == 24
    assert len({case["request_id"] for case in cases}) == 24
    assert len({case["correction_id"] for case in cases}) == 24
    groups = {case["template_id"] for case in cases}
    assert len(groups) == 6
    for template_id in groups:
        group = [case for case in cases if case["template_id"] == template_id]
        assert len(group) == 4
        assert Counter(case["old_value"] for case in group) == Counter(
            case["current_value"] for case in group
        )
        assert Counter(case["source_role"] for case in group) == {"user": 2, "assistant": 2}
        for role in ("user", "assistant"):
            role_cases = [case for case in group if case["source_role"] == role]
            assert Counter(case["old_value"] for case in role_cases) == Counter(
                case["current_value"] for case in role_cases
            )
    for case in cases:
        assert case["scenario_id"] == case["id"]
        assert case["old_value"] != case["current_value"]
        assert case["old_value"] in case["original"]
        assert case["current_value"] in case["correction"]
        assert case["old_value"] not in case["question"]
        assert case["current_value"] not in case["question"]
    cases[0]["original"] = "mutated locally"
    assert build_cases()[0]["original"] != "mutated locally"


def test_all_sixteen_factor_combinations_are_unique():
    cells = conditions()
    assert len(cells) == len({cell["id"] for cell in cells}) == 16
    assert {tuple(cell[key] for key in "ABCD") for cell in cells} == set(product((False, True), repeat=4))
    assert all(type(cell[key]) is bool for cell in cells for key in "ABCD")


@pytest.mark.parametrize("case", build_cases(), ids=lambda case: case["id"])
def test_render_preserves_question_system_provenance_and_factor_placement(case):
    for cell in conditions():
        messages = render(case, cell)
        assert messages[0] == {"role": "system", "content": SYSTEM}
        assert messages[-1] == {"role": "user", "content": case["question"] + "\n" + RESPONSE_INSTRUCTION}
        assert case["session_id"] in messages[1]["content"]
        assert f"{case['request_id']} / {case['source_role']}" in messages[1]["content"]
        source_messages = messages[1:-(2 if cell["D"] else 1)]
        assert len(source_messages) == (2 if cell["C"] else 1)
        assert all(message["role"] == "user" for message in source_messages)
        flat = "".join(message["content"] for message in source_messages)
        assert flat.count("Réponds simplement : noté.") == int(cell["A"])
        assert ("[Version ancienne" in flat) is cell["B"]
        assert ("[Version actuelle" in flat) is cell["B"]
        if not cell["B"]:
            assert f"[Original historique ; correction déclarée {case['correction_id']}]" in flat
        assert sum(message["role"] == "assistant" for message in messages) == int(cell["D"])
        if cell["D"]:
            assert messages[-2] == {"role": "assistant", "content": "Noté."}
            assert case["current_value"] in messages[-3]["content"]


@pytest.mark.parametrize("case", build_cases(), ids=lambda case: case["id"])
def test_c_changes_only_message_boundaries(case):
    for a, b, d in product((False, True), repeat=3):
        shared = {"A": a, "B": b, "D": d}
        joined = render(case, {**shared, "C": False})
        split = render(case, {**shared, "C": True})
        assert "".join(message["content"] for message in joined) == "".join(
            message["content"] for message in split
        )
        assert joined[1]["content"] == split[1]["content"] + split[2]["content"]
        assert joined[2:] == split[3:]


@pytest.mark.parametrize("a", [False, True])
@pytest.mark.parametrize("case", build_cases(), ids=lambda case: case["id"])
def test_current_labeling_matches_the_production_recall_context(case, a):
    text = case["original"] + ("\nRéponds simplement : noté." if a else "")
    passage = {
        "session": case["session_id"], "request": case["request_id"],
        "role": case["source_role"], "text": text,
        "correction": {"id": case["correction_id"], "text": case["correction"]},
    }
    source = {
        "request": {"texte": case["question"] + "\n" + RESPONSE_INSTRUCTION},
        "recalls": [{"id": "synthetic-recall", "passage": passage}],
        "history": [], "omissions": [],
    }
    profile = {
        "id": "synthetic-only", "max_input_characters": 100_000,
        "recent_pairs": 4, "options": {"num_ctx": 4096, "num_predict": 32},
    }
    actual = render(case, {"A": a, "B": False, "C": False, "D": False})
    assert actual == assemble_context(source, profile)["messages"]


def test_witness_names_and_truth_are_explicit_for_every_case():
    controls = control_conditions()
    assert controls == [
        "current_only", "old_only", "unchanged", "unknown", "other_subject", "multiple_updates"
    ]
    for case in build_cases():
        for name in controls:
            messages, expected = render_control(case, name)
            assert messages[0] == {"role": "system", "content": SYSTEM}
            assert messages[-1]["content"] == case["question"] + "\n" + RESPONSE_INSTRUCTION
            sources = "\n".join(message["content"] for message in messages[1:-1])
            assert all(message["role"] == "user" for message in messages[1:])
            if name == "current_only":
                assert expected == case["current_value"]
                assert case["correction"] in sources and case["old_value"] not in sources
            elif name == "old_only":
                assert expected == case["old_value"]
                assert case["original"] in sources and case["current_value"] not in sources
            elif name == "unchanged":
                assert expected == case["old_value"]
                assert sources.count(case["original"]) == 2
                assert "confirme sans changement" in sources
                assert case["current_value"] not in sources
            elif name == "unknown":
                assert expected == "inconnu"
                assert "aucune valeur n'est renseignée" in sources
                assert case["old_value"] not in sources and case["current_value"] not in sources
            elif name == "other_subject":
                assert expected == case["old_value"]
                assert case["original"] in sources
                assert "concerne exclusivement le sujet AUTRE" in sources
                assert f"ne modifie pas {case['subject']}" in sources
                assert "Sa valeur est " + case["current_value"] in sources
            else:
                assert expected == case["current_value"]
                assert sources.index(case["old_value"]) < sources.index("transit") < sources.rindex(case["current_value"])
                assert "remplace toutes les versions précédentes" in sources
                assert messages[-2]["content"].endswith(case["correction"])
            assert score(expected, expected, case["old_value"])["success"]


@pytest.mark.parametrize(
    "text, expected, old, success, category",
    [
        ("  JADE. \n", "jade", "ambre", True, "current"),
        ("ｊａｄｅ！", "jade", "ambre", True, "current"),
        ("Cafe\u0301\u00a0clair...", "café clair", "ambre", True, "current"),
        ("ambre !", "jade", "ambre", False, "old"),
        ("Ce n'est pas ambre.", "jade", "ambre", False, "other_or_format"),
        ("Pas ambre, jade.", "jade", "ambre", False, "other_or_format"),
        ("jade, et non ambre", "jade", "ambre", False, "other_or_format"),
        ("ambre / jade", "jade", "ambre", False, "other_or_format"),
        ("jade\nambre", "jade", "ambre", False, "other_or_format"),
        ("La valeur est jade.", "jade", "ambre", False, "other_or_format"),
        ('"jade"', "jade", "ambre", False, "other_or_format"),
        ("**jade**", "jade", "ambre", False, "other_or_format"),
        ("`jade`", "jade", "ambre", False, "other_or_format"),
        ("- jade", "jade", "ambre", False, "other_or_format"),
        ("ja.de", "jade", "ambre", False, "other_or_format"),
        ("jadé", "jade", "ambre", False, "other_or_format"),
        ("", "jade", "ambre", False, "abstention"),
        ("Je ne sais pas.", "jade", "ambre", False, "abstention"),
        ("Inconnu.", "inconnu", "ambre", True, "abstention"),
        ("ambre", "ambre", "ambre", True, "old"),
    ],
)
def test_strict_score_adversarial_responses(text, expected, old, success, category):
    result = score(text, expected, old)
    assert result["success"] is success
    assert result["category"] == category


@pytest.mark.parametrize("text, marker", [("Noté.", True), ("pas noté", True), ("NOte\u0301", True), ("annoté", False), ("noter", False), ("note", False)])
def test_acknowledgment_is_only_a_lexical_secondary_marker(text, marker):
    result = score(text, "jade", "ambre")
    assert result["acknowledgment_marker"] is marker
    assert not result["success"]
    assert result["category"] == "other_or_format"


def test_inputs_are_validated_instead_of_silently_coerced():
    case = build_cases()[0]
    with pytest.raises(ValueError, match="control"):
        render_control(case, "unknown_control")
    with pytest.raises(ValueError, match="bool"):
        render(case, {"A": 1, "B": False, "C": False, "D": False})
    with pytest.raises(TypeError, match="strings"):
        score(None, "jade", "ambre")
