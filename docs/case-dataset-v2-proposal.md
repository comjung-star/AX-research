# Data model proposal — AX Dataset v2 (DRAFT)

Unit: ONE independently identifiable enterprise business problem/workflow + corresponding real AX implementation.
A single corporate press release can generate zero, one or multiple Case IDs if each workflow is independently supported.

Tables (conceptual):
- source_document(source_id, publisher, url, title, passage/page locator, inspected_date)
- business_case_v2(case_id, parent_v1_case_id, workflow_problem, task, context, implementation, measured_outcome, outcome_status, source_id, evidence_locator, source_review_status)
- case_factor_labels_v2(case_id, factor_id, **Problem-only** textual evidence locator, review_status)
- case_strategy_labels_v2(case_id, strategy_id, **Solution-only** textual evidence locator, review_status)
- factor_strategy_relations_v2(case_id, factor_id, strategy_id, relation_status, relation_evidence_locator)
- case_change_audit_v2(case_id, changed_field, prior_value, proposed_value, reason, review_status)

Do not automatically turn m causes and n strategies into m×n **direct** solution relationships. However, keep separate descriptive co-occurrence data for univariate offline Wald if scientifically warranted; no causal claim.

Actual/estimated/POC/enterprise-level outcome types must be stored separately; unknown needs explicit state. Candidate child IDs must not be counted or modeled as independent unless source confirms distinct workflows. Old Case/GT freeze remains immutable.
