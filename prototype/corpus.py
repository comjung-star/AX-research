import hashlib
import json

import numpy as np


def load_expansion(root, frozen_cases, frozen_hash):
    release = root / "data/v2_4"
    corpus_path = release / "main_cases_v2_4.json"
    index_path = release / "expansion_bge_m3.npz"
    corpus = json.loads(corpus_path.read_text(encoding="utf-8"))
    manifest = json.loads((release / "index_manifest.json").read_text(encoding="utf-8"))
    corpus_hash = hashlib.sha256(corpus_path.read_bytes()).hexdigest()
    if corpus_hash != manifest["corpus_sha256"] or hashlib.sha256(index_path.read_bytes()).hexdigest() != manifest["index_sha256"]:
        raise ValueError("Expanded corpus/index integrity mismatch")
    baseline_index = root / "experiments/v23_dev/stage1/fixed_bge_m3_embeddings.npz"
    if hashlib.sha256(baseline_index.read_bytes()).hexdigest() != manifest["baseline_index_sha256"]:
        raise ValueError("Frozen baseline embedding index changed")
    if manifest["baseline_sha256"] != frozen_hash or corpus["baseline_sha256"] != frozen_hash:
        raise ValueError("Expanded corpus baseline mismatch")
    cases = {case["case_id"]: case for case in corpus["cases"]}
    if len(cases) != len(corpus["cases"]) or any(cases.get(case_id) != case for case_id, case in frozen_cases.items()):
        raise ValueError("Expanded corpus must preserve all frozen case contents")
    with np.load(index_path, allow_pickle=False) as archive:
        case_ids = archive["case_ids"].tolist()
        views = np.stack([archive[field + "_embeddings"] for field in ("problem", "task", "context")])
    if len(case_ids) != len(set(case_ids)) or set(case_ids) != set(cases) - set(frozen_cases):
        raise ValueError("Expansion embedding membership mismatch")
    if views.shape != (3, len(case_ids), 1024) or not np.isfinite(views).all() or not np.allclose(np.linalg.norm(views, axis=2), 1, atol=1e-4):
        raise ValueError("Invalid expanded multi-view vectors")
    return {"cases": cases, "case_ids": case_ids, "views": views, "corpus_hash": corpus_hash,
            "version": corpus["dataset_release"], "status": corpus["status"]}


def load_inclusive(root, inherited_cases, inherited_hash):
    release = root / "data/v2_5"
    corpus_path = release / "main_cases_v2_5.json"
    index_path = release / "inclusive_bge_m3.npz"
    corpus = json.loads(corpus_path.read_text(encoding="utf-8"))
    manifest = json.loads((release / "index_manifest.json").read_text(encoding="utf-8"))
    corpus_hash = hashlib.sha256(corpus_path.read_bytes()).hexdigest()
    if corpus_hash != manifest["corpus_sha256"] or hashlib.sha256(index_path.read_bytes()).hexdigest() != manifest["index_sha256"]:
        raise ValueError("Inclusive corpus/index integrity mismatch")
    if corpus["prior_v24_corpus_sha256"] != inherited_hash:
        raise ValueError("Inherited reviewed corpus mismatch")
    if hashlib.sha256((root / "data/v2_4/expansion_bge_m3.npz").read_bytes()).hexdigest() != manifest["inherited_v24_index_sha256"]:
        raise ValueError("Inherited reviewed index changed")
    cases = {case["case_id"]: case for case in corpus["cases"]}
    if len(cases) != len(corpus["cases"]) or any(cases.get(case_id) != case for case_id, case in inherited_cases.items()):
        raise ValueError("Inclusive corpus must preserve reviewed cases")
    with np.load(index_path, allow_pickle=False) as archive:
        identifiers = archive["case_ids"].tolist()
        views = np.stack([archive[field + "_embeddings"] for field in ("problem", "task", "context")])
    expected = {case_id for case_id, case in cases.items() if case_id not in inherited_cases and case["retrieval_eligible"]}
    if len(identifiers) != len(set(identifiers)) or set(identifiers) != expected:
        raise ValueError("Inclusive searchable record membership mismatch")
    if views.shape != (3, len(identifiers), 1024) or not np.isfinite(views).all():
        raise ValueError("Inclusive vector shape or values invalid")
    norms = np.linalg.norm(views, axis=2)
    if not np.all(np.isclose(norms, 0, atol=1e-6) | np.isclose(norms, 1, atol=1e-4)) or np.any(np.all(norms == 0, axis=0)):
        raise ValueError("Missing views must be zero; available vectors must be normalized")
    return {"cases": cases, "case_ids": identifiers, "views": views, "corpus_hash": corpus_hash,
            "version": corpus["dataset_release"], "metadata": corpus["inherited_case_metadata"]}
