import csv
import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from datetime import datetime

import numpy as np

from scripts.build_ax_expansion_release import ROOT, digest, read_json, write_json
from scripts.prepare_v25_research import leakage_groups, write_csv


OUTPUT = ROOT / "data/final_dataset_audit_20261026"
RESEARCH = ROOT / "data/v2_5/research"
BASE = "58047e14625825413e97d7cd2d1b1ffcd54d82cb"
RESTORED = {"AXV2N_0112", "AXV2N_0113", "AXV2N_0131"}
PENDING = {"AXV22_0092_01", "AXV22_0093_01"}


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def load_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def audit_judgment_pass(rows, expected_keys):
    keys = [(row["query_id"], row["perspective_id"], row["case_id"]) for row in rows]
    if len(keys) != len(set(keys)) or set(keys) != expected_keys:
        raise ValueError("Judgment pass has missing, duplicate or unexpected pairs")
    judges = {row["reviewer_id"] for row in rows}
    if len(judges) != 1 or not next(iter(judges)).strip():
        raise ValueError("A judgment pass requires one identified reviewer")
    for row in rows:
        if str(row["relevance_0_4"]) not in {"0", "1", "2", "3", "4"} or not row["rationale"].strip():
            raise ValueError("Judgments require an actual grade and evidence rationale")
    return {key: row for key, row in zip(keys, rows, strict=True)}, next(iter(judges))


def final_eligible_count(candidate_count, gates):
    return candidate_count if gates and all(value["passed"] is True for value in gates.values()) else 0


def approval_document(filename, input_fingerprint):
    path = OUTPUT / filename
    if not path.is_file():
        return False, "Missing: " + filename
    value = read_json(path)
    if value.get("input_fingerprint") != input_fingerprint or value.get("approved") is not True:
        return False, "Approval is absent or bound to a different input: " + filename
    if not str(value.get("reviewer_id", "")).strip() or not str(value.get("rationale", "")).strip():
        return False, "Approval lacks reviewer identity or rationale: " + filename
    return True, filename


def freeze_and_test_status():
    freeze_path = OUTPUT / "model_prompt_evaluation_freeze.json"
    test_path = OUTPUT / "heldout_test_queries.json"
    if not freeze_path.is_file():
        return (False, "No final model/prompt/evaluation freeze record"), (False, "Existing 10 questions are Dev; no held-out Test freeze")
    freeze = read_json(freeze_path)
    frozen_at = datetime.fromisoformat(freeze["frozen_at"])
    if frozen_at.tzinfo is None or not freeze.get("sha256"):
        return (False, "Freeze needs timezone-aware time and pinned artifact hashes"), (False, "Freeze is invalid")
    for filename, expected in freeze["sha256"].items():
        if not (ROOT / filename).is_file() or digest(ROOT / filename) != expected:
            return (False, "Frozen artifact mismatch: " + filename), (False, "Freeze is invalid")
    if not test_path.is_file():
        return (True, "Frozen artifact hashes match"), (False, "No held-out Test queries and qrels")
    test = read_json(test_path)
    created_at = datetime.fromisoformat(test["created_at"])
    valid = (created_at.tzinfo is not None and created_at > frozen_at and bool(test.get("queries"))
             and test.get("approved") is True and test.get("used_for_tuning") is False
             and test.get("freeze_sha256") == digest(freeze_path))
    test_qrels = OUTPUT / "heldout_test_qrels.csv"
    if not valid or not test_qrels.is_file() or digest(test_qrels) != test.get("qrels_sha256"):
        return (True, "Frozen artifact hashes match"), (False, "Test timing, approval or qrels hash failed")
    return (True, "Frozen artifact hashes match"), (True, "Test timestamp follows freeze and qrels hash matches")


def source_candidates():
    original = read_json(ROOT / "data/v2_5/main_cases_v2_5.json")
    by_id = {case["case_id"]: {**case, **original["inherited_case_metadata"].get(case["case_id"], {})} for case in original["cases"]}
    curated = read_json(RESEARCH / "dev_cases.json")["cases"]
    reviews = {row["case_id"]: row for row in read_json(OUTPUT / "individual_source_reviews.json")["reviews"]}
    candidates = [{**by_id[row["case_id"]], **row} for row in curated]
    for identifier in sorted(PENDING):
        if not all(reviews[identifier]["field_support"].values()):
            raise ValueError("Pending source fields are not supported")
        candidates.append(by_id[identifier])
    prior = read_json(ROOT / "data/v2_2/main_cases_v2_2.json")["cases"]
    for case in prior:
        if case["case_id"] in RESTORED:
            review = reviews[case["case_id"]]
            candidates.append({**case, "business_scope": review["business_scope"], "business_scope_tags": [review["business_scope"]],
                               "record_kind": "RESTORED_SOURCE_REVIEWED_WORKFLOW", "ai_status": "SOURCE_REVIEWED_AI_WORKFLOW",
                               "factor_labels": [case["factor_label"]] if case.get("factor_label") else [],
                               "strategy_labels": [case["strategy_label"]] if case.get("strategy_label") else []})
    candidates.sort(key=lambda case: case["case_id"])
    if len(candidates) != len({case["case_id"] for case in candidates}):
        raise ValueError("Source candidate identity is duplicated")
    return original, candidates, reviews


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for path in [ROOT / "data/v2_5/release_manifest.json", RESEARCH / "manifest.json"]:
        manifest = read_json(path)
        for filename, expected in manifest["sha256"].items():
            if digest(path.parent / filename) != expected:
                raise ValueError("Stored release artifact changed: " + filename)
    protected = ["data/v2_3", "data/v2_4", "data/v2_5", "experiments", "src", "configs"]
    subprocess.run(["git", "diff", "--exit-code", BASE, "--", *protected], cwd=ROOT, check=True, capture_output=True)
    original, candidates, source_reviews = source_candidates()
    groups, links = leakage_groups(candidates, {})
    existing_evidence = {row["case_id"]: row for line in (RESEARCH / "evidence_catalog.jsonl").read_text(encoding="utf-8").splitlines() if (row := json.loads(line))}
    prior_source_qa = {row["case_id"]: row for row in load_csv(ROOT / "data/v2_2/source_evidence_index_v2_2.csv")}
    source_audits = {row["candidate_id"]: row for row in read_json(ROOT / "data/v2_4/source_review_audit.json")}
    local_source_checks = []
    for case in candidates:
        if case["case_id"].startswith("AXV24_"):
            candidate_id = case["candidate_id"]
            path = ROOT / ".local/ax-expansion-source-review" / (candidate_id + ".json")
            if path.is_file():
                document = read_json(path)
                for field, offsets in case["evidence_paragraph_indices"].items():
                    for offset in offsets:
                        actual = hashlib.sha256(document["paragraphs"][offset].encode()).hexdigest()
                        assert source_audits[candidate_id]["paragraph_hashes"][str(offset)] == actual
                local_source_checks.append({"case_id": case["case_id"], "paragraph_hashes_match": True, "check_type": "INTEGRITY_NOT_SEMANTIC_FACT_REVIEW"})
    evidence_matrix = []
    normalized = []
    for case in candidates:
        identifier = case["case_id"]
        review = source_reviews.get(identifier)
        evidence = existing_evidence.get(identifier)
        if review:
            provenance = "data/final_dataset_audit_20261026/individual_source_reviews.json#case_id=" + identifier
            method = "CURRENT_AI_PRIMARY_DOCUMENT_REVIEW"
        elif identifier.startswith("AXALL_"):
            provenance = "data/v2_5/research/source_reviews.json#case_id=" + identifier
            method = "PRIOR_INDIVIDUAL_SOURCE_ROW_REVIEW"
        elif identifier.startswith("AXV24_"):
            provenance = "data/v2_4/reviewed_workflows.json#candidate_id=" + case["candidate_id"]
            method = "PRIOR_AI_PRIMARY_PASSAGE_REVIEW_WITH_PARAGRAPH_HASHES"
        else:
            if identifier not in prior_source_qa:
                raise ValueError("Prior reviewed case is missing source evidence index")
            provenance = "data/v2_2/source_evidence_index_v2_2.csv#case_id=" + identifier
            method = "PRIOR_AI_SOURCE_QA_PRESERVED_NOT_A_NEW_INDEPENDENT_REVIEW"
        evidence_matrix.append({"case_id": identifier, "source_url": case["source_url"], "source_document_evidence": provenance,
                                "document_review_method": method, "problem_present": bool(case.get("problem")),
                                "implementation_present": bool(case.get("implementation")),
                                "deployment_evidence": "SOURCE_REPORTED_ONLY", "observed_outcome_independently_measured": False,
                                "new_factor_independent_approval_this_run": False, "new_strategy_independent_approval_this_run": False,
                                "prior_factor_review_record_present": bool(case.get("factor_review")),
                                "prior_strategy_review_record_present": bool(case.get("strategy_review")),
                                "human_gold": False, "source_corroboration_independent_of_publisher": False,
                                "existing_evidence_id": evidence["evidence_id"] if evidence else "RESTORED_" + identifier})
        normalized.append({"case_id": identifier, **{field: case[field] for field in ("organization", "problem", "task", "context", "implementation", "outcome", "source_url")},
                           "business_scope": case["business_scope"], "deployment_stage": case.get("deployment_stage", "UNKNOWN"),
                           "factor_labels_provisional": case.get("factor_labels", []), "strategy_labels_provisional": case.get("strategy_labels", []),
                           "evidence_locator": provenance, "leakage_group_id": groups[identifier], "partition": "DEV_EXPOSED_NOT_HELDOUT",
                           "final_experiment_approved": False, "human_gold": False})
    write_json(OUTPUT / "source_supported_candidates.json", {"status": "NOT_FINAL_SOURCE_DOCUMENT_SUPPORTED_CANDIDATES", "cases": normalized})
    write_csv(OUTPUT / "case_evidence_matrix.csv", evidence_matrix, list(evidence_matrix[0]))
    write_json(OUTPUT / "source_cache_integrity.json", {"checks": local_source_checks, "new_semantic_fact_verifications_claimed": 0})
    partition_rows = [{"case_id": case["case_id"], "leakage_group_id": groups[case["case_id"]], "partition": "DEV_EXPOSED_NOT_HELDOUT"} for case in candidates]
    write_csv(OUTPUT / "candidate_groups.csv", partition_rows, list(partition_rows[0]))
    write_csv(OUTPUT / "known_group_links.csv", links, ["case_id", "linked_case_id", "basis"])
    queries = read_json(ROOT / "data/v2_3/dev_query_candidates_v2_3.json")["queries"]
    blind_input = {"status": "DEV_ONLY_NOT_FINAL_TEST", "queries": [{"query_id": query["query_id"], "query": query["business_problem_query"],
                    "reference_perspectives": query["draft_perspectives"]} for query in queries],
                   "cases": [{"case_id": case["case_id"], **{field: case[field] for field in ("problem", "task", "context")}} for case in candidates]}
    write_json(OUTPUT / "blind_relevance_input.json", blind_input)
    input_hash = fingerprint(blind_input)
    pairs = [{"query_id": query["query_id"], "perspective_id": perspective["id"], "case_id": case["case_id"],
              "relevance_0_4": "", "reviewer_id": "", "rationale": "", "input_sha256": input_hash, "status": "UNJUDGED"}
             for query in queries for perspective in query["draft_perspectives"] for case in candidates]
    write_csv(OUTPUT / "relevance_annotation_template.csv", pairs, list(pairs[0]))
    write_csv(OUTPUT / "factor_blind_input.csv", [{"case_id": case["case_id"], "problem": case["problem"]} for case in candidates], ["case_id", "problem"])
    write_csv(OUTPUT / "strategy_blind_input.csv", [{"case_id": case["case_id"], "implementation": case["implementation"], "outcome": case["outcome"]} for case in candidates], ["case_id", "implementation", "outcome"])
    expected_keys = {(row["query_id"], row["perspective_id"], row["case_id"]) for row in pairs}
    completed_passes = []
    disagreement_count = None
    for number in (1, 2):
        path = OUTPUT / f"relevance_pass_{number}.csv"
        if path.exists():
            rows = load_csv(path)
            if any(row["input_sha256"] != input_hash for row in rows):
                raise ValueError("Relevance judgments do not match the blinded input")
            completed_passes.append(audit_judgment_pass(rows, expected_keys))
    independent_complete = len(completed_passes) == 2 and completed_passes[0][1] != completed_passes[1][1]
    if independent_complete:
        first, second = completed_passes
        disagreement_count = sum(first[0][key]["relevance_0_4"] != second[0][key]["relevance_0_4"] for key in expected_keys)
    prior_silver = load_csv(ROOT / "data/v2_3/ground_truth/silver_dev_qrels_2520.csv")
    shared_ids = {case["case_id"] for case in candidates} & {row["case_id"] for row in prior_silver}
    pairwise = []
    with np.load(RESEARCH / "dev_bge_m3_128.npz", allow_pickle=False) as archive:
        identifiers = archive["case_ids"].tolist()
        views = archive["views"]
        scores = np.mean(views @ np.transpose(views, (0, 2, 1)), axis=0)
        for first_index, first_id in enumerate(identifiers):
            for second_index in range(first_index + 1, len(identifiers)):
                second_id = identifiers[second_index]
                if scores[first_index, second_index] >= 0.90:
                    pairwise.append({"first_case_id": first_id, "second_case_id": second_id, "mean_three_view_cosine": float(scores[first_index, second_index]),
                                     "same_known_leakage_group": groups[first_id] == groups[second_id],
                                     "semantic_duplicate_status": "UNADJUDICATED_SIMILARITY_FLAG_NOT_DUPLICATE_PROOF"})
    write_csv(OUTPUT / "semantic_duplicate_review_queue.csv", pairwise, ["first_case_id", "second_case_id", "mean_three_view_cosine", "same_known_leakage_group", "semantic_duplicate_status"])
    published_dispositions = load_csv(RESEARCH / "dispositions.csv")
    write_csv(OUTPUT / "registry_review_status.csv", [{"case_id": row["case_id"], "published_triage_decision": row["decision"],
              "evidence_ids": row["evidence_ids"], "published_review_method": row["decision_method"],
              "individual_fact_review_completed_this_run": row["case_id"] in source_reviews,
              "all_final_experiment_gates_passed": False} for row in published_dispositions],
              ["case_id", "published_triage_decision", "evidence_ids", "published_review_method", "individual_fact_review_completed_this_run", "all_final_experiment_gates_passed"])
    cohort_fingerprint = fingerprint(normalized)
    label_status = approval_document("factor_strategy_adjudication.json", cohort_fingerprint)
    duplicate_status = approval_document("semantic_duplicate_adjudication.json", cohort_fingerprint)
    researcher_status = approval_document("researcher_approval.json", cohort_fingerprint)
    freeze_status, test_status = freeze_and_test_status()
    relevance_status = approval_document("relevance_adjudication.json", input_hash)
    gates = {
        "independent_relevance_judgments": {"passed": independent_complete, "detail": f"{len(completed_passes)}/2 complete independent passes; {len(pairs)} pairs each"},
        "relevance_disagreements_adjudicated": {"passed": independent_complete and (disagreement_count == 0 or relevance_status[0]), "detail": relevance_status[1]},
        "factor_strategy_independent_validation": {"passed": label_status[0], "detail": label_status[1]},
        "semantic_duplicate_adjudication": {"passed": duplicate_status[0], "detail": duplicate_status[1]},
        "model_prompt_evaluation_frozen_before_test": {"passed": freeze_status[0], "detail": freeze_status[1]},
        "heldout_test_and_qrels": {"passed": test_status[0], "detail": test_status[1]},
        "researcher_approval": {"passed": researcher_status[0], "detail": researcher_status[1]}
    }
    final_count = final_eligible_count(len(candidates), gates)
    counts = Counter(case.get("record_kind", "PRIOR") for case in original["cases"])
    report = {"status": "FINAL_EXPERIMENT_READY" if final_count else "FINAL_EXPERIMENT_NOT_READY", "completion_claim": bool(final_count), "base_commit": BASE, "original_registry_records": len(original["cases"]),
              "original_search_candidates": 9416, "original_record_kind_counts": dict(counts),
              "published_dev_candidates": 112, "source_document_candidates_after_followup": len(candidates),
              "restored_previously_scope_excluded": sorted(RESTORED), "newly_rechecked_pending_sources": sorted(PENDING),
              "source_document_review_count_this_run": len(source_reviews), "new_independent_cross_publisher_fact_corroborations": 0,
              "prior_source_cache_integrity_checks": len(local_source_checks), "unique_candidate_leakage_groups": len(set(groups.values())),
              "known_cross_partition_links": 0, "heldout_candidate_cases": 0, "actual_heldout_test_questions": 0,
              "required_dev_relevance_pairs": len(pairs), "complete_independent_judgment_passes": len(completed_passes),
              "prior_silver_case_overlap": len(shared_ids), "prior_silver_pairs_for_overlapping_cases": sum(row["case_id"] in shared_ids for row in prior_silver),
              "prior_silver_status": "AI_ONLY_DEV_NOT_HUMAN_GOLD_NOT_TRANSFERRED_TO_NEW_COHORT",
              "semantic_similarity_flags": len(pairwise), "final_experiment_eligible_cases": final_count,
              "candidate_cohort_fingerprint": cohort_fingerprint,
              "gates": gates, "paid_api_calls": 0, "new_case_collection": 0, "protected_paths_unchanged": protected,
              "prohibited_claims": ["117 finalized cases", "all 11766 individually fact verified", "existing Dev renamed final Test", "AI Silver called human Gold"]}
    write_json(OUTPUT / "readiness.json", report)
    files = [path for path in OUTPUT.iterdir() if path.is_file() and path.name != "manifest.json"]
    write_json(OUTPUT / "manifest.json", {"base_commit": BASE, "branch": subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip(),
               "files_sha256": {path.name: digest(path) for path in sorted(files)}, "generator_sha256": digest(ROOT / "scripts/audit_final_dataset.py"),
               "blind_relevance_input_fingerprint": input_hash, "new_paid_api_calls": 0, "completion_claim": False})
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
