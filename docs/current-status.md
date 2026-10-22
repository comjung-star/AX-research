# Current Research Status

기준일: **2026-10-22**

이 문서는 현재 저장소의 실험 진행상황을 한눈에 확인하기 위한 상태 문서다.
세부 명세와 원시 결과는 각 실험 문서를 기준으로 한다.

## 1. 현재 위치

~~~text
Stage 0   Dataset / Ground Truth                    ✅
Stage 1   Multi-Perspective value validation        ✅
Stage 2-1 Multi-view Equal                         ✅
Stage 2-2 Query-Conditioned Gated Fusion v1        ✅  → 미채택
Stage 2-3 Hybrid Retrieval Candidate Union v1      ✅  → 보완성 확인, 50:50 방식 우위 없음
Stage 2-4 Query-Case Interaction MLP v1            ✅  → 미채택
Stage 3   Factor Anchor / Wald Evidence             ← NEXT
Stage 4   Evidence Fusion / LLM Recommendation
Final     Held-out Test
~~~

**중요:** Stage 번호는 교수 제안 아키텍처의 공식 명칭이 아니라, 교수 아키텍처의 구성요소를 하나씩 검증하기 위해 본 연구에서 붙인 운영 단계명이다.

## 2. 데이터와 평가 기준

- Main Dataset: AX0001~AX0100, 총 100건
- Dev/Pilot Query: GTQ001~GTQ010, 총 10건
- Perspective × Case relevance: 총 3000 active labels
- Gold threshold: relevance >= 3
- K: 5 / 10 / 20
- Runtime 검색 입력: 각 Query의 business_problem_query
- Stage 1 이후 비교 실험은 가능한 한 동일 Generated Perspective를 replay해 LLM sampling 차이를 통제
- Dev 결과를 보고 Ground Truth를 사후 수정하지 않음
- 최종 논문 성능은 모델/평가규칙 Freeze 후 별도 Held-out Test에서 확인

## 3. Stage 1 — Multi-Perspective

| System | Recall@5 | Recall@10 | Recall@20 |
|---|---:|---:|---:|
| Single Dense | 0.3575 | 0.5176 | 0.6947 |
| Multi-Perspective Dense | 0.3233 | 0.5027 | 0.6565 |
| GPT-only | 0.4270 | 0.6650 | 0.8748 |

MP Dense vs Single Dense Gold gained/lost:
- @5: +23 / -35 / net -12
- @10: +24 / -33 / net -9
- @20: +34 / -46 / net -12

해석:
- 다중관점은 Single Dense가 놓친 새로운 Gold를 실제로 찾음.
- 그러나 제한된 Top-K 안에서 기존 Gold가 더 많이 밀려 전체 Recall은 개선되지 않음.
- 따라서 문제는 관점 생성 자체보다 후보 결합/정렬까지 포함한 전체 Search Core에서 해결해야 함.

## 4. Stage 2-1 — Multi-view Equal

Case의 Problem / Task / Context를 각각 BGE-M3로 임베딩하고 세 score를 1/3 : 1/3 : 1/3로 평균했다.

| System | Recall@5 | Recall@10 | Recall@20 |
|---|---:|---:|---:|
| Stage 1 MP Dense | 0.323267 | 0.502667 | 0.656546 |
| Multi-view Equal | 0.323467 | 0.499295 | 0.659976 |

판단:
- View 분리로 ranking 변화는 발생.
- 그러나 동일가중 분리만으로는 뚜렷한 개선 없음.
- **Equal Fusion은 이후 비교를 위한 안정적 통제군으로 유지.**

## 5. Stage 2-2 — Query-Conditioned Gated Fusion v1

구조: semantic-anchor similarity → Linear(3→3) → Softmax → View weights

| System | Recall@5 | Recall@10 | Recall@20 |
|---|---:|---:|---:|
| Equal Fusion | 0.323467 | 0.499295 | 0.659976 |
| Gated Fusion v1 | 0.309681 | 0.464334 | 0.655820 |

평균 learned weight:
- Problem 0.5998
- Task 0.0026
- Context 0.3976

판단:
- 동적 가중치가 실제로 생성되었지만 Task가 거의 0으로 collapse.
- Equal Fusion보다 @5/@10 성능 악화.
- **현재 Gate v1은 미채택.**
- Gated Fusion이라는 아키텍처 개념 자체를 삭제하는 것은 아님.

## 6. Stage 2-3 — Hybrid Retrieval Candidate Union v1

| 각 Retriever Top-N | Hybrid slots/branch | Hybrid Recall | Dense-only 동일 slots | Delta |
|---|---:|---:|---:|---:|
| 5 | 10 | 0.6191 | 0.6495 | -0.0304 |
| 10 | 20 | 0.7803 | 0.7935 | -0.0132 |
| 20 | 40 | 0.9164 | 0.9356 | -0.0192 |

Dense/Sparse branch Jaccard는 약 0.31~0.36.

판단:
- BM25는 Dense와 다른 후보를 가져오며 새로운 Gold도 추가함.
- 그러나 고정 50:50 slot 배분에서는 Dense depth 손실이 더 커 평균 Candidate Recall 우위가 없음.
- **Hybrid의 보완성은 확인했지만 현재 50:50 v1을 우수한 방식으로 채택하지 않음.**

## 7. Stage 2-4 — Query-Case Interaction v1

교수 제안 구조: [q,c,q⊙c,|q-c|] → MLP → Relevance Score

| leg_k | Final K | QCI MLP | Same-pool RRF | Delta |
|---:|---:|---:|---:|---:|
| 5 | 5 | 0.2435 | 0.3211 | -0.0776 |
| 10 | 10 | 0.3635 | 0.5060 | -0.1425 |
| 20 | 10 | 0.3335 | 0.5174 | -0.1839 |
| 20 | 20 | 0.5489 | 0.6932 | -0.1443 |

판단:
- 현재 10개 Dev Query와 Query-level Gold supervision에서는 QCI MLP v1이 일반화되지 않음.
- Same-pool RRF가 더 안정적.
- **QCI MLP v1은 미채택**, 교수 제안 Interaction 구성요소 자체는 아키텍처에 유지.

## 8. Stage 2 전체 결론

현재 데이터 규모에서는 복잡한 학습형 결합을 추가한다고 자동으로 성능이 좋아지지 않았다.

~~~text
Multi-Perspective
→ 새로운 Gold 탐색 효과 확인
→ Top-K 보존 문제 존재

Multi-view Equal
→ 거의 동일

Gated Fusion v1
→ 악화

Hybrid 50:50 Candidate Union
→ Dense/Sparse 보완성 확인
→ 동일 슬롯 Recall 우위 없음

QCI MLP v1
→ Same-pool RRF보다 악화
~~~

따라서 현재 결과를 숨기거나 사후 튜닝해서 맞추지 않고, 각 결과를 **구성요소 기여도 검증(ablation)**으로 보존한다.

## 9. 다음 단계 — Stage 3

~~~text
Retrieved Cases
→ Case Evidence Pooling
→ Root Cause Factor Anchor
→ Wald Evidence
→ Evidence Fusion
→ Strategy Recommendation
~~~

Stage 3에서 검증할 핵심:
1. 검색된 사례를 Root Cause Factor(F01~F09)에 안정적으로 연결할 수 있는가?
2. Factor ↔ Strategy 관계를 Wald 통계 Evidence로 표현할 수 있는가?
3. 단순 사례 목록보다 Strategy Coverage와 Evidence Traceability가 개선되는가?
4. Wald 결과를 인과관계가 아니라 연관성 근거로 올바르게 사용할 수 있는가?

Stage 3 설계 전에는 Stage 2 실패 구현을 억지로 결합하지 않는다.
현재 Dev에서는 안정적인 비학습 ranking reference를 사용해 Evidence 단계 자체의 효과를 분리 검증한다.

## 10. 결과 문서

- RQ1: experiments/rq1_retrieval/results/rq1_v1_3_llm_dev/DEV_RESULT_ANALYSIS.md
- Stage 2-1: experiments/rq2_multiview/results/stage2_multiview_v1/DEV_RESULT_ANALYSIS.md
- Stage 2-2: experiments/rq2_multiview/results/stage2_gated_v1/DEV_RESULT_ANALYSIS.md
- Stage 2-3: experiments/rq2_multiview/results/stage2_hybrid_v1/DEV_RESULT_ANALYSIS.md
- Stage 2-4: experiments/rq2_multiview/results/stage2_interaction_v1/DEV_RESULT_ANALYSIS.md
