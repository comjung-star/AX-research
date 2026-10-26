import csv
import hashlib
import json
import tempfile
from pathlib import Path

import numpy as np
import pytest

from prototype.core import Engine, ROOT
from prototype.corpus import load_expansion
from prototype.storage import FeedbackStore
from scripts.build_ax_expansion_release import EXPECTED_FROZEN_HASH, FROZEN, RELEASE, identity_url, leakage_groups, screen_record


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_release_preserves_frozen_cases_and_taxonomy_without_fabricating_gold():
    assert hashlib.sha256(FROZEN.read_bytes()).hexdigest() == EXPECTED_FROZEN_HASH
    baseline = read_json(FROZEN)["cases"]
    corpus = read_json(RELEASE / "main_cases_v2_4.json")
    assert corpus["cases"][:84] == baseline
    additions = corpus["cases"][84:]
    assert len(additions) == corpus["counts"]["new_reviewed_workflows"] > 0
    identifiers = {case["case_id"] for case in corpus["cases"]}
    assert len(identifiers) == len(corpus["cases"])
    factors = {row["factor_id"] for row in csv.DictReader((ROOT / "data/v2_3/root_cause_taxonomy_v2_3.csv").open(encoding="utf-8-sig"))}
    strategies = {row["strategy_id"] for row in csv.DictReader((ROOT / "data/v2_3/strategy_taxonomy_v2_3.csv").open(encoding="utf-8-sig"))}
    for case in additions:
        assert set(case["factor_labels"]) <= factors
        assert set(case["strategy_labels"]) <= strategies
        assert case["deployment_stage"] == "PRODUCTION"
        assert case["human_ground_truth_approved"] is False
        assert case["quantitative_outcome_approved"] is False
        assert case["eligible_for_wald_confirmatory_analysis"] is False
        assert all(case["evidence_paragraph_indices"].values())


def test_every_collected_record_has_an_explicit_disposition_and_not_all_are_full_reviews():
    rows = list(csv.DictReader((RELEASE / "source_disposition.csv").open(encoding="utf-8-sig")))
    assert len(rows) == len({row["candidate_id"] for row in rows}) == 8430
    assert all(row["decision_reason"] for row in rows)
    assert {row["decision"] for row in rows} == {"EXCLUDE", "HOLD", "INCLUDE_REVIEWED_WORKFLOWS"}
    assert read_json(RELEASE / "review_summary.json")["full_content_review_completed_for_all_sources"] is False
    assert all(row["decision"] == "EXCLUDE" for row in rows if row["collection_kind"] == "PUBLIC_SECTOR_INVENTORY")


def test_new_relevance_sheet_is_entirely_unjudged():
    rows = list(csv.DictReader((RELEASE / "dev_relevance_annotation_sheet.csv").open(encoding="utf-8-sig")))
    count = read_json(RELEASE / "main_cases_v2_4.json")["counts"]["total"]
    assert len(rows) == 30 * count
    assert all(row["status"] == "UNJUDGED" and not row["relevance_0_4"] and not row["annotator_id"] for row in rows)


def test_uncertain_sources_are_held_not_silently_rejected_or_accepted():
    record = {"collection_kind": "ENTERPRISE_SOURCE", "collection_status": "FETCHED", "url": "https://example.test/a", "source_title": "AI platform", "triage_status": "AI_SIGNAL_FOUND_REVIEW_REQUIRED"}
    assert screen_record(record, set())[0] == "HOLD"
    assert screen_record({**record, "collection_status": "ACCESS_FAILED"}, set())[0] == "HOLD"


def test_portal_identity_and_transitive_grouping_prevent_split_leakage():
    assert identity_url("https://example.test/view?bcIdx=1&currMenu=2") != identity_url("https://example.test/view?bcIdx=2&currMenu=2")
    cases = [{"case_id": "one", "organization": "Acme", "source_url": "https://example.test/a", "sampling_group_id": "group-a"},
             {"case_id": "two", "organization": "Acme", "source_url": "https://example.test/b", "sampling_group_id": "group-b"},
             {"case_id": "three", "organization": "Different", "source_url": "https://example.test/b", "sampling_group_id": "group-c"}]
    groups = leakage_groups(cases)
    assert len(set(groups.values())) == 1


def test_expanded_dense_keeps_frozen_vectors_and_ranks_every_case_per_branch():
    frozen = Engine()
    expanded = Engine(profile="active")
    assert len(expanded.cases) > len(frozen.cases)
    np.testing.assert_array_equal(expanded.views[:, :84], frozen.views)
    result = expanded.recommend({"query": expanded.examples[0]["query"], "top_k": 10})
    assert result["corpus_version"] == expanded.corpus_version
    assert result["corpus_sha256"] == expanded.corpus_hash
    for branch in result["branches"]:
        vector = expanded.branch_vectors[f"{result['example_id']}|1|{branch['id']}"]
        scores = (expanded.views @ vector).mean(axis=0)
        expected = sorted(range(len(expanded.case_ids)), key=lambda offset: (-float(scores[offset]), expanded.case_ids[offset]))[:10]
        assert [case["case_id"] for case in branch["cases"]] == [expanded.case_ids[offset] for offset in expected]
        assert branch["candidate_count"] == len(expanded.cases)


def test_qci_replay_remains_bound_to_the_original_corpus():
    expanded = Engine(profile="active")
    result = expanded.recommend({"query": expanded.examples[0]["query"], "scorer": "qci_replay"})
    assert result["corpus_version"] == "v2.3.0"
    assert all(branch["candidate_count"] == 84 for branch in result["branches"])
    assert all(not case["case_id"].startswith("AXV24_") for branch in result["branches"] for case in branch["cases"])


def test_corrupt_index_is_rejected_before_using_search_vectors():
    frozen = Engine()
    with tempfile.TemporaryDirectory() as directory:
        temporary_root = Path(directory)
        release = temporary_root / "data/v2_4"
        release.mkdir(parents=True)
        for filename in ("main_cases_v2_4.json", "index_manifest.json"):
            (release / filename).write_bytes((RELEASE / filename).read_bytes())
        (release / "expansion_bge_m3.npz").write_bytes(b"corrupt index")
        with pytest.raises(ValueError, match="integrity mismatch"):
            load_expansion(temporary_root, frozen.cases, frozen.corpus_hash)


def test_expanded_corpus_loads_into_research_model_and_feedback_keeps_version():
    from ax_research.data import load_cases
    loaded = load_cases(RELEASE / "main_cases_v2_4.csv")
    engine = Engine(profile="active")
    assert {case.case_id for case in loaded} == set(engine.cases)
    new_case = next(case for case in loaded if case.case_id.startswith("AXV24_"))
    assert "implementation" not in new_case.problem_view_text()
    result = engine.recommend({"query": engine.examples[0]["query"]})
    branch = result["branches"][0]
    with tempfile.TemporaryDirectory() as directory:
        store = FeedbackStore(Path(directory) / "test.sqlite3")
        store.save(result, {"consent": True, "perspective_id": branch["id"], "case_id": branch["cases"][0]["case_id"], "rating": "partial", "comment": "검증용 임시 평가", "tester": "automated-test"})
        exported = json.loads(store.export("json"))
        assert exported["sessions"][0]["corpus_version"] == engine.corpus_version
        assert engine.corpus_version in store.export("csv").decode("utf-8-sig")
