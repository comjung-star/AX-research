import json
from pathlib import Path

import numpy as np
import pytest

from ax_research.semantic_mapping import aggregate, combined_score, compare_fields, field_profile, ranking_key

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "configs/semantic_mapping_20261028.json").read_text(encoding="utf-8"))
RULES = json.loads((ROOT / "configs/functional_mapping_20261028.json").read_text(encoding="utf-8-sig"))


def profile(text, **kwargs):
    return field_profile(text, CONFIG, RULES["negation_guard"], **kwargs)


def test_literal_spans_and_unknown_output():
    text = "Grant compliance and budget review; outputs a compliance report"
    result = profile(text, executed=True, context="Government staff")
    for field, evidence in result["spans"].items():
        source = "Government staff" if field == "context" else text
        for span in evidence:
            assert source[span["start"]:span["end"]] == span["quote"]
    assert result["fields"]["output"] == "a compliance report"
    assert profile("Answer employee policy questions", executed=True)["output_status"] == "UNKNOWN"


@pytest.mark.parametrize("task", ["Does not answer customer questions", "Plan to answer questions in future", "고객 응답 도입 예정"])
def test_unsupported_task_cannot_be_rescued_by_context(task):
    result = profile(task, executed=True, context="Answer customer questions")
    assert not any(result["fields"].values())
    assert compare_fields(profile("고객 질문 응답"), result, {}, CONFIG["weights"])["status"] == "UNKNOWN_TASK"


def test_no_function_grammar_required_for_task_semantics():
    result = profile("Unload cartons", executed=True)
    assert result["fields"]["task"] == "Unload cartons"
    assert "Unload" in result["fields"]["action"]
    assert "cartons" in result["fields"]["object"]


def test_missing_fields_are_excluded_and_cosine_is_not_probability():
    query = {"fields": {"task": "question", "action": "", "object": "", "output": "", "context": ""}}
    case = {"fields": {"task": "defects", "action": "", "object": "", "output": "", "context": ""}}
    vectors = {"question": np.array([1., 0.]), "defects": np.array([-1., 0.])}
    result = compare_fields(query, case, vectors, CONFIG["weights"])
    assert result["score"] == -1
    assert result["available_weight"] == .4
    assert set(result["components"]) == {"task"}


def test_max_branch_preserves_whole_and_has_no_duplicate_bonus():
    assert aggregate(.2, [.8]) == aggregate(.2, [.8] * 10) == .5
    assert aggregate(.2, []) == .2
    assert aggregate(.8, [.2]) == .5


def test_frozen_mixture_range_and_deterministic_ties():
    assert combined_score(0, -1) == 0
    assert combined_score(4, 1) == 1
    assert combined_score(4, -1) == combined_score(0, 1) == .5
    assert sorted(["b", "a"], key=lambda case_id: ranking_key(.5, .1, case_id)) == ["a", "b"]


def test_metadata_is_not_a_scoring_input():
    result = profile("Document retrieval", executed=True, context="Office staff")
    altered = profile("Document retrieval", executed=True, context="Office staff")
    altered["case_id"] = "any_id"
    altered["silver_score"] = 4
    vectors = {text: np.array([1., 0.]) for text in result["fields"].values() if text}
    assert compare_fields(result, result, vectors, CONFIG["weights"]) == compare_fields(result, altered, vectors, CONFIG["weights"])


def test_original_query_does_not_enter_branch_profile():
    assert profile("답변 품질 일관성")["source_text"] == "답변 품질 일관성"


def test_output_not_inferred_from_operation_name():
    assert profile("Generate report", executed=True)["fields"]["output"] == ""
