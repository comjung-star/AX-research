"""DEV-only evaluation. Prediction receipt is verified before Silver is opened."""

import csv
import socket
import statistics
from collections import Counter, defaultdict

from scripts import semantic_mapping_run as run


def csvsave(name, rows):
    if not rows:
        return
    path = run.OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def metric(ranking, positive, count):
    assert len(ranking) == len(set(ranking)) == 112
    hits = len(set(ranking[:count]) & positive)
    return {"precision": hits / count, "recall": hits / len(positive) if positive else None,
            "f1": 2 * hits / (count + len(positive)) if positive else None,
            "true_positives": hits, "related_ids": sorted(set(ranking[:count]) & positive)}


def align(rows, qid, repeat):
    candidates = [row for row in rows if row["qid"] == qid]
    return next((row for row in candidates if row["repeat"] == repeat),
                next((row for row in candidates if row["repeat"] == 0), None))


def main():
    run.verify_freeze()
    receipt = run.read(run.OUT / "prediction_receipt.json")
    assert receipt["preregistration_sha256"] == run.digest(run.OUT / "preregistration.json")
    for name, expected in receipt["artifact_sha256"].items():
        assert run.digest(run.OUT / name) == expected, name
    label_path = run.ROOT / "docs/stage123-openai-triplicate-2026-10-27/stage1_silver.json"
    label_hash = run.digest(label_path)
    assert label_hash == run.read(label_path.parent / "silver_freeze.json")["sha256"]
    silver = run.read(label_path)
    grades = defaultdict(dict)
    positive = defaultdict(set)
    for row in silver["records"]:
        assert not row["held"] and row["silver_score"] is not None
        grades[row["qid"]][row["cid"]] = row["silver_score"]
        if row["silver_score"] >= 3:
            positive[row["qid"]].add(row["cid"])
    assert len(grades) == 10 and len(silver["records"]) == 1120 and sum(map(len, positive.values())) == 18
    historical = run.read(run.HIST / "stage4_dev/results.json")
    predictions = run.read(run.OUT / "ranking/rankings.json")["systems"]
    systems = {**historical["systems"], **predictions}
    cases = run.read(run.INPUT / "case_registry.json")["cases"]
    expected_ids = set(cases)
    results = {}
    macro = {}
    macro_rows = []
    query_rows = []
    for name, rows in systems.items():
        evaluated = []
        for row in rows:
            assert set(row["ranking"]) == expected_ids
            cells = {str(count): metric(row["ranking"], positive[row["qid"]], count) for count in run.CFG["K"]}
            if "metrics" in row:
                for count in run.CFG["K"]:
                    for field in ("precision", "recall", "f1"):
                        assert cells[str(count)][field] == row["metrics"][str(count)][field]
            evaluated.append({"qid": row["qid"], "repeat": row["repeat"], "ranking": row["ranking"], "metrics": cells})
        results[name] = evaluated
        macro[name] = {}
        for count in run.CFG["K"]:
            summary = {}
            for field, denominator in (("precision", 10), ("recall", 6), ("f1", 6)):
                grouped = defaultdict(list)
                for row in evaluated:
                    value = row["metrics"][str(count)][field]
                    if value is not None:
                        grouped[row["qid"]].append(value)
                assert len(grouped) == denominator
                summary[field] = statistics.mean(statistics.mean(values) for values in grouped.values())
                summary[field + "_question_denominator"] = denominator
                for qid, values in grouped.items():
                    query_rows.append({"system": name, "qid": qid, "k": count, "metric": field,
                                       "mean": statistics.mean(values), "repeats": len(values),
                                       "stdev": statistics.stdev(values) if len(values) > 1 else None})
            macro[name][str(count)] = summary
            macro_rows.append({"system": name, "k": count, **summary})
        if name in historical["macro"]:
            for count in run.CFG["K"]:
                for field in ("precision", "recall", "f1"):
                    assert macro[name][str(count)][field] == historical["macro"][name][str(count)][field]
    run.save("evaluation/results.json", {"systems": results, "macro": macro,
             "label_source": "EXISTING_SAME_MODEL_TRIPLICATE_MEDIAN_AI_SILVER_NOT_HUMAN_GOLD",
             "silver_sha256": label_hash, "positive_pairs": 18,
             "zero_positive_queries": sorted(qid for qid in grades if not positive[qid]),
             "independent_test": False})
    csvsave("evaluation/macro_metrics.csv", macro_rows)
    csvsave("evaluation/query_mean_metrics.csv", query_rows)
    changes = []
    rank_changes = []
    change_summary = []
    unknown_ids = set(run.read(run.OUT / "mapping/unknown33.json")["case_ids"])
    for suffix, hybrid in (("O_SINGLE", "H_C"), ("D_SINGLE", "H_F"), ("O_THREE", "H_S_C3"), ("D_THREE", "H_S_F3")):
        for system, reference in (("SEM_" + suffix, "M_" + suffix), ("COMB_" + suffix, "M_" + suffix),
                                  ("COMB_" + suffix, "SEM_" + suffix), ("SEM_" + suffix, hybrid),
                                  ("COMB_" + suffix, hybrid)):
            local = []
            for row in results[system]:
                base = align(results[reference], row["qid"], row["repeat"])
                assert base is not None
                before_rank = {case_id: index for index, case_id in enumerate(base["ranking"], 1)}
                after_rank = {case_id: index for index, case_id in enumerate(row["ranking"], 1)}
                for case_id in cases:
                    rank_changes.append({"system": system, "reference": reference, "qid": row["qid"],
                         "repeat": row["repeat"], "case_id": case_id, "silver_grade": grades[row["qid"]][case_id],
                         "before_rank": before_rank[case_id], "after_rank": after_rank[case_id],
                         "rank_gain": before_rank[case_id] - after_rank[case_id],
                         "rule_unknown33": case_id in unknown_ids, "actual_task": cases[case_id]["task"]})
                for count in run.CFG["K"]:
                    previous = set(base["ranking"][:count]) & positive[row["qid"]]
                    current = set(row["ranking"][:count]) & positive[row["qid"]]
                    event = {"system": system, "reference": reference, "qid": row["qid"], "repeat": row["repeat"],
                             "k": count, "new": sorted(current - previous), "retained": sorted(current & previous),
                             "lost": sorted(previous - current),
                             "new_silver_negative_topk": sorted((set(row["ranking"][:count]) - set(base["ranking"][:count])) - positive[row["qid"]])}
                    changes.append(event)
                    local.append(event)
            for count in run.CFG["K"]:
                subset = [row for row in local if row["k"] == count]
                change_summary.append({"system": system, "reference": reference, "k": count,
                    **{field + "_events": sum(len(row[field]) for row in subset) for field in ("new", "retained", "lost")},
                    **{field + "_unique_query_case": len({(row["qid"], case_id) for row in subset for case_id in row[field]})
                       for field in ("new", "retained", "lost")}})
    run.save("evaluation/related_changes.json", {"events": changes, "summary": change_summary})
    csvsave("evaluation/rank_changes.csv", rank_changes)
    unknown_summary = []
    for case_id in sorted(unknown_ids):
        positive_queries = sorted(qid for qid in grades if case_id in positive[qid])
        unknown_summary.append({"case_id": case_id, "task": cases[case_id]["task"],
                                "silver_positive_queries": positive_queries})
    unknown_rows = [row for row in rank_changes if row["rule_unknown33"] and row["reference"] == "M_D_SINGLE"]
    csvsave("evaluation/unknown33_ranks.csv", unknown_rows)
    run.save("evaluation/unknown33_analysis.json", {"records": unknown_summary,
             "positive_pairs": sum(len(row["silver_positive_queries"]) for row in unknown_summary),
             "interpretation": "Nonempty Task embedding is coverage, not demonstrated semantic correctness; relevant only under existing Silver."})
    target_ids = ("AXV2N_0121", "AXV2N_0124", "AXV2C_0093_01")
    mappings = {(row["path_id"], row["case_id"]): row for row in run.lines(run.OUT / "mapping/mappings.jsonl")}
    queries = run.read(run.INPUT / "query_registry.json")["paths"]
    profiles = run.read(run.OUT / "mapping/case_profiles.json")
    mandatory = []
    for system in ("H_F", "M_D_SINGLE", "SEM_D_SINGLE", "COMB_D_SINGLE", "SEM_O_SINGLE", "COMB_O_SINGLE"):
        for row in results[system]:
            if row["qid"] == "V21D001":
                for case_id in target_ids:
                    mandatory.append({"system": system, "repeat": row["repeat"], "case_id": case_id,
                                      "rank": row["ranking"].index(case_id) + 1,
                                      "silver_grade": grades["V21D001"][case_id]})
    run.save("evaluation/mandatory_cases.json", {"rankings": mandatory,
        "records": [{"case_id": case_id, "ptc": cases[case_id], "profile": profiles[case_id],
                     "whole": mappings["o_V21D001", case_id],
                     "branches": [mappings[path_id, case_id] for path_id, query in queries.items()
                                  if query["qid"] == "V21D001" and query["scope"] == "dynamic"]} for case_id in target_ids]})
    run.verify_freeze()
    assert run.digest(label_path) == label_hash
    run.save("evaluation/audit.json", {"complete": True, "silver_unchanged": True,
        "historical_rankings_and_metrics_exact": True, "systems": len(systems),
        "prediction_receipt_verified_before_label_load": True, "new_ranking_rows": sum(map(len, predictions.values())),
        "preregistration_sha256": run.digest(run.OUT / "preregistration.json"),
        "prediction_receipt_sha256": run.digest(run.OUT / "prediction_receipt.json"),
        "independent_test_access": False, "paid_api_calls": 0, "new_labels": 0, "finetuning": False,
        "full_designer_blinding": False, "generalization_established": False,
        "statistical_significance_tested": False})
    report(macro, change_summary, unknown_summary, mandatory, profiles)
    print({name: {count: round(cell["f1"] * 100, 4) for count, cell in macro[name].items()}
           for name in ("M_D_SINGLE", "SEM_D_SINGLE", "COMB_D_SINGLE")})


def report(macro, changes, unknown, mandatory, profiles):
    def percent(value):
        return f"{value * 100:.3f}"

    doc = ["# BGE-M3 의미 기반 Query–Case 정밀 매핑 Dev 비교", "", "2026-10-28 KST", "",
           "기준 SHA: `" + run.CFG["base_commit"] + "`. 연구 브랜치: `" + run.CFG["branch"] + "`.", "",
           "아래 수치는 기존 AI Silver 기준의 개발 데이터 비교다. 의미 유사도는 실제 업무 적합성 판정 확률이 아니다. 설정은 추론 전 고정하고, 전 예측의 hash를 평가 전 저장했다. 결과를 보고 가중치를 조정하지 않았다.", "",
           "## 핵심 비교", "", "P는 10질문, R/F1은 양성 6질문 Macro(%). 무양성4질문 R/F1은 NA. 동적3회는 질문별 평균 후 Macro다.", "",
           "|방식|K|P|R|F1|", "|---|---:|---:|---:|---:|"]
    for name in ("H_F", "M_D_SINGLE", "SEM_D_SINGLE", "COMB_D_SINGLE"):
        for count in run.CFG["K"]:
            cell = macro[name][str(count)]
            doc.append(f"|{name}|{count}|{percent(cell['precision'])}|{percent(cell['recall'])}|{percent(cell['f1'])}|")
    doc.extend(["", "SEM은 Task/Action/Object/Output/Context 필드 cosine 가중평균, COMB는 기존 규칙 강도와 의미점수의 사전 고정 1:1 결합이다. 원질문과 최고 관점점수를 1:1로 유지한다. 기존 검색랭킹 H_F는 참조 조건이며 수정하지 않았다.", "",
                "## 전체 조건", "", "|조건|F1@5|F1@10|F1@20|", "|---|---:|---:|---:|"])
    for name in macro:
        doc.append("|" + name + "|" + "|".join(percent(macro[name][str(count)]["f1"]) for count in run.CFG["K"]) + "|")
    doc.extend(["", "전26조건 P/R/F1 및 질문별 평균/회차 변동은 evaluation/macro_metrics.csv, query_mean_metrics.csv, results.json에 있다.", "",
                "## 새로 찾고 잃은 Silver 관련 사례", "", "반복 사건 수는 질문×회차×사례 단위이며 동일 사례가 여러 번 포함될 수 있다. 고유 수는 질문-사례 중복을 제거했다. 서로 다른 회차에서 같은 쌍이 신규와 손실 모두에 나타날 수 있다.", "",
                "|방식|비교대상|K|신규 사건/고유|유지 사건/고유|손실 사건/고유|", "|---|---|---:|---:|---:|---:|"])
    for row in changes:
        if row["reference"] == "M_D_SINGLE" or (row["system"] == "COMB_D_SINGLE" and row["reference"] == "SEM_D_SINGLE"):
            doc.append(f"|{row['system']}|{row['reference']}|{row['k']}|" + "|".join(
                f"{row[field + '_events']}/{row[field + '_unique_query_case']}" for field in ("new", "retained", "lost")) + "|")
    doc.extend(["", "전 사례 ID, 신규 Silver 음성 진입, 질문·회차·K별 내역은 evaluation/related_changes.json, 전112후보 순위변동과 실제 Task는 rank_changes.csv에 있다.", "",
                "## 규칙 미인식 33사례", "", "Task 전체를 사용해 문법 밖 표현도 비교할 수 있다. 필드가 채워졌다는 사실과 의미 해석이 맞다는 사실은 구분해야 한다.", "",
                "|사례|실제 Task|기존 Silver 양성 질문|미확인 필드|", "|---|---|---|---|"])
    for row in unknown:
        doc.append(f"|{row['case_id']}|{row['task'].replace('|', '/')}|{', '.join(row['silver_positive_queries']) or '없음'}|{', '.join(profiles[row['case_id']]['unknown_fields']) or '없음'}|")
    doc.extend(["", f"이 33사례에 속한 기존 Silver 양성 질문-사례는 {sum(len(row['silver_positive_queries']) for row in unknown)}쌍이다. 질문별 전체 순위 및 Silver 점수는 evaluation/unknown33_ranks.csv에 저장했다.", "",
                "## 제조 불량·고객 답변·HR 질문응답", "", "사전 지정된 진단 사례이며 독립 테스트가 아니다. 분야가 달라도 질문응답 행동은 비슷할 수 있지만, 고객 응대와 직원 규정 답변의 적용 맥락은 다르다. 품질이라는 단어만으로 제조 불량 분석이 고객 답변 품질 개선을 수행한다고 해석하지 않는다.", "",
                "|사례|필드|원문에서 추출한 내용|", "|---|---|---|"])
    for case_id in ("AXV2N_0121", "AXV2N_0124", "AXV2C_0093_01"):
        for field, text in profiles[case_id]["fields"].items():
            doc.append(f"|{case_id}|{field}|{text.replace(chr(10), '; ').replace('|', '/') or 'UNKNOWN'}|")
    doc.extend(["", "|방식|회차|사례|순위|Silver|", "|---|---:|---|---:|---:|"])
    for row in mandatory:
        doc.append(f"|{row['system']}|{row['repeat']}|{row['case_id']}|{row['rank']}|{row['silver_grade']}|")
    doc.extend(["", "원질문 및 모든 Q1 관점의 필드별 cosine과 가용 가중치는 evaluation/mandatory_cases.json에 있다. query_profiles.json/case_profiles.json은 원문 위치를 제공하고 mapping/mappings.jsonl은 전13,216쌍을 제공한다.", "",
                "## 해석 한계와 다음 결정", "",
                "- 10 Dev 질문·18양성쌍의 희소한 AI Silver 평가다. 사람 Gold, 독립 공급자 합의, 일반화, 통계적 유의성을 증명하지 않는다.",
                "- 기존 예시와 Dev 결과가 알려진 상태에서 설계했다. 전처리·추론에 Silver를 넣지 않았지만 설계자 수준의 완전 눈가림은 아니다. 학습은 없으므로 학습/검증 분할 성능으로 표현하지 않는다.",
                "- Action은 넓은 표면 패턴, Object는 잔여 구절이다. 의미역과 수식 범위를 정확히 분리했다고 주장하지 않는다. Task 제목이 짧거나 모호하면 대응 의미도 제한된다. 기존 부정/미래 가드는 정상 Task도 과도하게 보류할 수 있다.",
                "- Output은 명시 문자열만 인정해 대부분 UNKNOWN일 수 있다. 산출물을 임의로 채워 완성된 다섯 의미역 비교처럼 제시하지 않는다. 누락 필드별 분모 차이와 query/case Context 추출 비대칭은 점수 비교의 한계다.",
                "- 원질문에서 원하는 작업과 사례가 실제 수행한 작업의 언어적 유사도를 측정한다. 요구사항 전체 충족, 배포 가능성, 보안, 실제 효과나 원 출판물 사실성을 보증하지 않는다. Context는 실행 증거를 대신하지 않는다.",
                "- 최고 관점 연산은 중복 가산을 막지만 우연히 높은 한 관점이 순위를 올릴 수 있다. 가중치·규칙강도/4·cosine 변환은 확률 보정값이 아니다. 1:1 결합은 임의 실험 선택이며 최적값이라고 주장하지 않는다.",
                "- 원질문/관점 Single 및 3View는 동일 매핑을 사용하고 기존 검색점수 동점 처리만 다르다. 이는 BGE 표현을 새로 3View 학습한 실험이 아니다. 저장한 과거 RRF는 역사적 검색 참조다.",
                "- 독립 Stage4 Test는 열람·실행하지 않았다. 새 유료 API, 라벨 생성, 파인튜닝은 0이다. 기존 모델의 CPU 추론은 로컬 자원을 사용했다. 외부 공증 없이 로컬 hash로 실행 순서를 기록했다.", "",
                "다음 선택은 결과가 좋은 단일 지표만 보고 내리지 않는다. 신규/손실 사례와 Task 근거를 검토하고, 별도 사람 검증 또는 차기 사전등록 실험이 준비된 뒤 확정한다. 이번 Dev 결과만으로 독립 Test를 개봉하지 않는다.", "",
                "## 재현", "", "저장소 루트에서 기존 AX-prototype 가상환경을 사용한다. PYTHONPATH=src와 HF_HUB_OFFLINE=1을 적용한다.", "",
                "```text", "python -m pytest tests/test_functional_mapping.py tests/test_semantic_mapping.py",
                "python -m scripts.semantic_mapping_run freeze", "python -m scripts.semantic_mapping_run run",
                "python -m scripts.semantic_mapping_evaluate", "```", "",
                "freeze는 기준 HEAD와 고정 해시를 요구하며 설정이 바뀐 재실행은 거부한다. 모델·원본 입력 경로·정확한 패키지 버전은 preregistration.json에 있다. Git 커밋 후에는 기존 봉인 파일로 run/evaluate를 재실행한다.", ""])
    (run.OUT / "README.md").write_text("\n".join(doc), encoding="utf-8", newline="\n")


if __name__ == "__main__":
    socket.socket.connect = run.blocked
    socket.create_connection = run.blocked
    main()
