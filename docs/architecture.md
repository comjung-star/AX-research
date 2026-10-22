# Architecture

이 문서는 연구 아키텍처를 구현 관점에서 정리한다.

기준 문서: [연구계획서](research-plan.md)

## 교수 제안 기준 흐름

~~~text
Business Problem Query
→ LLM Query Understanding
→ Multi-view Embedding
→ View Combination
→ Hybrid Retrieval
→ Query-Case Interaction
→ Perspective-specific Top-K Cases
→ Case Evidence Pooling
→ Root Cause Factor Anchor
→ Wald Evidence
→ Evidence Fusion
→ LLM Reasoning & Recommendation Head
~~~

교수 제안 아키텍처의 큰 흐름은 유지하고, 세부 구현은 단계별 실험으로 검증한다.

## 현재 Dev 검증 상태

| Architecture Component | 운영 단계 | v1 결과 | 현재 처리 |
|---|---|---|---|
| LLM Multi-Perspective | Stage 1 | 신규 Gold 탐색 효과, 총 Recall 우위 없음 | 유지 / 개선 대상 |
| Multi-view Embedding | Stage 2-1 | Equal Fusion 거의 동일 | 통제군으로 유지 |
| Gated Fusion / Attention | Stage 2-2 | Gate v1 악화 | v1 미채택, 개념 유지 |
| Hybrid Retrieval | Stage 2-3 | Dense/Sparse 보완성 확인, 50:50 우위 없음 | 개념 유지, v1 결과 보존 |
| Query-Case Interaction | Stage 2-4 | MLP v1이 RRF보다 낮음 | v1 미채택, 개념 유지 |
| Factor Anchor | Stage 3 | 미실행 | 다음 검증 |
| Wald Evidence | Stage 3 | 미실행 | 다음 검증 |
| Evidence Fusion | Stage 3~4 | 미실행 | 예정 |
| LLM Recommendation Head | Stage 4 | 미실행 | 예정 |

**주의:** Stage 2-1~2-4는 교수 아키텍처의 공식 명칭이 아니라, 각 구성요소의 기여도를 분리해서 확인하기 위한 본 연구의 실험 운영 단계다.

현재 세부 상태는 [Current Research Status](current-status.md)를 기준으로 한다.
