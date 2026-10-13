# Experiment Plan

구성요소를 한 번에 모두 구현하지 않고 단계별로 효과를 검증합니다.

## 권장 진행 순서

1. Dataset / Ground Truth 준비
2. Single-query Dense Retrieval baseline
3. Multi-Perspective Query
4. Multi-view Embedding
5. View Combination
6. Hybrid Retrieval
7. Query-Case Interaction
8. Factor Anchor / Wald Evidence
9. Evidence Fusion / Recommendation Head
10. Ablation 및 최종 평가

핵심 평가 지표는 `Recall@K`, `Strategy Coverage@K`를 중심으로 합니다.
