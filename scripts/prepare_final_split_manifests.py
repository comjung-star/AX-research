import hashlib
import json
import re
from collections import Counter, defaultdict

from scripts.audit_final_dataset import OUTPUT, fingerprint
from scripts.build_ax_expansion_release import digest, read_json, write_json
from scripts.prepare_v25_research import write_csv


def normalized_query(text):
    return re.sub(r"\s+", "", text).casefold()


def main():
    dev = read_json(OUTPUT / "blind_relevance_input.json")
    test = read_json(OUTPUT / "blind_test_relevance_input.json")
    authored = read_json(OUTPUT / "heldout_test_input.json")
    cases = read_json(OUTPUT / "source_supported_candidates.json")["cases"]
    assert {query["query_id"] for query in dev["queries"]}.isdisjoint(query["query_id"] for query in test["queries"])
    assert {normalized_query(query["query"]) for query in dev["queries"]}.isdisjoint(normalized_query(query["query"]) for query in test["queries"])
    assert dev["cases"] == test["cases"]
    split_rows = [{"query_id": query["query_id"], "partition": partition, "text_sha256": hashlib.sha256(query["query"].encode()).hexdigest(),
                   "reference_count": len(query["reference_perspectives"]), "synthetic_query": partition == "TEST_SYNTHETIC_HELDOUT_QUERY",
                   "candidate_corpus_shared_across_queries": True}
                  for partition, document in [("DEV_ONLY", dev), ("TEST_SYNTHETIC_HELDOUT_QUERY", test)] for query in document["queries"]]
    write_csv(OUTPUT / "query_split_manifest.csv", split_rows, list(split_rows[0]))
    grouped = defaultdict(list)
    for case in cases:
        grouped[case["leakage_group_id"]].append(case["case_id"])
    group_order = sorted(grouped, key=lambda group: (-len(grouped[group]), hashlib.sha256(("source-group-folds-seed42|" + group).encode()).hexdigest()))
    fold_sizes = [0] * 5
    assignments = {}
    for group in group_order:
        fold = min(range(5), key=lambda candidate: (fold_sizes[candidate], candidate))
        assignments[group] = fold
        fold_sizes[fold] += len(grouped[group])
    rows = [{"case_id": case["case_id"], "leakage_group_id": case["leakage_group_id"], "auxiliary_group_cv_fold": assignments[case["leakage_group_id"]],
             "not_an_untouched_case_test_split": True} for case in cases]
    write_csv(OUTPUT / "case_group_cv_folds.csv", rows, list(rows[0]))
    for group, members in grouped.items():
        assert len({row["auxiliary_group_cv_fold"] for row in rows if row["case_id"] in members}) == 1
    report = {"dev_queries": len(dev["queries"]), "synthetic_test_queries": len(test["queries"]),
              "dev_references": sum(len(query["reference_perspectives"]) for query in dev["queries"]),
              "test_references": sum(len(query["reference_perspectives"]) for query in test["queries"]),
              "dev_test_query_id_overlap": 0, "normalized_exact_query_text_overlap": 0,
              "candidate_case_count": len(cases), "shared_ir_candidate_corpus": True,
              "unseen_organization_generalization_claim": False, "case_groups": len(grouped),
              "auxiliary_case_group_fold_sizes": fold_sizes, "known_group_cross_fold_leakage": 0,
              "test_created_at": authored["created_at"], "freeze_sha256": authored["freeze_sha256"],
              "dev_input_fingerprint": fingerprint(dev), "test_input_fingerprint": fingerprint(test),
              "test_construction_limitation": "Synthetic case-domain-informed questions authored by parent AI, not external human field queries",
              "query_manifest_sha256": digest(OUTPUT / "query_split_manifest.csv"), "group_fold_sha256": digest(OUTPUT / "case_group_cv_folds.csv")}
    write_json(OUTPUT / "split_validation.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
