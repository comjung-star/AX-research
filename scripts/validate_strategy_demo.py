import json
import sys
import urllib.request
from urllib.error import HTTPError
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[1]
    base = "http://127.0.0.1:8765"
    with urllib.request.urlopen(base + "/api/bootstrap", timeout=10) as response:
        bootstrap = json.load(response)
    query = next(item["query"] for item in bootstrap["examples"] if item["query_id"] == "V21D004")
    request = urllib.request.Request(base + "/api/recommend", data=json.dumps({"query": query, "mode": "live", "top_k": 3}).encode("utf-8"),
                                     headers={"Content-Type": "application/json", "X-AX-Token": bootstrap["token"]})
    with urllib.request.urlopen(request, timeout=240) as response:
        result = json.load(response)
    report = result["strategy_report"]
    output = root / "docs/prototype-validation"
    (output / "strategy-demo-result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    assert result["provider"] == "live_llm_dense"
    if report["provider"] != "live_llm":
        print(f"Strategy synthesis fallback: {report.get('generation_error_code', 'unknown')}", file=sys.stderr)
        raise AssertionError("Live strategy synthesis did not complete; fallback must not be claimed as live")
    for branch in result["branches"]:
        cards = {card["case_id"]: card for card in branch["cases"]}
        for strategy in branch["recommendation"]["strategies"]:
            assert strategy["actions"] and strategy["prerequisites"] and strategy["limitations"]
            assert set(strategy["supporting_case_ids"]) <= set(cards)
            assert all(strategy["strategy_id"] in [item["id"] for item in cards[case_id]["strategies"]] for case_id in strategy["supporting_case_ids"])
    lines = ["# 우리 업무의 AX 적용 전략", "", f"업무문제: {query}", "", report["summary"], "", "## 먼저 해볼 일", "", report["next_step"], ""]
    for branch in result["branches"]:
        lines.extend([f"## {branch['id']}. {branch['title']}", "", branch["description"], ""])
        for strategy in branch["recommendation"]["strategies"]:
            lines.extend([f"### {strategy['title']} · {strategy['priority']}", "", strategy["explanation"], "", "실행 순서:"])
            lines.extend(f"{index}. {action}" for index, action in enumerate(strategy["actions"], 1))
            lines.extend(["", "준비할 것:", *[f"- {item}" for item in strategy["prerequisites"]], "", "확인할 점:", *[f"- {item}" for item in strategy["limitations"]], "", f"근거: {strategy['evidence_reason']}", ""])
        lines.extend(["### 참고 기업의 실제 해결 방식", ""])
        for card in branch["cases"]:
            lines.extend([f"**{card['organization']} · {card['task']}**", "", card["solution"], "", f"원문 보고 성과: {card['outcome']}", "", f"출처: {card['source_url']}", ""])
    lines.extend(["## 작성 범위", "", report["notice"], "", "사용자에게 제안한 실행 순서는 실제 기업의 확정된 절차와 구분해야 합니다. 학습형 Evidence Fusion이나 Wald 통계 분석의 검증 결과가 아닙니다."])
    (output / "strategy-demo-report.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"case_provider": result["provider"], "strategy_provider": report["provider"], "perspectives": len(result["branches"]),
                      "strategies": report["strategy_count"], "evidence_cases": report["evidence_case_count"],
                      "elapsed_seconds": result["elapsed_seconds"], "summary": report["summary"]}, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except HTTPError as error:
        print(f"Strategy demo verification failed: HTTP {error.code}", file=sys.stderr)
        print(error.read(2000).decode("utf-8", errors="replace"), file=sys.stderr)
        sys.exit(1)
    except Exception as error:
        print(f"Strategy demo verification failed: {type(error).__name__}", file=sys.stderr)
        sys.exit(1)
