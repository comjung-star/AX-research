#!/usr/bin/env python3
"""Stage 3 v2.3: sparse-safe Wald associations and complete retrieval provenance.
This analyzes associations, not causality; no fabricated Wald when sparse.
"""
import csv,json,sys
from collections import Counter,defaultdict
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from ax_research.stage3_wald import analyze,validate_cases
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"data/v2_3";ST1=ROOT/"experiments/v23_dev/stage1";ST2=ROOT/"experiments/v23_dev/stage2"
OUT=ROOT/"experiments/v23_dev/stage3";OUT.mkdir(parents=True,exist_ok=True)
def read(p):
 with open(p,encoding="utf-8",newline="") as f:return list(csv.DictReader(f))
def write(p,rows):
 assert rows
 with open(p,"w",encoding="utf-8",newline="") as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
cases=read(BASE/"main_cases_v2_3.csv")
factors=[r["factor_id"] for r in read(BASE/"root_cause_taxonomy_v2_3.csv")]
strategies=[r["strategy_id"] for r in read(BASE/"strategy_taxonomy_v2_3.csv")]
prepped=validate_cases(cases,factors,strategies)
assert len(prepped)==84 and len(factors)==11 and len(strategies)==7
wald=analyze(prepped,factors,strategies,min_cell=5)
assert len(wald)==77
write(OUT/"factor_strategy_wald_77_pairs.csv",wald)
lookup={(r["factor_id"],r["strategy_id"]):r for r in wald}
cmap={c["case_id"]:c for c in cases}
replay=read(ST2/"rankings_top20.csv")
branches=read(ST1/"branch_rankings.csv")
candidate=defaultdict(list)
for b in branches:
 if b["retrieval"]!="dense" or int(b["local_rank"])>20:continue
 candidate[(b["query_id"],int(b["run_id"]),b["case_id"])].append(b)
trace=[];link=[];insufficient=0
for r in replay:
 if r["system"] not in ("stage2_4_same_pool_rrf","stage2_4_query_case_MLP_LOQO"):continue
 if int(r["rank"])>10:continue
 c=cmap[r["case_id"]]
 q=r["query_id"];rep=int(r["run_id"]);cid=r["case_id"]
 br=candidate.get((q,rep,cid),[])
 # Stage2-4 pool may enter through sparse leg; look up sparse candidate too
 if not br:
  br=[b for b in branches if b["query_id"]==q and int(b["run_id"])==rep and b["case_id"]==cid and b["retrieval"]=="bm25" and int(b["local_rank"])<=10]
 for f in c["root_cause_factor"].split("|"):
  for st in c["strategy"].split("|"):
   w=lookup[(f,st)]
   trace.append(dict(system=r["system"],query_id=q,run_id=rep,rank=r["rank"],
    case_id=cid,factor_id=f,strategy_id=st,
    factor_strategy_link="WITHIN_CASE_CO_OCCURRENCE_NOT_CAUSAL",
    source_url=c["source_url"],candidate_perspectives="|".join(sorted({b["perspective_id"] for b in br})),
    wald_status=w["status"],wald_odds_ratio=w["odds_ratio"],
    wald_p=w["wald_p"],wald_bh_q=w["bh_q_all_pairs"]))
   if not w["wald_eligible"]:insufficient+=1
 link.append(dict(system=r["system"],query_id=q,run_id=rep,rank=r["rank"],
  case_id=cid,distinct_retrieval_branches=len({b["perspective_id"] for b in br}),
  has_evidence=bool(c["problem"] and c["implementation"] and c["source_url"]),
  rank_occurrence_unit="UNIQUE_QUERY_RUN_CASE"))
write(OUT/"source_factor_strategy_trace.csv",trace)
write(OUT/"retrieval_case_provenance.csv",link)
assert len(link)==600
counts=Counter(r["status"] for r in wald)
report=dict(stage="STAGE_3_REAL_EXECUTED",cases=84,factors=11,strategies=7,pairs=77,
 wald_eligible=counts.get("WALD_DESCRIPTIVE",0),wald_sparse_abstentions=counts.get("SPARSE_ABSTAIN",0),
 trace_rows=len(trace),unique_rank_occurrences=len(link),unusable_wald_case_links=insufficient,
 evaluative_claim="ASSOCIATION_ONLY_NOT_CAUSAL",
 reference_retrieval="same-pool RRF and interaction MLP, top10 each query x 3 repeats",
 strategy_coverage_cannot_increase_from_metadata_only=True,
 candidate_branch_links_not_ground_truth=True,
 status="DEV_AI_SILVER_EVIDENCE_DIAGNOSTIC")
(OUT/"manifest.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("STAGE3 COMPLETE",json.dumps(report,ensure_ascii=False),flush=True)
