#!/usr/bin/env python3
"""Validate that every v2.3 Stage1..4 is really executed and preserve honest report."""
import csv,json,hashlib
from pathlib import Path
from collections import Counter

R=Path(__file__).resolve().parents[1];D=R/"data/v2_3";OUT=R/"experiments/v23_stages"
def J(path):return json.loads(path.read_text(encoding="utf-8"))
def C(path):
 with path.open(encoding="utf-8",newline="") as f:return list(csv.DictReader(f))
cases=J(D/"main_cases_v2_3.json")["cases"];ids={x["case_id"] for x in cases}
byid={x["case_id"]:x for x in cases}
q=J(D/"dev_query_candidates_v2_3.json")["queries"];qids={x["query_id"] for x in q}
label=C(D/"ground_truth/silver_dev_qrels_2520.csv")
assert len(cases)==84 and len(qids)==10 and len(label)==2520
assert all(x["human_approved"]=="FALSE" for x in label)
s1=J(OUT/"stage1/rankings.json")
s2=J(OUT/"stage2/final_rankings.json")
s3=J(OUT/"stage3/manifest.json")
s4=J(OUT/"stage4/recommendations.json")
assert set(s1)==set(s2)==set(s4)==qids
for qid in qids:
 p=s1[qid]["perspectives"]
 assert 2<=len(p)<=5 and len(s1[qid]["gpt_only_responses"])==3
 for method,rank in s1[qid]["rankings"].items():
  assert len(rank)>=5 and set(rank)<=ids and len(rank)==len(set(rank)),(qid,method)
 for method,rank in s2[qid].items():
  assert len(rank)>=20 and set(rank)<=ids and len(rank)==len(set(rank)),(qid,method)
 rec=s4[qid]
 assert rec["llm_source_grounded_response_id"] and rec["gpt_only_baseline_response_id"]
 given=set(rec["preselected_case_ranking"])
 for item in rec["llm_source_grounded_recommendations"]:
  assert item["evidence_case_ids"] and set(item["evidence_case_ids"])<=given
  assert all(item["strategy_id"] in byid[c]["strategy_labels"] for c in item["evidence_case_ids"])
  assert item["source_urls"] and len(item["source_urls"])==len(item["evidence_case_ids"])
assert s3["tested_pairs"]==77 and s3["ranked_case_occurrences"]==100
assert s3["wald_eligible_min_5_cells"]+s3["wald_abstained_sparse"]==77
assert len(C(OUT/"stage3/wald_pairs.csv"))==77
assert len(C(OUT/"stage1/per_query_metrics.csv"))==10*8*3
assert len(C(OUT/"stage2/per_query_metrics.csv"))==10*5*3
assert len(C(OUT/"stage4/per_query_metrics.csv"))==10*4*2
for stage in ("stage1","stage2","stage3","stage4"):
 assert (OUT/stage/"RESULT.md").exists()
 assert (OUT/stage/"manifest.json").exists()
for stage in ("stage1","stage2","stage4"):
 for row in C(OUT/stage/"summary.csv"):
  assert 0<=float(row["mean_recall"] if stage!="stage4" else row["mean_proxy_strategy_coverage"])<=1.00001
summaries={}
for stage in ("stage1","stage2","stage4"):
 table=C(OUT/stage/"summary.csv")
 summaries[stage]=[r for r in table if r["k"]=="10" if stage!="stage4"] if stage!="stage4" else [r for r in table if r["k"]=="5"]
lines=[
"# AX v2.3 Stage 1~4 — reproducible Dev run validation",
"",
"**All four stages executed against 84 frozen cases; no v1 metrics transferred.**",
"All 2520 relevance slots are **AI-only provisional Dev labels**, not independent human Gold. All Stage4 strategy coverage is a derived proxy, not external accuracy.",
"",
"## Stage 1 — Retrieval comparison (K=10)",
"",
"| Method | Recall@10 | Perspective Coverage@10 | Derived Strategy Proxy@10 |",
"|---|---:|---:|---:|"]
for x in summaries["stage1"]:
 lines.append(f"| {x['method']} | {float(x['mean_recall']):.3f} | {float(x['mean_perspective_coverage']):.3f} | {float(x['mean_proxy_strategy_coverage']):.3f} |")
lines += ["","## Stage 2 — Four controlled ablations (K=10)","","| Method | Recall@10 | Perspective Coverage@10 | Derived Strategy Proxy@10 |","|---|---:|---:|---:|"]
for x in summaries["stage2"]:
 lines.append(f"| {x['method']} | {float(x['mean_recall']):.3f} | {float(x['mean_perspective_coverage']):.3f} | {float(x['mean_proxy_strategy_coverage']):.3f} |")
lines+=["","## Stage 3 — factor-strategy source evidence","","- 11 Factor × 7 Strategy = 77 tables",
 f"- Eligible for Wald with all four 2×2 cell counts ≥5: **{s3['wald_eligible_min_5_cells']}**",
 f"- Explicit abstentions for sparse tables: **{s3['wald_abstained_sparse']}**",
 f"- Benjamini-Hochberg adjusted q≤0.05: **{s3['wald_fdr_q_below_0_05']}**",
 "- 10 questions × top 10 cases = 100 traceable recommendation evidence sources. These are observational links, not causal effect estimates.",
 "","## Stage 4 — Evidence fusion and actual LLM recommendation (K=5)","","| Method | Derived Strategy Coverage@5 | Derived Strategy Precision@5 |","|---|---:|---:|"]
for x in summaries["stage4"]:
 lines.append(f"| {x['method']} | {float(x['mean_proxy_strategy_coverage']):.3f} | {float(x['mean_proxy_strategy_precision']):.3f} |")
lines+=["","## Non-negotiable interpretation limits",
 "- Dev question list was known during corpus construction; do not claim held-out validity or selection-independent generalization.",
 "- LLM-Silver relevant and strategy labels are not independently researcher-confirmed Gold.",
 "- Gate and MLP are trained leave-one-Dev-query-out; independent Test performance still unknown.",
 "- Statistical Wald associations with observational source-selected cases are not causal proof.",
 "- Stage4 output ID/strategy witnesses are machine-validated; natural language explanation fidelity lacks independent human quality scoring.",
 "- Prior v1 baseline or Professor-described architecture advantages cannot be asserted if absent from these measured numbers.",
 "","**Status: Dev Stage 1–4 experiment execution and audit complete, separate held-out Test verification remains future research.**"]
(OUT/"ALL_STAGES_VERIFICATION.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
print("PASS all four v2.3 experimental stages, three subprotocols and grounded LLM recommendations.",flush=True)
