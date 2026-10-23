# v2.3 Stage 2 — Actual Dev Ablation Results

Reference is 2520 AI-only Silver judgments, not human-adjudicated Gold. Ten Dev questions; no held-out Test.

| Method | Recall@10 | Perspective Coverage@10 | Derived Strategy Proxy@10 |
|---|---:|---:|---:|
| stage1_mp_dense | 0.486 | 0.967 | 0.867 |
| stage2_1_equal_multiview | 0.441 | 0.850 | 0.802 |
| stage2_2_loqo_gated | 0.320 | 0.783 | 0.710 |
| stage2_3_hybrid_rrf | 0.323 | 0.750 | 0.652 |
| stage2_4_loqo_interaction_mlp | 0.257 | 0.717 | 0.727 |

The hybrid candidate union is separately controlled at equal 2k retrieval slots; do not conflate union gain with top-K gain.
Gated and Interaction models use leave-one-QUERY-out training to avoid evaluating on labels used in their own fit; they may still overfit 10 Dev queries across folds.
