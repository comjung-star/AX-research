import csv
import hashlib
import json
import tempfile
from collections import Counter
from pathlib import Path

import numpy as np

from prototype.core import Engine, ROOT
from prototype.storage import FeedbackStore
from scripts.build_ax_expansion_release import EXPECTED_FROZEN_HASH, FROZEN, digest, read_json, write_json
from scripts.build_ax_inclusive_release import RELEASE
from scripts.review_all_ax_sources import all_inputs


QUERIES = [
    ("public_work", "시청으로 들어오는 반복 민원과 행정 절차 문의가 많아 담당자가 매번 같은 설명을 해야 합니다."),
    ("public_work", "공공기관에서 조달 계약서와 송장 서류를 사람이 검토하고 입력하느라 처리가 늦습니다."),
    ("education_research", "대학교 학생들의 수업과 학사 제도 질문에 반복해서 답변하느라 지원 담당자의 시간이 많이 듭니다."),
    ("consumer_personal", "개인이 언어를 공부하면서 실시간 대화 연습과 피드백을 받고 싶습니다."),
    ("all", "많은 문서와 영상에서 필요한 정보를 찾아 정리하는 데 시간이 오래 걸립니다.")
]


def main():
    import torch
    torch.set_num_threads(8)
    manifest = read_json(RELEASE / "release_manifest.json")
    for filename, expected in manifest["sha256"].items():
        assert digest(RELEASE / filename) == expected, filename
    for filename, expected in manifest["source_snapshots_sha256"].items():
        assert digest(ROOT / filename) == expected, filename
    inputs = all_inputs()
    corpus = read_json(RELEASE / "main_cases_v2_5.json")
    identifiers = {record["candidate_id"] for record in inputs}
    included = {case["candidate_id"] for case in corpus["cases"][108:]}
    assert included == identifiers
    assert len(corpus["cases"]) == len(inputs) + 108
    assert corpus["cases"][:84] == read_json(FROZEN)["cases"]
    assert digest(FROZEN) == EXPECTED_FROZEN_HASH
    coverage = list(csv.DictReader((RELEASE / "all_input_coverage.csv").open(encoding="utf-8-sig")))
    assert len(coverage) == len(inputs) and all(row["included_in_dataset"] == "True" and row["scope_exclusion"] == "False" for row in coverage)
    engine = Engine(profile="inclusive")
    expected = {case_id for case_id, case in engine.cases.items() if case.get("retrieval_eligible", True)}
    assert set(engine.case_ids) == expected
    assert all(case["human_ground_truth_approved"] is False for case in corpus["cases"])
    reports = []
    for scope, query in QUERIES:
        result = engine.recommend({"query": query, "mode": "demo", "top_k": 3, "business_scope": scope})
        assert result["provider"] == "local_dense"
        assert all(engine._matches_scope(card["case_id"], scope) for branch in result["branches"] for card in branch["cases"]) if scope != "all" else True
        assert all(card["case_id"] in expected for branch in result["branches"] for card in branch["cases"])
        reports.append({"business_scope": scope, "query": query, "provider": result["provider"],
                        "candidate_counts": [branch["candidate_count"] for branch in result["branches"]],
                        "results": [{"case_id": card["case_id"], "title": card["task"], "scope": card["business_scope"],
                                     "stage": card["deployment_stage_label"], "record_kind": card["record_kind"], "source_url": card["source_url"]}
                                    for branch in result["branches"] for card in branch["cases"]],
                        "strategy_count": result["strategy_report"]["strategy_count"]})
        print("Actual local Dense checked:", scope, flush=True)
    example = engine.recommend({"query": engine.examples[0]["query"], "mode": "demo"})
    with tempfile.TemporaryDirectory() as directory:
        store = FeedbackStore(Path(directory) / "inclusive-test.sqlite3")
        store.save(example, {"consent": True, "perspective_id": "", "case_id": "", "rating": "overall", "comment": "통합 버전 자동 검증", "tester": "automated-validation"})
        exported = json.loads(store.export("json"))
        assert exported["sessions"][0]["corpus_version"] == engine.corpus_version
        assert engine.corpus_version in store.export("csv").decode("utf-8-sig")
    result = {"dataset_release": engine.corpus_version, "input_registry_records_checked": len(inputs),
              "verification_method": "PROGRAMMATIC_MEMBERSHIP_HASH_SCHEMA_AND_LOCAL_DENSE_SMOKE_NOT_INDIVIDUAL_FACT_REVIEW",
              "new_independent_fact_verifications": 0,
              "all_collected_input_ids_included": True, "scope_exclusions": 0, "total_records": len(engine.cases),
              "retrievable_records": len(engine.case_ids), "frozen_preserved": True, "manifest_hashes_verified": len(manifest["sha256"]),
              "free_input_checks": reports, "feedback_version_export_verified": True, "paid_api_calls": 0,
              "not_a_relevance_or_fact_accuracy_benchmark": True}
    output = ROOT / "docs/prototype-validation/inclusive-validation.json"
    write_json(output, result)
    print(json.dumps({key: value for key, value in result.items() if key != "free_input_checks"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
