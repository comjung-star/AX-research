# Architecture

이 문서는 연구 아키텍처를 구현 관점에서 정리하기 위한 문서입니다.

기준 문서: [연구계획서](research-plan.md)

현재 기준 흐름:

```text
Business Problem Query
→ LLM Query Understanding
→ Multi-view Embedding
→ View Combination
→ Hybrid Retrieval
→ Query-Case Interaction
→ Perspective-specific Top-K Cases
→ Case Evidence Pooling
→ Root Cause Factor Anchor
→ Wald Evidence
→ Evidence Fusion
→ LLM Reasoning & Recommendation Head
```

세부 구현은 단계별 실험으로 검증하며, 교수 제안 아키텍처의 핵심 흐름을 임의로 변경하지 않습니다.
