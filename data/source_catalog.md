# Source Catalog

이 문서는 AX 사례 데이터셋 구축에 사용할 **공개·검증 가능한 원천(source pool)** 을 관리합니다.

## 국내 공공기관

### NIPA 국내 대표 AI 기업·서비스 사례집

- 발행기관: 정보통신산업진흥원(NIPA)
- 공개일: 2025-01-06
- 국문/영문 PDF 제공
- 국내 대표 AI 기업·서비스의 Use Case를 기업 설문·직접조사·자문회의 등을 거쳐 수록
- 활용방향: 국내 기업 사례의 핵심 원천으로 사용

Source:
https://www.nipa.kr/home/bsnsAll/3/nttDetail?bbsNo=1&nttNo=15766&tab=3

### NIA 공공부문 AI 도입·활용 사례집

- 발행기관: 한국지능정보사회진흥원(NIA)
- 공개일: 2025-12-29
- 공공기관의 AI 도입·활용 실증 사례 수록
- 활용방향: 기업 AX와 직접 비교가 어려운 사례는 보조 데이터 또는 별도 실험군으로 구분

Source:
https://nia.or.kr/site/nia_kor/ex/bbs/View.do?bcIdx=28925&cbIdx=27974&parentSeq=28925

### NIA 공공 AI 서비스 실증 사례집 / 해외 AI 활용 사례 인벤토리

- 「공공부문 초거대 AI 도입·활용 가이드라인 2.0」 부록
- 공공 AI 서비스 실증 사례 110건과 해외 AI 활용 사례 인벤토리 제공
- 활용방향: 문제/업무/맥락 구조화 예시와 추가 검증용 후보 풀로 사용

Source:
https://www.nia.or.kr/site/nia_kor/ex/bbs/View.do?bcIdx=27985&cbIdx=99953

## 글로벌 공식 Customer Stories

Pilot Dataset은 현재 아래 공식 공개 Customer Story에서 사례를 추출합니다.

- AWS Customer Stories
- Microsoft Customer Stories
- Google Cloud Customer Stories
- IBM Case Studies

원칙:
- 벤더 블로그나 제3자 요약보다 **공식 Customer Story 원문을 우선**합니다.
- 본문 전체를 저장하지 않고 연구 스키마에 필요한 내용을 **요약·구조화**합니다.
- source 컬럼에 원문 URL을 남깁니다.
- Business Problem / Task / Context는 원문에서 구조화하되 해결책을 Problem View에 섞지 않습니다.
- Root Cause Factor는 원문을 수집한 뒤 별도 Blind RCA 단계에서 부여합니다.

## Current Pilot

`pilot_cases.csv`에는 공식 공개 Customer Story 기반 20건을 1차 수록했습니다.

- Root Cause Factor: 아직 Blind RCA 전이므로 `PENDING_BLIND_RCA`
- Strategy: 현재 연구계획서의 초기 taxonomy를 사용한 **임시 매핑**
- 최종 학습 데이터로 확정하기 전 원문 재검증과 Pilot 품질검토 필요
