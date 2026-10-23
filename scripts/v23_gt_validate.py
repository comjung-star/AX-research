#!/usr/bin/env python3
"""Verify v2.3 silver qrels without treating AI judgments as human Gold."""
import csv, json
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"data/v2_3"
OUT=BASE/"ground_truth"
def rows(name):
    with (OUT/name).open(encoding="utf-8",newline="") as f:return list(csv.DictReader(f))
cases=json.loads((BASE/"main_cases_v2_3.json").read_text(encoding="utf-8"))
queries=json.loads((BASE/"dev_query_candidates_v2_3.json").read_text(encoding="utf-8"))["queries"]
cids={x["case_id"] for x in cases["cases"]}
pairs={(q["query_id"],p["id"]) for q in queries for p in q["draft_perspectives"]}
assert len(cids)==84 and len(pairs)==30
l=rows("silver_dev_qrels_2520.csv")
assert len(l)==2520 and len({(x["query_id"],x["perspective_id"],x["case_id"]) for x in l})==2520
assert {(x["query_id"],x["perspective_id"],x["case_id"]) for x in l}=={(q,p,c) for q,p in pairs for c in cids}
for r in l:
    scores=[int(r["score_pass"+str(i)]) for i in (1,2,3)]
    assert all(0<=v<=4 for v in scores)
    assert r["relevance_0_4"]==str(sorted(scores)[1])
    assert r["gold_relevant_flag"]==str(int(int(r["relevance_0_4"])>=3))
    assert r["exact_agreement"]==str(int(len(set(scores))==1))
    assert r["threshold_flip"]==str(int(len({v>=3 for v in scores})>1))
    assert r["judgment_status"].startswith("AI_SILVER_")
    assert r["human_approved"]=="FALSE"
    assert r["evidence_reason"] and r["response_id"] and r["judge_model"]
ps=rows("perspective_answerability.csv")
assert len(ps)==30 and {(r["query_id"],r["perspective_id"]) for r in ps}==pairs
for r in ps:
    eligible=sum(int(x["gold_relevant_flag"]) for x in l if (x["query_id"],x["perspective_id"])==(r["query_id"],r["perspective_id"]))
    assert int(r["silver_relevant_count"])==eligible
ss=rows("strategy_set_candidates.csv")
assert len(ss)==10 and all(r["status"].startswith("AI_SILVER_DERIVED") and r["human_approved"]=="FALSE" for r in ss)
h=rows("legacy_human_pilot_comparison.csv")
assert len(h)==50 and all(r["status"].endswith("NOT_V23_GOLD") for r in h)
rv=rows("optional_blind_researcher_review.csv")
assert all(r["status"]=="UNJUDGED_HUMAN_REVIEW_OPTIONAL" and not r["blind_human_score_0_4"] for r in rv)
manifest=json.loads((OUT/"silver_release_manifest.json").read_text(encoding="utf-8"))
assert manifest["status"]=="COMPLETE_AI_ONLY_SILVER_2520_NOT_HUMAN_GROUND_TRUTH"
assert manifest["counts"]["judgments"]==2520
assert manifest["counts"]["ai_api_grades"]==7560
assert manifest["counts"]["human_approved_v23"]==0
assert manifest["counts"]["optional_review_queue"]==len(rv)
assert manifest["counts"]["threshold_flips"]==sum(int(x["threshold_flip"]) for x in l)
assert sum(int(v) for v in manifest["counts"]["silver_score_histogram"].values())==2520
for q in queries:
    assert any(x["query_id"]==q["query_id"] for x in ss)
print("PASS: v2.3 AI silver 2520 complete, 3 blind passes each, perspective/strategy candidate coverage, ZERO false human Gold labels")
