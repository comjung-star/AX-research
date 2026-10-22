# AX Dataset v2.1 — Independent Relevance & Strategy Ground Truth Protocol

**Protocol date:** 2026-10-22  
**Corpus:** exactly 91 cases from `main_cases_v2_1.json`, fixed Git blob SHA in `release_manifest_v2_1.json`.  
**Status:** NOT YET ANNOTATED; do not call the exported spreadsheets human GT until actual independent raters complete and adjudicate them.

## Query / evaluation split

- `dev_query_candidates_v2_1.json` reuses the **10 v1 Dev query WORDINGS only**, under new `V21D001..010` IDs. No old `AX0001...` relevance or Gold strategy judgments survive migration.
- Thirty historical 3-perspective strings are only **draft evaluation references**. They never become runtime prompt templates or model input. In RQ1 production runtime, the LLM dynamically decomposes each Business Problem Query into variable `P1..Pk`.
- New held-out test questions must be independently authored, frozen before benchmark results, with no filter favoring multi-perspective models. Reused Dev queries are NOT held-out Test.

## Blind annotation input

For each Dev query and drafted perspective, 91 cases must be compared **only** using:
1. Query's Business Problem text and its corresponding drafted Problem Perspective;
2. Candidate case Problem, Task, Context;
3. Independent judge's reason referencing the exact shared problem/task/constraint.

Withhold Solution, Implementation, Factor Label, Strategy Label, Outcome, model ranking and any previous v1 relevance score from annotators. The review interface can show Case IDs but no gold solution hints.

## Relevance rubric (0–4)

| Score | Meaning |
|---:|---|
| 4 | Directly relevant: problem/task/context substantially matches a perspective |
| 3 | Strongly relevant: main workflow problem or task is similar, even if the context differs |
| 2 | Partially relevant: some common elements but the central task/problem is not matched |
| 1 | Peripheral relation only |
| 0 | No relevant problem correspondence |

Gold relevant = 3 or 4, as historical Dev threshold; no score must be invented simply to guarantee a positive result. Record explicit 0–4 relevance, judge ID, separate reviewer ID, evidence rationale and `ADJUDICATED` status. Relevance is a **judgment**, not provider's outcome KPI and not a factor/strategy label.

## Independent adjudication

- The case author/AI annotation output is not automatically an independent human rater.
- Blind annotator completes 2730 labels. An independent reviewer checks each rationale/label without viewing model outputs. Disagreement is recorded and reconciled on Problem View alone; preserve both initial scores and a decision log before overwriting a finalized dataset.
- After all 2730 slots and 10 strategy labels (separate strategy evaluation) are independently approved, freeze an immutable manifest of the result. Do not mutate this GT after observing leaderboard results.
- Strategy GT: a separate task, where judges may inspect Case Solution Evidence only **after** retrieval relevance grading; do not infer "Gold Strategies" just because selected candidate has a strategy label, and do not treat ABSTAIN as false negatives.

## Safeguards

`scripts/v21_evaluate.py` refuses evaluation while any slot is `UNJUDGED`, has empty rating/reason, duplicate annotator/reviewer, unknown Case ID or incomplete 10-query results. This prevents old v1 qrels or synthetic pseudo labels from silently yielding apparently scientific Recall@K, Perspective Coverage and Strategy Coverage values.

When Ground Truth is complete:
- Keep same corpus 91 and same retrieval budget across Single BM25, Single BGE-M3, GPT-only, LLM Multi-Perspective BM25/BGE-M3.
- Include source/company/parent `sampling_group_id` in any train/test split; do not split same source/system across independent folds.
- Preserve generated branch IDs and all branch-specific retrieval/rerank provenance. Do not use RRF as the proposed model.
- Evaluate `Recall@5/10`, Perspective Coverage and optionally Strategy Coverage from separately adjudicated Strategy GT; report confidence intervals paired by **query**, not 2730 labels as independent samples.
- Retain all method settings, model identifier, embedding model hash, LLM API identifier, prompt SHA, date, token budget, repeated runs, random seeds, ranking traces and costs.
