import pytest

from scripts.run_final_dataset_baselines import summarize_query_metrics, summarize_strategy_metrics


def test_unjudged_qrels_are_rejected_instead_of_scored_as_negative():
    with pytest.raises(ValueError, match="Unjudged"):
        summarize_query_metrics({("dense", "query"): ["case"]}, [{"query_id": "query", "perspective_id": "view", "case_id": "case", "relevance_0_4": ""}], [5])


def test_unanswerable_reference_is_reported_without_inventing_gold():
    labels = [{"query_id": "query", "perspective_id": "answerable", "case_id": "case", "relevance_0_4": "3"},
              {"query_id": "query", "perspective_id": "empty", "case_id": "case", "relevance_0_4": "1"}]
    row = summarize_query_metrics({("dense", "query"): ["case"]}, labels, [5])[0]
    assert row["recall"] == row["perspective_coverage_answerable"] == 1
    assert row["perspective_coverage_all_references"] == 0.5
    assert row["answerable_perspectives"] == 1 and row["reference_perspectives"] == 2


def test_no_positive_query_is_not_reported_as_zero_recall_accuracy():
    row = summarize_query_metrics({("dense", "query"): ["case"]}, [{"query_id": "query", "perspective_id": "view", "case_id": "case", "relevance_0_4": "0"}], [5])[0]
    assert row["recall"] == "" and row["perspective_coverage_answerable"] == ""


def test_strategy_abstention_is_explicit_and_never_imputed():
    qrels = [{"query_id": "query", "perspective_id": "view", "case_id": "known", "relevance_0_4": "3"},
             {"query_id": "query", "perspective_id": "view", "case_id": "unknown", "relevance_0_4": "3"}]
    labels = [{"case_id": "known", "strategy_labels": "S1", "decision": "LABEL"},
              {"case_id": "unknown", "strategy_labels": "", "decision": "ABSTAIN"}]
    row = summarize_strategy_metrics({("dense", "query"): ["unknown"]}, qrels, labels, [1])[0]
    assert row["strategy_coverage"] == 0
    assert row["reference_strategy_count"] == row["positive_case_strategy_abstentions"] == 1
