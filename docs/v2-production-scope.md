# v2 inclusion scope: production deployment only

Decision date: 2026-10-22. Explicit user decision: include only cases actually deployed in business operations.

An eligible workflow needs primary-source evidence of actual operational use by an identifiable organization. A built prototype, co-creation pilot, test, demo, planned rollout or supplier capability alone is insufficient. A named product and reported performance alone do not establish operational deployment. Unknown deployment status means abstain from inclusion.

`data/v2/production_scope_decisions_v2.csv` records explicit exclusions and holds. Absence from this file is not approval: every remaining candidate still needs affirmative production evidence before final acceptance. The 94-parent staging inventory and 38 historical split hypotheses remain preserved as audit inputs, not eligible-case counts. Any future accepted case must check this parent-level scope decision and independently establish its own workflow's operational use.

AX0095 is excluded from the final production corpus: the IBM source establishes a six-week pilot, with expansion described as future work. AX0096 was independently rechecked against the primary IBM page and is also excluded as a pilot. Telstra and Vodafone's cited GenAI workflows are excluded as pilots; Home Credit is held because a transition from the controlled pilot to regular production is not explicit. None can supply production outcomes or downstream v2 training/evaluation data under this decision.

Production deployment and outcome strength are separate dimensions. A production workflow may have vendor-reported, estimated, projected or missing outcomes; retain those qualifications. Never relabel a pilot measurement as a production result merely because a related workflow later deployed.

This scope decision resolves the pilot-inclusion question in `v2-freeze-blockers-2026-10-22.md`. It does not resolve the remaining primary-source reviews, workflow splits, taxonomy gaps, shared-outcome attribution or approval requirements. v1 and historical experiments remain unchanged. v2 remains unfrozen and PR #3 remains draft.
