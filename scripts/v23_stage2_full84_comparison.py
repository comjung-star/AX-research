#!/usr/bin/env python3
"""Frozen v2.3: full 84 AX cases per runtime perspective vs candidate pruning.

Every strategy uses the SAME scores/models, only admissible candidate IDs change.
Final outputs are PER-PERSPECTIVE, not early branch-balanced/global shortlists.
"""
from __future__ import annotations

import csv
import json
import math
import sys
from collections import OrderedDict, defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "experiments/v23_dev/stage1"
GT = ROOT / "data/v2_3/ground_truth/silver_dev_qrels_2520.csv"
OUT = ROOT / "experiments/v23_stage2_full84_comparison"

CASE_COUNT = 84
SEED = 42
K_VALUES = (5, 10)
CONFIGS = (
    "full84", "dense20", "dense40", "hybrid20_20",
    "dense_matched_hybrid_n", "sparse20_positive",
)
SCORERS = ("mlp", "dense_score", "rrf")


def readcsv(p: Path) -> list[dict]:
    with p.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def writecsv(p: Path, rows: list[dict]) -> None:
    if not rows:
        raise ValueError(f"empty rows for {p}")
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def build_pools(dense: list[str], sparse: list[tuple[str, float]]) -> dict[str, list[str]]:
    """Dense ranks the 84-case corpus; sparse only has valid lexical hits if BM25>0.

    Crucially, hybrid is a union, not replacing Dense20 with Sparse slots.
    """
    if len(dense) != CASE_COUNT or len(set(dense)) != CASE_COUNT:
        raise ValueError("dense not a complete unique 84-case ordering")
    if len(sparse) != CASE_COUNT or {cid for cid, _ in sparse} != set(dense):
        raise ValueError("sparse not a complete 84-case ordering")
    hits = [cid for cid, score in sparse if float(score) > 0]
    hyb = set(dense[:20]) | set(hits[:20])
    hyb_ids = [cid for cid in dense if cid in hyb]
    pools = {
        "full84": list(dense),
        "dense20": dense[:20],
        "dense40": dense[:40],
        "hybrid20_20": hyb_ids,
        "dense_matched_hybrid_n": dense[:len(hyb_ids)],
        "sparse20_positive": hits[:20],
    }
    if len(pools["dense_matched_hybrid_n"]) != len(pools["hybrid20_20"]):
        raise AssertionError("incorrect matched candidate budget")
    if not set(dense[:20]) <= set(pools["hybrid20_20"]):
        raise AssertionError("Hybrid dropped a Dense20 candidate")
    if len(set(pools["full84"])) != CASE_COUNT:
        raise AssertionError("incomplete full84 candidate universe")
    for name, pool in pools.items():
        if len(set(pool)) != len(pool) or not set(pool) <= set(dense):
            raise AssertionError(f"invalid pool {name}")
    return pools


def interaction_features(q: np.ndarray, docs: np.ndarray) -> np.ndarray:
    qq = np.broadcast_to(q[None, :], docs.shape)
    return np.concatenate([qq, docs, qq * docs, np.abs(qq - docs)], axis=1)


def train_loqo_model(
    held: str, query_ids: list[str], branch_keys: list[str],
    projected_queries: dict[str, np.ndarray], projected_cases: np.ndarray,
    case_ids: list[str], positive: dict[str, set[str]],
):
    """Copy the previously executed Stage2 diagnostic MLP, without retuning."""
    import torch
    from torch import nn
    torch.set_num_threads(2)
    torch.manual_seed(SEED)
    model = nn.Sequential(nn.Linear(192, 64), nn.ReLU(), nn.Linear(64, 1))
    xx, yy, train_qs = [], [], set()
    for key in branch_keys:
        q = key.split("|", 1)[0]
        if q == held:
            continue
        train_qs.add(q)
        xx.append(interaction_features(projected_queries[key], projected_cases))
        yy.extend(float(cid in positive[q]) for cid in case_ids)
    if train_qs != set(query_ids) - {held} or held in train_qs:
        raise AssertionError("training/held-query leakage")
    x = torch.tensor(np.concatenate(xx), dtype=torch.float32)
    y = torch.tensor(yy, dtype=torch.float32)
    pos = max(float(y.sum()), 1.0)
    neg = max(float(len(y) - y.sum()), 1.0)
    criterion = nn.BCEWithLogitsLoss(pos_weight=torch.tensor(neg / pos))
    optim = torch.optim.Adam(model.parameters(), lr=0.003, weight_decay=0.003)
    for _ in range(32):
        optim.zero_grad()
        loss = criterion(model(x).squeeze(-1), y)
        loss.backward()
        optim.step()
    model.eval()
    return model, sorted(train_qs), float(loss.item())


def ranking_for_pool(
    pool: list[str], scorer: str, scores: dict[str, dict[str, float]],
) -> list[str]:
    if scorer not in SCORERS:
        raise ValueError("invalid scorer")
    return sorted(pool, key=lambda cid: (-scores[cid][scorer], cid))


def precision_recall_and_coverage(
    chosen: set[str], reference: dict[str, set[str]],
) -> tuple[float, float, float, int]:
    groups = [cases for cases in reference.values() if cases]
    truth = set().union(*groups)
    if not groups or not truth:
        raise AssertionError("missing reference positives")
    good = len(chosen & truth)
    return good / len(truth), good / len(chosen) if chosen else 0.0, \
        sum(bool(chosen & cases) for cases in groups) / len(groups), good


def main():
    import torch
    expected = [
        SRC / "fixed_bge_m3_embeddings.npz",
        SRC / "branch_rankings.csv",
        SRC / "generated_runtime_perspectives.json",
        SRC / "rankings_top20.csv",
        GT,
    ]
    for p in expected:
        if not p.is_file():
            raise FileNotFoundError(str(p))
    npz = np.load(expected[0])
    cases = [str(x) for x in npz["case_ids"].tolist()]
    branch_keys = [str(x) for x in npz["branch_keys"].tolist()]
    qemb = npz["branch_embeddings"].astype(np.float32)
    docs = npz["document_embeddings"].astype(np.float32)
    if len(cases)!=CASE_COUNT or len(set(cases))!=CASE_COUNT:
        raise AssertionError("wrong case dimensions")
    if len(branch_keys)!=97 or len(set(branch_keys))!=97 or len(qemb)!=97:
        raise AssertionError("frozen generated perspective mismatch")
    idx = {case:i for i,case in enumerate(cases)}
    vectors = np.stack([npz["problem_embeddings"], npz["task_embeddings"],
                        npz["context_embeddings"]],axis=0)
    if vectors.shape[1:] != docs.shape:
        raise AssertionError("incorrect three-view case dimensions")
    generated=json.loads(expected[2].read_text(encoding="utf-8"))
    names={(p["query_id"],int(p["run_id"]),p["perspective_id"]):p["perspective_title"] for p in generated}
    if len(names)!=97:
        raise AssertionError("perspective label loss")
    sparse_rows=defaultdict(list)
    stage1_dense_rows=defaultdict(list)
    raw=readcsv(expected[1])
    if len(raw)!=97*2*84:
        raise AssertionError(f"incomplete prior raw branch ranking file {len(raw)}")
    for row in raw:
        key=f'{row["query_id"]}|{row["run_id"]}|{row["perspective_id"]}'
        tup=(int(row["local_rank"]),row["case_id"],float(row["score"]))
        if row["retrieval"]=="bm25":
            sparse_rows[key].append(tup)
        elif row["retrieval"]=="dense":
            stage1_dense_rows[key].append(tup)
        else:
            raise AssertionError("unexpected retrieval mode")
    labels_rows=readcsv(GT)
    if len(labels_rows)!=2520 or any(row["provenance"]!="AI_THREE_PASS_MEDIAN_NOT_HUMAN_GOLD" for row in labels_rows):
        raise AssertionError("frozen Silver judgements failed validation")
    ref=defaultdict(lambda:defaultdict(set))
    for row in labels_rows:
        ref[row["query_id"]][row["perspective_id"]] |= set()
        if int(row["relevance_0_4"])>=3:
            ref[row["query_id"]][row["perspective_id"]].add(row["case_id"])
    positive={qid:set().union(*d.values()) for qid,d in ref.items()}
    query_ids=sorted(positive)
    if len(query_ids)!=10 or any(not positive[q] for q in query_ids):
        raise AssertionError("expected ten positive Dev queries")
    original=list(readcsv(expected[3]))
    original_d=defaultdict(list)
    for row in original:
        if row["system"]=="mp_dense_bge_m3":
            original_d[(row["query_id"],int(row["run_id"]))].append(row)
    if len(original_d)!=30:
        raise AssertionError("original stage1 is incomplete")
    # Check original individual Stage1 single-document Dense ranks were
    # preserved so that source arrays are exact frozen rankings.
    branch_dense, branch_sparse, branch_score = {}, {}, {}
    for key, vec in zip(branch_keys,qemb):
        br=sorted(stage1_dense_rows[key])
        sp=sorted(sparse_rows[key])
        if [i for i,_,_ in br]!=list(range(1,85)) or [i for i,_,_ in sp]!=list(range(1,85)):
            raise AssertionError(f"missing branch ranks {key}")
        actual=[cid for _,cid,_ in br]
        single_scores=docs@vec
        rerank_single=[cases[i] for i in sorted(range(84),key=lambda i:(-float(single_scores[i]),cases[i]))]
        if actual[:20]!=rerank_single[:20]:
            raise AssertionError(f"frozen Stage1 per-branch dense mismatch: {key}")
        sp_list=[(cid,s) for _,cid,s in sp]
        view_scores=(vectors@vec).mean(axis=0)
        d_rank=[cases[i] for i in sorted(range(84),key=lambda i:(-float(view_scores[i]),cases[i]))]
        if set(d_rank)!=set(cid for cid,_ in sp_list):
            raise AssertionError("BM25 and Dense rank different case universes")
        sparse_ranks={cid:rank for rank,(cid,score) in enumerate(sp_list,1)}
        sparse_map=dict(sp_list)
        branch_dense[key]=d_rank
        branch_sparse[key]=sp_list
        # These scores are computed on full 84 and invariant across pruning strategies.
        branch_score[key]={
            cid:{"dense_score":float(view_scores[idx[cid]]),
                 "rrf":float(1/(60+d_rank.index(cid)+1)+(1/(60+sparse_ranks[cid]) if sparse_map[cid]>0 else 0)),
                 "bm25_score":float(sparse_map[cid]),
                 "dense_rank":int(d_rank.index(cid)+1),
                 "sparse_rank":int(sparse_ranks[cid]),
                 "sparse_positive":int(sparse_map[cid]>0)}
            for cid in cases}
    if len(branch_score)!=97:
        raise AssertionError("missing branch scores")

    rng=np.random.default_rng(SEED)
    dim=docs.shape[1]
    proj=rng.normal(0,1/math.sqrt(dim),size=(dim,48)).astype(np.float32)
    proj_cases=(docs@proj).astype(np.float32)
    proj_queries={k:(v@proj).astype(np.float32) for k,v in zip(branch_keys,qemb)}
    perspectives=defaultdict(list)
    for key in branch_keys:
        q,run,pid=key.split("|")
        perspectives[(q,int(run))].append(key)
    if len(perspectives)!=30 or sum(map(len,perspectives.values()))!=97:
        raise AssertionError("wrong number of runtime query-runs")
    candidate_by_run=[]
    output_by_run=[]
    perspective_rankings=[]
    candidate_provenance=[]
    loqo=[]
    for held in query_ids:
        model, trainqs, training_loss=train_loqo_model(
            held,query_ids,branch_keys,proj_queries,proj_cases,cases,positive)
        loqo.append(dict(held_query=held,training_queries="|".join(trainqs),
                         held_query_in_train=0,train_size_queries=len(trainqs),
                         final_train_loss=training_loss,seed=SEED))
        with torch.no_grad():
            for key in branch_keys:
                if not key.startswith(held+"|"):
                    continue
                features=interaction_features(proj_queries[key],proj_cases)
                mlp=model(torch.tensor(features,dtype=torch.float32)).squeeze(-1).numpy()
                for cid in cases:
                    branch_score[key][cid]["mlp"]=float(mlp[idx[cid]])
        for run in (1,2,3):
            pkeys=perspectives[(held,run)]
            if not 2<=len(pkeys)<=5:
                raise AssertionError("invalid perspective count")
            # Cache per-branch pools: the actual MLP is evaluated on 84 first, then
            # the same learned scores are restricted to admissible pool IDs.
            pools={key:build_pools(branch_dense[key],branch_sparse[key]) for key in pkeys}
            if any(len(pools[key]["full84"])!=84 for key in pkeys):
                raise AssertionError("full corpus not scored for a branch")
            truth=positive[held]
            for config in CONFIGS:
                pools_by_pid=OrderedDict()
                unique=set()
                total_pairs=0
                for key in pkeys:
                    pid=key.split("|")[2]
                    ids=pools[key][config]
                    pools_by_pid[pid]=(key,ids)
                    unique.update(ids)
                    total_pairs+=len(ids)
                    for cid in ids:
                        data=branch_score[key][cid]
                        evidence=("ALL" if config=="full84"
                                  else "BOTH" if cid in branch_dense[key][:20] and data["sparse_positive"] and data["sparse_rank"]<=20
                                  else "DENSE" if cid in branch_dense[key][:20]
                                  else "SPARSE" if data["sparse_positive"] else "DENSE_EXTENDED")
                        candidate_provenance.append(dict(
                            query_id=held,run_id=run,perspective_id=pid,
                            config=config,case_id=cid,source=evidence,
                            dense_rank=data["dense_rank"],sparse_rank=data["sparse_rank"],
                            bm25_score=data["bm25_score"],sparse_positive=data["sparse_positive"],
                            mlp_score=data["mlp"],dense_score=data["dense_score"],rrf_score=data["rrf"]))
                cand_recall=len(unique&truth)/len(truth)
                coverage=sum(bool(unique&group) for group in ref[held].values() if group)
                coverage/=len([g for g in ref[held].values() if g])
                candidate_by_run.append(dict(query_id=held,run_id=run,config=config,
                    runtime_perspectives=len(pkeys),total_84_reference_pairs=84*len(pkeys),
                    reranker_pairs=total_pairs,reduction_ratio=1-total_pairs/(84*len(pkeys)),
                    mean_branch_candidates=total_pairs/len(pkeys),unique_pool=len(unique),
                    silver_positive_count=len(truth),positive_in_pool=len(unique&truth),
                    candidate_recall=cand_recall,reference_coverage=coverage))
                for scorer in SCORERS:
                    branch_outputs={}
                    for pid,(key,ids) in pools_by_pid.items():
                        ordered=ranking_for_pool(ids,scorer,branch_score[key])
                        branch_outputs[pid]=ordered
                        for i,cid in enumerate(ordered[:max(K_VALUES)],1):
                            data=branch_score[key][cid]
                            perspective_rankings.append(dict(
                                query_id=held,run_id=run,config=config,scorer=scorer,
                                perspective_id=pid,perspective_title=names[(held,run,pid)],
                                rank=i,case_id=cid,mlp_score=data["mlp"],
                                dense_score=data["dense_score"],rrf_score=data["rrf"],
                                dense_rank=data["dense_rank"],sparse_rank=data["sparse_rank"],
                                bm25_score=data["bm25_score"]))
                    for k in K_VALUES:
                        selected=set().union(*(set(o[:k]) for o in branch_outputs.values()))
                        recall,prec,viewcov,nrel=precision_recall_and_coverage(selected,ref[held])
                        output_by_run.append(dict(
                            query_id=held,run_id=run,config=config,scorer=scorer,k=k,
                            runtime_perspectives=len(pkeys),branch_candidates=total_pairs,
                            unique_output_count=len(selected),output_positive=nrel,
                            silver_positive_total=len(truth),recall=recall,
                            precision=prec,reference_coverage=viewcov,
                            candidate_recall=cand_recall,
                            within_pool_output_recall=nrel/len(unique&truth) if unique&truth else 0,
                            positive_not_in_pool=len(truth-unique),
                            positive_in_pool_not_topk=len((unique&truth)-selected)))
    # Side-by-side paired gains/losses for identical query/run/scorer/k.
    choices=defaultdict(set)
    for r in perspective_rankings:
        choices[(r["query_id"],int(r["run_id"]),r["config"],r["scorer"],int(r["rank"]))].add(r["case_id"])
    outputs_grouped=defaultdict(lambda:defaultdict(list))
    for r in perspective_rankings:
        outputs_grouped[(r["query_id"],int(r["run_id"]),r["config"],r["scorer"])][r["perspective_id"]].append((int(r["rank"]),r["case_id"]))
    comparison=[]
    for row in output_by_run:
        q,run,config,scorer,k=row["query_id"],row["run_id"],row["config"],row["scorer"],row["k"]
        mine=set(cid for ranks in outputs_grouped[(q,run,config,scorer)].values()
                 for rank,cid in ranks if rank<=k)
        full=set(cid for ranks in outputs_grouped[(q,run,"full84",scorer)].values()
                 for rank,cid in ranks if rank<=k)
        positives=positive[q]
        comparison.append(dict(query_id=q,run_id=run,config=config,scorer=scorer,k=k,
            new_positive_not_in_full=len((mine-full)&positives),
            lost_positive_from_full=len((full-mine)&positives),
            unchanged_positive=len((mine&full)&positives),
            change_recall=(len(mine&positives)-len(full&positives))/len(positives)))
    for row in output_by_run:
        c=next(r for r in comparison if
               (r["query_id"],r["run_id"],r["config"],r["scorer"],r["k"])==
               (row["query_id"],row["run_id"],row["config"],row["scorer"],row["k"]))
        row["new_positive_vs_full84"]=c["new_positive_not_in_full"]
        row["lost_positive_vs_full84"]=c["lost_positive_from_full"]
        row["recall_delta_vs_full84"]=c["change_recall"]
    # Exact matched-cost and original-case verification.
    cost={(r["query_id"],int(r["run_id"]),r["config"]):int(r["reranker_pairs"])
          for r in candidate_by_run}
    for q in query_ids:
        for run in (1,2,3):
            assert cost[(q,run,"hybrid20_20")]==cost[(q,run,"dense_matched_hybrid_n")]
            assert cost[(q,run,"full84")]==84*len(perspectives[(q,run)])
    if len(output_by_run)!=30*len(CONFIGS)*len(SCORERS)*len(K_VALUES):
        raise AssertionError("incorrect output metrics rows")
    if any(r["candidate_recall"]!=1 for r in candidate_by_run if r["config"]=="full84"):
        raise AssertionError("full84 must cover all reference positives")

    writecsv(OUT/"per_perspective_topk.csv",perspective_rankings)
    writecsv(OUT/"candidate_provenance.csv",candidate_provenance)
    writecsv(OUT/"candidate_metrics_by_query_run.csv",candidate_by_run)
    writecsv(OUT/"final_topk_metrics_by_query_run.csv",output_by_run)
    writecsv(OUT/"full84_final_ranking_delta.csv",comparison)
    writecsv(OUT/"loqo_training_audit.csv",loqo)
    summary={"status":"SUCCESS_REAL_FROZEN_V23_DEV_REPLAY", "corpus_cases":84,
       "queries":10,"repetitions":3,"generated_runtime_perspectives":97,
       "training":"query-level Leave-One-Query-Out 9 of 10, BCE, original MLP architecture",
       "gt":"AI_SILVER_DEV_NOT_INDEPENDENT_GOLD_TEST",
       "stage_scope":"Search Core candidate→Query-Case Interaction→per-perspective topK; not Stage3/Stage4",
       "gate":"frozen equal-mean three-view Dense; learned gate not tested",
       "sparse":"Kiwi BM25 score>0 only counts as lexical hit",
       "scorers":list(SCORERS),"configs":list(CONFIGS),"k_values":list(K_VALUES),
       "table":[],"checks":{"full84_all_queries_candidate_recall_1":True,
                              "hybrid_all_dense_top20_retained":True,
                              "query_loqo_no_leakage":True,
                              "matched_per_branch_candidate_cost":True,
                              "original_stage1_single_dense_branch_replay":True}}
    for cfg in CONFIGS:
        c=[r for r in candidate_by_run if r["config"]==cfg]
        section={"config":cfg,"mean_reranker_pairs":float(np.mean([r["reranker_pairs"] for r in c])),
                 "mean_unique_pool":float(np.mean([r["unique_pool"] for r in c])),
                 "candidate_recall":float(np.mean([r["candidate_recall"] for r in c])),
                 "mean_reduction_vs_all84":float(np.mean([r["reduction_ratio"] for r in c]))}
        for scorer in SCORERS:
            for k in K_VALUES:
                rows=[r for r in output_by_run if r["config"]==cfg and r["scorer"]==scorer and r["k"]==k]
                if len(rows)!=30:
                    raise AssertionError("wrong row subgroup count")
                section[f"{scorer}_k{k}"]={
                    "macro_recall":float(np.mean([r["recall"] for r in rows])),
                    "macro_precision":float(np.mean([r["precision"] for r in rows])),
                    "mean_unique_output":float(np.mean([r["unique_output_count"] for r in rows])),
                    "macro_view_coverage":float(np.mean([r["reference_coverage"] for r in rows])),
                    "positive_added_vs_full84_appearances":int(sum(r["new_positive_vs_full84"] for r in rows)),
                    "positive_lost_vs_full84_appearances":int(sum(r["lost_positive_vs_full84"] for r in rows)),
                    "mean_recall_delta_vs_full84":float(np.mean([r["recall_delta_vs_full84"] for r in rows])),
                }
        summary["table"].append(section)
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("STAGE2_FULL84_CANDIDATE_COMPARE_OK "+json.dumps(summary,ensure_ascii=False),flush=True)

if __name__=="__main__":
    main()
