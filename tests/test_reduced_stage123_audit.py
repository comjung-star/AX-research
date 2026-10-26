import json

import pytest

from scripts.audit_reduced_stage123 import gate_blockers, measure_ranking, probe_credentials


def test_historical_metrics_preserve_denominators_and_empty_references():
    result = measure_ranking(["case_a", "case_b", "case_c"],
                             {"aspect_1": {"case_a", "case_d"}, "aspect_2": set()},
                             {"case_a": ["S1"], "case_b": ["S2"], "case_c": [], "case_d": ["S3"]}, 2)
    assert result["precision"] == 0.5
    assert result["recall"] == 0.5
    assert result["f1"] == 0.5
    assert result["perspective_coverage"] == 1.0
    assert result["answerable_reference_count"] == 1
    assert result["all_reference_count"] == 2
    assert result["strategy_coverage"] == 0.5


def test_zero_relevant_labels_are_not_recall_zero():
    result = measure_ranking(["case_a"], {"aspect_1": set()}, {"case_a": []}, 1)
    assert result["precision"] == 0
    assert result["recall"] is None
    assert result["f1"] is None
    assert result["perspective_coverage"] is None


def test_no_hit_has_f1_zero_when_truth_is_nonempty():
    result = measure_ranking(["case_a"], {"aspect_1": {"case_b"}}, {"case_a": [], "case_b": []}, 1)
    assert result["recall"] == 0
    assert result["f1"] == 0


@pytest.mark.parametrize("ranking,top_k", [(["case_a", "case_a"], 1), (["case_a"], 2), (["case_a"], 0)])
def test_invalid_rankings_fail_instead_of_changing_denominator(ranking, top_k):
    with pytest.raises(ValueError):
        measure_ranking(ranking, {"aspect_1": set()}, {"case_a": []}, top_k)


def test_repeats_of_one_model_do_not_satisfy_three_model_gate():
    dev = {"judged_pairs": 3360, "annotation_pairs": 3360, "approved_reference_perspectives": 30,
           "reference_perspectives": 30, "semantic_near_duplicate_review": "COMPLETE"}
    reasons = gate_blockers({"minimum_distinct_llms": 3}, dev,
                            {"verified_distinct_judgment_models": ["model_a", "model_a", "model_a"]})
    assert reasons == ["THREE_DISTINCT_LLMS_NOT_CONFIGURED_OR_VERIFIED"]


def test_labels_and_draft_references_remain_blockers_even_with_three_models():
    dev = {"judged_pairs": 0, "annotation_pairs": 3360, "approved_reference_perspectives": 0,
           "reference_perspectives": 30, "semantic_near_duplicate_review": "PENDING"}
    reasons = gate_blockers({"minimum_distinct_llms": 3}, dev,
                            {"verified_distinct_judgment_models": ["model_a", "model_b", "model_c"]})
    assert "NEW_RELEVANCE_LABELS_UNJUDGED_NO_APPROVED_QRELS" in reasons
    assert "REFERENCE_PERSPECTIVES_ARE_UNVALIDATED_DRAFTS" in reasons
    assert "SEMANTIC_DUPLICATE_AND_SOURCE_SCOPE_REVIEW_PENDING" in reasons


def test_credential_report_contains_presence_only(tmp_path, monkeypatch):
    from prototype.credentials import WindowsCredentialStore

    monkeypatch.setattr(WindowsCredentialStore, "read", lambda self: None)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "example-test-value-that-must-not-be-saved")
    (tmp_path / ".env").write_text("OPENAI_API_KEY=another-example-test-value\n", encoding="utf-8")
    report = probe_credentials(tmp_path)
    assert report["dotenv_key_presence"] == {"OPENAI_API_KEY": True}
    assert report["process_key_presence"]["ANTHROPIC_API_KEY"] is True
    assert "example-test-value" not in json.dumps(report)
    assert report["verified_distinct_judgment_models"] == []
