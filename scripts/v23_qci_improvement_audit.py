#!/usr/bin/env python3
"""Dev diagnostic: QCI label mismatch, full-vector ablation, dense-anchored pairwise ranking.

Frozen artifacts only. Per-runtime-perspective outputs, no premature global Top-K.
Human independent Test/Gold NOT provided.
"""
from __future__ import annotations

import csv
import json
import math
from collections import defaultdict, OrderedDict
from pathlib import Path

import numpy as np

from scripts.v23_stage2_full84_comparison import (
    build_pools, interaction_features, precision_recall_and_coverage,
    train_loqo_model,
)

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "experiments/v23_dev/stage1"
QRELS = ROOT / "data/v2_3/ground_truth/silver_dev_qrels_2520.csv"
OUT = ROOT / "experiments/v23_qci_improvement_audit"
SEED = 42
KS = (5, 10)
SCORERS = (
    "dense_3view", "legacy_48_pooled", "fullvec_pooled",
    "legacy_48_pseudoview", "anchor_pairwise_010", "anchor_pairwise_025",
)
POOLS = ("full84", "dense20", "hybrid20_20")


def csvread(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def csvwrite(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise ValueError(f"Empty output: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        w = csv.DictWriter(stream, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def view_centroids(
    reference: dict[str, dict[str, set[str]]],
    qid: str, doc_vectors: np.ndarray, idx: dict[str, int],
) -> dict[str, np.ndarray]:
    centroids = {}
    for ref_id, case_set in reference[qid].items():
        if not case_set:
            continue
        mean = doc_vectors[[idx[cid] for cid in sorted(case_set)]].mean(axis=0)
        magnitude = np.linalg.norm(mean)
        if magnitude > 1.e-8:
            centroids[ref_id] = mean / magnitude
    if not centroids:
        raise AssertionError("Zero reference centroids for " + qid)
    return centroids


def map_runtime_to_reference(
    qvec: np.ndarray, ref_centroids: dict[str, np.ndarray],
) -> tuple[str, float, float]:
    scores = sorted(((float(qvec @ vec),rid) for rid,vec in ref_centroids.items()),
                    key=lambda z: (-z[0],z[1]))
    best_score, selected = scores[0]
    second = scores[1][0] if len(scores)>1 else float("nan")
    return selected, best_score, best_score-second


def label_audit(reference: dict[str, dict[str,set[str]]]) -> list[dict]:
    rows=[]
    for q in sorted(reference):
        views=reference[q]
        vals=list(views.values())
        if len(vals)!=3:
            raise AssertionError("Expected 3 fixed reference perspectives")
        pos = set().union(*vals)
        exclusive=sum(sum(cid in s for s in vals)==1 for cid in pos)
        double=sum(sum(cid in s for s in vals)==2 for cid in pos)
        triple=sum(sum(cid in s for s in vals)==3 for cid in pos)
        pair_ji=[]
        for i in range(3):
            for j in range(i+1,3):
                union=vals[i]|vals[j]
                if union:
                    pair_ji.append(len(vals[i]&vals[j])/len(union))
        rows.append(dict(query_id=q,positive_union=len(pos),
            positive_only_one_reference_view=exclusive,
            positive_two_reference_views=double,
            positive_all_three_reference_views=triple,
            fraction_positive_not_shared_all_views=(exclusive+double)/len(pos),
            pairwise_ref_positive_jaccard_avg=float(np.mean(pair_ji)),
            ref_positive_sizes="|".join(str(len(s)) for s in vals)))
    return rows


def train_pseudo_mlp(
    held: str, queries: list[str], keys: list[str],
    projected_queries: dict, projected_docs: np.ndarray,
    case_ids: list[str], per_branch_labels: dict[str, set[str]],
):
    """Use exactly legacy 48D architecture, only TRAIN targets differ."""
    import torch
    from torch import nn
    torch.set_num_threads(2)
    torch.manual_seed(SEED)
    m = nn.Sequential(nn.Linear(192,64), nn.ReLU(), nn.Linear(64,1))
    xx, yy, training_qs = [], [], set()
    for key in keys:
        q=key.split("|",1)[0]
        if q==held:
            continue
        training_qs.add(q)
        xx.append(interaction_features(projected_queries[key], projected_docs))
        yy.extend(float(cid in per_branch_labels[key]) for cid in case_ids)
    if training_qs!=set(queries)-{held}:
        raise AssertionError("LOQO pseudo labels leakage")
    x=torch.tensor(np.concatenate(xx),dtype=torch.float32)
    y=torch.tensor(yy,dtype=torch.float32)
    npos=max(float(y.sum()),1.)
    nneg=max(float(len(y)-y.sum()),1.)
    criterion=nn.BCEWithLogitsLoss(pos_weight=torch.tensor(nneg/npos))
    optim=torch.optim.Adam(m.parameters(),lr=.003,weight_decay=.003)
    for epoch in range(32):
        optim.zero_grad()
        loss=criterion(m(x).squeeze(-1),y)
        loss.backward()
        optim.step()
    m.eval()
    return m, sorted(training_qs),float(loss.item())


def train_fullvec_pooled(
    held: str, queries: list[str], keys: list[str],
    embeddings: dict[str,np.ndarray], documents: np.ndarray,
    case_ids: list[str], positive: dict[str,set[str]],
):
    """Identical BCE MLP architecture to 48D, but keep full BGE-M3 dimensions."""
    import torch
    from torch import nn
    torch.set_num_threads(2)
    torch.manual_seed(SEED)
    d=int(documents.shape[1])
    m=nn.Sequential(nn.Linear(4*d,64),nn.ReLU(),nn.Linear(64,1))
    feats, labs, used=[],[],set()
    for key in keys:
        q=key.split("|",1)[0]
        if q==held:
            continue
        used.add(q)
        feats.append(interaction_features(embeddings[key],documents))
        labs.extend(float(cid in positive[q]) for cid in case_ids)
    if used!=set(queries)-{held}:
        raise AssertionError("fullvec train leakage")
    x=torch.tensor(np.concatenate(feats),dtype=torch.float32)
    y=torch.tensor(labs,dtype=torch.float32)
    pos=max(float(y.sum()),1.)
    neg=max(float(len(y)-y.sum()),1.)
    criterion=nn.BCEWithLogitsLoss(pos_weight=torch.tensor(neg/pos))
    opt=torch.optim.Adam(m.parameters(),lr=.003,weight_decay=.003)
    for epoch in range(32):
        opt.zero_grad()
        loss=criterion(m(x).squeeze(-1),y)
        loss.backward()
        opt.step()
    m.eval()
    return m,sorted(used),float(loss.item())


def pairwise_features(
    view_sims: np.ndarray, bm25_ranks: dict[str,int],
    bm25_scores: dict[str,float], cases: list[str],
) -> np.ndarray:
    """3 frozen view sims + sparse positive reciprocal-rank + match indicator."""
    sparse_rr=np.asarray([
        60/(60+bm25_ranks[cid]) if bm25_scores[cid]>0 else 0.0 for cid in cases
    ],dtype=np.float32)
    sparse_hit=np.asarray([1. if bm25_scores[cid]>0 else 0. for cid in cases],
                          dtype=np.float32)
    return np.column_stack([view_sims.T,sparse_rr,sparse_hit]).astype(np.float32)


def train_pairwise_anchor(
    held: str, queries: list[str], keys: list[str],
    features: dict[str,np.ndarray], scores: dict[str,np.ndarray],
    case_ids: list[str], positive: dict[str,set[str]],
):
    """RankNet (positive vs negative). Dense anchor plus trainable small residual.

    Fixed negative-pair sampling; no held query positives in sampling/loss.
    """
    import torch
    from torch import nn
    torch.set_num_threads(2)
    torch.manual_seed(SEED)
    rng=np.random.default_rng(SEED)
    idx={cid:i for i,cid in enumerate(case_ids)}
    x,base,pos_idx,neg_idx=[],[],[],[]
    offset=0
    used=set()
    for key in keys:
        q=key.split("|",1)[0]
        if q==held:
            continue
        used.add(q)
        positives=[idx[cid] for cid in case_ids if cid in positive[q]]
        negatives=[idx[cid] for cid in case_ids if cid not in positive[q]]
        if not positives or not negatives:
            raise AssertionError("Cannot sample positive-negative pairs")
        x.append(features[key])
        base.append(scores[key])
        for p in positives:
            # 3 negatives per positive, deterministic, per training branch.
            selected = rng.choice(negatives, size=3, replace=False)
            for n in selected:
                pos_idx.append(offset+p)
                neg_idx.append(offset+int(n))
        offset+=84
    if used!=set(queries)-{held}:
        raise AssertionError("Pairwise held query leakage")
    feats=torch.tensor(np.concatenate(x),dtype=torch.float32)
    dense=torch.tensor(np.concatenate(base),dtype=torch.float32)
    p=torch.tensor(pos_idx,dtype=torch.long)
    n=torch.tensor(neg_idx,dtype=torch.long)
    model=nn.Linear(5,1)
    with torch.no_grad():
        model.weight.zero_()
        model.bias.zero_()
    opt=torch.optim.Adam(model.parameters(),lr=.01)
    for epoch in range(80):
        opt.zero_grad()
        residual=torch.tanh(model(feats).squeeze(-1))
        # Train residual with fixed alpha=.10; alternate alpha=.25 on same model.
        rank_scores=dense+.10*residual
        loss=torch.nn.functional.softplus(-10*(rank_scores[p]-rank_scores[n])).mean()
        loss=loss+.01*torch.sum(model.weight**2)
        loss.backward()
        opt.step()
    model.eval()
    return model, sorted(used), float(loss.item()),len(pos_idx)


def main():
    import torch
    files=[SRC/"fixed_bge_m3_embeddings.npz",SRC/"branch_rankings.csv",
           SRC/"generated_runtime_perspectives.json", QRELS]
    for f in files:
        if not f.is_file():
            raise FileNotFoundError(str(f))
    z=np.load(files[0],allow_pickle=False)
    cases=[str(cid) for cid in z["case_ids"].tolist()]
    keys=[str(x) for x in z["branch_keys"].tolist()]
    docs=z["document_embeddings"].astype(np.float32)
    emb=z["branch_embeddings"].astype(np.float32)
    case_by_id={cid:i for i,cid in enumerate(cases)}
    if len(cases)!=84 or len(set(cases))!=84 or len(keys)!=97 or len(set(keys))!=97:
        raise AssertionError("Dataset not frozen at 84/97")
    dim=docs.shape[1]
    if dim!=1024:
        raise AssertionError(f"Expected full 1024-dimensional frozen BGE, got {dim}")
    kv={key:v for key,v in zip(keys,emb)}
    views=np.stack([z["problem_embeddings"],z["task_embeddings"],
                    z["context_embeddings"]],axis=0).astype(np.float32)
    if views.shape!=(3,84,dim):
        raise AssertionError("Unexpected frozen view dimensions")
    silver=csvread(QRELS)
    if len(silver)!=2520 or any(row["provenance"]!="AI_THREE_PASS_MEDIAN_NOT_HUMAN_GOLD" for row in silver):
        raise AssertionError("Qrels changed")
    ref=defaultdict(lambda:defaultdict(set))
    for r in silver:
        ref[r["query_id"]][r["perspective_id"]]|=set()
        if int(r["relevance_0_4"])>=3:
            ref[r["query_id"]][r["perspective_id"]].add(r["case_id"])
    pos={q:set().union(*groups.values()) for q,groups in ref.items()}
    queries=sorted(pos)
    if len(queries)!=10:
        raise AssertionError("Expected 10 Dev queries")
    audit=label_audit(ref)
    names={(p["query_id"],int(p["run_id"]),p["perspective_id"]):p["perspective_title"]
           for p in json.loads(files[2].read_text(encoding="utf-8"))}
    if len(names)!=97:
        raise AssertionError("Runtime perspective file not aligned")
    rs=defaultdict(list)
    for row in csvread(files[1]):
        if row["retrieval"]=="bm25":
            key=f'{row["query_id"]}|{row["run_id"]}|{row["perspective_id"]}'
            rs[key].append((int(row["local_rank"]),row["case_id"],float(row["score"])))
    if len(rs)!=97:
        raise AssertionError("Missing sparse branch")
    rng=np.random.default_rng(SEED)
    projection=rng.normal(0,1/math.sqrt(dim),size=(dim,48)).astype(np.float32)
    proj_docs=(docs@projection).astype(np.float32)
    proj_q={key:(v@projection).astype(np.float32) for key,v in kv.items()}
    center={q:view_centroids(ref,q,docs,case_by_id) for q in queries}
    pseudo_labels={}
    alignment=[]
    base_score={}
    f_pair={}
    pools={}
    for key in keys:
        q,run,pid=key.split("|")
        mapped,similarity,margin=map_runtime_to_reference(kv[key],center[q])
        pseudo_labels[key]=ref[q][mapped]
        alignment.append(dict(query_id=q,run_id=run,runtime_perspective=pid,
                              runtime_title=names[(q,int(run),pid)],
                              mapped_reference_perspective=mapped,
                              centroid_cosine=similarity,nearest_margin=margin,
                              pooled_positive_count=len(pos[q]),
                              mapped_positive_count=len(pseudo_labels[key]),
                              no_human_verification=1))
        view_sim=(views@kv[key]).astype(np.float32)
        dense_mean=view_sim.mean(axis=0)
        d_rank=[cases[i] for i in sorted(range(84),key=lambda i:(-float(dense_mean[i]),cases[i]))]
        rows=sorted(rs[key])
        if [r for r,cid,sc in rows]!=list(range(1,85)):
            raise AssertionError(f"BM25 not complete: {key}")
        srank={cid:i+1 for i,cid in enumerate([cid for rk,cid,score in rows])}
        sparse_scores={cid:score for rk,cid,score in rows}
        f_pair[key]=pairwise_features(view_sim,srank,sparse_scores,cases)
        base_score[key]=dense_mean
        slist=[(cid,score) for _,cid,score in rows]
        raw_pools=build_pools(d_rank,slist)
        pools[key]={mode:raw_pools[mode] for mode in POOLS}
    if len(alignment)!=97:
        raise AssertionError("missing pseudo alignment audit")
    groups=defaultdict(list)
    for key in keys:
        q,run,pid=key.split("|")
        groups[(q,int(run))].append(key)
    if len(groups)!=30:
        raise AssertionError("expected 30 query runs")
    training_audit=[]
    candidate_metrics=[]
    outcomes=[]
    rankings=[]
    for held in queries:
        legacy,train_legacy,loss_legacy=train_loqo_model(
            held,queries,keys,proj_q,proj_docs,cases,pos)
        full,train_full,loss_full=train_fullvec_pooled(
            held,queries,keys,kv,docs,cases,pos)
        pseudo,train_pseudo,loss_pseudo=train_pseudo_mlp(
            held,queries,keys,proj_q,proj_docs,cases,pseudo_labels)
        pair,train_pair,loss_pair,n_pairs=train_pairwise_anchor(
            held,queries,keys,f_pair,base_score,cases,pos)
        trainsets=[train_legacy,train_full,train_pseudo,train_pair]
        if any(set(s)!=set(queries)-{held} for s in trainsets):
            raise AssertionError("held-out query leaked into training")
        training_audit.append(dict(held_out_query=held,training_queries="|".join(train_legacy),
            legacy_loss=loss_legacy,fullvec_loss=loss_full,pseudoview_loss=loss_pseudo,
            pairwise_loss=loss_pair,ranknet_training_pairs=n_pairs))
        all_scores={}
        with torch.no_grad():
            for key in keys:
                if key.split("|",1)[0]!=held:
                    continue
                feats48=torch.tensor(interaction_features(proj_q[key],proj_docs),
                                     dtype=torch.float32)
                featsfull=torch.tensor(interaction_features(kv[key],docs),
                                       dtype=torch.float32)
                feat_pair=torch.tensor(f_pair[key],dtype=torch.float32)
                residual=torch.tanh(pair(feat_pair).squeeze(-1)).numpy()
                all_scores[key]={
                    "dense_3view":base_score[key],
                    "legacy_48_pooled":legacy(feats48).squeeze(-1).numpy(),
                    "fullvec_pooled":full(featsfull).squeeze(-1).numpy(),
                    "legacy_48_pseudoview":pseudo(feats48).squeeze(-1).numpy(),
                    "anchor_pairwise_010":base_score[key]+.10*residual,
                    "anchor_pairwise_025":base_score[key]+.25*residual,
                }
        for run in (1,2,3):
            pkeys=groups[(held,run)]
            if not 2<=len(pkeys)<=5:
                raise AssertionError("Bad runtime perspective count")
            for poolname in POOLS:
                pool_union=set().union(*(set(pools[key][poolname]) for key in pkeys))
                total_pairs=sum(len(pools[key][poolname]) for key in pkeys)
                truth=pos[held]
                candidate_metrics.append(dict(query_id=held,run_id=run,pool=poolname,
                    generated_perspectives=len(pkeys),eval_pairs=total_pairs,
                    unique_pool_size=len(pool_union),candidate_recall=len(pool_union&truth)/len(truth)))
                for scorer in SCORERS:
                    branch_outputs=[]
                    for key in pkeys:
                        p=key.split("|")[2]
                        values=all_scores[key][scorer]
                        eligible=pools[key][poolname]
                        ordered=sorted(eligible,key=lambda cid:(-float(values[case_by_id[cid]]),cid))
                        branch_outputs.append(ordered)
                        for rk,cid in enumerate(ordered[:10],1):
                            rankings.append(dict(query_id=held,run_id=run,
                                runtime_perspective=p,runtime_title=names[(held,run,p)],
                                pool=poolname,scorer=scorer,local_rank=rk,
                                case_id=cid,score=float(values[case_by_id[cid]]),
                                is_silver_union_positive=int(cid in pos[held])))
                    for k in KS:
                        selected=set().union(*(set(v[:k]) for v in branch_outputs))
                        recall,precision,coverage,got=precision_recall_and_coverage(
                            selected,ref[held])
                        outcomes.append(dict(query_id=held,run_id=run,pool=poolname,
                            scorer=scorer,k=k,unique_final_cases=len(selected),
                            silver_positive_found=got,silver_positive_total=len(truth),
                            recall=recall,precision=precision,reference_view_coverage=coverage,
                            candidate_recall=len(pool_union&truth)/len(truth),
                            eval_pairs=total_pairs))
    # Non-negotiable reproduction check before any interpretation.
    for scorer,expected in (("legacy_48_pooled",0.09710763093116034),
                            ("dense_3view",0.6331669637551992)):
        matching=[row["recall"] for row in outcomes if
                  row["pool"]=="full84" and row["scorer"]==scorer and row["k"]==10]
        if len(matching)!=30 or abs(float(np.mean(matching))-expected)>1e-6:
            raise AssertionError(f"Baseline full84 replay mismatch: {scorer}={np.mean(matching)}")
    if len(outcomes)!=30*len(POOLS)*len(SCORERS)*len(KS):
        raise AssertionError("Incomplete output records")
    summary={
        "status":"ACTUAL_QCI_IMPROVEMENT_AUDIT_EXECUTED",
        "data":"84 frozen AX cases, 10 Dev queries x3, 97 LLM runtime perspectives",
        "silver":"DEV_AI_SILVER_NOT_HUMAN_GOLD",
        "fixed_frozen_previous_results":True,
        "scorers":list(SCORERS),"candidate_pools":list(POOLS),"k_values":list(KS),
        "candidate_pool_table":[],
        "performance_table":[],
        "label_audit":{
            "mean_unshared_positive_fraction":float(np.mean([r["fraction_positive_not_shared_all_views"] for r in audit])),
            "mean_reference_jaccard":float(np.mean([r["pairwise_ref_positive_jaccard_avg"] for r in audit])),
            "total_unique_to_single_reference_view":int(sum(r["positive_only_one_reference_view"] for r in audit)),
            "total_positive_view_twice":int(sum(r["positive_two_reference_views"] for r in audit)),
            "total_positive_all_three":int(sum(r["positive_all_three_reference_views"] for r in audit)),
            "alignment_mean_cosine":float(np.mean([r["centroid_cosine"] for r in alignment])),
            "alignment_mean_margin_excluding_missing":float(np.mean([r["nearest_margin"] for r in alignment if not math.isnan(r["nearest_margin"])])),
        },
        "checks":{"legacy_48_full84_original_9p71_reproduced":True,
                  "dense_full84_original_63p32_reproduced":True,
                  "loqo_query_holdout_10fold":True,
                  "all_97_branches_evaluated":True,
                  "same_scoring_model_for_each_candidate_pool":True,
                  "runtime_views_not_equated_to_reference_by_id":True},
    }
    for pool in POOLS:
        c=[row for row in candidate_metrics if row["pool"]==pool]
        summary["candidate_pool_table"].append(dict(pool=pool,
            mean_eval_pairs=float(np.mean([r["eval_pairs"] for r in c])),
            mean_unique_cases=float(np.mean([r["unique_pool_size"] for r in c])),
            macro_candidate_recall=float(np.mean([r["candidate_recall"] for r in c]))))
        for scorer in SCORERS:
            for k in KS:
                sub=[r for r in outcomes if r["pool"]==pool
                     and r["scorer"]==scorer and r["k"]==k]
                if len(sub)!=30:
                    raise AssertionError("Expected 30 query-run outcomes")
                summary["performance_table"].append(dict(pool=pool,scorer=scorer,k=k,
                   macro_recall=float(np.mean([r["recall"] for r in sub])),
                   macro_precision=float(np.mean([r["precision"] for r in sub])),
                   mean_unique_final_cases=float(np.mean([r["unique_final_cases"] for r in sub])),
                   macro_reference_view_coverage=float(np.mean([r["reference_view_coverage"] for r in sub]))))
    csvwrite(OUT/"silver_reference_label_audit.csv",audit)
    csvwrite(OUT/"runtime_pseudo_reference_view_mapping.csv",alignment)
    csvwrite(OUT/"train_holdout_audit.csv",training_audit)
    csvwrite(OUT/"candidate_pool_metrics.csv",candidate_metrics)
    csvwrite(OUT/"model_metrics_by_query_run.csv",outcomes)
    csvwrite(OUT/"per_perspective_top10_rankings.csv",rankings)
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("QCI_IMPROVEMENT_AUDIT_SUCCESS "+json.dumps(summary,ensure_ascii=False),flush=True)


if __name__=="__main__":
    main()
