"""Trial 2: one-variable candidate-pool retention diagnostic on frozen development data.
Not a precision-mapping or final model experiment; candidate recall upper bound only.
No LLM, network, held-out test, or paid API calls.
"""
import hashlib
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RANKS = ROOT / "docs/validation-new20-20261107/diagnosis/raw_search_stage_rankings.json"
LABELS = ROOT / "docs/ax-transfer-relevance-20261108/02_working_transfer_qrels_2240.json"
TRACE = ROOT / "docs/autonomous-improvement-20261108/00_stage_rank_diagnostics.json"
OUT = ROOT / "trial2_candidate_retention_result.json"
K = 20

def main():
    if OUT.exists():
        raise RuntimeError("Refuse to overwrite previous result")
    raw = json.loads(RANKS.read_text())
    labels = json.loads(LABELS.read_text())["records"]
    trace = json.loads(TRACE.read_text())["records"]
    assert len(raw["questions"]) == 20 and len(raw["case_ids"]) == 112
    assert len(labels) == 2240 and len(trace) == 16
    ids = set(raw["case_ids"])
    systems = {}
    for name in ("Dense", "BM25", "Hybrid_RRF", "Original_C0"):
        entries = raw["systems"][name]
        systems[name] = {e["query_id"]: e["ranking"] for e in entries}
        assert set(systems[name]) == set(raw["questions"])
        assert all(len(r) == 112 and set(r) == ids for r in systems[name].values())
    positives = defaultdict(set)
    for x in labels:
        if x["grade"] >= 2:
            positives[x["query_id"]].add(x["case_id"])
    assert len([q for q in raw["questions"] if positives[q]]) == 16
    per_query = []
    for q in raw["questions"]:
        dense = set(systems["Dense"][q][:K])
        sparse = set(systems["BM25"][q][:K])
        union = dense | sparse
        hybrid = set(systems["Hybrid_RRF"][q][:K])
        c0 = set(systems["Original_C0"][q][:K])
        pos = positives[q]
        per_query.append({
            "query_id": q, "positive_count": len(pos), "candidate_count": len(union),
            "dense_hits": len(pos & dense), "sparse_hits": len(pos & sparse),
            "hybrid_hits": len(pos & hybrid), "c0_hits": len(pos & c0),
            "union_hits": len(pos & union),
            "union_recall_at_pool": len(pos & union)/len(pos) if pos else None,
            "hybrid_recall_at_pool": len(pos & hybrid)/len(pos) if pos else None,
            "c0_recall_at_pool": len(pos & c0)/len(pos) if pos else None,
            "union_only_positive_cases_vs_hybrid": sorted((pos & union) - hybrid),
            "union_missed_positive_cases": sorted(pos - union)
        })
    valid = [x for x in per_query if x["positive_count"]]
    summary = {
        "queries_with_positive_labels": len(valid),
        "macro_recall_hybrid_at_20": sum(x["hybrid_recall_at_pool"] for x in valid)/len(valid),
        "macro_recall_c0_at_20": sum(x["c0_recall_at_pool"] for x in valid)/len(valid),
        "macro_recall_dense_sparse_union_pool": sum(x["union_recall_at_pool"] for x in valid)/len(valid),
        "mean_candidate_pool_size": sum(x["candidate_count"] for x in per_query)/len(per_query)
    }
    focus = []
    for x in trace:
        q, c = x["query_id"], x["case_id"]
        focus.append({"query_id":q,"case_id":c,
            "dense_top20":c in systems["Dense"][q][:K],
            "sparse_top20":c in systems["BM25"][q][:K],
            "hybrid_top20":c in systems["Hybrid_RRF"][q][:K],
            "c0_top20":c in systems["Original_C0"][q][:K],
            "retained_by_union":c in set(systems["Dense"][q][:K]) | set(systems["BM25"][q][:K])})
    result = {
        "state":"CANDIDATE_POOL_DIAGNOSTIC_EXECUTED",
        "trial_number":2, "development_only":True,
        "preregistered_change":"Retain union of per-view Dense Top20 and Sparse Top20 instead of early Hybrid Top20 truncation; no change to embeddings, labels, precision mapping or final ranking",
        "important_limit":"Candidate-pool recall upper bound, NOT downstream F1/nDCG or validated multiview performance. This run does not execute precision mapping.",
        "f1_at_5":None,"ndcg_at_10":None,"independent_labels_verified":False,
        "input_sha256":{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (RANKS,LABELS,TRACE)},
        "summary":summary,"per_query":per_query,"provisional_16":focus,"paid_api_usd":0
    }
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"state":result["state"],"summary":summary,"retained_16":sum(x["retained_by_union"] for x in focus)}))

if __name__ == "__main__":
    main()
