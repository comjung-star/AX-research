# 실행 검증 · 2026-10-28

- 기준 ba5308d1619e53ee8b1b6c223480a439f5adcf8b, 독립 브랜치 research/professor-demo-20261028.
- 기존 단위 테스트: semantic_mapping, functional_mapping, BM25 총 27 passed (3.08s).
- 실제 서버 127.0.0.1:8766, CPU 로컬 BGE-M3 warmup 완료.
- HTTP 실추론: 예시 3개 결합 C + 동일 고객문의 입력 A/B/Dense/BM25 = 7회 통과. 112개 후보, 중복 없는 Top5, 내림차순, Task·출처 식별자 존재 확인. 빈 입력 400 확인.
- 측정 시간 0.44~0.52초. 이 PC의 준비 완료 후 측정이며 최초 모델 로딩 시간과 다른 PC 속도를 보장하지 않음.
- 10개 보존 파일 SHA256 검색 전후 일치. 기준 커밋과 내용 비교도 수행. 기존 설정 및 알고리즘 수정 없음.
- 화면: 예시 버튼 → 검색 → 실제 추천 카드 5개 → 첫 카드 세부 정보 펼침 확인. 한글 정상 표시. Task/Action/Object/Context/UNKNOWN Output/원문 출처 링크 확인.
- 문서 추출 예시 첫 결과: EY 세무 문서 데이터 추출, 상대 점수 0.9095, 규칙 4/4, 의미 0.6380. 이는 관련도 정답 판정이 아닌 실제 출력 기록.
- 외부 API 0회. 독립 Test 파일 열람·실행 없음. Gold 성능 주장 없음.
- 상세 출력 verification.json, 화면 demo-screen.png 참조.
