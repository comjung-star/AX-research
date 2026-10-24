# AX v2.3 Stage 1 — Branch-preserving Final Top10 Merge Diagnostic Protocol

Date: 2026-10-24. Protocol committed **before computing the candidate merge comparison described here**, but *after* reviewing the existing Stage 1 Dev outcomes. This is an **exploratory post-hoc diagnostic**, not an originally preregistered confirmatory Test.

## Frozen prerequisites
- Unchanged `release/ax-v2.3-stage1-to4-dev-20261023` v2.3: 84 cases, 10 dev queries, 3 MP runs/query; AI-Silver 2,520 perspective×case relevance labels, relevance >= 3.
- Saved Stage1 rankings `experiments/v23_dev/stage1/rankings_top20.csv` and all 84 cases' `branch_rankings.csv`, BGE-M3 MP branch scores, 97 generated branches. LLM branch texts remain unmodified; all comparisons reselect from exactly the same saved branch rankings.
- No extra embeddings, LLM calls, dataset/GT edits, or changes to the professor-proposed architecture. Historical baseline = exact Branch-balanced round-robin. This diagnostic changes only final Top10 selection.
- Stage 1 is intended to test both standard Recall and *unique relevant discovery*, not optimize Recall alone. Do not use Silver labels, ground truth, reference perspective names, or case Strategy/Factor in candidate scoring.

## Fixed deterministic alternatives (set before this specific candidate run)

**B0 / historical baseline:** Stored MP Dense branch-balanced round-robin final Top10 (unique cases).

**C1 / Branch-quota + consensus:** (1) Keep each generated branch separately, sorted P1..Pk. Select branch's first not-yet-selected case, one per branch, to guarantee one output from each branch. (2) Build candidate union from each branch's **local Top20** (no new retrieval). (3) Fill remaining slots to 10 by descending `branch_support_top10` (# of distinct branches in which case's local rank <=10); tie break ascending `best_branch_rank`, ascending `mean_present_branch_rank_top20`, then case_id lexicographic. Every selection retains its supporting branch provenance.

**C2 / Branch-quota + standardized score:** (1) Same one-per-branch quota stage. (2) Same local Top20 candidate union. (3) Compute per-branch z-score = (case cosine - mean cosine over **all 84 cases in that branch**) / population std of scores over all 84 cases. Set candidate priority to **maximum** branch z-score across generated branches; tie break descending branch_support_top10, ascending best_branch_rank, case_id. Cosine scores come directly from frozen branch rankings; z-scoring avoids arbitrarily preferring branches simply because raw cosine levels differ. If std=0, zscore=0. Branch-specific source provenance is retained.

**C3 / Branch-quota + original-query-anchor (diagnostic control, not a pure MP method):** (1) Same one-per-branch quota. (2) Same local Top20 union. (3) Fill remaining slots by ascending rank in frozen **original-query Single Dense full ranking** (instead of using labels); tie by best branch local rank, case ID. Because it explicitly incorporates the original query baseline, C3 is an anchor-based hybrid **diagnostic**, NOT evidence that pure MP outperforms Single Dense; avoid claiming the professor architecture requires this fusion. Original Single Dense may have only Top20 stored: for ranks outside Top20, assign rank=21 tied then best branch rank. This makes C3 only a Top20 query-anchor, and it must be clearly reported.

## Primary diagnostics (all Top10 output budgets identical)
- MP Recall@10, per-query then macro over **10 questions**, with MP three runs/query averaged within query. Baseline Single Dense fixed 1 run/query.
- MP-only Silver-positive gained count `(MP_top10 - Single_top10) ∩ Gq`; single-only lost count `(Single_top10 - MP_top10) ∩ Gq`, reported as appearance counts across 10×3; and 10 unique dev queries.
- **A-loss-recovery**: among baseline B0's 24 Single-only relevant appearances that were local Top10 candidates but excluded from B0 final Top10, report how many each alternative returns. Report also newly lost single relevant items vs B0 and change in novel positive retrieval; do not use recovery in actual ranking.
- Branch coverage and branch contribution: quota one per generated branch, verify branch provenance and final 10 unique cases. Note references with no relevant Silver case have no coverage denominator (compare existing Stage1 metric rule).
- Compare relevant unique discoveries and `exclusive` Silver positive cases (positive in exactly one of the 3 *reference* perspectives), plus selection overlap baseline.
- Also compute number of Top10 candidates preserved from original B0 to quantify how much a reranking changes selection.
- No hypothesis about significance or generalization from Dev 10 questions, repeated runs not independent, and no human Gold. Selection criteria fixed before rerank measurement in this document.

## Decision rule
Do **not** crown a winner using only Recall. Report Recall and novel-positive discovery together, and clearly describe trade-offs vs B0. If C3 improves by using Single Dense ranks, call that an anchor effect, not an MP-only gain. If C1/C2 fail, preserve that result and do not retrofit weights/criteria to Silver labels. Re-examine downstream planned gated fusion and held-out evaluation separately.

No modification to frozen corpus, AI-Silver ratings, historic Stage1–4 artifacts or original implementation.
