# Source Code

RQ1 Stage 1 구현 코드를 저장합니다.

## 구조

```text
src/ax_research/
├─ config.py
├─ data.py
├─ evaluation.py
├─ selection.py
├─ runner.py
├─ gpt_only_runner.py
├─ multi_perspective_runner.py
├─ comparison.py
├─ summary.py
├─ cli.py
├─ llm/
│  ├─ client.py
│  ├─ prompts.py
│  └─ schemas.py
└─ retrieval/
   ├─ bm25.py
   └─ dense.py
```

## 중요한 구현 원칙

- Primary Query는 `business_problem_query` only
- Case Retrieval 문서는 Problem / Task / Context only
- Solution View는 검색 입력에서 제외
- GPT-only와 Perspective Generator는 동일 `gpt-6-luna`
- Multi-Perspective branch 검색은 **Perspective only**
- BM25/MP-BM25는 같은 Kiwi/BM25 구현 공유
- Dense/MP-Dense는 같은 BGE-M3 구현 공유
- 최종 Top-K는 branch-balanced unique
- Unique Gold Recovery는 lost Gold와 net까지 함께 봄
- 모든 시스템은 동일 Evaluation Engine 사용

## 실행 준비

```bash
python -m pip install -e .
python -m pip install -r requirements-rq1.txt
```

실행은 `python -m ax_research.cli <system>` 형식을 사용합니다.
