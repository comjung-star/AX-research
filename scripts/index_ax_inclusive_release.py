import argparse
import hashlib
import json
import os
import sqlite3
import time

import numpy as np

from scripts.build_ax_expansion_release import EXPECTED_FROZEN_HASH, ROOT, digest, read_json, write_json
from scripts.build_ax_inclusive_release import RELEASE, build, meaningful, source_to_case
from scripts.review_all_ax_sources import all_inputs


VIEW_FIELDS = ("problem", "task", "context")
MODEL_MAX_TOKENS = 128


def retrieval_text(case, field):
    text = meaningful(case.get(field))
    if field == "task" and case.get("record_kind") == "SOURCE_REFERENCE":
        text = " ".join(value for value in [text, meaningful(case.get("source_description"))] if value)
    return text


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prime-public", action="store_true")
    parser.add_argument("--prime-available", action="store_true")
    parser.add_argument("--batch-size", type=int, default=24)
    parser.add_argument("--threads", type=int, default=8)
    arguments = parser.parse_args()
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    import torch
    from sentence_transformers import SentenceTransformer
    torch.set_num_threads(arguments.threads)
    cache_directory = ROOT / ".local/ax-inclusive-embedding-cache"
    cache_directory.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(cache_directory / "vectors.sqlite3")
    connection.execute("CREATE TABLE IF NOT EXISTS vectors (text_hash TEXT PRIMARY KEY, vector BLOB NOT NULL)")
    if arguments.prime_available:
        available_corpus, _, _ = build(require_complete=False)
        cases = [case for case in available_corpus["cases"][108:] if case["retrieval_eligible"]]
    elif arguments.prime_public:
        cases = [source_to_case(record) for record in all_inputs() if record["collection_kind"] == "PUBLIC_SECTOR_INVENTORY"]
    else:
        corpus = read_json(RELEASE / "main_cases_v2_5.json")
        cases = [case for case in corpus["cases"][108:] if case["retrieval_eligible"]]
    texts = list(dict.fromkeys(text for case in cases for field in VIEW_FIELDS if (text := retrieval_text(case, field))))
    identity = "BAAI/bge-m3|128|normalized|inclusive-v1|"
    hashes = {text: hashlib.sha256((identity + text).encode()).hexdigest() for text in texts}
    cached = {row[0] for row in connection.execute("SELECT text_hash FROM vectors")}
    pending = sorted((text for text in texts if hashes[text] not in cached), key=len)
    cache_hits = len(texts) - len(pending)
    print(json.dumps({"unique_texts": len(texts), "cached": len(texts) - len(pending), "pending": len(pending), "max_tokens": MODEL_MAX_TOKENS}), flush=True)
    model = None
    if pending:
        model = SentenceTransformer(str(ROOT / ".local/models/bge-m3"), device="cpu", local_files_only=True)
        model.max_seq_length = MODEL_MAX_TOKENS
    started = time.monotonic()
    for start in range(0, len(pending), arguments.batch_size):
        batch = pending[start:start + arguments.batch_size]
        vectors = model.encode(batch, batch_size=arguments.batch_size, normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False)
        if vectors.shape != (len(batch), 1024) or not np.isfinite(vectors).all():
            raise ValueError("Invalid local BGE-M3 embeddings")
        connection.executemany("INSERT OR REPLACE INTO vectors VALUES (?, ?)", [(hashes[text], vector.astype(np.float32).tobytes()) for text, vector in zip(batch, vectors, strict=True)])
        connection.commit()
        progress = {"scope": "available_cache" if arguments.prime_available else "public_cache" if arguments.prime_public else "complete_index", "unique_texts": len(texts),
                    "completed_new_texts": min(start + len(batch), len(pending)), "pending_texts": len(pending),
                    "cached_existing_texts": cache_hits, "total_ready_texts": cache_hits + min(start + len(batch), len(pending)),
                    "elapsed_seconds": round(time.monotonic() - started, 1), "paid_api_calls": 0}
        write_json(cache_directory / "progress.json", progress)
        if start % (arguments.batch_size * 10) == 0 or start + len(batch) == len(pending):
            print(json.dumps(progress), flush=True)
    if arguments.prime_public or arguments.prime_available:
        connection.close()
        return
    lookup = {text_hash: np.frombuffer(vector, dtype=np.float32).copy() for text_hash, vector in connection.execute("SELECT text_hash,vector FROM vectors")}
    vectors = np.zeros((3, len(cases), 1024), dtype=np.float32)
    for offset, case in enumerate(cases):
        for view, field in enumerate(VIEW_FIELDS):
            text = retrieval_text(case, field)
            if text:
                vectors[view, offset] = lookup[hashes[text]]
    np.savez_compressed(RELEASE / "inclusive_bge_m3.npz", case_ids=np.asarray([case["case_id"] for case in cases]),
                        problem_embeddings=vectors[0], task_embeddings=vectors[1], context_embeddings=vectors[2])
    write_json(RELEASE / "index_manifest.json", {"dataset_release": corpus["dataset_release"],
        "corpus_sha256": digest(RELEASE / "main_cases_v2_5.json"), "index_sha256": digest(RELEASE / "inclusive_bge_m3.npz"),
        "baseline_sha256": EXPECTED_FROZEN_HASH, "inherited_v24_index_sha256": digest(ROOT / "data/v2_4/expansion_bge_m3.npz"),
        "encoder": "BAAI/bge-m3", "dimensions": 1024, "new_text_max_tokens": MODEL_MAX_TOKENS,
        "new_retrievable_records": len(cases), "total_retrievable_records": len(cases) + 108,
        "zero_vectors_mean_unknown_view": True, "scoring": "MEAN_COSINE_OVER_NONMISSING_VIEWS", "paid_api_calls": 0})
    connection.close()
    print(json.dumps({"indexed_new_records": len(cases), "total_retrievable": len(cases) + 108}), flush=True)


if __name__ == "__main__":
    main()
