from ax_research.data import RelevanceLabel
from ax_research.diagnostics import (
    build_exclusive_perspective_gold,
    exclusive_perspective_coverage_at_k,
    mean_perspective_recall_at_k,
)


def test_exclusive_gold_removes_shared_cases():
    labels = [
        RelevanceLabel("Q1", "P1", "A", 4),
        RelevanceLabel("Q1", "P1", "B", 4),
        RelevanceLabel("Q1", "P2", "B", 4),
        RelevanceLabel("Q1", "P2", "C", 3),
        RelevanceLabel("Q1", "P3", "B", 3),
        RelevanceLabel("Q1", "P3", "D", 4),
    ]
    result = build_exclusive_perspective_gold(labels, query_id="Q1")
    assert result == {"P1": {"A"}, "P2": {"C"}, "P3": {"D"}}


def test_exclusive_coverage_ignores_perspectives_without_exclusive_gold():
    gold = {"P1": {"A"}, "P2": set(), "P3": {"D"}}
    assert exclusive_perspective_coverage_at_k(["A", "X"], gold, 2) == 0.5


def test_mean_perspective_recall_is_not_binary_coverage():
    gold = {"P1": {"A", "B"}, "P2": {"C", "D"}}
    # A and C mean both perspectives are covered, but each recall is 1/2.
    assert mean_perspective_recall_at_k(["A", "C"], gold, 2) == 0.5
