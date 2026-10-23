# AX dataset v2.2.0 — Source-screened extension (93 cases)

**2026-10-23 decision:** User approved immediate addition of appropriate real-world examples for 2 unanswered reference perspectives. **DO NOT overwrite / back-fill frozen v2.1 91 cases**; preserve the original exact artifacts and candidate decision trail.

## Results and counts
- New corpus v2.2.0: **93 operational-source-described workflows** (91 v2.1 cases carried forward unchanged + 2 source-screened cases).
- Added Wayfair product attribute catalog categorization: `AXV22_0092_01` — V21D006/P1 gap.
- Added Jeju Bank internally secured on-prem business-document Q&A workflow: `AXV22_0093_01` — V21D009/P1 gap.
- **Excluded** Home Credit Bank: official Google case describes deployment through a controlled 130-user pilot. Full non-pilot operational status for the matching secured-AI platform/workflow has not been independently distinguished. Also Gemini Enterprise managed cloud is **not on-prem**. Preserve in screening register, not v2.2 main cases.
- Seven historically held cases are NOT promoted by this extension.
- 91 original rows retain original Case IDs, source evidence, Factor/Strategy review statuses. Two new rows have null Factor and Strategy labels and explicit not-reviewed flags.
- Current old 64 Factor–Strategy links are unchanged. Do not create Wald/association pairs for new cases without independent review.
- 65 sampling groups (63 old + 2 new, each independently grouped).

## Research conditions
- `main_cases_v2_2.json`, `.csv`, `source_evidence_index_v2_2.csv`: full 93-case snapshot, source evidence and scope caveats.
- `release_manifest_v2_2.json`: exact Git blob hashes of new data, parent v2.1 hashes and release restrictions.
- `dev_query_candidates_v2_2.json`: same ten **Dev** queries (not Held-out) and draft reference perspectives; must not be passed to the runtime LLM as gold prompts.
- `dev_relevance_annotation_sheet_v2_2.csv`: **2790 UNJUDGED** slots (10×3×93). All grades, annotator IDs, reviewer IDs, reasons remain blank; do not copy the 2730 v2.1 AI draft labels.
- `dev_strategy_annotation_sheet_v2_2.csv`: 10 UNJUDGED strategy sets.
- Old v2.1 corpus/manifest/test results remain fully intact, and source-screened cases must undergo independent blind Human Relevance/Factor/Strategy review before Gold-based performance claims.

**Selection bias:** These exact cases were gathered after looking at Dev coverage gaps. This changes the dataset itself and can mechanically remove an empty view. Do not represent 91→93 as a demonstrated retrieval model gain or use the same Dev measurements as independent held-out evidence. Re-evaluate all methods on the same v2.2 corpus only after independent GT and pre-registered evaluation setup; build a genuinely new held-out test independently.

## Source links
- Wayfair Google Cloud: https://cloud.google.com/customers/wayfair-ai
- Jeju Bank Plateer: https://labs.plateer.com/en/customers/case/jeju-bank-genai-platform
- Home Credit Bank (watchlist): https://cloud.google.com/customers/homecreditbank
- Existing source-coverage audit: ../docs/v21-two-empty-perspectives-resolution-evidence-2026-10-23.md

**Status:** 93 cases committed as a versioned extension for independent review; **not** 93 human-validated Gold cases, no new Recall/Coverage results, and not frozen as an approved final benchmark.
