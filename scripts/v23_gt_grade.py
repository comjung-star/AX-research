#!/usr/bin/env python3
"""Three independent blind AI DEV-relevance passes on frozen v2.3.0; SILVER ONLY.

Never merge scores with Gold, never call this human review, never expose previous
pass results to the LLM, and never send solution/outcome/factor/strategy fields.
"""
import argparse
import csv
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from collections import Counter

import v21_provisional_ai_ground_truth as v21

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data/v2_3"
SCORE_FIELDS=[
 "query_id","perspective_id","case_id","pass_id","provisional_relevance_0_4",
 "evidence_reason","status","model_id","response_id",
 "prompt_sha256","input_sha256","timestamp_utc"
]

def load_input():
 data=json.loads((DATA/"main_cases_v2_3.json").read_text(encoding="utf-8"))
 query_doc=json.loads((DATA/"dev_query_candidates_v2_3.json").read_text(encoding="utf-8"))
 assert data["dataset_release"]=="2.3.0" and data["status"]=="FROZEN_SOURCE_ADJUDICATED_NOT_GROUND_TRUTH" and len(data["cases"])==84
 assert len(query_doc["queries"])==10
 assert len({c["case_id"] for c in data["cases"]})==84
 return data["cases"], query_doc["queries"]

def run(args):
 if not os.getenv("OPENAI_API_KEY", "").strip():
  raise RuntimeError("OPENAI_API_KEY missing; cannot claim an AI repetition happened")
 import openai
 cases,queries=load_input()
 matched=[q for q in queries if q["query_id"]==args.query_id]
 if len(matched)!=1 or args.pass_id not in (1,2,3):
  raise ValueError("Unknown query or repetition")
 q=matched[0]
 out=Path(args.output_dir)
 out.mkdir(parents=True,exist_ok=True)
 client=openai.OpenAI(timeout=180,max_retries=1)
 collected=[]
 audit=[]
 for lo in range(0,len(cases),args.chunk_size):
  batch=cases[lo:lo+args.chunk_size]
  raw,response,parsed=v21.grade_batch(
   client,args.model,q,batch,max_attempts=args.max_attempts,
   output_tokens=args.output_tokens
  )
  stamp=datetime.now(timezone.utc).isoformat()
  by_key={(x.perspective_id,x.case_id):x for x in parsed.rows}
  rows=[]
  for p in q["draft_perspectives"]:
   for c in batch:
    x=by_key[(p["id"],c["case_id"])]
    rows.append(dict(
     query_id=q["query_id"],perspective_id=p["id"],case_id=c["case_id"],
     pass_id=args.pass_id,provisional_relevance_0_4=x.relevance,
     evidence_reason=x.reason.strip(),status="V23_AI_BLIND_DRAFT_NOT_HUMAN_GOLD",
     model_id=response.model,response_id=response.id,
     prompt_sha256=v21.sha_text(v21.SYSTEM),
     input_sha256=v21.sha_text(raw),timestamp_utc=stamp
    ))
  collected.extend(rows)
  raw_path=out/"raw_batches"/f"{q['query_id']}_p{args.pass_id}_cases_{lo:03d}.json"
  raw_path.parent.mkdir(parents=True,exist_ok=True)
  raw_path.write_text(json.dumps({
   "query_id":q["query_id"],"pass_id":args.pass_id,
   "first_case":lo,"model_id":response.model,"response_id":response.id,
   "input_problem_only":json.loads(raw),
   "parsed_provisional_labels":parsed.model_dump()
  },ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
  audit.append({"first_case":lo,"size":len(batch),"response_id":response.id,
                "input_sha256":v21.sha_text(raw)})
  print(f"v2.3 query={q['query_id']} pass={args.pass_id} case {lo+1}-{lo+len(batch)}",flush=True)
 assert len(collected)==252, f"Expected 84*3 judgments per query/pass, got {len(collected)}"
 unique={(x["perspective_id"],x["case_id"]) for x in collected}
 assert len(unique)==252
 with (out/"ratings.csv").open("w",encoding="utf-8",newline="") as f:
  w=csv.DictWriter(f,fieldnames=SCORE_FIELDS);w.writeheader();w.writerows(collected)
 m={"status":"COMPLETE_SINGLE_BLIND_V23_AI_DRAFT_PASS","corpus":"2.2.0",
    "query_id":q["query_id"],"pass_id":args.pass_id,"model_requested":args.model,
    "model_ids":sorted({x["model_id"] for x in collected}),
    "cases":84,"perspectives":3,"judgments":len(collected),
    "prompt_sha256":v21.sha_text(v21.SYSTEM),
    "corpus_git_blob":"1705888f3338b219d3715fe4422641865c3075e2",
    "human_gt_count":0,"previous_scores_supplied_to_model":False,
    "batch_responses":audit,
    "score_histogram":dict(Counter(str(x["provisional_relevance_0_4"]) for x in collected))}
 (out/"manifest.json").write_text(json.dumps(m,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print("COMPLETE AI REPEAT PASS",q["query_id"],args.pass_id,len(collected),flush=True)

if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--query-id",required=True)
 p.add_argument("--pass-id",required=True,type=int)
 p.add_argument("--model",default="gpt-6-luna")
 p.add_argument("--chunk-size",type=int,default=12)
 p.add_argument("--max-attempts",type=int,default=3)
 p.add_argument("--output-tokens",type=int,default=16000)
 p.add_argument("--output-dir",required=True)
 args=p.parse_args()
 if args.chunk_size!=12:
  raise ValueError("Chunk size fixed at 12 for pass-to-pass comparability")
 run(args)
