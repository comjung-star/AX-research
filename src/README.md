# Source Code

연구 모델 구현 코드를 저장합니다.

## 현재 구현 — RQ1 Stage 1

```text
src/ax_research/
├─ data.py                 # Dataset / Query / Ground Truth 공통 로더
├─ config.py               # frozen YAML config 로더
├─ evaluation.py           # Recall / Perspective / Strategy Coverage
├─ selection.py            # branch-balanced unique selection
├─ runner.py               # BM25/Dense 공통 single-query runner
├─ cli.py                  # BM25/Dense 실행 CLI
├─ gpt_only_runner.py      # GPT-only 3회 반복 실행기
├─ retrieval/
│  ├─ bm25.py              # Kiwi + BM25
│  └─ dense.py             # BAAI/bge-m3 Dense Retrieval
└─ llm/
   ├─ prompts.py            # Prompt source of truth
   ├─ schemas.py            # Structured Output schema
   └─ client.py             # OpenAI Responses API client
```

## 구현 원칙

- Query는 v1 명세대로 `business_problem_query`만 사용
- Retrieval Case 문서는 Problem / Task / Context만 사용
- Solution View는 검색 입력에서 제외
- 모든 검색방식이 동일한 `evaluation.py` 사용
- Multi-Perspective final output은 `branch_balanced_unique`
- API key는 코드/Repository에 저장하지 않음

## 실행 예시

의존성:

```bash
pip install -r requirements-rq1.txt
```

Single-query BM25:

```bash
PYTHONPATH=src python -m ax_research.cli bm25
```

Single-query Dense:

```bash
PYTHONPATH=src python -m ax_research.cli dense
```

LLM 실행부는 구현되어 있으나 실제 API 호출은 실행환경/API key 준비 후 수행한다.

## 다음 구현

- Multi-Perspective branch query 구성방식 확정
- Multi-Perspective + BM25 runner
- Multi-Perspective + Dense runner
- 3-run 결과 summary / variability aggregation
