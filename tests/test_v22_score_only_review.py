"""v2.2 score-only evaluation allows blank reasons, without approving GT."""
import csv
from pathlib import Path
import pytest
from scripts.v22_score_only_review import (
    csv_rows,validate_researcher_first_pass,compare_independent_second_rater
)

ROOT=Path(__file__).resolve().parents[1]
FIRST=ROOT/"data/v2_2/qa/researcher_first_pass_2026-10-23/researcher_first_pass_50.csv"

def test_all_existing_50_valid_without_reasons():
    rows=csv_rows(FIRST)
    assert len(rows)==50
    assert all(row["human_reason"]=="" for row in rows)
    out=validate_researcher_first_pass(rows)
    assert out["reason_required"] is False
    assert out["independent_second_rater_required"] is False
    assert out["human_gold_adjudicated"] is False
    assert out["status"]=="RESEARCHER_FIRST_PASS_VALID_NOT_GOLD"

def test_score_required_not_reason():
    rows=csv_rows(FIRST)
    rows[0]["human_score_0_4"]=""
    with pytest.raises(ValueError,match="needs a score"):
        validate_researcher_first_pass(rows)
    rows=csv_rows(FIRST)
    rows[1]["human_reason"]=""
    assert validate_researcher_first_pass(rows)["first_pass_count"]==50

def test_two_distinct_raters_are_still_not_gold():
    first=csv_rows(FIRST)
    second=[dict(review_id=r["review_id"],query_id=r["query_id"],
                 reference_perspective=r["reference_perspective"],
                 case_id=r["case_id"],score_0_4=r["human_score_0_4"],
                 rater_id="synthetic_second_rater_TEST_ONLY",
                 status="SECOND_RATER_BLIND_PASS_NOT_GOLD") for r in first]
    # Synthetic reviewers inside unit tests are never actual human ratings.
    out=compare_independent_second_rater(first,second)
    assert out["exact_score_agreement"]==50
    assert out["independent_second_rater_required"] is False
    assert out["human_gold_adjudicated"] is False
    second[2]["score_0_4"]="0" if second[2]["score_0_4"]!="0" else "4"
    out=compare_independent_second_rater(first,second)
    assert out["needs_adjudication"]==1
    second[2]["rater_id"]="researcher"
    with pytest.raises(ValueError,match="Independent"):
        compare_independent_second_rater(first,second)
