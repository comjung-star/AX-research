"""Build the production-only, AI-reviewed release without altering staging or v1."""
from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import io
import json

from build_v2_replacement_release import ROOT, read_csv, read_json

INPUTS = (
    "active_candidate_corpus_v2.json", "inherited_evidence_review_v2.json",
    "final_source_corrections_v2.json", "independent_label_review_v2.json",
    "independent_mapping_review_v2.json", "strategy_taxonomy_v2.csv",
)
ANCHORS = ("problem_anchor", "context_anchor", "implementation_anchor", "deployment_anchor", "outcome_anchor")
SPLIT_ORGANIZATIONS = {
    "AX0006": "Danone", "AX0016": "Best Buy", "AX0017": "AT&T", "AX0042": "Law&Company",
    "AX0050": "Albert Heijn", "AX0068": "BNY", "AX0074": "Cashfree Payments",
    "AX0080": "Hong Leong Bank", "AX0092": "NatWest", "AX0093": "Suzhou Universal",
    "AX0094": "Savage Precision Fabrication",
}


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def demand(condition, message):
    if not condition:
        raise ValueError(message)


def session_records(payload, role):
    answers = {}
    inputs = {}
    for session in payload["sessions"]:
        if session["role"] != role:
            continue
        submitted = json.loads(session["submitted_prompt"].rsplit("\n", 1)[-1])
        expected_fields = {"review_id", "business_problem"} if role == "FACTOR_PROBLEM_TEXT_ONLY" else {"review_id", "task", "implementation"}
        demand(all(set(row) == expected_fields for row in submitted), "Review packet contains forbidden information")
        result = session["result"]
        expected_role = "STRICT_PROBLEM_TEXT_ONLY_AI" if role == "FACTOR_PROBLEM_TEXT_ONLY" else "SOLUTION_ONLY_STRATEGY_AI"
        demand(result["reviewer_role"] == expected_role, "Wrong independent reviewer role")
        identifiers = [row["review_id"] for row in submitted]
        returned = [row["review_id"] for row in result["records"]]
        demand(len(identifiers) == len(set(identifiers)) and len(returned) == len(set(returned)) and set(identifiers) == set(returned), "Missing or duplicated independent review")
        for row in submitted:
            identifier = row["review_id"]
            demand(identifier not in inputs or session.get("supersedes_matching_review_ids") is True, "Unexplained repeated review")
            inputs[identifier] = row
        for row in result["records"]:
            demand(row.get("rationale") and row.get("confidence") in {"HIGH", "MEDIUM", "LOW"}, "Independent review lacks rationale or confidence")
            answers[row["review_id"]] = {**row, "session_id": session["session_id"]}
    return inputs, answers


def corrected_candidates(root=ROOT):
    rows = copy.deepcopy(read_json(root, "active_candidate_corpus_v2.json")["cases"])
    inherited = read_json(root, "inherited_evidence_review_v2.json")["records"]
    expected = {row["case_id"] for row in rows if row["origin"] in {"HISTORICAL_FIRST_PASS_NOT_REAPPROVED", "PARENT_PRIMARY_RECONSTRUCTION"}}
    demand(len(inherited) == len(expected) and {row["case_id"] for row in inherited} == expected, "Every inherited case needs a source disposition")
    indexed = {row["case_id"]: row for row in inherited}
    additional = {row["case_id"]: row for row in read_json(root, "final_source_corrections_v2.json")["records"]}
    demand(set(additional) <= {row["case_id"] for row in rows}, "Unknown source correction")
    stage = {row["parent_v1_case_id"]: row for row in read_csv(root, "v2/main_case_parent_staging_v2.csv")}
    dispositions = []
    for row in rows:
        review = indexed.get(row["case_id"])
        if review:
            demand(review["decision"] in {"INCLUDE", "EXCLUDE"} and review["uncertainty"], "Invalid source disposition")
            demand(all(review.get(key) for key in ANCHORS), "Inherited source passage missing")
            row.update(review.get("updates", {}))
            row["organization"] = review["organization"]
            row["source_url"] = review.get("source_url", row["source_url"])
            row["evidence"] = {key: review[key] for key in ANCHORS}
            row["uncertainty"] = review["uncertainty"]
        if row["organization"] == "SEE_PRIMARY_SOURCE":
            row["organization"] = SPLIT_ORGANIZATIONS[row["parent_v1_case_id"]]
        if row["industry"] == "SEE_PARENT_STAGING":
            row["industry"] = stage[row["parent_v1_case_id"]]["industry_v1_provisional"]
        correction = additional.get(row["case_id"], {})
        row.update(correction.get("updates", {}))
        row["additional_primary_sources"] = []
        if correction.get("additional_source"):
            row["additional_primary_sources"].append({"url": correction["additional_source"], "anchors": correction["additional_anchors"]})
        if correction:
            row["uncertainty"] += " " + correction["reason"]
        decision = review["decision"] if review else "INCLUDE"
        dispositions.append({"case_id": row["case_id"], "decision": decision,
                             "reason": review["uncertainty"] if review else "Primary-source production/workflow review retained; independent annotation checked separately."})
    return rows, dispositions


def organization_key(name):
    key = name.casefold().split(" / ")[0]
    if key.startswith("ibm"):
        return "ibm"
    return key


def add_groups(rows):
    leaders = {row["case_id"]: row["case_id"] for row in rows}

    def leader(identifier):
        while leaders[identifier] != identifier:
            identifier = leaders[identifier]
        return identifier

    seen = {}
    for row in rows:
        keys = [("organization", organization_key(row["organization"])), ("source", row["source_url"])]
        keys += [("source", source["url"]) for source in row["additional_primary_sources"]]
        if row["parent_v1_case_id"]:
            keys.append(("parent", row["parent_v1_case_id"]))
        for key in keys:
            if key in seen:
                leaders[leader(row["case_id"])] = leader(seen[key])
            else:
                seen[key] = row["case_id"]
    components = {}
    for row in rows:
        components.setdefault(leader(row["case_id"]), []).append(row["case_id"])
    for row in rows:
        row["sampling_group_id"] = "AXV2G_" + digest(sorted(components[leader(row["case_id"])]))[:12]


def build(root=ROOT):
    rows, dispositions = corrected_candidates(root)
    reviews = read_json(root, "independent_label_review_v2.json")
    demand(reviews["user_authorized"] is True, "Independent AI delegation not authorized")
    identity = reviews["case_id_map"]
    demand(len(identity) == len(rows) and len({row["case_id"] for row in identity}) == len(rows), "Incomplete blinded ID map")
    review_ids = {row["case_id"]: row["review_id"] for row in identity}
    factor_inputs, factor_answers = session_records(reviews, "FACTOR_PROBLEM_TEXT_ONLY")
    strategy_inputs, strategy_answers = session_records(reviews, "STRATEGY_SOLUTION_ONLY")
    demand(set(factor_inputs) == set(review_ids.values()), "Factor review coverage incomplete")
    demand(set(strategy_inputs) == {"S" + key[1:] for key in review_ids.values()}, "Strategy review coverage incomplete")
    factor_labels = {row["factor_id"].split("_")[0]: row["factor_id"] for row in read_csv(root, "root_cause_factors_v1.csv")}
    strategy_labels = {row["strategy_id"].split("_")[0]: row["strategy_id"] for row in read_csv(root, "v2/strategy_taxonomy_v2.csv")}
    retained = {row["case_id"] for row in dispositions if row["decision"] == "INCLUDE"}
    included = []
    mapping_expected = set()
    for row in rows:
        factor_id = review_ids[row["case_id"]]
        strategy_id = "S" + factor_id[1:]
        demand(factor_inputs[factor_id]["business_problem"] == row["problem"], "Problem changed after blind review")
        demand(strategy_inputs[strategy_id] == {"review_id": strategy_id, "task": row["task"], "implementation": row["implementation"]}, "Solution changed after independent review")
        factor = factor_answers[factor_id]
        strategy = strategy_answers[strategy_id]
        demand(factor["factor"] in {*factor_labels, "ABSTAIN"} and strategy["strategy"] in {*strategy_labels, "ABSTAIN"}, "Unknown reviewed label")
        if row["case_id"] not in retained:
            continue
        demand(all(isinstance(row["evidence"].get(key), str) and row["evidence"][key].strip() for key in ANCHORS), "Final case lacks passage alignment")
        row["factor_label"] = factor_labels.get(factor["factor"])
        row["strategy_label"] = strategy_labels.get(strategy["strategy"])
        row["factor_review"] = factor
        row["strategy_review"] = strategy
        row["author_factor_disagreed"] = row["proposed_factor"] != row["factor_label"]
        row["author_strategy_disagreed"] = row["proposed_strategy"] != row["strategy_label"]
        row["annotation_status"] = "AI_REVIEWED_WITH_ABSTENTIONS" if not (row["factor_label"] and row["strategy_label"]) else "AI_REVIEWED"
        row["deployment_stage"] = "PRODUCTION"
        row["source_review_status"] = "AUTHOR_PRIMARY_PASSAGE_REVIEWED"
        row["human_ground_truth_approved"] = False
        if row["factor_label"] and row["strategy_label"]:
            mapping_expected.add(row["case_id"])
        for key in ("proposed_factor", "proposed_strategy", "mapping_status", "mapping_rationale"):
            row.pop(key)
        included.append(row)
    mapping_payload = read_json(root, "independent_mapping_review_v2.json")
    mapping = {}
    for session in mapping_payload["sessions"]:
        submitted = json.loads(session["submitted_prompt"].rsplit("\n", 1)[-1])
        returned = session["result"]["records"]
        demand(session["result"]["reviewer_role"] == "INDEPENDENT_DIRECT_APPLICABILITY_AI", "Wrong relation reviewer role")
        demand(len(submitted) == len(returned) and {row["case_id"] for row in submitted} == {row["case_id"] for row in returned}, "Relation review coverage mismatch")
        for entry in submitted:
            case = next(row for row in included if row["case_id"] == entry["case_id"])
            demand(entry["problem"] == case["problem"] and entry["implementation"] == case["implementation"] and
                   entry["factor"] == case["factor_review"]["factor"] and entry["strategy"] == case["strategy_review"]["strategy"], "Direct relation review is stale")
        for record in returned:
            demand(record["case_id"] not in mapping and record["rationale"] and record["decision"] in {"SUPPORTED_APPLICABILITY", "ABSTAIN"}, "Invalid or duplicated relation decision")
            mapping[record["case_id"]] = {**record, "session_id": session["session_id"]}
    demand(set(mapping) == mapping_expected, "Direct relation reviews incomplete")
    for row in included:
        relation = mapping.get(row["case_id"])
        row["direct_mappings"] = []
        row["mapping_review"] = relation or {"decision": "ABSTAIN", "rationale": "Factor or strategy explicitly abstained; no pair is created."}
        if relation and relation["decision"] == "SUPPORTED_APPLICABILITY":
            row["direct_mappings"].append({"factor": row["factor_label"], "strategy": row["strategy_label"],
                                           "kind": "APPLICABILITY_NOT_CAUSAL", "rationale": relation["rationale"],
                                           "evidence_anchors": [row["evidence"]["problem_anchor"], row["evidence"]["implementation_anchor"]]})
    add_groups(included)
    counts = {"source_candidates": len(rows), "included_workflows": len(included), "excluded_workflows": len(rows) - len(included),
              "factor_abstentions": sum(row["factor_label"] is None for row in included),
              "strategy_abstentions": sum(row["strategy_label"] is None for row in included),
              "supported_direct_mappings": sum(len(row["direct_mappings"]) for row in included),
              "sampling_groups": len({row["sampling_group_id"] for row in included}),
              "human_ground_truth_approved": 0}
    dataset = {"dataset_version": "2.0.0", "status": "FROZEN_SOURCE_CURATED_AI_ANNOTATED_WITH_ABSTENTIONS",
               "scope": "PRODUCTION_ONLY", "review_date": "2026-10-22", "counts": counts,
               "ground_truth_status": "NOT_HUMAN_GROUND_TRUTH", "cases": included, "dispositions": dispositions}
    manifest = {"dataset_version": "2.0.0", "status": dataset["status"], "counts": counts,
                "dataset_canonical_sha256": digest(dataset),
                "input_canonical_sha256": {name: digest(read_json(root, name)) if name.endswith(".json") else
                                           digest(read_csv(root, "v2/" + name)) for name in INPUTS},
                "label_source": "Isolated AI problem-only factor, separate solution-only strategy, separate applicability review; author source adjudication",
                "abstention_policy": "Retain eligible workflow; leave unsupported factor/strategy null and omit unsupported direct mappings. Exclude null labels from label-specific statistics.",
                "evaluation_restriction": "Not human GT, not retrieval relevance labels, not a held-out benchmark, and not causal or Wald evidence. Group by sampling_group_id before any split.",
                "sampling": "Purposeful/convenience sample, including source/organization clusters; no population representativeness claimed."}
    return dataset, manifest


def artifacts(root=ROOT):
    dataset, manifest = build(root)
    buffer = io.StringIO(newline="")
    fields = ["case_id", "parent_v1_case_id", "organization", "industry", "problem", "task", "context", "implementation",
              "outcome", "outcome_type", "source_url", "uncertainty", "factor_label", "strategy_label", "annotation_status", "sampling_group_id",
              "evidence_json", "additional_primary_sources_json", "direct_mappings_json", "mapping_decision"]
    writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
    writer.writeheader()
    for row in dataset["cases"]:
        writer.writerow({**row, "evidence_json": canonical(row["evidence"]),
                         "additional_primary_sources_json": canonical(row["additional_primary_sources"]),
                         "direct_mappings_json": canonical(row["direct_mappings"]), "mapping_decision": row["mapping_review"]["decision"]})
    taxonomy = read_csv(root, "v2/strategy_taxonomy_v2.csv")
    taxonomy_buffer = io.StringIO(newline="")
    taxonomy_writer = csv.DictWriter(taxonomy_buffer, fieldnames=list(taxonomy[0]), lineterminator="\n")
    taxonomy_writer.writeheader()
    taxonomy_writer.writerows({**row, "status": "FROZEN_V2_AI_REVIEWED_NOT_GT"} for row in taxonomy)
    return {"main_cases_v2.json": json.dumps(dataset, ensure_ascii=False, indent=2) + "\n",
            "main_cases_v2.csv": buffer.getvalue(),
            "release_manifest_v2.json": json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            "strategy_taxonomy_v2_frozen.csv": taxonomy_buffer.getvalue()}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    arguments = parser.parse_args()
    for name, content in artifacts().items():
        path = ROOT / "data/v2" / name
        if arguments.check:
            demand(path.read_text(encoding="utf-8") == content, "Release artifact is stale: " + name)
        else:
            path.write_text(content, encoding="utf-8", newline="\n")
    print(json.dumps(build()[1]["counts"], ensure_ascii=False))
