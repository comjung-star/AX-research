# Stage 3-2 Case Evidence → Factor Anchor → Wald Trace v1 (DRAFT)

Status: **PROTOCOL DRAFT — no Stage 3-2 execution or performance claim yet**
Date: 2026-10-22

## Objective

Validate whether retrieved, perspective-attributed AX Cases can be connected
to a verifiable chain:

```text
Generated Perspective (P1...Pk)
→ Retrieved Case ID (with rank and source)
→ Preassigned Root Cause Factor(s) (Blind RCA / Problem View only)
→ Case's implemented Strategy label(s) (Solution View)
→ Offline Factor ↔ Strategy Wald association (Stage 3-1)
→ Evidence Path / abstention
```

Stage 3-1 has shown that 35/54 Factor-Strategy tables meet the prespecified
cell-size diagnostic; 19 pairs require Wald abstention. This does **not**
establish that a Factor should cause a Strategy recommendation.

## Proposed fixed replay

- Case corpus: frozen `data/main_cases_v1.csv` (AX0001~AX0100).
- Query/GT: frozen GTQ001~GTQ010 only as **Dev**, not held-out.
- Input rankings:
  `experiments/rq2_multiview/results/stage2_interaction_v1/stage2_interaction_final_rankings.csv`.
- Fixed `system=stage2_same_pool_rrf`, `leg_k=10`, `final_rank <= 10`,
  all 3 prior generated-perspective runs.
- RRF here is a **stable reference ranking**, not a component of the proposed
  professor architecture; no claim is made that the RRF-based pipeline is
  the proposed neural Search Core.
- Preserve original `query_id`, `run_id`, `source_perspective_id`,
  `final_rank`, `case_id`. No new LLM call, reranking, budget change,
  GT editing, or post-hoc ratio tuning.
- Source metadata from the frozen Case, not a generated citation.

## Provenance join logic

1. Validate unique (Query, Run, Rank) and expected Case IDs.
2. Join Case → each frozen Root Cause Factor (do not re-infer from Strategy).
3. Join Case → each implemented Strategy; this records **observed case
   evidence**, not a predicted Strategy label.
4. Join each (Factor, Strategy) to offline Stage 3-1 pair diagnostics.
5. Assign evidence status:
   - `POSITIVE_ASSOCIATION`: eligible, OR > 1, BH q < 0.05
   - `NEGATIVE_ASSOCIATION`: eligible, OR < 1, BH q < 0.05
   - `INCONCLUSIVE`: eligible but q >= 0.05 (or OR=1)
   - `SPARSE_ABSTAIN`: failed minimum cell criterion
6. Keep a link even if inconclusive or negative; never turn significance into
   a hard Strategy filter.

## Proposed evaluation (no predictive benefit claimed yet)

- **Trace completeness@10**: share of 10 replayed Cases with ID, Source,
  valid Factor(s), and at least one evidence-link row.
- **Branch preservation**: fraction of input ranked cases retaining original
  source Perspective ID and rank after lineage expansion.
- **Wald availability**: share of Case–Factor–Strategy links with non-abstained
  Wald diagnostics; report link-weighted and unique-pair counts separately.
- **Evidence status distribution**: positive / negative / inconclusive /
  sparse abstain, overall and by Query/Run.
- **Observed Strategy Coverage@10**: read-only retrieval statistic using
  Ground Truth Gold Strategy Set. As the same Cases and Strategy labels are
  replayed, adding Wald annotations **cannot change this coverage**.
  Do not report a fictional improvement over no-Wald on unchanged rankings.

Denominator choices, exact column schema and validation of the freeze inputs
must be checked before marking this protocol `FROZEN_FOR_IMPLEMENTATION`.

## Interpretability and held-out guards

- Blind RCA: Problem/Task/Context only; Solution must not inform factor
  inference. Strategy labels are inspected only after the frozen factor join.
- Factor-level Wald estimates derive from curated observational Case labels;
  association != causality != recommendation confidence.
- Multiple labels may expand one Case into multiple evidence-link rows.
  Do not accidentally count those rows as additional retrieved Cases.
- 10 Dev Queries are reused only for diagnosis. Reserve final
  recommendation quality claims for a separately frozen Held-out Test.
- Stage 4 will be needed to test whether evidence actually changes strategy
  recommendation decisions or grounded explanation quality at a fixed budget.

## Next implementation slices

1. Freeze input invariants, output columns and denominator definitions.
2. Implement a read-only lineage export with tests for multi-label expansion,
   case uniqueness, branch provenance and sparse abstention.
3. Run the Dev replay and record structural diagnostics separately from
   strategy performance.
4. Then pre-register Stage 4 Evidence Fusion / Recommendation evaluation.
