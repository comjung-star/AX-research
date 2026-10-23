# v2.3 Stage 1 — Actual Dev Experiment

**Reference: AI-only Silver ratings, NOT human-validated Gold.** Dev result is exploratory and not held-out.

Search document uses Problem, Task and Context ONLY. Runtime perspectives generated independently from query; GPT-only rerun 3 times on 84 cases.

| Method | Recall@10 | Perspective Coverage@10 | Derived Strategy Proxy@10 |
|---|---:|---:|---:|
| single_bm25 | 0.225 | 0.650 | 0.643 |
| single_dense | 0.567 | 1.000 | 0.833 |
| gpt_only_pass1 | 0.567 | 0.900 | 0.740 |
| gpt_only_pass2 | 0.592 | 0.967 | 0.785 |
| gpt_only_pass3 | 0.509 | 0.900 | 0.765 |
| mp_bm25 | 0.268 | 0.683 | 0.598 |
| mp_dense | 0.486 | 0.967 | 0.867 |

Interpret improvement jointly with coverage and unique cases; do not claim statistical superiority from 10 Dev queries.
