# AX v2.3 Stage 1 관점별 결과 분리·보존 재분석 프로토콜

기록일: 2026-10-24. **실험 결과 확인 전 고정하는 분석계획**. 기존 Stage 1 frozen 결과 보존.

## 배경 → 문제점 → 방안
- 배경: 업무 문제를 LLM이 2~5개 실행 관점으로 분해; 84 AX사례에서 각 관점 검색.
- 문제점: Stage1 원본은 관점별 검색 결과를 round-robin으로 합쳐 전역 K개만 선택. 관련 사례가 개별 관점 상위에 있어도 최종 글로벌 결과에서 탈락할 수 있음.
- 방안: 개별 관점별 Top-K 결과를 별도로 보존하고, 평가 시에만 중복 제거 합집합을 산출.

## 실험 설계
- Frozen source: release/ax-v2.3-stage1-to4-dev-20261023. Branch: experiment/v23-stage1-perspective-separation-20261024.
- 입력: 84 cases, 10 Dev questions x 3 repeats, 97 generated runtime perspectives, original Dense and BM25 complete per-branch rankings, GPT-generated runtime perspectives, AI Silver qrels 2520, frozen NPZ embeddings. No fresh LLM/embedding calls.
- K=5,10,20; methods=original Dense and BM25, separately (not newly implemented hybrid).
- A: MP-global@K; frozen original branch-balanced global TopK. Recompute and verify exact match saved rankings.
- B: MP-separated@K per branch; preserve all perspective case lists and evaluate only their deduplicated union with candidate count N.
- C: Single Dense and Single BM25 @K original reference.
- D: matched budget Single Dense@N, N equals B distinct candidate count; reconstruct single Dense full ranking by frozen dot products; verify first 20 against frozen single Dense.
- E: matched budget MP-global@N, branch-balanced global top-N diagnostic. At N fixed to B, compare search result grouping versus count effect.
- F: for every relevant case in SingleDense@10 missed by MP-global@10, classify minimum branch dense rank: <=10 / 11-20 / >20; log qid, run, case and provenance. Note count uses 30 query-run appearances (not unique cases).
- Reference positives: relevance>=3 in union across Silver reference perspectives. Runtime-generated P1..P5 IDs are NOT the same definitions as reference P1..P3 IDs. Reference view coverage: fraction of non-empty Silver views with >=1 selected case.
- Report query-run macro mean, per-query paired delta, positive gain/loss, candidate count, reference view coverage, exact examples, source records.
- Stage1 saved values MP Dense global Recall@10=45.30% and Single Dense Recall@10=53.32% are regression invariants.
- Expect B Recall >= A possibly because B retrieves more cases. This is not controlled evidence of retrieval improvement; use D/E to interpret.
- New outputs only in experiments/v23_stage1_perspective_separation; do not modify frozen originals. Independent human Gold/test not represented.
- No Stage2/3/4 neural training, Gated Fusion, Query-Case reranking, Graph or recommendation in this experiment.

## Report
Organize final note: 배경 / 문제점 / 방안 / 문제를 해결하기 위한 설계 / 비교 / 판단 / 다음 실험.
