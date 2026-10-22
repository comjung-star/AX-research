# v2 freeze decision blockers — 2026-10-22

Current status is in [production replacement results](v2-production-replacements-2026-10-22.md): production-only inclusion and replacement of unresolved sources were both authorized. The questions below are historical, not new requests. Final freeze remains blocked by passage alignment/reapproval of inherited candidates and independently blinded label review, not by requiring recovery of cases now excluded.

Update: the user resolved the pilot-inclusion decision in favor of production-only cases. See `v2-production-scope.md` and `v2-evidence-review-2026-10-22.md` for the subsequent work. The question below is retained as history, not a pending request.

Status: NOT FROZEN. This check does not advance the 24 first-pass parents, approve any split, or complete the remaining 70 parents. Local staging validation passed with 100 v1 cases, 94 parents, 6 holds, 38 split hypotheses and zero approvals.

## AX0087: workflow boundary and outcome attribution

Primary source independently reopened: https://cloud.google.com/customers/black-eyewear

Passage anchors:

- “Building a frame recommendation agent with Gemini”: specialist facial-analysis models match customers to inventory; a Gemini Flash web agent provides personalized recommendations.
- “Transporting the elite, personalized London boutique experience to a global digital audience”: the subsequent paragraphs describe a separate image-generation virtual try-on capability using Nano Banana 2, integrated into the experience.
- The results paragraphs report company-wide frame sales growth and shorter consultations when shoppers arrive with AI-generated shortlists. They do not isolate virtual try-on's contribution from the recommendation agent.

Consequences: the existing first-pass virtual try-on row must not be accepted with sales growth or consultation savings attributed specifically to that workflow. Those metrics remain shared-experience, vendor-reported observations with component attribution unresolved. Same-day integration and image-generation latency concern the try-on implementation; they are not measured business impact. Expert-judgment dependence principally describes recommendation and must be reconsidered from the try-on problem passage alone. AX0087 also needs renewed split review despite currently being a single-workflow parent candidate.

## AX0095: implemented pilot versus production eligibility

Primary source independently reopened: https://www.ibm.com/case-studies/digital-office-company

Passage anchors: “Applying the best of both worlds” describes a six-week co-creation pilot for real-estate document classification and custom metadata tagging. “Enhanced document classification, insights and cost savings” attributes performance to that pilot; the closing paragraph describes expansion as future work. Production deployment at a named customer is not established.

The source supports an actually implemented pilot, not a hypothetical proposal. It does not support production outcome classification. Whether such cases enter the final research population changes the sampling definition and requires an explicit research-scope decision. Pending that decision AX0095 remains unapproved; the 2.4-second headline is pilot performance, not production evidence.

## Decision needed before final freeze

Define whether actually implemented pilots are eligible alongside production cases, with separate outcome strata, or whether the final corpus is production-only. Conservative interim treatment is to retain pilot evidence in staging and exclude it from approved production data. This decision does not resolve the outstanding source reviews, split validation, taxonomy audit, blind relabeling or independent approval requirements.

No immutable v1 files or historical experiment outputs were modified by this check. PR #3 remains draft.
