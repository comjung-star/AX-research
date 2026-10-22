# Experiment Plan

구성요소를 한 번에 모두 구현하지 않고 단계별로 효과를 검증합니다.

## 현재 RQ1 실행 명세

- Frozen specification: `docs/experiment-spec-rq1-v1.3.md`
- Frozen config: `configs/experiment_rq1_v1.3.yaml`
- Dev Ground Truth Freeze: `data/dev_ground_truth_freeze_v1.md`

v1.3 핵심 조건:
- 공통 LLM: `gpt-6-luna`
- temperature: API default / parameter omitted
- Query별 LLM 3회 독립 실행
- Multi-Perspective branch query: **Perspective only**
- Original Business Problem은 Perspective 생성에만 사용하고 branch 검색에는 다시 넣지 않음
- Runtime Perspective: 2~5개
- final selection: branch-balanced unique
- K = 5 / 10 / 20

## RQ1 Stage 1 상태

1. Dataset / Retrieval Ground Truth 준비 ✅
2. RQ1 Experiment Spec v1.3 Freeze ✅
3. Common Evaluation Engine ✅
4. Single-query BM25 baseline 구현/실행 ✅
5. Single-query Dense Retrieval baseline 구현/실행 ✅
6. GPT-only 구현/3-repeat 실행 ✅
7. Multi-Perspective + BM25 diagnostic 구현/3-repeat 실행 ✅
8. Multi-Perspective + Dense 구현/3-repeat 실행 ✅
9. Common Diagnostics / Summary ✅
10. Dev 실행 ✅
11. **Dev Result Review ← 현재**
12. Next-stage Multi-view / Gated Fusion / Hybrid Retrieval

## RQ1 v1.3 Dev Recall

| System | Recall@5 | Recall@10 | Recall@20 |
|---|---:|---:|---:|
| Single BM25 | 0.3643 | 0.5119 | 0.6446 |
| Single Dense | 0.3575 | 0.5176 | 0.6947 |
| GPT-only | 0.4270 | 0.6650 | 0.8748 |
| Multi-Perspective BM25 | 0.3063 | 0.4464 | 0.6547 |
| Multi-Perspective Dense | 0.3233 | 0.5027 | 0.6565 |

핵심 비교인 Single Dense vs Multi-Perspective Dense에서 MP Dense의 평균 Recall 개선은 확인되지 않았다.

Delta:
- @5: -0.0342
- @10: -0.0149
- @20: -0.0382

## Coverage 진단

일반 Perspective Coverage / Strategy Coverage는 모든 시스템이 @5부터 1.0으로 saturation되어 Dev 변별력이 없었다.

추가 diagnostic인 Exclusive Perspective Coverage:

| System | @5 | @10 | @20 |
|---|---:|---:|---:|
| Single Dense | 0.4667 | 0.6167 | 0.7333 |
| Multi-Perspective Dense | 0.4000 | 0.6222 | 0.8389 |

@20에서는 MP Dense가 관점 고유 사례를 더 넓게 회수했다.

Gold gained/lost vs Single Dense:
- @5: gained 23 / lost 35 / net -12
- @10: gained 24 / lost 33 / net -9
- @20: gained 34 / lost 46 / net -12

Perspective 분해가 새로운 Gold를 찾기는 하지만 현재 branch-balanced unique selection에서는 더 많은 기존 Gold가 밀려나는 trade-off가 관찰됐다.

상세 결과:
- `experiments/rq1_retrieval/results/rq1_v1_3_llm_dev/DEV_RESULT_ANALYSIS.md`

## Ground Truth 원칙

- `GTQ001~GTQ010`은 Dev/Pilot Query로 사용하며 최종 Test Query와 분리합니다.
- Main Dataset v1 `AX0001~AX0100`을 고정하여 사용합니다.
- Perspective × Case 관련도는 0~4, Gold threshold는 >=3입니다.
- Retrieval 관련도 판정은 Problem View 중심입니다.
- Ground Truth는 Runtime LLM 입력으로 사용하지 않습니다.
- Held-out Test는 모델·Prompt·평가규칙 Freeze 후 별도로 구축합니다.
- Dev 결과에 맞춰 Ground Truth를 수정하지 않습니다.

## 평가 지표

Primary:
- `Recall@K`
- `Perspective Coverage@K`
- `Strategy Coverage@K`

Diagnostic:
- Exclusive Perspective Coverage
- Branch pairwise Jaccard
- Duplicate candidate rate
- Gold gained / lost / net
- Generated Perspective count
- LLM 3회 반복 Run variability

Dev 결과는 방향성/실패사례 분석용이며, 10개 Query만으로 과도한 통계적 일반화를 하지 않습니다.
