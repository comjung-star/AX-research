#!/usr/bin/env python3
"""Stage 1 on frozen v2.3: Kiwi BM25, BGE-M3, GPT-only, MP Sparse/Dense.
All relevance metrics are DEV AI-generated references (not human Gold).
"""
import csv, json, os, hashlib, platform, time, sys
from collections import defaultdict, OrderedDict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np
from ax_research.data import AXCase
from ax_research.llm.client import RQ1OpenAIClient
from ax_research.retrieval.bm25 import KiwiBM25Retriever
from ax_research.retrieval.dense import BGEM3DenseRetriever
from ax_research.selection import branch_balanced_unique

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"experiments/v23_dev/stage1"
CASES=json.loads((ROOT/"data/v2_3/main_cases_v2_3.json").read_text(encoding="utf-8"))["cases"]
QUERIES=json.loads((ROOT/"data/v2_3/dev_query_candidates_v2_3.json").read_text(encoding="utf-8"))["queries"]
GT=ROOT/"data/v2_3/ground_truth/silver_dev_qrels_2520.csv"
MODEL="gpt-6-luna"
KS=(5,10,20)
assert len(CASES)==84 and len(QUERIES)==10
assert os.getenv("OPENAI_API_KEY"),"Real OpenAI API secret required: cannot fabricate GPT experiment"

def csvread(p):
 with open(p,encoding="utf-8",newline="") as f:return list(csv.DictReader(f))
def csvwrite(p,rows):
 assert rows, str(p)
 with open(p,"w",encoding="utf-8",newline="") as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def rank(scores, ids):return [x for x,_ in sorted(zip(ids,scores),key=lambda z:(-float(z[1]),z[0]))]
def metrics(ids,q):
 positives={pid:{cid for cid,score in z.items() if score>=3} for pid,z in label[q].items()}
 union=set().union(*positives.values())
 active=[v for v in positives.values() if v]
 targets={s for cid in union for s in cindex[cid]["strategy_labels"]}
 result=[]
 for k in KS:
  top=set(ids[:k])
  got_strat={s for cid in top for s in cindex[cid]["strategy_labels"]}
  result.append(dict(recall=len(top&union)/len(union) if union else None,
    perspective_coverage=sum(bool(top&p) for p in active)/len(active) if active else None,
    strategy_coverage=len(got_strat&targets)/len(targets) if targets else None,
    relevant_count=len(union),answerable_views=len(active),empty_views=3-len(active),
    strategy_reference="SILVER_DERIVED_NOT_INDEPENDENT"))
 return result
OUT.mkdir(parents=True,exist_ok=True)
cindex={c["case_id"]:c for c in CASES}; ids=list(cindex)
label=defaultdict(lambda:defaultdict(dict))
for r in csvread(GT):
 assert r["provenance"]=="AI_THREE_PASS_MEDIAN_NOT_HUMAN_GOLD"
 label[r["query_id"]][r["perspective_id"]][r["case_id"]]=int(r["relevance_0_4"])
assert sum(len(c) for q in label.values() for c in q.values())==2520
cases=[AXCase(c["case_id"],c["problem"],c["task"],c["context"],tuple(c["strategy_labels"])) for c in CASES]
bm=KiwiBM25Retriever(cases)
dense=BGEM3DenseRetriever(cases,device="cpu")
embed=dense._model
ids=dense._case_ids
documents=dense._case_embeddings
views={v:embed.encode([getattr(c,v) for c in cases],
 normalize_embeddings=True,convert_to_numpy=True,show_progress_bar=False).astype(np.float32)
 for v in ("business_problem","ax_target_task","business_context")}
qt=[q["business_problem_query"] for q in QUERIES]
qe=embed.encode(qt,normalize_embeddings=True,convert_to_numpy=True,show_progress_bar=False).astype(np.float32)
llm=RQ1OpenAIClient(model=MODEL,temperature=None,perspective_min=2,perspective_max=5)
def call_one(q,run):
 for attempt in range(3):
  try:
   perspectives=llm.generate_perspectives(q["business_problem_query"])
   assert 2<=len(perspectives)<=5
   assert len(set(p.id for p in perspectives))==len(perspectives)
   gpt=llm.gpt_only_rank(q["business_problem_query"],cases,top_n=20)
   assert len({x.case_id for x in gpt.ranked_cases})==20
   return (q["query_id"],run,perspectives,gpt)
  except Exception as e:
   if attempt==2:raise
   time.sleep(3*(attempt+1))
tasks=[(q,r) for q in QUERIES for r in (1,2,3)]
outputs={}
with ThreadPoolExecutor(max_workers=5) as pool:
 futures={pool.submit(call_one,q,r):(q["query_id"],r) for q,r in tasks}
 for fut in as_completed(futures):
  v=fut.result()
  outputs[(v[0],v[1])]=v
  print("Stage1 LLM finished",v[0],v[1],flush=True)
assert len(outputs)==30
# Encode runtime-generated perspectives ONLY, never the fixed evaluation reference views.
br_keys=[];br_defs=[]
for q in QUERIES:
 for rep in (1,2,3):
  for p in outputs[(q["query_id"],rep)][2]:
   key=(q["query_id"],rep,p.id)
   br_keys.append(key);br_defs.append(dict(query_id=key[0],run_id=key[1],perspective_id=p.id,
     perspective_title=p.title,perspective_description=p.description,branch_query_text=p.title))
assert len(br_keys)==len(set(br_keys))
branch_e=embed.encode([b["branch_query_text"] for b in br_defs],
 normalize_embeddings=True,convert_to_numpy=True,show_progress_bar=False).astype(np.float32)
np.savez_compressed(OUT/"fixed_bge_m3_embeddings.npz",
 case_ids=np.asarray(ids),query_ids=np.asarray([q["query_id"] for q in QUERIES]),
 query_embeddings=qe,document_embeddings=documents,
 problem_embeddings=views["business_problem"],task_embeddings=views["ax_target_task"],
 context_embeddings=views["business_context"],
 branch_embeddings=branch_e,
 branch_keys=np.asarray([f"{a}|{b}|{c}" for a,b,c in br_keys]))
(OUT/"generated_runtime_perspectives.json").write_text(json.dumps(br_defs,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
rankings=[];ms=[];branch_rows=[]
def record(system,q,run,ordered):
 assert len(set(ordered))==len(ordered)
 for rk,cid in enumerate(ordered[:20],1):
  rankings.append(dict(stage="1",system=system,query_id=q,run_id=run,rank=rk,case_id=cid))
 for k,met in zip(KS,metrics(ordered,q)):
  ms.append(dict(stage="1",system=system,query_id=q,run_id=run,k=k,**met))
for i,q in enumerate(QUERIES):
 qid=q["query_id"];query=q["business_problem_query"]
 single_bm=[x.case_id for x in bm.search(query)]
 single_dense=rank(documents@qe[i],ids)
 record("single_bm25",qid,0,single_bm)
 record("single_dense_bge_m3",qid,0,single_dense)
 for rep in (1,2,3):
  ranked_gpt=[x.case_id for x in outputs[(qid,rep)][3].ranked_cases]
  record("gpt_only",qid,rep,ranked_gpt)
  dranks=OrderedDict();sranks=OrderedDict()
  for idx,key in enumerate(br_keys):
   if key[0]!=qid or key[1]!=rep:continue
   brtxt=br_defs[idx]["branch_query_text"]
   ds=documents@branch_e[idx]
   dids=rank(ds,ids)
   branks=bm.search(brtxt)
   sids=[v.case_id for v in branks]
   dranks[key[2]]=dids;sranks[key[2]]=sids
   for local,cid in enumerate(dids,1):
    branch_rows.append(dict(query_id=qid,run_id=rep,perspective_id=key[2],
     retrieval="dense",local_rank=local,case_id=cid,score=float(ds[ids.index(cid)])))
   for local,x in enumerate(branks,1):
    branch_rows.append(dict(query_id=qid,run_id=rep,perspective_id=key[2],
     retrieval="bm25",local_rank=local,case_id=x.case_id,score=float(x.score)))
  record("mp_dense_bge_m3",qid,rep,[cid for _,cid in branch_balanced_unique(dranks,84)])
  record("mp_bm25",qid,rep,[cid for _,cid in branch_balanced_unique(sranks,84)])
csvwrite(OUT/"rankings_top20.csv",rankings)
csvwrite(OUT/"metrics_by_query.csv",ms)
csvwrite(OUT/"branch_rankings.csv",branch_rows)
summary=[]
for system in sorted(set(r["system"] for r in ms)):
 for k in KS:
  arr=[r for r in ms if r["system"]==system and r["k"]==k]
  summary.append(dict(system=system,k=k,observations=len(arr),n_queries=10,
   recall_mean=round(float(np.mean([r["recall"] for r in arr if r["recall"] is not None])),4),
   perspective_coverage_mean=round(float(np.mean([r["perspective_coverage"] for r in arr if r["perspective_coverage"] is not None])),4),
   strategy_coverage_mean=round(float(np.mean([r["strategy_coverage"] for r in arr if r["strategy_coverage"] is not None])),4)))
csvwrite(OUT/"summary.csv",summary)
manifest=dict(stage="STAGE_1_REAL_EXECUTED",corpus_version="v2.3.0",corpus_cases=84,
 qrels="AI_SILVER_NOT_HUMAN_GT",dense="BAAI/bge-m3",llm=MODEL,repeats=3,
 runtime_perspectives=len(br_defs),reference_perspectives_not_in_runtime=True,
 solution_not_in_retrieval=True,metric_k=KS,models=list(sorted(set(r["system"] for r in ms))),
 output_rankings=len(rankings),output_metrics=len(ms),
 python=platform.python_version(),silver_only_dev_no_test=True)
(OUT/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
assert len([x for x in ms if x["k"]==10])==10*2+30*3
print("STAGE1 COMPLETE",json.dumps(summary,ensure_ascii=False),flush=True)
