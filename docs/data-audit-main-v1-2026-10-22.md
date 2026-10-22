# Main Dataset v1 — All 100 AX Cases: Source / Unit / Label Audit
Date: 2026-10-22

**Status: 100/100 first-pass record-level triage complete; individual source-excerpt and label re-adjudication NOT complete.** No v2 dataset is being represented as frozen or validated.

Main frozen source: `data/main_cases_v1.csv` (SHA `4b85e296f797dd2759bf7f9e57b26d5473a72b38`) and source QA `data/main_qa_metadata_v1.csv`.
Per-case assessments: `data/main_case_unit_audit_2026-10-22.csv`.
Only original v1 data were read. No historical experiment, GT or Case row was rewritten.

## Core finding

Our newly agreed unit of analysis is **one independently identifiable business-workflow problem and its implemented AX solution**. The original 100 rows include broad enterprise AI programs, multiple workflows and general vendor offerings alongside legitimate focused business-use cases. Current Case IDs are not all one-to-one with the agreed workflow unit.

- **75 KEEP_WORKFLOW_CANDIDATE:** case description appears to represent a workflow, pending detailed field-to-source verification.
- **19 SPLIT_REVIEW:** multiple distinguishable workflows/products/metrics may have been collapsed into one Case; splitting is conditional on actual source anchors.
- **6 SCOPE_HOLD:** platform/product descriptions, vendor-only claims, or no clearly attributable implemented business-workflow need review against scope.
- **48** rows have explicit high-priority label concern; **ALL 100** still need factor and strategy support checked against exact source passages before final v2 release.
- `31` outcome descriptions include a term requiring clarification (expected, pilot, mixed attribution, UNKNOWN, etc.). This is a text screen, NOT a count of false claims.
- Main dataset v1: Root Cause 1/2/3/4 labels = 6/25/60/9; Strategy 1/2/3/4 labels = 6/58/35/1. Both multiple = 91/100.

## Independently accessed representative primary sources

- AX0005 SK Innovation: Microsoft explicitly covers SKI GPT, AutoRAG, no-code automation and Agentic AI. Distinct program components may not constitute one workflow.
- AX0006 Danone: Microsoft describes HR and order-to-cash applications as separate business processes.
- AX0016 Best Buy: Google discusses AI self-service and employee/customer-support workflow.
- AX0062 Telstra: Microsoft names Ask Telstra (knowledge retrieval) and One Sentence Summary as two separate tools.
- AX0066 Vodafone: Microsoft names TOBi and SuperAgent as different customer/agent applications.
- AX0068 BNY: Microsoft reports payment verification, settlement inquiry and customer onboarding metrics separately.
- AX0074 Cashfree: AWS reports customer support and merchant onboarding as distinct activities.
- AX0093 Suzhou: IBM discusses quality analysis and production scheduling in one orchestrated platform.
- AX0033 LaonPeople: the provided web page is a vendor-wide AI vision solution, not a named enterprise implementation.
- AX0051 Albertsons: the original Afresh link returned 404 in direct opening but an alternative Afresh official press release was located; replace broken link, do not falsely label the case unverified.
- AX0087 Black Eyewear: real virtual try-on case exists, but currently filed only as `S5 Optimization/Decision Support`. Verify whether taxonomy covers generative visual augmentation faithfully.
- AX0077 BMW: genuine AI infrastructure story, but define whether that is in the primary **enterprise workflow AX** scope or an AI platform enabling corpus.
- AX0053 pork inspection: customer complaint decrease coincided with additional quality measures; NOT solely attributable to Vision AI.

## Three separable concerns

1. **Case boundaries**: multi-workflow reporting under one Case may distort sample size and data leakage.
2. **Label validity**: F1/F2 and S1/S2 co-occurrence does not establish all F×S are direct supported pairings. A workflow can have multiple genuine causes/strategies; do not force arbitrary 1:1 labeling.
3. **Evidence type**: observed actual KPI vs expected/pilot KPI vs overall platform KPI vs unknown. Avoid attributing enterprise-wide outcomes to one child workflow.

## Source-access limitations

This round examined ALL 100 GitHub case narratives and QA metadata and attempted public source verification across the dataset. `NIPA` entries AX0035~AX0042 share a report landing URL rather than individual directly adjudicated sections. Some news/vendor URLs could not be fetched (including several Lotte Cloud pages). Actual 100-source *passage-by-passage* factual re-verification **remains outstanding** and must never be described as completed. Prior metadata indicating VERIFIED does not supersede this new check.

## Consequence for research

Freeze and **preserve v1** as historical Dev corpus. Do not silently overwrite source labels or reassign existing GT. Current Stage 3 Wald reflects **case-level Factor/Strategy co-occurrence**, not evidence that an individual Factor directly caused an intervention; it will need re-estimation when v2's distinct Case units are locked. Previous Recall and strategy coverage metrics cannot be reused to claim v2 improvements after corpus boundaries change.

## Recommended phased remediation

1. Confirm all `SPLIT_REVIEW` and `SCOPE_HOLD` from source paragraphs, assign independent workflow boundaries and actual KPI mapping.
2. Re-adjudicate Problem View Root Cause and Solution View Strategy labels separately using paragraph-level anchors. Add explicit direct mapping status: SUPPORTED / NOT_ESTABLISHED / CONTRADICTED.
3. Require actual client/task specificity, measured-vs-expected outcome state and source URL/page.
4. Build **new `business_case_v2` candidates** with `parent_case_id` to maintain lineage; do not enforce an arbitrary final sample size or one-factor/one-strategy rule.
5. Freeze v2 after reviewer check, then rebuild independent Dev/Test relevance and downstream retrieval / Wald / recommendation experiments.

**This audit is a reasoned triage and worklist, not a completed second source-labeling pass or a new validated dataset.**
