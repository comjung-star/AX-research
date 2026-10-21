# RQ1 Retrieval Experiments

핵심 질문:

> Single-query 검색보다 LLM Multi-Perspective branch 검색이 관련 AX 사례의 Recall과 Perspective Coverage를 개선하는가?

## Frozen 기준

- `docs/experiment-spec-rq1-v1.2.md`
- `configs/experiment_rq1_v1.2.yaml`
- `data/dev_ground_truth_freeze_v1.md`

## 비교 시스템

1. Single-query BM25
2. Single-query Dense
3. GPT-only
4. Multi-Perspective + BM25
5. Multi-Perspective + Dense

## Multi-Perspective v1.2 규칙

```text
Business Problem
→ gpt-6-luna가 Perspective 2~5개 생성
→ 각 branch 검색 입력 = Perspective title + description only
→ BM25 또는 BGE-M3
→ branch-balanced unique Top-K
```

Original Business Problem은 Perspective 생성에는 사용하지만,
각 branch Retrieval query에는 다시 붙이지 않습니다.

## 구현 완료

- Common Data Loader
- Common Evaluation Engine
- Kiwi + BM25 Retriever
- BGE-M3 Dense Retriever
- OpenAI Structured Output client
- GPT-only 3-run runner
- Perspective Generator
- Multi-Perspective BM25/Dense runner
- branch-balanced unique selector
- branch provenance 저장
- Branch Jaccard
- Duplicate candidate rate
- Gold gained / lost / net 비교
- 반복 Run summary
- GitHub Actions unit tests

## 실행

설치:

```bash
python -m pip install -e .
python -m pip install -r requirements-rq1.txt
```

실행:

```bash
python -m ax_research.cli bm25
python -m ax_research.cli dense
python -m ax_research.cli gpt-only
python -m ax_research.cli mp-bm25
python -m ax_research.cli mp-dense
```

LLM 시스템은 `OPENAI_API_KEY` 환경변수가 필요합니다.

실제 Dev 결과는 생성 후 이 폴더 아래에 보존합니다.
