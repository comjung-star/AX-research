# Current Research Status

기준일: **2026-10-22**

이 문서는 현재 저장소의 실험 진행상황을 한눈에 확인하기 위한 상태 문서다.
세부 명세와 원시 결과는 각 실험 문서를 기준으로 한다.

> **2026-10-22 DATA QUALITY HOLD (v2 재구축 우선):** 100건 v1의 사례 단위가 연구 목적의 '하나의 독립 업무문제와 실제 AX 해결'을 반드시 보장하지 않는 것으로 확인. 기존 v1/Dev/Stage 1~3 결과는 이력용으로 보존하지만 **Stage 3-2B와 신규 추천 실험을 잠정 중단**함. 별도 [v2 staging 현황](data-v2-staging-2026-10-22.md): 보류 6건 분리, 94건 부모 후보, 19건에서 38개 분할 초안(미확정), 원천 1차 재검토 24건, 승인 완료 0건. 자세한 사례별 검토는 [data audit](data-audit-main-v1-2026-10-22.md) 참조. 본 상태는 **PR #3 Draft 브랜치에만 존재**하며 main의 v1 연구기록은 보존된다.

## 1. 현재 위치

~~~text
Stage 0   Dataset / Ground Truth                    ✅ v1 historical / v2 reconstructing
Stage 1   Multi-Perspective value validation        ✅
Stage 2-1 Multi-view Equal                         ✅
Stage 2-2 Query-Conditioned Gated Fusion v1        ✅  → 미채택
Stage 2-3 Hybrid Retrieval Candidate Union v1      ✅  → 보완성 확인, 50:50 방식 우위 없음
Stage 2-4 Query-Case Interaction MLP v1            ✅  → 미채택
Stage 3-1 Factor ↔ Strategy Wald offline Dev        ✅  → 통계 진단 완료
Stage 3-2A Multi-Perspective provenance Dev           ✅  → 300 Cases / 641 branch links
Stage 3-2B Factor / Wald evidence trace             ⏸ data quality gate
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

## 9. 다음 단계 — Stage 3-2B / 3-2C

~~~text
Retrieved Cases
→ Case Evidence Pooling
→ Root Cause Factor Anchor
→ Wald Evidence
→ Evidence Fusion
→ Strategy Recommendation
~~~

Stage 3-2에서 검증할 핵심:
1. 검색된 사례를 Root Cause Factor(F01~F09)에 안정적으로 연결할 수 있는가?
2. Factor ↔ Strategy 관계를 Wald 통계 Evidence로 표현할 수 있는가?
3. 단순 사례 목록보다 Strategy Coverage와 Evidence Traceability가 개선되는가?
4. Wald 결과를 인과관계가 아니라 연관성 근거로 올바르게 사용할 수 있는가?

Stage 3-2 설계 전에는 Stage 2 실패 구현을 억지로 결합하지 않는다.
현재 Dev에서는 안정적인 비학습 ranking reference를 사용해 Evidence 단계 자체의 효과를 분리 검증한다.

## 10. Stage 3-1 — Offline Wald Evidence (Dev)

Workflow 39734864597: SUCCESS / Wald-specific unit tests 5 passed.
기존 전체 회귀 테스트 Workflow 39734864578: SUCCESS.

Frozen Case 100건에서 Root Cause 9종 × Strategy 6종 = 54개의
Case-level association을 분석했다.

- Wald cell eligibility (all a,b,c,d >= 5): 35 pairs
- Sparse/insufficient (any cell < 5): 19 pairs, Wald inference abstained
- BH-adjusted q<0.05 among eligible: 6 pairs
- 결과는 **univariate, observational, descriptive Dev evidence**이며, 인과 효과·추천 정확도 또는 Held-out 성능이 아니다.
- Offline Case→Factor→Strategy trace 생성. 실제 Query Case Evidence/Factor alignment와 Strategy Coverage 개선은 아직 미검증이다.
- 비교군으로서의 RRF와 제안 아키텍처의 Interaction 구성요소를 혼동하지 않는다.

분석: [Stage 3-1 Dev Analysis](../experiments/rq3_evidence/results/stage3_wald_v1/DEV_RESULT_ANALYSIS.md)

## 11. 결과 문서

- RQ1: experiments/rq1_retrieval/results/rq1_v1_3_llm_dev/DEV_RESULT_ANALYSIS.md
- Stage 2-1: experiments/rq2_multiview/results/stage2_multiview_v1/DEV_RESULT_ANALYSIS.md
- Stage 2-2: experiments/rq2_multiview/results/stage2_gated_v1/DEV_RESULT_ANALYSIS.md
- Stage 2-3: experiments/rq2_multiview/results/stage2_hybrid_v1/DEV_RESULT_ANALYSIS.md
- Stage 2-4: experiments/rq2_multiview/results/stage2_interaction_v1/DEV_RESULT_ANALYSIS.md

## 12. Stage 3-2A — Perspective Provenance replay (Dev)

- 프로토콜: [Stage 3-2A 동결 명세](experiment-spec-stage3-perspective-provenance-v1.md)
- GitHub Actions: 39743868005 — SUCCESS (초점 단위테스트 및 Dev 재생 실행), 기존 전체 회귀 테스트 39743867801 — SUCCESS.
- `stage2_same_pool_rrf`의 `leg_k=10`, Top-10, 10질의 × 3반복: 검색 사례 출현 300건.
- 원본 Hybrid candidate provenance를 통해 관점별 링크 **641건** 복원(대표 관점 외 추가 링크 341건).
- 다중관점으로 발견된 검색 사례 출현 **220/300 = 73.3%**. 1개 관점 80건 / 2개 110건 / 3개 99건 / 4개 11건.
- 관점별 링크 수 P1=211 / P2=203 / P3=207 / P4=20 (Case 수가 아닌 관점별 링크 수).
- 선택 관점 보존 300/300, 원본 후보 누락 0, 검색 결과 순위 및 Case 수 불변.
- 이 단계는 검색·추천 성능 개선이 아니라 **구조적 관점 출처 복원**만 입증한다. RRF는 제안 모델이 아닌 진단용 고정 비교군이다.
- 분석: [Stage 3-2A Dev 결과](../experiments/rq3_evidence/results/stage3_provenance_v1/DEV_RESULT_ANALYSIS.md).
- 다음은 Stage 3-2B: Blind RCA Factor 및 Offline Wald 근거를 **결과 재정렬 없이** 연결한다.
