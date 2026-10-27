#!/usr/bin/env python3
"""Blind v2.1 provisional relevance judgements for researcher's review.

Outputs are AI-generated DRAFTS, never independent human Ground Truth.
Uses only Business Problem Query and Problem/Task/Context for the 91 cases;
never sends solution/strategy/outcome, legacy labels or retrieved rankings.
Records raw model output and exact prompts/versions for audit.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "v2_1"
DEFAULT_DIR = ROOT / "data" / "v2_1" / "qa" / "ai_provisional_2026-10-23"

class Judgment(BaseModel):
    perspective_id: str
    case_id: str
    relevance: int = Field(ge=0, le=4)
    reason: str

class BatchJudgments(BaseModel):
    rows: list[Judgment]

SYSTEM = """You are a BLIND researcher making DRAFT retrieval relevance judgments for an enterprise AI/AX case corpus. These labels are not human Ground Truth.

You see one business problem query, the three distinct REFERENCE perspectives grounded in that query, and a small batch of actual enterprise workflow cases. Grade *each (reference perspective, case)* 0-4 on the Business Problem + Task + Context ONLY. The perspectives are EVALUATION REFERENCES, not model-generated perspectives. Never use solutions, AI strategies, implementations, company fame, or measured outcomes.

Scoring rubric:
4 = direct match of core problem/task, aligned operational context
3 = strong match of central business problem or task, despite contextual differences
2 = partial similarity; some problem/task overlap but central workflow differs
1 = remote/peripheral connection only
0 = substantively unrelated.

IMPORTANT: Do not inflate relevance to produce a desirable diversity/coverage metric. A common generic word (data, employee, AI, work, automation) is NOT relevance. Each perspective must be rated independently, including cases relevant to none. Strong relevance requires real task/problem evidence, not a hypothesis that AI could be used in the same industry. Do not infer undocumented problem descriptions from the organization.
Return exactly one row for every perspective_id x case_id combination. Give concise Korean evidence reason (10-35 words); for low scores distinguish mismatched task or context explicitly. For high scores cite the specific shared issue/task. Never copy previous GT, as none is supplied. Do not list scores from any model ranking."""

def sha_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def cases():
    d=json.loads((DATA/"main_cases_v2_1.json").read_text(encoding="utf-8"))
    assert d["dataset_release"]=="2.1.0"
    cs=d["cases"]
    assert len(cs)==91 and len({x["case_id"] for x in cs})==91
    return cs

def queries():
    d=json.loads((DATA/"dev_query_candidates_v2_1.json").read_text(encoding="utf-8"))
    assert len(d["queries"])==10
    return d["queries"]

def input_for(q, cs):
    # Whitelisted fields - no accident of including solution, factor, strategy.
    clean={
        "query_id":q["query_id"],
        "business_problem_query":q["business_problem_query"],
        "reference_perspectives":[{"id":p["id"],"problem_view":p["title"]} for p in q["draft_perspectives"]],
        "cases":[{"case_id":c["case_id"],"business_problem":c["problem"],
                  "ax_target_task":c["task"],"business_context":c["context"]} for c in cs],
    }
    return json.dumps(clean,ensure_ascii=False,separators=(",",":"))

def verify_batch(q, cs, rows):
    ps={p["id"] for p in q["draft_perspectives"]}
    ids={c["case_id"] for c in cs}
    expected={(p,c) for p in ps for c in ids}
    actual={(row.perspective_id,row.case_id) for row in rows}
    if len(rows)!=len(expected) or actual!=expected:
        raise ValueError(f"Missing/duplicate/extra labels expected={len(expected)} actual={len(rows)} unique={len(actual)}")
    if any(not x.reason.strip() for x in rows):
        raise ValueError("Missing evidence reason")

def load_checkpoint(path):
    if not path.exists():
        return []
    with path.open(encoding="utf-8",newline="") as f:
        return list(csv.DictReader(f))

def write_csv(path, rows):
    fieldnames=["query_id","perspective_id","case_id","provisional_relevance_0_4",
                "evidence_reason","status","annotator_kind","annotator_run",
                "model_id","response_id","prompt_sha256","case_input_sha256",
                "input_snapshot_sha256","timestamp_utc","needs_human_review"]
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

def grade_batch(client, model, q, batch, *, max_attempts=3, output_tokens=16000):
    from openai import OpenAIError
    text=input_for(q,batch)
    for attempt in range(max_attempts):
        try:
            response=client.responses.parse(
                model=model,
                input=[{"role":"system","content":SYSTEM},
                       {"role":"user","content":text}],
                text_format=BatchJudgments,
                max_output_tokens=output_tokens,
            )
            got=response.output_parsed
            if got is None:
                raise ValueError("No parsed labels (max_output_tokens exhaustion?)")
            verify_batch(q,batch,got.rows)
            return text,response,got
        except (OpenAIError,ValueError) as ex:
            if attempt+1==max_attempts:
                raise
            pause=min(40,2**(attempt+2))
            print(f"retry {q['query_id']} n={len(batch)} attempt={attempt+1}: {type(ex).__name__}: {str(ex)[:220]}",flush=True)
            time.sleep(pause)
    raise AssertionError("unreachable")

def run(args):
    import openai
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is absent; do not generate fabricated judgments")
    qs=queries()[:args.max_queries] if args.max_queries else queries()
    if args.query_id:
        qs=[q for q in queries() if q["query_id"]==args.query_id]
        if len(qs)!=1:
            raise ValueError(f"Unknown query_id {args.query_id}")
    cs=cases()[:args.max_cases] if args.max_cases else cases()
    out=Path(args.output_dir)
    out.mkdir(parents=True,exist_ok=True)
    csv_path=out/"provisional_ai_relevance.csv"
    manifest_path=out/"ai_judgment_manifest.json"
    historical=load_checkpoint(csv_path)
    seen={(r["query_id"],r["perspective_id"],r["case_id"]) for r in historical}
    assert len(seen)==len(historical),"Duplicate old checkpoint key"
    client=openai.OpenAI(timeout=180,max_retries=1)
    collected=list(historical)
    requests=0
    snapshots=[]
    for qi,q in enumerate(qs,1):
        for lo in range(0,len(cs),args.chunk_size):
            batch=cs[lo:lo+args.chunk_size]
            expected={(q["query_id"],p["id"],c["case_id"]) for p in q["draft_perspectives"] for c in batch}
            if expected.issubset(seen):
                continue
            if seen&expected:
                raise ValueError(f"Partial checkpoint batch {q['query_id']} {lo}")
            if requests>=args.max_requests:
                raise RuntimeError(f"API call cap {args.max_requests} reached before full labels")
            raw,response,parsed=grade_batch(client,args.model,q,batch,
                                            max_attempts=args.max_attempts,
                                            output_tokens=args.output_tokens)
            requests+=1
            stamp=datetime.now(timezone.utc).isoformat()
            row_by_key={(x.perspective_id,x.case_id):x for x in parsed.rows}
            for p in q["draft_perspectives"]:
                for case in batch:
                    row=row_by_key[(p["id"],case["case_id"])]
                    # Labels >=2 and near threshold need substantive independent human review,
                    # but no model-generated label is ever marked HUMAN_ADJUDICATED.
                    rec=dict(query_id=q["query_id"],perspective_id=p["id"],
                             case_id=case["case_id"],provisional_relevance_0_4=row.relevance,
                             evidence_reason=row.reason.strip(),
                             status="AI_DRAFT_NOT_HUMAN_GT",
                             annotator_kind="LLM_SINGLE_PASS_BLIND_PROVISIONAL",
                             annotator_run=f"v21-ai-{qi:02d}-{lo:03d}",
                             model_id=response.model,response_id=response.id,
                             prompt_sha256=sha_text(SYSTEM),
                             case_input_sha256=sha_text(json.dumps(
                                 {"problem":case["problem"],"task":case["task"],"context":case["context"]},
                                 ensure_ascii=False,sort_keys=True)),
                             input_snapshot_sha256=sha_text(raw),
                             timestamp_utc=stamp,
                             needs_human_review="YES")
                    collected.append(rec)
            if args.write_raw:
                path=out/"raw_batches"/f"{q['query_id']}_cases_{lo:03d}.json"
                path.parent.mkdir(parents=True,exist_ok=True)
                path.write_text(json.dumps(
                    {"query_id":q["query_id"],"first_case":lo,
                     "model_id":response.model,"response_id":response.id,
                     "input_problem_only":json.loads(raw),
                     "parsed_provisional_labels":parsed.model_dump()},
                    ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
            seen|=expected
            write_csv(csv_path,collected)
            print(f"graded {q['query_id']} cases {lo+1}-{min(lo+len(batch),len(cs))}; total={len(collected)}; API calls={requests}",flush=True)

    expected={(q["query_id"],p["id"],c["case_id"])
              for q in qs for p in q["draft_perspectives"] for c in cs}
    if set(seen)!=expected:
        raise ValueError(f"Provisional coverage incomplete expected={len(expected)} got={len(seen)}")
    by_score=Counter(str(r["provisional_relevance_0_4"]) for r in collected)
    by_query=defaultdict(Counter)
    for row in collected:
        by_query[row["query_id"]][str(row["provisional_relevance_0_4"])]+=1
    manifest={
       "version":"v2.1.0","purpose":"PROVISIONAL AI BLIND RELEVANCE DRAFT FOR RESEARCHER APPROVAL WORKFLOW",
       "human_ground_truth":False,"human_approved_labels":0,
       "gold_eligible":False,"independent_human_rater":False,
       "researcher_approval_scope":"AI draft/candidate review only; not an independent human annotation",
       "status":"COMPLETE_AI_DRAFT_ONLY",
       "model_requested":args.model,"model_ids_seen":sorted({x["model_id"] for x in collected}),
       "prompt_sha256":sha_text(SYSTEM),
       "cases_in_scope":len(cs),"queries_in_scope":len(qs),
       "perspectives_in_scope":sum(len(x["draft_perspectives"]) for x in qs),
       "judgment_count":len(collected),"score_histogram":dict(sorted(by_score.items())),
       "by_query":{q:dict(sorted(counts.items())) for q,counts in sorted(by_query.items())},
       "score_3_or_4":sum(int(k)>=3 and v for k,v in by_score.items()),
       "human_review_required_count":len(collected),
       "source_dataset_git_blob":"c2f6899e4cbd3eb5e903fa84766f541684d4aa45",
       "warning":"These are ONE-pass AI subjective labels, not ground truth. Never use for final claimed RQ1 results or tune prompts against held-out test.",
       "created_at_utc":datetime.now(timezone.utc).isoformat()
    }
    manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("COMPLETE PROVISIONAL AI DRAFT",json.dumps(manifest["score_histogram"],ensure_ascii=False),flush=True)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--model",default="gpt-6-luna")
    p.add_argument("--output-dir",default=str(DEFAULT_DIR))
    p.add_argument("--chunk-size",type=int,default=13)
    p.add_argument("--max-requests",type=int,default=100)
    p.add_argument("--max-attempts",type=int,default=3)
    p.add_argument("--output-tokens",type=int,default=16000)
    p.add_argument("--max-queries",type=int,default=0)
    p.add_argument("--query-id",default="")
    p.add_argument("--max-cases",type=int,default=0)
    p.add_argument("--write-raw",action="store_true")
    a=p.parse_args()
    if not (1<=a.chunk_size<=30):raise ValueError("1 <= chunk-size <= 30")
    run(a)

if __name__=="__main__":
    main()
