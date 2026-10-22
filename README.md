# AX-research

기업 업무문제 기반 다중관점 AX 사례 검색·전략 추천 모델 연구

## Documents

- [연구계획서](docs/research-plan.md)
- [아키텍처 정리](docs/architecture.md)
- [실험 로드맵](docs/experiments.md)
- [RQ1 검색실험 명세 v1.3](docs/experiment-spec-rq1-v1.3.md)
- [Dev Ground Truth v1 Freeze](data/dev_ground_truth_freeze_v1.md)
- [RQ1 v1.3 Dev 결과 분석](experiments/rq1_retrieval/results/rq1_v1_3_llm_dev/DEV_RESULT_ANALYSIS.md)
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
- GitHub Actions unit test
- Single BM25 / Dense Dev baseline 실제 실행
- GPT-only 3-repeat Dev 실제 실행
- Multi-Perspective BM25 3-repeat Dev 실제 실행
- Multi-Perspective Dense 3-repeat Dev 실제 실행
- RQ1 v1.3 결과 저장 및 1차 분석

### 현재 단계

**RQ1 Stage 1 Dev 실행 완료 → Dev Result Review**

Recall Macro:

| System | @5 | @10 | @20 |
|---|---:|---:|---:|
| Single BM25 | 0.3643 | 0.5119 | 0.6446 |
| Single Dense | 0.3575 | 0.5176 | 0.6947 |
| GPT-only | **0.4270** | **0.6650** | **0.8748** |
| Multi-Perspective BM25 | 0.3063 | 0.4464 | 0.6547 |
| Multi-Perspective Dense | 0.3233 | 0.5027 | 0.6565 |

현재 Dev에서는 **Multi-Perspective Dense의 평균 Recall이 Single Dense보다 높지 않았다.**
다만 Exclusive Perspective Coverage@20은 Single Dense 0.7333 대비 MP Dense 0.8389로 높아 관점 고유 사례 회수 신호가 확인됐다.

상세:
- `experiments/rq1_retrieval/results/rq1_v1_3_llm_dev/DEV_RESULT_ANALYSIS.md`

현재 Frozen 실행 기준:
- `docs/experiment-spec-rq1-v1.3.md`
- `configs/experiment_rq1_v1.3.yaml`

다음 단계:
- Query별 개선/악화 원인 분석
- Perspective 품질 / branch Gold 분포 분석
- branch-balanced unique의 Gold loss 원인 분석
- Multi-view / Gated Fusion / Hybrid Retrieval 단계 진행 판단

Ground Truth와 Frozen v1.3 조건은 Dev 결과에 맞춰 사후 수정하지 않는다.
