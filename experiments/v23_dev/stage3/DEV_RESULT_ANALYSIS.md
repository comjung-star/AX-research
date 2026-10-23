# AX v2.3 Stage 3 — 실제 Dev 실험 결과
**코퍼스:** 업무 사례 84개 · 개발 문제 10개 · AI 관련도 2,520개
**평가:** Dev AI 평가자료만 사용. 인간 Gold나 독립 Test가 아님.

## 실행 조건
{
  "stage": "STAGE_3_REAL_EXECUTED",
  "cases": 84,
  "factors": 11,
  "strategies": 7,
  "pairs": 77,
  "wald_eligible": 3,
  "wald_sparse_abstentions": 74,
  "trace_rows": 653,
  "unique_rank_occurrences": 600,
  "unusable_wald_case_links": 472,
  "evaluative_claim": "ASSOCIATION_ONLY_NOT_CAUSAL",
  "reference_retrieval": "same-pool RRF and interaction MLP, top10 each query x 3 repeats",
  "strategy_coverage_cannot_increase_from_metadata_only": true,
  "candidate_branch_links_not_ground_truth": true,
  "status": "DEV_AI_SILVER_EVIDENCE_DIAGNOSTIC"
}

## 통계 및 추적 결과
- Factor×Strategy: 77쌍
- Wald 분석 가능한 쌍: 3
- Wald 표본부족으로 보류: 74
- 추적 대상 검색 사례: 600
- 사례–원인–전략 근거 연결: 653
Wald 결과는 인과관계가 아닌 연관성이다. 표본 부족이면 통계 판단을 보류한다.

## 연구상 제한
- 사후에 사례 또는 Ground Truth를 성능 개선 목적으로 변경하지 않았다.
- v2.3 코퍼스에 Dev 관점에 맞춰 추가한 사례가 있으므로 선택 편향이 존재한다.
- 독립 Held-out Test를 완료한 것으로 표현하지 않는다.
