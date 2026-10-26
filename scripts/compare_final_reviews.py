import argparse
import json
from collections import Counter

from scripts.audit_final_dataset import OUTPUT, audit_judgment_pass, fingerprint, load_csv
from scripts.build_ax_expansion_release import read_json, write_json
from scripts.prepare_v25_research import write_csv


def agreement_statistics(pairs):
    matrix = [[0] * 5 for _ in range(5)]
    for first, second in pairs:
        matrix[first][second] += 1
    count = len(pairs)
    if not count:
        raise ValueError("Agreement requires actual judgments")
    row_counts = [sum(row) for row in matrix]
    column_counts = [sum(matrix[row][column] for row in range(5)) for column in range(5)]
    observed = sum(matrix[grade][grade] for grade in range(5)) / count
    expected = sum(row_counts[grade] * column_counts[grade] for grade in range(5)) / count ** 2
    observed_disagreement = sum(matrix[first][second] * abs(first - second) / 4 for first in range(5) for second in range(5)) / count
    expected_disagreement = sum(row_counts[first] * column_counts[second] * abs(first - second) / 4 for first in range(5) for second in range(5)) / count ** 2
    positive_a = sum(first >= 3 for first, _ in pairs)
    positive_b = sum(second >= 3 for _, second in pairs)
    both_positive = sum(first >= 3 and second >= 3 for first, second in pairs)
    both_negative = sum(first < 3 and second < 3 for first, second in pairs)
    binary_observed = (both_positive + both_negative) / count
    binary_expected = (positive_a * positive_b + (count - positive_a) * (count - positive_b)) / count ** 2
    return {"pair_count": count, "exact_agreement": observed, "cohen_kappa": (observed - expected) / (1 - expected) if expected < 1 else None,
            "linear_weighted_kappa": 1 - observed_disagreement / expected_disagreement if expected_disagreement else None,
            "threshold_agreement": binary_observed,
            "binary_kappa": (binary_observed - binary_expected) / (1 - binary_expected) if binary_expected < 1 else None,
            "positive_agreement": 2 * both_positive / (positive_a + positive_b) if positive_a + positive_b else None,
            "negative_agreement": 2 * both_negative / (2 * count - positive_a - positive_b) if 2 * count - positive_a - positive_b else None,
            "threshold_flip_count": sum((first >= 3) != (second >= 3) for first, second in pairs), "grade_confusion_matrix": matrix}


def compare(split):
    prefix = "test_" if split == "test" else ""
    input_path = OUTPUT / ("blind_test_relevance_input.json" if split == "test" else "blind_relevance_input.json")
    document = read_json(input_path)
    input_hash = fingerprint(document)
    cases = {case["case_id"]: case for case in document["cases"]}
    questions = {query["query_id"]: query for query in document["queries"]}
    expected = {(query["query_id"], perspective["id"], case_id) for query in questions.values() for perspective in query["reference_perspectives"] for case_id in cases}
    results = []
    for number in (1, 2):
        path = OUTPUT / f"{prefix}relevance_pass_{number}.csv"
        if not path.is_file():
            return {"status": "WAITING_FOR_INDEPENDENT_PASSES", "split": split, "missing_file": path.name}
        rows = load_csv(path)
        if len(rows) != len(expected):
            return {"status": "INCOMPLETE_PASS_NOT_ACCEPTED", "split": split, "file": path.name, "actual_rows": len(rows), "required_rows": len(expected)}
        if any(row["input_sha256"] != input_hash for row in rows):
            raise ValueError("Review does not match the sealed input: " + path.name)
        results.append(audit_judgment_pass(rows, expected))
    first, second = results
    if first[1] == second[1]:
        raise ValueError("Two distinct reviewer identities are required")
    decisions_path = OUTPUT / f"{prefix}relevance_adjudication_decisions.csv"
    decisions = {}
    if decisions_path.is_file():
        for row in load_csv(decisions_path):
            key = (row["query_id"], row["perspective_id"], row["case_id"])
            if key in decisions or key not in expected or row["input_sha256"] != input_hash:
                raise ValueError("Adjudication identity, input or duplicate mismatch")
            if str(row["relevance_0_4"]) not in {"0", "1", "2", "3", "4"} or not row["rationale"].strip():
                raise ValueError("Adjudication requires an explicit grade and reason")
            decisions[key] = row
    discrepancies = []
    qrels = []
    score_pairs = []
    for key in sorted(expected):
        row_a, row_b = first[0][key], second[0][key]
        grade_a, grade_b = int(row_a["relevance_0_4"]), int(row_b["relevance_0_4"])
        score_pairs.append((grade_a, grade_b))
        query_id, perspective_id, case_id = key
        query = questions[query_id]
        perspective = next(row for row in query["reference_perspectives"] if row["id"] == perspective_id)
        if grade_a != grade_b:
            discrepancies.append({"query_id": query_id, "perspective_id": perspective_id, "case_id": case_id,
                                  "grade_a": grade_a, "grade_b": grade_b, "reason_a": row_a["rationale"], "reason_b": row_b["rationale"],
                                  "query": query["query"], "reference": perspective["title"], **{field: cases[case_id][field] for field in ("problem", "task", "context")},
                                  "input_sha256": input_hash})
        decision = decisions.get(key)
        score = grade_a if grade_a == grade_b else int(decision["relevance_0_4"]) if decision else ""
        reason = decision["rationale"] if decision else row_a["rationale"] + " / " + row_b["rationale"] if grade_a == grade_b else ""
        qrels.append({"query_id": query_id, "perspective_id": perspective_id, "case_id": case_id, "relevance_0_4": score,
                      "positive_ge3": int(score >= 3) if isinstance(score, int) else "", "grade_a": grade_a, "grade_b": grade_b,
                      "judgment_status": "AI_SILVER_AGREED" if grade_a == grade_b else "AI_SILVER_ADJUDICATED" if decision else "DISAGREEMENT_UNRESOLVED",
                      "evidence_reason": reason, "input_sha256": input_hash, "human_approved": False})
    unresolved = sum(row["judgment_status"] == "DISAGREEMENT_UNRESOLVED" for row in qrels)
    fields = ["query_id", "perspective_id", "case_id", "grade_a", "grade_b", "reason_a", "reason_b", "query", "reference", "problem", "task", "context", "input_sha256"]
    write_csv(OUTPUT / f"{prefix}relevance_disagreements.csv", discrepancies, fields)
    write_csv(OUTPUT / f"{prefix}qrels_consensus.csv", qrels, list(qrels[0]))
    report = {"status": "AI_SILVER_COMPLETE_NOT_HUMAN_GOLD" if unresolved == 0 else "INDEPENDENT_PASSES_COMPLETE_ADJUDICATION_PENDING",
              "split": split, "input_sha256": input_hash, "judges": [first[1], second[1]],
              **agreement_statistics(score_pairs), "grade_disagreements": len(discrepancies), "unresolved_disagreements": unresolved,
              "adjudicated_disagreements": len(discrepancies) - unresolved,
              "score_histogram_a": dict(Counter(first_grade for first_grade, _ in score_pairs)),
              "score_histogram_b": dict(Counter(second_grade for _, second_grade in score_pairs)),
              "human_gold": False, "researcher_approval": False}
    write_json(OUTPUT / f"{prefix}review_agreement.json", report)
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=["dev", "test", "both"], default="both")
    arguments = parser.parse_args()
    for split in (["dev", "test"] if arguments.split == "both" else [arguments.split]):
        print(json.dumps(compare(split), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
