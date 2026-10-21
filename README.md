# AX-research

기업 업무문제 기반 다중관점 AX 사례 검색·전략 추천 모델 연구

## Documents

- [연구계획서](docs/research-plan.md)
- [아키텍처 정리](docs/architecture.md)
- [실험 로드맵](docs/experiments.md)
- [RQ1 검색실험 명세 v1](docs/experiment-spec-rq1-v1.md)
- [Dev Ground Truth v1 Freeze](data/dev_ground_truth_freeze_v1.md)
- [작업일지](worklog/README.md)
- [학습용 쉬운 설명](study/README.md)

## Repository Structure

```text
AX-research/
├─ AGENTS.md
├─ README.md
├─ docs/          # 연구계획서, 아키텍처, 실험 명세/로드맵
├─ data/          # Dataset, Ground Truth, Freeze/Archive
├─ configs/       # 재현 가능한 실험 설정
├─ experiments/   # 실험별 실행기록·결과
├─ src/           # 실제 구현 코드
├─ tests/         # 평가/검색/데이터 변환 테스트
├─ notebooks/     # 탐색적 분석 및 시각화
├─ study/         # 학습용 쉬운 설명
└─ worklog/       # 날짜별 공식 작업일지
```

## Current Status — 2026-10-21

### 완료

- 교수 제안 아키텍처 기준 연구 방향 확정
- Main Dataset v1: **AX0001~AX0100 / 100건 Freeze**
- Root Cause Dictionary v1: **9종 Freeze**
- Strategy Taxonomy v1: **6종 Freeze**
- Dev/Pilot Query: **GTQ001~GTQ010 10건**
- Active Perspective × Case relevance: **3000 labels**
- Active Query 10/10: `PILOT_GOLD_ADJUDICATED`
- Low-discrimination / sparse 초기 Pilot Query는 Archive 보존
- **Dev Ground Truth v1 Freeze 완료**

### 현재 단계

**RQ1 Retrieval Experiment Implementation**

현재 실험의 핵심 질문:

> Single-query BM25 / Dense / GPT-only보다 LLM Multi-Perspective branch 검색이 관련 AX 사례의 Recall과 Perspective Coverage를 개선하는가?

현재 작성된 초안:
- `docs/experiment-spec-rq1-v1.md` — FROZEN
- `configs/experiment_rq1_v1.yaml` — FROZEN
- `experiments/rq1_retrieval/README.md`

사용자 검토를 완료했으며 이제 공통 평가기부터 구현을 시작한다.

### 다음 순서

1. RQ1 실험 명세 검토 및 Freeze ✅
2. 공통 Data Loader / Evaluation Engine 구현 ← 다음
3. Single-query BM25
4. Single-query Dense Retrieval
5. GPT-only
6. Multi-Perspective + BM25 diagnostic
7. Multi-Perspective + Dense primary Stage 1
8. Dev 결과 검토
9. Multi-view / Gated Fusion / Hybrid Retrieval 등 후속 단계
10. 모델·Prompt·평가규칙 Freeze 후 별도 Held-out Test
