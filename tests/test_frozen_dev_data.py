"""Frozen Dev 데이터의 기본 조건을 실제 CSV로 검사합니다."""

from ax_research.data import (
    load_cases,
    load_gold,
    load_queries,
    load_relevance_labels,
)


def test_frozen_dev_counts():
    assert len(load_cases()) == 100
    assert len(load_queries()) == 10
    assert len(load_relevance_labels()) == 3000
    assert len(load_gold()) == 10


def test_all_active_queries_are_adjudicated():
    queries = load_queries()
    assert all(
        q.status == "PILOT_GOLD_ADJUDICATED"
        for q in queries
    )
