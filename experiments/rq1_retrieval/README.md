# RQ1 Retrieval Experiments

이 폴더는 RQ1의 첫 번째 검색실험을 관리한다.

핵심 질문:

> Single-query 검색보다 LLM Multi-Perspective branch 검색이 관련 AX 사례의 Recall과 Perspective Coverage를 개선하는가?

기준 문서:
- `docs/experiment-spec-rq1-v1-draft.md`
- `configs/experiment_rq1_v1_draft.yaml`
- `data/dev_ground_truth_freeze_v1.md`

계획된 비교:
1. Single-query BM25
2. Single-query Dense
3. GPT-only
4. Multi-Perspective + BM25 (diagnostic)
5. Multi-Perspective + Dense (primary Stage 1)

실행 결과가 생기면 이 폴더 아래에 config snapshot, ranking, metrics, summary를 실험 ID별로 보존한다.

아직 명세가 DRAFT 상태이므로 사용자 검토 전에는 실제 baseline 결과를 생성하지 않는다.
