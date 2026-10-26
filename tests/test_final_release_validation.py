import pytest

from scripts.compare_final_labels import parse_labels
from scripts.validate_final_research_dataset import validate_matrix


def relevance_row(**changes):
    return {"query_id": "Q1", "perspective_id": "P1", "case_id": "C1", "relevance_0_4": "3",
            "evidence_reason": "Document fields must be extracted and validated.", "judgment_status": "AI_SILVER_ADJUDICATED", **changes}


def test_qrels_must_cover_the_actual_reference_by_case_matrix():
    queries = [{"query_id": "Q1", "reference_perspectives": [{"id": "P1"}]}]
    with pytest.raises(ValueError, match="incomplete"):
        validate_matrix([relevance_row()], queries, {"C1", "C2"})
    with pytest.raises(ValueError, match="duplicated"):
        validate_matrix([relevance_row(), relevance_row()], queries, {"C1"})
    validate_matrix([relevance_row()], queries, {"C1"})


def test_unresolved_or_blank_final_qrels_are_rejected():
    queries = [{"query_id": "Q1", "reference_perspectives": [{"id": "P1"}]}]
    with pytest.raises(ValueError, match="Unjudged"):
        validate_matrix([relevance_row(relevance_0_4="")], queries, {"C1"})
    with pytest.raises(ValueError, match="Unresolved"):
        validate_matrix([relevance_row(judgment_status="UNRESOLVED")], queries, {"C1"})


def test_abstention_cannot_be_disguised_as_an_observed_negative_or_label():
    allowed = {"F01_REPETITIVE_MANUAL_WORK"}
    assert parse_labels({"factor_labels": "", "decision": "ABSTAIN", "rationale": "Cause is not specified."}, "factor_labels", allowed) == set()
    with pytest.raises(ValueError, match="disagree"):
        parse_labels({"factor_labels": "", "decision": "LABEL", "rationale": "Insufficient evidence."}, "factor_labels", allowed)
    with pytest.raises(ValueError, match="Unknown"):
        parse_labels({"factor_labels": "F99_INVENTED", "decision": "LABEL", "rationale": "Invented."}, "factor_labels", allowed)
