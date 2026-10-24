#!/usr/bin/env python3
"""Stage 1 & 2: focused AI-Silver review of 18 empty views, 17 threshold disputes.

Do NOT use AI review as human Gold. Original 8,148 raw qrels preserved.
"""
from __future__ import annotations
import csv,json,os,hashlib
from collections import defaultdict,Counter
from pathlib import Path
from datetime import datetime,timezone
from pydantic import BaseModel,Field

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"experiments/v23_runtime_perspective_qrels"
OUT=ROOT/"experiments/v23_qci256_four_step"
CASES=ROOT/"data/v2_3/main_cases_v2_3.json"
QUESTIONS=ROOT/"data/v2_3/dev_query_candidates_v2_3.json"
PROMPT="""You are an independent BLIND AI-Silver researcher auditing REAL dynamically generated AX problem perspectives.
For each exact pair supplied, judge only how closely the PARTICULAR generated business-problem perspective is addressed by the actual enterprise-case Problem, Task, Context. You must never infer hidden claims from brand, deployed solution, strategy, technology, result or outcomes.
Score 4=direct operational problem+task+context; 3=strong central problem or task match though context differs; 2=partial overlap with different central task; 1=remote/peripheral; 0=unrelated.
You see one original business query as context, and targeted generated perspectives, and individual cases. This audit intentionally samples near-miss cases; do NOT automatically promote any, do NOT force each perspective to have a positive.
For each supplied item return precisely its pair_id and 0..4 numeric score, with concise KOREAN reason identifying case-text commonalities AND missing requirements.
Previous judge scores, decisions, labels, search rankings and the case's outcome/implementation are not supplied. Human Ground Truth has not been provided."""
class R(BaseModel):
    pair_id:str
    score:int=Field(ge=0,le=4)
    reason:str=Field(min_length=8)
class Rs(BaseModel):
    rows:list[R]

def rows(p):
    with p.open(encoding="utf-8",newline="") as f:return list(csv.DictReader(f))
def write(p,rs):
    if not rs:raise AssertionError("no output rows")
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rs[0]));w.writeheader();w.writerows(rs)
def key(r):return "|".join([r["query_id"],str(r["run_id"]),r["runtime_perspective_id"],r["case_id"]])
def load():
    dataset=rows(BASE/"runtime_qrels_8148.csv")
    views=rows(BASE/"per_runtime_view_answerability.csv")
    cases=json.loads(CASES.read_text(encoding="utf-8"))["cases"]
    queries=json.loads(QUESTIONS.read_text(encoding="utf-8"))["queries"]
    zero={(x["query_id"],x["run_id"],x["perspective_id"]) for x in views if x["zero_positive_flag"]=="1"}
    assert len(zero)==18 and len(dataset)==8148 and len(cases)==84
    return dataset,zero,{x["case_id"]:x for x in cases},{q["query_id"]:q for q in queries}
def choose(dataset,zero):
    relevant=defaultdict(list)
    for x in dataset:
        v=(x["query_id"],x["run_id"],x["runtime_perspective_id"])
        if v in zero:relevant[v].append(x)
    assert len(relevant)==18
    target=[]
    counts=[]
    for v,arr in sorted(relevant.items()):
        disputed=[x for x in arr if int(x["threshold_flip"])==1]
        near=[x for x in arr if x["threshold_flip"]=="0" and
              int(x["relevance_pass1"])>=2 and int(x["relevance_pass2"])>=2]
        near.sort(key=lambda x:(-min(int(x["relevance_pass1"]),int(x["relevance_pass2"])),-max(int(x["relevance_pass1"]),int(x["relevance_pass2"])),x["case_id"]))
        chosen=disputed+near[:2]
        counts.append(dict(query_id=v[0],run_id=v[1],perspective_id=v[2],perspective_title=arr[0]["runtime_perspective_title"],
                           original_consensus_positive_count=0,conflict_pairs=len(disputed),near_miss_2plus_pairs_selected=len(near[:2]),
                           review_selected=len(chosen),review_policy="ALL_CONFLICTS_PLUS_TOP2_CONSISTENT_SCORE2_NEARMISSES"))
        for x in chosen:
            target.append(dict(pair_id=key(x),query_id=v[0],run_id=v[1],perspective_id=v[2],case_id=x["case_id"],
                               perspective_title=x["runtime_perspective_title"],
                               perspective_description=x["runtime_perspective_description"],
                               score_pass1=x["relevance_pass1"],score_pass2=x["relevance_pass2"],
                               reason_pass1=x["evidence_reason_pass1"],reason_pass2=x["evidence_reason_pass2"],
                               prior_binary_dispute=x["threshold_flip"],selection_reason="THRESHOLD_DISPUTE" if x["threshold_flip"]=="1" else "NEAR_MISS_2PLUS"))
    assert sum(int(c["conflict_pairs"]) for c in counts)==17, "Changed frozen disputed reference"
    assert len({x["pair_id"] for x in target})==len(target)
    return target,counts

def main():
    from openai import OpenAI
    if not os.getenv("OPENAI_API_KEY","").strip():raise RuntimeError("OPENAI_API_KEY missing, refuse simulated judgment")
    data,zero,cindex,qindex=load()
    targets,counts=choose(data,zero)
    OUT.mkdir(parents=True,exist_ok=True)
    write(OUT/"stage1_review_queue.csv",targets)
    write(OUT/"stage1_zero_view_audit.csv",counts)
    groups=defaultdict(list)
    for x in targets:groups[x["query_id"]].append(x)
    if len(groups)!=5:raise AssertionError("Expected 5 queries")
    client=OpenAI(timeout=240,max_retries=1)
    judgments=[]
    evidence=[]
    for qid,pairs in sorted(groups.items()):
        payload={"query_id":qid,
                 "original_query_context_only":qindex[qid]["business_problem_query"],
                 "pairs":[{"pair_id":x["pair_id"],"runtime_view":{"title":x["perspective_title"],
                   "description":x["perspective_description"]},
                   "case":{"problem":cindex[x["case_id"]]["problem"],"task":cindex[x["case_id"]]["task"],
                           "context":cindex[x["case_id"]]["context"]}} for x in pairs]}
        inp=json.dumps(payload,ensure_ascii=False)
        answer=client.responses.parse(model="gpt-6-luna",
             input=[{"role":"system","content":PROMPT},{"role":"user","content":inp}],
             text_format=Rs,max_output_tokens=12000)
        parsed=answer.output_parsed
        if parsed is None:raise AssertionError("No REAL AI labels")
        exp={x["pair_id"] for x in pairs}
        got=[x.pair_id for x in parsed.rows]
        if len(got)!=len(exp) or set(got)!=exp:raise AssertionError("Incomplete/duplicate review judgments")
        for r in parsed.rows:
            judgments.append(dict(pair_id=r.pair_id,review_score_0_4=r.score,review_reason=r.reason,
                                  review_model=answer.model,review_response_id=answer.id,
                                  prompt_sha256=hashlib.sha256(PROMPT.encode()).hexdigest(),
                                  data_snapshot_sha256=hashlib.sha256(inp.encode()).hexdigest(),
                                  human_approved="FALSE",provenance="THIRD_BLIND_AI_SILVER_AUDIT_ONLY"))
        evidence.append(dict(query_id=qid,response_id=answer.id,response_model=answer.model,
                            label_count=len(parsed.rows),input_sha256=hashlib.sha256(inp.encode()).hexdigest()))
        print("THIRD_PASS_BLIND_COMPLETE",qid,len(parsed.rows),flush=True)
    if len(judgments)!=len(targets):raise AssertionError("Review complete dataset mismatch")
    write(OUT/"stage1_review_ai_pass3.csv",sorted(judgments,key=lambda x:x["pair_id"]))
    write(OUT/"stage1_review_api_evidence.csv",evidence)
    review={r["pair_id"]:r for r in judgments}
    revised=[]
    counts=Counter()
    for row in data:
        original_binary=row["provisional_train_binary_relevant"]
        if row["include_in_training"]=="1":
            score=row["provisional_train_relevance_0_4"];train_binary=original_binary;src="TWO_PASS_AGREEMENT"
        elif key(row) in review and row["threshold_flip"]=="1":
            grade=int(review[key(row)]["review_score_0_4"])
            first=int(row["relevance_pass1"]);second=int(row["relevance_pass2"])
            votes=sum(x>=3 for x in (first,second,grade))
            train_binary=str(int(votes>=2))
            score=str(grade) if votes>=2 and grade>=3 else str(min(first,second,grade))
            src="THREE_PASS_AI_SILVER_BINARY_MAJORITY_NOT_GOLD"
        else:
            score="";train_binary="";src="UNRESOLVED_EXCLUDE_TRAIN"
        rr=dict(pair_id=key(row),query_id=row["query_id"],run_id=row["run_id"],
            perspective_id=row["runtime_perspective_id"],case_id=row["case_id"],
            score_pass1=row["relevance_pass1"],score_pass2=row["relevance_pass2"],
            score_pass3=review[key(row)]["review_score_0_4"] if key(row) in review else "",
            train_grade_0_4=score,train_binary=train_binary,
            train_eligible=int(train_binary!=""),label_provenance=src,
            human_approved="FALSE",third_pass_checked=int(key(row) in review),
            old_threshold_dispute=row["threshold_flip"])
        revised.append(rr);counts[src]+=1
    write(OUT/"stage2_training_label_manifest.csv",revised)
    all_reviewed=sum(x["third_pass_checked"] for x in revised)
    if all_reviewed!=len(judgments):raise AssertionError("Third review key mismatch")
    if any(x["label_provenance"]=="THREE_PASS_AI_SILVER_BINARY_MAJORITY_NOT_GOLD" and x["old_threshold_dispute"]!="1" for x in revised):
        raise AssertionError("Review may only revise 17 threshold-disputed pairs")
    nonempty={(x["query_id"],x["run_id"],x["perspective_id"]) for x in revised if x["train_binary"]=="1"}
    still_zero=sorted(zero-nonempty)
    summary={"status":"THIRD_AI_SILVER_AUDIT_COMPLETE_NOT_HUMAN_GOLD",
        "frozen_runtime_pairs":len(revised),"targeted_zero_views":18,
        "prior_zero_view_threshold_disputes":17,
        "targeted_review_pairs":len(targets),
        "third_ai_judge_responses":len(evidence),
        "confirmed_training_pairs":sum(x["train_eligible"] for x in revised),
        "training_positive":sum(x["train_binary"]=="1" for x in revised),
        "training_negative":sum(x["train_binary"]=="0" for x in revised),
        "unresolved_pairs":sum(x["train_binary"]=="" for x in revised),
        "old_two_pass_agreement_count":counts["TWO_PASS_AGREEMENT"],
        "third_pass_binary_majority_resolutions":counts["THREE_PASS_AI_SILVER_BINARY_MAJORITY_NOT_GOLD"],
        "still_zero_positive_views":len(still_zero),
        "still_zero_view_ids":["|".join(x) for x in still_zero],
        "human_gold_count":0,"notes":[
          "Third AI pass not independent human Gold; only blind to prior judgments.",
          "Original 8148 qrels untouched; selected cases enriched, not automatically forced positive.",
          "Primary evaluation should use two-pass agreement alone to prevent review selection bias."
        ]}
    (OUT/"stage12_summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("STAGE1_2_COMPLETED",json.dumps(summary,ensure_ascii=False),flush=True)

if __name__=="__main__":main()
