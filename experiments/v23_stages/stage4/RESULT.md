# v2.3 Stage 4 — Evidence Fusion / LLM Recommendation actual Dev experiment

Ten Dev business problems, ten source-anchored LLM recommendation calls, independent GPT-only strategy baseline.

| Method | Derived Strategy Coverage@5 | Derived Strategy Precision@5 |
|---|---:|---:|
| GPT_only_zero_shot | 0.740 | 0.810 |
| retrieved_case_vote | 0.802 | 0.615 |
| Wald_evidence_fusion | 0.802 | 0.615 |
| LLM_grounded_recommendation | 0.623 | 0.817 |

The reference strategies are **derived from AI-Silver-positive case annotations**, not independently adjudicated Gold. This is a feasibility/ablation diagnostic only, not proof of real-world recommendation accuracy. LLM case witness IDs and strategy availability programmatically enforced. Wald associations are NONCAUSAL and sparse cells abstain.
