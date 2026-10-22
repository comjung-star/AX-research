from ax_research.stage2_hybrid_runner import (
    candidate_perspective_coverage,
    candidate_recall,
)


def test_candidate_recall_uses_unordered_pool():
    assert candidate_recall({"A", "C"}, {"A", "B", "C", "D"}) == 0.5


def test_candidate_perspective_coverage():
    perspective_gold = {
        "R1": {"A", "B"},
        "R2": {"C"},
        "R3": {"D"},
    }
    assert candidate_perspective_coverage({"A", "C"}, perspective_gold) == 2 / 3
