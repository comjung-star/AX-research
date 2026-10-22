# Experiment Plan

구성요소를 한 번에 모두 구현하지 않고, 교수 제안 아키텍처의 각 요소를 controlled ablation으로 분리 검증한다.

> Stage 번호는 교수 제안의 공식 명칭이 아니라 본 연구의 실험 운영 순서다.

## 1. 공통 고정 조건

- Dataset: AX0001~AX0100
- Dev/Pilot Query: GTQ001~GTQ010
- Dev Ground Truth v1 Freeze
- relevance >= 3 = Gold
- K = 5 / 10 / 20
- Dev 결과에 맞춘 Ground Truth 사후 변경 금지
- 최종 Held-out Test는 모델/규칙 Freeze 후 별도 구축

## 2. 전체 진행상황

| 단계 | 질문 | 상태 | 현재 판단 |
|---|---|---|---|
| Stage 0 | 평가 가능한 Dataset/GT가 준비됐는가? | ✅ | Freeze |
| Stage 1 | Multi-Perspective가 단일 Query보다 도움이 되는가? | ✅ | 신규 Gold 탐색 효과, 총 Recall 우위 없음 |
| Stage 2-1 | Multi-view 분리 자체가 도움이 되는가? | ✅ | Equal Fusion은 거의 동일 |
| Stage 2-2 | Query별 동적 View 가중치가 도움이 되는가? | ✅ | Gate v1 미채택 |
| Stage 2-3 | Dense+Sparse가 후보 회수를 보완하는가? | ✅ | 보완성 확인, 50:50 우위 없음 |
| Stage 2-4 | Query-Case Interaction이 재정렬을 개선하는가? | ✅ | MLP v1 미채택 |
| Stage 3 | Factor Anchor + Wald Evidence가 근거 품질을 높이는가? | ← NEXT | 미실행 |
| Stage 4 | Evidence Fusion + LLM이 설명 가능한 전략 추천을 만드는가? | 예정 | 미실행 |
| Final | Held-out Query에서도 일반화되는가? | 예정 | 미실행 |

## 3. Stage 1 — Multi-Perspective

Frozen:
- docs/experiment-spec-rq1-v1.3.md
- configs/experiment_rq1_v1.3.yaml

| System | Recall@5 | Recall@10 | Recall@20 |
|---|---:|---:|---:|
| Single BM25 | 0.3643 | 0.5119 | 0.6446 |
| Single Dense | 0.3575 | 0.5176 | 0.6947 |
| GPT-only | 0.4270 | 0.6650 | 0.8748 |
| MP BM25 | 0.3063 | 0.4464 | 0.6547 |
| MP Dense | 0.3233 | 0.5027 | 0.6565 |

MP Dense vs Single Dense:
- @5: gained 23 / lost 35 / net -12
- @10: gained 24 / lost 33 / net -9
- @20: gained 34 / lost 46 / net -12

결론: **Perspective 분해는 새로운 Gold를 찾지만 현재 merge/ranking에서는 더 많은 기존 Gold가 밀려 총 Recall 우위로 연결되지 않았다.**

## 4. Stage 2-1 — Multi-view Equal

Frozen:
- docs/experiment-spec-stage2-multiview-v1.md
- configs/experiment_stage2_multiview_v1.yaml

| System | @5 | @10 | @20 |
|---|---:|---:|---:|
| Stage 1 MP Dense | 0.323267 | 0.502667 | 0.656546 |
| Multi-view Equal | 0.323467 | 0.499295 | 0.659976 |

결론: **Problem / Task / Context를 분리하고 동일가중으로 평균하는 것만으로는 뚜렷한 개선이 없었다.**

## 5. Stage 2-2 — Query-Conditioned Gated Fusion v1

Frozen:
- docs/experiment-spec-stage2-gated-v1.md
- configs/experiment_stage2_gated_v1.yaml

| System | @5 | @10 | @20 |
|---|---:|---:|---:|
| Equal Fusion | 0.323467 | 0.499295 | 0.659976 |
| Gated Fusion v1 | 0.309681 | 0.464334 | 0.655820 |

평균 weight: Problem 0.5998 / Task 0.0026 / Context 0.3976

결론: **Gate v1은 Task를 거의 제거하는 방향으로 수렴했고 Equal보다 낮았다. 현재 구현은 미채택하고 ablation으로 보존한다.**

## 6. Stage 2-3 — Hybrid Retrieval Candidate Union v1

Frozen:
- docs/experiment-spec-stage2-hybrid-v1.md
- configs/experiment_stage2_hybrid_v1.yaml

| leg_k | slots/branch | Hybrid Recall | Dense same-slot | Delta |
|---:|---:|---:|---:|---:|
| 5 | 10 | 0.619099 | 0.649538 | -0.030439 |
| 10 | 20 | 0.780287 | 0.793484 | -0.013196 |
| 20 | 40 | 0.916413 | 0.935577 | -0.019164 |

결론: **Sparse가 Dense와 다른 Gold를 추가하는 보완성은 확인됐지만, 고정 50:50 slot allocation은 same-slot Dense-only보다 평균 Recall이 낮았다.**

## 7. Stage 2-4 — Query-Case Interaction v1

Frozen:
- docs/experiment-spec-stage2-interaction-v1.md
- configs/experiment_stage2_interaction_v1.yaml

교수 제안 구조: [q,c,q⊙c,|q-c|] → MLP → Relevance Score

| leg_k | K | QCI MLP | RRF | Delta |
|---:|---:|---:|---:|---:|
| 5 | 5 | 0.243504 | 0.321087 | -0.077583 |
| 5 | 10 | 0.428052 | 0.476863 | -0.048811 |
| 10 | 10 | 0.363484 | 0.506004 | -0.142520 |
| 10 | 20 | 0.585269 | 0.685974 | -0.100705 |
| 20 | 10 | 0.333520 | 0.517393 | -0.183873 |
| 20 | 20 | 0.548902 | 0.693165 | -0.144263 |

결론: **현재 QCI MLP v1은 same-pool RRF보다 낮아 미채택한다. Query-Case Interaction 개념 자체를 기각하는 결과는 아니다.**

## 8. Stage 2 Search Core 종합

현재 100 Case / 10 Dev Query에서는:
- Multi-Perspective의 탐색 다양성은 확인됨
- Equal Multi-view는 중립적
- 학습형 Gate v1과 QCI MLP v1은 일반화 이득을 보이지 못함
- Hybrid는 Dense/Sparse 보완성을 보였지만 고정 50:50 배분은 비효율적
- 비학습 rank prior를 보존하는 방식이 더 안정적

실패한 세부 구현을 사후 튜닝해 성공으로 만들지 않고 결과를 보존한다.

## 9. Stage 3 — Factor Anchor / Wald Evidence

다음 검증 대상:

~~~text
Retrieved Cases
→ Case Evidence Pooling
→ Root Cause Factor Anchor
→ Wald Evidence
→ Evidence Fusion
~~~

주요 질문:
- 검색 결과를 Root Cause Factor에 안정적으로 연결할 수 있는가?
- Factor ↔ Strategy의 통계적 연관성을 Wald Evidence로 사용할 수 있는가?
- Strategy Coverage와 Traceable Evidence Path가 개선되는가?

Wald는 인과관계가 아니라 **연관성 Evidence**로 해석한다.

## 10. 평가 원칙

Primary:
- Recall@K
- Perspective Coverage@K
- Strategy Coverage@K

Diagnostics:
- Exclusive Perspective Coverage
- Gold gained / lost / net
- Branch Jaccard
- Duplicate candidate rate
- Candidate provenance
- Learned weight / score distribution

현재 Dev Query는 10개뿐이므로 과도한 통계적 일반화를 하지 않는다.
