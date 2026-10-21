from ax_research.data import AXCase, RelevanceLabel
from ax_research.evaluation import (
    build_perspective_gold,
    evaluate_at_k,
    gold_delta_at_k,
    perspective_coverage_at_k,
    recall_at_k,
    unique_gold_recovery,
)


def test_recall_at_k():
    ranked = ["A", "X", "B", "Y"]
    assert recall_at_k(ranked, {"A", "B", "C"}, 3) == 2 / 3


def test_perspective_coverage_at_k():
    gold = {"P1": {"A"}, "P2": {"B", "C"}, "P3": {"D"}}
    assert perspective_coverage_at_k(["A", "X", "B", "D"], gold, 3) == 2 / 3


def test_build_perspective_gold_uses_threshold():
    labels = [
        RelevanceLabel("Q1", "P1", "A", 4),
        RelevanceLabel("Q1", "P1", "B", 2),
        RelevanceLabel("Q1", "P2", "C", 3),
    ]
    assert build_perspective_gold(labels, query_id="Q1", threshold=3) == {
        "P1": {"A"},
        "P2": {"C"},
    }


def test_unique_gold_recovery():
    result = unique_gold_recovery(
        baseline_case_ids=["A", "B", "X"],
        proposed_case_ids=["A", "C", "D"],
        gold_case_ids={"A", "B", "C", "D"},
        k=3,
    )
    assert result == {"C", "D"}


def test_gold_delta_records_gained_lost_and_net():
    delta = gold_delta_at_k(
        baseline_case_ids=["A", "B", "C"],
        proposed_case_ids=["A", "D", "X"],
        gold_case_ids={"A", "B", "C", "D"},
        k=3,
    )
    assert delta.gained == frozenset({"D"})
    assert delta.lost == frozenset({"B", "C"})
    assert delta.net == -1


def test_evaluate_at_k():
    cases = {
        "A": AXCase("A", "", "", "", ("S1",)),
        "B": AXCase("B", "", "", "", ("S2",)),
        "X": AXCase("X", "", "", "", ("S9",)),
    }
    metrics = evaluate_at_k(
        ranked_case_ids=["A", "X", "B"],
        gold_case_ids={"A", "B"},
        perspective_gold={"P1": {"A"}, "P2": {"B"}},
        case_index=cases,
        gold_strategies={"S1", "S2"},
        k=2,
    )
    assert metrics.recall == 0.5
    assert metrics.perspective_coverage == 0.5
    assert metrics.strategy_coverage == 0.5
