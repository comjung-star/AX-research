#!/usr/bin/env python3
"""v2.3 Stage 1. Actual retrieval against frozen cases, 2520 AI-only Dev qrels.
Historical v1 rankings are never treated as v2.3 experiments.
"""
import csv,json,hashlib,platform,sys
from pathlib import Path
from collections import defaultdict
import numpy as np
from pydantic import BaseModel,Field
from sentence_transformers import SentenceTransformer
from kiwipiepy import Kiwi
from rank_bm25 import BM25Okapi
from openai import OpenAI

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"data/v2_3"
OUT=ROOT/"experiments/v23_stages/stage1"
OUT.mkdir(parents=True,exist_ok=True)
CASES=json.loads((BASE/"main_cases_v2_3.json").read_text(encoding="utf-8"))["cases"]
QUERIES=json.loads((BASE/"dev_query_candidates_v2_3.json").read_text(encoding="utf-8"))["queries"]
with (BASE/"ground_truth/silver_dev_qrels_2520.csv").open(encoding="utf-8",newline="") as f:QRELS=list(csv.DictReader(f))
IDS=[x["case_id"] for x in CASES]
I={c:i for i,c in enumerate(IDS)}
CID={c["case_id"]:c for c in CASES}
QID={q["query_id"]:q for q in QUERIES}
assert len(IDS)==len(set(IDS))==84 and len(QUERIES)==10 and len(QRELS)==2520
assert all(x["human_approved"]=="FALSE" for x in QRELS)
assert all(x["status"]=="FROZEN_SOURCE_QA_NOT_GROUND_TRUTH" for x in (c["v23_source_review"] for c in CASES))
PKEY={(r["query_id"],r["perspective_id"]):set() for r in QRELS}
for r in QRELS:
 if int(r["relevance_0_4"])>=3:PKEY[(r["query_id"],r["perspective_id"])].add(r["case_id"])
QGOLD={q:set().union(*(v for (k,p),v in PKEY.items() if k==q)) for q in QID}
STRAT={q:set().union(*(set(CID[c]["strategy_labels"]) for c in case_ids)) if case_ids else set() for q,case_ids in QGOLD.items()}
DOC=["Problem: "+c["problem"]+"\nTask: "+c["task"]+"\nContext: "+c["context"] for c in CASES]
KW=Kiwi()
def tokenize(s):return [tok.form.lower() for tok in KW.tokenize(s) if tok.tag not in ("SF","SP","SS","SE","SO","SW")]
bm=BM25Okapi([tokenize(x) for x in DOC])
ENC=SentenceTransformer("BAAI/bge-m3",device="cpu")
EMBS={}
def emb(texts):return np.asarray(ENC.encode(texts,batch_size=8,normalize_embeddings=True,show_progress_bar=False),dtype=np.float32)
V=emb([c["problem"] for c in CASES]),emb([c["task"] for c in CASES]),emb([c["context"] for c in CASES])
D=emb(DOC)
np.savez_compressed(OUT/"case_embeddings.npz",document=D,problem=V[0],task=V[1],context=V[2])

class Perspective(BaseModel):
 title:str
 description:str
class Perspectives(BaseModel):
 perspectives:list[Perspective]=Field(min_length=2,max_length=5)
class GPTSelection(BaseModel):
 case_ids:list[str]

SYS_P="You are a business-problem analyzer, not a relevance judge. Given one enterprise business problem, independently produce 2 to 5 meaningfully distinct problem perspectives for case search. Output problem perspectives only, no technologies/solutions/company names. Do not infer specific cases."
SYS_G="Act as GPT-only baseline. Based solely on the user's business problem and the provided case ID + Problem/Task/Context, rank up to 20 distinct most relevant case IDs. Do not use implementation, factors, strategies, outcomes, gold labels, other ranking methods or extra documents. Return only case IDs."
client=OpenAI(timeout=180,max_retries=1)
def ask(model,syst,user,format):
 res=client.responses.parse(model=model,input=[{"role":"system","content":syst},{"role":"user","content":user}],text_format=format,max_output_tokens=12000)
 if res.output_parsed is None:raise ValueError("LLM returned no parsed output")
 return res.output_parsed,res.id,res.model

def sort_scores(scores):
 return [IDS[i] for i in sorted(range(len(IDS)),key=lambda i:(-float(scores[i]),IDS[i]))]
def unique_balanced(branches,k=84):
 ranked=[];used=set()
 for j in range(84):
  for b in branches:
   if j<len(b) and b[j] not in used:
    ranked.append(b[j]);used.add(b[j])
    if len(ranked)>=k:return ranked
 return ranked
def metric(q,rank,k):
 xs=rank[:k];s=set(xs)
 positives=QGOLD[q];views=[v for (qid,pid),v in PKEY.items() if qid==q and v]
 coverage=sum(bool(s&v) for v in views)/len(views) if views else None
 sts=set().union(*(set(CID[c]["strategy_labels"]) for c in xs))
 return {"recall":len(s&positives)/len(positives) if positives else None,
 "perspective_coverage":coverage,"proxy_strategy_coverage":len(sts&STRAT[q])/len(STRAT[q]) if STRAT[q] else None,
 "retrieved_gold":len(s&positives),"gold_count":len(positives),"answerable_perspectives":len(views)}

results={}
metadata=[]
for q in QUERIES:
 qid=q["query_id"];query=q["business_problem_query"]
 pp,pid,pm=ask("gpt-6-luna",SYS_P,query,Perspectives)
 perspectives=[{"id":f"RP{i+1}","title":p.title,"description":p.description} for i,p in enumerate(pp.perspectives)]
 if not 2<=len(perspectives)<=5:raise ValueError("Number of runtime perspectives must be 2..5")
 case_context=[{"case_id":c["case_id"],"problem":c["problem"],"task":c["task"],"context":c["context"]} for c in CASES]
 gp=[]
 gpt_resp=[]
 for repeat in range(1,4):
  x,rid,model=ask("gpt-6-luna",SYS_G,json.dumps({"query":query,"cases":case_context},ensure_ascii=False),GPTSelection)
  # Reject hallucinated or duplicate IDs; do not manufacture missing results.
  # Preserve model hallucinations in audit. Accept ONLY exact IDs or an
  # unambiguous trailing _01 formatting suffix if the exact base ID exists.
  valid=[];unrecognized=[];coerced=[]
  for raw_id in x.case_ids:
   if raw_id in I:valid.append(raw_id)
   elif raw_id.endswith("_01") and raw_id[:-3] in I:
    valid.append(raw_id[:-3]);coerced.append({"returned":raw_id,"normalized_to":raw_id[:-3]})
   else:unrecognized.append(raw_id)
  unique=list(dict.fromkeys(valid))
  if len(unique)<5:raise ValueError(f"GPT-only returned too few valid case IDs: {len(unique)}, hallucinations: {unrecognized}")
  gp.append(unique)
  gpt_resp.append({"pass_id":repeat,"response_id":rid,"model":model,"n":len(unique),
    "unrecognized_case_ids":unrecognized,"normalized_unambiguous_ids":coerced})
 qvec=emb([query])[0];qsparse=sort_scores(bm.get_scores(tokenize(query)));qdense=sort_scores(D@qvec)
 allp=[p["title"]+"; "+p["description"] for p in perspectives]
 pv=emb(allp)
 pBM=[sort_scores(bm.get_scores(tokenize(t))) for t in allp]
 pD=[sort_scores(D@v) for v in pv]
 choices={"single_bm25":qsparse,"single_dense":qdense,"gpt_only_pass1":gp[0],"gpt_only_pass2":gp[1],"gpt_only_pass3":gp[2],
  "mp_bm25":unique_balanced(pBM),"mp_dense":unique_balanced(pD)}
 results[qid]={"query":query,"perspectives":perspectives,"generated_perspective_response_id":pid,
  "gpt_only_responses":gpt_resp,"rankings":choices,"branch_rankings":{"bm25":pBM,"dense":pD}}
 metadata.append({"query_id":qid,"runtime_perspective_count":len(perspectives),"gold_union":len(QGOLD[qid]),"gpt_only_response_ids":[a["response_id"] for a in gpt_resp]})
 print("STAGE1",qid,"perspectives",len(perspectives),"positives",len(QGOLD[qid]),flush=True)

(OUT/"rankings.json").write_text(json.dumps(results,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
detail=[]
for q,rr in results.items():
 for method,rank in rr["rankings"].items():
  for k in (5,10,20):
   v=metric(q,rank,k)
   detail.append({"query_id":q,"method":method,"k":k,**v})
def dump_csv(path,rows):
 with path.open("w",encoding="utf-8",newline="") as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
dump_csv(OUT/"per_query_metrics.csv",detail)
summary=[]
for method in results[next(iter(results))]["rankings"]:
 for k in (5,10,20):
  rs=[r for r in detail if r["method"]==method and r["k"]==k]
  summary.append({"method":method,"k":k,
   **{"mean_"+a:round(float(np.mean([r[a] for r in rs if r[a] is not None])),6) for a in ("recall","perspective_coverage","proxy_strategy_coverage")}})
dump_csv(OUT/"summary.csv",summary)
metadata_info={"stage":"1","dataset":"v2.3.0 frozen 84","reference":"v2.3 AI-only 2520 Silver",
 "retrieval_input_fields":["problem","task","context"],"system_model":"gpt-6-luna","embedding_model":"BAAI/bge-m3",
 "dev_only":True,"validation":"NO_HUMAN_GOLD","temperature":"API default","k":[5,10,20],
 "replay_reference_perspectives_to_runtime":False,"generated_perspectives":metadata,"python":platform.python_version(),
 "notes":["GPT-only results are independent 3 passes","Strategy coverage denominator derived from Silver-positive cases; not independent strategy Gold",
 "Empty relevance perspectives excluded from coverage denominator","Dataset source freeze unchanged"]}
(OUT/"manifest.json").write_text(json.dumps(metadata_info,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
qtop=[r for r in summary if r["k"]==10]
s="\n".join([f"| {v['method']} | {v['mean_recall']:.3f} | {v['mean_perspective_coverage']:.3f} | {v['mean_proxy_strategy_coverage']:.3f} |" for v in qtop])
(OUT/"RESULT.md").write_text("# v2.3 Stage 1 — Actual Dev Experiment\n\n"
 "**Reference: AI-only Silver ratings, NOT human-validated Gold.** Dev result is exploratory and not held-out.\n\n"
 "Search document uses Problem, Task and Context ONLY. Runtime perspectives generated independently from query; GPT-only rerun 3 times on 84 cases.\n\n"
 "| Method | Recall@10 | Perspective Coverage@10 | Derived Strategy Proxy@10 |\n|---|---:|---:|---:|\n"+s+
 "\n\nInterpret improvement jointly with coverage and unique cases; do not claim statistical superiority from 10 Dev queries.\n",encoding="utf-8")
print("PASS Stage1 results",len(summary),"comparison cells",flush=True)
