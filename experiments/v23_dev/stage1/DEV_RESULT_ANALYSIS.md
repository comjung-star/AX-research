# AX v2.3 Stage 1 — 실제 Dev 실험 결과
**코퍼스:** 업무 사례 84개 · 개발 문제 10개 · AI 관련도 2,520개
**평가:** Dev AI 평가자료만 사용. 인간 Gold나 독립 Test가 아님.

## 실행 조건
{
  "stage": "STAGE_1_REAL_EXECUTED",
  "corpus_version": "v2.3.0",
  "corpus_cases": 84,
  "qrels": "AI_SILVER_NOT_HUMAN_GT",
  "dense": "BAAI/bge-m3",
  "llm": "gpt-6-luna",
  "repeats": 3,
  "runtime_perspectives": 97,
  "reference_perspectives_not_in_runtime": true,
  "solution_not_in_retrieval": true,
  "metric_k": [
    5,
    10,
    20
  ],
  "models": [
    "gpt_only",
    "mp_bm25",
    "mp_dense_bge_m3",
    "single_bm25",
    "single_dense_bge_m3"
  ],
  "output_rankings": 2200,
  "output_metrics": 330,
  "python": "3.11.17",
  "silver_only_dev_no_test": true
}

## 비교 결과
| 방식 | K | Recall | 관점 Coverage | 전략 Coverage* |
|---|---:|---:|---:|---:|
| gpt_only | 5 | 0.513 | 0.950 | 0.705 |
| gpt_only | 10 | 0.724 | 0.967 | 0.860 |
| gpt_only | 20 | 0.888 | 0.967 | 0.917 |
| mp_bm25 | 5 | 0.161 | 0.633 | 0.565 |
| mp_bm25 | 10 | 0.247 | 0.683 | 0.718 |
| mp_bm25 | 20 | 0.304 | 0.683 | 0.903 |
| mp_dense_bge_m3 | 5 | 0.298 | 0.794 | 0.727 |
| mp_dense_bge_m3 | 10 | 0.453 | 0.928 | 0.838 |
| mp_dense_bge_m3 | 20 | 0.646 | 0.978 | 0.975 |
| single_bm25 | 5 | 0.171 | 0.650 | 0.545 |
| single_bm25 | 10 | 0.238 | 0.650 | 0.643 |
| single_bm25 | 20 | 0.294 | 0.683 | 0.805 |
| single_dense_bge_m3 | 5 | 0.345 | 0.967 | 0.708 |
| single_dense_bge_m3 | 10 | 0.533 | 1.000 | 0.867 |
| single_dense_bge_m3 | 20 | 0.685 | 1.000 | 0.950 |

* 전략 커버리지 기준은 Silver 양성 사례의 전략을 합친 **파생 지표**이며 독립적인 전략 정답 아님.

## 연구상 제한
- 사후에 사례 또는 Ground Truth를 성능 개선 목적으로 변경하지 않았다.
- v2.3 코퍼스에 Dev 관점에 맞춰 추가한 사례가 있으므로 선택 편향이 존재한다.
- 독립 Held-out Test를 완료한 것으로 표현하지 않는다.
