#!/usr/bin/env python3
"""v2.3 Stage 3: Factor↔Strategy cross-sectional Wald diagnostics
and verifiable Perspective→Case→Factor→Strategy evidence lineage.
Observational correlations only, no causal interpretation.
"""
import csv,json,math
from collections import defaultdict,Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data/v2_3";S2=ROOT/"experiments/v23_stages/stage2"
OUT=ROOT/"experiments/v23_stages/stage3";OUT.mkdir(parents=True,exist_ok=True)
cases=json.loads((DATA/"main_cases_v2_3.json").read_text(encoding="utf-8"))["cases"]
queries=json.loads((DATA/"dev_query_candidates_v2_3.json").read_text(encoding="utf-8"))["queries"]
stage1=json.loads((ROOT/"experiments/v23_stages/stage1/rankings.json").read_text(encoding="utf-8"))
ranking=json.loads((S2/"final_rankings.json").read_text(encoding="utf-8"))
factors=sorted({f for c in cases for f in c["factor_labels"]})
strategies=sorted({s for c in cases for s in c["strategy_labels"]})
cid={c["case_id"]:c for c in cases}
assert len(cases)==84 and len(factors)==11 and len(strategies)==7
def writer(name,rows,fields):
 with (OUT/name).open("w",encoding="utf-8",newline="") as f:
  w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore");w.writeheader();w.writerows(rows)
def bh(values):
 n=len(values);ordered=sorted(range(n),key=lambda j:(values[j],j))
 out=[1.0]*n;running=1.0
 for rank in range(n,0,-1):
  i=ordered[rank-1];running=min(running,values[i]*n/rank);out[i]=running
 return out
out=[]
for f in factors:
 for s in strategies:
  a=sum(f in c["factor_labels"] and s in c["strategy_labels"] for c in cases)
  b=sum(f in c["factor_labels"] and s not in c["strategy_labels"] for c in cases)
  c_=sum(f not in c["factor_labels"] and s in c["strategy_labels"] for c in cases)
  d=sum(f not in c["factor_labels"] and s not in c["strategy_labels"] for c in cases)
  eligible=min(a,b,c_,d)>=5
  if eligible:
   logor=math.log((a*d)/(b*c_))
   se=math.sqrt(1/a+1/b+1/c_+1/d)
   z=logor/se
   p=math.erfc(abs(z)/math.sqrt(2.0))
   odds=math.exp(logor)
  else:logor=se=z=p=odds=None
  out.append({"factor_id":f,"strategy_id":s,"a":a,"b":b,"c":c_,"d":d,
    "eligible":int(eligible),"log_odds_ratio":logor,"odds_ratio":odds,
    "wald_z":z,"wald_p":p,"wald_se":se,"fdr_q":None})
valid=[i for i,x in enumerate(out) if x["eligible"]]
qs=bh([out[i]["wald_p"] for i in valid])
for i,q in zip(valid,qs):out[i]["fdr_q"]=q
writer("wald_pairs.csv",out,list(out[0]))
look={(x["factor_id"],x["strategy_id"]):x for x in out}
# Stage 3-2 A/B/C trace, but no fake "all runtime perspectives recovered":
# Stage1 branch ranks actually contains every independent generated runtime perspective.
lines=[]
for q in queries:
 qid=q["query_id"];r=stage1[qid]
 branches=r["branch_rankings"]["dense"]
 final=ranking[qid]["stage2_1_equal_multiview"][:10]
 if len(branches)!=len(r["perspectives"]):raise ValueError("branch count mismatch")
 for rank,cid_ in enumerate(final,1):
  c=cid[cid_]
  found=[r["perspectives"][i]["id"] for i,b in enumerate(branches) if cid_ in b[:20]]
  if not found:found=["NOT_IN_STAGE1_DENSE_TOP20_BRANCHES"]
  for f in c["factor_labels"]:
   for s in c["strategy_labels"]:
    w=look[(f,s)]
    lines.append({"query_id":qid,"case_rank":rank,"case_id":cid_,
      "runtime_perspective_ids":"|".join(found),"factor_id":f,"strategy_id":s,
      "case_source_url":c["source_url"],"case_problem":c["problem"],
      "source_audited":"TRUE","wald_eligible":w["eligible"],
      "wald_logor":w["log_odds_ratio"] if w["eligible"] else "",
      "wald_fdr_q":w["fdr_q"] if w["eligible"] else "",
      "wald_interpretation":"OBSERVATIONAL_ASSOCIATION_NOT_CAUSAL" if w["eligible"] else "ABSTAIN_SPARSE_2x2"})
writer("evidence_trace_top10.csv",lines,list(lines[0]))
summary={
 "stage":"3","dataset":"frozen v2.3, 84 workflows","factors":len(factors),
 "strategies":len(strategies),"tested_pairs":len(out),
 "wald_eligible_min_5_cells":len(valid),"wald_abstained_sparse":len(out)-len(valid),
 "wald_fdr_q_below_0_05":sum(x["eligible"] and x["fdr_q"]<=.05 for x in out),
 "ranked_case_occurrences":100,
 "evidence_trace_rows":len(lines),
 "case_perspective_links":sum(len(x["runtime_perspective_ids"].split("|")) for x in lines),
 "source_referenced_rows":sum(bool(x["case_source_url"]) for x in lines),
 "reference_technique":"Offline 2x2 univariate logOR Wald, BH adjustment across eligible tests, exclude cell min<5",
 "causal_evidence":False,
 "warn":["F11/F10 were developed on same corpus; derived association not independently proven",
 "Sparse cell abstentions must not be scored as zero effects",
 "The source is company/vendor-reported case studies, not randomized trial",
 "A factor×strategy statistical association does not independently establish recommendation validity",
 "This Stage3 annotation does not alter precomputed retrieval rankings"]}
(OUT/"manifest.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
(OUT/"RESULT.md").write_text(
 "# v2.3 Stage 3 — Factor and evidence tracing\n\n"
 "Actual factor/strategy pairs: "+str(len(out))+
 "; Wald-eligible (all 2x2 cells >=5): "+str(len(valid))+
 "; abstained: "+str(len(out)-len(valid))+
 "; BH-FDR q<=0.05: "+str(summary["wald_fdr_q_below_0_05"])+
 ".\n\nSource-traced Case×Factor×Strategy evidence rows: "+str(len(lines))+
 "; 100 top-10 retrieved case occurrences across ten Dev queries.\n\n"
 "**No causal inference** and no human-grounded strategy accuracy are claimed. "
 "When sparse, do not produce a Wald odds ratio. Stage 3 trace must not change retrieval ranks.\n",encoding="utf-8")
print("PASS Stage3",summary,flush=True)
