# Tests

RQ1 구현의 재현성과 계산 오류를 자동 검증합니다.

현재 테스트 범위:
- Frozen v1.2 config
- Frozen Dev 데이터 100 Case / 10 Query / 3000 labels
- Recall / Perspective Coverage / Strategy Coverage
- Gold gained / lost / net
- branch-balanced unique selection
- Perspective-only branch query
- Duplicate candidate rate
- BM25 기본 ranking
- Dense 입력 검증
- GPT-only 반복 실행 runner
- Prompt leakage 방지
- Single-query runner
- Baseline vs Multi-Perspective 비교 diagnostics
- 반복 Run summary

GitHub Actions:
- `.github/workflows/rq1-tests.yml`

로컬 실행:

```bash
python -m pip install -e .
python -m pip install pytest PyYAML pydantic numpy
pytest -q
```

BGE-M3 실제 모델 다운로드와 OpenAI API 호출은 unit test에서 강제하지 않습니다.
이는 실제 Dev experiment 실행 단계에서 검증합니다.
