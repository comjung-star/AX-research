# AX-research

기업 업무문제 기반 다중관점 AX 사례 검색·전략 추천 모델 연구

## 가장 먼저 볼 문서

- [현재 연구 상태](docs/current-status.md)
- [연구계획서](docs/research-plan.md)
- [아키텍처](docs/architecture.md)
- [실험 로드맵](docs/experiments.md)

## Experiment Specs

- [RQ1 v1.3](docs/experiment-spec-rq1-v1.3.md)
- [Stage 2-1 Multi-view](docs/experiment-spec-stage2-multiview-v1.md)
- [Stage 2-2 Gated Fusion](docs/experiment-spec-stage2-gated-v1.md)
- [Stage 2-3 Hybrid Retrieval](docs/experiment-spec-stage2-hybrid-v1.md)
- [Stage 2-4 Query-Case Interaction](docs/experiment-spec-stage2-interaction-v1.md)

- [Stage 3-2A Provenance freeze](docs/experiment-spec-stage3-perspective-provenance-v1.md)

## Result Analyses

- [RQ1 Dev](experiments/rq1_retrieval/results/rq1_v1_3_llm_dev/DEV_RESULT_ANALYSIS.md)
- [Stage 2-1 Dev](experiments/rq2_multiview/results/stage2_multiview_v1/DEV_RESULT_ANALYSIS.md)
- [Stage 2-2 Dev](experiments/rq2_multiview/results/stage2_gated_v1/DEV_RESULT_ANALYSIS.md)
- [Stage 2-3 Dev](experiments/rq2_multiview/results/stage2_hybrid_v1/DEV_RESULT_ANALYSIS.md)
- [Stage 2-4 Dev](experiments/rq2_multiview/results/stage2_interaction_v1/DEV_RESULT_ANALYSIS.md)
- [Stage 3-2A Provenance Dev](experiments/rq3_evidence/results/stage3_provenance_v1/DEV_RESULT_ANALYSIS.md)

## Current Status — 2026-10-22

~~~text
Dataset / Dev GT                         ✅
Stage 1 Multi-Perspective                ✅
Stage 2-1 Multi-view Equal               ✅
Stage 2-2 Gated Fusion v1                ✅ (미채택)
Stage 2-3 Hybrid Candidate Union v1      ✅ (보완성 확인)
Stage 2-4 Query-Case Interaction v1      ✅ (미채택)
Stage 3-1 Factor–Strategy Wald Dev        ✅
Stage 3-2A Perspective lineage replay     ✅
Stage 3-2B Factor/Wald trace              ← NEXT
~~~

Stage 2 Search Core의 구성요소별 Dev 검증은 완료했다.
현재 데이터 규모에서는 학습형 Gate와 QCI MLP v1의 일반화 이득이 확인되지 않았고, Hybrid Retrieval은 Dense와 Sparse의 후보 보완성은 확인했지만 고정 50:50 배분에서 same-slot Dense-only를 넘지 못했다.

Stage 3-1의 Offline Wald 관계 진단과 Stage 3-2A의 다중관점 검색 경로 복원(Top-10 검색 사례 300건, 관점별 링크 641건)까지 Dev 검증했다. 이는 **아직 전략 추천 성능 개선을 입증한 것은 아니다.**

교수 제안 아키텍처의 구성요소는 삭제하지 않는다.
효과가 확인되지 않은 **현재 v1 구현만 미채택**으로 기록하고 다음 단계에서 Factor Anchor / Wald Evidence를 검증한다.

세부 수치와 채택 판단은 [현재 연구 상태](docs/current-status.md)를 기준으로 한다.

## Data

- Main Dataset v1: AX0001~AX0100 / 100 cases
- Dev/Pilot Query: GTQ001~GTQ010 / 10 queries
- Active Perspective × Case relevance: 3000 labels
- Dev Ground Truth v1 Freeze
- Gold threshold: relevance >= 3

## Repository Structure

~~~text
AX-research/
├─ README.md
├─ docs/
├─ data/
├─ configs/
├─ experiments/
├─ src/
├─ tests/
├─ study/
└─ worklog/
~~~

Ground Truth와 Frozen 실험조건은 Dev 결과에 맞춰 사후 수정하지 않는다.
