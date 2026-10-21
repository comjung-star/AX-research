# AX-research

기업 업무문제 기반 다중관점 AX 사례 검색·전략 추천 모델 연구

## Documents

- [연구계획서](docs/research-plan.md)
- [아키텍처 정리](docs/architecture.md)
- [실험 로드맵](docs/experiments.md)
- [RQ1 검색실험 명세 v1.2](docs/experiment-spec-rq1-v1.2.md)
- [Dev Ground Truth v1 Freeze](data/dev_ground_truth_freeze_v1.md)
- [작업일지](worklog/README.md)
- [학습용 쉬운 설명](study/README.md)

## Repository Structure

```text
AX-research/
├─ AGENTS.md
├─ README.md
├─ docs/
├─ data/
├─ configs/
├─ experiments/
├─ src/
├─ tests/
├─ notebooks/
├─ study/
└─ worklog/
```

## Current Status — 2026-10-21

### 완료

- Main Dataset v1: **AX0001~AX0100 / 100건 Freeze**
- Dev/Pilot Query: **GTQ001~GTQ010 10건**
- Active Perspective × Case relevance: **3000 labels**
- Dev Ground Truth v1 Freeze
- RQ1 Experiment Spec **v1.2 Freeze**
- Common Data Loader / Evaluation Engine
- Single-query BM25 (Kiwi)
- Single-query Dense (BAAI/bge-m3)
- GPT-only runner (gpt-6-luna)
- Perspective Generator (gpt-6-luna)
- Multi-Perspective + BM25
- Multi-Perspective + Dense
- branch-balanced unique selection
- Perspective-only branch query rule
- Branch overlap / duplicate candidate diagnostics
- Gold gained / lost / net diagnostics
- 반복 Run summary
- GitHub Actions unit test

### 현재 단계

**RQ1 Stage 1 구현 완료 → Dev 실행 준비**

Primary Multi-Perspective 흐름:

```text
Business Problem
→ gpt-6-luna Perspective 2~5개 생성
→ 각 Perspective title + description만 branch 검색
→ BM25 또는 BGE-M3
→ branch-balanced unique Top-K
→ Recall / Perspective Coverage / Strategy Coverage
```

현재 Frozen 실행 기준:
- `docs/experiment-spec-rq1-v1.2.md`
- `configs/experiment_rq1_v1.2.yaml`

다음 단계는 실제 Dev 실행이다.
LLM 기반 실험에는 `OPENAI_API_KEY`가 필요하며 Secret은 Git에 저장하지 않는다.
