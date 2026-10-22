# Stage 3-2A — Perspective Provenance Replay v1 (FROZEN FOR IMPLEMENTATION)

Date: 2026-10-22
Scope: **read-only lineage reconstruction**; Stage 3-2B Factor/Wald join is separately gated.
This protocol is an implementation choice under the professor's preserved
multi-perspective architecture; it is not a new professor proposal.

## Hypothesis / motivation

One retrieved Case may be found by P1, P2, ... Pk. Stage 2 final rankings
contain only `source_perspective_id` (the selected/representative source).
The candidate provenance artifact retains every perspective in the candidate
union. We must not mistake the representative source for an exhaustive lineage.

## Frozen input IDs and exact budget

- Frozen Case catalogue `data/main_cases_v1.csv`, blob
  `4b85e296f797dd2759bf7f9e57b26d5473a72b38` (100 Cases).
- Frozen Dev queries `data/retrieval_queries_v0.1.csv`, blob
  `60ed29a080b6df48cb7322fc69e0ce8c7403f8fb` (GTQ001~GTQ010).
- `experiments/rq2_multiview/results/stage2_interaction_v1/stage2_interaction_final_rankings.csv`,
  blob `620372adc2bd1e86e12876ad4f403ed2690ab424`.
- `experiments/rq2_multiview/results/stage2_hybrid_v1/stage2_hybrid_candidate_provenance.csv`,
  blob `dcf2fb00bbe035254674a8c7a70e27dbe35441b7`.
- **Filter** `system=stage2_same_pool_rrf`, `leg_k=10`,
  `final_rank=1..10`, all Dev Queries, `run_id=1,2,3`:
  expected **30 Query/Run groups × 10 ranked Case occurrences = 300**.
- This RRF is a stable *diagnostic reference ranking*, never the proposed
  Query-Case Interaction network / final architecture.
- No LLM call; no reranking; no use of `is_gold`, relevance labels, Strategy
  labels, Wald results, or held-out data in reconstruction.

## Join and validation rules

1. Validate all 30 ranking groups and exact rank values 1..10, with unique
   Case IDs per group. Ranking Case IDs must exist in frozen Case catalogue.
2. Candidate key is `(query_id, run_id, leg_k=10, case_id, perspective_id)`.
   Require each key unique and source ∈ {dense, sparse, both}.
3. For each selected ranked Case, require ≥1 matching candidate provenance
   record and require the selected `source_perspective_id` among them. Fail
   explicitly rather than quietly dropping data.
4. Emit **one row per (Query, Run, ranked Case, Perspective)** with:
   `query_id, run_id, leg_k, final_rank, case_id,
   selected_perspective_id, perspective_id, is_selected_perspective,
   retriever_source, dense_rank, sparse_rank`.
   Retain all additional paths and Dense/Sparse source annotations.
5. The ranked Case ID appears once in the 10-case ranking for a Query/Run.
   Provenance expansion does **not** create additional retrieved Cases.
6. No fixed number of perspectives: P1...Pk generated dynamically; `P4`
   and novel identifiers are allowed.

## Denominators / planned acceptance criteria

- **Ranked Case occurrences:** number of distinct Query × Run × rank
  events = 300. This is the unit for completeness / multi-path prevalence.
- **Perspective–Case links:** number of expanded rows; larger than/equal to
  ranked occurrences, **not** a Recall@K or Strategy Coverage denominator.
- **Additional links:** expanded links - 300.
- **Multi-perspective Case rate:** number of ranked occurrences with ≥2
  matching source perspectives / 300.
- **Selected-source preservation:** 300/300 ranked rows have exactly one
  matching selected-perspective link.
- **Provenance completeness:** 300/300 ranked occurrences have ≥1 candidate
  record, with no missing or unrecognized IDs. Fail closed on validation.
- **Branch counts:** number of expanded links for each observed generated
  perspective ID, without constraining the number of possible perspectives.

Exact outputs:
- `stage3_perspective_case_trace.csv` (row-level, no Gold field)
- `stage3_perspective_summary.json` (predeclared diagnostic totals)

## Interpretation and remaining stages

Passing the above checks establishes **structural provenance**, not retrieval
accuracy improvement, Factor agreement, Strategy recommendation quality or
Held-out generalization. Stage 3-2B will join the existing frozen Root Cause
Factor labels (Blind RCA Problem View only) and separate Strategy/Wald evidence
without re-inferring factors from solutions. Stage 3-2C will audit evidence
statuses and structural metrics. Stage 4 must separately evaluate actual
recommendation behavior and ground-truth strategy coverage at equal budget.
