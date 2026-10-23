# AX v2.3 Dev reference relevance: Gold/Silver data protocol

## Intended benchmark
Corpus snapshot: **84 independent enterprise AX workflows**, `data/v2_3/main_cases_v2_3.json`, Git blob `1705888f3338b219d3715fe4422641865c3075e2`. Dataset and its F/S classes are *source-adjudicated corpus annotations*; they are **not** user-question relevance judgments.

Dev: ten **previously developed** problem queries `V21D001`–`V21D010`, each with three **evaluation-only draft reference perspectives**. Full matrix = 84 × 10 × 3 = **2520 entries**.

## Rubric / leakage prevention
Independently rate relevance 0–4 using only query text, reference perspective title and each case's `problem` / `task` / `context`.

- 4: exact match of central problem/task and aligned workflow context.
- 3: strong match of central problem/task even in a different industry.
- 2: partial overlap but materially different central work.
- 1: only remote/general relationship.
- 0: no substantive relationship.

Binary relevance threshold **>=3**; do not force every perspective to have positives. Keep zero-positive perspectives and report separately (exclude unanswerable perspectives from denominator when interpreting coverage). **Never** input AI implementation, strategy labels, factor labels, outcome, historical gold, retrieval ranks or AI earlier scores to a fresh rater. Reference perspectives themselves must not be shown to the runtime multi-perspective generator or retriever.

## Provenance and limitations
Three fresh independent API runs rate all 2520 cells on **the frozen v2.3 inputs**, with identical rubric and deterministic batch boundaries, no cross-run leakage. Raw batches, parsed evidence reason, prompt SHA, response ID, source identifiers, models and UTC timestamps are stored.

The **median of 3** produces a reproducible **AI-Silver candidate** (not human Ground Truth). Preserve all 3 raw scores. Flag scores that vary across the `2/3` threshold and scores differing by >=2 points; persist a blind optional review worksheet. Repeated AI agreement **does not imply factual correctness**.

Historic researcher 50 **v2.2** first-pass scores are personal blind annotations on a different corpus snapshot / sometimes Korean paraphrased context. They are retained **as historical diagnostic only**, never auto-imported as v2.3 Gold, nor overwritten by model opinion.

A formal Gold label requires genuinely independent author/researcher judgment on the current target pair and explicit final approval; no AI agent can truthfully certify that human adjudication without it having occurred. If ratings are used for preliminary Dev comparisons, label all results "AI-Silver (provisional)" and report that constraint. No "Gold Recall" or final performance improvement may be claimed from AI-only ratings.

Strategy set candidates are obtained from source-verified strategy labels on AI-Silver positive cases for **analysis assistance**. They are not an independently judged query-level Strategy Gold Set. No metric should silently treat them as independent human gold.

Final model claims require separate held-out Test queries, Test relevance adjudication, independence from Dev adjustments, group-aware leakage controls, and explicit limitations of corpus-sampled taxonomy F10/F11. Avoid moving source cases/labels based on performance feedback; frozen v2.3 source release stays fixed.

## Exact release nomenclature
- `FROZEN_SOURCE_ADJUDICATED_NOT_GROUND_TRUTH`: v2.3 84-case **corpus**.
- `COMPLETE_AI_ONLY_SILVER_2520_NOT_HUMAN_GROUND_TRUTH`: 2520 **Dev relevance proxy ratings**.
- `HUMAN_GOLD` is **not** a status produced by this automated pipeline.
