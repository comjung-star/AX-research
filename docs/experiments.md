# Experiment Plan

구성요소를 한 번에 모두 구현하지 않고 단계별로 효과를 검증합니다.

## 현재 RQ1 실행 명세

- Frozen specification: `docs/experiment-spec-rq1-v1.md`
- Frozen config: `configs/experiment_rq1_v1.yaml`
- Dev Ground Truth Freeze: `data/dev_ground_truth_freeze_v1.md`

명세 v1은 2026-10-21 Freeze 완료. 이후 구현·실행은 frozen config를 기준으로 하며, 보완이 필요하면 v1.1 또는 v2로 버전 관리한다.

## 권장 진행 순서

1. Dataset / Retrieval Ground Truth 준비 ✅
2. RQ1 Experiment Spec Freeze ✅
3. Common Evaluation Engine ← 현재
4. Single-query BM25 baseline
5. Single-query Dense Retrieval baseline
6. GPT-only baseline
7. Multi-Perspective + BM25 diagnostic
8. Multi-Perspective + Dense
9. Multi-view Embedding
10. View Combination
11. Hybrid Retrieval
12. Query-Case Interaction
13. Factor Anchor / Wald Evidence
14. Evidence Fusion / Recommendation Head
15. Ablation 및 최종 평가

## Ground Truth 원칙

- `GTQ001~GTQ010`은 Dev/Pilot Query로 사용하며 최종 Test Query와 분리합니다.
- 최종 Held-out Test Query는 모델·Prompt·평가규칙을 Freeze한 뒤 별도로 생성하고, Test 결과를 보고 모델을 다시 조정하지 않습니다.
- Main Dataset v1 `AX0001~AX0100`을 고정하여 사용합니다.
- 평가 Query와 Gold Label은 모델 검색결과와 분리된 절차로 구축합니다.
- Query별 Reference Perspective를 별도로 유지하되 가능한 모든 관점의 폐쇄형 목록으로 간주하지 않습니다.
- Runtime LLM은 Query마다 관점의 수와 종류를 동적으로 생성합니다.
- Perspective × Case 관련도는 0~4, Gold threshold는 >=3으로 v1에서 Freeze되어 있습니다.
- Retrieval 관련도 판정은 Problem View 중심입니다.
- Gold Relevant Cases 확정 후 frozen Strategy taxonomy로 Gold Strategy Set을 구성합니다.

## 핵심 평가 지표

- `Recall@K`
- `Perspective Coverage@K`
- `Strategy Coverage@K`

Baseline과 제안모델은 동일한 최종 Output Budget 조건에서 비교하며, Multi-Perspective의 branch별 추가 회수와 overlap도 별도로 진단합니다.

## 평가 데이터 분리

```text
Dev/Pilot Query (GTQ001~GTQ010)
→ Ground Truth / Prompt / 모델 설계 검증
→ 모델·평가규칙 Freeze
→ 별도 Held-out Test Query + Ground Truth Freeze
→ 최종 평가
```

Test 결과를 본 뒤 모델을 수정해야 한다면 해당 Query는 Dev로 이동시키고 새로운 Held-out Test를 준비합니다.

## Current milestone

As of 2026-10-21:
- Main Dataset v1 frozen
- Dev Ground Truth v1 frozen
- GTQ001~GTQ010 active Dev/Pilot queries adjudicated
- 3000 active Perspective × Case relevance labels
- RQ1 experiment specification draft created
