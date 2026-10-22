"""Validate replacement coverage, primary evidence fields and candidate-only release."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from urllib.parse import urlparse

from build_v2_replacement_release import ROOT, build, read_csv, read_json


def demand(condition, message):
    if not condition:
        raise ValueError(message)


def validate(root=ROOT, freeze=False):
    source = read_json(root, "replacement_cases_v2.json")
    demand(source["status"] == "SOURCE_REVIEWED_PRODUCTION_CANDIDATES_NOT_FROZEN", "Replacement approval is not established")
    rows = source["cases"]
    demand(len(rows) == 40 and len({row["id"] for row in rows}) == 40, "Expected 40 distinct replacement workflows")
    demand(len({(row["organization"].casefold(), row["task"].casefold()) for row in rows}) == 40, "Duplicate replacement business workflow")
    fields = ("organization", "industry", "task", "problem", "context", "implementation", "problem_anchor", "context_anchor",
              "implementation_anchor", "deployment_anchor", "outcome_anchor", "outcome", "outcome_type", "mapping", "uncertainty")
    allowed_outcomes = {
        "USER_REPORTED_ANECDOTE", "VENDOR_REPORTED_OPERATIONAL", "USER_REPORTED_OPERATIONAL",
        "VENDOR_REPORTED_ESTIMATE_IN_PRODUCTION", "DEPLOYMENT_CONFIRMED_OUTCOME_UNKNOWN",
        "VENDOR_REPORTED_QUALITATIVE", "PRODUCTION_EXPERIMENT_REPORTED", "VENDOR_REPORTED_USAGE",
        "USER_REPORTED_QUALITATIVE", "SHARED_CAMPAIGN_OUTCOME_NOT_COMPONENT_EFFECT",
        "DEPLOYED_SYSTEM_TEST_RESULT", "MANUFACTURER_REPORTED_OPERATIONAL",
        "VENDOR_REPORTED_OPERATIONAL_WITH_METRIC_CAVEAT", "OBSERVED_WITH_SEPARATE_PROJECTION",
        "DEPLOYMENT_CONFIRMED_SHARED_KPI_WITHHELD", "DEPLOYMENT_CONFIRMED_EVALUATION_KPI_WITHHELD"}
    factors = {row["factor_id"].split("_")[0] for row in read_csv(root, "root_cause_factors_v1.csv")}
    taxonomy = read_csv(root, "v2/strategy_taxonomy_v2.csv")
    strategies = {row["strategy_id"].split("_")[0] for row in taxonomy}
    demand(len(taxonomy) == 7 and len(strategies) == 7, "Working strategy dictionary must contain seven unique classes")
    original_strategies = {row["strategy_id"] for row in read_csv(root, "strategy_taxonomy_v1.csv")}
    demand(original_strategies <= {row["strategy_id"] for row in taxonomy}, "Legacy strategy identifiers cannot be silently renamed")
    old_parents = {row["case_id"] for row in read_csv(root, "main_cases_v1.csv")}
    for row in rows:
        demand(all(isinstance(row.get(key), str) and row[key].strip() for key in fields), "Missing source passage evidence or qualification")
        demand(row["strategy"] in strategies, "Unrecognized proposed label")
        demand(row["factor"] in factors or (row["factor"] == "ABSTAIN" and bool(row.get("factor_abstention_reason"))), "Unsupported factor without explicit abstention reason")
        demand(row["outcome_type"] in allowed_outcomes, "Unknown or silently promoted outcome type")
        url = urlparse(row["source"])
        demand(url.scheme == "https" and bool(url.netloc), "Invalid primary source URL")
        demand(row.get("parent_v1_case_id") is None or row["parent_v1_case_id"] in old_parents, "Unknown source-parent lineage")
        demand(not any(key in row for key in ("approved", "second_reviewer_approved", "frozen")), "Author cannot self-certify independent approval")
    visual = [row for row in rows if row["strategy"] == "S7"]
    demand(len({row["organization"] for row in visual}) >= 3, "S7 needs evidence in at least three organizations")
    demand(len({row["source"] for row in visual}) >= 3, "Repeated URL is not independent taxonomy support")
    supported = next(row for row in taxonomy if row["strategy_id"].startswith("S7_"))["evidence_ids"].split("|")
    demand(set(supported) == {row["id"] for row in visual}, "Taxonomy evidence must identify the actual S7 workflows")
    demand(all(row["status"] == "WORKING_V2_NOT_GT" for row in taxonomy), "Working taxonomy cannot silently freeze")
    access = read_csv(root, "v2/replacement_source_access_v2.csv")
    demand(len(access) == len(rows) and {(row["parent_case_id"], row["url"]) for row in access} ==
           {(row["id"], row["source"]) for row in rows}, "Replacement access inventory does not match reviewed sources")
    demand(all(row["accessed_at_utc"] and row["status"] in {"ACCESS_FAILED", "FETCHED_NOT_SEMANTICALLY_VERIFIED", "NON_HTML_REQUIRES_MANUAL_REVIEW"} for row in access), "Download status cannot certify source truth")
    expected = build(root)
    actual = read_json(root, "active_candidate_corpus_v2.json")
    demand(actual == expected, "Generated candidate corpus is stale or edited outside the builder")
    demand(actual["approved_case_count"] == 0 and actual["independent_blind_label_approval"] is False, "Unapproved labels promoted")
    ledger = actual["replacement_ledger"]
    demand(len({row["replaced_id"] for row in ledger}) == 40, "Duplicate replaced slot")
    demand({row["replacement_id"] for row in ledger} == {row["id"] for row in rows}, "Replacement ledger incomplete")
    active = actual["cases"]
    demand(len({row["case_id"] for row in active}) == len(active), "Duplicate active candidate id")
    replaced_parent_ids = {row["replaced_id"] for row in ledger if row["replaced_unit"] == "PARENT"}
    demand(not any(row["parent_v1_case_id"] in replaced_parent_ids for row in active), "Excluded parent leaked into active corpus")
    demand(not any(row["parent_v1_case_id"] in actual["historical_first_pass_exclusions"] for row in active), "Historical hold leaked into active corpus")
    for row in active:
        demand(row["proposed_strategy"] and (row["proposed_factor"] or row["mapping_status"] == "ABSTAIN_FACTOR_EVIDENCE"), "Missing proposed label or abstention")
        demand(row["mapping_status"] in {"PROPOSED_APPLICABILITY_NOT_CAUSAL", "ABSTAIN_PENDING_PASSAGE_ALIGNMENT", "ABSTAIN_FACTOR_EVIDENCE"}, "Unapproved direct relation promoted")
        demand("|" not in (row["proposed_factor"] or "") + row["proposed_strategy"], "Cartesian factor-strategy expansion prohibited")
    summary = {"replacement_workflows": len(rows), "replaced_parent_slots": len(replaced_parent_ids),
               "replaced_split_slots": sum(row["replaced_unit"] == "SPLIT" for row in ledger),
               "active_candidates": len(active), "origin_counts": actual["origin_counts"],
               "new_organizations": len({row["organization"] for row in rows}),
               "source_urls": len({row["source"] for row in rows}),
               "factor_abstentions": sum(row["factor"] == "ABSTAIN" for row in rows),
               "replacement_strategy_counts": dict(Counter(row["strategy"] for row in rows)),
               "approved_frozen_cases": 0, "freeze_ready": False}
    if freeze:
        raise ValueError("FREEZE BLOCKED: active records remain first-pass candidates; independently blinded label approval and passage alignment have not occurred")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze", action="store_true")
    args = parser.parse_args()
    print(json.dumps(validate(freeze=args.freeze), ensure_ascii=False, indent=2))
