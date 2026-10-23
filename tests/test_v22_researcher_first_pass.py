"""Researcher-first-pass data integrity: 50 matching IDs, GT untouched."""
import csv
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ORIG=ROOT/"data/v2_2/qa/ai_repeatability_2026-10-23"
DATA=ROOT/"data/v2_2/qa/researcher_first_pass_2026-10-23"
def load(path):
 with path.open(encoding="utf-8",newline="") as f:
  return list(csv.DictReader(f))

def test_researcher_first_pass_is_complete_non_gold():
 blind=load(ORIG/"human_blind_review_50.csv")
 human=load(DATA/"researcher_first_pass_50.csv")
 assert len(human)==len(blind)==50
 assert [r["review_id"] for r in human]==[r["review_id"] for r in blind]
 for h,b in zip(human,blind):
  assert (h["query_id"],h["case_id"],h["reference_perspective"])==(b["query_id"],b["case_id"],b["reference_perspective"])
  assert h["human_score_0_4"] in ("0","1","2","3","4")
  assert h["status"]=="RESEARCHER_FIRST_PASS_NOT_GOLD"
  assert h["human_reason"]=="" and h["reviewer_id"]==""
  assert h["first_pass_annotator_id"]=="researcher"
  assert b["status"]=="UNJUDGED" and b["human_score_0_4"]==""
 payload=json.loads((DATA/"researcher_first_pass_50.json").read_text(encoding="utf-8"))
 assert payload["human_gold_adjudicated"] is False
 assert payload["blank_reason_count"]==50
 assert payload["sample_size"]==50

def test_comparison_is_reproducible_and_not_accuracy_claim():
 human=load(DATA/"researcher_first_pass_50.csv")
 pairs=load(DATA/"researcher_vs_ai_three_pass_50.csv")
 allai=load(ORIG/"three_pass_comparison.csv")
 q=json.loads((ROOT/"data/v2_2/dev_query_candidates_v2_2.json").read_text(encoding="utf-8"))["queries"]
 qmap={x["query_id"]:x for x in q}
 ai={(r["query_id"],r["perspective_id"],r["case_id"]):r for r in allai}
 assert len(pairs)==50 and len(ai)==2790
 assert [r["review_id"] for r in pairs]==[r["review_id"] for r in human]
 for h,p in zip(human,pairs):
  perspective=next(v["id"] for v in qmap[h["query_id"]]["draft_perspectives"] if v["title"]==h["reference_perspective"])
  a=ai[(h["query_id"],perspective,h["case_id"])]
  vals=[int(a[f"pass{i}"]) for i in (1,2,3)]
  median=sorted(vals)[1]
  score=int(h["human_score_0_4"])
  assert int(p["human_score_0_4"])==score and int(p["ai_median"])==median
  assert [int(p[f"ai_pass{i}"]) for i in (1,2,3)]==vals
  assert p["exact_match"]==("YES" if score==median else "NO")
  assert p["relevance_threshold_agreement"]==("YES" if (score>=3)==(median>=3) else "NO")
  assert p["comparison_status"]=="FIRST_PASS_DISAGREEMENT_ANALYSIS_NOT_GOLD"
 report=json.loads((DATA/"researcher_vs_ai_three_pass_report.json").read_text(encoding="utf-8"))
 assert report["verified_gt_count"]==0
 assert report["missing_rationales"]==50
 assert sum(p["exact_match"]=="YES" for p in pairs)==report["metrics"]["exact_ai_median_agreement"]==13
 assert sum(p["relevance_threshold_agreement"]=="NO" for p in pairs)==report["metrics"]["relevance_threshold_disagreement"]==20
 assert len(report["recheck_review_ids"])==report["metrics"]["recommended_recheck_union"]==26
