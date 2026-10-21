import csv
from pathlib import Path

from ax_research.config import RQ1Config
from ax_research.data import AXCase, GoldRecord, RelevanceLabel, RetrievalQuery
from ax_research.gpt_only_runner import run_gpt_only
from ax_research.llm.schemas import GPTOnlyRankedCase, GPTOnlyResponse


class FakeGPTOnlyClient:
    def gpt_only_rank(self, business_problem, cases, *, top_n):
        ids = [case.case_id for case in cases[:top_n]]
        return GPTOnlyResponse(
            ranked_cases=[GPTOnlyRankedCase(case_id=i, reason="test") for i in ids]
        )


def test_gpt_only_runner_repeats_and_writes_metrics(tmp_path: Path):
    config = RQ1Config(
        experiment_id="test",
        query_ids=("Q1",),
        evaluation_k=(1, 2),
        gold_threshold=3,
        dense_model="dummy",
        llm_repeats=3,
    )
    cases = [
        AXCase("A", "", "", "", ("S1",)),
        AXCase("B", "", "", "", ("S2",)),
        AXCase("C", "", "", "", ("S3",)),
    ]
    queries = [RetrievalQuery("Q1", "문제", "", "", "", "OK")]
    labels = [
        RelevanceLabel("Q1", "P1", "A", 4),
        RelevanceLabel("Q1", "P2", "B", 3),
    ]
    gold = [GoldRecord("Q1", ("P1", "P2"), ("A", "B"), ("S1", "S2"), "OK")]

    ranking_path, metrics_path = run_gpt_only(
        client=FakeGPTOnlyClient(),
        config=config,
        cases=cases,
        queries=queries,
        labels=labels,
        gold_records=gold,
        output_dir=tmp_path,
    )

    with metrics_path.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 6
    assert {row["run_id"] for row in rows} == {"1", "2", "3"}
    assert ranking_path.exists()
