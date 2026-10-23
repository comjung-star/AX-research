# AX v2.3 Stage 2 — 실제 Dev 실험 결과
**코퍼스:** 업무 사례 84개 · 개발 문제 10개 · AI 관련도 2,520개
**평가:** Dev AI 평가자료만 사용. 인간 Gold나 독립 Test가 아님.

## 실행 조건
{
  "stage": "STAGE_2_REAL_EXECUTED",
  "corpus_cases": 84,
  "source": "/home/runner/work/AX-research/AX-research/experiments/v23_dev/stage1",
  "methods": [
    "2-1 equal-view",
    "2-2 learned query-conditioned gate LOQO",
    "2-3 dense+sparse candidate union equal budget",
    "2-4 query-case MLP LOQO with identical RRF pool"
  ],
  "target_scores": "DEV_AI_SILVER_NOT_HUMAN_GT",
  "positive_threshold": 3,
  "test_set": "NOT_AVAILABLE",
  "train_test_leakage": "QUERY_LOQO_HOLDS_TARGET_OUT",
  "evaluation_reference_perspectives_not_in_runtime": true,
  "same_candidate_budget_per_branch": 20,
  "folds": 10,
  "perspective_branches": 97
}

## 비교 결과
| 방식 | K | Recall | 관점 Coverage | 전략 Coverage* |
|---|---:|---:|---:|---:|
| stage2_1_equal_view | 5 | 0.272 | 0.750 | 0.662 |
| stage2_1_equal_view | 10 | 0.424 | 0.822 | 0.811 |
| stage2_1_equal_view | 20 | 0.621 | 0.939 | 0.964 |
| stage2_2_learned_gated_LOQO | 5 | 0.203 | 0.606 | 0.552 |
| stage2_2_learned_gated_LOQO | 10 | 0.319 | 0.739 | 0.757 |
| stage2_2_learned_gated_LOQO | 20 | 0.463 | 0.794 | 0.890 |
| stage2_4_query_case_MLP_LOQO | 5 | 0.143 | 0.400 | 0.659 |
| stage2_4_query_case_MLP_LOQO | 10 | 0.246 | 0.606 | 0.836 |
| stage2_4_query_case_MLP_LOQO | 20 | 0.379 | 0.717 | 0.931 |
| stage2_4_same_pool_rrf | 5 | 0.204 | 0.639 | 0.579 |
| stage2_4_same_pool_rrf | 10 | 0.387 | 0.844 | 0.816 |
| stage2_4_same_pool_rrf | 20 | 0.582 | 0.933 | 0.933 |

* 전략 커버리지 기준은 Silver 양성 사례의 전략을 합친 **파생 지표**이며 독립적인 전략 정답 아님.

**2-3 후보 풀 평균 Recall 변화(동일 검색 슬롯)**: -0.107. 손실도 그대로 보고한다.
2-2/2-4 학습형 모델은 평가 대상 질의가 훈련에 포함되지 않는 Leave-One-Query-Out을 적용했다.

## 연구상 제한
- 사후에 사례 또는 Ground Truth를 성능 개선 목적으로 변경하지 않았다.
- v2.3 코퍼스에 Dev 관점에 맞춰 추가한 사례가 있으므로 선택 편향이 존재한다.
- 독립 Held-out Test를 완료한 것으로 표현하지 않는다.
