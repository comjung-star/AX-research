import argparse
import csv
import hashlib
import json
import math
import os
import shutil
import statistics
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "data/v2_5/research"
BASE = "58047e14625825413e97d7cd2d1b1ffcd54d82cb"
PROTECTED = ("data/", "collections/", "experiments/", "configs/", "src/", "prototype/", "scripts/")
KEY_NAMES = (
    "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY",
    "AZURE_OPENAI_API_KEY", "DEEPSEEK_API_KEY", "OPENROUTER_API_KEY",
)


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def digest(path):
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path, rows):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def measure_ranking(ranking, positives_by_reference, strategies, top_k):
    if top_k < 1 or len(ranking) < top_k or len(set(ranking)) != len(ranking):
        raise ValueError("Ranking must have unique IDs and at least K entries")
    selected = set(ranking[:top_k])
    relevant = set().union(*positives_by_reference.values())
    active = [values for values in positives_by_reference.values() if values]
    hits = len(selected & relevant)
    precision = hits / top_k
    recall = hits / len(relevant) if relevant else None
    f1 = 2 * precision * recall / (precision + recall) if recall is not None and hits else (0.0 if relevant else None)
    target_strategies = {label for case_id in relevant for label in strategies[case_id]}
    retrieved_strategies = {label for case_id in selected for label in strategies[case_id]}
    return {
        "k": top_k, "retrieved_count": len(selected), "hit_count": hits,
        "relevant_count": len(relevant), "precision": precision, "recall": recall, "f1": f1,
        "covered_reference_count": sum(bool(selected & values) for values in active),
        "answerable_reference_count": len(active), "all_reference_count": len(positives_by_reference),
        "perspective_coverage": sum(bool(selected & values) for values in active) / len(active) if active else None,
        "strategy_reference_count": len(target_strategies),
        "strategy_coverage": len(retrieved_strategies & target_strategies) / len(target_strategies) if target_strategies else None,
    }


def audit_historical_retrieval():
    cases = read_json(ROOT / "data/v2_3/main_cases_v2_3.json")["cases"]
    strategies = {case["case_id"]: case["strategy_labels"] for case in cases}
    silver = read_csv(ROOT / "data/v2_3/ground_truth/silver_dev_qrels_2520.csv")
    positive = defaultdict(lambda: defaultdict(set))
    for row in silver:
        values = positive[row["query_id"]][row["perspective_id"]]
        if int(row["relevance_0_4"]) >= 3:
            values.add(row["case_id"])
    diagnostics = []
    summaries = []
    metric_checks = 0
    for stage in (1, 2):
        folder = ROOT / f"experiments/v23_dev/stage{stage}"
        groups = defaultdict(list)
        for row in read_csv(folder / "rankings_top20.csv"):
            groups[(row["system"], row["query_id"], row["run_id"])].append(row)
        stored = {
            (row["system"], row["query_id"], row["run_id"], int(row["k"])): row
            for row in read_csv(folder / "metrics_by_query.csv")
        }
        computed = {}
        for (system, query_id, run_id), rows in sorted(groups.items()):
            ordered = sorted(rows, key=lambda row: int(row["rank"]))
            if [int(row["rank"]) for row in ordered] != list(range(1, 21)):
                raise ValueError("Historical ranking positions are incomplete")
            for top_k in (5, 10, 20):
                measured = measure_ranking([row["case_id"] for row in ordered], positive[query_id], strategies, top_k)
                key = (system, query_id, run_id, top_k)
                for metric in ("recall", "perspective_coverage", "strategy_coverage"):
                    if abs(measured[metric] - float(stored[key][metric])) > 1e-12:
                        raise ValueError(f"Historical metric mismatch: {stage}/{key}/{metric}")
                    metric_checks += 1
                item = {"historical_stage": stage, "system": system, "query_id": query_id, "run_id": run_id,
                        **measured, "label_basis": "OLD_SAME_MODEL_AI_SILVER_DEV_ONLY",
                        "precision_f1_status": "POSTHOC_AUDIT_NOT_NEW_STAGE_RESULT"}
                diagnostics.append(item)
                computed[key] = item
        if set(computed) != set(stored):
            raise ValueError("Historical metric keys mismatch")
        for summary in read_csv(folder / "summary.csv"):
            items = [item for key, item in computed.items() if key[0] == summary["system"] and key[3] == int(summary["k"])]
            for metric in ("recall", "perspective_coverage", "strategy_coverage"):
                mean = statistics.mean(item[metric] for item in items)
                if abs(mean - float(summary[metric + "_mean"])) > 0.000051:
                    raise ValueError("Historical summary differs from raw rankings")
            summaries.append({"historical_stage": stage, **summary})
    return diagnostics, summaries, metric_checks


def audit_old_labels():
    silver = read_csv(ROOT / "data/v2_3/ground_truth/silver_dev_qrels_2520.csv")
    runtime = read_csv(ROOT / "experiments/v23_runtime_perspective_qrels/runtime_qrels_8148.csv")
    exact = sum(len({row["score_pass1"], row["score_pass2"], row["score_pass3"]}) == 1 for row in silver)
    flips = sum(len({int(row[field]) >= 3 for field in ("score_pass1", "score_pass2", "score_pass3")}) > 1 for row in silver)
    return {
        "reference_pairs": len(silver), "reference_scores": 3 * len(silver),
        "reference_judge_models": sorted({row["judge_model"] for row in silver}),
        "reference_exact_agreement_numerator": exact, "reference_agreement_denominator": len(silver),
        "reference_exact_agreement": exact / len(silver), "reference_threshold_flips": flips,
        "reference_human_approved": sum(row["human_approved"].lower() == "true" for row in silver),
        "runtime_pairs": len(runtime), "runtime_scores": 2 * len(runtime),
        "runtime_judge_models": sorted({row[field] for row in runtime for field in ("judge_model_pass1", "judge_model_pass2")}),
        "runtime_exact_agreement": sum(row["relevance_pass1"] == row["relevance_pass2"] for row in runtime),
        "runtime_threshold_flips": sum((int(row["relevance_pass1"]) >= 3) != (int(row["relevance_pass2"]) >= 3) for row in runtime),
        "status": "REPEATED_ONE_MODEL_NOT_THREE_DISTINCT_LLMS_NOT_HUMAN_GOLD",
    }


def audit_historical_evidence():
    cases = read_json(ROOT / "data/v2_3/main_cases_v2_3.json")["cases"]
    by_id = {case["case_id"]: case for case in cases}
    wald = read_csv(ROOT / "experiments/v23_dev/stage3/factor_strategy_wald_77_pairs.csv")
    for row in wald:
        cells = Counter((row["factor_id"] in case["factor_labels"], row["strategy_id"] in case["strategy_labels"]) for case in cases)
        for column, key in (("a_factor_and_strategy", (True, True)), ("b_factor_no_strategy", (True, False)),
                            ("c_no_factor_strategy", (False, True)), ("d_neither", (False, False))):
            if cells[key] != int(row[column]):
                raise ValueError("Historical Wald contingency count mismatch")
        eligible = min(cells.get(key, 0) for key in ((True, True), (True, False), (False, True), (False, False))) >= 5
        if eligible != (row["wald_eligible"].lower() == "true"):
            raise ValueError("Historical Wald eligibility mismatch")
    relevant = defaultdict(set)
    for row in read_csv(ROOT / "data/v2_3/ground_truth/silver_dev_qrels_2520.csv"):
        if int(row["relevance_0_4"]) >= 3:
            relevant[row["query_id"]].add(row["case_id"])
    truth = {query_id: {label for case_id in case_ids for label in by_id[case_id]["strategy_labels"]}
             for query_id, case_ids in relevant.items()}
    frequency = defaultdict(lambda: defaultdict(float))
    for row in read_csv(ROOT / "experiments/v23_dev/stage2/rankings_top20.csv"):
        if row["system"] == "stage2_4_same_pool_rrf" and int(row["rank"]) <= 10:
            for label in by_id[row["case_id"]]["strategy_labels"]:
                frequency[(row["query_id"], row["run_id"])][label] += 1 / math.log2(int(row["rank"]) + 1)
    if any(row["bh_q_all_pairs"] and float(row["bh_q_all_pairs"]) < 0.05 for row in wald):
        raise ValueError("Historical Fusion needs a different audit because significant Wald evidence exists")
    llm = {(row["query_id"], row["run_id"]): row["chosen_strategies"].split("|") if row["chosen_strategies"] else []
           for row in read_csv(ROOT / "experiments/v23_dev/stage4/final_strategy_recommendations.csv")}
    metrics = read_csv(ROOT / "experiments/v23_dev/stage4/strategy_metrics_by_query.csv")
    recomputed = []
    for row in metrics:
        key = (row["query_id"], row["run_id"])
        scores = frequency[key]
        predicted = llm[key] if row["system"] == "evidence_grounded_llm" else sorted(scores, key=lambda label: (-scores[label], label))[:3]
        expected = truth[row["query_id"]]
        hits = len(set(predicted) & expected)
        recall = hits / len(expected)
        precision = hits / len(set(predicted))
        if len(predicted) != int(row["recommended_count"]) or abs(recall - float(row["strategy_recall_at_3"])) > 1e-12 or abs(precision - float(row["strategy_precision_at_3"])) > 1e-12:
            raise ValueError("Historical recommendation metric mismatch")
        recomputed.append({"system": row["system"], "query_id": row["query_id"], "run_id": row["run_id"],
                           "hit_count": hits, "recommended_count": len(predicted), "reference_strategy_count": len(expected),
                           "recall": recall, "precision_actual_output_denominator": precision,
                           "precision_fixed_three_denominator_posthoc": hits / 3})
    for row in read_csv(ROOT / "experiments/v23_dev/stage4/summary.csv"):
        selected = [item for item in recomputed if item["system"] == row["system"]]
        if abs(statistics.mean(item["recall"] for item in selected) - float(row["strategy_recall_at_3_mean"])) > 1e-12 or abs(statistics.mean(item["precision_actual_output_denominator"] for item in selected) - float(row["strategy_precision_at_3_mean"])) > 1e-12:
            raise ValueError("Historical recommendation summary mismatch")
    return wald, recomputed


def probe_credentials(credential_root):
    report = {"process_key_presence": {name: bool(os.environ.get(name)) for name in KEY_NAMES},
              "dotenv_key_presence": {}, "network_access_tested": False, "paid_api_calls": 0,
              "verified_distinct_judgment_models": [], "scope": "Project dotenv, known environment names, project Windows credential, PATH and local models only"}
    if credential_root:
        dotenv_path = credential_root / ".env"
        if dotenv_path.is_file():
            for line in dotenv_path.read_text(encoding="utf-8-sig").splitlines():
                name, separator, value = line.partition("=")
                name = name.strip().removeprefix("export ")
                if separator and name in KEY_NAMES:
                    report["dotenv_key_presence"][name] = bool(value.strip().strip("\"'"))
        report["local_model_directories"] = sorted(path.name for path in (credential_root / ".local/models").glob("*") if path.is_dir())
    report["local_generator_executables"] = {name: shutil.which(name) is not None for name in ("ollama", "lms")}
    if os.name == "nt":
        import winreg
        for scope, hive, path in (
            ("user", winreg.HKEY_CURRENT_USER, "Environment"),
            ("machine", winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"),
        ):
            presence = {}
            try:
                with winreg.OpenKey(hive, path) as handle:
                    for name in KEY_NAMES:
                        try:
                            presence[name] = bool(winreg.QueryValueEx(handle, name)[0])
                        except FileNotFoundError:
                            presence[name] = False
            except OSError:
                presence["registry_read_failed"] = True
            report[scope + "_key_presence"] = presence
        from prototype.credentials import WindowsCredentialStore
        saved = WindowsCredentialStore().read()
        report["project_windows_openai_credential_present"] = bool(saved and saved.get("api_key"))
    return report


def verify_inputs():
    manifest = read_json(RESEARCH / "manifest.json")
    checks = {}
    for prefix, entries in ((ROOT, manifest["input_sha256"]), (RESEARCH, manifest["sha256"])):
        for relative, expected in entries.items():
            path = prefix / relative
            checks[path.relative_to(ROOT).as_posix()] = digest(path) == expected
    index = read_json(RESEARCH / "dev_index_manifest.json")
    checks["data/v2_5/research/dev_bge_m3_128.npz"] = digest(RESEARCH / "dev_bge_m3_128.npz") == index["index_sha256"]
    if not all(checks.values()):
        raise ValueError("Inherited input SHA-256 mismatch: " + ", ".join(name for name, valid in checks.items() if not valid))
    return checks


def audit_dev_inputs():
    cases = read_csv(RESEARCH / "dev_problem_views.csv")
    queries = read_json(RESEARCH / "dev_queries.json")["queries"]
    qrels = read_csv(RESEARCH / "dev_qrels_annotation.csv")
    splits = read_csv(RESEARCH / "split_groups.csv")
    links = read_csv(RESEARCH / "leakage_links.csv")
    case_ids = {row["case_id"] for row in cases}
    query_ids = {row["query_id"] for row in queries}
    references = {(row["query_id"], row["perspective_id"]) for row in qrels}
    expected = {(query_id, perspective_id, case_id) for query_id, perspective_id in references for case_id in case_ids}
    observed = {(row["query_id"], row["perspective_id"], row["case_id"]) for row in qrels}
    if observed != expected or len(observed) != len(qrels) or {key[0] for key in references} != query_ids:
        raise ValueError("Dev annotation Cartesian product is incomplete or duplicated")
    partition = {row["case_id"]: row["partition"] for row in splits}
    cross_links = sum(partition[row["case_id"]] != partition[row["linked_case_id"]] for row in links)
    if cross_links or any(partition[case_id] != "DEV_ONLY" for case_id in case_ids):
        raise ValueError("Dev data crosses known reservation boundary")
    judged = sum(row["relevance_0_4"] != "" for row in qrels)
    if any(row["judgment_status"] != "UNJUDGED" for row in qrels):
        raise ValueError("Annotation state changed: reassess the stop gate")
    return {
        "cases": len(cases), "original_queries": len(queries), "reference_perspectives": len(references),
        "annotation_pairs": len(qrels), "judged_pairs": judged, "unjudged_pairs": len(qrels) - judged,
        "query_case_pairs_required_by_new_protocol": len(cases) * len(queries),
        "three_llm_reference_ratings_required": 3 * len(qrels),
        "three_llm_total_ratings_with_independent_query_case_labels": 3 * (len(qrels) + len(cases) * len(queries)),
        "known_leakage_links": len(links), "known_cross_partition_links": cross_links,
        "partition_counts": dict(Counter(partition.values())),
        "source_verification_status": "INHERITED_SOURCE_SUPPORTED_DEV_NOT_FULL_INDEPENDENT_FACT_VERIFICATION",
        "semantic_near_duplicate_review": "PENDING", "approved_reference_perspectives": 0,
        "human_validation_this_run": 0, "heldout_test_created_or_executed": False,
    }


def protected_snapshot():
    filenames = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", BASE], cwd=ROOT, text=True, encoding="utf-8").splitlines()
    return {name: digest(ROOT / name) for name in filenames if name.startswith(PROTECTED)}


def gate_blockers(config, dev, access):
    reasons = []
    if len(set(access["verified_distinct_judgment_models"])) < config["minimum_distinct_llms"]:
        reasons.append("THREE_DISTINCT_LLMS_NOT_CONFIGURED_OR_VERIFIED")
    if dev["judged_pairs"] != dev["annotation_pairs"]:
        reasons.append("NEW_RELEVANCE_LABELS_UNJUDGED_NO_APPROVED_QRELS")
    if dev["approved_reference_perspectives"] != dev["reference_perspectives"]:
        reasons.append("REFERENCE_PERSPECTIVES_ARE_UNVALIDATED_DRAFTS")
    if dev["semantic_near_duplicate_review"] != "COMPLETE":
        reasons.append("SEMANTIC_DUPLICATE_AND_SOURCE_SCOPE_REVIEW_PENDING")
    return reasons


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "docs/reduced-stage123-2026-10-26/evidence")
    parser.add_argument("--credential-root", type=Path)
    parser.add_argument("--verify-snapshot", type=Path)
    args = parser.parse_args(argv)
    args.output.mkdir(parents=True, exist_ok=True)
    initial = protected_snapshot()
    if args.verify_snapshot and initial != read_json(args.verify_snapshot):
        raise ValueError("Protected inherited bytes changed since the first audit")
    write_json(args.output / "protected_inputs_sha256.json", initial)
    input_checks = verify_inputs()
    historical, summary, count = audit_historical_retrieval()
    write_csv(args.output / "historical_ranking_metrics_recomputed.csv", historical)
    write_json(args.output / "historical_summary_checked.json", summary)
    config = read_json(ROOT / "configs/reduced_stage123_20261026.json")
    dev = audit_dev_inputs()
    access = probe_credentials(args.credential_root)
    blockers = gate_blockers(config, dev, access)
    wald, recommendations = audit_historical_evidence()
    write_csv(args.output / "historical_strategy_metrics_recomputed.csv", recommendations)
    stage4_counts = {
        system: dict(Counter(int(row["recommended_count"]) for row in recommendations if row["system"] == system))
        for system in sorted({row["system"] for row in recommendations})
    }
    report = {
        "status": "BLOCKED_BEFORE_NEW_STAGE1_JUDGMENTS" if blockers else "AUDIT_ONLY_REQUIRES_LABEL_RELEASE_CHECK",
        "local_time": datetime.now(ZoneInfo("Asia/Seoul")).isoformat(), "base_commit": BASE,
        "branch": subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip(),
        "protocol_sha256": digest(ROOT / "configs/reduced_stage123_20261026.json"),
        "input_sha256_checks": input_checks, "old_labels": audit_old_labels(),
        "historical_metric_values_recomputed_and_matched": count, "historical_metric_rows": len(historical),
        "historical_stage3": {"wald_pairs": len(wald), "contingency_cell_counts_recomputed": 4 * len(wald), "eligible_pairs": sum(row["wald_eligible"].lower() == "true" for row in wald),
                              "bh_significant_pairs": sum(bool(row["bh_q_all_pairs"]) and float(row["bh_q_all_pairs"]) < 0.05 for row in wald)},
        "historical_stage4": {"recommended_count_histograms": stage4_counts,
                              "metric_rows_recomputed_and_matched": len(recommendations),
                              "llm_fixed_three_precision_posthoc": statistics.mean(row["precision_fixed_three_denominator_posthoc"] for row in recommendations if row["system"] == "evidence_grounded_llm"),
                              "precision_denominator": "ACTUAL_RECOMMENDED_COUNT_NOT_FIXED_3", "new_execution": False},
        "dev": dev, "access": access, "blockers": blockers,
        "new_stage_status": {"stage1": "INPUT_AUDIT_DONE_JUDGMENTS_BLOCKED", "stage2": "NOT_EXECUTED_STAGE1_GATE", "stage3": "NOT_EXECUTED_STAGE1_GATE", "stage4": "SEALED_NOT_CREATED_NOT_EXECUTED"},
        "new_effectiveness_metrics": None, "new_llm_agreement_metrics": None,
        "paid_api_calls": 0, "generated_labels": 0,
        "protected_inherited_files": len(initial), "protected_bytes_unchanged_after_audit": initial == protected_snapshot(),
        "python": sys.version, "limitations": ["Credentials present is not API permission or model availability verification", "No account-wide credential search; additional access may exist outside checked project configuration", "Hash and schema checks are not source fact verification", "Historical metric reproduction does not make old labels independent", "New Stage 1-3 were not completed"],
    }
    if not report["protected_bytes_unchanged_after_audit"]:
        raise ValueError("Audit modified a protected input")
    write_json(args.output / "audit_report.json", report)
    write_json(args.output / "failure_log.json", {"expected_exit_code": 2 if blockers else 0,
               "reason": blockers, "api_request_attempts": 0, "api_errors": [], "model_substitutions": [],
               "stopped_at": "NEW_STAGE1_INDEPENDENT_LABELING_PREREQUISITES", "stage2_stage3_attempts": 0})
    print(json.dumps({"status": report["status"], "metric_checks": count, "dev": dev,
                      "blockers": blockers, "paid_api_calls": 0}, ensure_ascii=False, indent=2))
    return 2 if blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
