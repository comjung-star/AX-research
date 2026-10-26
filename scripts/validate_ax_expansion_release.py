import json
import subprocess

from prototype.core import Engine, ROOT
from scripts.build_ax_expansion_release import EXPECTED_FROZEN_HASH, FROZEN, RELEASE, digest, read_json, write_json


QUERIES = [
    "회사 뉴스와 공지의 영문 번역을 사람이 매번 작성해서 발행이 늦어집니다.",
    "보험 가입 서류마다 양식이 달라 담당자가 PDF를 읽고 필요한 항목을 엑셀로 옮깁니다.",
    "직원 설문 응답이 많아 공통 불만과 개선 의견을 정리하는 데 시간이 걸립니다.",
    "장비별 센서 기록이 따로 있어 원격으로 이상 상태를 빨리 파악하기 어렵습니다.",
    "고객이 영수증을 다시 보내 달라고 하면 직원이 숙박 기록을 찾아 이메일로 보내야 합니다.",
    "감사 자료를 잘못 낸 고객에게 반려 이유와 필요한 서류를 매번 다시 설명해야 합니다."
]


def main():
    import torch
    torch.set_num_threads(4)
    manifest = read_json(RELEASE / "release_manifest.json")
    for filename, expected in manifest["sha256"].items():
        if digest(RELEASE / filename) != expected:
            raise ValueError("Release file hash mismatch: " + filename)
    if digest(FROZEN) != EXPECTED_FROZEN_HASH:
        raise ValueError("Frozen baseline changed")
    git_manifest = read_json(ROOT / "data/v2_3/release_manifest_v2_3.json")
    for filename, expected in git_manifest["git_blob_sha"].items():
        actual = subprocess.check_output(["git", "hash-object", "--path=" + filename, filename], cwd=ROOT, text=True).strip()
        if actual != expected:
            raise ValueError("Frozen Git blob changed: " + filename)
    baseline = Engine()
    engine = Engine(profile="active")
    examples = []
    for example in engine.examples:
        result = engine.recommend({"query": example["query"], "top_k": 3})
        assert all(branch["candidate_count"] == len(engine.cases) for branch in result["branches"])
        examples.append({"query_id": example["query_id"], "branches": len(result["branches"]),
                         "strategy_provider": result["strategy_report"]["provider"], "corpus_version": result["corpus_version"]})
    checks = []
    for query in QUERIES:
        result = engine.recommend({"query": query, "top_k": 3})
        assert result["provider"] == "local_dense"
        branches = engine._local_branches(query)
        vectors = engine._encode(branches)
        reference = []
        for vector in vectors:
            scores = (baseline.views @ vector).mean(axis=0)
            indices = sorted(range(len(baseline.case_ids)), key=lambda offset: (-float(scores[offset]), baseline.case_ids[offset]))[:3]
            reference.append([baseline.case_ids[offset] for offset in indices])
        checks.append({"query": query, "provider": result["provider"], "baseline_top3_per_branch": reference,
                       "expanded_top3_per_branch": [[{"case_id": case["case_id"], "organization": case["organization"], "task": case["task"],
                                                     "source_url": case["source_url"]} for case in branch["cases"]] for branch in result["branches"]],
                       "strategy_count": result["strategy_report"]["strategy_count"]})
        print("Dense checked:", query, flush=True)
    output = ROOT / "docs/prototype-validation/expansion-validation.json"
    write_json(output, {"dataset_release": engine.corpus_version, "corpus_sha256": engine.corpus_hash, "case_count": len(engine.cases), "baseline_case_count": len(baseline.cases),
                       "baseline_sha256": digest(FROZEN), "frozen_git_blobs_verified": len(git_manifest["git_blob_sha"]),
                       "release_hashes_verified": len(manifest["sha256"]), "examples": examples, "free_input_smoke_checks": checks,
                       "new_cases_found_in_smoke_queries": len({case["case_id"] for check in checks for branch in check["expanded_top3_per_branch"] for case in branch if case["case_id"].startswith("AXV24_")}),
                       "paid_api_calls": 0, "is_relevance_benchmark": False,
                       "limitation": "Known-domain development smoke inputs; not held-out Test, human relevance evaluation, or evidence of Recall improvement."})
    print("Saved", output)


if __name__ == "__main__":
    main()
