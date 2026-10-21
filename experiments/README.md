# Experiments

각 실험의 실행 설정과 결과 요약을 관리합니다.

## 현재 단계

RQ1 Retrieval Experiment 준비:
- [RQ1 Retrieval 실험영역](rq1_retrieval/README.md)
- 명세: `docs/experiment-spec-rq1-v1-draft.md`
- 설정: `configs/experiment_rq1_v1_draft.yaml`

## 실험 기록 원칙

각 실험에는 가능하면 다음 내용을 기록합니다.

- 실험 목적
- Dataset / Ground Truth version
- Git commit SHA
- Model / configuration
- Prompt version/hash
- Baseline 또는 비교대상
- Search Budget / Top-K 조건
- Recall@K
- Perspective Coverage@K
- Strategy Coverage@K
- branch overlap / unique Gold recovery 같은 진단값
- 결과 해석
- 다음 실험에서 변경할 사항

## 기본 비교

1. Single-query BM25
2. Single-query Dense Retrieval
3. GPT-only
4. Multi-Perspective + BM25 (diagnostic)
5. Multi-Perspective + Dense (primary Stage 1)

이후 Multi-view → Gated Fusion → Hybrid Retrieval → Query-Case Interaction → Factor Anchor/Wald → Evidence Fusion/Recommendation Head 순으로 단계별 효과를 검증합니다.
