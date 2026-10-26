import json
from decimal import Decimal

import pytest

from scripts import query_isolated_revalidation as run


def example(scope="query_case"):
    query = "제조현장에서 생산계획을 수작업으로 조정하는 데 시간이 오래 걸린다."
    reference = "생산계획 조정 지연" if scope == "reference_case" else ""
    unit = {"query_id": "V21D010", "perspective_id": "P1" if reference else "", "case_id": "CASE_A", "reference_perspective": reference}
    cases = {"CASE_A": {"problem": "Production schedules require manual adjustment.", "task": "Adjust production schedules", "context": "Manufacturing order changes"}}
    job = run.build_job("pilot", 0, scope, [unit], cases, {"V21D010": query})
    row = {"query_id": unit["query_id"], "perspective_id": unit["perspective_id"], "case_id": "CASE_A", "score": 3,
           "task_match": "DIRECT", "ambiguity": "NONE", "query_quote": query[:15], "case_quote": cases["CASE_A"]["problem"],
           "reference_quote": reference, "reason": "Production rescheduling directly matches the query's manufacturing planning task."}
    return job, row, {"V21D010": query, "V21D002": "긴 이메일 스레드를 읽고 요약하는 업무에 많은 시간을 쓰고 있다."}


def test_homogeneous_batch_passes_with_exact_source_quotes():
    job, row, queries = example()
    assert run.validate(json.dumps({"ratings": [row]}), job, queries)["valid"]
    assert job["items"][0]["query_text"] == queries["V21D010"]


def test_reference_id_and_quote_are_kept_separate():
    job, row, queries = example("reference_case")
    assert run.validate(json.dumps({"ratings": [row]}), job, queries)["valid"]
    row["reference_quote"] = "unrelated text"
    assert "REFERENCE_QUOTE_NOT_VERBATIM" in run.validate(json.dumps({"ratings": [row]}), job, queries)["format_errors"]


def test_original_manufacturing_email_confusion_is_detected():
    job, row, queries = example()
    row["score"] = 0
    row["task_match"] = "NONE"
    row["reason"] = "Production scheduling is unrelated to email-thread summarization."
    result = run.validate(json.dumps({"ratings": [row]}), job, queries)
    assert not result["valid"]
    assert result["hard_errors"][0]["kind"] == "UNANCHORED_FOREIGN_TASK"


def test_quote_from_another_query_is_a_hard_error():
    job, row, queries = example()
    row["query_quote"] = queries["V21D002"][:15]
    assert any(error["kind"] == "OTHER_QUERY_QUOTE" for error in run.validate(json.dumps({"ratings": [row]}), job, queries)["hard_errors"])


def test_long_reason_does_not_hide_question_confusion():
    job, row, queries = example()
    row["reason"] = "Production scheduling is unrelated to email-thread summarization. " + "extra " * 45
    result = run.validate(json.dumps({"ratings": [row]}), job, queries)
    assert "REASON_WORD_LIMIT" in result["format_errors"]
    assert result["hard_errors"][0]["kind"] == "UNANCHORED_FOREIGN_TASK"


def test_vehicle_body_shop_is_manufacturing_source_evidence():
    job, row, queries = example()
    job["items"][0].update(query_text="Customer support inquiry burden is rising.", problem="Metal deposits can damage cables.", task="Detect weld splatter on vehicle underbodies")
    job["items"][0]["context"] = "Neckarsulm body shop series production"
    row["reason"] = "Vehicle manufacturing inspection differs from customer inquiry handling."
    assert "MANUFACTURING" not in run.context_flags(row, job["items"][0])


def test_creative_image_production_is_not_a_manufacturing_trigger():
    job,row,queries=example()
    job["items"][0].update(query_text="Summarize long email threads and identify actions.",problem="Costly photography constrains creative assets.",task="Produce approved lifestyle images",context="Product advertising campaigns")
    row["reason"]="Advertising image production does not summarize email threads."
    assert not run.context_flags(row,job["items"][0])


def test_gemini_schema_requires_exact_keys_without_relaxing_validation():
    job, row, queries = example()
    body = run.request_body("gemini", job)
    schema = body["generationConfig"]["responseJsonSchema"]
    item = schema["properties"]["ratings"]["items"]
    assert set(item["required"]) == run.FIELDS
    assert item["additionalProperties"] is False
    assert item["properties"]["query_id"]["enum"] == [job["query_id"]]
    row["case_id_quote"] = row.pop("case_quote")
    assert not run.validate(json.dumps({"ratings": [row]}), job, queries)["valid"]


def test_evidence_from_another_case_is_a_hard_mapping_error():
    job, row, queries = example()
    other = {**job["items"][0], "case_id": "CASE_B", "task": "Classify invoice tax codes for billing review"}
    job["items"].append(other)
    row["case_quote"] = other["task"]
    assert any(e["kind"] == "OTHER_CASE_QUOTE" for e in run.validate(json.dumps({"ratings": [row]}), job, queries)["hard_errors"])


def test_unknown_billed_attempt_is_not_replayed(tmp_path, monkeypatch):
    job, row, queries = example()
    monkeypatch.setattr(run, "OUTPUT", tmp_path)
    path = tmp_path / "attempts/claude/pilot_0000_a1.json"
    path.parent.mkdir(parents=True)
    path.write_text('{"state":"ACCESS_OR_TRANSPORT_FAILURE","reserved_usd":"0.01"}', encoding="utf-8")
    monkeypatch.setattr(run.api, "transport", lambda *args: pytest.fail("Must not replay uncertain generation"))
    run.STOP.clear()
    try:
        assert run.run_job("claude", job, queries)["state"] == "UNCERTAIN_PREVIOUS_ATTEMPT_NO_REPLAY"
    finally:
        run.STOP.clear()


def test_full_stage1_requires_reviewed_pilot_gate(tmp_path, monkeypatch):
    monkeypatch.setattr(run, "OUTPUT", tmp_path)
    (tmp_path / "pilot_gate.json").write_text('{"allow_full_stage1":false}', encoding="utf-8")
    with pytest.raises(ValueError, match="reviewed exact-40"):
        run.execute_stage1({})


def test_methodology_hold_blocks_cli_before_any_preparation_or_api(tmp_path,monkeypatch):
    monkeypatch.setattr(run,"OUTPUT",tmp_path)
    (tmp_path/"halt.json").write_text('{"active":true}',encoding="utf-8")
    monkeypatch.setattr(run,"prepare",lambda:pytest.fail("No work may precede active hold"))
    monkeypatch.setattr(run.api,"transport",lambda *a:pytest.fail("Hold must prevent all API calls"))
    assert run.main(["stage1"])==2
    assert run.main(["count"])==2
    job,_,_=example()
    with pytest.raises(ValueError,match="Methodology hold"):
        run.reserve_attempt("claude",job,1,Decimal("0.01"))


def test_wrong_id_is_never_remapped_to_a_neighbor():
    job, row, queries = example()
    row["case_id"] = "CASE_B"
    result = run.validate(json.dumps({"ratings": [row]}), job, queries)
    assert not result["ratings"]
    assert any(error["kind"] == "INVALID_TARGET_ID" for error in result["hard_errors"])


def test_missing_and_duplicate_items_fail():
    job, row, queries = example()
    assert not run.validate('{"ratings":[]}', job, queries)["valid"]
    assert not run.validate(json.dumps({"ratings": [row, row]}), job, queries)["valid"]


def test_reason_word_limit_matches_prompt_and_policy():
    job, row, queries = example()
    row["reason"] = " ".join(["planning"] * 41)
    assert "REASON_WORD_LIMIT" in run.validate(json.dumps({"ratings": [row]}), job, queries)["format_errors"]
    assert run.CONFIG["max_reason_words"] == 40
    assert "at most 40" in run.SYSTEM


def test_mixed_queries_and_aspects_are_rejected_before_requests():
    job, row, queries = example()
    units = [job["units"][0], {**job["units"][0], "query_id": "V21D002"}]
    with pytest.raises(ValueError, match="Mixed"):
        run.build_job("pilot", 0, "query_case", units, {}, queries)
    units = [job["units"][0], {**job["units"][0], "perspective_id": "OTHER_ASPECT"}]
    with pytest.raises(ValueError, match="Mixed"):
        run.build_job("pilot", 0, "reference_case", units, {}, queries)


def test_three_judges_and_unknown_are_not_silently_changed():
    assert run.CONFIG["independent_judges_required"] == 3
    assert len(set(run.CONFIG["models"].values())) == 3
    assert not run.CONFIG["unjudged_is_zero"]
    assert run.CONFIG["stage4_test_sealed"]


def test_uncertain_budget_keeps_full_reserved_cost(tmp_path, monkeypatch):
    monkeypatch.setattr(run, "OUTPUT", tmp_path)
    monkeypatch.setattr(run, "PREVIOUS_OUTPUT", tmp_path / "previous")
    target = tmp_path / "attempts/claude/a.json"
    target.parent.mkdir(parents=True)
    target.write_text('{"reserved_usd":"0.03","state":"TIMEOUT"}', encoding="utf-8")
    assert run.reserved_cost("claude") == Decimal("0.03")


def test_exact_same_pilot_keys_and_no_original_mutation(tmp_path, monkeypatch):
    monkeypatch.setattr(run, "OUTPUT", tmp_path)
    plan = run.prepare()
    assert sum(len(job["units"]) for job in plan["pilot_jobs"]) == 40
    assert len(plan["pilot_jobs"]) == 27
    assert sum(len(job["units"]) for job in plan["stage1_jobs"]) == 1120
    assert len(plan["stage1_jobs"]) == 140
    for job in plan["pilot_jobs"] + plan["stage1_jobs"]:
        assert len({(item["query_id"], item["perspective_id"]) for item in job["items"]}) == 1


def test_adjacent_operation_cannot_be_labeled_high_without_direct_match():
    job, row, queries = example()
    row["task_match"] = "PARTIAL"
    assert "TASK_MATCH_SCORE_CONSTRAINT" in run.validate(json.dumps({"ratings": [row]}), job, queries)["format_errors"]
