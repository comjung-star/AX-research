# AX v2.3 Stage 1–4 Dev 재실험: 완료

**최종 검증 완료:** 2026-10-23 · `v2.3` 84개 업무사례 × 10개 개발용 문제 × AI 평가자료 2,520개.

[전체 실험 결과·채택/보류 판단·원인 분석 보고서](../../docs/v23-stage1-to4-dev-final-report-2026-10-23.md)

- [Stage 1: BM25·Dense·GPT-only·다중관점 검색](stage1/DEV_RESULT_ANALYSIS.md) — 최고 Recall@10 GPT-only 0.7235, 다중관점 Dense 0.4530, 단일 Dense 0.5332
- [Stage 2: Multi-view/Gate/Hybrid/Interaction](stage2/DEV_RESULT_ANALYSIS.md) — 학습형 Gate·MLP 및 50:50 Hybrid 성능 개선 미확인
- [Stage 3: Factor/Wald/출처 추적](stage3/DEV_RESULT_ANALYSIS.md) — 근거 추적 완료, Wald 77조합 중 3개 가능, BH 유의 0개
- [Stage 4: 전략 추천/Evidence Fusion](stage4/DEV_RESULT_ANALYSIS.md) — 30회 LLM 추천, Fusion의 빈도 방식 대비 개선 없음

[성공한 전체 GitHub Actions 실행](https://github.com/comjung-star/AX-research/actions/runs/39952604227)

**해석:** 개발용 AI 관련도 평가 기준의 재현 가능한 실험 결과. 별도 Held-out Test 미수행. 실험 가설의 일관된 성능 향상이 입증된 것으로 주장할 수 없음.
