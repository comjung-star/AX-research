# AX Case Dataset v2 — Actual Staging Build / Partial Source Review

Date: 2026-10-22 · **Status: IN PROGRESS (not a final dataset)**

## Scope chosen by researcher

One Case = one independently identifiable corporate business problem/workflow with its matching implemented AX solution. Keep original `data/main_cases_v1.csv` frozen; exclude the 6 current SCOPE_HOLD rows from v2 **candidate** evaluation without permanently deleting them.

## Materials generated

1. `data/v2/main_case_parent_staging_v2.csv`: **94** old Case parents, maintaining all v1 IDs, source URLs, old text and labels. **75** single-workflow *provisional* parent drafts copy original Problem/Task/Context/Implementation into explicitly unverified fields; **19** mixed-unit parents have EMPTY workflow-specific drafted fields pending case decomposition (prevent training on broad blended summaries). Old multi-label fields carry `UNVERIFIED` in column names.
2. `data/v2/workflow_split_drafts_v2.csv`: **38** candidate workflow-unit hypotheses derived from the 19 split-review parents. Every new workflow draft has `NOT_APPROVED` and NO imported Factor, Strategy or Outcome labels. Each has its parent id, original primary source URL, relevant keyword locator and qualification. Hypotheses may be abandoned, merged or split again after exact passage-level verification.
3. `data/v2/scope_hold_exclusions_v2.csv`: **6** preserved case links and review rationale, not copied into v2 candidate evaluation.
4. `data/v2/build_summary_v2.json`: machine-readable counts/limitations.

## New direct source-check findings (scoped, not comprehensive)

- `AX0005`: Microsoft explicitly differentiates enterprise SKI GPT, AutoRAG, Power Automate and Foundry pilot agents. **Static safety-incident report Agent is still described as PoC**; do not call it a deployed enterprise use case.
- `AX0006`: Microsoft lists HR and order-to-cash as distinct deployed process categories; KPI by branch not established.
- `AX0016`: Google Best Buy describes customer AI self-service and representative support; self-service containment/transfer rate should not be assigned to representative assistance.
- `AX0017`: AT&T source centers on AI customer interactions; scope-narrow a single CX Case rather than multiplying cases based on an unrelated corporate AI program.
- `AX0018`: NOS source mixes cloud/data-mesh infrastructure with conversational customer service; keep CX task separate from platform-level achievements.
- `AX0037`: NIPA landing page is accessible, but the satellite-specific report pages remain to be inspected; all split hypotheses pending.
- `AX0042`: SuperLawyer legal research and document drafting are distinct features; Microsoft reports overall tool user productivity, not per-feature causal KPIs.
- `AX0043`: Team Reboot source distinguishes HS-code classification 99.2% and combined trade-automation time savings 60%; do not duplicate the 60% across children.
- `AX0050`: Microsoft identifies demand prediction (~1 billion daily forecasts) and Dynamic Markdown (250,000 kg annual waste reduction) separately, with other initiatives beyond those two.
- `AX0062`: Microsoft explicitly names Ask Telstra versus One Sentence Summary with distinct responses/outcomes.
- `AX0066`: Microsoft identifies TOBi (customer virtual assistant) and SuperAgent (human representative assistance).
- `AX0068`: Microsoft identifies three unrelated activity streams and separately reports 10% payment validation, 80% faster settlement inquiry, 20% faster onboarding.
- `AX0074`: AWS distinguishes support ticket and merchant onboarding.
- `AX0080`: Google HLB explicitly describes trade documents OCR and credit underwriting sanction screening. Trade OCR 30% efficiency gain does not belong to sanction-screening branch.
- `AX0088`: Google describes secure AI consolidation plus CRM churn/conversion agent; platform deployment and CRM outcome have different scopes.
- `AX0092`: IBM NatWest source supports **Cora+ customer-facing service**. A separate agent-facing conversation-summarization solution was **not found in this cited source**; do not create the second child without another credible source.
- `AX0093`: IBM Suzhou describes quality/root-cause process and production scheduling.
- `AX0094`: IBM Savage describes quoting, planning and procurement as related, but separable task components; procurement-specific results not reported.
- `AX0087` even though among single-workflow candidates: Black Eyewear is a generative-image virtual try-on. Existing S5 optimization/support label may not adequately describe its intervention. **Hold that Strategy label pending taxonomy decision.**

## Explicit data-integrity gates

- Every source feature must be tied to a definite problem/task, implementation and source passage before v2 Case approval. Corporate program news ≠ task-level Case.
- For each approved workflow: reconstruct Blind RCA only from Problem/Task/Context. Separately label implemented Strategy using solution source. **No cross-product of multiple labels as verified direct relationships**.
- Separate measured single-workflow KPI, measured enterprise-wide KPI, expected/potential KPI, PoC, and no quantified KPI. Only use case-specific outcomes actually traceable to the source.
- Do not reuse parent v1 outcomes across multiple children, even when narrative mentions multiple percentages.
- v2 candidate is NOT training ready; do not rerun Wald or replace old Dev Ground Truth until data freeze. New held-out set remains unbuilt.
- All 94 parents need source-passage-level final sign-off; this step established workflow candidates and targeted original page inspection, **not** full source adjudication of every label.

## Decision at this checkpoint

**Existing v1 evaluation is historical only. 94 selected input parent rows have been staged, 6 scope holds separated, 38 workflow decomposition hypotheses generated but 0 fully signed-off v2 Cases.** Next gate is exact source-evidence capture for candidate workflows and subsequent full relabeling.

See prior triage: `docs/data-audit-main-v1-2026-10-22.md`.
