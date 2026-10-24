#!/usr/bin/env python3
"""Measure *official professor-style per-perspective Top-K unions* separately from global Top-K.

No label used for ranking; silver labels used for post-hoc evaluation only.
"""
from __future__ import annotations
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

from scripts.v23_professor_hybrid_preserving import ROOT, GT, load_csv, write_csv

OUT=ROOT/"experiments/v23_full_union_topm"
METHODS=("dense","rrf","interleave")
MS=(10,20,40,60,84)
KS=(5,10,20)


def main():
    case_rows=load_csv(OUT/"perspective_topk_rankings.csv")
    gt_rows=load_csv(GT)
    positive=defaultdict(set)
    ref=defaultdict(lambda:defaultdict(set))
    for row in gt_rows:
        if int(row["relevance_0_4"])>=3:
            positive[row["query_id"]].add(row["case_id"])
            ref[row["query_id"]][row["perspective_id"]].add(row["case_id"])
    branch=defaultdict(lambda:defaultdict(list))
    all_perspectives=defaultdict(set)
    for row in case_rows:
        q=row["query_id"]; run=int(row["run_id"]); m=int(row["m"])
        key=(q,run,row["method"],m,row["scorer"])
        branch[key][row["perspective_id"]].append((int(row["rank"]),row["case_id"]))
        all_perspectives[(q,run)].add(row["perspective_id"])
    for key,pers in branch.items():
        m=key[3]
        for p,ls in pers.items():
            assert sorted(k for k,_ in ls)==list(range(1,min(m,20)+1))
            assert len({c for _,c in ls})==len(ls)
        assert set(pers)==all_perspectives[key[:2]]
    metrics=[]
    for q in sorted(positive):
        for run in (1,2,3):
            gt=positive[q]; active=[s for s in ref[q].values() if s]
            for m in MS:
                for method in METHODS:
                    for scorer in ("rrf","mlp"):
                        key=(q,run,method,m,scorer)
                        pers=branch[key]
                        for k in KS:
                            if k>m:
                                continue
                            pool=set()
                            for pid,ls in pers.items():
                                pool.update(cid for rk,cid in ls if rk<=k)
                            assert pool and len(pool)<=len(pers)*k
                            metrics.append(dict(query_id=q,run_id=run,method=method,
                                m=m,scorer=scorer,per_perspective_k=k,
                                branch_count=len(pers),unique_count=len(pool),
                                positive_count=len(pool&gt),
                                candidate_recall=len(pool&gt)/len(gt),
                                ref_view_coverage=sum(bool(pool&s) for s in active)/len(active),
                                silver_gt_size=len(gt)))
    idx={(r["query_id"],int(r["run_id"]),r["method"],int(r["m"]),r["scorer"],int(r["per_perspective_k"])):r for r in metrics}
    for r in metrics:
        control=idx[(r["query_id"],int(r["run_id"]),"dense",int(r["m"]),r["scorer"],int(r["per_perspective_k"]))]
        r["recall_delta_vs_dense_same_m"]=r["candidate_recall"]-control["candidate_recall"]
        r["unique_count_delta_vs_dense_same_m"]=r["unique_count"]-control["unique_count"]
    assert len(metrics)==len(positive)*3*len(METHODS)*2*(2+4*3)
    write_csv(OUT/"perspective_topk_union_metrics.csv",metrics)
    summary={"metric":"per-perspective Top-K union over runtime branches, NOT global Top-K",
             "query_count":len(positive),"query_runs":len(positive)*3,
             "gt":"AI-Silver Dev only","rows":len(metrics),"table":[]}
    for m in MS:
        for k in KS:
            if k>m:
                continue
            for scorer in ("rrf","mlp"):
                row={"m":m,"per_perspective_k":k,"scorer":scorer}
                for method in METHODS:
                    rs=[x for x in metrics if x["m"]==m and x["per_perspective_k"]==k
                        and x["scorer"]==scorer and x["method"]==method]
                    assert len(rs)==30
                    row[method]=dict(
                        macro_recall=float(np.mean([x["candidate_recall"] for x in rs])),
                        mean_unique=float(np.mean([x["unique_count"] for x in rs])),
                        macro_ref_coverage=float(np.mean([x["ref_view_coverage"] for x in rs])),
                        recall_delta_vs_dense=float(np.mean([x["recall_delta_vs_dense_same_m"] for x in rs])))
                summary["table"].append(row)
    (OUT/"perspective_topk_union_summary.json").write_text(
        json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("PER_PERSPECTIVE_TOPK_UNION_OK "+json.dumps(summary,ensure_ascii=False),flush=True)


if __name__=="__main__":
    main()
