"""Build a traceable candidate inventory; never approve source or GT labels."""
from __future__ import annotations

import csv
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_json(root, name):
    return json.loads((root / "data/v2" / name).read_text(encoding="utf-8"))


def read_csv(root, name):
    with (root / "data" / name).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def build(root=ROOT):
    replacements = read_json(root, "replacement_cases_v2.json")["cases"]
    screens = read_json(root, "remaining_parent_screening_v2.json")["parents"]
    parents = read_json(root, "parent_reconstructions_v2.json")["cases"]
    reconstructed = {row["parent"] for row in parents}
    decisions = read_json(root, "split_adjudications_v2.json")["decisions"]
    targets = [(row["parent"], "PARENT", row["finding"]) for row in screens if row["parent"] not in reconstructed]
    targets += [(row["draft_id"], "SPLIT", row["reason"]) for row in decisions if row["decision"].startswith("HOLD_")]
    targets += [("AX0098", "PARENT", "Insufficient independent implementation detail")]
    targets.sort()
    if len(replacements) != len(targets):
        raise ValueError("Each authorized unresolved slot requires one replacement")
    ledger = [{"replaced_id": target[0], "replaced_unit": target[1], "replacement_id": row["id"],
               "reason": target[2], "relationship": "ADMINISTRATIVE_SUBSTITUTION_NOT_EVIDENCE_LINEAGE"}
              for target, row in zip(targets, sorted(replacements, key=lambda row: row["id"]))]
    factors = {row["factor_id"].split("_")[0]: row["factor_id"] for row in read_csv(root, "root_cause_factors_v1.csv")}
    strategies = {row["strategy_id"].split("_")[0]: row["strategy_id"] for row in read_csv(root, "v2/strategy_taxonomy_v2.csv")}
    corpus = []
    for row in replacements:
        corpus.append({"case_id": row["id"], "origin": "REPLACEMENT_PRIMARY_REVIEW",
                       "parent_v1_case_id": row.get("parent_v1_case_id"),
                       "organization": row["organization"], "industry": row["industry"],
                       "problem": row["problem"], "task": row["task"], "context": row["context"],
                       "implementation": row["implementation"], "outcome": row["outcome"],
                       "outcome_type": row["outcome_type"], "source_url": row["source"],
                       "evidence": {key: row[key] for key in ("problem_anchor", "context_anchor", "implementation_anchor", "deployment_anchor", "outcome_anchor")},
                       "proposed_factor": factors.get(row["factor"]), "proposed_strategy": strategies[row["strategy"]],
                       "mapping_status": "ABSTAIN_FACTOR_EVIDENCE" if row["factor"] == "ABSTAIN" else "PROPOSED_APPLICABILITY_NOT_CAUSAL",
                       "mapping_rationale": row.get("factor_abstention_reason", row["mapping"]),
                       "uncertainty": row["uncertainty"]})
    drafts = {row["draft_workflow_id"]: row for row in read_csv(root, "v2/workflow_split_drafts_v2.csv")}
    indexed = {row["draft_id"]: row for row in decisions}
    for row in read_json(root, "workflow_candidates_v2.json")["cases"]:
        corpus.append({"case_id": row["case_id"], "origin": "SPLIT_PRIMARY_REVIEW", "parent_v1_case_id": row["parent_case_id"],
                       "organization": "SEE_PRIMARY_SOURCE", "industry": "SEE_PARENT_STAGING",
                       "problem": row["problem"], "task": row["task"], "context": row["context"],
                       "implementation": row["implementation"], "outcome": row["outcome"], "outcome_type": row["outcome_type"],
                       "source_url": indexed[row["draft_id"]].get("source_url", drafts[row["draft_id"]]["source_url"]),
                       "evidence": {"problem_anchor": row["problem_anchor"], "context_anchor": row["production_anchor"],
                                    "implementation_anchor": row["implementation_anchor"], "deployment_anchor": row["production_anchor"], "outcome_anchor": row["outcome_anchor"]},
                       "proposed_factor": row["factor"], "proposed_strategy": row["strategy"],
                       "mapping_status": "PROPOSED_APPLICABILITY_NOT_CAUSAL", "mapping_rationale": row["mapping_rationale"],
                       "uncertainty": "First-pass review; not independent blind labeling or approved Ground Truth"})
    stage = {row["parent_v1_case_id"]: row for row in read_csv(root, "v2/main_case_parent_staging_v2.csv")}
    source_screens = {row["parent"]: row for row in screens}
    report_url = "https://www.nipa.kr/comm/getFile?srvcId=BBSTY1&upperNo=Co1q7uuEpe2WvBi9**6DZg==&fileTy=ATTACH&fileNo=Aa7YtxzX3F8qeDCOXtcHPw=="
    for row in parents:
        if row.get("acceptance", "").startswith("HOLD_"):
            continue
        parent = row["parent"]
        corpus.append({"case_id": "AXV2P2_" + parent[2:] + "_01", "origin": "PARENT_PRIMARY_RECONSTRUCTION", "parent_v1_case_id": parent,
                       "organization": "SEE_PRIMARY_SOURCE", "industry": stage[parent]["industry_v1_provisional"],
                       "problem": row["problem"], "task": row["task"], "context": row["context"], "implementation": row["implementation"],
                       "outcome": row["outcome"], "outcome_type": row["outcome_type"],
                       "source_url": report_url if parent in {"AX0036", "AX0039", "AX0040"} else
                                     re.findall(r"https?://[^\s;]+", stage[parent]["original_source"])[-1],
                       "evidence": {"review_record": "remaining_parent_screening_v2.json#" + parent, "section": source_screens[parent]["anchor"]},
                       "proposed_factor": factors[row["factor"]], "proposed_strategy": strategies[row["strategy"]],
                       "mapping_status": "ABSTAIN_PENDING_PASSAGE_ALIGNMENT", "mapping_rationale": "",
                       "uncertainty": "Reconstruction has section-level evidence; independent alignment/approval not complete"})
    excluded_historical = {"AX0027": "Anonymous operating context lacks identified customer confirmation",
                           "AX0079": "Catalog attribute classification taxonomy boundary unresolved",
                           "AX0087": "Try-on problem boundary and component-outcome attribution require reconstruction",
                           "AX0095": "Pilot only", "AX0096": "Pilot only"}
    for row in read_csv(root, "v2/source_relabel_pilot_v2.csv"):
        parent = row["parent_case_id"]
        if parent in excluded_historical:
            continue
        corpus.append({"case_id": "AXV2H_" + parent[2:] + "_01", "origin": "HISTORICAL_FIRST_PASS_NOT_REAPPROVED", "parent_v1_case_id": parent,
                       "organization": "SEE_PRIMARY_SOURCE", "industry": stage[parent]["industry_v1_provisional"],
                       "problem": row["business_problem_problem_view"], "task": row["task_problem_view"], "context": row["context_problem_view"],
                       "implementation": row["implementation_solution_view"], "outcome": row["reported_outcome"], "outcome_type": row["outcome_evidence_type"],
                       "source_url": row["primary_source_url"],
                       "evidence": {"problem_anchor": row["problem_evidence_locator"], "implementation_anchor": row["solution_evidence_locator"], "outcome_anchor": row["outcome_evidence_locator"]},
                       "proposed_factor": row["primary_root_cause_factor"], "proposed_strategy": row["primary_strategy"],
                       "mapping_status": "ABSTAIN_PENDING_PASSAGE_ALIGNMENT", "mapping_rationale": "", "uncertainty": row["outcome_qualification"]})
    corpus.sort(key=lambda row: row["case_id"])
    return {"status": "ACTIVE_CANDIDATES_NOT_FROZEN_NOT_GT", "scope": "PRODUCTION_ONLY",
            "independent_blind_label_approval": False, "approved_case_count": 0,
            "replacement_ledger": ledger, "historical_first_pass_exclusions": excluded_historical,
            "origin_counts": dict(Counter(row["origin"] for row in corpus)), "cases": corpus}


if __name__ == "__main__":
    payload = build()
    output = ROOT / "data/v2/active_candidate_corpus_v2.json"
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"candidate_count": len(payload["cases"]), "replacement_count": len(payload["replacement_ledger"]),
                      "origins": payload["origin_counts"], "approved": 0}, ensure_ascii=False))
