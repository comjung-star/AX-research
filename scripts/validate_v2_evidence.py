"""Validate new evidence and explicitly refuse a premature v2 freeze."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE = "cce75b8d14c2a191ebf3916239de68bf85121c22"


def load_csv(root, name):
    with (root / name).open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        if not rows or any(None in row or None in row.values() for row in rows):
            raise ValueError(f"Malformed or empty CSV: {name}")
        return rows


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate(root=ROOT, freeze=False):
    stage = load_csv(root, "data/v2/main_case_parent_staging_v2.csv")
    parents = {row["parent_v1_case_id"] for row in stage}
    drafts = {row["draft_workflow_id"]: row for row in load_csv(root, "data/v2/workflow_split_drafts_v2.csv")}
    scope = {row["parent_case_id"]: row for row in load_csv(root, "data/v2/production_scope_decisions_v2.csv")}
    review = json.loads((root / "data/v2/split_adjudications_v2.json").read_text(encoding="utf-8"))
    decisions = review["decisions"]
    require(len(decisions) == len(drafts), "Every split hypothesis needs exactly one disposition")
    require({row["draft_id"] for row in decisions} == set(drafts), "Split coverage mismatch")
    require(len({row["draft_id"] for row in decisions}) == len(decisions), "Duplicate split decision")
    allowed = {"PRODUCTION_CANDIDATE", "EXCLUDE_PILOT", "HOLD_WORKFLOW_BOUNDARY",
               "REJECT_GENERIC_SPLIT", "HOLD_PRIMARY_REPORT", "HOLD_IMPLEMENTATION_DETAIL",
               "HOLD_PRODUCTION_UNVERIFIED", "REJECT_PLATFORM_SPLIT"}
    for row in decisions:
        require(row["decision"] in allowed, "Unknown split decision")
        require(row.get("anchor") and row.get("reason"), "Split lacks evidence anchor or reason")
    indexed = {row["draft_id"]: row for row in decisions}
    factors = {row["factor_id"] for row in load_csv(root, "data/root_cause_factors_v1.csv")}
    strategies = {row["strategy_id"] for row in load_csv(root, "data/strategy_taxonomy_v1.csv")}
    payload = json.loads((root / "data/v2/workflow_candidates_v2.json").read_text(encoding="utf-8"))
    require(payload["status"] == "SOURCE_GROUNDED_CANDIDATES_NOT_FROZEN", "Premature candidate approval")
    cases = payload["cases"]
    require(cases and len({row["case_id"] for row in cases}) == len(cases), "Duplicate or empty candidates")
    require(len({row["draft_id"] for row in cases}) == len(cases), "Duplicate workflow reconstruction")
    required = ("task", "problem", "context", "implementation", "production_anchor", "problem_anchor",
                "implementation_anchor", "outcome", "outcome_type", "outcome_anchor", "mapping_rationale")
    for row in cases:
        parent = row["parent_case_id"]
        require(parent in parents, "Unknown or held legacy parent")
        require(parent not in scope, "Excluded or uncertain-production parent promoted")
        require(row["draft_id"] in indexed, "Missing split lineage")
        require(drafts[row["draft_id"]]["parent_case_id"] == parent, "Child-parent mismatch")
        require(indexed[row["draft_id"]]["decision"] == "PRODUCTION_CANDIDATE", "Rejected split promoted")
        require(all(isinstance(row.get(key), str) and row[key].strip() for key in required), "Incomplete workflow evidence")
        require(row["factor"] in factors and row["strategy"] in strategies, "Invalid factor or strategy")
        require("|" not in row["factor"] + row["strategy"], "Implicit Cartesian mapping prohibited")
        require(row["outcome_type"].startswith("VENDOR_REPORTED_"), "Unsupported outcome evidence type")
        source = indexed[row["draft_id"]].get("source_url", drafts[row["draft_id"]]["source_url"])
        require(source.startswith("https://"), "Missing primary source")
    access = load_csv(root, "data/v2/source_access_audit_v2.csv")
    require({row["parent_case_id"] for row in access} == parents, "Source access inventory lacks parents")
    require(len({(row["parent_case_id"], row["url"]) for row in access}) == len(access), "Duplicate source access record")
    for row in access:
        require(row["status"] in {"ACCESS_FAILED", "FETCHED_NOT_SEMANTICALLY_VERIFIED", "NON_HTML_REQUIRES_MANUAL_REVIEW"}, "Download silently treated as source approval")
        if row["status"] == "FETCHED_NOT_SEMANTICALLY_VERIFIED":
            require(len(row["sha256"]) == 64 and int(row["visible_characters"]) > 0, "Missing source fingerprint")
    pilot = load_csv(root, "data/v2/source_relabel_pilot_v2.csv")
    split_parents = {row["parent_case_id"] for row in drafts.values()}
    prior_review_parents = {row["parent_case_id"] for row in pilot}
    pending = sorted(parents - split_parents - prior_review_parents)
    screening = json.loads((root / "data/v2/remaining_parent_screening_v2.json").read_text(encoding="utf-8"))
    screened = screening["parents"]
    require({row["parent"] for row in screened} == set(pending), "Remaining-parent screening coverage mismatch")
    require(len(screened) == len(pending), "Duplicate remaining-parent screen")
    for row in screened:
        require(row["depth"] in {"PASSAGE_SCREEN", "ACCESS_FAILED", "ACCESS_LIMITED", "SECONDARY_ONLY"}, "Unknown screening depth")
        require(row["anchor"] and row["finding"], "Screening lacks source limitation or finding")
    parent_payload = json.loads((root / "data/v2/parent_reconstructions_v2.json").read_text(encoding="utf-8"))
    require(parent_payload["status"] == "SOURCE_GROUNDED_CANDIDATES_NOT_FROZEN", "Parent reconstructions prematurely approved")
    reconstructed = parent_payload["cases"]
    reconstructed_ids = [row["parent"] for row in reconstructed]
    require(len(reconstructed_ids) == len(set(reconstructed_ids)), "Duplicate parent reconstruction")
    require(set(reconstructed_ids) <= set(pending), "Unexpected parent reconstruction")
    factor_prefixes = {label.split("_")[0] for label in factors}
    strategy_prefixes = {label.split("_")[0] for label in strategies}
    for row in reconstructed:
        require(all(isinstance(row.get(key), str) and row[key].strip() for key in
                    ("problem", "task", "context", "implementation", "outcome", "outcome_type")), "Incomplete parent reconstruction")
        require(row["factor"] in factor_prefixes and row["strategy"] in strategy_prefixes, "Invalid reconstructed label")
        require(row["parent"] not in scope, "Excluded parent reconstructed as production")
    pending = sorted(set(pending) - set(reconstructed_ids))
    unresolved = [row["draft_id"] for row in decisions if row["decision"].startswith("HOLD_")]
    summary = {"source_inventory_parents": len(parents), "historical_first_pass_parents": len(prior_review_parents),
               "split_dispositions": len(decisions), "split_disposition_counts": dict(Counter(row["decision"] for row in decisions)),
               "reconstructed_workflows": len(cases), "remaining_non_split_parents_without_detailed_review": pending,
               "additional_parent_reconstructions": len(reconstructed), "remaining_parent_screens": len(screened),
               "unresolved_split_hypotheses": unresolved, "approved_frozen_cases": 0,
               "freeze_ready": False}
    if freeze:
        raise ValueError("FREEZE BLOCKED: detailed source reviews remain pending; split holds and taxonomy gaps remain; independent label approval absent. " + json.dumps(summary, ensure_ascii=False))
    return summary


def verify_immutable(root=ROOT):
    paths = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", BASELINE], cwd=root, text=True).splitlines()
    protected = [path for path in paths if path.startswith("experiments/") or
                 (path.startswith("data/") and not path.startswith("data/v2/"))]
    for relative in protected:
        baseline = subprocess.check_output(["git", "show", f"{BASELINE}:{relative}"], cwd=root)
        current = (root / relative).read_bytes()
        require(hashlib.sha256(baseline).digest() == hashlib.sha256(current.replace(b"\r\n", b"\n")).digest()
                or baseline == current, f"Immutable research artifact changed: {relative}")
    return len(protected)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze", action="store_true")
    parser.add_argument("--check-immutable", action="store_true")
    arguments = parser.parse_args()
    result = validate(freeze=arguments.freeze)
    if arguments.check_immutable:
        result["immutable_files_checked"] = verify_immutable()
    print(json.dumps(result, ensure_ascii=False, indent=2))
