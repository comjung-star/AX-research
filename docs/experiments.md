# Experiment Plan

구성요소를 한 번에 모두 구현하지 않고 단계별로 효과를 검증합니다.

## 권장 진행 순서

1. Dataset / Retrieval Ground Truth 준비
2. Single-query BM25 baseline
3. Single-query Dense Retrieval baseline
4. GPT-only baseline
5. Multi-Perspective Query
6. Multi-view Embedding
7. View Combination
8. Hybrid Retrieval
9. Query-Case Interaction
10. Factor Anchor / Wald Evidence
11. Evidence Fusion / Recommendation Head
12. Ablation 및 최종 평가

## Ground Truth 원칙

- Main Dataset v1 `AX0001~AX0100`을 고정하여 사용합니다.
- 평가 Query와 Gold Label은 모델 검색결과와 분리된 절차로 구축합니다.
- Query별 Gold Perspective를 별도로 유지합니다.
- Perspective × Case 관련도는 0~4 척도로 기록하고, Gold threshold는 Ground Truth protocol에서 사전에 고정합니다.
- Retrieval 관련도 판정은 Problem View를 중심으로 하여 Solution View 누출을 최소화합니다.
- Gold Relevant Cases 확정 후 frozen Strategy taxonomy를 이용해 Gold Strategy Set을 구성합니다.

## 핵심 평가 지표

- `Recall@K`
- `Perspective Coverage@K`
- `Strategy Coverage@K`

Baseline과 제안모델은 동일한 Search Budget / 출력 건수 조건에서 비교합니다.
