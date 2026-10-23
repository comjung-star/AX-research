#!/usr/bin/env python3
"""Stage 4 v2.3: evidence fusion and source-grounded LLM strategy generation.
Evaluates DEV AI-Silver-derived strategy references, not independent Gold.
"""
import csv,json,math,os,time,hashlib
from collections import Counter,defaultdict
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
from pydantic import BaseModel,Field
from openai import OpenAI
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/"data/v2_3"
IN=ROOT/"experiments/v23_dev/stage2";ST3=ROOT/"experiments/v23_dev/stage3"
OUT=ROOT/"experiments/v23_dev/stage4";OUT.mkdir(parents=True,exist_ok=True)
MODEL="gpt-6-luna"
def read(p):
 with open(p,encoding="utf-8",newline="") as f:return list(csv.DictReader(f))
def write(p,rs):
 assert rs
 with open(p,"w",encoding="utf-8",newline="") as f:
  w=csv.DictWriter(f,fieldnames=list(rs[0]));w.writeheader();w.writerows(rs)
cases=json.loads((BASE/"main_cases_v2_3.json").read_text(encoding="utf-8"))["cases"]
cmap={c["case_id"]:c for c in cases}
qs=json.loads((BASE/"dev_query_candidates_v2_3.json").read_text(encoding="utf-8"))["queries"]
qmap={q["query_id"]:q["business_problem_query"] for q in qs}
ranking=read(IN/"rankings_top20.csv")
w=read(ST3/"factor_strategy_wald_77_pairs.csv")
wald={(r["factor_id"],r["strategy_id"]):r for r in w}
silver=read(BASE/"ground_truth/silver_dev_qrels_2520.csv")
positive=defaultdict(set)
for r in silver:
 if int(r["relevance_0_4"])>=3:positive[r["query_id"]].add(r["case_id"])
sref={q:{s for cid in positive[q] for s in cmap[cid]["strategy_labels"]} for q in qmap}
assert len(cases)==84 and len(sref)==10
all_strategies={s for c in cases for s in c["strategy_labels"]}
group=defaultdict(list)
for r in ranking:
 if r["system"]=="stage2_4_same_pool_rrf" and int(r["rank"])<=10:
  group[(r["query_id"],int(r["run_id"]))].append(r)
assert len(group)==30
SYSTEM="""You are reporting enterprise AX strategy recommendations using ONLY the retrieved case evidence given.
Choose up to 3 valid strategy IDs from the included cases. Every recommendation MUST cite evidence_case_ids among the retrieved cases that IMPLEMENT that strategy. Do not infer causal impact from Wald odds ratios. SPARSE_ABSTAIN is not evidence of effect. Describe tradeoffs and limits. If there is no applicable documented case abstain (empty array). Use the business query to judge relevance; do not invent performance, URLs, projects, or technology. Respond in Korean."""
class Rec(BaseModel):
 strategy_id:str
 evidence_case_ids:list[str]
 reason:str
class Answer(BaseModel):
 recommendations:list[Rec]=Field(default_factory=list)
 limits:str
def score_candidates(items):
 base=defaultdict(float);fused=defaultdict(float);anchors=defaultdict(set);sources=defaultdict(set)
 for rank,cid in enumerate(items,1):
  c=cmap[cid]
  for s in c["strategy_labels"]:
   weight=1/math.log2(rank+1)
   base[s]+=weight
   sources[s].add(cid)
   for f in c["factor_labels"]:
    anchors[s].add(f)
    r=wald[(f,s)]
    # Sparse-safe: ONLY statistically reportable positive association adds evidence.
    # Both q-values and uncertainty are used to avoid spurious boost.
    if r["status"]=="WALD_DESCRIPTIVE" and r["odds_ratio"] and float(r["odds_ratio"])>1 and r["bh_q_all_pairs"] and float(r["bh_q_all_pairs"])<0.05:
     fused[s]+=weight*0.35
 for s in base:fused[s]+=base[s]
 return (sorted(base,key=lambda s:(-base[s],s)),
         sorted(fused,key=lambda s:(-fused[s],s)),anchors,sources,base,fused)
def evidence(q,rep,ids,ranking_baseline,ranking_fused,anchors,sources):
 package=[]
 for rank,cid in enumerate(ids,1):
  c=cmap[cid]
  pairs=[]
  for f in c["factor_labels"]:
   for s in c["strategy_labels"]:
    r=wald[(f,s)]
    pairs.append(dict(factor_id=f,strategy_id=s,
      wald_status=r["status"],odds_ratio=r["odds_ratio"] if r["status"]=="WALD_DESCRIPTIVE" else None,
      bh_adjusted_p=r["bh_q_all_pairs"] if r["status"]=="WALD_DESCRIPTIVE" else None))
  package.append(dict(case_id=cid,rank=rank,organization=c["organization"],
   problem=c["problem"],task=c["task"],root_cause_factors=c["factor_labels"],
   implemented_strategies=c["strategy_labels"],
   factor_strategy_associations=pairs,source_url=c["source_url"]))
 return dict(query_id=q,run_id=rep,business_problem=qmap[q],
  source_grounded_cases=package,
  strategy_evidence_fusion_rank=ranking_fused[:3],
  source_corpus="AX v2.3 frozen 84 cases",gold_relevance_not_in_prompt=True)
inputs={}
for (q,rep),v in sorted(group.items()):
 ids=[x["case_id"] for x in sorted(v,key=lambda z:int(z["rank"]))]
 b,f,a,s,base,fused=score_candidates(ids)
 inputs[(q,rep)]=(ids,b,f,a,s,base,fused,evidence(q,rep,ids,b,f,a,s))
def generate(pair,item):
 q,rep=pair;ids,b,f,a,s,base,fused,inp=item
 if not os.getenv("OPENAI_API_KEY"):raise RuntimeError("Stage 4 requires real LLM API")
 client=OpenAI(timeout=180,max_retries=1)
 for attempt in range(3):
  try:
   response=client.responses.parse(model=MODEL,input=[
    {"role":"system","content":SYSTEM},
    {"role":"user","content":json.dumps(inp,ensure_ascii=False)}],
    text_format=Answer,max_output_tokens=4000)
   got=response.output_parsed
   assert got is not None and len(got.recommendations)<=3
   seen=set()
   for rec in got.recommendations:
    assert rec.strategy_id in all_strategies and rec.strategy_id not in seen
    seen.add(rec.strategy_id)
    assert rec.evidence_case_ids
    assert set(rec.evidence_case_ids)<=set(ids)
    assert all(rec.strategy_id in cmap[cid]["strategy_labels"] for cid in rec.evidence_case_ids)
    assert rec.reason.strip()
   return dict(query_id=q,run_id=rep,model_id=response.model,response_id=response.id,
    recommendations=[r.model_dump() for r in got.recommendations],limits=got.limits,
    prompt_hash=hashlib.sha256(SYSTEM.encode()).hexdigest(),valid=True)
  except Exception:
   if attempt==2:raise
   time.sleep(3*(attempt+1))
output={}
with ThreadPoolExecutor(max_workers=5) as pool:
 futures={pool.submit(generate,pair,item):pair for pair,item in inputs.items()}
 for future in as_completed(futures):
  v=future.result();output[(v["query_id"],v["run_id"])]=v
  print("Stage 4 grounded answer:",v["query_id"],v["run_id"],flush=True)
assert len(output)==30
def measure(pred,truth):
 p=set(pred);g=set(truth)
 return (len(p&g)/len(g) if g else None,
         len(p&g)/len(p) if p else None)
results=[];cards=[];traces=[]
for pair,item in inputs.items():
 q,rep=pair;ids,b,f,a,s,base,fused,inp=item
 ans=output[pair]
 strategies=[x["strategy_id"] for x in ans["recommendations"]]
 methods={"retrieved_case_frequency":b[:3],"wald_safe_evidence_fusion":f[:3],
          "evidence_grounded_llm":strategies}
 for name,ss in methods.items():
  recall,precision=measure(ss,sref[q])
  results.append(dict(stage=4,system=name,query_id=q,run_id=rep,
   recommended_count=len(ss),strategy_recall_at_3=recall,
   strategy_precision_at_3=precision,reference_strategy_count=len(sref[q]),
   reference_status="DEPENDENT_AI_SILVER_CASE_UNION_NOT_QUERY_GOLD"))
 for rr,rec in enumerate(ans["recommendations"],1):
  for cid in rec["evidence_case_ids"]:
   traces.append(dict(query_id=q,run_id=rep,recommendation_rank=rr,
    strategy_id=rec["strategy_id"],case_id=cid,
    source_url=cmap[cid]["source_url"],factor_ids="|".join(cmap[cid]["factor_labels"]),
    rationale=rec["reason"],trace_status="VALID_CASE_STRATEGY_LINK_NOT_CAUSAL"))
 cards.append(dict(query_id=q,run_id=rep,query_problem=qmap[q],
  chosen_strategies="|".join(strategies),
  evidence_json=json.dumps(ans["recommendations"],ensure_ascii=False),
  limits=ans["limits"],model_id=ans["model_id"],response_id=ans["response_id"],
  wald_eligible_pairs=sum(int(x["status"]=="WALD_DESCRIPTIVE") for x in w),
  status="DEV_RECOMMENDATION_NOT_CLINICALLY_OR_HUMAN_VALIDATED"))
write(OUT/"strategy_metrics_by_query.csv",results)
write(OUT/"final_strategy_recommendations.csv",cards)
write(OUT/"recommendation_case_evidence_trace.csv",traces)
(OUT/"full_llm_answers.json").write_text(json.dumps([output[key] for key in sorted(output)],ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
summary=[]
for method in sorted({r["system"] for r in results}):
 all=[r for r in results if r["system"]==method]
 summary.append(dict(system=method,n=len(all),
  strategy_recall_at_3_mean=sum(r["strategy_recall_at_3"] for r in all)/len(all),
  strategy_precision_at_3_mean=sum(r["strategy_precision_at_3"] for r in all)/len(all),
  status="DEV_AI_SILVER_DEPENDENT_STRATEGY_SET"))
write(OUT/"summary.csv",summary)
report=dict(stage="STAGE_4_REAL_EXECUTED",query_repetitions=len(group),
 evidence_grounded_llm_answers=len(cards),trace_records=len(traces),
 strategy_labels=len(all_strategies),methods=[x["system"] for x in summary],
 llm_model=MODEL, input_no_gold_labels=True,predefined_fusion_rule=True,
 pairs_wald_eligible=sum(r["status"]=="WALD_DESCRIPTIVE" for r in w),
 silent_wald_fill=False,
 metrics="DEV_ONLY_WITH_SILVER_DERIVED_NONINDEPENDENT_REFERENCE",
 final_test_completed=False,causal_claim=False)
(OUT/"manifest.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("STAGE4 COMPLETE",json.dumps(summary,ensure_ascii=False),flush=True)
