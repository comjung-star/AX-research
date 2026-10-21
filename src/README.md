# Source Code

연구 모델 구현 코드를 저장합니다.

## 현재 구현 — RQ1 Stage 1

```text
src/ax_research/
├─ data.py          # Main Dataset / Query / Relevance / Gold 공통 로더
├─ config.py        # Frozen RQ1 YAML config 로더
├─ evaluation.py    # Recall / Perspective Coverage / Strategy Coverage 등
├─ selection.py     # branch-balanced unique selection
├─ rq1_runner.py    # Single-query BM25/Dense 공통 실행기
└─ retrieval/
   ├─ bm25.py       # Kiwi + BM25
   └─ dense.py      # BAAI/bge-m3 Dense Retrieval
```

### 중요한 구현 원칙

- Query는 `business_problem_query`만 사용
- Case 검색문서는 Problem / Task / Context만 사용
- Strategy / AI Technology / Implementation / Outcome은 Retrieval 입력에서 제외
- BM25와 Multi-Perspective BM25는 같은 retriever 구현을 공유
- Dense와 Multi-Perspective Dense는 같은 BGE-M3 구현을 공유
- 모든 시스템은 동일한 evaluation 함수로 채점

### 실행 준비

```bash
python -m pip install -e .
python -m pip install -r requirements-rq1.txt
```

BM25:

```bash
python -m ax_research.rq1_runner --system bm25
```

Dense:

```bash
python -m ax_research.rq1_runner --system dense
```

결과는 기본적으로 `experiments/rq1_retrieval/runs/` 아래에
`rankings.csv`, `metrics.csv`, `summary.json`으로 저장됩니다.

LLM 관련 GPT-only / Perspective Generator 구현은 API 모델명 확정 후 추가합니다.
