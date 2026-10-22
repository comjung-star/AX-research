# Stage 3-1 Factor–Strategy Wald Dev Result Analysis

Date: **2026-10-22**
Run: [Stage 3-1 GitHub Actions 39734864597](https://github.com/comjung-star/AX-research/actions/runs/39734864597)
Code/Protocol: `src/ax_research/stage3_wald.py`,
`docs/experiment-spec-stage3-factor-wald-v1.md`

## Question

Can the frozen AX Case corpus support *descriptive* Wald association evidence
between preassigned Problem-only Root Cause Factors and Solution Strategy labels,
and which relationships must be withheld due to sparse tables?

This is an **offline statistical diagnostic**, not an improved recommender
or a Factor-aware retrieval ablation.

## Reproducible execution

```bash
python -m ax_research.stage3_wald \
  --cases data/main_cases_v1.csv \
  --factors data/root_cause_factors_v1.csv \
  --strategies data/strategy_taxonomy_v1.csv \
  --output-dir experiments/rq3_evidence/results/stage3_wald_v1
```

CI confirmed: 5 focused unit tests passed; pre-existing full repository
test suite also passed. Full CSV/JSON files are uploaded as the GitHub Actions
`stage3-wald-v1-diagnostics` artifact. The artifact includes all 54 2×2
tables and Case→Factor→Strategy lineage.

## Main findings

| Check | Result |
|---|---:|
| Frozen AX Case rows | 100 |
| Root Cause factors | 9 |
| Strategies | 6 |
| Prespecified Factor × Strategy pairs | 54 |
| Pairs with each cell >= 5 | 35 |
| Pairs failing sparse-cell diagnostic | 19 |
| Eligible pairs with BH q < 0.05 | 6 |

Exploratory strongest associations (a,b,c,d are contingency counts):

| Factor | Strategy | (a,b,c,d) | OR | BH q approx. |
|---|---|---|---:|---:|
| F01 반복 수작업 | S6 프로세스 자동화 | (43,5,13,39) | 25.80 | <0.0001 |
| F09 예측·최적화 복잡성 | S4 예측·탐지 | (21,7,14,58) | 12.43 | 0.00005 |
| F09 예측·최적화 복잡성 | S5 최적화·의사결정 지원 | (23,5,26,46) | 8.14 | 0.0026 |
| F05 프로세스·시스템 분절 | S2 에이전트·대화형 AI | (14,7,23,56) | 4.87 | 0.033 |
| F01 반복 수작업 | S5 최적화·의사결정 지원 | (16,32,33,19) | 0.29 | 0.033 |
| F03 전문가 판단 의존 | S5 최적화·의사결정 지원 | (21,8,28,43) | 4.03 | 0.034 |

The six q-values above are rounded for readability; the CI artifact contains
unrounded values. OR<1 indicates a negative association in this corpus,
not a prohibition on recommending that Strategy.

## Interpretation and constraints

- Statistical unit: unique **Case**, not duplicate Query/Run/Perspective.
- Blind RCA labels were prepared with **Problem View** only; this stage
  consumes frozen labels rather than re-inferring them from Strategy.
- Multi-label factors and strategies are **correlated**; tests here are
  marginal/unadjusted, and cross-industry/source heterogeneity remains.
- Many cases are sourced from curated, public success stories. The resulting
  associations may reflect selection bias and labeling criteria.
- A significant Wald relationship is not causal evidence, proof of a Strategy's
  effectiveness, or a calibrated recommendation confidence score.
- A sparse pair yields **no** Wald β/OR/p/CI claim; a non-significant pair is
  also not evidence that a Strategy is unsuitable.
- Do not tune Root Cause taxonomy, Ground Truth, or hybrid search allocation
  against these Dev results.

## Next: Stage 3-2

Use the frozen Stage 2 *reference* retrieved cases without modifying their
order. Join Case → Root Cause Factor → Wald association and original Source,
preserving per-Perspective branch identity. Freeze the evaluation first:
trace completeness, unsupported-link/abstention rate, Strategy Coverage and
evidence-based explanation fidelity at a fixed Top-K/recommendation budget.

RRF is an experimental **reference baseline only**, never a substitute for
the professor's proposed Query–Case Interaction model.
