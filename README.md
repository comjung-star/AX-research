# AX-research

## 다음 대화에서 이어받기 · 2026-10-26

**[인수인계 시작 문서: HANDOFF.md](HANDOFF.md)** — 사용자 최종 범위 변경, 전체 데이터·원천 확인 결과, 코드 위치, 실행 명령과 남은 작업을 정리했습니다. v2.5 전체 등록본은 11,766개 기록이고 검색 대상은 9,416개입니다. **전체 Dense 인덱스 생성과 실제 앱 전환은 아직 남아 있으며 현재 실행 화면은 108개 버전입니다.** 저장소 main 대신 `handoff/ax-inclusive-20261026` 브랜치를 확인하세요.

**2026-10-26 사례 확장 적용:** 기존 frozen 84개를 보존하고 원문 검토 신규 24개를 추가한 **108개 코퍼스**를 기본 Dense 검색에 연결했습니다. 수집 기록의 포함·제외·보류 원장과 미판정 평가표를 별도로 제공합니다. [적용 결과·남은 검토·재현 방법](data/v2_4/README.md).

## 실행 가능한 AX 사례 추천 프로토타입 · 2026-10-24

바탕화면의 **AX나침반.exe**를 실행하면 한국어 웹 화면이 열립니다. 키 없이 10개 예시의 저장된 LLM 관점과 실제 BGE-M3 Dense 계산을 시연하고, 관점별 사례 평가와 자유의견을 저장·내보낼 수 있습니다.

**10월 25일 업데이트:** 실제 API 연결 시 **기업의 해결 방식 → 우리 업무의 적용 전략·실행 순서·준비사항·한계**까지 생성합니다. 키 없는 전략 시연도 제공하며 실제 AI 작성과 구분합니다. [전략 출력 결과와 시연 순서](docs/prototype-strategy-demo-2026-10-25.md).

- [실행·시연·테스트 안내](docs/prototype-demo-guide-2026-10-24.md)
- [구현·검증 결과](docs/prototype-delivery-2026-10-24.md)
- 직접 실행: `python run_prototype.py` → `http://127.0.0.1:8765`
- 원본 84개 frozen 사례, 기존 관점·임베딩·실험결과는 읽기 전용으로 사용합니다.

> **AX Dataset v2.1 (2026-10-22):** 연구자가 실제 운영업무 **91건**을 최종 연구 코퍼스로 고정했습니다. 추가 보류 7건은 제외 원장으로 보존했습니다. **인간 Ground Truth가 아니며** 새로운 RQ1/Stage 3 성능평가는 아직 측정되지 않았습니다. [데이터 진입점](data/v2_1/README.md) · [정식 종합 보고서](docs/v21-freeze-and-experiment-report-2026-10-22.md).\n\n
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
