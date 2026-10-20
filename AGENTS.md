# AGENTS.md

## Project purpose

This repository contains the implementation and research artifacts for:

**기업 업무문제 기반 다중관점 AX 사례 검색·전략 추천 모델 연구**

The research plan in `docs/research-plan.md` is the primary project document.

## Source of truth

When implementing or modifying the model, use the following priority:

1. Professor-proposed architecture attached to the 2nd feedback document
2. `docs/research-plan.md`
3. Explicit decisions documented in this repository
4. New implementation ideas only when they do not change the architecture's intent

Do **not** redesign the research model simply because another implementation looks cleaner.

If an implementation detail is not specified, choose the smallest testable option and document it as an experimental choice rather than presenting it as professor-confirmed.

## Architecture guardrails

The current target architecture is based on:

- **LLM-Augmented Multi-View Neural Search Model for AX Cases**
- **FAME-AX + LLM: LLM-augmented Factor-Anchored Multi-view Evidence Recommender**

Preserve the following overall flow:

```text
Business Problem Query
→ LLM Query Understanding
  → Perspective Decomposition
  → Synonym / Taxonomy Expansion
  → Structured Problem Parsing
→ Multi-view Embedding
  → Problem View
  → Task View
  → Context View
→ View Combination
  → Gated Fusion / Attention
→ Hybrid Retrieval
  → Dense Retrieval
  → Sparse Retrieval
  → Graph Retrieval when experimentally justified
→ Candidate Union
→ Query-Case Interaction Neural Network
→ Perspective-specific Top-K Cases
→ Case Evidence Pooling
→ Root Cause Factor Anchor
→ Wald Evidence
→ Evidence Fusion
→ LLM Reasoning & Recommendation Head
→ Recommended Strategies
  + Traceable Evidence Path
  + Actionable Explanation
  + Confidence / Priority
```

## Non-negotiable research decisions

### Multi-perspective search

- One business problem may produce multiple valid perspectives: `P1 ... Pk`.
- Perspectives must be preserved as separate branches through retrieval and recommendation.
- Do not collapse perspectives into one global ranking too early.
- Perspective decomposition generates problem viewpoints, not solutions.
- Gold perspectives are evaluation references only; they are **not** fixed runtime perspectives or prompts.
- At runtime, the LLM must dynamically generate `P1 ... Pk` from each user Business Problem Query.
- The number of generated perspectives is not fixed to three unless an experiment explicitly imposes that constraint.

### Multi-view representation

Keep these views separate before fusion:

- Business Problem
- AX Target / Task
- Business Context

Do not reduce the case to one dense embedding before the multi-view stage.

### RRF is not part of the proposed model

- Do **not** use RRF or Weighted RRF as the proposed architecture.
- Earlier RRF-based designs are obsolete and should not be reintroduced unless explicitly requested as a historical baseline.

### Hybrid Retrieval

- Retrieval is for candidate generation / recall.
- Dense, Sparse, and Graph retrieval may contribute candidates.
- Candidate results are unioned before neural relevance scoring.
- Graph Retrieval is subject to stepwise validation; do not treat it as mandatory if experiments show no benefit.

### Query-Case Interaction

The interaction network performs fine-grained relevance scoring between one perspective and one candidate case.

A professor-proposed interaction form includes:

```text
[q, c, q ⊙ c, |q - c|]
→ MLP
→ Relevance Score
```

Perspective-local ranking is allowed; cross-perspective global ranking should not erase branch identity.

### Root Cause / Factor Anchor

- Root Cause is a shared factor/anchor, not merely a post-hoc explanation.
- Build Root Cause Factors offline from the **Problem View**.
- Keep Solution information hidden during Blind RCA to reduce target leakage.
- Query and retrieved evidence may align to pre-structured Root Cause Factors.
- Multi-label Root Cause is allowed if supported by the data and experiment design.

### Wald Evidence

Wald analysis is statistical evidence for:

```text
Root Cause ↔ Strategy
```

Use it as evidence, not as the recommender itself.

- Interpret β / Odds Ratio / p-value as association evidence.
- Do not claim causality from Wald results.
- Prefer offline precomputation and online lookup.
- Check sample sparsity before trusting statistical conclusions.

### Evidence Fusion

Evidence Fusion happens **after retrieval** and combines evidence such as:

- Branch / Perspective representation
- Case Evidence
- Factor / Root Cause representation
- Wald Evidence

Do not confuse this with the earlier Gated Fusion of Problem / Task / Context.

### Recommendation Head

- Strategy recommendation should be evidence-grounded.
- Prefer a controlled Strategy taxonomy and multi-label prediction over unconstrained LLM invention.
- The LLM may generate explanations and rationale from the evidence.
- Keep final outputs traceable back to retrieved cases and factors.

### Dike

Professor clarification: Dike is fundamentally a discriminant/judgment concept and is reflected in the learning objective / final judgment criteria rather than requiring a separate named module.

- Do not add a standalone Dike block unless explicitly requested.
- Do not invent a new `Dike Loss` formula without experimental justification.
- Preserve branch evidence until late-stage judgment.

## Training objectives

The professor architecture currently includes training objectives such as:

- Ranking Loss
- Multi-view Diversity Loss
- In-batch Contrastive Loss

The full model may also include strategy/factor-related objectives depending on the implemented stage.

Do not invent exact weights or final formulas without an experiment. Treat loss weights as hyperparameters to validate.

## Evaluation priorities

The main research question is whether multi-perspective retrieval improves the discovery of relevant AX cases and strategies compared with simpler approaches.

Primary metrics:

- `Recall@K`
- `Perspective Coverage@K` (auxiliary retrieval metric for checking whether distinct Gold perspectives are represented in retrieved results)
- `Strategy Coverage@K`

Primary baselines:

- Single-query BM25 / sparse lexical retrieval
- Single-query Dense Retrieval
- GPT-only recommendation/judgment

The core comparison is not "dense vs. proposed" alone. The research must test whether preserving multiple problem perspectives improves retrieval over single-query retrieval regardless of whether the single-query baseline is lexical (BM25) or dense.

Use comparable search/output budgets when comparing systems.

For Retrieval Ground Truth:
- Build labels independently from model outputs.
- Use Problem View information (Business Problem / AX Target / Business Context) for case relevance judgment to reduce solution leakage.
- Preserve Gold perspectives separately instead of collapsing them into one global relevance label.
- Store Perspective × Case relevance on a 0–4 scale; the exact Gold threshold and adjudication rule must be documented as an experimental decision before baseline evaluation.
- Derive Gold Strategy Set only after relevant cases are fixed, using the frozen Strategy taxonomy.

Perform staged ablation to test the value of each component.

Examples:

```text
Baseline
→ + Multi-Perspective
→ + Multi-view
→ + Gated Fusion
→ + Hybrid Retrieval
→ + Query-Case Interaction
→ + Factor Anchor / Wald
→ + Evidence Fusion / Recommendation Head
```

If a component does not improve the intended metric or explanation quality, record the result rather than forcing the component to remain.

## Data design

Target AX case dataset: approximately 100–150 cases.

Initial Pilot / Development Set: approximately 20–30 cases.

Key fields should include, where supported by the source:

- Case ID
- Industry
- Business Problem
- AX Target / Task
- Business Context / Condition
- Root Cause Factor
- Strategy (multi-label)
- AI Technology
- Implementation
- Outcome
- Source

Maintain a clear distinction between:

```text
Problem View
- Business Problem
- AX Target / Task
- Business Context

Solution View
- Strategy
- AI Technology
- Implementation
```

Do not infer missing source information silently. Use `UNKNOWN` or an explicit missing value when necessary.

## Research-data safety and copyright

- Do not commit copyrighted books, reports, or case-study full text unless redistribution is clearly permitted.
- Prefer structured summaries, labels, metadata, and source references.
- Do not commit secrets, API keys, tokens, credentials, or private company data.
- Keep sensitive or restricted enterprise data out of the repository unless explicitly approved.

## Implementation style

Use Python for model and experiment code unless there is a strong reason otherwise.

Prefer a modular layout such as:

```text
src/
  query_understanding/
  multi_view/
  retrieval/
  interaction/
  factor_anchor/
  evidence/
  recommendation/

experiments/
docs/
data/
tests/
```

Implementation rules:

- Keep modules small and independently testable.
- Add reproducible experiment configs where practical.
- Fix random seeds when comparing model variants.
- Record experiment assumptions and dataset versions.
- Write tests for data transformations and scoring logic where practical.
- Avoid premature optimization.
- Prefer simple baselines before complex model variants.

## Before making a substantial architectural change

1. Read `docs/research-plan.md`.
2. Check whether the change exists in the professor architecture.
3. If it does not, treat it as an experiment, not a replacement.
4. Preserve the current architecture on `main` unless the user explicitly approves the change.
5. Prefer a branch/PR for substantial experimental changes.

## Current project rule

The goal is not to invent a different recommender.

The goal is to **implement, validate, and refine the professor-proposed architecture step by step without losing its core structure**.
