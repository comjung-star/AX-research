from scripts.prepare_v25_research import decide, leakage_groups


def record(identifier, **changes):
    return {"case_id": identifier, "record_kind": "SOURCE_REPORTED_USE_CASE", "organization": "UNKNOWN",
            "source_url": "https://inventory.test/list.csv", "source_dataset_id": "SOURCE", "source_record_id": identifier,
            "problem": "Manual entry causes delays", "task": "Record entry", "context": "Office records",
            "implementation": "Model extracts fields", "outcome": "UNKNOWN", "deployment_stage": "DEPLOYED",
            "ai_status": "SOURCE_CLASSIFIED_AI", **changes}


def test_shared_inventory_download_is_not_one_duplicate_case_group():
    groups, _ = leakage_groups([record("first"), record("second")], {})
    assert groups["first"] != groups["second"]


def test_organization_duplicate_and_parent_links_are_transitive():
    cases = [record("first", organization="Example Agency"), record("second", organization="Example Agency"),
             record("third", exact_duplicate_of="second"), record("parent", covered_by_reviewed_workflows=["third"])]
    groups, links = leakage_groups(cases, {})
    assert len(set(groups.values())) == 1
    assert {row["basis"] for row in links} == {"organization", "explicit_representative"}


def test_redirected_pages_and_same_text_are_kept_together():
    cases = [record("first", record_kind="SOURCE_REFERENCE", candidate_id="one", source_url="https://page.test/old"),
             record("second", record_kind="SOURCE_REFERENCE", candidate_id="two", source_url="https://page.test/new")]
    audits = {"one": {"access": {"final_url": "https://page.test/new"}}}
    groups, _ = leakage_groups(cases, audits)
    assert groups["first"] == groups["second"]


def test_unknown_organization_and_source_id_do_not_merge_unrelated_rows():
    cases = [record("first", source_record_id="UNKNOWN"), record("second", source_record_id="UNKNOWN")]
    groups, _ = leakage_groups(cases, {})
    assert len(set(groups.values())) == 2


def test_rule_and_source_ai_deployment_signals_do_not_pass_individual_review():
    decision, reasons = decide(record("first", problem="AI automates manual forms"))
    assert decision == "HOLD"
    assert "PROBLEM_SOLUTION_MIX_RISK_REQUIRES_PASSAGE_REVIEW" in reasons
    assert "INDIVIDUAL_PASSAGE_REVIEW_PENDING" in reasons


def test_scope_and_non_ai_uncertainty_never_delete_records():
    for scope in ["public_work", "enterprise_work", "consumer_personal", "education_research", "social_nonprofit"]:
        decision, reasons = decide(record(scope, business_scope=scope, ai_status="NON_AI_OR_UNCONFIRMED_TECHNOLOGY"))
        assert decision == "HOLD"
        assert "AI_STATUS_UNCONFIRMED_NOT_PROVEN_NON_AI" in reasons


def test_missing_outcome_does_not_prevent_descriptive_source_review_but_is_flagged():
    decision, reasons = decide(record("first"), {"outcome_status": "EXPECTED_ONLY"})
    assert decision == "EXPERIMENT_SUITABLE"
    assert "OUTCOME_NOT_INDEPENDENTLY_VALIDATED" in reasons


def test_parser_and_duplicate_exclusion_are_analytic_only_with_reasons():
    assert decide(record("artifact", record_kind="PRIOR_PARSER_ARTIFACT"))[0] == "EXCLUDE"
    decision, reasons = decide(record("copy", exact_duplicate_of="original"))
    assert decision == "EXCLUDE"
    assert reasons[0] == "EXACT_DUPLICATE_REPRESENTATIVE_RETAINED"


def test_pending_inherited_review_is_not_promoted_to_experiment_suitable():
    decision, _ = decide(record("prior", record_kind="REVIEWED_WORKFLOW", source_review_status="PRIMARY_SOURCE_CHECKED_SECOND_REVIEW_PENDING"))
    assert decision == "HOLD"
