import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import sys

import numpy as np

from scripts.build_ax_expansion_release import ROOT, digest, read_json, write_json
from scripts.prepare_v25_research import OUTPUT, write_csv


RESULTS = ROOT / "docs/prototype-validation/v25-dev"
VIEW_FIELDS = ("problem", "task", "context")


def verify_preparation():
    manifest = read_json(OUTPUT / "manifest.json")
    for filename, expected in manifest["sha256"].items():
        if digest(OUTPUT / filename) != expected:
            raise ValueError("Research input hash mismatch: " + filename)
    for filename, expected in manifest["input_sha256"].items():
        if digest(ROOT / filename) != expected:
            raise ValueError("Source input hash mismatch: " + filename)


def index_identity():
    return {"cases_sha256": digest(OUTPUT / "dev_cases.json"), "queries_sha256": digest(OUTPUT / "dev_queries.json"),
            "encoder": "BAAI/bge-m3", "max_tokens_all_views_and_queries": 128, "dimensions": 1024,
            "views": list(VIEW_FIELDS), "solution_and_labels_excluded": True, "normalized": True}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rebuild-index", action="store_true")
    parser.add_argument("--top-k", type=int, default=10)
    args = parser.parse_args()
    if args.top_k < 1:
        raise ValueError("top-k must be positive")
    verify_preparation()
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    import torch
    from ax_research.retrieval.bm25 import BM25Retriever
    torch.set_num_threads(8)
    torch.manual_seed(20261026)
    np.random.seed(20261026)
    RESULTS.mkdir(parents=True, exist_ok=True)
    cases = sorted(read_json(OUTPUT / "dev_cases.json")["cases"], key=lambda case: case["case_id"])
    queries = read_json(OUTPUT / "dev_queries.json")["queries"]
    case_ids = [case["case_id"] for case in cases]
    query_ids = [query["query_id"] for query in queries]
    identity = index_identity()
    index_path = OUTPUT / "dev_bge_m3_128.npz"
    manifest_path = OUTPUT / "dev_index_manifest.json"
    if args.rebuild_index or not index_path.exists():
        from sentence_transformers import SentenceTransformer
        model_directory = ROOT / ".local/models/bge-m3"
        weights = next(path for path in [model_directory / "model.safetensors", model_directory / "pytorch_model.bin"] if path.is_file())
        weight_hash = digest(weights)
        if weight_hash != read_json(ROOT / "data/v2_4/index_manifest.json")["model_weights_sha256"]:
            raise ValueError("Local BGE-M3 differs from inherited model weights")
        model = SentenceTransformer(str(model_directory), device="cpu", local_files_only=True)
        model.max_seq_length = 128
        texts = [case[field] for field in VIEW_FIELDS for case in cases] + [query["query"] for query in queries]
        vectors = model.encode(texts, batch_size=16, normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False).astype(np.float32)
        if vectors.shape != (len(texts), 1024) or not np.isfinite(vectors).all():
            raise ValueError("Invalid clean research embeddings")
        np.savez_compressed(index_path, case_ids=np.asarray(case_ids), query_ids=np.asarray(query_ids),
                            views=vectors[:3 * len(cases)].reshape(3, len(cases), 1024), queries=vectors[3 * len(cases):])
        write_json(manifest_path, {**identity, "index_sha256": digest(index_path), "model_weights_sha256": weight_hash,
                                  "model_config_sha256": {path.name: digest(path) for path in model_directory.glob("*.json")},
                                  "vector_content_sha256": hashlib.sha256(vectors.tobytes()).hexdigest(), "paid_api_calls": 0})
        print("Clean Dev index created", flush=True)
    manifest = read_json(manifest_path)
    if any(manifest[key] != value for key, value in identity.items()) or digest(index_path) != manifest["index_sha256"]:
        raise ValueError("Dev index does not match inputs or hash")
    with np.load(index_path, allow_pickle=False) as archive:
        if archive["case_ids"].tolist() != case_ids or archive["query_ids"].tolist() != query_ids:
            raise ValueError("Dev index order mismatch")
        views = archive["views"]
        query_vectors = archive["queries"]
    if views.shape != (3, len(cases), 1024) or query_vectors.shape != (len(queries), 1024):
        raise ValueError("Dev index shape mismatch")
    for vectors in [views, query_vectors]:
        if not np.isfinite(vectors).all() or not np.allclose(np.linalg.norm(vectors, axis=-1), 1, atol=1e-4):
            raise ValueError("Invalid normalized Dev vectors")
    documents = {case["case_id"]: "\n".join(case[field] for field in VIEW_FIELDS) for case in cases}
    bm25 = BM25Retriever(documents)
    dense_rows = []
    sparse_rows = []
    for query, vector in zip(queries, query_vectors, strict=True):
        scores = np.mean(views @ vector, axis=0)
        offsets = sorted(range(len(cases)), key=lambda offset: (-float(scores[offset]), case_ids[offset]))[:args.top_k]
        dense_rows.extend({"query_id": query["query_id"], "case_id": case_ids[offset], "rank": rank,
                           "score": float(scores[offset])} for rank, offset in enumerate(offsets, 1))
        sparse_rows.extend({"query_id": query["query_id"], "case_id": row.case_id, "rank": rank, "score": row.score}
                           for rank, row in enumerate(bm25.search(query["query"], top_k=args.top_k), 1))
    for rows in [dense_rows, sparse_rows]:
        assert len(rows) == len(queries) * min(args.top_k, len(cases))
        assert all(row["case_id"] in case_ids and np.isfinite(row["score"]) for row in rows)
    fields = ["query_id", "case_id", "rank", "score"]
    write_csv(RESULTS / "single_query_dense.csv", dense_rows, fields)
    write_csv(RESULTS / "single_query_bm25.csv", sparse_rows, fields)
    packages = ["numpy", "torch", "sentence-transformers", "transformers", "kiwipiepy", "rank-bm25", "pytest", "requests"]
    report = {"status": "EXECUTED_DESCRIPTIVE_DEV_BASELINES_NO_APPROVED_QRELS", "corpus_records": len(cases),
              "queries": len(queries), "top_k": args.top_k, "ranking_rows_each": len(dense_rows),
              "systems": ["SINGLE_QUERY_KIWI_BM25", "SINGLE_QUERY_BGE_M3_MEAN_3VIEW_COSINE"],
              "input_manifest_sha256": digest(OUTPUT / "manifest.json"), "index_manifest_sha256": digest(manifest_path),
              "ranking_sha256": {path.name: digest(path) for path in [RESULTS / "single_query_dense.csv", RESULTS / "single_query_bm25.csv"]},
              "seed": 20261026, "device": "cpu", "threads": 8, "paid_api_calls": 0,
              "python": sys.version, "platform": platform.platform(), "package_versions": {name: importlib.metadata.version(name) for name in packages},
              "metrics": None, "metrics_blocker": "3360 unjudged pairs; unjudged is not a non-relevant label. No v25 Recall/Coverage claim.",
              "language_limitation": "Korean Dev queries and mostly English source summaries. BM25 lexical mismatch is an experimental limitation; no inferred relevance from scores.",
              "generalization_limitation": "112 source-supported Dev cases are not representative of all 9416 retrieval candidates or a held-out Test",
              "architecture": "Baselines only. Full learned FAME-AX and GPT-only comparisons remain unevaluated on v25."}
    write_json(RESULTS / "run_report.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
