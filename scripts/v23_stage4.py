#!/usr/bin/env python3
"""Stage 4: preselected equal-view retrieval + evidence fusion + real LLM
recommendation, measured against v2.3 Dev AI-only *derived* strategy proxy.
Do NOT call these human/held-out recommendation accuracy results.
"""
import csv,json,math
from collections import defaultdict
from pathlib import Path
from openai import OpenAI
from pydantic import BaseModel,Field

ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/"data/v2_3"
TOP=ROOT/"experiments/v23_stages";OUT=TOP/"stage4";OUT.mkdir(parents=True,exist_ok=True)
CASES=json.loads((BASE/"main_cases_v2_3.json").read_text(encoding="utf-8"))["cases"]
QUERIES=json.loads((BASE/"dev_query_candidates_v2_3.json").read_text(encoding="utf-8"))["queries"]
S1=json.loads((TOP/"stage1/rankings.json").read_text(encoding="utf-8"))
S2=json.loads((TOP/"stage2/final_rankings.json").read_text(encoding="utf-8"))
C={x["case_id"]:x for x in CASES}
with (BASE/"ground_truth/silver_dev_qrels_2520.csv").open(encoding="utf-8",newline="") as f:QRELS=list(csv.DictReader(f))
with (TOP/"stage3/wald_pairs.csv").open(encoding="utf-8",newline="") as f:WALD=list(csv.DictReader(f))
W={(r["factor_id"],r["strategy_id"]):r for r in WALD}
STRAT=sorted({s for x in CASES for s in x["strategy_labels"]})
DEF={}
with (BASE/"strategy_taxonomy_v2_3.csv").open(encoding="utf-8",newline="") as f:
 for row in csv.DictReader(f):DEF[row["strategy_id"]]=row["definition"]
P=defaultdict(set)
for r in QRELS:
 if int(r["relevance_0_4"])>=3:P[r["query_id"]].add(r["case_id"])
G={q["query_id"]:set().union(*(set(C[c]["strategy_labels"]) for c in P[q["query_id"]])) if P[q["query_id"]] else set() for q in QUERIES}
client=OpenAI(timeout=180,max_retries=1)
class Recommendation(BaseModel):
 strategy_id:str
 evidence_case_ids:list[str]
 rationale:str
class RecResponse(BaseModel):
 recommendations:list[Recommendation]=Field(min_length=1,max_length=5)
class BaseResponse(BaseModel):
 strategy_ids:list[str]=Field(min_length=1,max_length=5)

def ask(sys_,user,fmt):
 r=client.responses.parse(model="gpt-6-luna",
   input=[{"role":"system","content":sys_},{"role":"user","content":json.dumps(user,ensure_ascii=False)}],
   text_format=fmt,max_output_tokens=15000)
 if r.output_parsed is None:raise ValueError("LLM returned no parsed result")
 return r.output_parsed,r.id,r.model
def rank_votes(ids):
 totals=defaultdict(float);support=defaultdict(list)
 for pos,cid in enumerate(ids[:10],1):
  for s in C[cid]["strategy_labels"]:
   totals[s]+=1/math.log2(pos+1)
   support[s].append(cid)
 return sorted(totals,key=lambda s:(-totals[s],s)),totals,support
def rank_wald(ids):
 totals=defaultdict(float);detail=defaultdict(list)
 for pos,cid in enumerate(ids[:10],1):
  c=C[cid]
  for st in c["strategy_labels"]:
   base=1/math.log2(pos+1)
   additive=0.0
   for factor in c["factor_labels"]:
    w=W[(factor,st)]
    eligible=w["eligible"]=="1"
    significant=(eligible and w["fdr_q"] and float(w["fdr_q"])<=.05)
    # Association weight small and bounded; non-significant link adds NO statistical evidence.
    factor_gain=.1*max(-1.0,min(1.0,float(w["log_odds_ratio"]))) if significant else 0.0
    additive+=factor_gain
    detail[st].append({"case_id":cid,"factor_id":factor,
       "wald_supported":significant,"wald_fdr_q":w["fdr_q"] if eligible else "",
       "association_gain":factor_gain})
   totals[st]+=base*(1+additive)
 return sorted(totals,key=lambda s:(-totals[s],s)),totals,detail
def evaluate(pred,truth,n):
 p=pred[:n];return {"coverage":len(set(p)&truth)/len(truth) if truth else None,
 "precision":len(set(p)&truth)/len(p) if p else None,"hits":len(set(p)&truth)}

rows=[];recs={};issues=[]
sys_g="""You are the final Evidence-grounded AX business strategy recommendation head, not a source of new factual claims.
Based ONLY on business question, supplied real-case problem/task/context, audited Factor and Strategy labels and correctly marked NONCAUSAL Wald associations,
recommend 1-5 strategy IDs. For each strategy cite 1-3 exact case IDs that actually have that strategy label. Explain business relevance.
Do not invent factors, deployment details, benefits or new references. If the evidence is weak, explicitly state uncertainty. Never interpret Wald correlations as cause."""
sys_base="You are an enterprise AX strategy baseline with no retrieved cases. Recommend up to five strategy IDs from the given taxonomy to address the user business problem. Do not claim you have evidence of particular real deployments."
for q in QUERIES:
 qid=q["query_id"];query=q["business_problem_query"]
 selected=S2[qid]["stage2_1_equal_multiview"][:10] # PRE-REGISTERED, NOT chosen by Dev result
 assert len(selected)==10 and len(set(selected))==10
 vote,vt,vs=rank_votes(selected)
 fusion,ft,details=rank_wald(selected)
 cases_for_llm=[]
 for cid in selected:
  c=C[cid]
  cases_for_llm.append({"case_id":cid,"problem":c["problem"],"task":c["task"],
    "context":c["context"],"factors":c["factor_labels"],
    "documented_strategies":c["strategy_labels"],
    "official_source":c["source_url"]})
 llm_prompt={"query_id":qid,"business_problem":query,
  "authorized_strategies":DEF,"cases":cases_for_llm,
  "evidence_fusion_ranking":fusion[:5],
  "statistical_cautions":{"valid_wald_pairs":sum(w["eligible"]=="1" for w in WALD),
    "note":"All factor/strategy statistical associations are observational; do not infer causality"}}
 answer,rid,actual_model=ask(sys_g,llm_prompt,RecResponse)
 available=set().union(*(set(C[c]["strategy_labels"]) for c in selected))
 checked=[];rejected=[]
 for item in answer.recommendations:
  witnesses=list(dict.fromkeys(item.evidence_case_ids))
  if item.strategy_id not in STRAT or item.strategy_id not in available:
   rejected.append({"strategy":item.strategy_id,"reason":"NOT_SUPPORTED_BY_RETRIEVED_CASE_STRATEGY"});continue
  if not witnesses or any(cid not in selected or item.strategy_id not in C[cid]["strategy_labels"] for cid in witnesses):
   rejected.append({"strategy":item.strategy_id,"reason":"NO_VALID_SUPPORTING_SOURCE_CASE"});continue
  if item.strategy_id not in {x["strategy_id"] for x in checked}:
   checked.append({"strategy_id":item.strategy_id,"evidence_case_ids":witnesses,
    "rationale":item.rationale,
    "source_urls":[C[cid]["source_url"] for cid in witnesses]})
 if not checked:raise ValueError("No fact-grounded recommendation for "+qid)
 zeroshot,bid,bmodel=ask(sys_base,{"query":query,"strategy_taxonomy":DEF},BaseResponse)
 zs=list(dict.fromkeys(s for s in zeroshot.strategy_ids if s in STRAT))
 if not zs:raise ValueError("GPT-only baseline did not return valid strategy")
 methods={"GPT_only_zero_shot":zs,"retrieved_case_vote":vote,"Wald_evidence_fusion":fusion,
  "LLM_grounded_recommendation":[c["strategy_id"] for c in checked]}
 truth=G[qid]
 for name,stlist in methods.items():
  for k in (3,5):
   rows.append({"query_id":qid,"method":name,"k":k,
    "positive_case_count":len(P[qid]),"proxy_gold_strategy_count":len(truth),
    **{a:b for a,b in evaluate(stlist,truth,k).items()}})
 recs[qid]={"query":query,"preselected_case_ranking":selected,
  "reference_strategy_proxy":sorted(truth),"retrieved_case_vote":vote,
  "observational_wald_fusion":fusion,
  "llm_source_grounded_response_id":rid,
  "gpt_only_baseline_response_id":bid,
  "llm_source_grounded_recommendations":checked,
  "rejected_unfaithful_llm_recommendations":rejected,
  "gpt_only_zero_shot":zs}
 print("STAGE4",qid,"witnessed",len(checked),"invalid",len(rejected),flush=True)

with (OUT/"recommendations.json").open("w",encoding="utf-8") as f:json.dump(recs,f,ensure_ascii=False,indent=2)
def save(name,rows):
 with (OUT/name).open("w",encoding="utf-8",newline="") as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
save("per_query_metrics.csv",rows)
summary=[]
for method in ("GPT_only_zero_shot","retrieved_case_vote","Wald_evidence_fusion","LLM_grounded_recommendation"):
 for k in (3,5):
  rr=[r for r in rows if r["method"]==method and r["k"]==k]
  summary.append({"method":method,"k":k,
   "mean_proxy_strategy_coverage":round(sum(r["coverage"] for r in rr)/len(rr),6),
   "mean_proxy_strategy_precision":round(sum(r["precision"] for r in rr)/len(rr),6)})
save("summary.csv",summary)
manifest={"stage":4,"dataset":"frozen v2.3 84 cases","ground_truth_status":"AI-Silver-derived strategy proxy, NOT independent human Gold",
 "precommitted_retrieval":"stage2_1_equal_multiview; no posthoc best-of-stage2 system selection",
 "methods":["GPT-only no cases","direct case weighted voting","Wald factor-strategy fusion","real LLM source-grounded recommendation"],
 "llm_model":"gpt-6-luna","LLM_generation_completed":len(recs)==10,
 "recommended_case_source_provenance_required":True,
 "factual_support_check":"Each recommended strategy must be a label of at least one cited actually retrieved frozen case.",
 "independent_strategy_gold":False,"observational_wald_only":True,
 "frozen_retrieval_results_modified":False,"source_case_data_modified":False,
 "limitations":["Strategies in proxy denominator were derived from positive cases in same 84-case corpus.",
 "A retrieved case can count as both source and evaluation gold via its strategy label; this is not an independent recommendation test.",
 "The LLM explanation has programmatic witness-id checks, not human factual quality rating.",
 "No Held-out test or human-Gold validated claims are allowed."]}
(OUT/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
table="\n".join(f"| {r['method']} | {r['mean_proxy_strategy_coverage']:.3f} | {r['mean_proxy_strategy_precision']:.3f} |" for r in summary if r["k"]==5)
(OUT/"RESULT.md").write_text("# v2.3 Stage 4 — Evidence Fusion / LLM Recommendation actual Dev experiment\n\n"
 "Ten Dev business problems, ten source-anchored LLM recommendation calls, independent GPT-only strategy baseline.\n\n"
 "| Method | Derived Strategy Coverage@5 | Derived Strategy Precision@5 |\n|---|---:|---:|\n"+table+
 "\n\nThe reference strategies are **derived from AI-Silver-positive case annotations**, not independently adjudicated Gold. This is a feasibility/ablation diagnostic only, not proof of real-world recommendation accuracy. "
 "LLM case witness IDs and strategy availability programmatically enforced. Wald associations are NONCAUSAL and sparse cells abstain.\n",encoding="utf-8")
print("PASS Stage4",len(recs),"Dev queries completed",flush=True)
