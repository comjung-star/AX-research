import csv
import hashlib
import json
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

from scripts.build_ax_expansion_release import ROOT, digest, identity_url, read_json, write_json
from scripts.build_ax_inclusive_release import meaningful
from scripts.collect_ax_portals import clean, parse_csv


OUTPUT = ROOT / "data/v2_5/research"
BASE = "8b40bfbefa82e0cbf710482823f7d97b58f1690b"
DECISIONS = {"EXPERIMENT_SUITABLE": "실험 적합", "REFERENCE_ONLY": "참고 전용", "HOLD": "보류", "EXCLUDE": "제외"}
FIELDS = ("problem", "task", "context", "implementation", "outcome")
SOLUTION_SIGNAL = re.compile(r"\b(?:AI|chatbot|automates?|automating|AI-powered|leverages?|utilizes?)\b|도입|챗봇|자동화|생성형", re.I)


def write_csv(path, rows, fields):
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows({key: json.dumps(value, ensure_ascii=False, sort_keys=True) if isinstance(value, (list, dict)) else value
                          for key, value in row.items()} for row in rows)


def normalize_organization(value):
    if not meaningful(value):
        return ""
    normalized = re.sub(r"[^a-z0-9가-힣]", "", value.casefold().split(" / ")[0])
    if normalized.startswith("ibm"):
        return "ibm"
    return {"starling": "starlingbank"}.get(normalized, normalized)


def leakage_groups(cases, audits):
    parents = {case["case_id"]: case["case_id"] for case in cases}

    def find(identifier):
        while parents[identifier] != identifier:
            parents[identifier] = parents[parents[identifier]]
            identifier = parents[identifier]
        return identifier

    def union(first, second):
        parents[find(first)] = find(second)

    seen = {}
    links = []
    for case in cases:
        identifier = case["case_id"]
        organization = normalize_organization(case.get("organization"))
        keys = [("organization", organization), ("sampling", meaningful(case.get("sampling_group_id")))]
        structured = case.get("record_kind") == "SOURCE_REPORTED_USE_CASE"
        if structured:
            if meaningful(case.get("source_record_id")):
                keys.append(("source_record", case["source_dataset_id"] + "|" + case["source_record_id"]))
        else:
            audit = audits.get(case.get("candidate_id"), {})
            for url in [case.get("source_url"), audit.get("access", {}).get("final_url")]:
                if meaningful(url) and str(url).startswith(("http://", "https://")):
                    keys.append(("page_url", identity_url(url)))
            if audit.get("text_sha256"):
                keys.append(("page_text", audit["text_sha256"]))
        for key in keys:
            if not key[1]:
                continue
            if key in seen:
                union(identifier, seen[key])
                links.append({"case_id": identifier, "linked_case_id": seen[key], "basis": key[0]})
            else:
                seen[key] = identifier
        for other in [case.get("exact_duplicate_of"), *case.get("covered_by_reviewed_workflows", [])]:
            if other:
                if other not in parents:
                    raise ValueError("Duplicate representative is absent: " + other)
                union(identifier, other)
                links.append({"case_id": identifier, "linked_case_id": other, "basis": "explicit_representative"})
    components = defaultdict(list)
    for identifier in parents:
        components[find(identifier)].append(identifier)
    groups = {identifier: "V25G_" + hashlib.sha256("|".join(sorted(members)).encode()).hexdigest()[:20]
              for members in components.values() for identifier in members}
    return groups, links


def decide(case, review=None):
    reasons = []
    kind = case["record_kind"]
    missing = [field for field in FIELDS if not meaningful(case.get(field))]
    reasons.extend("MISSING_" + field.upper() for field in missing)
    if not review and SOLUTION_SIGNAL.search(meaningful(case.get("problem"))):
        reasons.append("PROBLEM_SOLUTION_MIX_RISK_REQUIRES_PASSAGE_REVIEW")
    if kind == "PRIOR_PARSER_ARTIFACT":
        return "EXCLUDE", ["HISTORICAL_PARSER_ARTIFACT_NOT_A_CASE", *reasons]
    if case.get("exact_duplicate_of"):
        return "EXCLUDE", ["EXACT_DUPLICATE_REPRESENTATIVE_RETAINED", *reasons]
    if case.get("covered_by_reviewed_workflows"):
        return "EXCLUDE", ["PARENT_PAGE_REPRESENTED_BY_REVIEWED_WORKFLOWS", *reasons]
    if review:
        return "EXPERIMENT_SUITABLE", ["INDIVIDUAL_SOURCE_ROW_REVIEW_FOR_DESCRIPTIVE_DEV", "DEPLOYMENT_SOURCE_REPORTED_ONLY", "OUTCOME_NOT_INDEPENDENTLY_VALIDATED"]
    if kind == "REVIEWED_WORKFLOW":
        if case.get("source_review_status") in {"AUTHOR_PRIMARY_PASSAGE_REVIEWED", "AI_PRIMARY_PASSAGE_REVIEWED"}:
            return "EXPERIMENT_SUITABLE", ["PRIOR_PASSAGE_REVIEW_PRESERVED_FOR_EXPLORATORY_DEV", "NOT_HUMAN_GOLD", *reasons]
        return "HOLD", ["PRIOR_SECOND_SOURCE_REVIEW_PENDING", *reasons]
    if kind == "SOURCE_REFERENCE" and case.get("content_check_status") == "PUBLIC_PAGE_FETCH_AND_TEXT_CHECK_COMPLETED":
        return "REFERENCE_ONLY", ["PAGE_METADATA_NOT_INDIVIDUAL_WORKFLOW_EVIDENCE", *reasons]
    if kind in {"SOURCE_REFERENCE", "SOURCE_LINK"}:
        return "HOLD", ["SOURCE_CONTENT_UNAVAILABLE_OR_INSUFFICIENT", *reasons]
    if case.get("ai_status") != "SOURCE_CLASSIFIED_AI":
        reasons.append("AI_STATUS_UNCONFIRMED_NOT_PROVEN_NON_AI")
    if case.get("deployment_stage") not in {"DEPLOYED", "PRODUCTION"}:
        reasons.append("STAGE_" + case.get("deployment_stage", "UNKNOWN"))
    reasons.extend(["SOURCE_ROW_MATCH_IS_NOT_FACT_VERIFICATION", "INDIVIDUAL_PASSAGE_REVIEW_PENDING"])
    return "HOLD", reasons


def field_checks(case, review):
    kind = case["record_kind"]
    inherited = kind == "REVIEWED_WORKFLOW"
    fields = {}
    for field in FIELDS:
        if not meaningful(case.get(field)):
            fields[field] = "UNKNOWN"
        elif review and field != "outcome":
            fields[field] = "INDIVIDUAL_SOURCE_ROW_REVIEW_NOT_CORROBORATED"
        elif inherited:
            fields[field] = "PRIOR_PASSAGE_REVIEW_NOT_HUMAN_GOLD"
        elif kind == "SOURCE_REPORTED_USE_CASE":
            fields[field] = "RULE_EXTRACTED_OR_SOURCE_REPORTED_NOT_SEMANTICALLY_VALIDATED"
        else:
            fields[field] = "PAGE_METADATA_ONLY"
    fields.update(ai=case.get("ai_status", "UNKNOWN"), stage=case.get("deployment_stage", "UNKNOWN"),
                  source_access=case.get("content_check_status", "UNKNOWN"),
                  outcome_verification=review["outcome_status"] if review else "NO_NEW_INDEPENDENT_OUTCOME_VERIFICATION",
                  independent_fact_corroboration=False, human_gold=False,
                  factor_labels="EXISTING_PROVISIONAL_NOT_APPROVED", strategy_labels="EXISTING_PROVISIONAL_NOT_APPROVED")
    return fields


def verify_sources():
    release = ROOT / "data/v2_5"
    manifest = read_json(release / "release_manifest.json")
    verified = {}
    for filename, expected in manifest["sha256"].items():
        path = release / filename
        if digest(path) != expected:
            raise ValueError("Input hash mismatch: " + str(path))
        verified[path.relative_to(ROOT).as_posix()] = expected
    for filename, expected in manifest["source_snapshots_sha256"].items():
        if digest(ROOT / filename) != expected:
            raise ValueError("Source snapshot changed: " + filename)
        verified[filename] = expected
    protected = ["data/v2_3", "data/v2_4", "experiments", "configs", "src"]
    subprocess.run(["git", "diff", "--exit-code", BASE, "--", *protected], cwd=ROOT, check=True, capture_output=True)
    return verified, protected


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    verified, protected = verify_sources()
    corpus = read_json(ROOT / "data/v2_5/main_cases_v2_5.json")
    cases = [{**case, **corpus["inherited_case_metadata"].get(case["case_id"], {})} for case in corpus["cases"]]
    audits = {path.stem: read_json(path) for path in (ROOT / "collections/ax-review-all-2026-10-26/page_audits").glob("*.json")}
    row_audits = {row["candidate_id"]: row for row in read_json(ROOT / "data/v2_5/structured_row_audits.json")}
    reviews_payload = read_json(OUTPUT / "source_reviews.json")
    reviews = {review["case_id"]: review for review in reviews_payload["reviews"]}
    raw_path = ROOT / "collections/ax-expansion-2026-10-25/portals/source_datasets/US_OMB_2025.csv"
    if digest(raw_path) != reviews_payload["source_snapshot_sha256"]:
        raise ValueError("Individually reviewed source snapshot changed")
    _, source_rows, malformed = parse_csv(raw_path.read_bytes())
    if malformed:
        raise ValueError("Source row parse failed")
    source_rows = dict(source_rows)
    for case in cases:
        review = reviews.get(case["case_id"])
        if review:
            raw = source_rows[review["source_row"]]
            if case["source_row"] != review["source_row"] or case["source_record_id"] != review["source_record_id"]:
                raise ValueError("Review identity mismatch")
            if clean(raw["id"]) != meaningful(review["source_record_id"]) or clean(raw["use_case_name"]) != case["task"]:
                raise ValueError("Review source row identity mismatch")
            if raw["development_stage"] != "Deployed" or not raw["classification"]:
                raise ValueError("Review stage or AI source field missing")
    groups, links = leakage_groups(cases, audits)
    dev_groups = {groups[case["case_id"]] for case in cases if case["record_kind"] == "REVIEWED_WORKFLOW" or case["case_id"] in reviews}
    split_rows = []
    evidence = []
    evidence_hashes = {}
    dispositions = []
    suitable = []
    for original in cases:
        identifier = original["case_id"]
        review = reviews.get(identifier)
        case = {**original, **{field: review[field] for field in FIELDS if field != "outcome"}} if review else original
        decision, reasons = decide(case, review)
        group = groups[identifier]
        split = "DEV_ONLY" if group in dev_groups else "FUTURE_TEST_RESERVATION_NOT_HELDOUT" if int(hashlib.sha256(("v25-seed-20261026|" + group).encode()).hexdigest(), 16) % 5 == 0 else "UNASSIGNED_REVIEW_POOL"
        split_rows.append({"case_id": identifier, "leakage_group_id": group, "partition": split, "decision": decision,
                           "not_a_train_test_evaluation_split": True})
        evidence_id = "EV_" + identifier
        audit_path = original.get("source_audit_locator", "data/v2_4/main_cases_v2_4.json#case_id=" + identifier)
        evidence_path = audit_path.split("#")[0]
        evidence_file = ROOT / evidence_path
        if not evidence_file.is_file():
            raise ValueError("Missing evidence: " + evidence_path)
        if evidence_path not in evidence_hashes:
            evidence_hashes[evidence_path] = digest(evidence_file)
        audit = audits.get(original.get("candidate_id"), {})
        row_audit = row_audits.get(original.get("candidate_id"), {})
        review_anchors = {"problem": {"source_field": "problem_solved"}, "task": {"source_field": "use_case_name"},
                          "context": {"source_fields": ["agency_name", "agency_bureau", "topic_area"]},
                          "implementation": {"source_field": "system_outputs"}, "outcome": {"source_field": "benefits", "observed_outcome_verified": False}}
        if identifier == "AXALL_US_OMB_2025_02640":
            review_anchors["problem"]["sentence_indices"] = [0]
        evidence.append({"evidence_id": evidence_id, "case_id": identifier, "source_url": original["source_url"],
                         "source_record_id": original.get("source_record_id", ""), "source_row": original.get("source_row"),
                         "evidence_locator": audit_path, "evidence_sha256": evidence_hashes[evidence_path],
                         "source_snapshot_sha256": row_audit.get("source_snapshot_sha256", ""),
                         "page_text_sha256": audit.get("text_sha256", ""),
                         "access_status": audit.get("access", {}).get("status", "NOT_A_NEW_WEB_CHECK"),
                         "field_anchors": review_anchors if review else original.get("evidence", {}),
                         "reviewed_raw_field_sha256": {field: hashlib.sha256(source_rows[review["source_row"]][field].encode()).hexdigest()
                                                       for field in ["problem_solved", "system_outputs", "development_stage", "classification", "benefits"]} if review else {},
                         "source_fields_for_individual_review": ["problem_solved", "system_outputs", "development_stage", "classification", "benefits"] if review else [],
                         "independent_fact_corroboration": False})
        dispositions.append({"case_id": identifier, "decision": decision, "decision_ko": DECISIONS[decision],
                             "reason_codes": reasons, "evidence_ids": [evidence_id],
                             "individual_review_rationale": review["rationale"] if review else "",
                             "decision_method": "INDIVIDUAL_SAVED_SOURCE_ROW_REVIEW" if review else "PRIOR_PASSAGE_REVIEW_STATUS" if case["record_kind"] == "REVIEWED_WORKFLOW" else "DETERMINISTIC_EVIDENCE_TRIAGE_NOT_FACT_REVIEW",
                             "field_checks": field_checks(case, review), "leakage_group_id": group, "partition": split,
                             "business_scope": case["business_scope"], "original_record_preserved": True,
                             "original_retrieval_eligible": case.get("retrieval_eligible", True)})
        if decision == "EXPERIMENT_SUITABLE":
            suitable.append({"case_id": identifier, **{field: case[field] for field in FIELDS}, "source_url": case["source_url"],
                             "business_scope": case["business_scope"], "ai_status": case["ai_status"],
                             "deployment_stage": case["deployment_stage"], "evidence_ids": [evidence_id],
                             "leakage_group_id": group, "partition": "DEV_ONLY", "human_gold": False,
                             "labels_validated": False, "outcome_validated": False,
                             "suitability": "DESCRIPTIVE_RETRIEVAL_DEV_NOT_CONFIRMATORY_WALD_OR_OUTCOME_EVALUATION"})
    counts = dict(Counter(row["decision"] for row in dispositions))
    assert len(dispositions) == len({row["case_id"] for row in dispositions}) == 11766
    assert sum(case.get("retrieval_eligible", True) for case in cases) == 9416
    assert all(row["partition"] == "DEV_ONLY" for row in suitable)
    membership = {row["case_id"]: row["partition"] for row in split_rows}
    group_partitions = defaultdict(set)
    for row in split_rows:
        group_partitions[row["leakage_group_id"]].add(row["partition"])
    assert all(len(partitions) == 1 for partitions in group_partitions.values())
    assert all(groups[link["case_id"]] == groups[link["linked_case_id"]] for link in links)
    write_csv(OUTPUT / "dispositions.csv", dispositions, list(dispositions[0]))
    write_csv(OUTPUT / "split_groups.csv", split_rows, list(split_rows[0]))
    write_csv(OUTPUT / "leakage_links.csv", links, ["case_id", "linked_case_id", "basis"])
    with (OUTPUT / "evidence_catalog.jsonl").open("w", encoding="utf-8", newline="\n") as handle:
        for row in evidence:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    write_json(OUTPUT / "dev_cases.json", {"status": "EXPLORATORY_SOURCE_SUPPORTED_NOT_GROUND_TRUTH", "cases": suitable})
    write_csv(OUTPUT / "dev_problem_views.csv", [{key: row[key] for key in ("case_id", "problem", "task", "context", "evidence_ids", "leakage_group_id")} for row in suitable],
              ["case_id", "problem", "task", "context", "evidence_ids", "leakage_group_id"])
    queries = read_json(ROOT / "data/v2_3/dev_query_candidates_v2_3.json")["queries"]
    write_json(OUTPUT / "dev_queries.json", {"status": "EXISTING_DEV_TEXTS_NOT_HELDOUT", "queries": [{"query_id": row["query_id"], "query": row["business_problem_query"]} for row in queries]})
    qrels = [{"query_id": query["query_id"], "perspective_id": perspective["id"], "reference_perspective": perspective["title"],
              "case_id": case["case_id"], "relevance_0_4": "", "reviewer_id": "", "judgment_status": "UNJUDGED",
              "evidence_ids": case["evidence_ids"], "rationale": "", "human_approved": False}
             for query in queries for perspective in query["draft_perspectives"] for case in suitable]
    write_csv(OUTPUT / "dev_qrels_annotation.csv", qrels, list(qrels[0]))
    policy = {"version": "v25-research-20261026-1", "relevance_scale": {"0": "unrelated", "1": "weak contextual relation", "2": "partially addresses the perspective", "3": "directly relevant problem and task", "4": "strong direct fit with matching context"},
              "positive_threshold": 3, "independent_judges_required": 2, "adjudicate": "All grade disagreement and all threshold flips; researcher approval before confirmatory evaluation",
              "judgment_input": "Query + reference perspective + problem/task/context only; hide implementation/outcome/factor/strategy and model scores",
              "reference_perspectives": "Draft evaluation references only, never runtime prompts; validate before qrels approval",
              "unjudged_is_not_zero": True, "old_silver_transferred": False, "new_qrels_approved": False,
              "scope_filter_for_selection": False, "outcome_required_for_descriptive_retrieval": False,
              "label_scope": "Source support is separate from relevance, causal correctness, independent deployment verification and human Gold",
              "heldout_test": "Not created. Freeze prompts, model, thresholds and evaluation rules before independent held-out query construction. Reservation groups are not a Test dataset.",
              "near_duplicate_semantic_review": "PENDING; exact/source/organization/explicit links alone do not certify all near duplicates absent",
              "strategy_gold": "Derive only after relevant cases are adjudicated using frozen S1-S7 taxonomy",
              "confirmatory_wald": "BLOCKED: factor/strategy labels are provisional and missingness/sparsity require review"}
    write_json(OUTPUT / "evaluation_policy.json", policy)
    summary = {"base_commit": BASE, "source_records_preserved": len(cases), "source_retrieval_candidates": 9416, "new_collection_count": 0,
               "decision_counts": counts, "decision_counts_ko": {DECISIONS[key]: count for key, count in counts.items()},
               "decision_method_counts": dict(Counter(row["decision_method"] for row in dispositions)),
               "new_individual_saved_row_reviews": len(reviews), "new_independent_fact_corroborations": 0,
               "dev_case_count": len(suitable), "dev_query_count": len(queries), "unjudged_qrel_pairs": len(qrels),
               "new_approved_qrels": 0, "human_gold_labels": 0, "heldout_test_queries": 0,
               "leakage_group_count": len(set(groups.values())), "leakage_link_count": len(links),
               "partition_counts": dict(Counter(membership.values())), "cross_partition_link_count": 0,
               "missing_problem_count": sum(not meaningful(case.get("problem")) for case in cases),
               "potential_problem_solution_mix_count": sum(bool(SOLUTION_SIGNAL.search(meaningful(case.get("problem")))) for case in cases),
               "scope_exclusions": 0, "paid_api_calls": 0, "protected_paths_unchanged_from_base": protected,
               "ready": {"descriptive_dev_inputs": True, "inclusive_dense": (ROOT / "data/v2_5/index_manifest.json").is_file(),
                         "v25_recall_coverage_benchmark": False, "confirmatory_wald": False, "heldout_test": False},
               "blockers": ["Remaining source records lack individual passage review or corroboration; inspect per-record reasons",
                            "Independent relevance judgments and approved reference perspectives are missing",
                            "Held-out queries must follow model/prompt/evaluation freeze",
                            "Semantic near-duplicate adjudication and independent factor/strategy labels remain pending",
                            "Inclusive task embeddings mix source descriptions and 128-token additions with inherited longer encodings; use clean research views for controlled comparisons"]}
    write_json(OUTPUT / "readiness.json", summary)
    generated = ["source_reviews.json", "dispositions.csv", "split_groups.csv", "leakage_links.csv", "evidence_catalog.jsonl", "dev_cases.json", "dev_problem_views.csv", "dev_queries.json", "dev_qrels_annotation.csv", "evaluation_policy.json", "readiness.json"]
    write_json(OUTPUT / "manifest.json", {"base_commit": BASE, "branch": subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip(),
               "input_sha256": verified, "sha256": {filename: digest(OUTPUT / filename) for filename in generated},
               "generator_sha256": digest(Path(__file__)), "reproduce": "python -m scripts.prepare_v25_research",
               "all_source_records_preserved": True, "all_original_experiment_artifacts_unchanged": True,
               "deterministic_outputs": True, "human_gold": False})
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
