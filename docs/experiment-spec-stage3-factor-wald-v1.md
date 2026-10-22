# Stage 3-1 Factor Anchor / Wald Evidence — Dev Protocol v1

Status: **FROZEN FOR IMPLEMENTATION / validation pending** (2026-10-22)

## Why now

Stage 2-3 Hybrid Candidate Union and Stage 2-4 Query-Case Interaction were executed.
The 50:50 Hybrid candidate allocation and Interaction MLP v1 did not beat
their respective same-budget references; do not retune those failed ablations
post hoc. Preserve the professor-proposed search architecture, while isolating
the evidence stage using a stable, nonlearned *reference* retrieval ranking.
RRF is **not** the proposed architecture.

## Scope of this first Stage 3 step

**Offline factor–strategy relationship audit only.** Do not yet call this a
Factor-Anchored recommender, Case Evidence Pooling model, or an improvement
in Strategy Coverage.

Input:
- 100 frozen case records in \`data/main_cases_v1.csv\`
- 9 frozen Root Cause IDs (\`data/root_cause_factors_v1.csv\`)
- 6 frozen Strategy IDs (\`data/strategy_taxonomy_v1.csv\`)
- Case ID + preassigned Root Cause multi-labels + Strategy multi-labels
- Original case source for audit trail

The existing Root Cause labels originated from **Blind RCA using only
Business Problem / AX Target Task / Business Context**. This analysis does not
re-infer Root Cause from Solution View. Strategy is read separately from
Solution View to estimate pairwise associations.

## Statistical unit and model

Unit: **unique AX Case**, not retrieved candidates, perspectives, or repeated
LLM runs. Each (Factor, Strategy) test treats factor membership and strategy
membership as binary indicators for the same set of 100 cases.

For each of 9×6 = 54 prespecified pairs:

| | Strategy present | Strategy absent |
|---|---:|---:|
| Factor present | a | b |
| Factor absent | c | d |

The univariate (intercept + single-factor) logistic maximum-likelihood
coefficient, when all cells are nonzero, is:

- β = ln(a·d/(b·c))
- OR = exp(β)
- SE(β) = sqrt(1/a + 1/b + 1/c + 1/d)
- z = β / SE(β), two-sided Wald p = erfc(|z|/sqrt(2))
- 95% OR CI = exp(β ± 1.96 SE)

This is **unadjusted association**, not a causal effect or a multivariate
control for industry, case dependencies, or co-occurring factors.

### Sparse cell guard and multiplicity

- Predeclare min(a,b,c,d) ≥ 5 as the conservative **diagnostic** Wald
  eligibility rule, not proof of validity.
- If any cell <5, mark \`SPARSE_ABSTAIN\`; β / OR / Wald p / CI remain blank.
  Do not fabricate a continuity-corrected Wald inference.
- BH FDR adjustment across the complete 54-pair family; abstained pairs
  count as p=1 for the adjustment but expose no q-value as an inference.
- Even if q<0.05, no automated recommendation from p-values alone.

## Output

- \`stage3_wald_pairs.csv\`: all 54 contingency tables and diagnostics
- \`stage3_case_factor_strategy_links.csv\`: Case → Root Cause → Strategy
  provenance (not a model prediction)
- \`stage3_wald_summary.json\`: sample size, sparse pairs, eligible pairs
  and preliminary adjusted associations

All outputs are **Dev/offline descriptive evidence**. The 10 Dev queries do
not become new training cases. Existing Ground Truth is unchanged.

## Next Stage 3-2 study

Keep Stage 2-3 candidate provenance and Stage 2-4 ranked-case artifacts
unaltered. As a controlled reference, replay the same
\`stage2_same_pool_rrf\` rankings (not as the proposed model), selecting one
fixed budget, and join each retrieved Case to its Root Cause Factor labels.
Test, without new tuning:

1. Coverage / correctness of Case → Factor links and evidence source.
2. Factor-label agreement or uncertainty using **Problem View only**.
3. Strategy discovery and evidence traceability with vs without offline
   Wald annotations, at identical retrieved cases and recommendation budget.
4. Effect of sparse/negative/non-significant links (abstention; do not
   suppress legitimate strategies just for non-significance).

Only after freeze of Stage 3-2 criteria should Evidence Fusion and the
LLM Recommendation Head be compared on **held-out** Query tests.
