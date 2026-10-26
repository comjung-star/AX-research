import argparse
import json

import numpy as np

from ax_research.retrieval.bm25 import BM25Retriever
from scripts.audit_final_dataset import OUTPUT, fingerprint, load_csv
from scripts.build_ax_expansion_release import ROOT, digest, read_json, write_json
from scripts.prepare_v25_research import write_csv


def summarize_query_metrics(rankings, qrels, k_values):
    by_query = {}
    for row in qrels:
        if row["relevance_0_4"] == "":
            raise ValueError("Unjudged and unresolved qrels cannot be treated as negative labels")
        perspectives = by_query.setdefault(row["query_id"], {})
        relevant = perspectives.setdefault(row["perspective_id"], set())
        if int(row["relevance_0_4"]) >= 3:
            relevant.add(row["case_id"])
    rows = []
    for (system, query_id), ranked in rankings.items():
        perspectives = by_query[query_id]
        positives = set().union(*perspectives.values())
        answerable = [cases for cases in perspectives.values() if cases]
        for top_k in k_values:
            retrieved = set(ranked[:top_k])
            rows.append({"system": system, "query_id": query_id, "k": top_k,
                         "recall": len(retrieved & positives) / len(positives) if positives else "",
                         "perspective_coverage_answerable": sum(bool(retrieved & cases) for cases in answerable) / len(answerable) if answerable else "",
                         "perspective_coverage_all_references": sum(bool(retrieved & cases) for cases in perspectives.values()) / len(perspectives),
                         "reference_perspectives": len(perspectives), "answerable_perspectives": len(answerable),
                         "judged_positive_cases": len(positives), "human_gold": False})
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=["dev", "test"], default="dev")
    parser.add_argument("--release-heldout", action="store_true")
    arguments = parser.parse_args()
    if arguments.split == "test" and not arguments.release_heldout:
        raise ValueError("Held-out inference requires an explicit --release-heldout; do not use Test for tuning")
    cases = read_json(OUTPUT / "source_supported_candidates.json")["cases"]
    index_manifest = read_json(OUTPUT / "candidate_index_manifest.json")
    if index_manifest["candidate_fingerprint"] != fingerprint(cases) or index_manifest["index_sha256"] != digest(OUTPUT / "candidate_bge_m3_128.npz"):
        raise ValueError("Candidate index integrity mismatch")
    with np.load(OUTPUT / "candidate_bge_m3_128.npz", allow_pickle=False) as archive:
        identifiers = archive["case_ids"].tolist()
        views = archive["views"]
    assert identifiers == [case["case_id"] for case in cases]
    split = arguments.split
    input_document = read_json(OUTPUT / ("blind_relevance_input.json" if split == "dev" else "blind_test_relevance_input.json"))
    prefix = "" if split == "dev" else "test_"
    agreement = read_json(OUTPUT / f"{prefix}review_agreement.json")
    if agreement["unresolved_disagreements"] != 0 or agreement["input_sha256"] != fingerprint(input_document):
        raise ValueError("Independent qrels must be fully adjudicated for the exact split input before evaluation")
    qrels = load_csv(OUTPUT / f"{prefix}qrels_consensus.csv")
    if any(row["input_sha256"] != fingerprint(input_document) for row in qrels):
        raise ValueError("Qrels input identity mismatch")
    if split == "dev":
        with np.load(ROOT / "data/v2_5/research/dev_bge_m3_128.npz", allow_pickle=False) as archive:
            query_vectors = dict(zip(archive["query_ids"].tolist(), archive["queries"], strict=True))
        source_queries = {query["query_id"]: query["query"] for query in read_json(ROOT / "data/v2_5/research/dev_queries.json")["queries"]}
        if any(source_queries[query["query_id"]] != query["query"] for query in input_document["queries"]):
            raise ValueError("Cached Dev query vectors do not match query texts")
    else:
        import os
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"
        import torch
        from sentence_transformers import SentenceTransformer
        torch.set_num_threads(8)
        model = SentenceTransformer(str(ROOT / ".local/models/bge-m3"), device="cpu", local_files_only=True)
        model.max_seq_length = 128
        vectors = model.encode([query["query"] for query in input_document["queries"]], normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False)
        query_vectors = dict(zip([query["query_id"] for query in input_document["queries"]], vectors, strict=True))
    bm25 = BM25Retriever({case["case_id"]: "\n".join(case[field] for field in ("problem", "task", "context")) for case in cases})
    rankings = {}
    ranking_rows = []
    for query in input_document["queries"]:
        scores = np.mean(views @ query_vectors[query["query_id"]], axis=0)
        offsets = sorted(range(len(identifiers)), key=lambda offset: (-float(scores[offset]), identifiers[offset]))
        dense = [(identifiers[offset], float(scores[offset])) for offset in offsets]
        sparse = [(item.case_id, item.score) for item in bm25.search(query["query"], top_k=None)]
        for system, items in [("single_query_dense_3view", dense), ("single_query_kiwi_bm25", sparse)]:
            rankings[system, query["query_id"]] = [case_id for case_id, _ in items]
            ranking_rows.extend({"system": system, "query_id": query["query_id"], "rank": rank, "case_id": case_id, "score": score}
                                for rank, (case_id, score) in enumerate(items, 1))
    k_values = read_json(OUTPUT / "frozen_retrieval_protocol.json")["k_values"]
    metrics = summarize_query_metrics(rankings, qrels, k_values)
    destination = ROOT / "docs/prototype-validation/final-dataset-baselines" / split
    destination.mkdir(parents=True, exist_ok=True)
    write_csv(destination / "rankings.csv", ranking_rows, list(ranking_rows[0]))
    write_csv(destination / "metrics.csv", metrics, list(metrics[0]))
    summary = []
    for system in sorted({row["system"] for row in metrics}):
        for top_k in k_values:
            selected = [row for row in metrics if row["system"] == system and row["k"] == top_k]
            valid = [row for row in selected if row["recall"] != ""]
            summary.append({"system": system, "k": top_k, "macro_recall": float(np.mean([row["recall"] for row in valid])) if valid else None,
                            "macro_perspective_coverage_answerable": float(np.mean([row["perspective_coverage_answerable"] for row in valid])) if valid else None,
                            "query_count": len(selected), "answerable_query_count": len(valid)})
    report = {"split": split, "status": "EXECUTED_AGAINST_ADJUDICATED_AI_SILVER_NOT_HUMAN_GOLD", "candidate_count": len(cases),
              "query_count": len(input_document["queries"]), "input_fingerprint": fingerprint(input_document),
              "qrels_sha256": digest(OUTPUT / f"{prefix}qrels_consensus.csv"), "summary": summary,
              "rankings_sha256": digest(destination / "rankings.csv"), "metrics_sha256": digest(destination / "metrics.csv"),
              "paid_api_calls": 0, "full_fame_ax_effectiveness_claim": False,
              "limitations": ["Source-curated cohort, not exhaustive factual verification of the 11766 registry records", "Korean queries and multilingual case descriptions can disadvantage lexical retrieval", "AI-Silver relevance is not independent human accuracy evidence"]}
    write_json(destination / "run_report.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
