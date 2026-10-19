# Source Catalog

이 문서는 AX 사례 데이터셋 구축에 사용할 **공개·검증 가능한 원천(source pool)** 을 관리한다.

## 1. NIPA 국내 대표 AI 기업·서비스 사례집

- 발행기관: 정보통신산업진흥원(NIPA)
- 발행: 2024-12 / 홈페이지 게시 2025-01-06
- 국내 AI기업 설문·직접조사·자문을 거쳐 52개 대표 기업·서비스 선정
- 국문/영문 PDF 제공

Source:
https://www.nipa.kr/home/bsnsAll/3/nttDetail?bbsNo=1&nttNo=15766&tab=3

### Core Pilot에 추가한 NIPA-backed 8건

| Case | 기업 | 분야 | NIPA page |
|---|---|---|---:|
| AX0035 | Lunit | Healthcare | 12-13 |
| AX0036 | SuperBin | Environment | 20-21 |
| AX0037 | SI Analytics | Environment / GEOINT | 22-23 |
| AX0038 | RexGen | Transportation | 36-37 |
| AX0039 | Mathpresso | Education | 44-45 |
| AX0040 | December & Company | Finance | 50-51 |
| AX0041 | AIZEN Global | Finance | 54-55 |
| AX0042 | Law&Company | Legal | 58-59 |

가능한 경우 NIPA 문서만 사용하지 않고 기업 공식 페이지, 정부 우수사례, 공식 Customer Story를 함께 대조했다.

---

## 2. 글로벌 공식 Customer Stories

초기 Core Pilot에 사용:

- AWS Customer Stories
- Microsoft Customer Stories
- Google Cloud Customer Stories
- IBM Case Studies

원칙:
- 공식 Customer Story 원문 우선
- 원문 전체 복제 금지
- 연구 스키마에 필요한 내용만 요약·구조화
- source URL 보존

---

## 3. 국내 공개 산업 사례

### MakinaRocks
제조·자동차·에너지·화학의 Prediction / Optimization 부족 영역을 보완하기 위해 11건 사용.

Source:
https://www.makinarocks.ai/use-cases/

### 한국축산데이터 / MSIT
가축 행동분석·질병 사전예측 사례.

Source:
https://eiec.kdi.re.kr/policy/materialView.do?num=211732

### LaonPeople
AI Vision 기반 반복 육안검사 자동화.

Source:
https://laonpeople.com/ai-vision-solution/

### MICUBE Solution
SMD 라인 불량 사전예측 사례.

Source:
https://www.micube.co.kr/news/view/208

---

## 4. 마지막 Diversification Batch의 보조 검증 원천

- Lunit official real-world deployment
- SuperBin official Nephron page
- SI Analytics official solution page
- RexGen official solution page
- K-Global Mathpresso success case
- fint official AI investment page
- AIZEN official CreditConnect deployment
- Microsoft / Law&Company customer story

이 보조 원천은 NIPA 요약정보와 실제 구현·성과의 정합성을 확인하기 위해 사용했다.

---

## 5. Supplemental Public Set

기업 AX와 공공부문 AI의 분포 차이를 유지하기 위해 공공사례는 Core와 분리했다.

- K-water AI 정수장
- AI 홍수예보
- 특허청 AI 특허심사 지원

File:
`supplemental_public_cases.csv`

---

## 6. Current Dataset Status

### Core Pilot
- **42건**
- Blind RCA 완료
- Strategy labeling 완료
- QA metadata 완료
- Root Cause Dictionary v1 Freeze
- Strategy Taxonomy v1 Freeze
- **Pilot 종료**

### Supplemental
- **4건**

### Main Dataset v1
- **100건**
- AX0001~AX0100
- QA 100건
- Root Cause v1 / Strategy v1 동일 적용
- 2026-10-19 **v1 Freeze**

### Supplemental
- **4건**

### Next
Retrieval Ground Truth를 구축한다.

Main Dataset에 추가 사례가 발견되더라도 현재 AX0001~AX0100은 v1 실험 기준으로 유지하고, 추가분은 확장셋 또는 차기 버전으로 분리한다.


## 7. 공개 PDF/XLSX Screening

추가로 다음 공개 원천을 검토했다.

- KOSA AX 사례집
- NIA 공공AI 서비스 실증 사례집 110건
- NIA 해외 AI 활용 사례 인벤토리 XLSX
- 2026 AI 정부 서비스 사례집
- Deloitte 식품·식자재 유통 생성형 AI PDF
- Deloitte 생성형 AI 활용서 6대 산업 PDF
- WEF AI-First Operating System
- Federal Reserve AI Use Case Inventory

상세 결과:
- `public_source_screening.md`
- `main_candidate_pool.csv`
- `supplemental_candidate_pool.csv`

Main Dataset에 바로 편입 가능한 것으로 검증된 10건은 AX0043~AX0052로 `main_cases_v1.csv`에 반영했다.

공공기관 중심 대량자료(NIA 110건, Federal Reserve Inventory)는 기업 AX Main 분포를 왜곡하지 않도록 Supplemental/외적 타당성 검증용으로 분리한다.


## 8. 실전 AX 리포트 및 100건 확장

『실전 AX 리포트』 PART 5 13건을 별도 검증했다.

- Main 편입: 7건 (AX0053~AX0059)
- Supplemental: 1건 (PUB0004)
- HOLD: 5건

이후 Microsoft, AWS, Google Cloud, IBM 및 국내 기업 공식 고객사례를 추가 검증해 AX0060~AX0100을 구축했다.

최종 Main Dataset v1은 **100건**이며 상세 검증은 `main_dataset_validation_v1.md`를 따른다.
