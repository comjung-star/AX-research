# AX-research

기업 업무문제 기반 다중관점 AX 사례 검색·전략 추천 모델 연구

## Documents

- [연구계획서](docs/research-plan.md)
- [아키텍처 정리](docs/architecture.md)
- [실험 로드맵](docs/experiments.md)
- [RQ1 검색실험 명세 v1.3](docs/experiment-spec-rq1-v1.3.md)
- [Stage 2-1 Multi-view 실험 명세](docs/experiment-spec-stage2-multiview-v1.md)
- [Dev Ground Truth v1 Freeze](data/dev_ground_truth_freeze_v1.md)
- [RQ1 v1.3 Dev 결과 분석](experiments/rq1_retrieval/results/rq1_v1_3_llm_dev/DEV_RESULT_ANALYSIS.md)
- [Stage 2-1 Dev 결과 분석](experiments/rq2_multiview/results/stage2_multiview_v1/DEV_RESULT_ANALYSIS.md)
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

## Current Status — 2026-10-22

### 완료

- Main Dataset v1: **AX0001~AX0100 / 100건 Freeze**
- Dev/Pilot Query: **GTQ001~GTQ010 10건**
- Active Perspective × Case relevance: **3000 labels**
- Dev Ground Truth v1 Freeze
- RQ1 Experiment Spec **v1.3 Freeze**
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
- Exclusive Perspective Coverage diagnostic
- Single BM25 / Dense Dev baseline 실제 실행
- GPT-only 3-repeat Dev 실제 실행
- Multi-Perspective BM25 3-repeat Dev 실제 실행
- Multi-Perspective Dense 3-repeat Dev 실제 실행
- RQ1 v1.3 결과 저장 및 1차 분석
- **Stage 2-1 Multi-view Equal Dense 구현/실행**
- **Stage 1 Generated Perspective replay로 LLM sampling 통제**
- Problem / Task / Context별 BGE-M3 embedding 및 view score 기록

### 현재 단계

**Stage 2-1 Multi-view Dev 실행 완료 → Stage 2-2 Gated Fusion 설계/실험**

기존 Stage 1 Recall Macro:

| System | @5 | @10 | @20 |
|---|---:|---:|---:|
| Single BM25 | 0.3643 | 0.5119 | 0.6446 |
| Single Dense | 0.3575 | 0.5176 | 0.6947 |
| GPT-only | **0.4270** | **0.6650** | **0.8748** |
| Multi-Perspective BM25 | 0.3063 | 0.4464 | 0.6547 |
| Multi-Perspective Dense | 0.3233 | 0.5027 | 0.6565 |

Stage 2-1 비교:

| System | @5 | @10 | @20 |
|---|---:|---:|---:|
| Stage 1 MP Dense | 0.323267 | 0.502667 | 0.656546 |
| Stage 2-1 Multi-view Equal Dense | 0.323467 | 0.499295 | 0.659976 |
| Delta | +0.000200 | -0.003372 | +0.003430 |

Stage 2-1에서는 **View를 분리해 동일가중 평균한 것만으로는 의미 있는 Recall 개선이 확인되지 않았다.**
새 Gold와 lost Gold가 거의 상쇄되어, 단순 분리보다 Query/Perspective별 View 중요도 조정의 필요성이 남았다.

상세:
- `experiments/rq1_retrieval/results/rq1_v1_3_llm_dev/DEV_RESULT_ANALYSIS.md`
- `experiments/rq2_multiview/results/stage2_multiview_v1/DEV_RESULT_ANALYSIS.md`

현재 Frozen 실행 기준:
- `docs/experiment-spec-rq1-v1.3.md`
- `configs/experiment_rq1_v1.3.yaml`
- `docs/experiment-spec-stage2-multiview-v1.md`
- `configs/experiment_stage2_multiview_v1.yaml`

다음 단계:
- **Stage 2-2 Gated Fusion / Attention**
- Query/Perspective별 Problem / Task / Context 가중치 동적 조정
- 동일 Perspective replay / 동일 K / 동일 final selection 유지
- 학습형 Gate의 Query-level leakage 방지

Ground Truth와 Frozen 조건은 Dev 결과에 맞춰 사후 수정하지 않는다.
