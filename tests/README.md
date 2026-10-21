# Tests

데이터 변환, 검색 점수, 평가 지표 등 재현성이 필요한 로직의 테스트를 관리합니다.

현재 테스트 대상:
- Recall@K
- Perspective Coverage@K
- Strategy Coverage@K
- Unique Gold Recovery
- Perspective Gold threshold
- branch-balanced unique selection
- 공통 Runner CSV 출력
- GPT-only 3회 반복 Runner
- LLM Prompt에서 Business Problem only / Solution leakage 방지

2026-10-21 구현 시 로컬 pytest 기준 **11 tests passed**.
