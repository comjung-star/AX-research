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
11. Dev Result Review ✅
12. Stage 2-1 Multi-view Equal Dense ✅
13. Stage 2-2 Gated Fusion LOQO ✅
14. Stage 2-3 Hybrid Retrieval Candidate Union ✅
15. Stage 2-4 Query-Case Interaction LOQO ✅
16. **Stage 3 Factor Anchor / Wald Evidence 설계 ← 다음**

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

## RQ1 Coverage 진단

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

---

## Stage 2-1 — Multi-view Embedding 분리 실험

Frozen specification:
- `docs/experiment-spec-stage2-multiview-v1.md`
- `configs/experiment_stage2_multiview_v1.yaml`

목적:
- Stage 1 MP Dense의 **실제 Generated Perspective를 그대로 replay**
- LLM sampling을 제거한 상태에서 Case 표현만 변경
- 기존: `Problem + Task + Context` 연결 문서 1개
- Stage 2-1: `Problem / Task / Context`를 각각 BGE-M3 임베딩
- 세 View cosine score를 1/3씩 동일가중 평균
- final selection은 기존 `branch_balanced_unique` 그대로 유지

### Stage 2-1 Dev Recall

| System | Recall@5 | Recall@10 | Recall@20 |
|---|---:|---:|---:|
| Stage 1 MP Dense | 0.323267 | 0.502667 | 0.656546 |
| Stage 2-1 Multi-view Equal Dense | 0.323467 | 0.499295 | 0.659976 |
| Delta | +0.000200 | -0.003372 | +0.003430 |

동일가중 Multi-view 분리만으로는 **뚜렷한 Recall 개선이 확인되지 않았다.**

Gold gained/lost vs Stage 1 MP Dense:
- @5: gained 20 / lost 19 / net +1
- @10: gained 28 / lost 27 / net +1
- @20: gained 25 / lost 27 / net -2

Branch diagnostics:
- Stage 1 MP Dense mean Jaccard: 0.3757
- Stage 2-1 mean Jaccard: 0.4035
- Stage 1 duplicate candidate rate: 0.4218
- Stage 2-1 duplicate candidate rate: 0.4340

즉 View를 분리하면 ranking은 바뀌지만, 모든 Query에 동일한 1/3 가중치를 적용하는 방식은
Stage 1의 Recall trade-off를 해결하지 못했다.

상세:
- `experiments/rq2_multiview/results/stage2_multiview_v1/DEV_RESULT_ANALYSIS.md`

### 다음: Stage 2-2 Gated Fusion

다음 실험은 Query/Perspective별로 Problem / Task / Context 중요도를 동적으로 조정하는
Gated Fusion / Attention의 추가 효과를 검증한다.

Stage 2-1과 동일하게 다음 조건을 통제한다.
- 동일 Stage 1 Generated Perspective replay
- 동일 Dataset / GT
- 동일 BGE-M3 backbone
- 동일 K
- 동일 branch-balanced unique final selection

학습형 Gate를 사용할 경우 동일 Query의 Gold label이 학습과 평가 양쪽에 들어가지 않도록
Query 단위 분리를 사용한다.

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


---

## Stage 2-2 — Query-Conditioned Gated Fusion

Frozen specification:
- `docs/experiment-spec-stage2-gated-v1.md`
- `configs/experiment_stage2_gated_v1.yaml`

통제:
- Stage 1 Generated Perspective 그대로 replay
- Stage 2-1에서 계산된 Problem / Task / Context view score 재사용
- BGE-M3 / Dataset / GT / K / branch-balanced unique 동일
- LLM 재호출 없음

Gate:
- branch query와 3개 semantic view anchor 간 cosine similarity를 입력 feature로 사용
- `Linear(3→3) + Softmax`
- 총 12개 학습 파라미터
- 초기값은 equal weight
- Query-level Leave-One-Out(LOQO)으로 평가 Query label 누수 방지
- Query-level Gold를 pairwise logistic ranking loss로 학습

### Stage 2-2 Dev Recall

| System | Recall@5 | Recall@10 | Recall@20 |
|---|---:|---:|---:|
| Stage 1 MP Dense | 0.323267 | 0.502667 | 0.656546 |
| Stage 2-1 Equal Fusion | 0.323467 | 0.499295 | 0.659976 |
| Stage 2-2 Gated Fusion | 0.309681 | 0.464334 | 0.655820 |

Stage 2-1 Equal 대비 Delta:
- @5: -0.013785
- @10: -0.034962
- @20: -0.004156

Gold gained/lost vs Stage 2-1 Equal:
- @5: gained 21 / lost 25 / net -4
- @10: gained 21 / lost 33 / net -12
- @20: gained 19 / lost 19 / net 0

평균 learned weight:
- Problem: 0.5998
- Task: 0.0026
- Context: 0.3976

범위:
- Problem: 0.4652 ~ 0.8103
- Task: 0.0012 ~ 0.0054
- Context: 0.1861 ~ 0.5336

Branch diagnostics:
- mean Jaccard: 0.3744
- duplicate candidate rate: 0.4211

### Stage 2-2 해석

현재 v1 Gate는 Query마다 weight 차이를 만들기는 했지만 Task View를 거의 0으로
억제하는 방향으로 학습됐고, Equal Fusion보다 @5/@10 Recall이 악화됐다.

따라서 현 시점 결론은:
- "동적 가중치가 무조건 좋다"는 가설은 지지되지 않음
- 현재의 semantic-anchor + pairwise-loss Gate v1은 채택하지 않음
- 같은 Dev 결과를 보고 hyperparameter를 사후 조정해 성능을 끌어올리지 않음
- 결과를 정식 ablation으로 보존하고 다음 구성요소인 Hybrid Retrieval로 진행

이 결과는 Multi-view 전체를 기각하는 것이 아니라,
**현재 Gate의 입력 feature와 학습목표가 적절한가**를 별도 연구문제로 남긴다.

상세:
- `experiments/rq2_multiview/results/stage2_gated_v1/DEV_RESULT_ANALYSIS.md`

### Stage 2-3 — Hybrid Retrieval Candidate Union

Frozen specification:
- `docs/experiment-spec-stage2-hybrid-v1.md`
- `configs/experiment_stage2_hybrid_v1.yaml`

교수 제안 아키텍처에서 Hybrid Retrieval은 최종 순위를 확정하는 단계가 아니라
Dense + Sparse 결과를 결합해 Candidate Pool을 확보하는 단계다.

따라서 Stage 2-3에서는 실패한 Gate v1을 사용하지 않고 Stage 2-1 Equal Dense를 Dense leg로 사용했으며,
같은 Generated Perspective에 Kiwi BM25 Sparse leg를 추가했다.

공정한 검색 슬롯 비교:
- Dense Top-5 + BM25 Top-5 vs Dense Top-10
- Dense Top-10 + BM25 Top-10 vs Dense Top-20
- Dense Top-20 + BM25 Top-20 vs Dense Top-40

### Stage 2-3 Dev Candidate Recall

| leg_k | slots/branch | Hybrid | Dense same-slot | Delta |
|---:|---:|---:|---:|---:|
| 5 | 10 | 0.619099 | 0.649538 | -0.030439 |
| 10 | 20 | 0.780287 | 0.793484 | -0.013196 |
| 20 | 40 | 0.916413 | 0.935577 | -0.019164 |

Gold gained/lost vs same-slot Dense:
- leg_k=5: gained 28 / lost 36 / net -8
- leg_k=10: gained 23 / lost 33 / net -10
- leg_k=20: gained 12 / lost 17 / net -5

Dense/Sparse branch mean Jaccard:
- leg_k=5: 0.3483
- leg_k=10: 0.3122
- leg_k=20: 0.3558

해석:
- Sparse는 Dense와 다른 후보를 실제로 추가함
- 일부 Query/Run에서는 Hybrid가 Dense-only보다 더 많은 Gold를 회수함
- 그러나 50:50 retrieval slot 배분에서는 평균적으로 lost Gold가 더 많았음
- 따라서 Hybrid의 보완성은 확인됐지만, Candidate Recall 우위는 확인되지 않음
- 이 단계는 최종 Ranking이 아니므로 Hybrid 구조 전체를 기각하지 않음
- 다음 Query-Case Interaction에서 Candidate Pool의 후보를 relevance 기준으로 재평가하는 효과를 검증함

상세:
- `experiments/rq2_multiview/results/stage2_hybrid_v1/DEV_RESULT_ANALYSIS.md`

### 다음: Stage 2-4 Query-Case Interaction

Hybrid Retrieval이 가져온 Candidate Pool을 입력으로
`[q,c,q⊙c,|q-c|] → MLP → Relevance Score` 구조의 추가 효과를 검증한다.


---

## Stage 2-4 — Query-Case Interaction

Frozen specification:
- `docs/experiment-spec-stage2-interaction-v1.md`
- `configs/experiment_stage2_interaction_v1.yaml`

교수 제안 구조:
`[q,c,q⊙c,|q-c|] → MLP → Relevance Score`

통제:
- Stage 2-3 Hybrid Candidate Pool 그대로 사용
- leg_k 5 / 10 / 20 모두 평가
- BGE-M3 + Problem/Task/Context equal-mean Case representation
- corpus-only PCA 64-d
- MLP 256→32→1
- Query-level LOQO
- 동일 Candidate Pool RRF baseline
- 동일 branch-balanced unique final selection

### Stage 2-4 Dev Recall

| leg_k | K | QCI MLP | Same-pool RRF | Delta |
|---:|---:|---:|---:|---:|
| 5 | 5 | 0.243504 | 0.321087 | -0.077583 |
| 5 | 10 | 0.428052 | 0.476863 | -0.048811 |
| 5 | 20 | 0.619099 | 0.619099 | 0.000000 |
| 10 | 5 | 0.219441 | 0.316405 | -0.096964 |
| 10 | 10 | 0.363484 | 0.506004 | -0.142520 |
| 10 | 20 | 0.585269 | 0.685974 | -0.100705 |
| 20 | 5 | 0.204402 | 0.319923 | -0.115521 |
| 20 | 10 | 0.333520 | 0.517393 | -0.183873 |
| 20 | 20 | 0.548902 | 0.693165 | -0.144263 |

QCI v1은 모든 실질 비교에서 same-pool RRF보다 낮았다.
leg_k=5, K=20의 동률은 작은 candidate pool에서 최종 후보가 사실상 모두 포함되는 경우가 많기 때문이다.

Gold delta vs RRF:
- leg_k=5: K5 net -25 / K10 net -15 / K20 net 0
- leg_k=10: K5 net -29 / K10 net -46 / K20 net -32
- leg_k=20: K5 net -36 / K10 net -60 / K20 net -54

해석:
- 현재 Query-level Gold union supervision에서는 branch-specific interaction 학습이 충분하지 않았을 가능성
- 10개 Dev Query 규모에서 learned MLP의 query-level 일반화가 제한됨
- RRF가 Dense/BM25의 rank prior를 안정적으로 보존
- 현 v1 QCI는 채택하지 않고 failed ablation으로 보존
- 같은 Dev 결과를 보고 즉시 hyperparameter를 사후 튜닝하지 않음

상세:
- `experiments/rq2_multiview/results/stage2_interaction_v1/DEV_RESULT_ANALYSIS.md`

### Stage 2 Search Core 현재 판단

교수 제안 Search Core의 Multi-view / Gated Fusion / Hybrid Retrieval / Query-Case Interaction을
모두 구성요소별로 Dev 검증했다.

현재 데이터 규모에서:
- Multi-view 분리 자체: 중립적
- Gated Fusion v1: 악화
- Hybrid 50:50 Candidate Union: 보완성은 있으나 평균 Candidate Recall 악화
- Query-Case Interaction v1: same-pool RRF보다 악화

이 결과는 교수 아키텍처를 임의 삭제하는 근거가 아니라,
각 구현의 채택 여부를 실험으로 검증한 ablation 결과다.
