"""Focused tests for exact Stage 3-2A retrieval lineage preservation."""
import pytest

from ax_research.stage3_perspective_provenance import reconstruct


def rank(rank="1", case="AX1", perspective="P2"):
    return {
        "system": "stage2_same_pool_rrf", "leg_k": "10",
        "query_id": "Q1", "run_id": "1", "final_rank": rank,
        "case_id": case, "source_perspective_id": perspective,
    }


def candidate(perspective="P1", case="AX1", source="dense"):
    return {
        "leg_k": "10", "query_id": "Q1", "run_id": "1",
        "case_id": case, "perspective_id": perspective,
        "source": source, "dense_rank": "2", "sparse_rank": "",
    }


def execute(rankings=None, candidates=None, top_k=1):
    return reconstruct(
        [rank()] if rankings is None else rankings,
        [candidate("P1"), candidate("P2", source="both")]
        if candidates is None else candidates,
        {"AX1", "AX2"}, {"Q1"}, runs=("1",), top_k=top_k,
    )


def test_preserves_all_perspectives_without_duplicating_case():
    rows, summary = execute()
    assert [r["perspective_id"] for r in rows] == ["P1", "P2"]
    assert [r["is_selected_perspective"] for r in rows] == [False, True]
    assert summary["ranked_case_occurrences"] == 1
    assert summary["perspective_case_links"] == 2
    assert summary["multi_perspective_case_occurrences"] == 1
    assert all("is_gold" not in r for r in rows)


def test_dynamic_perspective_p4_allowed():
    rows, summary = execute(candidates=[candidate("P2"), candidate("P4")])
    assert summary["link_count_by_perspective"] == {"P2": 1, "P4": 1}


def test_missing_candidate_is_error_not_ignored():
    with pytest.raises(ValueError, match="provenance"):
        execute(candidates=[])


def test_selected_perspective_must_be_among_candidate_paths():
    with pytest.raises(ValueError, match="selected perspective"):
        execute(candidates=[candidate("P1")])


def test_candidate_duplicate_perspective_is_error():
    with pytest.raises(ValueError, match="Duplicate"):
        execute(candidates=[candidate("P2"), candidate("P2")])


def test_ranking_duplicate_case_is_error():
    with pytest.raises(ValueError, match="duplicated"):
        execute(
            rankings=[rank("1"), rank("2")],
            candidates=[candidate("P2")],
            top_k=2,
        )


def test_ranking_missing_query_run_group_is_error():
    with pytest.raises(ValueError, match="groups"):
        reconstruct([], [candidate("P2")], {"AX1"}, {"Q1"}, runs=("1",))


def test_two_distinct_ranked_cases_preserve_top_k_denominator():
    rows, summary = execute(
        rankings=[rank("1"), rank("2", case="AX2")],
        candidates=[
            candidate("P2"), candidate("P3"),
            candidate("P2", case="AX2"),
        ], top_k=2,
    )
    assert summary["ranked_case_occurrences"] == 2
    assert summary["perspective_case_links"] == 3
    assert [r["final_rank"] for r in rows] == [1, 1, 2]
