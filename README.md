# AX-research

기업 업무문제 기반 다중관점 AX 사례 검색·전략 추천 모델 연구

## Documents

- [연구계획서](docs/research-plan.md)
- [아키텍처 정리](docs/architecture.md)
- [실험 로드맵](docs/experiments.md)
- [RQ1 검색실험 명세 v1.3](docs/experiment-spec-rq1-v1.3.md)
- [Stage 2-1 Multi-view 실험 명세](docs/experiment-spec-stage2-multiview-v1.md)
- [Stage 2-2 Gated Fusion 실험 명세](docs/experiment-spec-stage2-gated-v1.md)
- [Stage 2-3 Hybrid Retrieval 실험 명세](docs/experiment-spec-stage2-hybrid-v1.md)
- [Stage 2-4 Query-Case Interaction 실험 명세](docs/experiment-spec-stage2-interaction-v1.md)
- [Dev Ground Truth v1 Freeze](data/dev_ground_truth_freeze_v1.md)
- [RQ1 v1.3 Dev 결과 분석](experiments/rq1_retrieval/results/rq1_v1_3_llm_dev/DEV_RESULT_ANALYSIS.md)
- [Stage 2-1 Dev 결과 분석](experiments/rq2_multiview/results/stage2_multiview_v1/DEV_RESULT_ANALYSIS.md)
- [Stage 2-2 Dev 결과 분석](experiments/rq2_multiview/results/stage2_gated_v1/DEV_RESULT_ANALYSIS.md)
- [Stage 2-3 Dev 결과 분석](experiments/rq2_multiview/results/stage2_hybrid_v1/DEV_RESULT_ANALYSIS.md)
- [Stage 2-4 Dev 결과 분석](experiments/rq2_multiview/results/stage2_interaction_v1/DEV_RESULT_ANALYSIS.md)
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
- **Stage 2-2 Query-Conditioned Gated Fusion LOQO 구현/실행**
- Query 단위 Leave-One-Out으로 Gate 학습/평가 누수 방지
- **Stage 2-3 Dense + Sparse Candidate Union 구현/실행**
- 동일 retrieval slot budget 기준 Hybrid vs Dense-only Candidate Recall 비교
- **Stage 2-4 Query-Case Interaction LOQO 구현/실행**
- `[q,c,q⊙c,|q-c|] → MLP`과 same-pool RRF 비교

### 현재 단계

**Stage 2 Search Core 구성요소별 Dev 검증 완료 → Stage 3 Factor Anchor / Wald Evidence 준비**

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

Stage 2-2에서는 Query/Perspective에 따라 View weight를 학습하는 12-parameter Gate를
Query-level LOQO로 평가했다.

| System | @5 | @10 | @20 |
|---|---:|---:|---:|
| Stage 1 MP Dense | 0.323267 | 0.502667 | 0.656546 |
| Stage 2-1 Equal Fusion | 0.323467 | 0.499295 | 0.659976 |
| Stage 2-2 Gated Fusion | 0.309681 | 0.464334 | 0.655820 |

Equal Fusion 대비 Stage 2-2 Delta:
- @5: -0.013785
- @10: -0.034962
- @20: -0.004156

학습된 평균 View weight:
- Problem: 0.5998
- Task: 0.0026
- Context: 0.3976

현재 v1 Gate는 Task View를 거의 제거하는 방향으로 수렴했고 @5/@10 Recall이 악화됐다.
따라서 **현재 Gated Fusion v1은 채택하지 않고**, 결과를 ablation으로 보존한 뒤
다음 구성요소인 Hybrid Retrieval을 검증한다.

상세:
- `experiments/rq1_retrieval/results/rq1_v1_3_llm_dev/DEV_RESULT_ANALYSIS.md`
- `experiments/rq2_multiview/results/stage2_multiview_v1/DEV_RESULT_ANALYSIS.md`
- `experiments/rq2_multiview/results/stage2_gated_v1/DEV_RESULT_ANALYSIS.md`

현재 Frozen 실행 기준:
- `docs/experiment-spec-rq1-v1.3.md`
- `configs/experiment_rq1_v1.3.yaml`
- `docs/experiment-spec-stage2-multiview-v1.md`
- `configs/experiment_stage2_multiview_v1.yaml`
- `docs/experiment-spec-stage2-gated-v1.md`
- `configs/experiment_stage2_gated_v1.yaml`

Stage 2-3 Hybrid Candidate Recall:

| 각 Retriever Top-N | Hybrid slots/branch | Hybrid Recall | Dense-only 동일 slots | Delta |
|---|---:|---:|---:|---:|
| 5 | 10 | 0.6191 | 0.6495 | -0.0304 |
| 10 | 20 | 0.7803 | 0.7935 | -0.0132 |
| 20 | 40 | 0.9164 | 0.9356 | -0.0192 |

Hybrid는 새로운 Gold를 추가로 찾았지만 같은 검색 슬롯 예산에서는 lost Gold가 더 많아
평균 Candidate Recall 개선으로 이어지지 않았다. 다만 Dense/Sparse branch Jaccard가
약 0.31~0.36으로 낮아 **서로 다른 후보를 가져오는 보완성 자체는 확인**됐다.

다음 단계:
- **Stage 2-4 Query-Case Interaction**
- Hybrid Candidate Pool 안에서 실제 관련도가 높은 Case를 재평가/정렬
- Stage 2-3의 candidate provenance를 그대로 보존해 Sparse가 추가한 후보의 최종 기여 확인

Ground Truth와 Frozen 조건은 Dev 결과에 맞춰 사후 수정하지 않는다.


### Stage 2-4 Query-Case Interaction 결과

같은 Hybrid Candidate Pool에서 QCI MLP와 RRF를 비교했다.

| leg_k | Final K | QCI MLP | Same-pool RRF | Delta |
|---:|---:|---:|---:|---:|
| 5 | 5 | 0.2435 | 0.3211 | -0.0776 |
| 5 | 10 | 0.4281 | 0.4769 | -0.0488 |
| 10 | 5 | 0.2194 | 0.3164 | -0.0970 |
| 10 | 10 | 0.3635 | 0.5060 | -0.1425 |
| 10 | 20 | 0.5853 | 0.6860 | -0.1007 |
| 20 | 5 | 0.2044 | 0.3199 | -0.1155 |
| 20 | 10 | 0.3335 | 0.5174 | -0.1839 |
| 20 | 20 | 0.5489 | 0.6932 | -0.1443 |

현재 QCI MLP v1은 same-pool RRF보다 낮아 **채택하지 않는다**.
교수 제안 Query-Case Interaction 구성요소 자체를 삭제하는 것이 아니라,
현재 10개 Dev Query와 Query-level Gold supervision에서 구현한 v1을 failed ablation으로 보존한다.

다음 단계:
- **Stage 3 Factor Anchor / Wald Evidence**
- Search Core 결과를 근거 단계로 연결
- 현재 Dev에서는 안정적인 ranking reference를 사용하고, QCI v1 실패 결과는 별도 보존
