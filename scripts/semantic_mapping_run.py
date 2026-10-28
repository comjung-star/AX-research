"""Freeze, then run label-free offline BGE-M3 field mapping. No Silver imports."""

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import socket
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from ax_research.semantic_mapping import aggregate, combined_score, compare_fields, field_profile, ranking_key

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/semantic_mapping_20261028.json"
CFG = json.loads(CONFIG.read_text(encoding="utf-8-sig"))
OUT = ROOT / CFG["output"]
INPUT = ROOT / CFG["inputs"]
HIST = ROOT / CFG["historical"]


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def digest(path):
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def save(name, value):
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def jsonl(name, rows):
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")


def lines(path):
    with path.open(encoding="utf-8-sig") as stream:
        return [json.loads(line) for line in stream]


def blocked(*args, **kwargs):
    raise RuntimeError("Network disabled in semantic mapping experiment")


def protected_files():
    names = [INPUT / name for name in ("query_registry.json", "case_registry.json", "candidate_features.jsonl",
             "mapping_candidate_pools.jsonl", "mapping_schema.json", "mapping_input_examples.json")]
    names += [ROOT / "configs/functional_mapping_20261028.json", ROOT / "src/ax_research/functional_mapping.py",
              HIST / "stage2/case_profiles.json", HIST / "stage2/query_profiles.json", HIST / "stage3/rankings.json"]
    return names


def freeze():
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip() == CFG["base_commit"]
    protected = {}
    for path in protected_files():
        relative = path.relative_to(ROOT).as_posix()
        original = subprocess.check_output(["git", "show", CFG["base_commit"] + ":" + relative], cwd=ROOT)
        assert path.read_bytes().replace(b"\r\n", b"\n") == original.replace(b"\r\n", b"\n"), relative
        protected[relative] = digest(path)
    model = (ROOT / CFG["model_path"]).resolve()
    model_hashes = {path.relative_to(model).as_posix(): digest(path) for path in sorted(model.rglob("*"))
                    if path.is_file() and ".cache" not in path.relative_to(model).parts}
    code = {path.relative_to(ROOT).as_posix(): digest(path) for path in (
        CONFIG, ROOT / "src/ax_research/semantic_mapping.py", ROOT / "scripts/semantic_mapping_run.py",
        ROOT / "scripts/semantic_mapping_evaluate.py", ROOT / "tests/test_semantic_mapping.py",
        OUT / "protocol.md")}
    state = {"config": CFG, "protected_sha256": protected, "algorithm_sha256": code,
             "model_sha256": model_hashes, "python": platform.python_version(),
             "packages": {name: importlib.metadata.version(name) for name in
                          ("numpy", "torch", "transformers", "sentence-transformers")},
             "frozen_before_inference": True, "silver_read": False, "independent_test_read": False}
    if (OUT / "preregistration.json").exists():
        old = read(OUT / "preregistration.json")
        assert all(old[key] == value for key, value in state.items()), "Frozen configuration changed"
    else:
        state["created_utc"] = datetime.now(timezone.utc).isoformat()
        save("preregistration.json", state)
    print("Preregistration SHA256:", digest(OUT / "preregistration.json"), flush=True)


def verify_freeze():
    frozen = read(OUT / "preregistration.json")
    for group in ("algorithm_sha256", "protected_sha256"):
        for name, expected in frozen[group].items():
            assert digest(ROOT / name) == expected, name
    return frozen


def run():
    verify_freeze()
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    import torch
    from sentence_transformers import SentenceTransformer

    torch.manual_seed(CFG["seed"])
    np.random.seed(CFG["seed"])
    torch.set_num_threads(CFG["threads"])
    torch.use_deterministic_algorithms(True)
    cases = read(INPUT / "case_registry.json")["cases"]
    queries = read(INPUT / "query_registry.json")["paths"]
    assert len(cases) == 112 and len(queries) == 118
    assert sum(query["scope"] == "dynamic" for query in queries.values()) == 108
    rules = read(ROOT / "configs/functional_mapping_20261028.json")
    query_profiles = {key: field_profile(value["query_text"], CFG, rules["negation_guard"])
                      for key, value in queries.items()}
    case_profiles = {key: field_profile(value["task"], CFG, rules["negation_guard"], executed=True,
                                       context=value["context"]) for key, value in cases.items()}
    save("mapping/query_profiles.json", query_profiles)
    save("mapping/case_profiles.json", case_profiles)
    texts = sorted({text for profile in [*query_profiles.values(), *case_profiles.values()]
                    for text in profile["fields"].values() if text})
    model_path = (ROOT / CFG["model_path"]).resolve()
    pooling = read(model_path / "1_Pooling/config.json")
    assert pooling["pooling_mode_cls_token"] and not pooling["pooling_mode_mean_tokens"]
    model = SentenceTransformer(str(model_path), device=CFG["device"], local_files_only=True)
    model.max_seq_length = CFG["max_tokens"]
    lengths = [len(model.tokenizer.encode(text)) for text in texts]
    assert max(lengths) <= CFG["max_tokens"], "No silent truncation permitted"
    print(f"Encoding {len(texts)} unique literal field texts; maximum {max(lengths)} tokens", flush=True)
    vectors = model.encode(texts, batch_size=CFG["batch_size"], normalize_embeddings=True,
                           convert_to_numpy=True, show_progress_bar=True).astype(np.float32)
    assert vectors.shape == (len(texts), CFG["dimensions"]) and np.isfinite(vectors).all()
    assert np.allclose(np.linalg.norm(vectors, axis=1), 1, atol=1e-5)
    np.savez_compressed(OUT / "mapping/embeddings.npz", texts=np.array(texts), vectors=vectors)
    embeddings = dict(zip(texts, vectors))
    mappings = []
    lookup = {}
    for path_id, query in query_profiles.items():
        for case_id, case in case_profiles.items():
            comparison = compare_fields(query, case, embeddings, CFG["weights"])
            lookup[path_id, case_id] = comparison
            mappings.append({"path_id": path_id, "case_id": case_id, **comparison})
    jsonl("mapping/mappings.jsonl", mappings)
    old = read(HIST / "stage3/rankings.json")["systems"]
    names = {"C": "O_SINGLE", "F": "D_SINGLE", "S_C3": "O_THREE", "S_F3": "D_THREE"}
    systems = {}
    explanations = []
    for pool in lines(INPUT / "mapping_candidate_pools.jsonl"):
        suffix = names[pool["condition"]]
        original = "o_" + pool["qid"]
        branch_paths = [path for path in pool["path_ids"] if queries[path]["scope"] == "dynamic"]
        reference = next(row for row in old["M_" + suffix]
                         if row["qid"] == pool["qid"] and row["repeat"] == pool["repeat"])
        scores = {}
        for case_id in pool["candidate_ids_ranked_all112"]:
            whole = lookup[original, case_id]["score"]
            branches = [lookup[path, case_id]["score"] for path in branch_paths]
            semantic = aggregate(whole, branches)
            strength = max(reference["whole_grades"][case_id], reference["best_perspective_grades"][case_id])
            scores[case_id] = {"SEM": semantic, "COMB": combined_score(strength, semantic)}
            explanations.append({"condition": suffix, "qid": pool["qid"], "repeat": pool["repeat"],
                                 "case_id": case_id, "whole_score": whole,
                                 "branch_scores": {path: lookup[path, case_id]["score"] for path in branch_paths},
                                 "rule_strength": strength, "scores": scores[case_id]})
        for method in ("SEM", "COMB"):
            ranking = sorted(scores, key=lambda case_id: ranking_key(
                scores[case_id][method], pool["final_retrieval_score"][case_id], case_id))
            assert len(set(ranking)) == 112
            systems.setdefault(method + "_" + suffix, []).append({
                "qid": pool["qid"], "repeat": pool["repeat"], "ranking": ranking,
                "path_ids": pool["path_ids"], "retrieval_reference": pool["condition"]})
    save("ranking/rankings.json", {"systems": systems, "labels_read": False, "primary": CFG["primary"]})
    jsonl("ranking/explanations.jsonl", explanations)
    baseline_profiles = read(HIST / "stage2/case_profiles.json")
    unknown_ids = sorted(key for key, value in baseline_profiles.items() if not value["task"]["function_ids"])
    assert len(unknown_ids) == 33
    save("mapping/unknown33.json", {"case_ids": unknown_ids, "records": [
        {"case_id": key, "actual_task": cases[key]["task"], "profile": case_profiles[key]} for key in unknown_ids]})
    artifacts = ["mapping/query_profiles.json", "mapping/case_profiles.json", "mapping/mappings.jsonl",
                 "mapping/embeddings.npz", "mapping/unknown33.json", "ranking/rankings.json", "ranking/explanations.jsonl"]
    save("prediction_receipt.json", {"created_utc": datetime.now(timezone.utc).isoformat(),
         "preregistration_sha256": digest(OUT / "preregistration.json"),
         "artifact_sha256": {name: digest(OUT / name) for name in artifacts},
         "label_inputs": [], "independent_test_access": False, "new_api_calls": 0,
         "training": False, "unique_texts": len(texts), "max_tokens_observed": max(lengths),
         "unknown33_with_nonempty_task": sum(bool(case_profiles[key]["fields"]["task"]) for key in unknown_ids),
         "model_files_verified": {name: digest(model_path / name) for name in read(OUT / "preregistration.json")["model_sha256"]}})
    assert read(OUT / "prediction_receipt.json")["model_files_verified"] == read(OUT / "preregistration.json")["model_sha256"]
    verify_freeze()
    print("Predictions frozen; no Silver read. Receipt:", digest(OUT / "prediction_receipt.json"), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=("freeze", "run"))
    args = parser.parse_args()
    socket.socket.connect = blocked
    socket.create_connection = blocked
    {"freeze": freeze, "run": run}[args.stage]()
