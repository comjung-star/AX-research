import json
import os
from collections import Counter

import numpy as np

from scripts.audit_final_dataset import OUTPUT, ROOT, fingerprint
from scripts.build_ax_expansion_release import digest, read_json, write_json
from scripts.prepare_v25_research import write_csv


def main():
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    cases = read_json(OUTPUT / "source_supported_candidates.json")["cases"]
    identifiers = [case["case_id"] for case in cases]
    input_hash = fingerprint(cases)
    index_path = OUTPUT / "candidate_bge_m3_128.npz"
    index_manifest = OUTPUT / "candidate_index_manifest.json"
    if not index_path.is_file():
        import torch
        from sentence_transformers import SentenceTransformer
        torch.set_num_threads(8)
        torch.manual_seed(20261026)
        np.random.seed(20261026)
        model_directory = ROOT / ".local/models/bge-m3"
        weights = next(path for path in [model_directory / "model.safetensors", model_directory / "pytorch_model.bin"] if path.is_file())
        if digest(weights) != read_json(ROOT / "data/v2_4/index_manifest.json")["model_weights_sha256"]:
            raise ValueError("Local encoder weights differ from frozen inherited model")
        model = SentenceTransformer(str(model_directory), device="cpu", local_files_only=True)
        model.max_seq_length = 128
        texts = [case[field] for field in ("problem", "task", "context") for case in cases]
        vectors = model.encode(texts, batch_size=16, normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False).astype(np.float32)
        views = vectors.reshape(3, len(cases), 1024)
        np.savez_compressed(index_path, case_ids=np.asarray(identifiers), views=views)
        write_json(index_manifest, {"candidate_fingerprint": input_hash, "index_sha256": digest(index_path),
                                    "encoder": "BAAI/bge-m3", "model_weights_sha256": digest(weights),
                                    "view_fields": ["problem", "task", "context"], "max_tokens": 128, "dimensions": 1024,
                                    "excluded_from_encoding": ["implementation", "outcome", "factor", "strategy"], "paid_api_calls": 0})
    manifest = read_json(index_manifest)
    assert manifest["candidate_fingerprint"] == input_hash and manifest["index_sha256"] == digest(index_path)
    with np.load(index_path, allow_pickle=False) as archive:
        assert archive["case_ids"].tolist() == identifiers
        views = archive["views"]
    assert views.shape == (3, len(cases), 1024) and np.isfinite(views).all()
    assert np.allclose(np.linalg.norm(views, axis=2), 1, atol=1e-4)
    similarities = views @ np.transpose(views, (0, 2, 1))
    mean = np.mean(similarities, axis=0)
    selected = set()
    for first in range(len(cases)):
        neighbors = sorted((second for second in range(len(cases)) if second != first), key=lambda second: -float(mean[first, second]))[:3]
        for second in neighbors:
            selected.add(tuple(sorted((first, second))))
    rows = []
    for first, second in sorted(selected, key=lambda pair: -float(mean[pair[0], pair[1]])):
        rows.append({"case_id_a": identifiers[first], "case_id_b": identifiers[second],
                     "mean_three_view_cosine": round(float(mean[first, second]), 6),
                     "problem_cosine": round(float(similarities[0, first, second]), 6),
                     "task_cosine": round(float(similarities[1, first, second]), 6),
                     "same_known_group": cases[first]["leakage_group_id"] == cases[second]["leakage_group_id"],
                     "organization_a": cases[first]["organization"], "organization_b": cases[second]["organization"],
                     "task_a": cases[first]["task"], "task_b": cases[second]["task"]})
    write_csv(OUTPUT / "semantic_nearest_pairs.csv", rows, list(rows[0]))
    exact = Counter(fingerprint({field: case[field] for field in ("organization", "problem", "task", "context", "implementation")}) for case in cases)
    report = {"candidate_count": len(cases), "candidate_fingerprint": input_hash, "index_shape": list(views.shape),
              "known_group_count": len({case["leakage_group_id"] for case in cases}),
              "exact_full_workflow_duplicates": sum(count - 1 for count in exact.values()),
              "top3_neighbor_pairs": len(rows), "mean_cosine_at_least_085": sum(row["mean_three_view_cosine"] >= 0.85 for row in rows),
              "problem_cosine_at_least_090": sum(row["problem_cosine"] >= 0.90 for row in rows),
              "all_source_urls_present": all(case["source_url"].startswith("https://") for case in cases),
              "all_problem_views_present": all(all(case[field] and not case[field].startswith("UNKNOWN") for field in ("problem", "task", "context")) for case in cases),
              "semantic_adjudication_completed": False, "human_gold": False, "paid_api_calls": 0}
    write_json(OUTPUT / "candidate_integrity.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
