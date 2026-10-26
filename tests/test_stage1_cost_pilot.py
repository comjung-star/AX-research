import json
from decimal import Decimal

import pytest

from scripts import stage1_cost_pilot as pilot


def test_prompt_excludes_solution_and_legacy_labels():
    cases = {"case_a": {"problem": "delay", "task": "review", "context": "office", "implementation": "SECRET_SOLUTION", "old_score": 4}}
    unit = {"query_id": "query_a", "case_id": "case_a", "perspective_id": "aspect_a", "reference_perspective": "REF_ONLY"}
    batch = pilot.build_batch("test", "query_case", [unit], cases, {"query_a": "manual review"})
    assert "SECRET_SOLUTION" not in batch["user"]
    assert "old_score" not in batch["user"]
    assert "REF_ONLY" not in batch["user"]
    assert "case_a" not in batch["user"]


def test_reference_prompt_retains_aspect():
    cases = {"case_a": {"problem": "delay", "task": "review", "context": "office"}}
    unit = {"query_id": "query_a", "case_id": "case_a", "reference_perspective": "REF_ONLY"}
    assert "REF_ONLY" in pilot.build_batch("test", "reference_case", [unit], cases, {"query_a": "query"})["user"]


@pytest.mark.parametrize("text", [
    '{"ratings":[{"i":0,"r":true,"why":"evidence"}]}',
    '{"ratings":[{"i":0,"r":5,"why":"evidence"}]}',
    '{"ratings":[]}',
    '{"ratings":[{"i":1,"r":0,"why":"evidence"}]}',
])
def test_invalid_output_is_not_converted_to_nonrelevance(text):
    with pytest.raises(ValueError):
        pilot.parse_ratings(text, 1)


def test_valid_rating_preserves_score_and_reason():
    assert pilot.parse_ratings('{"ratings":[{"i":0,"r":3,"why":"Direct problem and task match"}]}', 1)[0]["r"] == 3


def test_actual_cached_usage_cost_is_decimal_exact():
    result = pilot.extract_usage("openai", {"usage": {"input_tokens": 1000, "output_tokens": 100, "input_tokens_details": {"cached_tokens": 200}}})
    assert Decimal(result["usage_cost_usd"]) == Decimal("0.00013200")


def test_gemini_reasoning_tokens_are_included():
    result = pilot.extract_usage("gemini", {"usageMetadata": {"promptTokenCount": 100, "candidatesTokenCount": 20, "thoughtsTokenCount": 10}})
    assert result["actual_output_tokens_including_thinking"] == 30
    assert Decimal(result["usage_cost_usd"]) == Decimal("0.00010500")


def test_uncertain_requests_keep_full_reservation_and_enforce_cap(tmp_path, monkeypatch):
    monkeypatch.setattr(pilot, "LOCAL", tmp_path)
    batch = {"batch_id": "one"}
    assert pilot.reserve_generation("claude", batch, Decimal("0.20"))
    with pytest.raises(ValueError, match="cost cap"):
        pilot.reserve_generation("claude", {"batch_id": "two"}, Decimal("0.06"))


def test_counting_payloads_do_not_request_generation():
    batch = {"user": "actual prompt", "max_output_tokens": 1408}
    assert "max_tokens" not in pilot.request_body("claude", batch, True)
    assert "max_output_tokens" not in pilot.request_body("openai", batch, True)
    assert "generateContentRequest" in pilot.request_body("gemini", batch, True)


def test_json_mode_reminder_is_present_in_user_input_not_only_system():
    cases = {"case_a": {"problem": "delay", "task": "review", "context": "office"}}
    unit = {"query_id": "query_a", "case_id": "case_a"}
    batch = pilot.build_batch("test", "query_case", [unit], cases, {"query_a": "manual review"})
    assert batch["user"].endswith("Return JSON.")


def test_fixed_plan_contains_only_authorized_forty_pilot_pairs(tmp_path, monkeypatch):
    monkeypatch.setattr(pilot, "OUTPUT", tmp_path)
    plan = pilot.prepare()
    assert plan["pilot_pairs"] == 40
    assert sum(batch["pair_count"] for batch in plan["full_batches"]) == 4480
    assert len(plan["full_batches"]) == 224
    assert len(plan["pilot_batches"]) == 2
    assert all(len({unit["query_id"] for unit in batch["units"]}) == 10 for batch in plan["pilot_batches"])
    assert "implementation" not in json.dumps([batch["user"] for batch in plan["full_batches"]])


def test_output_projection_weights_full_scope_sizes_not_pilot_mix():
    target = [{"scope": "query_case", "pair_count": 10}, {"scope": "reference_case", "pair_count": 30}]
    sample = [{"scope": "query_case", "pair_count": 10, "actual_output_tokens_including_thinking": 10, "schema_valid": True},
              {"scope": "reference_case", "pair_count": 10, "actual_output_tokens_including_thinking": 30, "schema_valid": True}]
    assert pilot.estimate_output_tokens(target, sample) == 100


def test_model_identity_is_not_silently_substituted():
    assert pilot.model_matches("gemini", "gemini-3.5-flash-lite")
    assert not pilot.model_matches("gemini", "gemini-2.5-flash-lite")
    assert not pilot.model_matches("claude", None)


def test_full_batches_cannot_be_sent_through_pilot_generator():
    with pytest.raises(ValueError, match="authorized"):
        pilot.pilot_one("claude", {"batch_id": "full-query_case-0000", "pair_count": 20})


def test_full_execution_is_not_a_cli_phase():
    with pytest.raises(SystemExit):
        pilot.main(["full"])
