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


## 구현 상태 — 2026-10-21

완료:
- Common Data Loader
- Common Evaluation Engine
- Branch-balanced unique selection
- Single-query BM25 Retriever
- Single-query BGE-M3 Dense Retriever
- 공통 baseline runner / 결과 CSV·JSON schema
- Unit test 코드

대기:
- GPT-only
- Perspective Generator
- Multi-Perspective BM25/Dense pipeline

LLM 구현 전 API에서 사용할 실제 모델 ID를 확정해야 한다.


## 구현 업데이트 — GPT-6 Luna / Multi-Perspective pipeline

- 공통 LLM: `gpt-6-luna`
- GPT-only runner 구현
- Perspective Generator 구현
- Multi-Perspective + BM25 / Dense 공통 runner 구현
- 두 branch query 방식 모두 코드로 지원
  - `perspective_only`
  - `original_plus_perspective`
- 잘못 생성된 중복 runner는 제거하고 `runner.py`를 공통 Single-query runner로 유지
- GitHub Actions 테스트 workflow 추가
- 2026-10-21 기준 unit test workflow: **SUCCESS**

실제 Multi-Perspective Dev 실행 전 남은 결정:
- 각 Perspective branch에 검색 입력을 Perspective만 줄지,
  Original Business Problem과 Perspective를 함께 줄지 Primary 규칙을 확정해야 함.
