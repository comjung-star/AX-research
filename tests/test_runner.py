import csv
from pathlib import Path

from ax_research.config import RQ1Config
from ax_research.data import AXCase, GoldRecord, RelevanceLabel, RetrievalQuery
from ax_research.runner import run_single_query_baseline


class _Result:
    def __init__(self, case_id, score):
        self.case_id = case_id
        self.score = score


class FakeRetriever:
    def search(self, query, top_k=None):
        rows = [_Result("A", 1.0), _Result("X", 0.8), _Result("B", 0.7)]
        return rows if top_k is None else rows[:top_k]


def test_runner_writes_rankings_and_metrics(tmp_path: Path):
    config = RQ1Config(
        experiment_id="test",
        query_ids=("Q1",),
        evaluation_k=(2,),
        gold_threshold=3,
        dense_model="dummy",
    )
    cases = [
        AXCase("A", "", "", "", ("S1",)),
        AXCase("B", "", "", "", ("S2",)),
        AXCase("X", "", "", "", ("S9",)),
    ]
    queries = [RetrievalQuery("Q1", "업무문제", "goal", "context", "", "OK")]
    labels = [
        RelevanceLabel("Q1", "P1", "A", 4),
        RelevanceLabel("Q1", "P2", "B", 3),
    ]
    gold = [GoldRecord("Q1", ("P1", "P2"), ("A", "B"), ("S1", "S2"), "OK")]

    ranking_path, metrics_path = run_single_query_baseline(
        system_name="fake",
        retriever=FakeRetriever(),
        config=config,
        cases=cases,
        queries=queries,
        labels=labels,
        gold_records=gold,
        output_dir=tmp_path,
    )

    with metrics_path.open(encoding="utf-8") as f:
        row = next(csv.DictReader(f))
    assert row["recall"] == "0.5"
    assert row["perspective_coverage"] == "0.5"
    assert row["strategy_coverage"] == "0.5"
    assert ranking_path.exists()
