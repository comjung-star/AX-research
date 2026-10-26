import argparse
import json

from scripts.audit_final_dataset import OUTPUT, fingerprint, load_csv
from scripts.build_ax_expansion_release import digest, read_json, write_json
from scripts.compare_final_reviews import compare
from scripts.prepare_v25_research import write_csv


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=["dev", "test"], required=True)
    arguments = parser.parse_args()
    split = arguments.split
    prefix = "test_" if split == "test" else ""
    document = read_json(OUTPUT / ("blind_test_relevance_input.json" if split == "test" else "blind_relevance_input.json"))
    input_hash = fingerprint(document)
    differences = load_csv(OUTPUT / f"{prefix}relevance_disagreements.csv")
    expected = {(row["query_id"], row["perspective_id"], row["case_id"]) for row in differences}
    proposals = {}
    provenance = {}
    for number in (1, 2):
        path = OUTPUT / f"reviewer_{number}/{split}_adjudication_proposals.csv"
        if not path.is_file():
            raise ValueError("Adjudication proposals are incomplete: " + str(path))
        provenance[path.relative_to(OUTPUT).as_posix()] = digest(path)
        for row in load_csv(path):
            key = (row["query_id"], row["perspective_id"], row["case_id"])
            if key not in expected or key in proposals or row["input_sha256"] != input_hash:
                raise ValueError("Duplicate/unexpected/wrong-input adjudication proposal")
            if row["relevance_0_4"] not in {"0", "1", "2", "3", "4"} or not row["rationale"].strip():
                raise ValueError("An adjudication proposal is not actually judged")
            proposals[key] = row
    if set(proposals) != expected:
        raise ValueError(f"All grade differences need adjudication: {len(proposals)} / {len(expected)}")
    parent_path = OUTPUT / f"parent_{split}_threshold_decisions.json"
    parent_overrides = {}
    if parent_path.is_file():
        parent = read_json(parent_path)
        if parent["input_sha256"] != input_hash:
            raise ValueError("Parent adjudication input mismatch")
        for group in parent["groups"]:
            for case_id, score, rationale in group["decisions"]:
                key = (group["query_id"], group["perspective_id"], case_id)
                if key not in expected or key in parent_overrides or type(score) is not int or not 0 <= score <= 4 or not rationale.strip():
                    raise ValueError("Parent adjudication grade or identity mismatch")
                parent_overrides[key] = {"query_id": key[0], "perspective_id": key[1], "case_id": key[2], "relevance_0_4": score,
                                         "rationale": rationale, "reviewer_id": parent["reviewer_id"], "input_sha256": input_hash}
        provenance[parent_path.name] = digest(parent_path)
    threshold_keys = {(row["query_id"], row["perspective_id"], row["case_id"]) for row in differences
                      if (int(row["grade_a"]) >= 3) != (int(row["grade_b"]) >= 3)}
    if set(parent_overrides) != threshold_keys:
        raise ValueError(f"Every positive-threshold conflict needs explicit parent review: {len(parent_overrides)} / {len(threshold_keys)}")
    decisions = [{**proposals[key], **parent_overrides.get(key, {})} for key in sorted(expected)]
    fields = ["query_id", "perspective_id", "case_id", "relevance_0_4", "rationale", "reviewer_id", "input_sha256"]
    write_csv(OUTPUT / f"{prefix}relevance_adjudication_decisions.csv", decisions, fields)
    result = compare(split)
    if result["unresolved_disagreements"] != 0:
        raise ValueError("Adjudication did not close all grade differences")
    approval = {"input_fingerprint": input_hash, "approved": True, "reviewer_id": "PARENT_AI_EVIDENCE_ADJUDICATOR",
                "rationale": "Two raw independent passes preserved. Every grade difference has a substantive post-independent proposal; every positive-threshold flip has an explicit parent Problem/Task/Context adjudication. All are AI-Silver judgments, not human Gold or researcher approval.",
                "split": split, "all_grade_disagreements_adjudicated": len(expected), "parent_threshold_adjudications": len(parent_overrides),
                "proposal_provenance_sha256": provenance, "final_qrels_sha256": digest(OUTPUT / f"{prefix}qrels_consensus.csv"),
                "human_gold": False, "researcher_approval": False,
                "independent_pass_provenance": {f"{prefix}relevance_pass_{number}.csv": digest(OUTPUT / f"{prefix}relevance_pass_{number}.csv") for number in (1, 2)}}
    write_json(OUTPUT / f"{prefix}relevance_adjudication.json", approval)
    print(json.dumps(approval, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
