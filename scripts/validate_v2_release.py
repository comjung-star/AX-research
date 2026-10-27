"""Validate the final data snapshot; structural checks never certify source truth."""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from urllib.parse import urlparse

from build_v2_final_release import ANCHORS, ROOT, artifacts, build, demand, organization_key, read_csv, read_json

OUTCOME_TYPES = {
    "DEPLOYED_SYSTEM_TEST_RESULT", "DEPLOYMENT_CONFIRMED_EVALUATION_KPI_WITHHELD", "DEPLOYMENT_CONFIRMED_OUTCOME_UNKNOWN",
    "DEPLOYMENT_CONFIRMED_SHARED_KPI_WITHHELD", "IMPLEMENTED_NO_QUANTIFIED_OUTCOME", "MANUFACTURER_REPORTED_OPERATIONAL",
    "OBSERVED_WITH_SEPARATE_PROJECTION", "OPERATION_CONFIRMED_OUTCOME_UNKNOWN", "OPERATION_CONFIRMED_OUTCOME_WITHHELD",
    "OPERATION_CONFIRMED_SHARED_KPI_WITHHELD", "PRODUCTION_EXPERIMENT_REPORTED", "PRODUCTION_QUALITATIVE_PILOT_KPI_WITHHELD",
    "PROJECTED_AND_QUALITATIVE", "QUALITATIVE_WITH_SHARED_METRICS_WITHHELD", "REPORTED_DEPLOYMENT_FOOTPRINT", "REPORTED_SERVICE_USAGE",
    "SHARED_CAMPAIGN_OUTCOME_NOT_COMPONENT_EFFECT", "USER_REPORTED_ANECDOTE", "USER_REPORTED_OPERATIONAL", "USER_REPORTED_QUALITATIVE",
    "VENDOR_REPORTED_BUSINESS_OUTCOME", "VENDOR_REPORTED_COST_COMPARISON", "VENDOR_REPORTED_DEPLOYMENT",
    "VENDOR_REPORTED_ESTIMATE_IN_PRODUCTION", "VENDOR_REPORTED_INTEGRATED_WORKFLOW", "VENDOR_REPORTED_MODEL_PERFORMANCE",
    "VENDOR_REPORTED_OPERATIONAL", "VENDOR_REPORTED_OPERATIONAL_WITH_BASELINE_CAVEAT",
    "VENDOR_REPORTED_OPERATIONAL_WITH_COUNTERFACTUAL_BASELINE", "VENDOR_REPORTED_OPERATIONAL_WITH_DENOMINATOR_CAVEAT",
    "VENDOR_REPORTED_OPERATIONAL_WITH_METRIC_CAVEAT", "VENDOR_REPORTED_OPERATIONAL_WITH_SCOPE_CAVEAT",
    "VENDOR_REPORTED_OPERATIONAL_WITH_SUBSET_CAVEAT", "VENDOR_REPORTED_QUALITATIVE", "VENDOR_REPORTED_QUALITATIVE_FOLLOWUP",
    "VENDOR_REPORTED_TASK_SPECIFIC_KPI", "VENDOR_REPORTED_TASK_USAGE", "VENDOR_REPORTED_TECHNICAL_PRODUCTION",
    "VENDOR_REPORTED_THROUGHPUT_WITH_PROJECTED_IMPACT", "VENDOR_REPORTED_USAGE", "VENDOR_REPORTED_USAGE_AND_USER_FEEDBACK",
    "VENDOR_REPORTED_USAGE_WITH_SHARED_METRICS_WITHHELD",
}


def validate(root=ROOT, freeze=False):
    expected, manifest = build(root)
    for name, content in artifacts(root).items():
        path = root / "data/v2" / name
        demand(path.exists() and path.read_text(encoding="utf-8") == content, "Stale or altered final release: " + name)
    rows = expected["cases"]
    candidate_ids = {row["case_id"] for row in read_json(root, "active_candidate_corpus_v2.json")["cases"]}
    dispositions = expected["dispositions"]
    demand(len(dispositions) == len(candidate_ids) and {row["case_id"] for row in dispositions} == candidate_ids, "Missing final disposition")
    identifiers = [row["case_id"] for row in rows]
    demand(len(identifiers) == len(set(identifiers)), "Duplicate final workflow")
    demand({row["case_id"] for row in dispositions if row["decision"] == "INCLUDE"} == set(identifiers), "Excluded case promoted")
    demand(len({(row["organization"].casefold(), row["task"].casefold()) for row in rows}) == len(rows), "Duplicate organization/workflow")
    parents = {row["case_id"] for row in read_csv(root, "main_cases_v1.csv")}
    factors = {row["factor_id"] for row in read_csv(root, "root_cause_factors_v1.csv")}
    strategies = {row["strategy_id"] for row in read_csv(root, "v2/strategy_taxonomy_v2_frozen.csv")}
    seen_groups = {}
    for row in rows:
        demand(re.fullmatch(r"AXV2(?:C|H|N|P2)_\d{4}(?:_\d{2})?", row["case_id"]), "Invalid final identifier")
        demand(row["deployment_stage"] == "PRODUCTION", "Nonproduction case promoted")
        demand(row["parent_v1_case_id"] is None or row["parent_v1_case_id"] in parents, "Unknown final parent lineage")
        for field in ("organization", "industry", "problem", "task", "context", "implementation", "outcome", "uncertainty"):
            demand(isinstance(row[field], str) and row[field].strip() and not row[field].startswith("SEE_"), "Missing final content: " + field)
        demand(not re.search(r"\b(?:GPT|Gemini|Copilot|RAG|Claude|watsonx)\b", row["problem"], re.IGNORECASE), "Solution leaked into final problem")
        demand(all(row["evidence"].get(key) for key in ANCHORS), "Missing final evidence anchor")
        demand(row["outcome_type"] in OUTCOME_TYPES, "Unsupported or promoted outcome class")
        urls = [row["source_url"]] + [source["url"] for source in row["additional_primary_sources"]]
        demand(all(urlparse(url).scheme == "https" and urlparse(url).netloc for url in urls), "Invalid final source")
        demand(row["factor_label"] is None or row["factor_label"] in factors, "Unknown final factor")
        demand(row["strategy_label"] is None or row["strategy_label"] in strategies, "Unknown final strategy")
        demand((row["factor_label"] is None) == (row["factor_review"]["factor"] == "ABSTAIN"), "Factor abstention erased")
        demand((row["strategy_label"] is None) == (row["strategy_review"]["strategy"] == "ABSTAIN"), "Strategy abstention erased")
        demand(row["human_ground_truth_approved"] is False, "AI review falsely promoted to human GT")
        demand(len(row["direct_mappings"]) <= 1, "Cartesian relation expansion")
        for mapping in row["direct_mappings"]:
            demand(row["factor_label"] and row["strategy_label"] and mapping["factor"] == row["factor_label"] and
                   mapping["strategy"] == row["strategy_label"] and mapping["kind"] == "APPLICABILITY_NOT_CAUSAL" and
                   row["mapping_review"]["decision"] == "SUPPORTED_APPLICABILITY", "Unsupported direct mapping")
        group_keys = [("organization", organization_key(row["organization"]))] + [("source", url) for url in urls]
        if row["parent_v1_case_id"]:
            group_keys.append(("parent", row["parent_v1_case_id"]))
        for key in group_keys:
            demand(key not in seen_groups or seen_groups[key] == row["sampling_group_id"], "Source or organization cluster split")
            seen_groups[key] = row["sampling_group_id"]
    labels = read_json(root, "independent_label_review_v2.json")["sessions"]
    relations = read_json(root, "independent_mapping_review_v2.json")["sessions"]
    all_sessions = labels + relations
    session_ids = [session["session_id"] for session in all_sessions]
    demand(len(session_ids) == len(set(session_ids)) and all(re.fullmatch(r"[0-9a-f-]{36}", value) for value in session_ids), "Reviewer sessions are not isolated")
    generated = read_csv(root, "v2/main_cases_v2.csv")
    demand(len(generated) == len(rows) and all(row["uncertainty"] and row["evidence_json"] for row in generated), "CSV dropped uncertainty or provenance")
    taxonomy = read_csv(root, "v2/strategy_taxonomy_v2_frozen.csv")
    demand(all(row["status"] == "FROZEN_V2_AI_REVIEWED_NOT_GT" for row in taxonomy), "Wrong frozen taxonomy status")
    creative = [row for row in rows if row["strategy_label"] == "S7_GENERATIVE_CONTENT_CREATION"]
    demand(len({row["organization"] for row in creative}) >= 3 and len({row["source_url"] for row in creative}) >= 3, "S7 lacks repeated independent-source support")
    return {**manifest["counts"], "freeze_valid": bool(freeze), "dataset_sha256": manifest["dataset_canonical_sha256"],
            "factor_counts": dict(Counter(row["factor_label"] or "ABSTAIN" for row in rows)),
            "strategy_counts": dict(Counter(row["strategy_label"] or "ABSTAIN" for row in rows)),
            "human_ground_truth": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze", action="store_true")
    arguments = parser.parse_args()
    print(json.dumps(validate(freeze=arguments.freeze), ensure_ascii=False, indent=2))
