import csv

from ax_research.comparison import compare_gold_recovery
from ax_research.data import GoldRecord


def _write(path, fieldnames, rows):
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def test_compare_gold_recovery_records_gain_loss_and_net(tmp_path):
    baseline = tmp_path / "baseline.csv"
    mp = tmp_path / "mp.csv"
    out = tmp_path / "diag.csv"

    _write(
        baseline,
        ["query_id", "rank", "case_id"],
        [
            {"query_id": "Q1", "rank": 1, "case_id": "A"},
            {"query_id": "Q1", "rank": 2, "case_id": "B"},
            {"query_id": "Q1", "rank": 3, "case_id": "C"},
        ],
    )
    _write(
        mp,
        ["query_id", "run_id", "final_rank", "case_id"],
        [
            {"query_id": "Q1", "run_id": 1, "final_rank": 1, "case_id": "A"},
            {"query_id": "Q1", "run_id": 1, "final_rank": 2, "case_id": "D"},
            {"query_id": "Q1", "run_id": 1, "final_rank": 3, "case_id": "X"},
        ],
    )

    gold = [
        GoldRecord(
            "Q1",
            ("P1",),
            ("A", "B", "C", "D"),
            ("S1",),
            "OK",
        )
    ]

    compare_gold_recovery(
        baseline_ranking_csv=baseline,
        multi_perspective_final_ranking_csv=mp,
        gold_records=gold,
        k_values=(3,),
        output_csv=out,
    )

    with out.open(encoding="utf-8") as f:
        row = next(csv.DictReader(f))

    assert row["gained_gold_count"] == "1"
    assert row["lost_gold_count"] == "2"
    assert row["net_gold_change"] == "-1"
    assert row["gained_gold_cases"] == "D"
    assert row["lost_gold_cases"] == "B|C"
