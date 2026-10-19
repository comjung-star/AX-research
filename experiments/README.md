# Experiments

각 실험의 실행 설정과 결과 요약을 관리합니다.

각 실험에는 가능하면 다음 내용을 기록합니다.

- 실험 목적
- Dataset / Ground Truth version
- Model / configuration
- Baseline 또는 비교대상
- Search Budget / Top-K 조건
- Recall@K
- Perspective Coverage@K
- Strategy Coverage@K
- 결과 해석
- 다음 실험에서 변경할 사항

## 기본 Baseline

1. Single-query BM25
2. Single-query Dense Retrieval
3. GPT-only

이후 Multi-Perspective → Multi-view → Hybrid Retrieval → Query-Case Interaction → Factor Anchor/Wald → Evidence Fusion/Recommendation Head 순으로 단계별 효과를 검증합니다.
