import json
import shutil
import platform
import sys
from collections import Counter
from datetime import datetime, timezone
from importlib.metadata import version

from scripts.audit_final_dataset import OUTPUT, bound_annotation_status, fingerprint, load_csv, main as audit_main
from scripts.build_ax_expansion_release import ROOT, digest, read_json, write_json
from scripts.compare_final_labels import compare_labels
from scripts.compare_final_reviews import compare
from scripts.prepare_final_split_manifests import main as split_main
from scripts.prepare_v25_research import write_csv


RELEASE = ROOT / "data/v2_6"


def complete_qrels(split):
    result = compare(split)
    if result.get("unresolved_disagreements") != 0:
        raise ValueError("All relevance disagreements must be adjudicated: " + split)
    prefix = "test_" if split == "test" else ""
    approval = read_json(OUTPUT / f"{prefix}relevance_adjudication.json")
    path = OUTPUT / f"{prefix}qrels_consensus.csv"
    if approval.get("approved") is not True or approval.get("final_qrels_sha256") != digest(path):
        raise ValueError("Qrels adjudication evidence does not match: " + split)
    return load_csv(path)


def strategy_references(split, queries, qrels, labels):
    rows = []
    for query in queries:
        for perspective in query["reference_perspectives"]:
            relevant = {row["case_id"] for row in qrels if row["query_id"] == query["query_id"]
                        and row["perspective_id"] == perspective["id"] and int(row["relevance_0_4"]) >= 3}
            known = [labels[identifier] for identifier in sorted(relevant) if labels[identifier]["decision"] == "LABEL"]
            strategies = sorted({label for row in known for label in row["strategy_labels"].split("|")})
            rows.append({"split": split, "query_id": query["query_id"], "perspective_id": perspective["id"],
                         "relevant_cases": len(relevant), "strategy_labelled_relevant_cases": len(known),
                         "relevant_strategy_abstentions": len(relevant) - len(known), "reference_strategy_set": "|".join(strategies),
                         "answerability": "SUPPORTED_AI_SILVER" if strategies else "NO_POSITIVE_LABELLED_CASE",
                         "human_gold": False})
    return rows


def wald_inputs(cases, factors, strategies):
    rows = [{"case_id": case["case_id"], "leakage_group_id": case["leakage_group_id"],
             "factor_labels": factors[case["case_id"]]["factor_labels"], "strategy_labels": strategies[case["case_id"]]["strategy_labels"]}
            for case in cases if factors[case["case_id"]]["decision"] == "LABEL" and strategies[case["case_id"]]["decision"] == "LABEL"]
    factor_ids = [row["factor_id"] for row in load_csv(ROOT / "data/v2_3/root_cause_taxonomy_v2_3.csv")]
    strategy_ids = [row["strategy_id"] for row in load_csv(ROOT / "data/v2_3/strategy_taxonomy_v2_3.csv")]
    cells = []
    for factor_id in factor_ids:
        for strategy_id in strategy_ids:
            counts = Counter((factor_id in row["factor_labels"].split("|"), strategy_id in row["strategy_labels"].split("|")) for row in rows)
            counts_by_cell = [counts[True, True], counts[True, False], counts[False, True], counts[False, False]]
            cells.append({"factor_id": factor_id, "strategy_id": strategy_id, "both": counts_by_cell[0],
                          "factor_only": counts_by_cell[1], "strategy_only": counts_by_cell[2], "neither": counts_by_cell[3],
                          "total": len(rows), "independent_groups": len({row["leakage_group_id"] for row in rows}),
                          "screen": "MINIMUM_CELL_COUNTS_PASS_CLUSTER_ADJUSTMENT_STILL_REQUIRED" if min(counts_by_cell) >= 5 else "SPARSE_DO_NOT_TRUST_NAIVE_WALD",
                          "causal_evidence": False})
    return rows, cells


def main():
    cases = read_json(OUTPUT / "source_supported_candidates.json")["cases"]
    cohort_hash = fingerprint(cases)
    label_results = [compare_labels(kind) for kind in ("factor", "strategy")]
    if any(result.get("unresolved") != 0 for result in label_results):
        raise ValueError("Independent factor/strategy validation is incomplete")
    approved, detail = bound_annotation_status("factor_strategy_adjudication.json", cohort_hash, "consensus_sha256")
    if not approved:
        raise ValueError(detail)
    qrels = {split: complete_qrels(split) for split in ("dev", "test")}
    queries = {split: read_json(OUTPUT / ("blind_relevance_input.json" if split == "dev" else "blind_test_relevance_input.json"))["queries"] for split in ("dev", "test")}
    test_document = read_json(OUTPUT / "heldout_test_input.json")
    shutil.copyfile(OUTPUT / "test_qrels_consensus.csv", OUTPUT / "heldout_test_qrels.csv")
    write_json(OUTPUT / "heldout_test_queries.json", {**test_document, "approved": True,
               "approval_level": "TWO_AI_SILVER_PASSES_AND_EXPLICIT_ADJUDICATION_NOT_HUMAN_GOLD",
               "qrels_sha256": digest(OUTPUT / "heldout_test_qrels.csv"), "researcher_approval": False})
    split_main()
    audit_main()
    readiness = read_json(OUTPUT / "readiness.json")
    if not readiness["completion_claim"]:
        raise ValueError("Data preparation gates remain open")
    factors = {row["case_id"]: row for row in load_csv(OUTPUT / "factor_consensus.csv")}
    strategies = {row["case_id"]: row for row in load_csv(OUTPUT / "strategy_consensus.csv")}
    evidence = {row["case_id"]: row for row in load_csv(OUTPUT / "case_evidence_matrix.csv")}
    RELEASE.mkdir(parents=True, exist_ok=True)
    final_cases = [{**case, "factor_labels": factors[case["case_id"]]["factor_labels"].split("|") if factors[case["case_id"]]["decision"] == "LABEL" else [],
                    "factor_status": factors[case["case_id"]]["decision"],
                    "strategy_labels": strategies[case["case_id"]]["strategy_labels"].split("|") if strategies[case["case_id"]]["decision"] == "LABEL" else [],
                    "strategy_status": strategies[case["case_id"]]["decision"],
                    "final_experiment_approved": True, "approval_level": "AI_SILVER_SOURCE_SUPPORTED_RETRIEVAL_INPUT",
                    "individual_outcome_independent_measurement": False, "source_support_method": evidence[case["case_id"]]["document_review_method"]}
                   for case in cases]
    write_json(RELEASE / "cases.json", {"dataset": "FAME-AX-v2.6-AI-Silver", "human_gold": False, "cases": final_cases})
    features = [{"case_id": case["case_id"], "business_problem": case["problem"], "ax_target_task": case["task"],
                 "business_context": case["context"], "leakage_group_id": case["leakage_group_id"]} for case in cases]
    write_csv(RELEASE / "case_features.csv", features, list(features[0]))
    label_rows = [{"case_id": case["case_id"], "factor_labels": factors[case["case_id"]]["factor_labels"], "factor_status": factors[case["case_id"]]["decision"],
                   "strategy_labels": strategies[case["case_id"]]["strategy_labels"], "strategy_status": strategies[case["case_id"]]["decision"], "human_gold": False} for case in cases]
    write_csv(RELEASE / "case_labels.csv", label_rows, list(label_rows[0]))
    reference_rows = []
    for split in ("dev", "test"):
        query_rows = [{"query_id": query["query_id"], "business_problem_query": query["query"]} for query in queries[split]]
        write_csv(RELEASE / f"{split}_queries.csv", query_rows, list(query_rows[0]))
        write_json(RELEASE / f"{split}_reference_perspectives.json", {"split": split, "queries": queries[split], "runtime_input": False, "human_gold": False})
        write_csv(RELEASE / f"{split}_qrels.csv", qrels[split], list(qrels[split][0]))
        reference_rows.extend(strategy_references(split, queries[split], qrels[split], strategies))
    write_csv(RELEASE / "reference_strategy_sets.csv", reference_rows, list(reference_rows[0]))
    wald_rows, sparsity_rows = wald_inputs(cases, factors, strategies)
    write_csv(RELEASE / "wald_input.csv", wald_rows, ["case_id", "leakage_group_id", "factor_labels", "strategy_labels"])
    write_csv(RELEASE / "wald_sparsity.csv", sparsity_rows, list(sparsity_rows[0]))
    copies = {"candidate_bge_m3_128.npz": "case_bge_m3_128.npz", "candidate_index_manifest.json": "index_provenance.json",
              "case_evidence_matrix.csv": "case_evidence_matrix.csv", "query_split_manifest.csv": "query_split_manifest.csv",
              "case_group_cv_folds.csv": "case_group_cv_folds.csv", "frozen_retrieval_protocol.json": "frozen_retrieval_protocol.json",
              "model_prompt_evaluation_freeze.json": "model_prompt_evaluation_freeze.json"}
    for source_name, destination_name in copies.items():
        shutil.copyfile(OUTPUT / source_name, RELEASE / destination_name)
    for name in ("strategy_taxonomy_v2_3.csv", "root_cause_taxonomy_v2_3.csv"):
        shutil.copyfile(ROOT / "data/v2_3" / name, RELEASE / name)
    packages = ["numpy", "torch", "sentence-transformers", "transformers", "kiwipiepy", "rank-bm25", "pytest", "PyYAML", "openai", "pydantic", "requests", "beautifulsoup4"]
    versions = {name: version(name) for name in packages}
    write_json(RELEASE / "environment.json", {"python": sys.version, "platform": platform.platform(), "packages": versions,
               "model_location": ".local/models/bge-m3", "model_weights_sha256": read_json(OUTPUT / "candidate_index_manifest.json")["model_weights_sha256"],
               "generative_local_model_available": False, "dev_run_requires_paid_api": False})
    (RELEASE / "requirements-lock.txt").write_text("\n".join(name + "==" + value for name, value in versions.items()) + "\n", encoding="utf-8")
    registry_rows = load_csv(OUTPUT / "registry_review_status.csv")
    prior_dispositions = {row["case_id"]: row for row in load_csv(ROOT / "data/v2_5/research/dispositions.csv")}
    registry_ids = {row["case_id"] for row in registry_rows}
    cohort_ids = {case["case_id"] for case in cases}
    decisions = [{**row, "original_reason_codes": prior_dispositions[row["case_id"]]["reason_codes"],
                  "original_individual_review_rationale": prior_dispositions[row["case_id"]]["individual_review_rationale"],
                  "original_field_checks": prior_dispositions[row["case_id"]]["field_checks"],
                  "original_record_preserved": True, "final_cohort_member": row["case_id"] in cohort_ids,
                  "current_retrieval_disposition": "EXPERIMENT_SUITABLE_AI_SILVER" if row["case_id"] in cohort_ids else row["published_triage_decision"],
                  "current_reason": "Source-supported curated workflow; independent relevance and label review complete, abstentions retained" if row["case_id"] in cohort_ids else "Prior evidence-linked triage retained; not promoted by schema/access checks",
                  "schema_and_access_checks_are_not_individual_fact_review": True} for row in registry_rows]
    write_csv(RELEASE / "registry_dispositions.csv", decisions, list(decisions[0]))
    report = {"status": "READY_FOR_AI_SILVER_RETRIEVAL_EXPERIMENTS", "cases": len(cases),
              "source_cohort_fingerprint": cohort_hash, "leakage_groups": len({case["leakage_group_id"] for case in cases}),
              "dev_queries": len(queries["dev"]), "synthetic_heldout_test_queries": len(queries["test"]),
              "dev_qrels": len(qrels["dev"]), "test_qrels": len(qrels["test"]), "raw_independent_relevance_judgments": 2 * sum(len(rows) for rows in qrels.values()),
              "unresolved_relevance_disagreements": 0, "factor_labelled_cases": sum(row["decision"] == "LABEL" for row in factors.values()),
              "factor_abstentions": sum(row["decision"] == "ABSTAIN" for row in factors.values()),
              "strategy_labelled_cases": sum(row["decision"] == "LABEL" for row in strategies.values()),
              "strategy_abstentions": sum(row["decision"] == "ABSTAIN" for row in strategies.values()),
              "wald_complete_label_cases": len(wald_rows), "wald_sparse_factor_strategy_pairs": sum(row["screen"].startswith("SPARSE") for row in sparsity_rows),
              "test_retrieval_has_been_executed": False, "human_gold_cases": 0, "new_collection": 0, "paid_api_calls": 0,
              "all_11766_individually_fact_verified": False, "full_fame_ax_model_trained": False,
              "registry_records_preserved": len(registry_rows), "final_cases_already_in_registry": len(cohort_ids & registry_ids),
              "restored_legacy_cases_outside_registry_membership": sorted(cohort_ids - registry_ids),
              "registry_disposition_counts": dict(Counter(row["current_retrieval_disposition"] for row in decisions)),
              "limitations": ["Deployment and outcomes retain publisher/agency source-report provenance, not independent effect verification",
                              "AI-Silver relevance and labels; no human Gold or researcher signoff is fabricated",
                              "Synthetic case-domain-informed query Test with shared case corpus, not unseen-organization generalization",
                              "Ten original Dev queries remain exposed Dev; Test is never used to tune methods",
                              "Raw registry outside curated cohort remains reference/hold/excluded, not individually certified by this release",
                              "Wald input is association-only; sparse cells and within-group dependence need appropriate analysis"]}
    write_json(RELEASE / "release_report.json", report)
    files = [path for path in RELEASE.iterdir() if path.is_file() and path.name != "manifest.json"]
    write_json(RELEASE / "manifest.json", {"dataset": "FAME-AX-v2.6-AI-Silver", "created_at": datetime.now(timezone.utc).isoformat(),
               "source_cohort_fingerprint": cohort_hash, "files_sha256": {path.name: digest(path) for path in sorted(files)},
               "annotation_evidence_sha256": {name: digest(OUTPUT / name) for name in ["relevance_adjudication.json", "test_relevance_adjudication.json", "factor_strategy_adjudication.json", "semantic_duplicate_adjudication.json"]},
               "generator_sha256": digest(ROOT / "scripts/build_final_research_dataset.py"), "human_gold": False})
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
