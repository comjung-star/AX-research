#!/usr/bin/env python3
"""Validate v2.2 score-only single-researcher pilot without automatic Gold approval.

Neither free-text reasons nor independent second/third-party reviewers are mandatory.
The old v2.1 final-Gold validation gate is intentionally preserved separately.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"data/v2_2/qa/researcher_first_pass_2026-10-23"
VALID_SCORES={"0","1","2","3","4"}

def csv_rows(path: Path)->list[dict]:
    with path.open(encoding="utf-8",newline="") as f:
        return list(csv.DictReader(f))

def validate_researcher_first_pass(rows:list[dict])->dict:
    if len(rows)!=50:
        raise ValueError("Pilot must contain 50 rated cases")
    ids=[r.get("review_id") for r in rows]
    expected=["V22R"+str(i).zfill(3) for i in range(1,51)]
    if ids!=expected:
        raise ValueError("Missing/duplicate/reordered review ID")
    if any(r.get("human_score_0_4") not in VALID_SCORES
           or r.get("status")!="RESEARCHER_FIRST_PASS_NOT_GOLD"
           or r.get("first_pass_annotator_id")!="researcher"
           or not r.get("query_id") or not r.get("case_id")
           or not r.get("reference_perspective")
           for r in rows):
        raise ValueError("First pass needs a score, status, rater and case identity")
    # Intentionally DO NOT check human_reason; it is optional, including blank.
    return {"first_pass_count":50,"missing_scores":0,
            "reason_required":False,"independent_second_rater_required":False,
            "human_gold_adjudicated":False,
            "status":"RESEARCHER_FIRST_PASS_VALID_NOT_GOLD"}

def compare_independent_second_rater(first:list[dict],second:list[dict])->dict:
    """Optional add-on comparison if a second rater volunteers; never a GT gate."""
    validate_researcher_first_pass(first)
    if len(second)!=50:
        raise ValueError("Second rater must cover the same 50 pilot items")
    lookup={r.get("review_id"):r for r in second}
    if len(lookup)!=50 or None in lookup:
        raise ValueError("Duplicate or missing second-rater ID")
    equal=0
    for original in first:
        next_row=lookup.get(original["review_id"])
        if next_row is None:
            raise ValueError("Unmatched evaluation item")
        for field in ("query_id","case_id","reference_perspective"):
            if original[field]!=next_row.get(field):
                raise ValueError(f"Second rater has mismatched {field}")
        if next_row.get("score_0_4") not in VALID_SCORES:
            raise ValueError("Second human score must be 0..4")
        if not next_row.get("rater_id") or next_row["rater_id"]=="researcher":
            raise ValueError("Independent second-rater identity required")
        if next_row.get("status")!="SECOND_RATER_BLIND_PASS_NOT_GOLD":
            raise ValueError("Second pass must not claim adjudication")
        if original["human_score_0_4"]==next_row["score_0_4"]:
            equal+=1
    # Judge provenance and final decision (if scores differ) are future steps.
    return {"first_pass_count":50,"second_pass_count":50,
            "exact_score_agreement":equal,"needs_adjudication":50-equal,
            "reason_required":False,"independent_second_rater_required":False,
            "human_gold_adjudicated":False,
            "status":"OPTIONAL_DOUBLE_RATED_PILOT_NOT_GOLD"}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--first",type=Path,default=BASE/"researcher_first_pass_50.csv")
    parser.add_argument("--second",type=Path,default=None,
                        help="Optional only (NOT required for single-researcher v2.2 work)")
    args=parser.parse_args()
    first=csv_rows(args.first)
    outcome=(compare_independent_second_rater(first,csv_rows(args.second))
             if args.second else validate_researcher_first_pass(first))
    print(json.dumps(outcome,ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
