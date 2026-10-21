# Tests

데이터 변환, 검색 점수, 평가 지표 등 재현성이 필요한 로직의 테스트를 관리합니다.

현재 테스트:
- `test_evaluation.py` — Recall / Coverage / Unique Gold Recovery / 반복 Run 요약
- `test_selection.py` — branch-balanced unique selection
- `test_frozen_dev_data.py` — Frozen Dev 데이터 건수/상태
- `test_bm25.py` — 간단한 한국어 BM25 ranking
- `test_dense.py` — Dense 입력 검증

실행:

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
```

BGE-M3 실제 모델 다운로드/추론은 무거운 통합실험에 해당하므로
기본 unit test에서는 모델 다운로드를 강제하지 않습니다.
