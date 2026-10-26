import csv
import json

import pytest

from scripts.audit_final_dataset import OUTPUT, audit_judgment_pass, final_eligible_count


def judgment(**changes):
    return {"query_id": "DEV01", "perspective_id": "P1", "case_id": "CASE01", "relevance_0_4": "3",
            "reviewer_id": "independent-review-context-a", "rationale": "The stated document review task directly addresses manual form processing.", **changes}


def test_placeholder_relevance_rows_cannot_count_as_a_completed_pass():
    with pytest.raises(ValueError, match="actual grade"):
        audit_judgment_pass([judgment(relevance_0_4="")], {("DEV01", "P1", "CASE01")})


def test_unjudged_is_not_silently_converted_to_irrelevant_zero():
    with pytest.raises(ValueError, match="actual grade"):
        audit_judgment_pass([judgment(relevance_0_4="UNJUDGED")], {("DEV01", "P1", "CASE01")})


def test_missing_or_duplicate_judgments_fail_coverage_checks():
    expected = {("DEV01", "P1", "CASE01"), ("DEV01", "P1", "CASE02")}
    with pytest.raises(ValueError, match="missing, duplicate"):
        audit_judgment_pass([judgment(), judgment()], expected)


def test_scores_without_reviewer_or_evidence_are_not_validated_labels():
    expected = {("DEV01", "P1", "CASE01")}
    with pytest.raises(ValueError, match="identified reviewer"):
        audit_judgment_pass([judgment(reviewer_id="")], expected)
    with pytest.raises(ValueError, match="evidence rationale"):
        audit_judgment_pass([judgment(rationale="")], expected)


def test_one_missing_final_gate_prevents_a_positive_final_case_count():
    assert final_eligible_count(117, {"source": {"passed": True}, "heldout": {"passed": False}}) == 0
    assert final_eligible_count(117, {}) == 0
    assert final_eligible_count(117, {"source": {"passed": True}, "heldout": {"passed": True}}) == 117


def test_source_candidates_are_not_labeled_as_final_or_human_gold():
    document = json.loads((OUTPUT / "source_supported_candidates.json").read_text(encoding="utf-8"))
    assert len(document["cases"]) == len({case["case_id"] for case in document["cases"]}) == 117
    assert all(case["final_experiment_approved"] is False and case["human_gold"] is False for case in document["cases"])
    assert {case["case_id"] for case in document["cases"]} >= {"AXV2N_0112", "AXV2N_0113", "AXV2N_0131"}


def test_blinded_inputs_hide_implementations_outcomes_labels_and_rankings():
    document = json.loads((OUTPUT / "blind_relevance_input.json").read_text(encoding="utf-8"))
    assert all(set(case) == {"case_id", "problem", "task", "context"} for case in document["cases"])
    with (OUTPUT / "factor_blind_input.csv").open(encoding="utf-8-sig", newline="") as handle:
        assert next(csv.reader(handle)) == ["case_id", "problem"]
    with (OUTPUT / "strategy_blind_input.csv").open(encoding="utf-8-sig", newline="") as handle:
        assert next(csv.reader(handle)) == ["case_id", "implementation", "outcome"]


def test_final_audit_retains_complete_original_registry_membership():
    with (OUTPUT / "registry_review_status.csv").open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == len({row["case_id"] for row in rows}) == 11766
    assert sum(row["individual_fact_review_completed_this_run"] == "True" for row in rows) == 2


def test_current_final_experiment_gate_is_closed():
    report = json.loads((OUTPUT / "readiness.json").read_text(encoding="utf-8"))
    assert report["source_document_candidates_after_followup"] == 117
    assert report["required_dev_relevance_pairs"] == 3510
    assert report["actual_heldout_test_questions"] == 0
    assert report["final_experiment_eligible_cases"] == 0
