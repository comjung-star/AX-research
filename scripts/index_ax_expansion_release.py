import json
import os

import numpy as np

from scripts.build_ax_expansion_release import EXPECTED_FROZEN_HASH, FROZEN, RELEASE, ROOT, digest, read_json, write_json


def main():
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    import torch
    from sentence_transformers import SentenceTransformer
    torch.set_num_threads(4)
    corpus = read_json(RELEASE / "main_cases_v2_4.json")
    baseline = read_json(FROZEN)["cases"]
    if digest(FROZEN) != EXPECTED_FROZEN_HASH or corpus["cases"][:len(baseline)] != baseline:
        raise ValueError("Frozen baseline was modified")
    additions = corpus["cases"][len(baseline):]
    model = SentenceTransformer(str(ROOT / ".local/models/bge-m3"), device="cpu", local_files_only=True)
    views = {}
    for field in ("problem", "task", "context"):
        views[field + "_embeddings"] = model.encode([case[field] for case in additions], batch_size=8,
                  normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False).astype(np.float32)
        print(field, views[field + "_embeddings"].shape, flush=True)
    np.savez_compressed(RELEASE / "expansion_bge_m3.npz", case_ids=np.asarray([case["case_id"] for case in additions]), **views)
    write_json(RELEASE / "index_manifest.json", {"corpus_sha256": digest(RELEASE / "main_cases_v2_4.json"),
               "baseline_sha256": EXPECTED_FROZEN_HASH, "encoder": "BAAI/bge-m3", "dimensions": 1024,
               "views": ["problem", "task", "context"], "new_cases": len(additions), "paid_api_calls": 0,
               "index_sha256": digest(RELEASE / "expansion_bge_m3.npz"),
               "baseline_index_sha256": digest(ROOT / "experiments/v23_dev/stage1/fixed_bge_m3_embeddings.npz"),
               "model_weights_sha256": digest(ROOT / ".local/models/bge-m3/model.safetensors") if (ROOT / ".local/models/bge-m3/model.safetensors").exists() else digest(ROOT / ".local/models/bge-m3/pytorch_model.bin")})
    print(json.dumps({"indexed_new_cases": len(additions), "paid_api_calls": 0}))


if __name__ == "__main__":
    main()
