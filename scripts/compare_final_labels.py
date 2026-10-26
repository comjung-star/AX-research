import json

from scripts.audit_final_dataset import OUTPUT, fingerprint, load_csv
from scripts.build_ax_expansion_release import ROOT, digest, read_json, write_json
from scripts.prepare_v25_research import write_csv


def parse_labels(row, label_field, allowed):
    labels = set(filter(None, row[label_field].split("|")))
    if not labels <= allowed or row["decision"] not in {"LABEL", "ABSTAIN"}:
        raise ValueError("Unknown label or decision")
    if bool(labels) != (row["decision"] == "LABEL") or not row["rationale"].strip():
        raise ValueError("Abstention and supported-label evidence disagree")
    return labels


def compare_labels(kind):
    label_field = kind + "_labels"
    input_path = OUTPUT / f"{kind}_blind_input.csv"
    input_hash = digest(input_path)
    inputs = {row["case_id"]: row for row in load_csv(input_path)}
    taxonomy_name = "root_cause" if kind == "factor" else "strategy"
    taxonomy_path = ROOT / f"data/v2_3/{taxonomy_name}_taxonomy_v2_3.csv"
    allowed = {row[kind + "_id"] for row in load_csv(taxonomy_path)}
    passes = []
    reviewers = []
    for number in (1, 2):
        path = OUTPUT / f"{kind}_pass_{number}.csv"
        if not path.is_file():
            return {"status": "WAITING_FOR_TWO_INDEPENDENT_PASSES", "kind": kind}
        rows = load_csv(path)
        indexed = {row["case_id"]: row for row in rows}
        if len(rows) != len(indexed) or set(indexed) != set(inputs):
            raise ValueError("Missing, duplicate or unexpected label case")
        identities = {row["reviewer_id"] for row in rows}
        if len(identities) != 1 or not next(iter(identities)).strip():
            raise ValueError("Each label pass requires one identified reviewer")
        for row in rows:
            if row["input_sha256"] != input_hash:
                raise ValueError("Label pass input hash mismatch")
            parse_labels(row, label_field, allowed)
        passes.append(indexed)
        reviewers.append(next(iter(identities)))
    if len(set(reviewers)) != 2:
        raise ValueError("Independent label reviewer identities must differ")
    decisions_path = OUTPUT / f"parent_{kind}_decisions.json"
    decisions = {}
    if decisions_path.is_file():
        document = read_json(decisions_path)
        if document["input_sha256"] != input_hash:
            raise ValueError("Label adjudication input mismatch")
        for row in document["decisions"]:
            if row["case_id"] in decisions or row["case_id"] not in inputs:
                raise ValueError("Duplicate or unexpected label adjudication")
            parse_labels(row, label_field, allowed)
            decisions[row["case_id"]] = row
    conflicts = []
    consensus = []
    unresolved = 0
    for identifier in sorted(inputs):
        first, second = [review[identifier] for review in passes]
        equal = parse_labels(first, label_field, allowed) == parse_labels(second, label_field, allowed)
        if not equal:
            conflicts.append({"case_id": identifier, "labels_a": first[label_field], "labels_b": second[label_field],
                              "reason_a": first["rationale"], "reason_b": second["rationale"],
                              **{field: value for field, value in inputs[identifier].items() if field != "case_id"}, "input_sha256": input_hash})
        selected = first if equal else decisions.get(identifier)
        unresolved += selected is None
        consensus.append({"case_id": identifier, label_field: "|".join(sorted(parse_labels(selected, label_field, allowed))) if selected else "",
                          "decision": selected["decision"] if selected else "UNRESOLVED",
                          "rationale": selected["rationale"] if selected else "",
                          "judgment_status": "AI_SILVER_AGREED" if equal else "AI_SILVER_ADJUDICATED" if selected else "UNRESOLVED",
                          "reviewer_id": selected["reviewer_id"] if selected else "", "input_sha256": input_hash, "human_gold": False})
    conflict_keys = {row["case_id"] for row in conflicts}
    if not set(decisions) <= conflict_keys:
        raise ValueError("Adjudication must only resolve genuine independent differences")
    fields = ["case_id", "labels_a", "labels_b", "reason_a", "reason_b", *[field for field in next(iter(inputs.values())) if field != "case_id"], "input_sha256"]
    write_csv(OUTPUT / f"{kind}_disagreements.csv", conflicts, fields)
    write_csv(OUTPUT / f"{kind}_consensus.csv", consensus, list(consensus[0]))
    report = {"kind": kind, "cases": len(inputs), "reviewers": reviewers, "input_sha256": input_hash,
              "exact_set_agreement": (len(inputs) - len(conflicts)) / len(inputs), "disagreements": len(conflicts),
              "unresolved": unresolved, "labelled_cases": sum(row["decision"] == "LABEL" for row in consensus),
              "abstentions": sum(row["decision"] == "ABSTAIN" for row in consensus), "human_gold": False,
              "consensus_sha256": digest(OUTPUT / f"{kind}_consensus.csv"), "taxonomy_sha256": digest(taxonomy_path),
              "raw_pass_sha256": {f"{kind}_pass_{number}.csv": digest(OUTPUT / f"{kind}_pass_{number}.csv") for number in (1, 2)}}
    write_json(OUTPUT / f"{kind}_agreement.json", report)
    return report


def main():
    results = [compare_labels(kind) for kind in ("factor", "strategy")]
    print(json.dumps(results, ensure_ascii=False, indent=2))
    if all(result.get("unresolved") == 0 for result in results):
        cases = read_json(OUTPUT / "source_supported_candidates.json")["cases"]
        write_json(OUTPUT / "factor_strategy_adjudication.json", {
            "input_fingerprint": fingerprint(cases), "approved": True, "reviewer_id": "PARENT_AI_EVIDENCE_ADJUDICATOR",
            "rationale": "Two independent Problem-only factor and implementation/outcome-only strategy passes; all label-set differences explicitly adjudicated. ABSTAIN is retained, not a fabricated negative or label. AI-Silver only.",
            "human_gold": False, "researcher_approval": False,
            "consensus_sha256": {kind + "_consensus.csv": digest(OUTPUT / f"{kind}_consensus.csv") for kind in ("factor", "strategy")},
            "results": results})


if __name__ == "__main__":
    main()
