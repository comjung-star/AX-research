#!/usr/bin/env python3
"""Validate the independently reviewed QA sidecar without altering frozen dataset v2.0.0."""
import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "v2"
AUDIT = DATA / "qa" / "independent_q01_q09_2026-10-22.json"
TABLE = DATA / "qa" / "case_status_2026-10-22.csv"
PILOTS = DATA / "qa" / "pilot_and_scope_hold_registry_2026-10-22.csv"
CRITERIA = tuple("Q0" + str(n) for n in range(1, 10))
CATEGORIES = {"MEASURED", "PILOT", "ESTIMATED", "AGGREGATE", "UNKNOWN"}
DECISIONS = {"PROVISIONAL_AI_QA_PASS_PENDING_HUMAN", "REVIEW"}


def check():
    original = json.loads((DATA / "main_cases_v2.json").read_text(encoding="utf-8"))
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    orig_rows = original["cases"]
    results = audit["cases"]
    assert len(orig_rows) == len(results) == 98, "Record count mismatch"
    orig_ids = [row["case_id"] for row in orig_rows]
    qa_ids = [row["case_id"] for row in results]
    assert len(set(orig_ids)) == 98
    assert orig_ids == qa_ids, "QA is not aligned to original case order"
    orig_map = {c["case_id"]: c for c in orig_rows}
    qa_counts = Counter()
    criterion_counts = {name: Counter() for name in CRITERIA}
    outcomes = Counter()
    for row in results:
        case = orig_map[row["case_id"]]
        assert row["organization"] == case["organization"]
        assert row["source_url"] == case["source_url"]
        assert row["annotated_factor"] == case["factor_label"]
        assert row["annotated_strategy"] == case["strategy_label"]
        assert row["outcome_previous_type"] == case["outcome_type"]
        assert row["human_second_reviewer_approved"] is False
        assert row["ai_qa_decision"] in DECISIONS
        assert set(row["criteria"]) == set(CRITERIA)
        assert row["outcome_normalized"]["category"] in CATEGORIES
        assert row["criteria"]["Q08"]["result"] == "PASS", "outcome must be conservatively normalized"
        assert row["criteria"]["Q04"]["result"] == "PASS"
        assert row["criteria"]["Q09"]["result"] == "PASS"
        if not case["factor_label"]:
            assert row["criteria"]["Q05"]["result"] == "REVIEW", "no invented root cause"
        if not case["strategy_label"]:
            assert row["criteria"]["Q06"]["result"] == "REVIEW", "no invented strategy"
        if case["direct_mappings"]:
            assert len(case["direct_mappings"]) == 1
            assert case["mapping_review"]["decision"] == "SUPPORTED_APPLICABILITY"
        assert row["criteria"]["Q07"]["result"] == "PASS", "no fabricated link"
        for key in CRITERIA:
            criterion_counts[key][row["criteria"][key]["result"]] += 1
        pending = [key for key in CRITERIA if row["criteria"][key]["result"] != "PASS"]
        assert row["pending_criteria"] == pending
        expected = "REVIEW" if pending else "PROVISIONAL_AI_QA_PASS_PENDING_HUMAN"
        assert row["ai_qa_decision"] == expected
        qa_counts[expected] += 1
        outcomes[row["outcome_normalized"]["category"]] += 1

    assert dict(qa_counts) == audit["qa_decisions"]
    for code in CRITERIA:
        assert dict(criterion_counts[code]) == audit["criteria_counts"][code], code
    assert not any(c["human_ground_truth_approved"] for c in orig_rows)
    with TABLE.open(newline="", encoding="utf-8") as f:
        table = list(csv.DictReader(f))
    assert len(table) == 98
    for qa, item in zip(results, table):
        assert item["case_id"] == qa["case_id"]
        assert item["qa_decision"] == qa["ai_qa_decision"]
        assert item["outcome_category"] == qa["outcome_normalized"]["category"]
        for code in CRITERIA:
            assert item[code] == qa["criteria"][code]["result"]
    with PILOTS.open(newline="", encoding="utf-8") as f:
        pilot_rows = list(csv.DictReader(f))
    assert len(pilot_rows) == 6
    assert Counter(p["scope_decision"] for p in pilot_rows) == {
        "EXCLUDE_PILOT": 5,
        "HOLD_PRODUCTION_UNVERIFIED": 1,
    }
    assert qa_counts["PROVISIONAL_AI_QA_PASS_PENDING_HUMAN"] == 14
    assert qa_counts["REVIEW"] == 84
    print("Q01–Q09 QA sidecar PASS (integrity only; not source truth or human GT)")
    print("Provisional AI QA:", qa_counts["PROVISIONAL_AI_QA_PASS_PENDING_HUMAN"])
    print("REVIEW:", qa_counts["REVIEW"])
    print("Outcome classes:", dict(outcomes))


if __name__ == "__main__":
    check()
