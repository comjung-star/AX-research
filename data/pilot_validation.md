# Pilot Dataset Validation Report

검증일: **2026-10-14**

대상:
- Core Pilot: `data/pilot_cases.csv` **42건**
- Supplemental Public Set: `data/supplemental_public_cases.csv` **3건**

## 1. 최종 판정

**PASS — Pilot 종료 / Taxonomy v1 Freeze 완료**

쉽게 말하면, 이제는 Pilot 데이터를 더 늘리면서 분류 기준을 계속 바꾸는 단계가 아니라 **확정한 기준으로 Main Dataset을 만드는 단계로 넘어가도 된다는 뜻**이다.

42건의 Core Pilot에서:
- 기존 11개 스키마 컬럼 유지 가능
- Problem / Task / Context 분리 가능
- Blind RCA 적용 가능
- Root Cause 9개로 모든 사례 설명 가능
- Strategy 6개로 모든 사례 설명 가능
- 마지막 8건의 출처·산업 다양화 검증에서도 신규 Strategy가 필요하지 않았음
- F09는 제조 외 산업에서도 반복적으로 확인되어 독립 Root Cause로 유지

---

## 2. 마지막 다양화 검증 8건

| Case | 산업 | 기업/원천 | 검증 목적 | 결과 |
|---|---|---|---|---|
| AX0035 | Healthcare | NIPA + Lunit | 전문판독·대량처리·진단지원 | PASS |
| AX0036 | Environment | NIPA + SuperBin | 재활용 자동식별·회수 | PASS |
| AX0037 | Geospatial / Environment | NIPA + SI Analytics | 대규모 위성영상 분석 | PASS |
| AX0038 | Transportation | NIPA + RexGen | 실시간 교통 분석·최적화 | PASS |
| AX0039 | Education | NIPA + Mathpresso | 교육 접근성·개인화 | PASS |
| AX0040 | Finance | NIPA + December & Company | 자산배분·자동운용 | PASS |
| AX0041 | Finance / Credit | NIPA + AIZEN | 비정형 데이터 신용판단 | PASS |
| AX0042 | Legal | NIPA + Law&Company | 법률검색·문서분석 | PASS |

이 8건은 기존 MakinaRocks 중심 제조 샘플과 겹치지 않도록 헬스케어, 환경, 교통, 교육, 금융, 법률을 중심으로 선정했다.

---

## 3. Root Cause Dictionary v1

| Factor | 의미 | 42건 중 출현 | 최종상태 |
|---|---|---:|---|
| F01_REPETITIVE_MANUAL_WORK | 반복 수작업 | 18 | FROZEN_V1 |
| F02_INFORMATION_KNOWLEDGE_FRAGMENTATION | 정보·지식 분산 | 6 | FROZEN_V1 |
| F03_EXPERT_JUDGMENT_DEPENDENCY | 전문가 판단 의존 | 11 | FROZEN_V1 |
| F04_UNSTRUCTURED_INFORMATION_COMPLEXITY | 비정형 정보 복잡성 | 10 | FROZEN_V1 |
| F05_PROCESS_SYSTEM_FRAGMENTATION | 프로세스·시스템 분절 | 7 | FROZEN_V1 |
| F06_HIGH_VOLUME_SCALABILITY_BOTTLENECK | 대량 처리·확장성 병목 | 14 | FROZEN_V1 |
| F07_DATA_VISIBILITY_INTEGRATION_GAP | 데이터 가시성·통합 부족 | 5 | FROZEN_V1 |
| F08_ERROR_COMPLIANCE_RISK | 오류·컴플라이언스 위험 | 13 | FROZEN_V1 |
| F09_PREDICTION_OPTIMIZATION_COMPLEXITY | 예측·최적화 복잡성 | 14 | FROZEN_V1 |

### F09 최종판정

F09는 제조 Pilot에서 처음 발견됐지만 마지막 검증에서 다음과 같이 제조 외 산업에도 나타났다.

- SI Analytics: 광범위한 위성영상 변화·객체 분석
- RexGen: 동적 교통흐름 분석 및 신호 최적화
- fint: 시장상황·고객조건에 따른 포트폴리오 최적화
- AIZEN: 비정형 모빌리티 데이터 기반 신용위험 판단

따라서 특정 제조 도메인에만 나타나는 현상이 아니라 **다수 변수·제약·불확실성을 다루는 업무 전반의 공통 Root Cause**로 판단해 v1에 포함했다.

---

## 4. Strategy Taxonomy v1

| Strategy | 의미 | 42건 중 출현 | 최종상태 |
|---|---|---:|---|
| S1_KNOWLEDGE_RETRIEVAL_RAG | 지식검색·RAG | 7 | FROZEN_V1 |
| S2_AGENT_CONVERSATIONAL_AI | 에이전트·대화형 AI | 12 | FROZEN_V1 |
| S3_DOCUMENT_INTELLIGENCE | 문서 인텔리전스 | 12 | FROZEN_V1 |
| S4_PREDICTION_DETECTION | 예측·탐지 | 16 | FROZEN_V1 |
| S5_OPTIMIZATION_DECISION_SUPPORT | 최적화·의사결정 지원 | 22 | FROZEN_V1 |
| S6_WORKFLOW_PROCESS_AUTOMATION | 워크플로우·프로세스 자동화 | 21 | FROZEN_V1 |

42건 모두 위 6개 Strategy의 단일 또는 Multi-label 조합으로 표현됐다.

**신규 Strategy 필요 사례: 0건**

---

## 5. 스키마 검증

| 검증항목 | 결과 |
|---|---|
| Business Problem / AX Task / Context 구분 | PASS |
| Problem View / Solution View 분리 | PASS |
| Blind RCA 적용 | PASS |
| Root Cause multi-label | 유지 |
| Strategy multi-label | 유지 |
| AI Technology 분리 | PASS |
| Outcome 정량·정성 혼합 | 유지 |
| Source 재추적 | PASS |
| QA metadata | 유지 |
| 스키마 변경 필요 | 없음 |

---

## 6. Source Balance

Core Pilot 42건의 주요 source group:

| Source group | 건수 |
|---|---:|
| Microsoft | 11 |
| MakinaRocks | 11 |
| NIPA-backed diversification batch | 8 |
| AWS | 4 |
| Google Cloud | 3 |
| IBM | 2 |
| MSIT / Korean Livestock Data | 1 |
| LaonPeople | 1 |
| MICUBE Solution | 1 |

초기 Pilot에서 Microsoft 비중이 55%였으나 현재는 약 26% 수준으로 낮아졌다.

MakinaRocks도 11건으로 비중이 높지만, 마지막 8건을 모두 다른 기업·산업에서 확보해 분류체계가 특정 제조 공급기업의 서술방식에만 맞는지 재검증했다.

---

## 7. 최종 결론

Pilot 단계에서 필요한 검증을 완료했다.

**Pilot 종료 조건**
- 약 40건 확보: 충족 (42건)
- 다양한 산업 포함: 충족
- 다양한 원천 포함: 충족
- 신규 Root Cause 반복 여부 확인: 충족
- 신규 Strategy 필요 여부 확인: 신규 없음
- F09 재검증: 충족
- QA/출처 추적성: 충족

따라서:
- `Root Cause Dictionary v1` Freeze
- `Strategy Taxonomy v1` Freeze
- Pilot 종료
- **Main Dataset v1 100~150건 구축 단계로 전환**

상세 Freeze 기준은 `taxonomy_freeze_v1.md`를 따른다.
