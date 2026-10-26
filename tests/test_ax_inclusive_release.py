import copy
import json
from pathlib import Path

import numpy as np
import pytest

from prototype.core import Engine, clean_text
from prototype.strategy import StrategyResponse, selected_evidence, template_report, validate_report
from scripts.build_ax_inclusive_release import factor_labels_from_problem, inherited_metadata, separate_source_statements, source_to_case
from scripts.review_all_ax_sources import all_inputs
from scripts.collect_ax_portals import parse_csv


def sample_record(**changes):
    return {"candidate_id": "EXAMPLE", "collection_kind": "PUBLIC_SECTOR_INVENTORY", "source_dataset_id": "TEST_PUBLIC",
            "organization": "Example City", "title": "Resident help chatbot", "task": "Resident help chatbot",
            "problem": "Staff face a high volume of manual questions. The city uses a chatbot to answer resident questions.",
            "context": "Citizen service", "source_url": "https://example.test/city", "development_stage": "PILOT",
            "ai_status": "SOURCE_CLASSIFIED_AI", **changes}


def test_every_saved_record_link_and_malformed_fragment_is_in_the_inventory():
    records = all_inputs()
    assert len(records) == len({row["candidate_id"] for row in records}) == 11658
    assert sum(row["collection_kind"] == "PUBLIC_SECTOR_INVENTORY" for row in records) == 5961
    assert sum(row["collection_kind"] == "DISCOVERED_SOURCE" for row in records) == 3208
    assert sum(row["collection_kind"] == "MALFORMED_SOURCE_ROW" for row in records) == 11
    assert sum(row.get("recovered_from_prior_parser", False) for row in records) == 9


def test_csv_header_without_quotes_does_not_disable_escaped_quotes_in_data():
    header, rows, malformed = parse_csv(b'id,title,description\n1,Example,"A ""quoted"" phrase, still one field"\n')
    assert malformed == []
    assert rows[0][1]["description"] == 'A "quoted" phrase, still one field'


def test_public_pilot_non_ai_and_unknown_scopes_are_retained_with_their_labels():
    record = source_to_case(sample_record())
    assert record["business_scope"] == "public_work"
    assert record["deployment_stage"] == "PILOT"
    assert record["retrieval_eligible"] is True
    non_ai = source_to_case(sample_record(ai_status="NON_AI_OR_UNCONFIRMED_TECHNOLOGY"))
    assert non_ai["retrieval_eligible"] is True
    assert non_ai["strategy_labels"] == []
    assert non_ai["human_ground_truth_approved"] is False
    unknown = source_to_case({"candidate_id": "UNCLASSIFIED", "collection_kind": "CASE_PORTAL", "url": "https://example.test/a"})
    assert unknown["business_scope"] == "unspecified"
    assert unknown["case_id"]


def test_missing_source_text_does_not_turn_into_an_implemented_workflow():
    source = {"candidate_id": "LINK", "collection_kind": "DISCOVERED_SOURCE", "url": "https://example.test/story", "publisher": "Public source"}
    audit = {"access": {"status": "ACCESS_FAILED"}, "check_status": "ACCESS_ATTEMPT_COMPLETED_CONTENT_UNAVAILABLE"}
    record = source_to_case(source, audit)
    assert record["record_kind"] == "SOURCE_LINK"
    assert record["retrieval_eligible"] is False
    assert record["problem"] == record["implementation"] == "UNKNOWN"
    assert record["deployment_stage"] == "UNKNOWN"


def test_consumer_and_research_content_is_classified_without_scope_rejection():
    audit = {"access": {"status": "FETCHED"}, "check_status": "PUBLIC_PAGE_FETCH_AND_TEXT_CHECK_COMPLETED"}
    for title, expected in [("Personal use hobby assistant", "consumer_personal"), ("University research assistant", "education_research")]:
        record = source_to_case({"candidate_id": expected, "collection_kind": "CASE_PORTAL", "source_title": title, "url": "https://example.test/" + expected}, audit)
        assert expected in record["business_scope_tags"]
        assert record["retrieval_eligible"] is True


def test_problem_factor_rules_cannot_read_solution_fields():
    problem = "Manual copying takes hours."
    factors = factor_labels_from_problem(problem)
    assert factors and all(not factor.startswith("F04_") for factor in factors)
    assert factor_labels_from_problem("UNKNOWN") == []
    parsed_problem, implementation, anchors = separate_source_statements("The office relies on costly manual copying. It uses a chatbot to answer questions.")
    assert "chatbot" not in parsed_problem
    assert "chatbot" in implementation
    assert anchors == {"problem": [0], "implementation": [1]}


def test_malformed_source_row_is_preserved_without_invented_column_values():
    record = source_to_case({"candidate_id": "BAD_ROW", "collection_kind": "MALFORMED_SOURCE_ROW", "source_record_id": "PSTW-X", "title": "Broken source row", "source_row": 20, "raw_field_count": 9, "expected_field_count": 59})
    assert record["record_kind"] == "SOURCE_ROW_WITH_PARSE_ERROR"
    assert record["retrieval_eligible"] is False
    assert record["source_parse_error_details"]["raw_field_count"] == 9
    assert record["problem"] == "UNKNOWN"


def test_reference_only_branch_can_abstain_from_strategy_generation():
    engine = Engine()
    result = engine.recommend({"query": engine.examples[0]["query"]})
    branches = copy.deepcopy(result["branches"][:1])
    for card in branches[0]["cases"]:
        card["strategies"] = []
        card["factors"] = []
    report = template_report(result["query"], branches)
    assert report["perspectives"][0]["strategies"] == []
    report["case_explanations"] = [{"case_id": card["case_id"], "solution": "구현 미확인", "outcome": "성과 미확인"} for card in branches[0]["cases"]]
    StrategyResponse.model_validate(report)
    validate_report(report, selected_evidence(branches), clean_text)
    assert "근거가 부족" in report["summary"]


def test_scope_validation_rejects_untrusted_or_unknown_filter_values():
    engine = Engine()
    for scope in [[], {}, "DROP TABLE", "private_only"]:
        with pytest.raises(ValueError):
            engine.recommend({"query": "관련 자료를 확인하려는 업무 질문입니다", "business_scope": scope})


def test_scope_filter_applies_to_every_branch_without_changing_stored_corpus():
    engine = Engine()
    chosen = engine.case_ids[0]
    engine.case_metadata[chosen] = {"business_scope_tags": ["public_work"], "business_scope_ko": "공공기관·공공서비스"}
    result = engine.recommend({"query": engine.examples[0]["query"], "business_scope": "public_work"})
    assert all(branch["candidate_count"] == 1 for branch in result["branches"])
    assert all([case["case_id"] for case in branch["cases"]] == [chosen] for branch in result["branches"])
    assert len(engine.cases) == 84
    assert result["business_scope"] == "public_work"
