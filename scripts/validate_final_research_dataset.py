import json
from collections import Counter

import numpy as np

from scripts.audit_final_dataset import OUTPUT, fingerprint, load_csv
from scripts.build_ax_expansion_release import ROOT, digest, read_json, write_json
from scripts.build_final_research_dataset import RELEASE


def validate_matrix(rows, queries, case_ids):
    expected = {(query["query_id"], perspective["id"], identifier) for query in queries
                for perspective in query["reference_perspectives"] for identifier in case_ids}
    keys = [(row["query_id"], row["perspective_id"], row["case_id"]) for row in rows]
    if len(keys) != len(set(keys)) or set(keys) != expected:
        raise ValueError("Qrels matrix is incomplete, duplicated or contains unexpected pairs")
    for row in rows:
        if row["relevance_0_4"] not in {"0", "1", "2", "3", "4"} or not row["evidence_reason"].strip():
            raise ValueError("Unjudged row cannot become a negative label")
        if row["judgment_status"] not in {"AI_SILVER_AGREED", "AI_SILVER_ADJUDICATED"}:
            raise ValueError("Unresolved judgment")


def validate_release():
    manifest = read_json(RELEASE / "manifest.json")
    for filename, expected in manifest["files_sha256"].items():
        if digest(RELEASE / filename) != expected:
            raise ValueError("Release artifact hash mismatch: " + filename)
    for filename, expected in manifest["annotation_evidence_sha256"].items():
        if digest(OUTPUT / filename) != expected:
            raise ValueError("Annotation provenance changed: " + filename)
    cases = read_json(RELEASE / "cases.json")["cases"]
    identifiers = [case["case_id"] for case in cases]
    case_ids = set(identifiers)
    if len(case_ids) != len(cases):
        raise ValueError("Duplicate case identity")
    source_cases = read_json(OUTPUT / "source_supported_candidates.json")["cases"]
    if fingerprint(source_cases) != manifest["source_cohort_fingerprint"]:
        raise ValueError("Frozen source cohort changed")
    by_source = {case["case_id"]: case for case in source_cases}
    if case_ids != set(by_source):
        raise ValueError("Source/release membership mismatch")
    fields = ["problem", "task", "context", "implementation", "outcome", "source_url", "leakage_group_id"]
    if any(case[field] != by_source[case["case_id"]][field] for case in cases for field in fields):
        raise ValueError("Source/release field mismatch")
    features = load_csv(RELEASE / "case_features.csv")
    if [row["case_id"] for row in features] != identifiers:
        raise ValueError("Feature/case identity order mismatch")
    if any(set(row) != {"case_id", "business_problem", "ax_target_task", "business_context", "leakage_group_id"} for row in features):
        raise ValueError("Solution or label leaked into retrieval feature columns")
    labels = load_csv(RELEASE / "case_labels.csv")
    if {row["case_id"] for row in labels} != case_ids or len(labels) != len(case_ids):
        raise ValueError("Case label membership mismatch")
    for kind, taxonomy_name in (("factor", "root_cause"), ("strategy", "strategy")):
        allowed = {row[kind + "_id"] for row in load_csv(RELEASE / f"{taxonomy_name}_taxonomy_v2_3.csv")}
        for row in labels:
            selected = set(filter(None, row[kind + "_labels"].split("|")))
            if not selected <= allowed or row[kind + "_status"] not in {"LABEL", "ABSTAIN"} or bool(selected) != (row[kind + "_status"] == "LABEL"):
                raise ValueError("Unknown, unreviewed or fabricated case label")
    index = read_json(RELEASE / "index_provenance.json")
    if index["candidate_fingerprint"] != manifest["source_cohort_fingerprint"] or index["index_sha256"] != digest(RELEASE / "case_bge_m3_128.npz"):
        raise ValueError("Index provenance mismatch")
    with np.load(RELEASE / "case_bge_m3_128.npz", allow_pickle=False) as archive:
        if archive["case_ids"].tolist() != identifiers or archive["views"].shape != (3, len(cases), 1024):
            raise ValueError("Index/case identity or shape mismatch")
        norms = np.linalg.norm(archive["views"], axis=-1)
        if not np.isfinite(archive["views"]).all() or not np.allclose(norms, 1, atol=0.0001):
            raise ValueError("Embedding normalization or finite-value failure")
    queries = {}
    empty_perspectives = {}
    for split in ("dev", "test"):
        queries[split] = read_json(RELEASE / f"{split}_reference_perspectives.json")["queries"]
        rows = load_csv(RELEASE / f"{split}_qrels.csv")
        validate_matrix(rows, queries[split], case_ids)
        query_csv = load_csv(RELEASE / f"{split}_queries.csv")
        if [(row["query_id"], row["business_problem_query"]) for row in query_csv] != [(query["query_id"], query["query"]) for query in queries[split]]:
            raise ValueError("Query text mismatch")
        positives = Counter((row["query_id"], row["perspective_id"]) for row in rows if int(row["relevance_0_4"]) >= 3)
        empty_perspectives[split] = [{"query_id": query["query_id"], "perspective_id": perspective["id"]} for query in queries[split]
                                      for perspective in query["reference_perspectives"] if not positives[query["query_id"], perspective["id"]]]
    if {query["query_id"] for query in queries["dev"]} & {query["query_id"] for query in queries["test"]}:
        raise ValueError("Query split identity leakage")
    if {"".join(query["query"].split()).casefold() for query in queries["dev"]} & {"".join(query["query"].split()).casefold() for query in queries["test"]}:
        raise ValueError("Exact normalized query text leakage")
    folds = load_csv(RELEASE / "case_group_cv_folds.csv")
    group_folds = {}
    for row in folds:
        if row["leakage_group_id"] != by_source[row["case_id"]]["leakage_group_id"]:
            raise ValueError("Fold group does not match source group")
        existing = group_folds.setdefault(row["leakage_group_id"], row["auxiliary_group_cv_fold"])
        if existing != row["auxiliary_group_cv_fold"]:
            raise ValueError("Organization/source group crosses CV folds")
    if {row["case_id"] for row in folds} != case_ids or len(folds) != len(case_ids):
        raise ValueError("Group fold membership mismatch")
    report = {"status": "PASS", "cases": len(cases), "dev_queries": len(queries["dev"]), "test_queries": len(queries["test"]),
              "complete_qrels": sum(len(load_csv(RELEASE / f"{split}_qrels.csv")) for split in ("dev", "test")),
              "unresolved_judgments": 0, "known_group_fold_leakage": 0, "groups": len(group_folds),
              "zero_positive_reference_perspectives": empty_perspectives, "release_manifest_sha256": digest(RELEASE / "manifest.json"),
              "source_fingerprint": manifest["source_cohort_fingerprint"], "checks_are_schema_hash_split_and_matrix_validation_not_fact_verification": True}
    return report


def main():
    report = validate_release()
    destination = ROOT / "docs/prototype-validation/final-dataset-validation.json"
    write_json(destination, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
