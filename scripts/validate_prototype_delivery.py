import argparse
import hashlib
import json
import subprocess
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8765")
    parser.add_argument("--live", action="store_true", help="Run one real paid LLM-to-Dense end-to-end request using the already connected key")
    args = parser.parse_args()
    output = ROOT / "docs/prototype-validation"
    output.mkdir(parents=True, exist_ok=True)

    def get(path):
        with urllib.request.urlopen(args.url + path, timeout=10) as response:
            return json.load(response)

    bootstrap = get("/api/bootstrap")
    payload = {"query": "직원들이 흩어진 사내 규정과 매뉴얼을 찾느라 시간을 쓰고 있습니다. 그리고 긴 이메일에서 후속조치를 정리하기 어렵습니다.", "mode": "demo", "top_k": 3}
    request = urllib.request.Request(args.url + "/api/recommend", data=json.dumps(payload).encode("utf-8"),
                                     headers={"Content-Type": "application/json", "X-AX-Token": bootstrap["token"]})
    with urllib.request.urlopen(request, timeout=180) as response:
        result = json.load(response)
    assert result["provider"] == "local_dense" and len(result["branches"]) == 2
    assert result["branches"][0]["cases"][0]["case_id"] == "AXV2N_0110"
    assert result["branches"][1]["cases"][0]["case_id"] == "AXV2H_0002_01"
    (output / "custom-dense-result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    live_result = None
    if args.live:
        live_request = urllib.request.Request(args.url + "/api/recommend", data=json.dumps({**payload, "mode": "live"}).encode("utf-8"),
                                              headers={"Content-Type": "application/json", "X-AX-Token": bootstrap["token"]})
        with urllib.request.urlopen(live_request, timeout=180) as response:
            live_result = json.load(response)
        assert live_result["provider"] == "live_llm_dense" and live_result["llm_evidence"]["api_called"]
        assert 1 <= len(live_result["branches"]) <= 6
        (output / "live-api-result.json").write_text(json.dumps(live_result, ensure_ascii=False, indent=2), encoding="utf-8")
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    unchanged = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", "data", "experiments", "configs", "src"], cwd=ROOT).returncode == 0
    assert unchanged
    original_files = subprocess.check_output(["git", "ls-files", "-z", "data", "experiments", "configs", "src"], cwd=ROOT).split(b"\0")
    test_root = ET.parse(output / "tests.xml").getroot()
    suites = list(test_root.iter("testsuite"))
    test_counts = {field: sum(int(suite.get(field, "0")) for suite in suites) for field in ("tests", "failures", "errors", "skipped")}
    assert test_counts["tests"] >= 180 and test_counts["failures"] == test_counts["errors"] == 0
    frozen = ["data/v2_3/main_cases_v2_3.json", "data/v2_3/main_cases_v2_3.csv", "data/v2_3/release_manifest_v2_3.json",
              "experiments/v23_dev/stage1/fixed_bge_m3_embeddings.npz", "experiments/v23_dev/stage1/generated_runtime_perspectives.json",
              "experiments/v23_qci256_four_step/stage34_top10_rankings.csv"]
    launcher = ROOT / "dist/desktop/AX나침반.exe"
    assert launcher.read_bytes().startswith(b"MZ")
    strategy_path = output / "strategy-demo-result.json"
    strategy_result = json.loads(strategy_path.read_text(encoding="utf-8")) if strategy_path.exists() else {}
    strategy_report = strategy_result.get("strategy_report", {})
    strategy_verified = strategy_result.get("provider") == "live_llm_dense" and strategy_report.get("provider") == "live_llm" and strategy_report.get("api_evidence", {}).get("api_called") is True
    manifest = {"verified_at_kst": datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds"),
                "source_repository": "https://github.com/comjung-star/AX-research", "source_commit": revision,
                "research_files_unchanged": unchanged, "tracked_research_file_count": sum(bool(path) for path in original_files),
                "frozen_sha256": {path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in frozen},
                "tests": test_counts, "desktop_launcher_sha256": hashlib.sha256(launcher.read_bytes()).hexdigest(),
                "health": get("/api/health"), "local_model_ready": bootstrap["dense_model_ready"],
                "real_new_query_dense": {"provider": result["provider"], "perspective_count": len(result["branches"]),
                                         "elapsed_seconds": result["elapsed_seconds"], "top_case_ids": [branch["cases"][0]["case_id"] for branch in result["branches"]]},
                "live_llm_api_verified": bool(live_result) or strategy_verified or bool(bootstrap.get("connection", {}).get("verified")),
                "live_end_to_end_verified": live_result is not None or strategy_verified,
                "live_strategy_verified": strategy_verified,
                "live_strategy": {"provider": strategy_report.get("provider"), "evidence": strategy_report.get("api_evidence"), "result_path": str(strategy_path.relative_to(ROOT))},
                "live_llm_api_reason": "Real paid end-to-end call completed" if live_result else "Recorded live strategy run verified" if strategy_verified else "See connection status; end-to-end paid request was not run by this validation",
                "live_connection": bootstrap.get("connection", {}),
                "production_feedback_count": get("/api/bootstrap")["feedback"]["total"],
                "git_publication": "LOCAL_ONLY_NOT_COMMITTED_OR_PUSHED"}
    (output / "verification.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"tests": test_counts, "research_files_preserved": manifest["tracked_research_file_count"],
                      "new_query": manifest["real_new_query_dense"], "live_api_verified": manifest["live_llm_api_verified"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
