#!/usr/bin/env python3
"""Frozen Stage 1: keep original runtime perspective lists instead of early global Top-K.

No API calls; no new text encoding. Outputs are DEV AI-Silver diagnostics.
"""
from __future__ import annotations

import csv
import json
import sys
from collections import OrderedDict, defaultdict
from pathlib import Path
from statistics import mean

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from ax_research.selection import branch_balanced_unique

SRC = ROOT / "experiments/v23_dev/stage1"
OUT = ROOT / "experiments/v23_stage1_perspective_separation"
GT = ROOT / "data/v2_3/ground_truth/silver_dev_qrels_2520.csv"
KS = (5, 10, 20)
METHODS = ("dense", "bm25")
STAGE1_SYSTEM = {"dense":"mp_dense_bge_m3", "bm25":"mp_bm25"}
SINGLE_SYSTEM = {"dense":"single_dense_bge_m3", "bm25":"single_bm25"}

def csvread(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))

def csvwrite(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise ValueError(f"Empty data: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

def relevant_union_and_coverage(selected: set[str], labels: dict[str, dict[str, set[str]]], qid: str) -> tuple[float,float,int,int]:
    refs = [s for s in labels[qid].values() if s]
    positives = set().union(*refs)
    if not positives or not refs:
        raise AssertionError(f"No Silver answerable views: {qid}")
    nrel = len(selected & positives)
    return nrel / len(positives), sum(bool(selected & r) for r in refs) / len(refs), nrel, len(positives)

def load_frozen() -> tuple[dict,dict,dict,dict,dict,dict,dict]:
    raw = csvread(SRC / "branch_rankings.csv")
    if len(raw) != 97*84*2:
        raise AssertionError(f"expected 16296 frozen per-branch ranking rows, got {len(raw)}")
    ranked = defaultdict(list)
    for r in raw:
        key = (r["query_id"], int(r["run_id"]), r["retrieval"], r["perspective_id"])
        ranked[key].append((int(r["local_rank"]), r["case_id"]))
    if len(ranked) != 97*2:
        raise AssertionError(f"expected 194 complete branch retrieval rankings, got {len(ranked)}")
    branches = defaultdict(OrderedDict)
    for (qid,run,method,pid), lst in ranked.items():
        if method not in METHODS:
            raise AssertionError("Unexpected retrieval type")
        if sorted(rk for rk,cid in lst) != list(range(1,85)):
            raise AssertionError(f"Bad ranks {qid}/{run}/{pid}/{method}")
        arr = [cid for _,cid in sorted(lst)]
        if len(set(arr)) != 84:
            raise AssertionError(f"Duplicate case {qid}/{run}/{pid}/{method}")
        branches[(qid,run,method)][pid] = arr
    definitions = json.loads((SRC / "generated_runtime_perspectives.json").read_text(encoding="utf-8"))
    if len(definitions) != 97:
        raise AssertionError("Expected 97 generated perspectives")
    definitions_by_key = {(d["query_id"],int(d["run_id"]),d["perspective_id"]):d for d in definitions}
    if len(definitions_by_key) != 97:
        raise AssertionError("Repeated generated perspective ID")
    for qid,run,method in branches:
        expected = [d["perspective_id"] for d in definitions
                    if d["query_id"]==qid and int(d["run_id"])==run]
        if len(expected) < 2 or len(expected) > 5:
            raise AssertionError("Perspective count outside 2..5")
        br = branches[(qid,run,method)]
        if set(br) != set(expected):
            raise AssertionError(f"Perspective difference {qid}/{run}/{method}")
        # The original stage1 script uses generation order; preserve this exact order.
        branches[(qid,run,method)] = OrderedDict((pid,br[pid]) for pid in expected)
    if len(branches) != 30*2:
        raise AssertionError("Expected 30 question-runs x 2 retrievers")
    raw_labels = csvread(GT)
    if len(raw_labels) != 2520 or any(r["provenance"] != "AI_THREE_PASS_MEDIAN_NOT_HUMAN_GOLD" for r in raw_labels):
        raise AssertionError("Frozen AI-Silver relevance table mismatch")
    labels = defaultdict(lambda:defaultdict(set))
    for row in raw_labels:
        if int(row["relevance_0_4"]) >= 3:
            labels[row["query_id"]][row["perspective_id"]].add(row["case_id"])
        else:
            labels[row["query_id"]][row["perspective_id"]] |= set()
    baselines = defaultdict(list)
    for row in csvread(SRC / "rankings_top20.csv"):
        key = (row["query_id"],int(row["run_id"]),row["system"])
        baselines[key].append((int(row["rank"]),row["case_id"]))
    top20 = {}
    for key, rows in baselines.items():
        sr=sorted(rows)
        if [rank for rank,cid in sr] != list(range(1,21)):
            raise AssertionError(f"Bad saved 20 ranks {key}")
        top20[key] = [cid for rank,cid in sr]
    expected_metric = {}
    for r in csvread(SRC / "metrics_by_query.csv"):
        expected_metric[(r["query_id"],int(r["run_id"]),r["system"],int(r["k"]))] = float(r["recall"])
    npz = np.load(SRC / "fixed_bge_m3_embeddings.npz", allow_pickle=False)
    case_ids = [str(x) for x in npz["case_ids"].tolist()]
    queries = [str(x) for x in npz["query_ids"].tolist()]
    query_vec = npz["query_embeddings"]
    doc_vec = npz["document_embeddings"]
    if len(case_ids)!=84 or len(queries)!=10 or len(set(case_ids))!=84:
        raise AssertionError("Frozen dimensions mismatch")
    # Recompute full original SINGLE Dense ranking without encoding anything new.
    single_dense = {}
    for qid,vec in zip(queries, query_vec):
        sims = doc_vec @ vec
        arr = [case_ids[i] for i in sorted(range(84),key=lambda i:(-float(sims[i]),case_ids[i]))]
        if arr[:20] != top20[(qid,0,SINGLE_SYSTEM["dense"])]:
            raise AssertionError(f"Saved Single Dense Top20 not reproducible: {qid}")
        single_dense[qid] = arr
    queries_raw = json.loads((ROOT/"data/v2_3/dev_query_candidates_v2_3.json").read_text(encoding="utf-8"))["queries"]
    query_text={q["query_id"]:q["business_problem_query"] for q in queries_raw}
    cases_raw=json.loads((ROOT/"data/v2_3/main_cases_v2_3.json").read_text(encoding="utf-8"))["cases"]
    case_text={c["case_id"]:c["problem"] for c in cases_raw}
    return branches,definitions_by_key,labels,top20,expected_metric,single_dense,{"queries":query_text,"cases":case_text}

def evaluate_record(qid,run,method,k,selected,labels,baselines,reported_count=None):
    selected = list(selected)
    if len(selected)!=len(set(selected)):
        raise AssertionError(f"Duplicate case in output: {qid}/{run}/{method}")
    recall, coverage, relevant,total = relevant_union_and_coverage(set(selected),labels,qid)
    return dict(query_id=qid,run_id=run,retrieval=method,k=k,
                selected_count=len(selected),relevant_count=relevant,total_silver_positive=total,
                recall=recall,reference_view_coverage=coverage)

def main():
    branches,definitions,labels,frozen,expected,single_dense,texts=load_frozen()
    output_branches,metrics,comparisons,loss_rows,query_examples=[],[],[],[],[]
    baseline_replay=[]
    for qid in sorted(texts["queries"]):
        for run in (1,2,3):
            for method in METHODS:
                br=branches[(qid,run,method)]
                ordered=branch_balanced_unique(br,84)
                rr=[c for pid,c in ordered]
                if len(rr)!=84 or len(set(rr))!=84:
                    raise AssertionError("Global merge incomplete")
                if rr[:20] != frozen[(qid,run,STAGE1_SYSTEM[method])]:
                    raise AssertionError(f"Frozen global Top20 mismatch {qid}/{run}/{method}")
                for pid,arr in br.items():
                    for pos,cid in enumerate(arr[:20],1):
                        d=definitions[(qid,run,pid)]
                        output_branches.append(dict(
                            query_id=qid,run_id=run,retrieval=method,perspective_id=pid,
                            perspective_title=d["perspective_title"],local_rank=pos,case_id=cid,
                            case_problem=texts["cases"][cid],
                            globally_merged_rank=(rr.index(cid)+1)))
                for k in KS:
                    global_ids=rr[:k]
                    perbranch={pid:arr[:k] for pid,arr in br.items()}
                    independent_ids=set().union(*(set(x) for x in perbranch.values()))
                    # Unions are sets; construct a deterministic list for audit.
                    independent_order=[cid for cid in rr if cid in independent_ids]
                    if set(global_ids)-set(rr):
                        raise AssertionError("Invalid global merge")
                    n=len(independent_ids)
                    original_single=frozen[(qid,0,SINGLE_SYSTEM[method])][:k]
                    # With N > 20, BM25 cannot be strictly matched from saved
                    # single rank top20, so use Single Dense@N consistently.
                    single_matched=single_dense[qid][:n]
                    global_matched=rr[:n]
                    selections={
                        "mp_global_fixed_k":global_ids,
                        "mp_separated_each_view_k":independent_order,
                        "single_fixed_k":original_single,
                        "single_dense_matched_unique_n":single_matched,
                        "mp_global_matched_unique_n":global_matched,
                    }
                    evaluated={}
                    for setting,ids in selections.items():
                        row=evaluate_record(qid,run,method,k,ids,labels,frozen)
                        row["setting"]=setting
                        row["effective_budget"]=len(ids)
                        metrics.append(row)
                        evaluated[setting]=row
                    single_recall = evaluated["single_fixed_k"]["recall"]
                    stage_recall = expected[(qid,run,STAGE1_SYSTEM[method],k)]
                    if abs(evaluated["mp_global_fixed_k"]["recall"]-stage_recall)>1e-12:
                        raise AssertionError("Frozen Stage1 MP recall mismatch")
                    baseline_replay.append((qid,run,method,k,stage_recall))
                    positives=set().union(*(s for s in labels[qid].values()))
                    gset=set(global_ids); iset=independent_ids; ssize=set(single_matched)
                    comparisons.append(dict(
                        query_id=qid,run_id=run,retrieval=method,k=k,perspective_count=len(br),
                        separated_budget_n=n,
                        global_recall=evaluated["mp_global_fixed_k"]["recall"],
                        separated_recall=evaluated["mp_separated_each_view_k"]["recall"],
                        single_fixed_k_recall=single_recall,
                        single_dense_budget_n_recall=evaluated["single_dense_matched_unique_n"]["recall"],
                        mp_global_budget_n_recall=evaluated["mp_global_matched_unique_n"]["recall"],
                        global_coverage=evaluated["mp_global_fixed_k"]["reference_view_coverage"],
                        separated_coverage=evaluated["mp_separated_each_view_k"]["reference_view_coverage"],
                        single_dense_matched_coverage=evaluated["single_dense_matched_unique_n"]["reference_view_coverage"],
                        gained_positive_vs_global=len((iset-gset)&positives),
                        lost_positive_vs_global=len((gset-iset)&positives),
                        extra_positive_vs_single_matched=len((iset-ssize)&positives),
                        missed_positive_vs_single_matched=len((ssize-iset)&positives)))
                # For k=10 loss taxonomy vs Single Dense@10, exactly the claim.
                if method=="dense":
                    positives=set().union(*(s for s in labels[qid].values()))
                    single10=set(single_dense[qid][:10]); mpglobal10=set(rr[:10])
                    sep10=set().union(*(set(arr[:10]) for arr in br.values()))
                    sep20=set().union(*(set(arr[:20]) for arr in br.values()))
                    for cid in sorted((single10-mpglobal10)&positives):
                        ranks={pid:(arr.index(cid)+1) for pid,arr in br.items()}
                        closest=min(ranks.values())
                        cat="within_branch_top10" if closest<=10 else "branch_rank_11_to_20" if closest<=20 else "beyond_branch_top20"
                        loss_rows.append(dict(
                            query_id=qid,run_id=run,case_id=cid,
                            query_text=texts["queries"][qid],case_problem=texts["cases"][cid],
                            single_dense_rank=single_dense[qid].index(cid)+1,
                            mp_global_full_rank=rr.index(cid)+1,
                            minimum_branch_dense_rank=closest,
                            minimum_branch_perspective=min(ranks,key=ranks.get),
                            branch_rank_details="|".join(f"{p}:{r}" for p,r in ranks.items()),
                            category=cat,
                            recovered_in_sep10=int(cid in sep10),
                            recovered_in_sep20=int(cid in sep20)))
    dense10=[r for r in comparisons if r["retrieval"]=="dense" and r["k"]==10]
    if len(dense10)!=30 or len(loss_rows)!=39:
        raise AssertionError(f"Unexpected Stage1 old errors count: dense10 {len(dense10)}, losses {len(loss_rows)}")
    if abs(mean(r["global_recall"] for r in dense10)-.4530)>0.0001:
        raise AssertionError("Original Dense MP macro Recall@10 mismatch")
    if abs(mean(r["single_fixed_k_recall"] for r in dense10)-.5332)>0.0001:
        raise AssertionError("Original Single Dense macro Recall@10 mismatch")

    charts=[]
    for method in METHODS:
        for k in KS:
            rows=[r for r in comparisons if r["retrieval"]==method and r["k"]==k]
            assert len(rows)==30
            charts.append(dict(
                retrieval=method,k=k,runs=30,
                avg_perspectives=mean(r["perspective_count"] for r in rows),
                mean_separated_unique_n=mean(r["separated_budget_n"] for r in rows),
                global_recall=mean(r["global_recall"] for r in rows),
                separated_recall=mean(r["separated_recall"] for r in rows),
                single_fixed_k_recall=mean(r["single_fixed_k_recall"] for r in rows),
                single_dense_budget_n_recall=mean(r["single_dense_budget_n_recall"] for r in rows),
                mp_global_budget_n_recall=mean(r["mp_global_budget_n_recall"] for r in rows),
                global_coverage=mean(r["global_coverage"] for r in rows),
                separated_coverage=mean(r["separated_coverage"] for r in rows),
                single_dense_matched_coverage=mean(r["single_dense_matched_coverage"] for r in rows),
                positive_new_vs_global_occurrences=sum(r["gained_positive_vs_global"] for r in rows),
                positive_lost_vs_global_occurrences=sum(r["lost_positive_vs_global"] for r in rows),
                positive_new_vs_single_dense_n_occurrences=sum(r["extra_positive_vs_single_matched"] for r in rows),
                positive_lost_vs_single_dense_n_occurrences=sum(r["missed_positive_vs_single_matched"] for r in rows),
                separated_better_than_single_n_runs=sum(r["separated_recall"]>r["single_dense_budget_n_recall"] for r in rows),
                separated_worse_than_single_n_runs=sum(r["separated_recall"]<r["single_dense_budget_n_recall"] for r in rows),
                separated_equal_to_single_n_runs=sum(r["separated_recall"]==r["single_dense_budget_n_recall"] for r in rows)))
    by_cat={cat:sum(1 for r in loss_rows if r["category"]==cat)
            for cat in ("within_branch_top10","branch_rank_11_to_20","beyond_branch_top20")}
    qid_cat=defaultdict(lambda:defaultdict(int))
    for r in loss_rows:
        qid_cat[r["query_id"]][r["category"]]+=1
    diagnostics=dict(
        cases=84,dev_queries=10,repetitions=3,generated_perspectives=97,
        retrievals=list(METHODS), k_values=list(KS),
        old_single_dense_at10_relevant_losses_count=len(loss_rows),
        lost_positive_breakdown_by_minimum_branch_rank=by_cat,
        recovered_by_separated_branch_top10=sum(int(r["recovered_in_sep10"]) for r in loss_rows),
        recovered_by_separated_branch_top20=sum(int(r["recovered_in_sep20"]) for r in loss_rows),
        query_loss_counts={q:dict(c) for q,c in sorted(qid_cat.items())},
        note="39 are query-run-case appearances in 30 MP runs, not distinct cases; AI-Silver Dev",
        checks={"original_global_top20_ranking_replayed":True,
                "original_stage1_all_mp_k_metrics_equal":True,
                "single_dense_full_order_matches_saved_top20":True,
                "runtime_perspective_count_matches":True})
    summary={
        "status":"SUCCESS_STAGE1_FROZEN_REANALYSIS",
        "question":"Does professor-recommended keeping per-view Top-K reduce global merge losses?",
        "methodology":"Frozen Stage1 per-branch Dense/BM25 reused; no new inference. Independent per-view TopK and equal-unique-budget controls.",
        "ground_truth":"AI_SILVER_DEV_NOT_INDEPENDENT_TEST",
        "original_dataset_frozen":True,
        "chart":charts,
        "loss_diagnostics":diagnostics,
    }
    OUT.mkdir(parents=True,exist_ok=True)
    csvwrite(OUT/"per_perspective_top20_source_rankings.csv",output_branches)
    csvwrite(OUT/"all_comparisons_by_query_run.csv",comparisons)
    csvwrite(OUT/"all_setting_metrics.csv",metrics)
    csvwrite(OUT/"old_global_top10_missing_single_relevant_cases.csv",loss_rows)
    (OUT/"summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("STAGE1_PERSPECTIVE_REANALYSIS_OK "+json.dumps(summary,ensure_ascii=False),flush=True)

if __name__=="__main__":
    main()
