#!/usr/bin/env python3
"""Check source-adjudicated AX Dataset v2 candidates, not human scholarly approval."""
import csv
import json
from collections import Counter
from pathlib import Path

root = Path(__file__).resolve().parents[1] / "data" / "v2"
qa = root / "qa"


def check():
    full = json.loads((root / "main_cases_v2.json").read_text(encoding="utf-8"))["cases"]
    p3 = json.loads((qa / "independent_source_pass3_2026-10-22.json").read_text(encoding="utf-8"))
    subset = json.loads((qa / "provisional_source_qualified_91_2026-10-22.json").read_text(encoding="utf-8"))
    p2 = json.loads((qa / "independent_source_pass2_2026-10-22.json").read_text(encoding="utf-8"))
    fullmap = {x["case_id"]: x for x in full}
    ids = [x["case_id"] for x in full]
    assert len(ids) == 98 and len(set(ids)) == 98
    rows = p3["rows"]
    assert [x["case_id"] for x in rows] == ids
    assert p3["human_ground_truth_approved"] == 0
    counts = Counter(x["review_status"] for x in rows)
    assert dict(counts) == p3["counts"]
    assert counts == {"AI_SOURCE_QA_PASS": 91, "REVIEW_CORRECTION": 4, "REVIEW_PRIMARY_PASSAGE": 3}
    orig2 = {x["case_id"]: x for x in p2["rows"]}
    for row in rows:
        c = fullmap[row["case_id"]]
        assert row["organization"] == c["organization"]
        assert row["source_url"] == c["source_url"]
        assert row["human_approved"] is False
        if row["review_status"] == "AI_SOURCE_QA_PASS":
            assert row["verified_against_source"] is True
            assert row["primary_source_passage_anchor"]
            assert row["corpus_usage"] == "SOURCE_CURATED_CANDIDATE_ONLY_NOT_HUMAN_GT"
        else:
            assert row["corpus_usage"] == "EXCLUDE_FROM_FINAL_MAIN_UNTIL_REVIEW"
            assert row["issue"]
    candidates = subset["cases"]
    approved = [x for x in rows if x["review_status"] == "AI_SOURCE_QA_PASS"]
    assert len(candidates) == subset["count"] == 91
    assert [c["case_id"] for c in candidates] == [x["case_id"] for x in approved]
    for case in candidates:
        source = fullmap[case["case_id"]]
        assert case["quality_status"] == "AI_SOURCE_QA_PASS_PENDING_HUMAN"
        assert case["root_label_abstained"] == (source["factor_label"] is None)
        assert case["strategy_label_abstained"] == (source["strategy_label"] is None)
        assert case["direct_mappings"] == source["direct_mappings"]
        assert not case["human_ground_truth_approved"]
        assert case["sampling_group_id"] == source["sampling_group_id"]
    assert subset["human_approved_count"] == 0
    assert len(subset["exclusions_pending"]) == 7
    for item in subset["exclusions_pending"]:
        assert item["case_id"] not in {c["case_id"] for c in candidates}
    with (qa / "final_case_adjudication_table_2026-10-22.csv").open(encoding="utf-8", newline="") as fh:
        ledger = list(csv.DictReader(fh))
    assert len(ledger) == 98
    for case, row, record in zip(full, rows, ledger):
        assert record["case_id"] == case["case_id"]
        assert record["qa_source_status"] == row["review_status"]
        assert record["human_approved"] == "NO"
        assert record["sampling_group_id"] == case["sampling_group_id"]
    src_groups, org_groups, parent_groups = {}, {}, {}
    for c in full:
        src_groups.setdefault(c["source_url"], set()).add(c["sampling_group_id"])
        org_groups.setdefault(c["organization"], set()).add(c["sampling_group_id"])
        if c["parent_v1_case_id"]:
            parent_groups.setdefault(c["parent_v1_case_id"], set()).add(c["sampling_group_id"])
    assert all(len(g) == 1 for g in src_groups.values())
    assert all(len(g) == 1 for g in org_groups.values())
    assert all(len(g) == 1 for g in parent_groups.values())
    print("Source Q01-Q09 sidecar integrity PASS: 91 provisional, 7 held, 0 human GT")
    print("Warning: this check is data integrity, not independent source semantic proof.")


if __name__ == "__main__":
    check()
