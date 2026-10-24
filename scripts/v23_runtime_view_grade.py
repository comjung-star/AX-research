#!/usr/bin/env python3
"""Blind runtime-perspective x AX-case relevance judgments.

Two independently prompted model passes, no reference perspective or old scores.
Each job grades ONE query-run/pass (7 API requests at 12 cases each).
Never treat outputs as human adjudicated Gold.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel, Field

ROOT=Path(__file__).resolve().parents[1]
CASES_FILE=ROOT/"data/v2_3/main_cases_v2_3.json"
QUERIES_FILE=ROOT/"data/v2_3/dev_query_candidates_v2_3.json"
PERSPECTIVES_FILE=ROOT/"experiments/v23_dev/stage1/generated_runtime_perspectives.json"
OUTROOT=ROOT/"experiments/v23_runtime_perspective_qrels/raw_passes"

JUDGE_PROMPT="""You are grading BLIND **AI-Silver research relevance candidates**, never human ground truth.
Input contains one original business issue (context ONLY), multiple ACTUAL runtime-generated problem perspectives from this issue, and a batch of enterprise AX business cases with only Problem, Task and Context.

For EVERY generated perspective and case pair, independently grade whether the actual case problem, task and context meaningfully match THAT SPECIFIC runtime perspective. Do not grade the whole original question in place of each perspective. A case may match more than one perspective, and some perspectives may have zero strong matching cases.

Rubric:
4 = the case directly addresses the core operational problem/task AND its context strongly fits that perspective.
3 = strong match on core business problem or task, even when industry/context differs.
2 = partial overlap in some business activity but crucial workflow/issue is different.
1 = remote generic association only (words such as AI, data, customers, efficiency alone do not suffice).
0 = substantively unrelated business problem/task.

Return EXACTLY one entry for every perspective ID x case ID cross product. Score 0..4 and a short, specific KOREAN explanation anchored in case Problem or Task text (e.g. identify common workflow or mismatch). Do not invent case characteristics, do not force positives and do not use solutions, outcome, strategies, organizational fame, retrieval ranks, existing judgements, or other grader results.
Scores 3-4 require central problem/task alignment. Avoid grading relevance high merely because the same technology could theoretically solve both.
Do not refer to other model passes. No data was supplied from other judges."""

class JudgeRow(BaseModel):
    perspective_id:str
    case_id:str
    relevance:int=Field(ge=0,le=4)
    reason:str=Field(min_length=6)

class BatchLabels(BaseModel):
    rows:list[JudgeRow]

FIELDS=[
    "query_id","run_id","runtime_perspective_id","case_id","pass_id",
    "score_0_4","evidence_reason","judge_status","model_id","response_id",
    "prompt_sha256","input_sha256","timestamp_utc"
]


def sha(x:bytes|str)->str:
    return hashlib.sha256(x.encode("utf-8") if isinstance(x,str) else x).hexdigest()

def load_input(qid:str, run:int):
    cases=json.loads(CASES_FILE.read_text(encoding="utf-8"))["cases"]
    queries=json.loads(QUERIES_FILE.read_text(encoding="utf-8"))["queries"]
    dynamic=json.loads(PERSPECTIVES_FILE.read_text(encoding="utf-8"))
    assert len(cases)==84 and len({x["case_id"] for x in cases})==84
    assert len(queries)==10 and len(dynamic)==97
    match=[q for q in queries if q["query_id"]==qid]
    assert len(match)==1
    views=[p for p in dynamic if p["query_id"]==qid and int(p["run_id"])==run]
    assert 2<=len(views)<=5 and len({p["perspective_id"] for p in views})==len(views)
    return cases,match[0],views


def make_input(query:dict,views:list[dict],cases:list[dict])->str:
    # Security / scientific integrity: no implementation, outcome, factor, strategy,
    # draft evaluation perspectives, previous qrels or ranks may be supplied.
    payload={
        "query_id":query["query_id"],
        "original_business_problem_context_only":query["business_problem_query"],
        "generated_perspectives":[
            {"perspective_id":p["perspective_id"],
             "title":p["perspective_title"],
             "description":p["perspective_description"]}
            for p in views],
        "cases":[
            {"case_id":c["case_id"],"business_problem":c["problem"],
             "target_task":c["task"],"business_context":c["context"]}
            for c in cases],
    }
    return json.dumps(payload,ensure_ascii=False,separators=(",",":"))


def check_batch(rows:list[JudgeRow],views:list[dict], cases:list[dict]):
    expected={(p["perspective_id"],c["case_id"]) for p in views for c in cases}
    seen=[(r.perspective_id,r.case_id) for r in rows]
    if len(seen)!=len(expected) or len(set(seen))!=len(seen) or set(seen)!=expected:
        raise ValueError(f"AI batch wrong number/ID of judgments: actual={len(seen)} unique={len(set(seen))} expected={len(expected)}")
    if any(not r.reason.strip() for r in rows):
        raise ValueError("Missing relevance reasons")


def call_judge(client, model:str, query:dict, views:list[dict], batch:list[dict], *,
               output_tokens:int, max_attempts:int):
    from openai import OpenAIError
    data=make_input(query,views,batch)
    for attempt in range(max_attempts):
        try:
            answer=client.responses.parse(
                model=model,
                input=[{"role":"system","content":JUDGE_PROMPT},
                       {"role":"user","content":data}],
                text_format=BatchLabels,
                max_output_tokens=output_tokens)
            parsed=answer.output_parsed
            if parsed is None:
                raise ValueError("AI returned no structured answer")
            check_batch(parsed.rows,views,batch)
            return data,answer,parsed
        except (ValueError,OpenAIError) as e:
            if attempt==max_attempts-1:
                raise
            wait=min(30,2**(attempt+2))
            print(f"retry pass on {query['query_id']} attempt {attempt+1}: {str(e)[:180]}",flush=True)
            time.sleep(wait)
    raise RuntimeError("unreachable")


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--query-id",required=True)
    ap.add_argument("--run-id",type=int,required=True,choices=[1,2,3])
    ap.add_argument("--pass-id",type=int,required=True,choices=[1,2])
    ap.add_argument("--model",default="gpt-6-luna")
    ap.add_argument("--chunk-size",type=int,default=12)
    ap.add_argument("--max-attempts",type=int,default=3)
    ap.add_argument("--output-tokens",type=int,default=16000)
    args=ap.parse_args()
    if args.chunk_size!=12:
        raise ValueError("Frozen 12-case batch size for comparability")
    if not os.getenv("OPENAI_API_KEY","").strip():
        raise RuntimeError("OPENAI_API_KEY missing. Refuse to fabricate labels.")
    from openai import OpenAI
    cases,query,views=load_input(args.query_id,args.run_id)
    client=OpenAI(timeout=240,max_retries=1)
    out=OUTROOT/f"{args.query_id}-run{args.run_id}-pass{args.pass_id}"
    out.mkdir(parents=True,exist_ok=True)
    csvfile=out/"grades.csv"
    collected=[]
    audits=[]
    for lo in range(0,len(cases),args.chunk_size):
        batch=cases[lo:lo+args.chunk_size]
        data,reply,parsed=call_judge(client,args.model,query,views,batch,
                                      output_tokens=args.output_tokens,
                                      max_attempts=args.max_attempts)
        response_by={(r.perspective_id,r.case_id):r for r in parsed.rows}
        stamp=datetime.now(timezone.utc).isoformat()
        for p in views:
            for c in batch:
                judged=response_by[(p["perspective_id"],c["case_id"])]
                collected.append(dict(query_id=args.query_id,run_id=args.run_id,
                    runtime_perspective_id=p["perspective_id"],case_id=c["case_id"],
                    pass_id=args.pass_id,score_0_4=judged.relevance,
                    evidence_reason=judged.reason.strip(),
                    judge_status="AI_BLIND_RUNTIME_VIEW_NOT_HUMAN_GOLD",
                    model_id=reply.model,response_id=reply.id,
                    prompt_sha256=sha(JUDGE_PROMPT),input_sha256=sha(data),
                    timestamp_utc=stamp))
        audits.append(dict(first_case=lo,count_cases=len(batch),
                           judgment_count=len(parsed.rows),input_sha256=sha(data),
                           response_id=reply.id,model=reply.model))
        # Store the exact whitelisted prompt inputs and parsed outputs for reproducibility.
        (out/f"batch_{lo:03d}.json").write_text(json.dumps(dict(
            query_id=args.query_id,run_id=args.run_id,pass_id=args.pass_id,
            input=json.loads(data),rows=parsed.model_dump()["rows"],
            response_id=reply.id,model=reply.model),
            ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        print(f"dynamic-grade {args.query_id} run {args.run_id} pass {args.pass_id}: {lo+len(batch)}/84",flush=True)
    expected={(p["perspective_id"],c["case_id"]) for p in views for c in cases}
    assert len(collected)==len(expected) and {(r["runtime_perspective_id"],r["case_id"]) for r in collected}==expected
    with csvfile.open("w",encoding="utf-8",newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(collected)
    manifest={
        "status":"COMPLETE_AI_BLIND_RUNTIME_VIEW_SINGLE_PASS_NOT_GOLD",
        "query_id":args.query_id,"run_id":args.run_id,"pass_id":args.pass_id,
        "model_requested":args.model,"observed_models":sorted({r["model_id"] for r in collected}),
        "case_count":84,"runtime_perspectives":len(views),
        "judge_rows":len(collected),"judge_prompt_sha256":sha(JUDGE_PROMPT),
        "case_corpus_sha256":sha(CASES_FILE.read_bytes()),
        "generated_perspectives_sha256":sha(PERSPECTIVES_FILE.read_bytes()),
        "previous_labels_in_prompt":False,"solution_fields_in_prompt":False,
        "human_gold_labels":0,"batches":audits,
        "histogram":dict(Counter(str(r["score_0_4"]) for r in collected))
    }
    (out/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("RUNTIME_VIEW_AI_PASS_COMPLETE "+json.dumps({k:manifest[k] for k in ("query_id","run_id","pass_id","judge_rows","runtime_perspectives")}),flush=True)

if __name__=="__main__":
    main()
