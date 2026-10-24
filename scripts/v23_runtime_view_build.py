#!/usr/bin/env python3
"""Build 8,148 runtime perspective/case qrels from two REAL blind AI passes.

No fake labels, no reference-view ID mapping, no human Gold claims.
"""
from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path
from statistics import mean

ROOT=Path(__file__).resolve().parents[1]
INROOT=ROOT/"experiments/v23_runtime_perspective_qrels/raw_passes"
OUT=ROOT/"experiments/v23_runtime_perspective_qrels"
CASEFILE=ROOT/"data/v2_3/main_cases_v2_3.json"
QUERYFILE=ROOT/"data/v2_3/dev_query_candidates_v2_3.json"
VIEWSFILE=ROOT/"experiments/v23_dev/stage1/generated_runtime_perspectives.json"

def csvread(path):
    with path.open(encoding="utf-8",newline="") as f:
        return list(csv.DictReader(f))

def csvwrite(path,rows):
    if not rows:
        raise ValueError(f"No data {path}")
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]))
        w.writeheader();w.writerows(rows)

def expected_runtime(case_list, query_list, views):
    if len(case_list)!=84 or len(query_list)!=10 or len(views)!=97:
        raise AssertionError("Frozen dimensions unexpected")
    qids={q["query_id"] for q in query_list}
    cids={c["case_id"] for c in case_list}
    if len(cids)!=84 or len(qids)!=10:
        raise AssertionError("Duplicate case/query")
    group=defaultdict(list)
    for p in views:
        q=p["query_id"];run=int(p["run_id"]);pid=p["perspective_id"]
        if q not in qids or run not in (1,2,3):
            raise AssertionError("Invalid perspective question")
        group[(q,run)].append(pid)
    if len(group)!=30 or any(not 2<=len(v)<=5 or len(v)!=len(set(v)) for v in group.values()):
        raise AssertionError("Generated branches malformed")
    expected={(p["query_id"],int(p["run_id"]),p["perspective_id"],cid)
              for p in views for cid in cids}
    if len(expected)!=97*84:
        raise AssertionError("Repeated dynamic perspective")
    return expected, group, qids, cids

def grade_consensus(s1:int,s2:int):
    """Predeclared, no overwriting disagreements with silent negatives."""
    if any(s<0 or s>4 for s in (s1,s2)):
        raise ValueError("Out of range")
    threshold_flip=int((s1>=3)!=(s2>=3))
    uncertain=bool(threshold_flip)
    grade=min(s1,s2) if not uncertain else None
    binary=int(grade>=3) if grade is not None else None
    if uncertain:
        status="AI_SILVER_THRESHOLD_CONFLICT_EXCLUDE_TRAIN"
    elif s1==s2:
        status="AI_SILVER_CONSISTENT_GRADE"
    else:
        status="AI_SILVER_SAME_CLASS_GRADE_DIFFERENCE"
    return grade,binary,int(not uncertain),status,threshold_flip

def load_pass(qids, group, case_ids, views):
    manifest_rows=[]
    ratings={1:{},2:{}}
    manifests={1:[],2:[]}
    for p in (1,2):
        for qid in sorted(qids):
            for run in (1,2,3):
                d=INROOT/f"v23-dynamic-{qid}-run{run}-pass{p}"
                if not d.is_dir():
                    d=INROOT/f"{qid}-run{run}-pass{p}"
                path=d/"grades.csv"
                mpath=d/"manifest.json"
                if not path.exists() or not mpath.exists():
                    raise FileNotFoundError(f"Missing REAL judge outputs {d}")
                manifest=json.loads(mpath.read_text(encoding="utf-8"))
                rows=csvread(path)
                assert manifest["status"]=="COMPLETE_AI_BLIND_RUNTIME_VIEW_SINGLE_PASS_NOT_GOLD"
                assert (manifest["query_id"],int(manifest["run_id"]),int(manifest["pass_id"]))==(qid,run,p)
                assert manifest["case_count"]==84
                assert manifest["runtime_perspectives"]==len(group[(qid,run)])
                assert manifest["judge_rows"]==len(group[(qid,run)])*84==len(rows)
                assert manifest["previous_labels_in_prompt"] is False
                assert manifest["solution_fields_in_prompt"] is False
                assert manifest["human_gold_labels"]==0
                assert manifest["case_corpus_sha256"]==hashlib.sha256(CASEFILE.read_bytes()).hexdigest()
                assert manifest["generated_perspectives_sha256"]==hashlib.sha256(VIEWSFILE.read_bytes()).hexdigest()
                assert len(manifest["batches"])==7
                manifests[p].append(manifest)
                batch_keys=set()
                batch_ids=set()
                for r in rows:
                    key=(r["query_id"],int(r["run_id"]),r["runtime_perspective_id"],r["case_id"])
                    if key[0]!=qid or key[1]!=run or r["runtime_perspective_id"] not in group[(qid,run)] or r["case_id"] not in case_ids:
                        raise AssertionError(f"Wrong key in judge pass {key}")
                    if key in batch_keys or key in ratings[p]:
                        raise AssertionError(f"Duplicate label {key} pass={p}")
                    assert int(r["pass_id"])==p and 0<=int(r["score_0_4"])<=4
                    assert r["judge_status"]=="AI_BLIND_RUNTIME_VIEW_NOT_HUMAN_GOLD"
                    assert r["response_id"] and r["model_id"] and len(r["evidence_reason"].strip())>=6
                    batch_keys.add(key)
                    batch_ids.add(r["response_id"])
                    ratings[p][key]=r
                assert len(batch_keys)==len(group[(qid,run)])*84
                assert len(batch_ids)==7, "Each of seven API batches must be a different actual response"
                manifest_rows.append(dict(query_id=qid,run_id=run,pass_id=p,
                     model_requested=manifest["model_requested"],
                     observed_models="|".join(manifest["observed_models"]),
                     score_rows=len(rows),judging_api_responses=len(batch_ids),
                     prompt_sha256=manifest["judge_prompt_sha256"],
                     corpus_sha256=manifest["case_corpus_sha256"]))
    return ratings, manifests, manifest_rows

def construct():
    case_list=json.loads(CASEFILE.read_text(encoding="utf-8"))["cases"]
    query_list=json.loads(QUERYFILE.read_text(encoding="utf-8"))["queries"]
    views=json.loads(VIEWSFILE.read_text(encoding="utf-8"))
    expected,groups,qids,cids=expected_runtime(case_list,query_list,views)
    grade_pass,manifests,manifest_rows=load_pass(qids,groups,cids,views)
    if set(grade_pass[1])!=expected or set(grade_pass[2])!=expected:
        raise AssertionError("Missing any of 8148 expected AI judgments")
    model_pass1={m["model_requested"] for m in manifests[1]}
    model_pass2={m["model_requested"] for m in manifests[2]}
    if model_pass1!=model_pass2 or len(model_pass1)!=1:
        raise AssertionError("Different judge models across blind passes")
    all_prompts={x["judge_prompt_sha256"] for x in manifest_rows}
    if len(all_prompts)!=1:
        raise AssertionError("Prompt changed between passes")
    if len({r["response_id"] for p in (1,2) for r in grade_pass[p].values()})!=420:
        raise AssertionError("Expected 420 independent API response IDs")
    vindex={(p["query_id"],int(p["run_id"]),p["perspective_id"]):p for p in views}
    cindex={c["case_id"]:c for c in case_list}
    qindex={q["query_id"]:q for q in query_list}
    result=[]
    training=[]
    positives=[]
    reviews=[]
    by_view=defaultdict(list)
    for key in sorted(expected):
        q,run,pid,cid=key
        a,b=grade_pass[1][key],grade_pass[2][key]
        s1,s2=int(a["score_0_4"]),int(b["score_0_4"])
        grade,binary,eligible,status,flip=grade_consensus(s1,s2)
        needs_review=bool(flip or abs(s1-s2)>=2 or (s1==2 or s2==2 or s1==3 or s2==3))
        priority="HIGH_THRESHOLD_FLIP" if flip else ("MEDIUM_WIDE_GRADE_GAP" if abs(s1-s2)>=2 else ("LOW_NEAR_THRESHOLD" if needs_review else "NONE"))
        v=vindex[(q,run,pid)]
        row=dict(query_id=q,run_id=run,runtime_perspective_id=pid,
            runtime_perspective_title=v["perspective_title"],
            runtime_perspective_description=v["perspective_description"],
            case_id=cid,
            relevance_pass1=s1,relevance_pass2=s2,
            provisional_train_relevance_0_4="" if grade is None else grade,
            provisional_train_binary_relevant="" if binary is None else binary,
            include_in_training=eligible,
            judgment_status=status,threshold_flip=flip,
            exact_grade_agreement=int(s1==s2),
            abs_grade_difference=abs(s1-s2),
            needs_human_review=int(needs_review),review_priority=priority,
            evidence_reason_pass1=a["evidence_reason"],
            evidence_reason_pass2=b["evidence_reason"],
            judge_model_pass1=a["model_id"],judge_model_pass2=b["model_id"],
            response_id_pass1=a["response_id"],response_id_pass2=b["response_id"],
            provenance="AI_TWO_INDEPENDENT_BLIND_PASSES_SILVER_NOT_HUMAN_GOLD",
            human_approved="FALSE",
            query_source="data/v2_3/dev_query_candidates_v2_3.json",
            dynamic_views_source="experiments/v23_dev/stage1/generated_runtime_perspectives.json",
            cases_source="data/v2_3/main_cases_v2_3.json")
        result.append(row)
        by_view[(q,run,pid)].append(row)
        if eligible:
            training.append(row)
        if eligible and binary==1:
            positives.append(row)
        if needs_review:
            reviews.append(dict(query_id=q,run_id=run,perspective_id=pid,
                perspective_title=v["perspective_title"],
                perspective_description=v["perspective_description"],
                original_business_query=qindex[q]["business_problem_query"],
                case_id=cid,case_problem=cindex[cid]["problem"],
                case_task=cindex[cid]["task"],case_context=cindex[cid]["context"],
                score_pass1=s1,score_pass2=s2,
                reason_pass1=a["evidence_reason"],reason_pass2=b["evidence_reason"],
                priority=priority,
                reviewer_score_0_4="",reviewer_id="",reviewer_status="HUMAN_REVIEW_NOT_YET_PERFORMED"))
    if len(result)!=8148 or len(by_view)!=97 or len(result)!=len(training)+sum(x["threshold_flip"] for x in result):
        raise AssertionError("Aggregate length mismatch")
    views_summary=[]
    for key,rs in sorted(by_view.items()):
        label_pos=sum(int(x["provisional_train_binary_relevant"]=="1" or x["provisional_train_binary_relevant"]==1) for x in rs)
        unresolved=sum(int(x["threshold_flip"]) for x in rs)
        counts=Counter(str(x["provisional_train_relevance_0_4"]) for x in rs)
        views_summary.append(dict(query_id=key[0],run_id=key[1],perspective_id=key[2],
            perspective_title=vindex[key]["perspective_title"],case_count=84,
            high_relevance_count=label_pos,trainable_negative_count=84-unresolved-label_pos,
            unresolved_count=unresolved,exact_agreement_count=sum(x["exact_grade_agreement"] for x in rs),
            pass1_relevant_count=sum(x["relevance_pass1"]>=3 for x in rs),
            pass2_relevant_count=sum(x["relevance_pass2"]>=3 for x in rs),
            zero_positive_flag=int(label_pos==0),grade_histogram=json.dumps(dict(counts),ensure_ascii=False),
            silver_only="AI_SILVER_NOT_HUMAN_GT"))
    splits=[]
    for q in sorted(qids):
        splits.append(dict(held_out_query_id=q,
            train_query_ids="|".join(sorted(qids-{q})),
            train_dynamic_view_count=sum(1 for p in views if p["query_id"]!=q),
            held_out_dynamic_view_count=sum(1 for p in views if p["query_id"]==q),
            no_shared_original_query_between_train_and_heldout=1,
            split_policy="QUERY_LEVEL_LEAVE_ONE_QUERY_OUT_3_RUNS_TOGETHER"))
    # Safe output checks before writing.
    if sum(x["include_in_training"] for x in result)!=len(training):
        raise AssertionError("Train eligibility count mismatch")
    for x in result:
        if x["threshold_flip"] and x["include_in_training"]:
            raise AssertionError("Threshold disagreement leaked into training")
        if x["human_approved"]!="FALSE":
            raise AssertionError("False Gold declaration")
    OUT.mkdir(parents=True,exist_ok=True)
    csvwrite(OUT/"runtime_qrels_8148.csv",result)
    csvwrite(OUT/"trainable_pairs_ai_silver.csv",training)
    csvwrite(OUT/"positive_pairs_ai_silver.csv",positives)
    csvwrite(OUT/"review_priority.csv",reviews)
    csvwrite(OUT/"per_runtime_view_answerability.csv",views_summary)
    csvwrite(OUT/"loqo_split_manifest.csv",splits)
    csvwrite(OUT/"api_pass_integrity.csv",manifest_rows)
    scorehist1=Counter(str(x["relevance_pass1"]) for x in result)
    scorehist2=Counter(str(x["relevance_pass2"]) for x in result)
    exact=sum(x["exact_grade_agreement"] for x in result)
    flips=sum(x["threshold_flip"] for x in result)
    posit=len(positives)
    human_queue=Counter(x["priority"] for x in reviews)
    details={
      "status":"COMPLETE_RUNTIME_VIEW_AI_SILVER_8148_NOT_HUMAN_GT",
      "created_at_utc":datetime.now(timezone.utc).isoformat(),
      "cases":84,"dev_business_queries":10,"runs_per_query":3,
      "generated_runtime_views":97,"judged_pairs":len(result),
      "blind_ai_passes":2,"total_raw_judgments":len(grade_pass[1])+len(grade_pass[2]),
      "unique_actual_response_ids":len({r["response_id"] for p in (1,2) for r in grade_pass[p].values()}),
      "expected_api_requests":420,
      "judge_model_requested":next(iter(model_pass1)),
      "judge_model_observed":sorted({r["model_id"] for p in (1,2) for r in grade_pass[p].values()}),
      "model_prompt_sha256":next(iter(all_prompts)),
      "case_corpus_sha256":hashlib.sha256(CASEFILE.read_bytes()).hexdigest(),
      "runtime_perspectives_sha256":hashlib.sha256(VIEWSFILE.read_bytes()).hexdigest(),
      "score_histogram_pass1":dict(scorehist1),"score_histogram_pass2":dict(scorehist2),
      "exact_grade_agreement_count":exact,
      "exact_grade_agreement_fraction":exact/len(result),
      "binary_threshold_flip_count":flips,
      "binary_threshold_flip_fraction":flips/len(result),
      "binary_agreement_fraction":1-flips/len(result),
      "trainable_pairs_count":len(training),
      "trainable_positive_count":posit,
      "trainable_negative_count":len(training)-posit,
      "review_queue_count":len(reviews),
      "review_queue_priorities":dict(human_queue),
      "runtime_views_with_no_consensus_positive":sum(x["zero_positive_flag"] for x in views_summary),
      "mean_trainable_positives_per_runtime_view":mean(x["high_relevance_count"] for x in views_summary),
      "all_10_queries_separated_in_loqo":True,
      "independent_human_gold_available":False,
      "provenance":"AI_TWO_INDEPENDENT_BLIND_PASSES_SILVER_NOT_HUMAN_GOLD",
      "notes":[
        "Runtime view IDs are not reference evaluation view IDs.",
        "AI agreement is reproducibility, not human correctness.",
        "Unresolved threshold flips are not silently labelled negative.",
        "Review queue optional targeted checks, not required full manual annotation.",
        "10 original questions means this is a Dev-only corpus and not an independent Test."
      ]
    }
    (OUT/"label_quality_report.json").write_text(json.dumps(details,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("RUNTIME_VIEW_QRELS_COMPLETE "+json.dumps(details,ensure_ascii=False),flush=True)
    return details

if __name__=="__main__":
    construct()
