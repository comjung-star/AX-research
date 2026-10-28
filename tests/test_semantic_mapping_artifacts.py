import numpy as np
import pytest

from scripts import semantic_mapping_evaluate as evaluation
from scripts import semantic_mapping_run as run

pytestmark = pytest.mark.skipif(not (run.OUT / "evaluation/results.json").exists(), reason="Frozen experiment artifacts not generated")


def test_frozen_inputs_code_model_and_predictions_unchanged():
    frozen = run.verify_freeze()
    receipt = run.read(run.OUT / "prediction_receipt.json")
    assert receipt["preregistration_sha256"] == run.digest(run.OUT / "preregistration.json")
    for name, expected in receipt["artifact_sha256"].items():
        assert run.digest(run.OUT / name) == expected
    assert frozen["model_sha256"] == receipt["model_files_verified"]
    assert receipt["label_inputs"] == []
    assert receipt["independent_test_access"] is False


def test_all_paths_cases_branches_and_embedding_norms_preserved():
    profiles = run.read(run.OUT / "mapping/query_profiles.json")
    cases = run.read(run.OUT / "mapping/case_profiles.json")
    queries = run.read(run.INPUT / "query_registry.json")["paths"]
    assert len(profiles) == 118 and len(cases) == 112
    assert sum(query["scope"] == "dynamic" for query in queries.values()) == 108
    for path_id, profile in profiles.items():
        assert profile["source_text"] == queries[path_id]["query_text"]
    with np.load(run.OUT / "mapping/embeddings.npz", allow_pickle=False) as cache:
        assert cache["vectors"].shape == (len(cache["texts"]), 1024)
        assert np.isfinite(cache["vectors"]).all()
        assert np.allclose(np.linalg.norm(cache["vectors"], axis=1), 1, atol=1e-5)
    mappings = run.lines(run.OUT / "mapping/mappings.jsonl")
    assert len(mappings) == len({(row["path_id"], row["case_id"]) for row in mappings}) == 13216


def test_new_rankings_keep_same_candidate_universe_and_historical_exact():
    systems = run.read(run.OUT / "evaluation/results.json")["systems"]
    historical = run.read(run.HIST / "stage4_dev/results.json")["systems"]
    case_ids = set(run.read(run.INPUT / "case_registry.json")["cases"])
    assert len(systems) == 26
    assert sum(len(rows) for name, rows in systems.items() if name.startswith(("SEM_", "COMB_"))) == 160
    for name, rows in systems.items():
        for row in rows:
            assert set(row["ranking"]) == case_ids and len(row["ranking"]) == 112
        if name in historical:
            assert [row["ranking"] for row in rows] == [row["ranking"] for row in historical[name]]


def test_every_reported_metric_is_recomputed_from_same_frozen_silver():
    label_file = run.ROOT / "docs/stage123-openai-triplicate-2026-10-27/stage1_silver.json"
    results = run.read(run.OUT / "evaluation/results.json")
    assert run.digest(label_file) == results["silver_sha256"]
    positive = {}
    for row in run.read(label_file)["records"]:
        if row["silver_score"] >= 3:
            positive.setdefault(row["qid"], set()).add(row["cid"])
    assert sum(map(len, positive.values())) == 18
    for rows in results["systems"].values():
        for row in rows:
            for count in (5, 10, 20):
                assert evaluation.metric(row["ranking"], positive.get(row["qid"], set()), count) == row["metrics"][str(count)]


def test_gain_loss_sets_are_exact_set_differences():
    results = run.read(run.OUT / "evaluation/results.json")["systems"]
    for event in run.read(run.OUT / "evaluation/related_changes.json")["events"]:
        current = evaluation.align(results[event["system"]], event["qid"], event["repeat"])
        previous = evaluation.align(results[event["reference"]], event["qid"], event["repeat"])
        after = set(current["metrics"][str(event["k"])]["related_ids"])
        before = set(previous["metrics"][str(event["k"])]["related_ids"])
        assert set(event["new"]) == after - before
        assert set(event["lost"]) == before - after
        assert set(event["retained"]) == before & after


def test_zero_positive_query_metrics_and_repeat_alignment():
    ranking = [f"case_{index}" for index in range(112)]
    assert evaluation.metric(ranking, set(), 5) == {
        "precision": 0, "recall": None, "f1": None, "true_positives": 0, "related_ids": []}
    deterministic = {"qid": "query", "repeat": 0}
    dynamic = {"qid": "query", "repeat": 2}
    assert evaluation.align([deterministic], "query", 3) == deterministic
    assert evaluation.align([deterministic, dynamic], "query", 2) == dynamic


def test_all_cosines_replay_from_saved_vectors_without_labels_or_model():
    queries = run.read(run.OUT / "mapping/query_profiles.json")
    cases = run.read(run.OUT / "mapping/case_profiles.json")
    with np.load(run.OUT / "mapping/embeddings.npz", allow_pickle=False) as cache:
        vectors = dict(zip(cache["texts"].tolist(), cache["vectors"]))
    for row in run.lines(run.OUT / "mapping/mappings.jsonl"):
        replay = run.compare_fields(queries[row["path_id"]], cases[row["case_id"]], vectors, run.CFG["weights"])
        assert replay["score"] == row["score"]
        assert replay["components"] == row["components"]


def test_all_rankings_replay_from_frozen_formula_and_original_pools():
    predictions = run.read(run.OUT / "ranking/rankings.json")["systems"]
    original_rules = run.read(run.HIST / "stage3/rankings.json")["systems"]
    mappings = {(row["path_id"], row["case_id"]): row for row in run.lines(run.OUT / "mapping/mappings.jsonl")}
    suffixes = {"C": "O_SINGLE", "F": "D_SINGLE", "S_C3": "O_THREE", "S_F3": "D_THREE"}
    for pool in run.lines(run.INPUT / "mapping_candidate_pools.jsonl"):
        suffix = suffixes[pool["condition"]]
        rule_row = evaluation.align(original_rules["M_" + suffix], pool["qid"], pool["repeat"])
        scores = {"SEM": {}, "COMB": {}}
        for case_id in pool["candidate_ids_ranked_all112"]:
            original = "o_" + pool["qid"]
            branch_scores = [mappings[path_id, case_id]["score"] for path_id in pool["path_ids"] if path_id != original]
            semantic = run.aggregate(mappings[original, case_id]["score"], branch_scores)
            strength = max(rule_row["whole_grades"][case_id], rule_row["best_perspective_grades"][case_id])
            scores["SEM"][case_id] = semantic
            scores["COMB"][case_id] = run.combined_score(strength, semantic)
        for method in ("SEM", "COMB"):
            replay = sorted(scores[method], key=lambda case_id: run.ranking_key(
                scores[method][case_id], pool["final_retrieval_score"][case_id], case_id))
            assert replay == evaluation.align(predictions[method + "_" + suffix], pool["qid"], pool["repeat"])["ranking"]
