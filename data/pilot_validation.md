# Pilot Dataset Validation Report

검증일: **2026-10-14**

대상:
- Core Pilot: `data/pilot_cases.csv` **34건**
- Supplemental Public Set: `data/supplemental_public_cases.csv` **3건**

## 1. 최종 요약

기존 20건에 국내 공개 원천 중심의 제조·예측·최적화 사례 **14건**을 추가하여 Core Pilot을 **34건**으로 확장했다.

추가 사례는 기존 Pilot에서 부족했던 두 영역을 의도적으로 보완했다.

- `S4_PREDICTION_DETECTION`: 2건 → **11건**
- `F03_EXPERT_JUDGMENT_DEPENDENCY`: 1건 → **7건**

또한 반복적으로 등장한 새로운 원인 패턴을 별도 Factor로 분리했다.

- `F09_PREDICTION_OPTIMIZATION_COMPLEXITY`
- 의미: 다수 변수·동적 조건·제약·불확실성으로 인해 수동 또는 단순 룰 방식만으로 미래상태 예측이나 최적 의사결정이 어려운 상태
- Core Pilot 출현: **10건**

현재 판정은 **CONDITIONAL PASS**이다.

Strategy 6개는 34건 모두를 표현할 수 있어 안정화 단계에 들어갔지만, Root Cause에는 새 F09가 추가되었으므로 소수의 다양한 추가 사례로 경계를 한 번 더 검증한 후 v1을 Freeze하는 것이 안전하다.

---

## 2. 이번에 추가한 Core 사례 14건

| Case | 공개 원천 | 핵심 업무문제 | 주 Strategy | 검증 |
|---|---|---|---|---|
| AX0021 | MakinaRocks / Hyundai Motor | 산업용 로봇 고장·다운타임 | Prediction / Detection | PASS |
| AX0022 | MakinaRocks | 배터리 공정 수동개입·시스템 분절 | Agent + Decision Support + Automation | PASS |
| AX0023 | MakinaRocks | 도면 견적의 수작업·숙련자 의존 | Document + Decision Support + Automation | PASS |
| AX0024 | MakinaRocks | 비정형 주문서 수동 표준화 | Agent + Document + Automation | PASS |
| AX0025 | MakinaRocks | 소재 레시피·물성 예측 복잡성 | Prediction + Decision Support | PASS |
| AX0026 | MakinaRocks | 발효공정 숙련자 수동운전 | Prediction + Optimization + Automation | PASS |
| AX0027 | MakinaRocks | 환기팬 고장 사전탐지 | Prediction / Detection | PASS |
| AX0028 | MakinaRocks | 다품종 생산 스케줄링 복잡성 | Optimization / Decision Support | PASS |
| AX0029 | MakinaRocks | 다중로봇 수동 프로그래밍 | Optimization + Automation | PASS |
| AX0030 | MakinaRocks | EV HVAC 제어모델 한계 | Prediction + Optimization | PASS |
| AX0031 | MakinaRocks | 태양광 발전량 예측 불확실성 | Prediction / Detection | PASS |
| AX0032 | MSIT / 한국축산데이터 | 대량 가축관리·질병 선제대응 | Prediction + Decision Support | PASS |
| AX0033 | LaonPeople | 반복 육안검사의 피로·주관성 | Prediction / Detection + Automation | PASS |
| AX0034 | MICUBE Solution | SMD 불량·설비 이상 사전탐지 | Prediction + Decision Support | PASS |

### 대표 정량검증

- 산업용 로봇 예지보전: 고장 최대 5일 전, 90% 이상 정확도
- 도면 견적: 검토시간 67% 단축, 견적 리드타임 50% 단축
- 발효공정: 제어 편차 4.3% → 0.2%
- 생산 스케줄링: 계획 준수율 19% → 85%
- OLP 자동화: 수주~수개월 수준 작업을 약 3일로 단축
- EV HVAC: 에너지 사용 10% 절감, 주행거리 5% 증가
- 태양광 예측: 787개 발전소, 3,000개 이상 모델, 94% 이상 정확도
- 한국축산데이터: 생산성 30% 향상, 폐사율 40% 감소
- MICUBE SMD 사례: 공정 불량률 57% 감소

---

## 3. Root Cause Factor 재검증

Blind RCA는 이전과 동일하게 **Problem View만 사용**했다.

```text
Business Problem
+ AX Target / Task
+ Business Context
```

Solution View의 Strategy, AI Technology, Implementation, Outcome은 Root Cause를 결정할 때 사용하지 않았다.

| Factor | 의미 | 34건 중 출현 | 상태 |
|---|---|---:|---|
| F01_REPETITIVE_MANUAL_WORK | 반복 수작업 | 17 | RETAIN |
| F02_INFORMATION_KNOWLEDGE_FRAGMENTATION | 정보·지식 분산 | 5 | RETAIN |
| F03_EXPERT_JUDGMENT_DEPENDENCY | 전문가 판단 의존 | 7 | RETAIN |
| F04_UNSTRUCTURED_INFORMATION_COMPLEXITY | 비정형 정보 복잡성 | 9 | RETAIN |
| F05_PROCESS_SYSTEM_FRAGMENTATION | 프로세스·시스템 분절 | 7 | RETAIN |
| F06_HIGH_VOLUME_SCALABILITY_BOTTLENECK | 대량 처리·확장성 병목 | 9 | RETAIN |
| F07_DATA_VISIBILITY_INTEGRATION_GAP | 데이터 가시성·통합 부족 | 4 | RETAIN |
| F08_ERROR_COMPLIANCE_RISK | 오류·컴플라이언스 위험 | 10 | RETAIN |
| F09_PREDICTION_OPTIMIZATION_COMPLEXITY | 예측·최적화 복잡성 | 10 | **NEW — 재검증 필요** |

### F09를 새로 분리한 이유

기존 20건은 문서·고객지원·업무자동화 비중이 높아 예측·최적화 문제의 공통 원인이 충분히 드러나지 않았다.

제조·에너지 사례를 추가하자 다음 문제가 반복됐다.

- 기상·공정·설비 등 다변량 환경의 미래상태 예측
- 수많은 조합·제약조건을 동시에 고려해야 하는 최적화
- 단순 룰이나 사람 경험만으로 모든 변수를 처리하기 어려움
- 동적 환경에서 계획·제어를 지속 수정해야 함

이를 기존 F03(전문가 의존)만으로 묶으면 **왜 전문가가 필요한지**에 해당하는 기술적·업무적 원인을 잃게 되므로 F09로 분리했다.

---

## 4. Strategy Taxonomy 재검증

| Strategy | 의미 | 34건 중 출현 | 상태 |
|---|---|---:|---|
| S1_KNOWLEDGE_RETRIEVAL_RAG | 지식검색·RAG | 5 | RETAIN |
| S2_AGENT_CONVERSATIONAL_AI | 에이전트·대화형 AI | 11 | RETAIN |
| S3_DOCUMENT_INTELLIGENCE | 문서 인텔리전스 | 10 | RETAIN |
| S4_PREDICTION_DETECTION | 예측·탐지 | 11 | RETAIN |
| S5_OPTIMIZATION_DECISION_SUPPORT | 최적화·의사결정 지원 | 16 | RETAIN |
| S6_WORKFLOW_PROCESS_AUTOMATION | 워크플로우·프로세스 자동화 | 18 | RETAIN |

### 판단

- 34건 모두 6개 Strategy 범주로 표현 가능
- 신규 Strategy를 추가해야 하는 미분류 사례는 없음
- 이전에 부족했던 S4가 11건으로 증가
- Strategy taxonomy는 **v1 Freeze 후보 수준**으로 판단

다만 Main Dataset으로 확대하기 전, 서로 다른 출처의 사례를 6~10건 정도 추가해 6개 범주가 유지되는지 마지막으로 확인한다.

---

## 5. Source Balance

### Core Pilot 34건

| Source | 건수 | 비율 |
|---|---:|---:|
| Microsoft | 11 | 32.4% |
| MakinaRocks | 11 | 32.4% |
| AWS | 4 | 11.8% |
| Google Cloud | 3 | 8.8% |
| IBM | 2 | 5.9% |
| MSIT / 한국축산데이터 | 1 | 2.9% |
| LaonPeople | 1 | 2.9% |
| MICUBE Solution | 1 | 2.9% |

기존 Microsoft 55% 편중은 크게 완화됐지만, 이번 확장 과정에서 MakinaRocks가 11건으로 증가했다.

이는 **Pilot의 부족한 Prediction/Optimization 유형을 보완하기 위한 의도적 표집**이므로 현재 단계에서는 허용한다. 단, Main Dataset에서는 특정 공급기업의 사례 서술방식에 편향되지 않도록 NIPA 사례집과 다른 기업의 공식 사례를 더 확보해야 한다.

---

## 6. Supplemental Public Set

기업 AX와 공공부문 AI는 업무환경이 다르기 때문에 Core Pilot에 섞지 않았다.

별도 `supplemental_public_cases.csv`에 3건을 저장했다.

| ID | 사례 | 활용 목적 |
|---|---|---|
| PUB0001 | K-water AI 정수장 | 복합 공정 최적화·자율운영 taxonomy stress-test |
| PUB0002 | 환경부 AI 홍수예보 | 예측 + 전문가 검증(Human-in-the-loop) stress-test |
| PUB0003 | 특허청 AI 특허심사 지원 | 지식검색·문서·전문가 판단지원 stress-test |

Supplemental Set은 현재 Core Dataset의 학습분포에는 포함하지 않고 **taxonomy 외적 타당성 점검**에 활용한다.

---

## 7. 스키마 검증 결과

| 항목 | 결과 |
|---|---|
| Problem / Task / Context 분리 | PASS |
| Problem / Solution View 분리 | PASS |
| Root Cause multi-label | 필요성 재확인 |
| Strategy multi-label | 필요성 재확인 |
| Source 추적성 | PASS |
| Prediction/Optimization 사례 표현 | F09 추가 후 PASS |
| 기존 11개 데이터 컬럼 | 유지 가능 |
| Strategy 미분류 사례 | 0 |
| Core 사례 수 | 34 |
| Supplemental 사례 수 | 3 |

---

## 8. 다음 단계 판정

현재 Core Pilot 34건은 **Pilot 목적에 충분히 근접**했다.

다음 단계에서는 데이터를 무작정 늘리기보다 **출처 다양화용 6~10건**을 추가하는 것이 가장 효율적이다.

우선순위:

1. NIPA 국내 대표 AI 기업·서비스 사례집에서 비-MakinaRocks 기업 사례 확보
2. 금융·물류·교육·법률·환경 등 제조 외 산업 보완
3. F02·F07처럼 상대적으로 적은 Root Cause 보완
4. 동일 기준으로 Blind RCA 및 Strategy labeling
5. 약 40건 전후에서 **Root Cause Dictionary v1 / Strategy Taxonomy v1 Freeze**

그 이후 Main Dataset 100~150건 구축으로 이동한다.

**현재 결론:** 데이터 구조 자체는 안정적이며, Strategy 체계는 거의 고정 가능하다. Root Cause는 새 F09가 반복적으로 확인되어 한 번의 출처 다양화 검증 후 고정하는 것이 적절하다.
