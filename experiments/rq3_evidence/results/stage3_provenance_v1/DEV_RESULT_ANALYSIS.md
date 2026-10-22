# Stage 3-2A — Perspective Provenance Dev Result Analysis

Date: 2026-10-22
Status: **COMPLETE — STRUCTURAL DIAGNOSTIC ONLY**
Protocol: `docs/experiment-spec-stage3-perspective-provenance-v1.md`
Implementation: `src/ax_research/stage3_perspective_provenance.py`
GitHub Actions: [Stage 3-2A replay](https://github.com/comjung-star/AX-research/actions/runs/39743868005) SUCCESS; [existing regression suite](https://github.com/comjung-star/AX-research/actions/runs/39743867801) SUCCESS.

## What was tested

Frozen `stage2_same_pool_rrf` Top-10 ranking was replayed only as an
unchanging retrieval **reference**. The original Stage 2-3 Hybrid candidate
provenance ledger was joined by Query, Run, Case and `leg_k=10`.
This does **not** adopt RRF as the professor-proposed Search Core.

## Observed frozen Dev results

| Indicator | Observed |
|---|---:|
| Dev Queries | 10 |
| Repeated perspective runs | 3 |
| Query/Run groups | 30 |
| Ranked Case occurrences (Top-10) | **300** |
| Candidate perspective links recovered | **641** |
| Links beyond one representative source | **341** |
| Ranked Cases with 1 matching perspective | 80 |
| Ranked Cases with 2 matching perspectives | 110 |
| Ranked Cases with 3 matching perspectives | 99 |
| Ranked Cases with 4 matching perspectives | 11 |
| Ranked Cases matched in 2+ perspectives | **220/300 (73.3%)** |
| Ranked Cases with missing candidate provenance | **0** |
| Ranked Cases retaining selected perspective | **300/300** |

Expanded link counts by perspective ID: P1=211; P2=203; P3=207; P4=20.
These are **not** counts of independently retrieved ranked Cases.
There is no enforced three-perspective limit.

Candidate-source composition across all 641 expanded links:
`both`=400, `dense`=136, `sparse`=105. Here `both` means the candidate
was seen in both Dense and Sparse within a particular perspective branch.

## Why it matters

A displayed top-ranked Case may be related to more than one dynamic
problem perspective. The final ranking carries one representative source;
the expanded read-only ledger preserves additional legitimate evidence paths.
A one-to-one join to `source_perspective_id` would discard that information.

**No change** to the original case ranking, retrieved Case count,
Ground Truth labels, relevance scores, pretrained embeddings or Wald evidence.

## Hard limits and next experiment

This is evidence **traceability and provenance completeness**, not a gain
in Recall@K, Strategy Coverage@K, Factor reliability, recommendation accuracy,
or held-out generalization. 300 is the Case-occurrence denominator; 641 is
the expanded branch-link denominator.

Next Stage 3-2B: using this ledger, join preassigned Blind-RCA Factor labels,
observed implemented Strategy labels (separate Solution View), and frozen
offline Factor–Strategy Wald diagnostics. Do not let Strategy labels influence
Root Cause reconstruction. Stage 3-2C should audit evidence statuses with
prespecified denominators before any Stage 4 model-efficacy claims.
