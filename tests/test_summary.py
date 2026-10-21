import csv

from ax_research.summary import summarize_metrics


def test_summarize_metrics_uses_all_runs(tmp_path):
    src = tmp_path / "metrics.csv"
    out = tmp_path / "summary.csv"

    with src.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "system",
                "run_id",
                "query_id",
                "k",
                "recall",
                "perspective_coverage",
                "strategy_coverage",
            ],
        )
        w.writeheader()
        for run_id, recall in [(1, 0.5), (2, 0.7), (3, 0.6)]:
            w.writerow(
                {
                    "system": "gpt_only",
                    "run_id": run_id,
                    "query_id": "Q1",
                    "k": 10,
                    "recall": recall,
                    "perspective_coverage": 1.0,
                    "strategy_coverage": 0.5,
                }
            )

    summarize_metrics(src, out)

    with out.open(encoding="utf-8") as f:
        row = next(csv.DictReader(f))

    assert row["row_count"] == "3"
    assert abs(float(row["mean_recall"]) - 0.6) < 1e-12
    assert float(row["min_recall"]) == 0.5
    assert float(row["max_recall"]) == 0.7
