# AX v2.3 Stage 4 — 실제 Dev 실험 결과
**코퍼스:** 업무 사례 84개 · 개발 문제 10개 · AI 관련도 2,520개
**평가:** Dev AI 평가자료만 사용. 인간 Gold나 독립 Test가 아님.

## 실행 조건
{
  "stage": "STAGE_4_REAL_EXECUTED",
  "query_repetitions": 30,
  "evidence_grounded_llm_answers": 30,
  "trace_records": 93,
  "strategy_labels": 7,
  "methods": [
    "evidence_grounded_llm",
    "retrieved_case_frequency",
    "wald_safe_evidence_fusion"
  ],
  "llm_model": "gpt-6-luna",
  "input_no_gold_labels": true,
  "predefined_fusion_rule": true,
  "pairs_wald_eligible": 3,
  "silent_wald_fill": false,
  "metrics": "DEV_ONLY_WITH_SILVER_DERIVED_NONINDEPENDENT_REFERENCE",
  "final_test_completed": false,
  "causal_claim": false
}

## 추천 전략 비교 (탐색적 Dev)
| 방식 | Strategy Recall@3 | Strategy Precision@3 |
|---|---:|---:|
| evidence_grounded_llm | 0.545 | 0.978 |
| retrieved_case_frequency | 0.618 | 0.656 |
| wald_safe_evidence_fusion | 0.618 | 0.656 |

근거 연결 93건. 실제 API 생성 답변 30회.
전략 기준은 AI 관련도 양성 사례들에서 파생됐고 독립 정답이 아니다. 최종 전략추천 정확도의 검증으로 해석할 수 없다.

## 연구상 제한
- 사후에 사례 또는 Ground Truth를 성능 개선 목적으로 변경하지 않았다.
- v2.3 코퍼스에 Dev 관점에 맞춰 추가한 사례가 있으므로 선택 편향이 존재한다.
- 독립 Held-out Test를 완료한 것으로 표현하지 않는다.
