# AX Dataset v2.1.0 — Frozen research case corpus

**Decision (2026-10-22):** The researcher chose to use **91 operational AX workflow cases** and to keep the remaining seven as documented holds, rather than extend the candidate verification cycle.

This version is **frozen as a source-reviewed research corpus**, **NOT human-adjudicated Ground Truth**. No claim of measured model quality, factor–strategy causality or final held-out performance follows from this release.

## Files

| Artifact | Meaning |
|---|---|
| `main_cases_v2_1.json` | 91 immutable source-QA-qualified cases; problem/task/context kept separate from solution/outcome |
| `main_cases_v2_1.csv` | Review/export table for the 91 cases |
| `release_manifest_v2_1.json` | Exact Git blob SHA, provenance and counts; preserves v2.0.0 |
| `source_evidence_index_v2_1.csv` | All 91 cases' official URL, problem/context/implementation/deployment/outcome locator and qualification |
| `factor_strategy_evidence_v2_1.csv` | 64 explicitly reviewed **applicability-not-causality** factor–strategy relations |
| `dev_query_candidates_v2_1.json` | 10 historical Dev **query wordings only**, new v2.1 IDs; 30 draft perspectives |
| `dev_relevance_annotation_sheet_v2_1.csv` | **2730 UNJUDGED** reference-perspective × case slots; not relevance GT |
| `../v2/qa/independent_source_pass3_2026-10-22.json` | 91 provisional vs 7 held individual decisions |
| `../../experiments/rq3_evidence/results/v21_wald_contingency_2026-10-22.csv` | 63 descriptive F–S cells; only 2 have all four counts ≥5 |

**Counts:** 91 cases, 63 source/company/parent sampling groups; 22 factor ABSTAIN, 2 strategy ABSTAIN, 68 jointly annotated cases, 64 explicitly established factor–strategy application links, **0 human Ground Truth approvals**.

## What is finished?

1. Frozen 91-case research corpus, with original data lineage and seven held decisions retained.
2. Dataset integrity and evidence provenance indexing.
3. Separate 5-class outcome basis (note that `MEASURED` also includes provider-reported use/task metrics, **not independently audited causal impact**).
4. Offline F–S contingency diagnostics, with sparsity limitations.
5. v2.1-ready Dev query and unjudged annotation template, retrieval/trace smoke implementation and tests.

## What is NOT finished?

- 2730 independent relevance judgments and independent adjudicator sign-off (historical v1 qrels cannot be transferred).
- A new, independently written held-out Test set and its fully blind relevance Ground Truth.
- Measured `BAAI/bge-m3` model quality / comparative Recall, Perspective Coverage, Strategy Coverage on v2.1.
- Stage 3-2B/Stage 4 actual model-quality experiments and a validated LLM recommendation head. An evidence trace is a wiring prototype, not an outcome.
- Review of the **19 historically relative source locators**. The researcher froze the existing source-curated corpus accepting this documented limitation; the index retains both old and supplementary source anchors.
- Human second reviewer approval of F/S annotations; paper must describe the corpus as source-curated, AI-annotated, **not human GT**.

## Commands

From repository root:

```bash
python scripts/validate_v21_freeze.py
python -m unittest discover -s tests -p "test_v21_*.py" -v

# Dependency-free wiring diagnostic, NOT an embedding model/accuracy evaluation:
python scripts/v21_retrieval_smoke.py --backend char_ngram \
  --query-text "Manual factory production quotation and scheduling requires too much effort" \
  --top-k 10

# Optional research-aligned execution after installing requirements-rq1.txt
PYTHONPATH=src python scripts/v21_retrieval_smoke.py --backend bm25 --query-id V21D001
PYTHONPATH=src python scripts/v21_retrieval_smoke.py --backend bge-m3 --query-id V21D001

# Intentionally fails until relevance labels are independently adjudicated:
python scripts/v21_evaluate.py --rankings path/to/ten_dev_query_results.json
```

Never supply `draft_perspectives` from the GT candidate file to a runtime retrieval engine. The runtime has to generate its own `P1...Pk`. **RRF/weighted-RRF is not the proposed model**; branch-preserving candidate union and source citation are preserved in the smoke pipeline. Proper LLM perspective generation and gated/multiview methods remain in the historical staged experiment code and must be re-run on the v2.1 corpus with genuine GT before comparative claims.

See [freeze and experiment report](../../docs/v21-freeze-and-experiment-report-2026-10-22.md) and [research plan](../../docs/research-plan.md).
