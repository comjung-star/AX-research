#!/usr/bin/env python3
"""Evaluate AX v2.1 retrieval ONLY after independently adjudicated relevance labels.

This refuses legacy AX0001..AX0100 qrels and any UNJUDGED, unreviewed or
model-derived relevance labels. A current dataset + a query sheet is not GT.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data/v2_1"
REQUIRED={"query_id","perspective_id","case_id","relevance_0_4",
          "annotator_id","reviewer_id","evidence_reason","status"}


def evaluate(labels_path: Path, rank_paths: list[Path], k: int = 10) -> dict:
    cases=json.loads((DATA/"main_cases_v2_1.json").read_text(encoding="utf-8"))["cases"]
    case_ids={c["case_id"] for c in cases}
    assert len(case_ids)==91
    queries=json.loads((DATA/"dev_query_candidates_v2_1.json").read_text(encoding="utf-8"))["queries"]
    qmap={q["query_id"]:[p["id"] for p in q["draft_perspectives"]] for q in queries}
    expected={(q,p,c) for q,ids in qmap.items() for p in ids for c in case_ids}

    with labels_path.open(encoding="utf-8",newline="") as f:
        reader=csv.DictReader(f)
        if not REQUIRED.issubset(set(reader.fieldnames or [])):
            raise ValueError("Missing annotation fields")
        labels=list(reader)
    got={(r["query_id"],r["perspective_id"],r["case_id"]) for r in labels}
    if len(labels)!=len(expected) or got!=expected:
        raise ValueError("v2.1 relevance GT must cover every query-perspective-case slot")
    if any(r["status"]!="ADJUDICATED" or r["relevance_0_4"] not in {"0","1","2","3","4"}
            or not r["annotator_id"] or not r["reviewer_id"]
            or r["annotator_id"]==r["reviewer_id"] or not r["evidence_reason"]
            for r in labels):
        raise ValueError("Ground Truth NOT READY: relevance labels need blind independent adjudication; do not fabricate scores")

    gold=defaultdict(lambda:defaultdict(set))
    for r in labels:
        if int(r["relevance_0_4"])>=3:
            gold[r["query_id"]][r["perspective_id"]].add(r["case_id"])
    rankings={}
    for p in rank_paths:
        d=json.loads(p.read_text(encoding="utf-8"))
        q=d["query_id"]
        if q in rankings or q not in qmap:
            raise ValueError(f"Duplicate/unknown query in ranking: {q}")
        ranked=[x["case_id"] for x in d["candidate_union"]][:k]
        if len(set(ranked))!=len(ranked) or any(x not in case_ids for x in ranked):
            raise ValueError("Invalid/duplicate/non-v2.1 Case ID in rankings")
        rankings[q]=ranked
    if set(rankings)!=set(qmap):
        raise ValueError("Need all 10 Dev query runs with identical corpus and K")
    per_query=[]
    for q in qmap:
        retrieved=set(rankings[q])
        relevant=set().union(*(gold[q][p] for p in qmap[q]))
        covered=sum(bool(retrieved&gold[q][p]) for p in qmap[q])
        recall=(len(retrieved&relevant)/len(relevant)) if relevant else None
        cov=covered/len(qmap[q])
        per_query.append({"query_id":q,"recall_at_k":recall,
                          "perspective_coverage_at_k":cov,
                          "gold_case_count":len(relevant)})
    observed=[x["recall_at_k"] for x in per_query if x["recall_at_k"] is not None]
    return {"dataset":"v2.1","k":k,"n_queries":len(per_query),
            "mean_recall":sum(observed)/len(observed) if observed else None,
            "mean_perspective_coverage":sum(x["perspective_coverage_at_k"] for x in per_query)/len(per_query),
            "metrics_scope":"DEV_ONLY_not_heldout","per_query":per_query}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--labels",type=Path,default=DATA/"dev_relevance_annotation_sheet_v2_1.csv")
    ap.add_argument("--rankings",type=Path,nargs="+",required=True)
    ap.add_argument("--k",type=int,default=10)
    ap.add_argument("--out",type=Path)
    args=ap.parse_args()
    result=evaluate(args.labels,args.rankings,args.k)
    out=json.dumps(result,ensure_ascii=False,indent=2)+"\n"
    if args.out:
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(out,encoding="utf-8")
    else:
        print(out)


if __name__=="__main__":
    main()
