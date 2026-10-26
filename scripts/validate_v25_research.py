import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict

import requests

from scripts.build_ax_expansion_release import ROOT, digest, read_json, write_json
from scripts.prepare_v25_research import OUTPUT, verify_sources
from scripts.review_all_ax_sources import all_inputs
from scripts.run_v25_dev_baselines import RESULTS, verify_preparation


def load_csv(filename):
    with (OUTPUT / filename).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url")
    args = parser.parse_args()
    verified, protected = verify_sources()
    verify_preparation()
    dispositions = load_csv("dispositions.csv")
    splits = load_csv("split_groups.csv")
    links = load_csv("leakage_links.csv")
    qrels = load_csv("dev_qrels_annotation.csv")
    cases = read_json(OUTPUT / "dev_cases.json")["cases"]
    corpus = read_json(ROOT / "data/v2_5/main_cases_v2_5.json")
    source = corpus["cases"]
    source_by_id = {case["case_id"]: {**case, **corpus["inherited_case_metadata"].get(case["case_id"], {})} for case in source}
    source_ids = {case["case_id"] for case in source}
    reconstructed_inputs = all_inputs()
    for record in reconstructed_inputs:
        stored = source_by_id["AXALL_" + record["candidate_id"]]
        expected = hashlib.sha256(json.dumps(record, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
        assert stored["raw_collection_record_sha256"] == expected
    assert len(reconstructed_inputs) == 11658
    assert {row["case_id"] for row in dispositions} == source_ids
    assert len(dispositions) == len(source_ids) == 11766
    assert Counter(row["decision"] for row in dispositions) == read_json(OUTPUT / "readiness.json")["decision_counts"]
    assert {row["case_id"] for row in dispositions if row["decision"] == "EXPERIMENT_SUITABLE"} == {case["case_id"] for case in cases}
    assert all(row["original_record_preserved"] == "True" and json.loads(row["reason_codes"]) and json.loads(row["evidence_ids"]) for row in dispositions)
    with (OUTPUT / "evidence_catalog.jsonl").open(encoding="utf-8") as handle:
        evidence = {row["evidence_id"]: row for line in handle if (row := json.loads(line))}
    assert len(evidence) == len(source_ids)
    verified_evidence_files = {}
    for row in dispositions:
        checks = json.loads(row["field_checks"])
        assert checks["independent_fact_corroboration"] is False and checks["human_gold"] is False
        for evidence_id in json.loads(row["evidence_ids"]):
            item = evidence[evidence_id]
            assert item["case_id"] == row["case_id"]
            path = item["evidence_locator"].split("#")[0]
            if path not in verified_evidence_files:
                verified_evidence_files[path] = digest(ROOT / path)
            assert verified_evidence_files[path] == item["evidence_sha256"]
    partitions = {row["case_id"]: row["partition"] for row in splits}
    groups = defaultdict(set)
    for row in splits:
        groups[row["leakage_group_id"]].add(row["partition"])
    assert all(len(partitions) == 1 for partitions in groups.values())
    assert all(partitions[row["case_id"]] == partitions[row["linked_case_id"]] for row in links)
    assert all(partitions[case["case_id"]] == "DEV_ONLY" for case in cases)
    assert all(row["relevance_0_4"] == "" and row["judgment_status"] == "UNJUDGED" for row in qrels)
    assert len(qrels) == len({(row["query_id"], row["perspective_id"], row["case_id"]) for row in qrels}) == 3360
    with (OUTPUT / "dev_problem_views.csv").open(encoding="utf-8-sig", newline="") as handle:
        assert set(next(csv.reader(handle))) == {"case_id", "problem", "task", "context", "evidence_ids", "leakage_group_id"}
    run = read_json(RESULTS / "run_report.json")
    assert run["input_manifest_sha256"] == digest(OUTPUT / "manifest.json")
    assert run["index_manifest_sha256"] == digest(OUTPUT / "dev_index_manifest.json")
    for filename, expected in run["ranking_sha256"].items():
        assert digest(RESULTS / filename) == expected
    assert run["metrics"] is None and run["paid_api_calls"] == 0
    http_report = None
    if args.base_url:
        if not args.base_url.startswith("http://127.0.0.1:"):
            raise ValueError("Only the explicitly started local validation server is supported")
        health_response = requests.get(args.base_url + "/api/health", timeout=10)
        health_response.raise_for_status()
        health = health_response.json()
        assert health["cases"] == 9416 and health["records"] == 11766 and health["corpus_version"] == "2.5.0-inclusive"
        bootstrap_response = requests.get(args.base_url + "/api/bootstrap", timeout=10)
        bootstrap_response.raise_for_status()
        bootstrap = bootstrap_response.json()
        assert bootstrap["version"] == "2.5.0-inclusive"
        response = requests.post(args.base_url + "/api/recommend", timeout=120,
                                 headers={"X-AX-Token": bootstrap["token"], "Origin": args.base_url},
                                 json={"query": "시청의 반복 민원을 사람이 확인하고 분류하느라 응답이 지연됩니다.", "mode": "demo", "top_k": 3, "business_scope": "public_work", "include_strategy": True})
        response.raise_for_status()
        result = response.json()
        assert result["provider"] == "local_dense" and result["llm_evidence"] is None
        assert all("public_work" in source_by_id[card["case_id"]]["business_scope_tags"] for branch in result["branches"] for card in branch["cases"])
        assert all(card["case_id"] in source_ids for branch in result["branches"] for card in branch["cases"])
        http_report = {"base_url": args.base_url, "health": health, "bootstrap_version": bootstrap["version"],
                       "provider": result["provider"], "corpus_sha256": result["corpus_sha256"],
                       "candidate_counts": [branch["candidate_count"] for branch in result["branches"]],
                       "case_ids": [card["case_id"] for branch in result["branches"] for card in branch["cases"]],
                       "elapsed_seconds": result["elapsed_seconds"], "llm_called": False}
    result = {"status": "PASSED", "registry_membership": len(dispositions), "evidence_catalog_entries": len(evidence),
              "evidence_files_hashed": len(verified_evidence_files), "source_manifest_hashes": len(verified),
              "reconstructed_input_record_hashes_checked": len(reconstructed_inputs),
              "raw_structured_rows_reparsed_by_input_reconstruction": 5961,
              "clean_dev_records": len(cases), "unjudged_pairs_preserved": len(qrels),
              "known_leakage_links_checked": len(links), "known_cross_partition_links": 0,
              "clean_annotation_view_hides_solution_and_labels": True, "protected_paths_unchanged": protected,
              "baseline_ranking_hashes_verified": True, "v25_effectiveness_metrics_computed": False,
              "http": http_report, "paid_api_calls": 0}
    write_json(ROOT / "docs/prototype-validation/v25-research-validation.json", result)
    if http_report is not None:
        write_json(ROOT / "docs/prototype-validation/v25-http-validation.json", http_report)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
