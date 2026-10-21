# Experiment Plan

구성요소를 한 번에 모두 구현하지 않고 단계별로 효과를 검증합니다.

## 현재 RQ1 실행 명세

- Frozen specification: `docs/experiment-spec-rq1-v1.2.md`
- Frozen config: `configs/experiment_rq1_v1.2.yaml`
- Dev Ground Truth Freeze: `data/dev_ground_truth_freeze_v1.md`

v1.2의 핵심 추가 결정:
- 공통 LLM: `gpt-6-luna`
- Multi-Perspective branch query: **Perspective only**
- Original Business Problem은 Perspective 생성에만 사용하고 branch 검색에는 다시 넣지 않음

## RQ1 Stage 1 구현 상태

1. Dataset / Retrieval Ground Truth 준비 ✅
2. RQ1 Experiment Spec Freeze ✅
3. Common Evaluation Engine ✅
4. Single-query BM25 baseline ✅
5. Single-query Dense Retrieval baseline ✅
6. GPT-only baseline ✅
7. Multi-Perspective + BM25 diagnostic ✅
8. Multi-Perspective + Dense ✅
9. Common Diagnostics / Summary ✅
10. Dev 실행 ← 현재
11. Dev Result Review
12. Next-stage Multi-view / Gated Fusion / Hybrid Retrieval

## Ground Truth 원칙

- `GTQ001~GTQ010`은 Dev/Pilot Query로 사용하며 최종 Test Query와 분리합니다.
- Main Dataset v1 `AX0001~AX0100`을 고정하여 사용합니다.
- Perspective × Case 관련도는 0~4, Gold threshold는 >=3입니다.
- Retrieval 관련도 판정은 Problem View 중심입니다.
- Ground Truth는 Runtime LLM 입력으로 사용하지 않습니다.
- Held-out Test는 모델·Prompt·평가규칙 Freeze 후 별도로 구축합니다.

## 핵심 평가 지표

- `Recall@K`
- `Perspective Coverage@K`
- `Strategy Coverage@K`

진단:
- Branch pairwise Jaccard
- Duplicate candidate rate
- Gold gained / lost / net
- Generated Perspective count
- 3회 반복 Run의 평균/최소/최대/표준편차

Dev 결과는 방향성/실패사례 분석용이며, 10개 Query만으로 과도한 통계적 일반화를 하지 않습니다.
