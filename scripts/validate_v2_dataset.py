"""Validate that AX Dataset v2 remains an explicitly unapproved evidence staging area.

No external dependency or network call. This validator checks schema/lineage and
prevents provisional legacy labels from silently becoming new Ground Truth.
"""
from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def load(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows or any(None in row for row in rows):
        raise ValueError(f"Malformed or empty CSV: {path}")
    return rows


def demand(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def run() -> dict[str, int]:
    old = load(DATA / "main_cases_v1.csv")
    stage = load(DATA / "v2/main_case_parent_staging_v2.csv")
    splits = load(DATA / "v2/workflow_split_drafts_v2.csv")
    holds = load(DATA / "v2/scope_hold_exclusions_v2.csv")
    pilot = load(DATA / "v2/source_relabel_pilot_v2.csv")
    scope = load(DATA / "v2/production_scope_decisions_v2.csv")
    summary = json.loads((DATA / "v2/build_summary_v2.json").read_text(encoding="utf-8"))

    old_ids = {r["case_id"] for r in old}
    scope_ids = [row["parent_case_id"] for row in scope]
    demand(len(scope_ids) == len(set(scope_ids)), "Duplicate production scope decision")
    demand(set(scope_ids) <= old_ids, "Unknown production scope parent")
    for row in scope:
        demand(row["eligibility"] in {"EXCLUDE_PILOT", "HOLD_PRODUCTION_UNVERIFIED"},
               "Scope ledger cannot grant production approval")
        demand(all(row[field].strip() for field in
                   ("deployment_stage", "source_url", "evidence_anchor", "reason")),
               "Production scope decision lacks evidence or reason")
        demand(row["source_url"].startswith("https://"), "Invalid production evidence URL")
    staged_ids = [r["parent_v1_case_id"] for r in stage]
    hold_ids = [r["case_id"] for r in holds]
    demand(len(old) == 100 and len(old_ids) == 100, "Frozen input must have 100 distinct cases")
    demand(len(stage) == 94 and len(set(staged_ids)) == 94, "Expected 94 unique candidate parents")
    demand(len(holds) == 6 and len(set(hold_ids)) == 6, "Expected six distinct held records")
    demand(set(staged_ids).isdisjoint(hold_ids), "Candidate and held cases overlap")
    demand(set(staged_ids) | set(hold_ids) == old_ids, "v1 parent-case lineage incomplete")
    statuses = Counter(r["source_scope_status"] for r in stage)
    demand(statuses == {"KEEP_WORKFLOW_CANDIDATE": 75, "SPLIT_REVIEW": 19},
           f"Unexpected parent-case classification: {statuses}")
    demand(all(r["workflow_case_acceptance"] == "NOT_YET_APPROVED" for r in stage),
           "Staging contains prematurely approved case")
    demand(all(not r["proposed_outcome"] for r in stage),
           "Original KPI cannot be automatically promoted")
    for row in stage:
        is_split = row["source_scope_status"] == "SPLIT_REVIEW"
        keys = ("workflow_business_problem_draft", "workflow_task_draft",
                "workflow_context_draft", "workflow_implementation_draft")
        demand(all(not row[k] for k in keys) if is_split else all(row[k] for k in keys),
               f"Invalid provisional workflow field policy: {row['parent_v1_case_id']}")
        demand(bool(row["original_source"]), "Source missing")
    split_parents = {r["parent_v1_case_id"] for r in stage if r["source_scope_status"] == "SPLIT_REVIEW"}
    demand(len(splits) == 38 and len({r["draft_workflow_id"] for r in splits}) == 38,
           "Expected 38 unique split hypotheses")
    demand({r["parent_case_id"] for r in splits} == split_parents,
           "Split hypotheses do not cover exactly 19 candidate parents")
    for row in splits:
        demand(row["case_approval"] == "NOT_APPROVED", "Unverified child promoted")
        demand(not row["factor_labels"] and not row["strategy_labels"] and
               not row["outcome_new_verified"], "Old labels/outcomes leaked to proposed child")
        demand(row["source_url"] and row["locator_keyword"],
               "Child workflow lacks source locator")
    demand(len(pilot) >= 10 and len({r["parent_case_id"] for r in pilot}) == len(pilot),
           "Source-review rows must have unique parents and at least ten entries")
    demand({r["parent_case_id"] for r in pilot} <= set(staged_ids) - split_parents,
           "Pilot contains held/split parent")
    for row in pilot:
        demand(row["review_status"] == "SOURCE_REVIEWED_ONE_PASS_NOT_FROZEN",
               "Pilot falsely upgraded to frozen status")
        demand(row["second_reviewer_approved"] == "NO", "No secondary review has occurred")
        demand(row["direct_factor_strategy_relation_status"] == "NOT_ESTABLISHED",
               "Incorrect evidence-relation approval")
        for col in ("business_problem_problem_view", "task_problem_view", "context_problem_view",
                    "implementation_solution_view", "primary_root_cause_factor",
                    "primary_strategy", "primary_source_url", "problem_evidence_locator",
                    "solution_evidence_locator", "outcome_evidence_locator"):
            demand(bool(row[col]), f"Missing source evidence {row['parent_case_id']}/{col}")
    demand(summary["new_approved_v2_case_count"] == 0,
           "Summary must not report unapproved as accepted")
    demand(summary["new_verified_factor_strategy_relations"] == 0,
           "No direct factor-strategy relations verified")
    demand(summary["provisional_parent_case_candidates"] == len(stage) and
           summary["excluded_pending_source_review"] == len(holds) and
           summary["draft_workflow_suggestions_not_validated"] == len(splits),
           "Summary doesn't match actual staged files")
    return {"old": len(old), "staging": len(stage), "holds": len(holds),
            "split_parent": len(split_parents), "split_draft": len(splits),
            "source_review_one_pass": len(pilot), "approved": 0}


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, sort_keys=True))
