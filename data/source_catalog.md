# Source Catalog

이 문서는 AX 사례 데이터셋 구축에 사용할 **공개·검증 가능한 원천(source pool)** 을 관리합니다.

## 1. 국내 공공 사례집 / 원천

### NIPA 국내 대표 AI 기업·서비스 사례집

- 발행기관: 정보통신산업진흥원(NIPA)
- 공개일: 2025-01-06
- 국문/영문 PDF 제공
- 국내 대표 AI 기업·서비스 Use Case를 기업 설문·직접조사·자문 등을 통해 수록
- Main Dataset 확장 시 국내 산업·기업 다양화의 핵심 source pool로 사용

Source:
https://www.nipa.kr/home/bsnsAll/3/nttDetail?bbsNo=1&nttNo=15766&tab=3

### NIA 공공부문 AI 도입·활용 사례

공공업무 사례는 기업 AX와 분포가 다르기 때문에 Core Dataset과 섞지 않고 Supplemental / 외적 타당성 검증 후보로 사용한다.

Source:
https://nia.or.kr/

---

## 2. 글로벌 공식 Customer Stories

기존 Core Pilot 20건에 사용:

- AWS Customer Stories
- Microsoft Customer Stories
- Google Cloud Customer Stories
- IBM Case Studies

원칙:

- 공식 Customer Story 원문 우선
- 원문 전체 복제 금지
- 연구 스키마에 필요한 내용을 요약·구조화
- source 컬럼에 원문 URL 보존

---

## 3. 국내 공개 산업 사례

### MakinaRocks

이번 Pilot 확장에 제조·자동차·에너지·화학 분야 11건을 사용했다.

주요 사례:

- Hyundai Motor 산업용 로봇 예지보전
- 전기차 배터리 SDF / Agentic AI 자율제어
- 도면 기반 AI 견적 자동화
- 주문서 표준화 Agent
- 복합수지 물성 예측
- 발효공정 최적운전
- 자동차 도장 환기팬 이상탐지
- 생산 스케줄링 최적화
- 다중로봇 OLP 자동화
- EV HVAC 최적화
- 태양광 발전량 예측

Source:
https://www.makinarocks.ai/use-cases/

### 한국축산데이터 / MSIT

CCTV 기반 가축 행동분석과 질병 사전예측 사례를 사용했다.

Source:
https://eiec.kdi.re.kr/policy/materialView.do?num=211732

### LaonPeople

반복 육안검사의 피로·주관성을 AI Vision으로 보완하는 제조 검사 사례를 사용했다.

Source:
https://laonpeople.com/ai-vision-solution/

### MICUBE Solution

SMD 자동화 라인 설비 데이터를 활용한 불량 사전예측 및 제조 AI 사례를 사용했다.

Source:
https://www.micube.co.kr/news/view/208

---

## 4. Supplemental Public Cases

Core 기업 AX 데이터와 분리하여 다음 3건을 보조셋으로 저장했다.

- K-water AI 정수장
- AI 홍수예보
- 특허청 AI 특허심사 지원

파일:
`supplemental_public_cases.csv`

이 사례들은 taxonomy가 기업 외 업무에서도 설명력을 가지는지 확인하기 위한 stress-test 용도이며 Core 학습분포에는 포함하지 않는다.

---

## 5. Current Dataset Status

### Core Pilot

- 총 **34건**
- 초기 글로벌 사례 20건
- 추가 국내 공개 원천 사례 14건
- Blind RCA 완료
- Strategy Labeling 완료
- Source/QA metadata 기록

### Supplemental

- 공공부문 **3건**

### 다음 Source 우선순위

Core Pilot을 약 40건까지 늘릴 때는 MakinaRocks 추가 수집보다 다음을 우선한다.

1. NIPA 사례집의 비-MakinaRocks 국내 기업
2. 금융 / 물류 / 교육 / 법률 / 환경
3. F02 정보·지식 분산 및 F07 데이터 통합 부족 유형
4. 공급기업이 직접 작성하지 않은 검증 가능한 공공/기업 자료

상세 검증 결과:
`pilot_validation.md`
