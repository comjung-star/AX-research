# v2.3 Professor Search-Core: preserving Dense + Sparse hybrid candidates

Date: 2026-10-24. This is an **exploratory Dev implementation** based on the frozen professor's Search Core diagram and `docs/research-plan.md` sections 4.1–4.4. It is NOT a post-hoc modification to any archived Stage1–4 metrics, nor an independently held-out Test.

## Architecture fidelity

LLM-generated perspectives (replay frozen 97 outputs) → frozen BGE-M3 perspective and case **Problem / Task / Context Multi-view** (currently equal-mean as the supported comparator; frozen learned gate has not demonstrated improvement) → branch-wise **Dense + Kiwi BM25** → **Candidate Union (Top-M per retrieval leg)** without dropping dense cases → **Query–Case Interaction** learned on **other queries only**, producing per-perspective scored TopK → preserve branch identity and case source provenance for subsequent evidence pooling.

**No assumption** that the professor means original-query Dense plus multi-perspective Dense: in the drawing 'Hybrid' explicitly means **Dense + Sparse**. Graph retrieval belongs to the larger FAME-AX proposal, not the pictured Search Core, and is not included here. The professor diagram has Top-M and Top-K, so 'unlimited candidates' is not claimed. The current study has only 84 cases.

## Input reuse, no paid API or rerunning GPT

- Existing 84 frozen `data/v2_3/main_cases_v2_3.json` and `data/v2_3/ground_truth/silver_dev_qrels_2520.csv` unchanged.
- Read frozen `experiments/v23_dev/stage1/fixed_bge_m3_embeddings.npz`, `generated_runtime_perspectives.json`, and `branch_rankings.csv` for Dense, Kiwi BM25 and branch IDs. No model calls, no new tokenization or embedding runtime drift.
- Store outputs only under `experiments/v23_hybrid_preserving/`. Never overwrite `experiments/v23_dev`.

## Controlled candidate configurations, specified prior to running

A. `dense20`: per generated perspective, **multi-view equal-mean Dense** Top20. 20 retrieval slots per branch.
B. `replace10_10`: Dense Top10 + BM25 Top10, 20 slots per branch. **Historical v2.3 hybrid comparator**.
C. `preserve20_add20`: Dense Top20 + BM25 Top20, 40 retrieval slots per branch. **Professor-aligned preserving union**.
D. `dense40_equal_slots`: Dense Top40, 40 slots per branch. **Fair same-slot control**.
E. `preserve20_add10`: Dense Top20 + BM25 Top10, 30 slots per branch.
F. `dense30_equal_slots`: Dense Top30, 30 slots per branch.

Each branch candidate union deduplicates case ID and keeps dense_rank, bm25_rank and provenance (DENSE/BM25/BOTH). Also compute **cross-branch** candidate union for query-run diagnostics but do not prematurely collapse branch outputs.

The per-branch dense leg is `mean(cosine(perspective, case_problem), cosine(perspective, case_task), cosine(perspective, case_context))`, matching frozen stage2-1 representation; BM25 is the preserved Stage1 branch sparse ranking (problem/task/context text). Different slot budgets must not be compared as if equal.

## Query–Case Interaction test

Per query held out for evaluation, train a deterministic MLP on *other 9 queries only*, including all repetitions, with candidate pools from the same configuration. Use frozen case embeddings and frozen perspective embeddings projected through **fixed-seed random 48-dimensional matrix** as in v2.3 Stage2 script. Interaction features `[q, c, q*c, abs(q-c)]`, 192→64→1, BCE with class weighting, seed=42, Adam lr=0.003, weight decay 0.003, 32 epochs; feature projection trained on **no relevance labels**. Do not use a target query's Silver labels in training, and never make GT a candidate selection feature.

For each candidate branch output sort by MLP score; preserve **per-perspective Top5/10/20** independent of global union. Also compute optional *diagnostic* unique global Top10 and Top20 via branch-balanced selection, not as the professor's per-perspective output.

To isolate learned reranking, a non-learning per-branch RRF(60) rank baseline on the **same candidate pool** (dense rank and BM25 rank) is used for fair comparison; neither model reads labels at inference.

## Primary evaluation and integrity

- Candidate stage: number of unique cross-branch candidates; query macro recall across all positives (=union of three AI-Silver reference perspectives, median >=3); relevant added/lost; branch coverage; unique-relevant discovery vs Single Dense at **matching K**, not simply larger pool.
- Equal-slot comparisons `preserve20_add20 vs dense40_equal_slots`, `preserve20_add10 vs dense30_equal_slots`, historical `replace10_10 vs dense20`.
- Per-perspective output: top K counts, unique IDs, provenance; evaluated with Silver **reference** perspectives only as secondary diagnostic (generated P1...Pk are not assumed one-to-one with reference P1..P3).
- Final diagnostic selection RRF vs MLP with same fixed pool, K=5/10/20. Macro over **10 questions**; 3 repetitions grouped within each question. Same trained model cannot see held-out query's relevance labels. Explain that dev Silver labels are LLM-based and the 84-case corpus is not independent of dev.
- If reranking degrades quality, retain result and do not silently tune. Do not claim learned gate, Graph retrieval, final Stage3/4 evidence pooling, or full FAME-AX end-to-end tested from this experiment. Report missing pieces clearly.

## Acceptance gates

1. Frozen original data and artifacts not modified.
2. Candidate union contains every Dense Top20 item and every BM25 Top20 item for `preserve20_add20`.
3. No duplicate case IDs in any per-branch union or perspective TopK; deterministic tie breaks.
4. Branch ID/provenance persisted, and target query disjoint from train queries for all LOQO folds.
5. Candidate size <= slots per branch; cross-branch union no duplicates; same-slot comparisons explicitly named.
6. Exit nonzero for missing frozen files, invalid 84-case labels, or incomplete branch rankings; publish saved metrics and run logs only on successful execution.
