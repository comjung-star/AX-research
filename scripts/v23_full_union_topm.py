#!/usr/bin/env python3
"""Exploratory interpretation: UNION full Dense and positive BM25 results THEN select Top-M.

Frozen v2.3 84-case dataset, 97 runtime perspectives, no new LLM/embedding calls.
Source architecture: docs/research-plan.md 4.2. Does NOT modify frozen experiments.
"""
from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict, OrderedDict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.v23_professor_hybrid_preserving import (
    ROOT, SRC, GT, SEED, CASE_COUNT, load_csv, write_csv,
    branch_balanced, interaction_features, train_model,
)

OUT = ROOT / "experiments/v23_full_union_topm"
METHODS = ("dense", "rrf", "interleave")
MS = (10, 20, 40, 60, 84)
KS = (5, 10, 20)


def full_union(dense_order: list[str], sparse_rows: list[tuple[str, float]]) -> list[dict]:
    """Combine the entire search ranking before any candidate count restriction.

    A BM25 zero-score row carries no real lexical match; it cannot boost rank.
    """
    if len(dense_order) != CASE_COUNT or len(sparse_rows) != CASE_COUNT:
        raise ValueError("Incomplete full search results")
    dense_ids = set(dense_order)
    sparse_ids = {cid for cid, _ in sparse_rows}
    if len(dense_ids) != CASE_COUNT or len(sparse_ids) != CASE_COUNT:
        raise ValueError("Duplicate case IDs in complete rankings")
    if dense_ids != sparse_ids:
        raise ValueError("Dense and BM25 did not cover the same frozen 84 cases")
    dense_rank = {case: i + 1 for i, case in enumerate(dense_order)}
    sparse_rank = {case: i + 1 for i, (case, _) in enumerate(sparse_rows)}
    sparse_score = {case: float(score) for case, score in sparse_rows}
    out = []
    for cid in sorted(dense_ids):
        hit = sparse_score[cid] > 0.0
        dr, sr = dense_rank[cid], sparse_rank[cid]
        score = 1.0 / (60 + dr) + (1.0 / (60 + sr) if hit else 0.0)
        out.append(dict(case_id=cid, dense_rank=dr,
                        sparse_rank=sr, bm25_score=sparse_score[cid],
                        sparse_hit=int(hit),
                        rrf_score=score, source="BOTH" if hit else "DENSE"))
    return out


def select_top_m(union: list[dict], method: str, m: int) -> list[dict]:
    """Select M *after* union; no GT, no early per-retriever TopN cutoff."""
    if method not in METHODS:
        raise ValueError("Unknown method")
    if not 1 <= m <= len(union):
        raise ValueError("Bad M")
    by_id = {r["case_id"]: r for r in union}
    if len(by_id) != len(union):
        raise AssertionError("Non-unique union")
    dense = sorted(union, key=lambda r: (r["dense_rank"], r["case_id"]))
    sparse = sorted(
        (r for r in union if r["sparse_hit"]),
        key=lambda r: (r["sparse_rank"], r["case_id"]))
    if method == "dense":
        ordered = dense
    elif method == "rrf":
        ordered = sorted(union, key=lambda r:
                         (-r["rrf_score"], r["dense_rank"], r["case_id"]))
    else:
        ids = []
        seen = set()
        pos_d, pos_s, turn = 0, 0, 0
        while len(ids) < len(union):
            order = dense if turn % 2 == 0 else sparse
            pos = pos_d if turn % 2 == 0 else pos_s
            while pos < len(order) and order[pos]["case_id"] in seen:
                pos += 1
            if turn % 2 == 0:
                pos_d = pos
            else:
                pos_s = pos
            if pos >= len(order):
                # Sparse can run out of true matches; fill from Dense.
                order = dense
                pos = pos_d
                while pos < len(order) and order[pos]["case_id"] in seen:
                    pos += 1
                pos_d = pos
                if pos >= len(order):
                    break
                ids.append(order[pos]["case_id"])
                seen.add(order[pos]["case_id"])
                pos_d += 1
            else:
                ids.append(order[pos]["case_id"])
                seen.add(order[pos]["case_id"])
                if turn % 2 == 0:
                    pos_d += 1
                else:
                    pos_s += 1
            turn += 1
        ordered = [by_id[c] for c in ids]
    selected = ordered[:m]
    if len(selected) != m or len({r["case_id"] for r in selected}) != m:
        raise AssertionError("Top-M failed")
    if m == CASE_COUNT and {r["case_id"] for r in selected} != set(by_id):
        raise AssertionError("M=84 must preserve entire corpus")
    return selected


def rerank(selected: list[dict], scorer: str, all_mlp_scores: np.ndarray, idx: dict) -> list[str]:
    if scorer == "mlp":
        return [r["case_id"] for r in sorted(
            selected, key=lambda r: (-float(all_mlp_scores[idx[r["case_id"]]]), r["case_id"]))]
    if scorer == "rrf":
        return [r["case_id"] for r in sorted(
            selected, key=lambda r: (-r["rrf_score"], r["dense_rank"], r["case_id"]))]
    raise ValueError(scorer)


def main() -> None:
    import torch
    required = [
        SRC / "fixed_bge_m3_embeddings.npz",
        SRC / "branch_rankings.csv",
        SRC / "generated_runtime_perspectives.json",
        SRC / "rankings_top20.csv", GT,
    ]
    for p in required:
        if not p.exists():
            raise FileNotFoundError(str(p))
    npz = np.load(required[0])
    case_ids = [str(x) for x in npz["case_ids"].tolist()]
    if len(case_ids) != CASE_COUNT or len(set(case_ids)) != CASE_COUNT:
        raise AssertionError("Expected 84 distinct cases")
    idx = {cid: i for i, cid in enumerate(case_ids)}
    key_list = [str(x) for x in npz["branch_keys"].tolist()]
    qemb = npz["branch_embeddings"]
    if len(key_list) != 97 or len(set(key_list)) != 97 or len(qemb) != 97:
        raise AssertionError("Expected frozen 97 branch definitions and embeddings")
    view = np.stack([
        npz["problem_embeddings"], npz["task_embeddings"], npz["context_embeddings"],
    ], axis=0)
    rankings = defaultdict(lambda: defaultdict(list))
    rows = load_csv(required[1])
    if len(rows) != 97 * 84 * 2:
        raise AssertionError("Missing frozen Dense or BM25 branch score rows")
    for row in rows:
        key = f'{row["query_id"]}|{row["run_id"]}|{row["perspective_id"]}'
        rankings[key][row["retrieval"]].append(
            (int(row["local_rank"]), row["case_id"], float(row["score"])))
    full = {}
    for key, emb in zip(key_list, qemb):
        sims = ((view @ emb).mean(axis=0)).astype(np.float32)
        dense = [case_ids[i] for i in sorted(range(CASE_COUNT),
                                              key=lambda i: (-float(sims[i]), case_ids[i]))]
        if sorted(r[0] for r in rankings[key]["bm25"]) != list(range(1, 85)):
            raise AssertionError(f"Bad BM25 ranks {key}")
        sparse = [(cid, score) for _, cid, score in sorted(rankings[key]["bm25"])]
        full[key] = full_union(dense, sparse)
    if len(full) != 97:
        raise AssertionError("Incomplete generated perspective coverage")
    qrels = load_csv(GT)
    if len(qrels) != 2520:
        raise AssertionError("Frozen AI Silver GT changed")
    gold, reference_views = defaultdict(set), defaultdict(lambda: defaultdict(set))
    for row in qrels:
        if int(row["relevance_0_4"]) >= 3:
            gold[row["query_id"]].add(row["case_id"])
            reference_views[row["query_id"]][row["perspective_id"]].add(row["case_id"])
    queries = sorted(gold)
    if len(queries) != 10 or any(not gold[q] for q in queries):
        raise AssertionError("Expected ten answerable Dev queries")
    baseline = defaultdict(list)
    for row in load_csv(required[3]):
        if row["system"] == "single_dense_bge_m3":
            baseline[row["query_id"]].append((int(row["rank"]), row["case_id"]))
    baseline = {q: [cid for _, cid in sorted(baseline[q])] for q in queries}
    assert all(len(x) == 20 for x in baseline.values())

    rng = np.random.default_rng(SEED)
    dim = npz["document_embeddings"].shape[1]
    proj = rng.normal(0, 1 / np.sqrt(dim), size=(dim, 48)).astype(np.float32)
    case_proj = (npz["document_embeddings"] @ proj).astype(np.float32)
    query_proj = {key: (vec @ proj).astype(np.float32) for key, vec in zip(key_list, qemb)}

    detail_candidates, pool_metrics = [], []
    detail_topk, global_metrics, train_audit = [], [], []
    for q in queries:
        # Same LOQO model for every candidate method/M to isolate pooling choice.
        model, training_q, loss = train_model(
            q, queries, key_list, query_proj, case_proj, case_ids, gold)
        train_audit.append(dict(held_query=q, train_queries="|".join(training_q),
                                target_labels_in_training=0, final_loss=loss))
        mlp_scores = {}
        with torch.no_grad():
            for key in key_list:
                if key.startswith(q + "|"):
                    x = interaction_features(query_proj[key], case_proj)
                    mlp_scores[key] = model(torch.tensor(x, dtype=torch.float32)).squeeze(-1).numpy()
        for run in (1, 2, 3):
            pkeys = [key for key in key_list if key.startswith(f"{q}|{run}|")]
            if not 2 <= len(pkeys) <= 5:
                raise AssertionError("Wrong number of perspectives")
            active_refs = [s for s in reference_views[q].values() if s]
            # Shared controls: full-union Top-M rather than early per-retriever cut.
            per_method_m = {}
            for m in MS:
                for method in METHODS:
                    pool = set()
                    orders = {"rrf": OrderedDict(), "mlp": OrderedDict()}
                    branch_positive = 0
                    sparse_only = 0
                    for key in pkeys:
                        pid = key.split("|")[2]
                        chosen = select_top_m(full[key], method, m)
                        chosen_ids = {v["case_id"] for v in chosen}
                        branch_positive += len(chosen_ids & gold[q])
                        sparse_only += sum(bool(v["sparse_hit"]) for v in chosen)
                        pool |= chosen_ids
                        for at, r in enumerate(chosen, 1):
                            detail_candidates.append(dict(
                                query_id=q, run_id=run, perspective_id=pid, method=method,
                                m=m, selected_rank=at, case_id=r["case_id"],
                                dense_rank=r["dense_rank"], sparse_rank=r["sparse_rank"],
                                bm25_score=r["bm25_score"], sparse_hit=r["sparse_hit"],
                                fused_rrf_score=r["rrf_score"], source=r["source"]))
                        for scorer in orders:
                            ranking = rerank(chosen, scorer, mlp_scores[key], idx)
                            orders[scorer][pid] = ranking
                            for at, cid in enumerate(ranking[:min(m,20)], 1):
                                detail_topk.append(dict(
                                    query_id=q, run_id=run, perspective_id=pid,
                                    method=method, m=m, scorer=scorer,
                                    rank=at, case_id=cid))
                    per_method_m[(method,m)] = (pool,orders)
                    p=pool & gold[q]
                    pool_metrics.append(dict(
                        query_id=q, run_id=run, method=method, m=m,
                        branch_count=len(pkeys), pool_unique_count=len(pool),
                        positive_pool_count=len(p), silver_positive_total=len(gold[q]),
                        candidate_recall=len(p)/len(gold[q]),
                        coverage=sum(bool(pool & s) for s in active_refs)/len(active_refs),
                        branch_positive_slots=branch_positive,
                        branch_sparse_hit_slots=sparse_only))
            # Matched M comparisons, independent of gold at selection time.
            for m in MS:
                dense_set = per_method_m[("dense",m)][0]
                for method in METHODS:
                    pool,orders=per_method_m[(method,m)]
                    for r in pool_metrics[-len(METHODS)*len(MS):]:
                        if (r["query_id"],r["run_id"],r["method"],r["m"])==(q,run,method,m):
                            r["added_vs_dense"] = len((pool-dense_set) & gold[q])
                            r["lost_vs_dense"] = len((dense_set-pool) & gold[q])
                    for scorer,branches in orders.items():
                        # Global comparison is diagnostic; official output remains
                        # per-perspective Top-K and perspective IDs are retained.
                        for k in KS:
                            if k > m:
                                continue
                            global_top = branch_balanced(branches,k)
                            if len(global_top) != k:
                                raise AssertionError("Cannot assemble diagnostic global Top-K")
                            gset=set(global_top)
                            single=set(baseline[q][:k]) if k<=20 else set()
                            global_metrics.append(dict(
                                query_id=q, run_id=run, method=method, m=m, scorer=scorer,
                                k=k, relevant_count=len(gset & gold[q]),
                                recall=len(gset & gold[q])/len(gold[q]),
                                perspective_coverage=sum(bool(gset & s)
                                    for s in active_refs)/len(active_refs),
                                mp_only_relevant_vs_single=len((gset-single)&gold[q]),
                                single_only_relevant_missing=len((single-gset)&gold[q]),
                                metric_type="DIAGNOSTIC_GLOBAL_NOT_PROFESSOR_OUTPUT"))

    output_files=[
        ("candidate_pool_metrics.csv",pool_metrics),
        ("selected_candidate_provenance.csv",detail_candidates),
        ("perspective_topk_rankings.csv",detail_topk),
        ("global_shortlist_diagnostics.csv",global_metrics),
        ("loqo_training_audit.csv",train_audit),
    ]
    for name,rows in output_files:
        write_csv(OUT/name,rows)
    summary=dict(
        status="SUCCESS_FROZEN_V23_DEV_EXPLORATORY_REPLAY", corpus_cases=84,
        source_branches=97, query_count=10, repetitions=3,
        interpretation="full Dense 84 and BM25 84 → union → Top-M → QCI → per-perspective Top-K",
        methods=list(METHODS), m_values=list(MS), k_values=list(KS),
        bm25_zero_is_not_sparse_evidence=True,
        query_case_model="fixed LOQO 48d 32 epochs; same model across methods and M",
        source_labels="AI_SILVER_DEV_NOT_INDEPENDENT_TEST", chart=[],
    )
    for m in MS:
        row={"M":m}
        for method in METHODS:
            pool_rows=[r for r in pool_metrics if r["method"]==method and r["m"]==m]
            row[method]={
                "mean_unique_pool":float(np.mean([r["pool_unique_count"] for r in pool_rows])),
                "macro_candidate_recall":float(np.mean([r["candidate_recall"] for r in pool_rows])),
                "added_relevant_vs_same_m_dense_occurrences":sum(r["added_vs_dense"] for r in pool_rows),
                "lost_relevant_vs_same_m_dense_occurrences":sum(r["lost_vs_dense"] for r in pool_rows),
                "macro_coverage":float(np.mean([r["coverage"] for r in pool_rows])),
            }
            for scorer in ("rrf","mlp"):
                for k in KS:
                    if k>m:
                        continue
                    xs=[r for r in global_metrics if r["method"]==method
                        and r["m"]==m and r["scorer"]==scorer and r["k"]==k]
                    row[method][f"{scorer}_global_diagnostic_recall_at_{k}"]=float(
                        np.mean([r["recall"] for r in xs]))
        summary["chart"].append(row)
    if any(not all(row[x]["macro_candidate_recall"]==1 for x in METHODS)
           for row in summary["chart"] if row["M"]==84):
        raise AssertionError("All-case M=84 upper bound not 100%")
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",
                                     encoding="utf-8")
    print("FULL_UNION_TOPM_OK "+json.dumps(summary,ensure_ascii=False),flush=True)


if __name__=="__main__":
    main()
