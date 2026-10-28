import csv
import json
import re
import statistics
from pathlib import Path

import pytest

from scripts import semantic_mapping_run as source

REPORT = source.ROOT / "docs/query-case-semantic-mapping-report-2026-10-28"
pytestmark = pytest.mark.skipif(not (REPORT / "README.md").exists(), reason="Publication report not generated")


def rows(name):
    with (REPORT / name).open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def test_published_metrics_and_deltas_match_completed_experiment():
    original = source.read(source.OUT / "evaluation/results.json")["macro"]
    published = rows("performance_comparison.csv")
    assert len(published) == 18
    for row in published:
        cell = original[row["system"]][row["k"]]
        reference = original["M_" + row["scope"] + "_SINGLE"][row["k"]]
        for field in ("precision", "recall", "f1"):
            assert float(row[field]) == cell[field]
            assert float(row[field + "_delta_vs_A_pp"]) == 100 * (cell[field] - reference[field])


def test_query_means_preserve_missing_labels_and_macro_order():
    details = rows("question_details.csv")
    assert len(details) == 180
    for row in details:
        if row["positive_cases"] == "0":
            assert row["recall"] == row["f1"] == ""
            assert float(row["precision"]) == 0
    for summary in rows("performance_comparison.csv"):
        subset = [row for row in details if row["system"] == summary["system"] and row["k"] == summary["k"]]
        assert len(subset) == 10
        for field in ("precision", "recall", "f1"):
            available = [float(row[field]) for row in subset if row[field] != ""]
            assert len(available) == (10 if field == "precision" else 6)
            assert statistics.mean(available) == float(summary[field])


def test_all_unknown33_case_statistics_replay_from_query_ranks():
    cases = rows("unknown33_cases.csv")
    pairs = rows("unknown33_query_ranks.csv")
    assert len(cases) == 33 and len(pairs) == 990
    assert sum(row["action_available"] == "True" for row in cases) == 17
    assert all(row["semantic_task_available"] == "True" and row["silver_positive_queries"] == "0" for row in cases)
    for case in cases:
        subset = [row for row in pairs if row["case_id"] == case["case_id"]]
        assert len(subset) == 30
        assert all(float(row["silver_grade"]) < 3 for row in subset)
        for method in ("A", "B", "C"):
            for count in (5, 10, 20):
                assert int(case[f"{method}_top{count}_events"]) == sum(int(row[method + "_rank"]) <= count for row in subset)


def test_representative_ranks_and_scores_are_saved_outputs_not_new_judgments():
    original = source.read(source.OUT / "evaluation/mandatory_cases.json")
    published = rows("representative_cases.csv")
    assert len(published) == 9
    for row in published:
        for method, prefix in (("A", "M"), ("B", "SEM"), ("C", "COMB")):
            actual = next(record for record in original["rankings"] if record["system"] == prefix + "_D_SINGLE"
                          and record["case_id"] == row["case_id"] and record["repeat"] == int(row["repeat"]))
            assert int(row[method + "_rank"]) == actual["rank"]
        whole = next(record["whole"] for record in original["records"] if record["case_id"] == row["case_id"])
        assert float(row["B_whole_cosine"]) == whole["score"]


def test_frozen_experiment_files_are_unchanged_during_publication():
    manifest = source.read(REPORT / "source_manifest.json")
    for name, expected in manifest["source_sha256"].items():
        assert source.digest(source.ROOT / name) == expected
    assert manifest["new_experiment_run"] is False
    assert manifest["new_embeddings"] is False


def test_report_local_links_resolve_inside_repository():
    text = (REPORT / "README.md").read_text(encoding="utf-8")
    for target in re.findall(r"\]\(([^)]+)\)", text):
        if target.startswith(("https://", "http://", "#")):
            continue
        resolved = (REPORT / target.split("#")[0]).resolve()
        assert resolved.is_relative_to(source.ROOT)
        assert resolved.exists(), target
