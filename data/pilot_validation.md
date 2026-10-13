# Pilot Dataset Validation Report

검증일: **2026-10-14**

대상: `data/pilot_cases.csv`의 AX 사례 **20건**

## 1. 결론

현재 Pilot 20건은 **스키마 검증과 초기 Factor/Strategy 체계 검증에 사용할 수 있는 수준**으로 판단한다.

다만 아직 Main Dataset용 taxonomy를 최종 고정하기에는 표본이 부족하다.

- 공식 원천 확인: **20/20건**
- Business Problem / Task / Context 분리: **20/20건 사용 가능**
- Blind RCA 수행: **20/20건**
- Strategy taxonomy 적용 가능: **20/20건**
- Root Cause Factor: **8개 후보**
- Strategy taxonomy: **6개 후보**
- 주요 보완점:
  - Microsoft Customer Story 비중이 55%로 높음
  - `S4_PREDICTION_DETECTION` 사례가 2건으로 적음
  - `F03_EXPERT_JUDGMENT_DEPENDENCY` 사례가 1건으로 적음
  - 국내 기업/공공 사례를 추가해 표현·산업 편향을 낮출 필요가 있음

따라서 **현재 체계를 유지하되 10~20건의 균형 보완 사례를 추가한 뒤 taxonomy를 Freeze**하는 것이 적절하다.

---

## 2. 검증 방법

### Source Verification

각 사례의 `source`에 기록된 AWS, Microsoft, Google Cloud, IBM 공식 Customer Story / Case Study를 다시 확인했다.

검증 항목:

1. 해당 사례가 실제 공개 사례인지
2. Business Problem이 원문에서 확인되는지
3. AX Target / Task가 원문에서 추론 가능한 업무 단위인지
4. AI Technology 및 Implementation이 원문에 근거하는지
5. Outcome의 핵심 수치·효과가 원문과 부합하는지

### Blind RCA

Root Cause Factor는 다음 정보만 사용했다.

```text
Business Problem
+ AX Target / Task
+ Business Context
```

다음 정보는 Root Cause 판단에 사용하지 않았다.

```text
Strategy
AI Technology
Implementation
Outcome
```

### Strategy Validation

Strategy는 Solution View를 기준으로 적용했다.

한 사례가 복수 전략을 동시에 사용한 경우 Multi-label을 허용했다.

---

## 3. Source Verification 결과

| Case | Source | 검증 | 주요 확인 내용 |
|---|---|---:|---|
| AX0001 | AWS / i-Tom Solutions | PASS | 일 200~600건 문의, 생성형 AI 지원, 4~5주 POC 및 1주 배포 확인 |
| AX0002 | AWS / Epilot | PASS | 긴 이메일 처리 문제, 월 55,000건 요약, 처리시간 87% 절감 확인 |
| AX0003 | AWS / Genpact | PASS after edit | 수작업 검증 최대 90% 감소, 5일→2.5일, 100% contractual compliance 확인. 원문 근거가 없는 ‘편향’ 표현 삭제 |
| AX0004 | AWS / Orion Health | PASS | 지식 사일로, 50만+ 레코드, 1분 미만 검색, 50시간/일 절감 확인 |
| AX0005 | Microsoft / SK Innovation | PASS | SKI GPT, AutoRAG, 65+ 챗봇, Power Automate 및 Agentic AI 전환 확인 |
| AX0006 | Microsoft / Danone | PASS | HR 및 order-to-cash 자동화, 오류·분쟁 감소 및 cash flow 개선 확인 |
| AX0007 | Microsoft / Navien | PASS | 글로벌 데이터 분산, Azure/Fabric/Power Platform, AI/자동화 성과 확인 |
| AX0008 | Microsoft / EY | PASS | K-1 등 복잡 세무문서, 수작업 최대 90% 감소, 고객 온보딩 수일 단축 확인 |
| AX0009 | Microsoft / Worten | PASS | SharePoint 문서 검색, 검색시간 분→초, 연 11,000시간 이상 절감 확인 |
| AX0010 | Microsoft / Sandvik | PASS | 제품지식 접근 문제, Manufacturing Copilot, 생산성 20~30% 수준 향상 확인 |
| AX0011 | Microsoft / Dow | PASS | 운임·청구 검토 자동화, 불일치 탐지, 첫해 수백만 달러 절감 기대 확인 |
| AX0012 | Microsoft / Shift Technology | PASS | 보험문서 대량 처리, 수주→수일 단축, 사기탐지 의사결정 지원 확인 |
| AX0013 | Microsoft / Relativity | PASS | 법률문서 AI 검토, 최대 300배 속도, 비용 73% 절감 확인 |
| AX0014 | Microsoft / LayerX | PASS | 문서 중심 반복업무 자동화, 고객사 연 570시간 절감 예상 확인 |
| AX0015 | Microsoft / Ontada | PASS | 1.5억 비정형 문서, Document Intelligence/OpenAI, 70% 미활용 정보 활용 및 4배 속도 확인 |
| AX0016 | Google Cloud / Best Buy | PASS | 고객 셀프서비스, call containment 50%+ 향상, 상담원 지식지원 확인 |
| AX0017 | Google Cloud / AT&T | PASS after label refinement | 20% 더 많은 문의 자동 해결, BigQuery routing, Gemini agent 확인. Strategy는 S2 중심으로 정제 |
| AX0018 | Google Cloud / NOS | PASS | 고객 상호작용 자동화 70%, 해결시간 25% 단축, 데이터/AI 통합 확인 |
| AX0019 | IBM / IBM Finance | PASS | 수동 분개, AI+RPA 자동화, cycle time 90%+ 단축 및 연 USD 600K 절감 예상 확인 |
| AX0020 | IBM / Claims Connection Group | PASS | 수동·분절 청구 프로세스, 최대 70% 빠른 해결, 수작업 30~50% 감소 확인 |

### 수정 반영

- **AX0003**: 공식 원문에서 직접 확인되지 않은 `편향` 표현 제거
- **AX0017**: Customer Experience Agent가 핵심이므로 과도한 `S5_OPTIMIZATION_DECISION_SUPPORT` 라벨 제거
- **S4**: Prediction뿐 아니라 anomaly/risk detection을 포함할 수 있도록 `S4_PREDICTION_DETECTION`으로 Pilot taxonomy 명칭 정제

---

## 4. Blind RCA 결과

### Root Cause Factor Dictionary

| Factor | 의미 | Pilot 건수 | 판단 |
|---|---|---:|---|
| F01_REPETITIVE_MANUAL_WORK | 반복 수작업 | 11 | 유지 |
| F02_INFORMATION_KNOWLEDGE_FRAGMENTATION | 정보·지식 분산 | 4 | 유지 |
| F03_EXPERT_JUDGMENT_DEPENDENCY | 전문가 판단 의존 | 1 | 후보 유지, 추가 사례 필요 |
| F04_UNSTRUCTURED_INFORMATION_COMPLEXITY | 비정형 정보 복잡성 | 8 | 유지 |
| F05_PROCESS_SYSTEM_FRAGMENTATION | 프로세스·시스템 분절 | 6 | 유지 |
| F06_HIGH_VOLUME_SCALABILITY_BOTTLENECK | 대량 처리·확장성 병목 | 7 | 유지 |
| F07_DATA_VISIBILITY_INTEGRATION_GAP | 데이터 가시성·통합 부족 | 3 | 후보 유지, 추가 사례 필요 |
| F08_ERROR_COMPLIANCE_RISK | 오류·컴플라이언스 위험 | 7 | 유지 |

### 해석

현재 20건에서는 **반복 수작업(F01)**, **비정형 정보 복잡성(F04)**, **대량 처리 병목(F06)**, **오류/컴플라이언스 위험(F08)**이 자주 관찰되었다.

이는 현재 Pilot이 고객지원·문서처리·업무자동화 사례를 많이 포함하기 때문일 수 있으므로 최종 분포로 해석하면 안 된다.

특히 F03은 1건뿐이지만 연구에서 중요한 유형이므로 삭제하지 않고 다음 Pilot 확장 단계에서 전문가 판단 의존 사례를 의도적으로 추가한다.

---

## 5. Strategy Taxonomy 검증

| Strategy | 의미 | Pilot 건수 | 판단 |
|---|---|---:|---|
| S1_KNOWLEDGE_RETRIEVAL_RAG | 지식검색·RAG | 5 | 유지 |
| S2_AGENT_CONVERSATIONAL_AI | 에이전트·대화형 AI | 9 | 유지 |
| S3_DOCUMENT_INTELLIGENCE | 문서 인텔리전스 | 8 | 유지 |
| S4_PREDICTION_DETECTION | 예측·탐지 | 2 | 유지, 보완 사례 필요 |
| S5_OPTIMIZATION_DECISION_SUPPORT | 최적화·의사결정 지원 | 7 | 유지 |
| S6_WORKFLOW_PROCESS_AUTOMATION | 워크플로우·프로세스 자동화 | 12 | 유지 |

### Taxonomy Coverage

20건 모두 현재 6개 Strategy로 표현 가능했다.

따라서 **새 Strategy 범주를 추가할 필요성은 현재 Pilot에서 발견되지 않았다.**

다만 S6가 12건으로 높고 S4가 2건에 불과해 최종 데이터셋에는 다음 유형을 보완해야 한다.

- 수요·용량·고장·리스크 예측
- 이상탐지
- 예측 유지보수
- 자원 최적화
- 스케줄링
- 가격/재고/공급망 최적화

---

## 6. Dataset Balance 점검

### Source Vendor

| Source | 건수 | 비율 |
|---|---:|---:|
| AWS | 4 | 20% |
| Microsoft | 11 | 55% |
| Google Cloud | 3 | 15% |
| IBM | 2 | 10% |

Microsoft 비중이 지나치게 높으므로 Main Dataset에서는 특정 벤더의 사례 서술방식에 모델이 편향되지 않도록 균형화가 필요하다.

### 현재 Pilot의 역할

현재 데이터는 **모델 학습용 최종 데이터셋이 아니라 스키마·라벨링 체계를 검증하는 Development/Pilot Set**으로 사용한다.

따라서 현재 벤더 편향 자체가 Pilot 실패를 의미하지는 않는다.

---

## 7. 스키마 검증

| 항목 | 결과 | 판단 |
|---|---|---|
| Business Problem과 Solution 분리 | 가능 | PASS |
| Business Problem / Task 구분 | 대부분 명확 | PASS |
| Context 작성 가능성 | 모든 사례에서 확보 가능 | PASS |
| Root Cause Multi-label 필요성 | 다수 사례에서 확인 | PASS |
| Strategy Multi-label 필요성 | 다수 사례에서 확인 | PASS |
| AI Technology 분리 | 가능 | PASS |
| Outcome 정량/정성 혼합 | 필요 | PASS |
| Source 재검증 가능성 | 20/20 공식 URL 확보 | PASS |
| Missing value 처리 | UNKNOWN 규칙 사용 가능 | PASS |

현재 11개 컬럼 스키마는 Pilot 단계에서 **구조 변경 없이 유지 가능**하다.

단, Main Dataset 구축 시 원문 추적성을 강화하기 위해 별도 QA 파일에 다음 정보를 저장하는 것을 권장한다.

- source_title
- source_vendor
- source_checked_at
- extraction_status
- reviewer_note

이 필드들은 모델 입력용 `pilot_cases.csv`에 반드시 포함할 필요는 없으며 QA 메타데이터로 분리한다.

---

## 8. Pilot 단계 최종 판정

**판정: CONDITIONAL PASS**

현재 스키마와 Factor/Strategy 체계는 다음 단계로 진행하기에 충분하다.

그러나 **아직 taxonomy를 완전히 Freeze하지 않는다.**

다음 10~20건은 무작위로 추가하기보다 현재 부족한 영역을 보완한다.

### 우선 확보 대상

1. 국내 NIPA/NIA/KOSA 사례
2. Prediction / Detection 중심 사례
3. Expert Judgment Dependency 사례
4. Manufacturing / Logistics / Finance의 최적화 사례
5. 특정 클라우드 벤더에 종속되지 않은 기업 자체 AX 사례

### Freeze 기준

Pilot을 약 **30~40건**으로 확장한 후:

- 새로운 Root Cause가 반복적으로 등장하는지
- 기존 Factor 간 경계가 모호한지
- Strategy 미분류 사례가 존재하는지
- 희소 범주의 최소 사례 수가 확보되는지

를 재검증하고 **Root Cause Dictionary v1 / Strategy Taxonomy v1**을 고정한다.

그 이후 Main Dataset 100~150건에 동일 기준을 적용한다.
