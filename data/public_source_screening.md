# Public Source Acquisition & Screening Review

검토일: **2026-10-14**

목적: 공개 PDF/XLSX/공식 데이터 소스를 실제로 확인하고, 기존 Core Pilot 42건과 중복을 제거한 뒤 **Main Dataset v1 후보**와 **Supplemental 후보**를 분리한다.

> 원본 PDF/XLSX 파일 자체는 저작권·재배포 및 저장소 용량 문제로 GitHub에 복제하지 않는다.  
> 대신 공식 URL, 원문 검증 상태, 후보 선정 결과를 저장한다.

## 1. 전체 결과 요약

| Source | 확보/접근 상태 | 분석 결과 | Main 활용 |
|---|---|---|---|
| NIPA 국내 대표 AI 기업·서비스 사례집 | 공식 PDF 확인 | 기존 Pilot에서 이미 8건(AX0035~AX0042) 사용 | 추가 채굴 가능, 기존 8건 중복 제외 |
| KOSA AX 사례집 | 공식 발간/전문 열람 경로 확인 | 실증지표 확인, 1건은 기업 1차자료까지 재검증 | **1건 READY**, 2건 HOLD |
| NIA 공공AI 서비스 실증 사례집 | 공식 PDF, 110건 | 54/37/19 범주 구조 확인 | **Supplemental only** |
| NIA 해외 AI 활용 사례 인벤토리 | 공식 XLSX | 해외 공공 AI 후보 탐색용 | **Supplemental discovery** |
| 2026 AI 정부 서비스 사례집 | 공식 PDF, 16건 | 공공부문 상세 사례 | Supplemental; 2건은 기존 PUB 중복 |
| Deloitte 식품·식자재 유통 GenAI | **공식 PDF 16p 직접 파싱** | 실제 기업 사례/성과 다수 확인 | **9건 READY + 1건 HOLD** |
| Deloitte 생성형 AI 활용서 6대 산업 | 공식 PDF, 60개 사례/활용사례 | 기업명·실증여부가 불명확한 항목 혼재 | discovery only, 개별 원출처 검증 후 사용 |
| WEF AI-First Operating System | 공식 PDF/보고서, 50+ 조직, 3 case studies | Indeed/Cognizant/Gamma 확인 | 2건 REVIEW, Gamma 제외 |
| Federal Reserve AI Inventory | 공식 XLSX/CSV/HTML | 구조화된 개별 use case 확인 | **Supplemental only** |

## 2. Main Candidate Pool

파일: `main_candidate_pool.csv`

현재 후보 **16건**을 등록했다.

### 바로 Main 구조화 단계로 넘길 수 있는 후보: 10건

| ID | 조직 | 사례 | 이유 |
|---|---|---|---|
| MC001 | Team Reboot + Lablup | 무역문서 자동화 / HS Code | KOSA + 기업 공식자료 이중 검증 |
| MC002 | Carrefour | Hopla 쇼핑 어시스턴트 | Carrefour 공식자료 확인 |
| MC003 | Carrefour | 구매문서 작성 / 견적 분석 | Carrefour 공식자료 확인 |
| MC004 | Tesco | 컨테이너 공급망 가시성 | 공급사 실제 운영사례 확인 |
| MC005 | Walmart | Customer Support Assistant | Walmart 공식자료 확인 |
| MC006 | Walmart | Sparky 쇼핑 어시스턴트 | Walmart 공식자료 확인 |
| MC007 | Albert Heijn | 매장 직원 AI 어시스턴트 | Microsoft 고객사례 확인 |
| MC008 | Albert Heijn | 수요예측 / Dynamic Markdown | Microsoft 고객사례 확인 |
| MC009 | Albertsons | Afresh DC Forecasts | Afresh 공식 고객사례 확인 |
| MC010 | Sainsbury's | ML 수요예측 / 자동발주 | Sainsbury's + Blue Yonder 검증 |

**READY_TO_PROMOTE의 뜻:**  
후보로서 출처와 실제 적용 여부는 충분히 확인됐다. 다음 작업에서 정식 Main Dataset 스키마로 다시 작성하고, **Solution View를 가린 상태에서 Blind RCA를 다시 수행한 후** AX0043 이후의 Case ID를 부여할 수 있다는 의미다.

### 추가 검증 후 결정할 후보

- MC011 Kroger: Deloitte + 2차자료는 있으나 기업 1차자료 필요
- MC012 KOSA GPU 최적화: 약 80% 비용절감은 확인되지만 공개자료에서 기업/업무 맥락 매핑이 불명확
- MC013 Indeed: WEF의 구체적 case study이나 특정 business workflow보다 AI 운영 플랫폼 성격이 강함
- MC014 Cognizant: 53,000+ 직원 실험은 확인되나 장기 운영성과보다 실험/역량확산 성격이 강함
- MC015 KOSA FTE 73%: 지표는 확인되나 현재 확보 자료만으로 사례 주체와 프로세스가 불명확
- MC016 Kraft Heinz: Deloitte 보고서 내용은 유용하지만 독립 기업 공식자료 재검증 필요

## 3. 기존 42건과 중복 제거

### NIPA

기존 Pilot에 이미 포함된 NIPA 기반 사례:
- AX0035 Lunit
- AX0036 SuperBin
- AX0037 SI Analytics
- AX0038 RexGen
- AX0039 Mathpresso
- AX0040 December & Company / fint
- AX0041 AIZEN Global
- AX0042 Law&Company

따라서 위 8개는 새 후보로 추가하지 않았다.

### 2026 AI 정부 서비스 사례집

- AI 스마트 정수장 → **PUB0001과 중복**
- AI 홍수예보 → **PUB0002와 중복**

따라서 다시 추가하지 않는다.

### Deloitte / KOSA / WEF

현재 READY/REVIEW 후보 중 기존 AX0001~AX0042와 동일한 조직+동일 업무 사례는 발견되지 않았다.

## 4. NIA 110건 PDF / 해외 XLSX 판정

NIA 공식 페이지에서 다음을 확인했다.

- 공공AI 서비스 실증 사례집: **110건**
  - 사회문제 해결 54
  - 대국민 서비스 혁신 37
  - 일하는 방식 개선 19
- 해외 AI 활용 사례 인벤토리: XLSX 제공

이 자료는 데이터 양은 크지만 **공공기관 업무를 중심으로 구성**되어 있다.

우리 논문의 Main Dataset은 기업 AX 사례를 중심으로 하기 때문에 110건을 Main에 대량 혼합하지 않는다.

활용 방식:
1. Supplemental Dataset 확장
2. F01~F09 / S1~S6의 외적 타당성 점검
3. Query 표현 다양화 참고
4. 기업과 유사한 업무가 발견되더라도 Main 편입 전 별도 검증

## 5. Deloitte Food Distribution PDF 분석

공식 16페이지 PDF의 실제 사례 구간을 분석했다.

주요 확인 사례:
- Carrefour: Hopla, 직원 AI assistant, EdgeSense, 구매업무
- Kroger: Sell-Through, 가상 assistant, 상품페이지 자동화
- Tesco: Clubcard 개인화, Roambee 공급망 가시성
- Walmart: Wallaby, Sparky, Associate/Marty/Developer agents, Customer Support
- Albert Heijn / Ahold Delhaize: Gen AI Labs, My AH Assistant, 직원 chatbot, Dynamic Markdown
- Albertsons: 광고 생성, Afresh DC Forecasts, 와인 추천
- ALDI: AI Copywriter, autonomous checkout
- Kraft Heinz: RAG content platform, KraftGPT/KHAI
- Sainsbury's: AI retail media, Blue Yonder demand/replenishment

보고서의 모든 행을 곧바로 Main 사례로 쓰지는 않는다.

선정 기준:
- 실제 조직이 식별되는가
- 해결하려는 업무문제가 있는가
- 구현이 실제 운영/파일럿으로 확인되는가
- Problem / Task / Context를 작성할 근거가 있는가
- 단순 전망/아이디어가 아닌가
- 기존 42건과 동일 사례가 아닌가

이 기준을 적용해 현재 9건을 READY, 나머지는 검증/보류 상태로 분리했다.

## 6. KOSA AX 사례집 분석

KOSA 공식 자료는 사례집이 단순 AI 제품 소개가 아니라:
- 추진 배경/목표
- 적용 업무
- 데이터/인프라/모델
- 운영 경험
- 성과 및 시행착오

를 다루는 실무 사례집임을 확인했다.

공개 자료에서 확인된 대표 성과:
- AI agent: FTE 최대 73% 감소
- 무역·물류 비정형 문서: 업무시간 60%+ 감소
- HS Code 분류: 99.2%
- GPU 동적할당: 인프라 비용 약 80% 감소
- 25개 계열사 AI service 통합 governance

이 중 **Team Reboot + Lablup** 사례는 기업 공식자료에서도 동일 지표가 확인되어 READY로 분류했다.

나머지는 기업명-지표-업무문제의 정확한 매핑이 필요해 HOLD 상태로 유지했다.

## 7. WEF AI-First Operating System 분석

공식 WEF 자료는 50개 이상의 조직을 바탕으로 AI-first 운영모델을 설명하며 Indeed, Gamma, Cognizant의 case study를 포함한다.

판정:
- **Indeed:** 후보 유지. MCP 기반 중앙 agent platform이 구체적이나 business workflow 사례인지 추가 판단 필요.
- **Cognizant:** 후보 유지. 53,000+ 직원/40개국 AI-assisted development 실험은 구체적이나 장기 업무성과 검토 필요.
- **Gamma:** Main에서 제외. 기존 기업의 AX 전환이라기보다 AI-native 기업의 운영모델 사례에 가까움.

## 8. Federal Reserve XLSX/CSV 판정

공식 Inventory가 2025년 XLSX/CSV/HTML로 제공되며 Problem, Expected Benefit, Output, Stage, Data 등 구조화 필드를 제공한다.

예:
- Economic Trend Modeling
- PDF OCR
- Bank Examiner Search Engine
- Risk Rating Model

데이터 구조는 우리 연구와 매우 잘 맞지만 **정부 규제기관의 내부업무**이므로 Main에 섞지 않고 Supplemental 후보로 관리한다.

파일: `supplemental_candidate_pool.csv`

## 9. 다음 작업

다음 순서로 진행한다.

1. READY 10건을 정식 `main_cases_v1.csv` 스키마로 구조화
2. Problem View와 Solution View를 분리해 기록
3. Root Cause는 후보표의 provisional label을 복사하지 않고 **Blind RCA 재수행**
4. Strategy v1(S1~S6) 적용
5. Outcome 수치 재확인
6. QA metadata 생성
7. Case ID AX0043 이후 부여
8. HOLD/REVIEW 후보는 병행 원출처 추가 검증
9. 이후 NIPA 잔여 기업 및 『실전 AX 리포트』 EPUB 사례와 합쳐 100~150건까지 확장


## 10. Promotion 완료

검증 완료된 READY 후보 10건을 `main_cases_v1.csv`에 AX0043~AX0052로 정식 편입했다.

- 기존 Pilot 42건은 버리지 않고 Main Dataset v1의 초기 42건으로 포함
- 신규 편입 10건
- Main Dataset v1 현재 총 **52건**
- 신규 편입 사례는 정식 스키마로 다시 작성
- Root Cause는 후보표의 provisional 값을 그대로 복사하지 않고 Problem View만 기준으로 다시 판정
- 정량 성과가 공개되지 않은 사례는 임의 수치를 만들지 않고 UNKNOWN 처리
- Main용 QA는 `main_qa_metadata_v1.csv`로 별도 관리

현재 HOLD / REVIEW 6건은 Main에 넣지 않았다.
