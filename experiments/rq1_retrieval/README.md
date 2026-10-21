# RQ1 Retrieval Experiments

이 폴더는 RQ1의 첫 번째 검색실험을 관리한다.

핵심 질문:

> Single-query 검색보다 LLM Multi-Perspective branch 검색이 관련 AX 사례의 Recall과 Perspective Coverage를 개선하는가?

기준 문서:
- `docs/experiment-spec-rq1-v1.md`
- `configs/experiment_rq1_v1.yaml`
- `data/dev_ground_truth_freeze_v1.md`

계획된 비교:
1. Single-query BM25
2. Single-query Dense
3. GPT-only
4. Multi-Perspective + BM25 (diagnostic)
5. Multi-Perspective + Dense (primary Stage 1)

실행 결과가 생기면 이 폴더 아래에 config snapshot, ranking, metrics, summary를 실험 ID별로 보존한다.

명세 v1은 `FROZEN_FOR_IMPLEMENTATION` 상태다. 실제 구현은 공통 Data Loader / Evaluation Engine부터 시작하며, Dev 실험에서 보완이 필요하면 버전을 올려 변경 이력을 남긴다.


## Implementation status — 2026-10-21

구현 완료:
- Common Data Loader
- Common Evaluation Engine
- Kiwi + BM25 Retriever
- BGE-M3 Dense Retriever
- branch-balanced unique selector
- Single-query BM25/Dense common runner + CLI
- OpenAI Structured Output client
- Perspective Prompt / GPT-only Prompt
- GPT-only 3-run runner

검증:
- 로컬 unit test: **11 passed**

아직 실제 실험결과는 생성하지 않았다.
다음은 Multi-Perspective branch에 어떤 검색문장을 전달할지 확정한 뒤 BM25/Dense pipeline을 연결한다.
