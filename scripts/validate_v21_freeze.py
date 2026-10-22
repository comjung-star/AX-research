#!/usr/bin/env python3
"""AX Dataset v2.1 frozen corpus/GT readiness validator (no fabricated labels)."""
from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/v2_1"
OLD = ROOT / "data/v2"
EVIDENCE = ROOT / "experiments/rq3_evidence/results/v21_wald_contingency_2026-10-22.csv"


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def check():
    release_path=DATA/"main_cases_v2_1.json"
    csv_path=DATA/"main_cases_v2_1.csv"
    release=read_json(release_path)
    manifest=read_json(DATA/"release_manifest_v2_1.json")
    original=read_json(OLD/"main_cases_v2.json")["cases"]
    eligible=read_json(OLD/"qa/provisional_source_qualified_91_2026-10-22.json")["cases"]
    qa=read_json(OLD/"qa/independent_source_pass3_2026-10-22.json")["rows"]
    qa_map={x["case_id"]:x for x in qa}
    orig_map={x["case_id"]:x for x in original}
    cases=release["cases"]
    ids=[x["case_id"] for x in cases]
    assert len(cases)==91 and len(set(ids))==91
    assert release["dataset_release"]==manifest["version"]=="2.1.0"
    assert manifest["summary"]["included"]==91
    assert manifest["summary"]["held"]==7
    assert manifest["git_blob_sha"]["dataset_json"]==git_blob_sha(release_path)
    assert manifest["git_blob_sha"]["dataset_csv"]==git_blob_sha(csv_path)
    assert set(ids)=={x["case_id"] for x in eligible}
    assert set(ids)=={x["case_id"] for x in qa if x["review_status"]=="AI_SOURCE_QA_PASS"}
    assert len([x for x in qa if x["review_status"]!="AI_SOURCE_QA_PASS"])==7
    assert all(x["human_ground_truth_approved"] is False for x in cases)
    assert all(x["human_ground_truth_approved"] is False for x in original)
    assert all(x["source_qa"]["human_review_status"]=="NOT_REVIEWED" for x in cases)
    assert all(x["source_qa"]["status"]=="AI_SOURCE_QA_PASS" for x in cases)
    assert all(x["corpus_status"]=="FROZEN_SOURCE_QA_ELIGIBLE" for x in cases)
    assert all(x["deployment_stage"]=="PRODUCTION" for x in cases)
    assert all(x["case_id"] in orig_map for x in cases)
    for x in cases:
        raw=orig_map[x["case_id"]]
        assert x["problem"]==raw["problem"]
        assert x["task"]==raw["task"]
        assert x["context"]==raw["context"]
        assert x["implementation"]==raw["implementation"]
        assert x["factor_label"]==raw["factor_label"]
        assert x["strategy_label"]==raw["strategy_label"]
        assert x["direct_mappings"]==raw["direct_mappings"]
        assert x["source_url"]==raw["source_url"]
        assert x["source_qa"]["independent_source_anchor"]==qa_map[x["case_id"]]["primary_source_passage_anchor"]
    with csv_path.open(encoding="utf-8",newline="") as f:
        tab=list(csv.DictReader(f))
    assert len(tab)==91
    assert [x["case_id"] for x in tab]==ids
    assert all(c["case_id"]==tab[i]["case_id"] for i,c in enumerate(cases))
    grouped={"source_url":{},"organization":{},"parent_v1_case_id":{}}
    for c in cases:
        for key,m in grouped.items():
            if c.get(key):
                m.setdefault(c[key],set()).add(c["sampling_group_id"])
    assert all(len(g)==1 for m in grouped.values() for g in m.values())
    assert len({x["sampling_group_id"] for x in cases})==63
    assert sum(not x["factor_label"] for x in cases)==22
    assert sum(not x["strategy_label"] for x in cases)==2
    assert sum(bool(x["factor_label"] and x["strategy_label"]) for x in cases)==68
    assert sum(len(x["direct_mappings"]) for x in cases)==64

    dev=read_json(DATA/"dev_query_candidates_v2_1.json")["queries"]
    assert len(dev)==10
    assert sum(len(x["draft_perspectives"]) for x in dev)==30
    assert all(x["status"].startswith("DEV_") for x in dev)
    with (DATA/"dev_relevance_annotation_sheet_v2_1.csv").open(encoding="utf-8",newline="") as f:
        label_rows=list(csv.DictReader(f))
    assert len(label_rows)==2730
    assert all(x["status"]=="UNJUDGED" and not x["relevance_0_4"] for x in label_rows)
    assert {x["case_id"] for x in label_rows}==set(ids)
    assert len({(x["query_id"],x["perspective_id"],x["case_id"]) for x in label_rows})==2730

    with EVIDENCE.open(encoding="utf-8",newline="") as f:
        pairs=list(csv.DictReader(f))
    assert len(pairs)==63
    assert sum(x["all_cells_at_least_5"]=="YES" for x in pairs)==2
    for row in pairs:
        assert sum(int(row[k]) for k in
                   ["a_factor_strategy","b_factor_only","c_strategy_only","d_neither"])==68
    print("Frozen v2.1 integrity: PASS")
    print("91 operational cases, 7 held, 63 groups, 22 factor abstentions, 2 strategy abstentions")
    print("68 dual-labelled cases, 64 explicit applicability links")
    print("Dev query pack: 10 queries, 30 draft perspectives, 2730 UNJUDGED pairs")
    print("Wald: 2/63 cell-eligible under min>=5, descriptive only")
    print("Human GT approvals: ZERO. No v2.1 held-out result exists.")


if __name__=="__main__":
    check()
