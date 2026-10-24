#!/usr/bin/env python3
"""Professor search-core: preserve Dense AND Sparse candidates before neural reranking.

Replay of frozen v2.3 perspectives, BGE-M3 embeddings and Kiwi-BM25 rankings.
No OpenAI calls. No writes to the immutable experiments/v23_dev or data/v2_3.
"""
from __future__ import annotations

import csv
import json
import math
from collections import defaultdict, OrderedDict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "experiments/v23_dev/stage1"
OUT = ROOT / "experiments/v23_hybrid_preserving"
GT = ROOT / "data/v2_3/ground_truth/silver_dev_qrels_2520.csv"
K_VALUES = (5, 10, 20)
CASE_COUNT = 84
SEED = 42
CONFIGS = OrderedDict([
    ("dense20", (20, 0)),
    ("replace10_10", (10, 10)),
    ("preserve20_add10", (20, 10)),
    ("dense30_equal_slots", (30, 0)),
    ("preserve20_add20", (20, 20)),
    ("dense40_equal_slots", (40, 0)),
])


def load_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise ValueError(f"empty output: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def union_candidates(
    dense_order: list[str], sparse_order: list[str], dense_n: int, sparse_n: int
) -> list[dict]:
    """Never trade away dense cases; deduplicate and keep source provenance."""
    if dense_n < 0 or sparse_n < 0:
        raise ValueError("negative retrieval slots")
    if len(dense_order) != len(set(dense_order)):
        raise ValueError("duplicate dense ranks")
    if len(sparse_order) != len(set(sparse_order)):
        raise ValueError("duplicate sparse ranks")
    if set(dense_order) != set(sparse_order):
        raise ValueError("Dense and Sparse must rank identical case corpus")
    dr = {cid: i + 1 for i, cid in enumerate(dense_order)}
    sr = {cid: i + 1 for i, cid in enumerate(sparse_order)}
    pool = set(dense_order[:dense_n]) | set(sparse_order[:sparse_n])
    out = []
    for cid in sorted(pool):
        in_dense = dr[cid] <= dense_n
        in_sparse = sr[cid] <= sparse_n
        out.append(dict(
            case_id=cid, dense_rank=dr[cid], sparse_rank=sr[cid],
            dense_selected=int(in_dense), sparse_selected=int(in_sparse),
            source="BOTH" if in_dense and in_sparse else "DENSE" if in_dense else "SPARSE",
            rrf=(1.0 / (60 + dr[cid]) if in_dense else 0.0)
                + (1.0 / (60 + sr[cid]) if in_sparse else 0.0),
        ))
    if len(out) > dense_n + sparse_n:
        raise AssertionError("candidate budget exceeded")
    return out


def rank_rrf(items: list[dict]) -> list[str]:
    return [x["case_id"] for x in sorted(items, key=lambda x: (-x["rrf"], x["case_id"]))]


def branch_balanced(branch_orders: OrderedDict[str, list[str]], k: int) -> list[str]:
    """Only a *diagnostic global shortlist*: professor output stays per branch."""
    seen = set()
    cursor = {pid: 0 for pid in branch_orders}
    selected = []
    while len(selected) < k:
        changed = False
        for pid, ordered in branch_orders.items():
            while cursor[pid] < len(ordered) and ordered[cursor[pid]] in seen:
                cursor[pid] += 1
            if cursor[pid] < len(ordered):
                cid = ordered[cursor[pid]]
                cursor[pid] += 1
                selected.append(cid)
                seen.add(cid)
                changed = True
                if len(selected) == k:
                    break
        if not changed:
            break
    return selected


def interaction_features(p: np.ndarray, c: np.ndarray) -> np.ndarray:
    """q,case,q*case,|q-case|; no outcome/relevance fields included."""
    pp = np.broadcast_to(p[None, :], c.shape)
    return np.concatenate([pp, c, pp * c, np.abs(pp - c)], axis=1)


def train_model(held: str, queries: list[str], keys: list[str],
                projected_query: dict, projected_cases: np.ndarray,
                case_ids: list[str], positives: dict):
    """Leave-one-QUERY-out: all three runs of held query are excluded."""
    import torch
    from torch import nn
    torch.set_num_threads(2)
    torch.manual_seed(SEED)
    dim = 48 * 4
    model = nn.Sequential(nn.Linear(dim, 64), nn.ReLU(), nn.Linear(64, 1))
    feat, labs, train_queries = [], [], []
    for key in keys:
        q = key.split("|", 1)[0]
        if q == held:
            continue
        train_queries.append(q)
        feat.append(interaction_features(projected_query[key], projected_cases))
        labs.extend(float(cid in positives[q]) for cid in case_ids)
    if set(train_queries) != set(queries) - {held} or held in train_queries:
        raise AssertionError("Query-level LOQO leakage")
    x = torch.tensor(np.concatenate(feat), dtype=torch.float32)
    y = torch.tensor(labs, dtype=torch.float32)
    pos = max(float(y.sum()), 1.0)
    neg = max(float(len(y) - y.sum()), 1.0)
    loss_fn = nn.BCEWithLogitsLoss(pos_weight=torch.tensor(neg / pos))
    opt = torch.optim.Adam(model.parameters(), lr=0.003, weight_decay=0.003)
    for _ in range(32):
        opt.zero_grad()
        loss = loss_fn(model(x).squeeze(-1), y)
        loss.backward()
        opt.step()
    return model, sorted(set(train_queries)), float(loss.item())


def main():
    import torch
    files = [SRC / "fixed_bge_m3_embeddings.npz",
             SRC / "branch_rankings.csv", SRC / "generated_runtime_perspectives.json",
             GT, SRC / "rankings_top20.csv"]
    for p in files:
        if not p.is_file():
            raise FileNotFoundError(str(p))
    npz = np.load(files[0])
    case_ids = [str(x) for x in npz["case_ids"].tolist()]
    if len(case_ids) != CASE_COUNT or len(set(case_ids)) != CASE_COUNT:
        raise AssertionError("Frozen case IDs missing or duplicated")
    idx = {cid: i for i, cid in enumerate(case_ids)}
    q_embeddings = npz["branch_embeddings"]
    key_list = [str(k) for k in npz["branch_keys"].tolist()]
    if len(key_list) != len(set(key_list)) or len(key_list) != 97:
        raise AssertionError("Frozen runtime branches inconsistent")
    if len(q_embeddings) != len(key_list):
        raise AssertionError("Embedding/key length mismatch")
    views = np.stack([
        npz["problem_embeddings"], npz["task_embeddings"], npz["context_embeddings"],
    ], axis=0)
    sparse = defaultdict(list)
    dense_from_stage1 = defaultdict(list)
    for row in load_csv(files[1]):
        key = f'{row["query_id"]}|{row["run_id"]}|{row["perspective_id"]}'
        (sparse if row["retrieval"] == "bm25" else dense_from_stage1)[key].append(
            (int(row["local_rank"]), row["case_id"]))
    for key in key_list:
        if len(sparse[key]) != 84 or len(dense_from_stage1[key]) != 84:
            raise AssertionError(f"incomplete sparse or dense ranks: {key}")
    positives = defaultdict(set)
    ref_positive = defaultdict(lambda: defaultdict(set))
    gt_rows = load_csv(GT)
    if len(gt_rows) != 2520:
        raise AssertionError("Frozen Silver size changed")
    for row in gt_rows:
        if int(row["relevance_0_4"]) >= 3:
            positives[row["query_id"]].add(row["case_id"])
            ref_positive[row["query_id"]][row["perspective_id"]].add(row["case_id"])
    queries = sorted(positives)
    if len(queries) != 10:
        raise AssertionError("Expected 10 distinct Dev queries")
    single = defaultdict(list)
    for row in load_csv(files[4]):
        if row["system"] == "single_dense_bge_m3":
            single[row["query_id"]].append((int(row["rank"]), row["case_id"]))
    for q in queries:
        single[q] = [c for _, c in sorted(single[q])]
        if len(single[q]) != 20:
            raise AssertionError(f"Single Dense Top20 missing: {q}")
    # Fixed random projection as in original v2.3 interaction diagnostic.
    rng = np.random.default_rng(SEED)
    dimension = npz["document_embeddings"].shape[1]
    projection = rng.normal(0, 1 / math.sqrt(dimension), size=(dimension, 48)).astype(np.float32)
    projected_cases = (npz["document_embeddings"] @ projection).astype(np.float32)
    projected_query = {k: (v @ projection).astype(np.float32)
                       for k, v in zip(key_list, q_embeddings)}
    # Per-branch true three-view equal-mean dense ranks, NOT Stage1 single-view ranks.
    dense = {}
    for key, emb in zip(key_list, q_embeddings):
        scores = ((views @ emb).mean(axis=0)).astype(np.float32)
        dense[key] = [case_ids[i] for i in sorted(
            range(CASE_COUNT), key=lambda i: (-float(scores[i]), case_ids[i]))]
        sparse[key] = [c for _, c in sorted(sparse[key])]
        if set(dense[key]) != set(sparse[key]) or len(dense[key]) != CASE_COUNT:
            raise AssertionError(f"Wrong branch case universe: {key}")
    per_branch = []
    candidate_metrics = []
    output_metrics = []
    global_rankings = []
    train_audit = []
    for held in queries:
        model, training_queries, loss = train_model(
            held, queries, key_list, projected_query, projected_cases, case_ids, positives)
        train_audit.append(dict(held_query=held, training_queries="|".join(training_queries),
                                held_query_in_training=0, last_loss=loss, random_seed=SEED))
        with torch.no_grad():
            score_by_branch = {}
            for key in key_list:
                if key.split("|", 1)[0] != held:
                    continue
                xx = interaction_features(projected_query[key], projected_cases)
                score_by_branch[key] = model(torch.tensor(xx, dtype=torch.float32)).squeeze(-1).numpy()
        for run in (1, 2, 3):
            key_prefix = f"{held}|{run}|"
            pkeys = [k for k in key_list if k.startswith(key_prefix)]
            if not 2 <= len(pkeys) <= 5:
                raise AssertionError(f"Unexpected perspective count: {key_prefix}")
            target = positives[held]
            answerable = [v for v in ref_positive[held].values() if v]
            for method, (dn, sn) in CONFIGS.items():
                branch_orders = {"rrf": OrderedDict(), "mlp": OrderedDict()}
                candidate_union = set()
                source_counts = {"DENSE": 0, "SPARSE": 0, "BOTH": 0}
                for key in pkeys:
                    pid = key.split("|")[2]
                    items = union_candidates(dense[key], sparse[key], dn, sn)
                    assert set(dense[key][:dn]) <= {r["case_id"] for r in items}
                    assert set(sparse[key][:sn]) <= {r["case_id"] for r in items}
                    candidate_union.update(x["case_id"] for x in items)
                    for x in items:
                        source_counts[x["source"]] += 1
                        x["mlp"] = float(score_by_branch[key][idx[x["case_id"]]])
                        per_branch.append(dict(method=method, query_id=held, run_id=run,
                            perspective_id=pid, case_id=x["case_id"],
                            dense_rank=x["dense_rank"], sparse_rank=x["sparse_rank"],
                            source=x["source"], rrf_score=x["rrf"], mlp_score=x["mlp"]))
                    branch_orders["rrf"][pid] = rank_rrf(items)
                    branch_orders["mlp"][pid] = [
                        x["case_id"] for x in sorted(
                            items, key=lambda x: (-x["mlp"], x["case_id"]))]
                compare_budget = (dn + sn)
                dcomp = set()
                for key in pkeys:
                    dcomp.update(dense[key][:compare_budget])
                candidate_metrics.append(dict(method=method, query_id=held, run_id=run,
                    slots_per_branch=compare_budget, branch_count=len(pkeys),
                    candidate_count=len(candidate_union),
                    dense_same_slot_candidate_count=len(dcomp),
                    candidate_recall=len(candidate_union & target) / len(target),
                    dense_same_slot_recall=len(dcomp & target) / len(target),
                    relevant_gained=len((candidate_union - dcomp) & target),
                    relevant_lost=len((dcomp - candidate_union) & target),
                    candidate_perspective_coverage=sum(bool(candidate_union & p)
                        for p in answerable) / len(answerable),
                    dense_source_entries=source_counts["DENSE"],
                    sparse_source_entries=source_counts["SPARSE"],
                    both_source_entries=source_counts["BOTH"]))
                for scorer, orders in branch_orders.items():
                    # Professor view: preserve perspective-specific ranked outputs.
                    for pid, ordered in orders.items():
                        for i, cid in enumerate(ordered[:20], 1):
                            # Ranking by the full candidate pool is stored, not truncated before MLP.
                            global_rankings.append(dict(type="perspective", method=method,
                                scorer=scorer, query_id=held, run_id=run, perspective_id=pid,
                                rank=i, case_id=cid))
                    # Global result is a diagnostic output ONLY, not the professor's output.
                    glob = branch_balanced(orders, 20)
                    assert len(glob) == 20 and len(set(glob)) == 20
                    for i, cid in enumerate(glob, 1):
                        global_rankings.append(dict(type="global_diagnostic", method=method,
                            scorer=scorer, query_id=held, run_id=run, perspective_id="",
                            rank=i, case_id=cid))
                    for k in K_VALUES:
                        got = set(glob[:k])
                        sset = set(single[held][:k])
                        output_metrics.append(dict(method=method, scorer=scorer, query_id=held,
                            run_id=run, k=k, recall=len(got & target) / len(target),
                            perspective_coverage=sum(bool(got & p) for p in answerable) / len(answerable),
                            new_relevant_vs_single=len((got - sset) & target),
                            lost_relevant_vs_single=len((sset - got) & target),
                            gt_status="AI_SILVER_DEV_ONLY"))
    write_csv(OUT / "candidate_pool_metrics.csv", candidate_metrics)
    write_csv(OUT / "candidate_case_provenance.csv", per_branch)
    write_csv(OUT / "rankings_perspective_and_global.csv", global_rankings)
    write_csv(OUT / "final_diagnostic_metrics.csv", output_metrics)
    write_csv(OUT / "loqo_training_audit.csv", train_audit)
    summary = {"status": "REAL_EXECUTED_FROZEN_V23_DEV_REPLAY",
               "qrels": "AI_SILVER_NOT_HUMAN_GOLD", "cases": 84, "queries": 10,
               "repetitions": 3, "generated_branches": len(key_list),
               "gate": "equal_mean_three_view; learned_gate_not_claimed",
               "qci": "query_case_MLP_48d_random_projection_LOQO",
               "graph_retrieval": "NOT_IMPLEMENTED_SEARCH_CORE_ONLY",
               "end_to_end_stage3_stage4": "NOT_EXECUTED_IN_THIS_DIAGNOSTIC",
               "configs": {}}
    for method, (dn, sn) in CONFIGS.items():
        subset = [r for r in candidate_metrics if r["method"] == method]
        obj = dict(dense_slots=dn, sparse_slots=sn,
            mean_pool_size=float(np.mean([r["candidate_count"] for r in subset])),
            candidate_recall=float(np.mean([r["candidate_recall"] for r in subset])),
            same_slot_dense_recall=float(np.mean([r["dense_same_slot_recall"] for r in subset])),
            added_relevant_appearances=sum(r["relevant_gained"] for r in subset),
            lost_relevant_appearances=sum(r["relevant_lost"] for r in subset),
            hybrid_candidate_better=sum(r["candidate_recall"] > r["dense_same_slot_recall"]
                                        for r in subset),
            hybrid_candidate_worse=sum(r["candidate_recall"] < r["dense_same_slot_recall"]
                                       for r in subset))
        for scorer in ("rrf", "mlp"):
            for k in K_VALUES:
                arr = [r for r in output_metrics if r["method"] == method
                       and r["scorer"] == scorer and r["k"] == k]
                obj[f"{scorer}_diagnostic_recall_at_{k}"] = float(
                    np.mean([r["recall"] for r in arr]))
                obj[f"{scorer}_diagnostic_new_positive_at_{k}"] = sum(
                    r["new_relevant_vs_single"] for r in arr)
        summary["configs"][method] = obj
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
                                       encoding="utf-8")
    print("PROFESSOR_HYBRID_DONE " + json.dumps(summary, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
