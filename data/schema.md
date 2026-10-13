# AX Case Dataset Schema

이 문서는 AX 사례 데이터셋의 컬럼 정의와 작성 기준을 정리한 문서입니다.

연구계획서와 교수 제안 아키텍처를 기준으로 하며, 특히 **Problem View**와 **Solution View**를 분리하여 관리합니다.

---

## 1. 기본 원칙

1. 원문에 존재하지 않는 사실은 임의로 생성하지 않습니다.
2. 값이 확인되지 않으면 빈칸 대신 `UNKNOWN`을 사용합니다.
3. 사례의 검색 입력에 사용되는 정보와 해결방안 정보를 분리합니다.
4. **Blind RCA**를 위해 Root Cause 도출 시 Solution View 정보를 사용하지 않습니다.
5. Strategy는 하나의 사례에 여러 개가 존재할 수 있으므로 **multi-label**을 허용합니다.
6. 출처를 반드시 남겨 이후 재검증이 가능하도록 합니다.
7. 동일 사례를 여러 자료에서 발견한 경우 중복 여부를 확인하고 하나의 Case ID로 관리합니다.

---

## 2. View 구분

### Problem View

검색과 Root Cause 분석의 핵심 입력입니다.

- Business Problem
- AX Target / Task
- Business Context / Condition

### Solution View

실제 사례가 어떤 방식으로 문제를 해결했는지 나타냅니다.

- Strategy
- AI Technology
- Implementation
- Outcome

> **중요:** Blind RCA 단계에서는 Solution View를 보지 않고 Problem View만 사용합니다.

---

## 3. 컬럼 정의

| 컬럼명 | 필수 | View | 의미 | 작성 기준 |
|---|---:|---|---|---|
| `case_id` | O | Metadata | 사례 고유 식별자 | `AX0001`, `AX0002` 형태로 부여 |
| `industry` | O | Metadata | 사례가 속한 산업/업종 | 가능한 한 상위 산업 분류로 통일 |
| `business_problem` | O | Problem | 해결하려는 업무문제 | 해결방안이 아니라 현재의 문제·불편·비효율 중심으로 작성 |
| `ax_target_task` | O | Problem | AX 적용 대상 업무/Task | 실제 개선 또는 자동화 대상이 되는 업무 단위 |
| `business_context` | O | Problem | 업무환경 및 제약조건 | 조직, 시스템, 데이터, 업무방식 등 문제 발생 맥락 |
| `root_cause_factor` | △ | Derived | 공통 Root Cause Factor | Blind RCA 후 표준 Factor ID 또는 label로 부여 |
| `strategy` | O | Solution | 사례에서 적용된 AX 전략 | 하나 이상 가능, 표준 Strategy taxonomy 사용 |
| `ai_technology` | △ | Solution | 실제 사용된 AI 기술 | 원문에 명시된 경우에만 작성 |
| `implementation` | △ | Solution | 실제 구현 방식 | 시스템/프로세스/서비스에 어떻게 적용했는지 기술 |
| `outcome` | △ | Solution | 적용 결과 | 정량/정성 성과를 원문 근거로 기록 |
| `source` | O | Metadata | 사례 출처 | 보고서명, 기업 사례명, URL 등 검증 가능한 형태 |

- `O`: 기본적으로 필수
- `△`: 원문에 없으면 `UNKNOWN` 허용

---

## 4. 컬럼별 작성 기준

### 4.1 case_id

사례의 고유 식별자입니다.

형식:

```text
AX0001
AX0002
AX0003
...
```

한 사례가 여러 Perspective로 검색되더라도 Case ID는 하나만 유지합니다.

---

### 4.2 industry

사례가 속한 산업을 기록합니다.

예시:

```text
Manufacturing
Finance
Retail
Healthcare
Public
IT/Service
Logistics
Telecom
```

초기 Pilot 단계에서는 지나치게 세분화하지 않고, 사례 수가 충분히 확보된 후 taxonomy를 조정합니다.

---

### 4.3 business_problem

기업이 실제로 해결하고자 했던 **업무문제**를 기록합니다.

좋은 예:

```text
DB 자원 신청 시 담당자가 신청내용을 수작업으로 검토하고
적정 자원량을 판단해야 하므로 처리시간과 전문가 의존도가 높다.
```

피해야 할 예:

```text
AI를 활용하여 DB 자원 신청을 자동화한다.
```

두 번째 문장은 이미 해결방안을 포함하고 있으므로 Business Problem으로 사용하지 않습니다.

작성 원칙:

- 현재의 문제 상태를 기술
- 비효율, 지연, 반복작업, 오류, 전문가 의존성 등을 명확하게 표현
- 해결책이나 특정 AI 기술명은 가급적 포함하지 않음

---

### 4.4 ax_target_task

AX가 적용되는 구체적인 **업무 단위**를 기록합니다.

예시:

```text
DB 자원 신청내용 검토
DB 자원량 산정
DB 자원 할당 및 Provisioning
```

Business Problem이 "왜 개선이 필요한가"라면, AX Target / Task는 "어떤 업무를 개선하는가"에 해당합니다.

---

### 4.5 business_context

업무문제가 발생하는 환경과 조건을 기록합니다.

포함 가능한 내용:

- 담당 조직/역할
- 기존 시스템
- 데이터 환경
- 수작업 여부
- 전문가 판단 필요 여부
- 업무 빈도
- 시스템 연계 상태
- 규정/보안/운영 제약

예시:

```text
사내 DB 자원 신청 시스템을 사용하며,
신청내용 검토와 자원량 산정을 운영 담당자가 수작업으로 수행한다.
자원 할당은 별도 Provisioning 절차와 연계되어 있다.
```

---

### 4.6 root_cause_factor

Problem View를 기반으로 Blind RCA를 수행한 후 부여하는 표준 Root Cause Factor입니다.

예시:

```text
F01_REPETITIVE_MANUAL_WORK
F02_EXPERT_JUDGMENT_DEPENDENCY
F03_INSUFFICIENT_PREDICTION
F04_PROCESS_SYSTEM_DISCONNECTION
```

초기 20~30건 Pilot 사례에서 반복되는 원인을 수집하고, Factor Dictionary를 만든 뒤 Main Dataset에 적용합니다.

주의사항:

- 원문에 Root Cause가 직접 적혀 있더라도 표준 Factor 체계로 정규화할 수 있음
- Strategy / AI Technology / Implementation을 보고 역으로 Root Cause를 정하지 않음
- 하나의 사례에 여러 Factor가 존재할 수 있음

권장 저장 형태:

```json
["F01_REPETITIVE_MANUAL_WORK", "F02_EXPERT_JUDGMENT_DEPENDENCY"]
```

CSV에서는 다음과 같이 저장할 수 있습니다.

```text
F01_REPETITIVE_MANUAL_WORK|F02_EXPERT_JUDGMENT_DEPENDENCY
```

---

### 4.7 strategy

사례에서 실제로 적용된 AX 전략을 표준 taxonomy로 기록합니다.

초기 taxonomy 후보:

```text
S1_KNOWLEDGE_RETRIEVAL_RAG
S2_AGENT_CONVERSATIONAL_AI
S3_DOCUMENT_INTELLIGENCE
S4_PREDICTION
S5_OPTIMIZATION_DECISION_SUPPORT
S6_WORKFLOW_PROCESS_AUTOMATION
```

> 이 taxonomy는 현재 연구를 위한 **초기 실험안**이며, Pilot 사례 분석 후 수정될 수 있습니다.

하나의 사례에 여러 Strategy가 함께 적용될 수 있습니다.

예:

```text
S4_PREDICTION|S5_OPTIMIZATION_DECISION_SUPPORT
```

---

### 4.8 ai_technology

실제 사례에서 사용된 AI 기술을 기록합니다.

예시:

```text
LLM
RAG
Forecasting Model
Computer Vision
OCR
Recommendation Model
Optimization Model
```

원문에 기술이 명확하지 않은 경우 추정하지 않고 `UNKNOWN`으로 기록합니다.

---

### 4.9 implementation

AX가 실제 시스템이나 업무 프로세스에 어떻게 적용되었는지 기록합니다.

예시:

```text
과거 자원 사용량과 신청 데이터를 기반으로 자원량을 예측하고,
승인 후 자동 Provisioning API와 연계하여 자원을 할당한다.
```

가능하면 다음 내용을 포함합니다.

- 어떤 데이터가 입력되는지
- 어떤 시스템/모델이 처리하는지
- 기존 업무와 어떻게 연결되는지
- 사람이 최종 승인하는지 여부

---

### 4.10 outcome

적용 이후의 결과를 기록합니다.

정량 예시:

```text
처리시간 35% 감소
예측오차 18% 감소
수작업 건수 50% 감소
```

정성 예시:

```text
담당자 검토부담 감소
전문가 의존도 완화
업무 표준화
```

원문에 성과가 없으면 `UNKNOWN`을 사용합니다.

---

### 4.11 source

사례의 출처를 기록합니다.

최소 포함 권장정보:

```text
기관/기업명
자료명
발행연도
URL 또는 문서 위치
페이지/섹션(가능한 경우)
```

예시:

```text
NIA, AI 도입 우수사례집, 2026, p.34
```

또는

```text
Company A Customer Story, 2026, https://...
```

---

## 5. Pilot 데이터 예시

아래는 **연구 구조를 설명하기 위한 가상 예시**이며 실제 사례 데이터가 아닙니다.

| 컬럼 | 예시 값 |
|---|---|
| case_id | AX0001 |
| industry | IT/Service |
| business_problem | DB 자원 신청 시 담당자가 신청내용을 수작업으로 검토하고 적정 자원량을 판단해야 해 처리시간과 전문가 의존도가 높다. |
| ax_target_task | DB 자원 신청 검토 / 자원량 산정 / 자원 할당 |
| business_context | 사내 자원관리 시스템을 사용하며 검토·산정·Provisioning 절차가 분리되어 있다. |
| root_cause_factor | F01_REPETITIVE_MANUAL_WORK\|F02_EXPERT_JUDGMENT_DEPENDENCY\|F04_PROCESS_SYSTEM_DISCONNECTION |
| strategy | S4_PREDICTION\|S5_OPTIMIZATION_DECISION_SUPPORT\|S6_WORKFLOW_PROCESS_AUTOMATION |
| ai_technology | Forecasting Model / Optimization Model |
| implementation | 과거 사용량 기반 자원량 예측 후 승인결과를 Provisioning API와 연계 |
| outcome | UNKNOWN |
| source | ILLUSTRATIVE_EXAMPLE |

---

## 6. 추천 저장 포맷

초기 데이터는 CSV 또는 JSONL 중 하나로 관리합니다.

### CSV

사람이 직접 확인하고 수정하기 쉽기 때문에 Pilot 단계에 적합합니다.

예정 파일:

```text
data/
├─ schema.md
├─ pilot_cases.csv
└─ README.md
```

### JSONL

multi-label, nested evidence, Perspective 등의 구조가 복잡해지는 단계에서 유리합니다.

예:

```json
{
  "case_id": "AX0001",
  "industry": "IT/Service",
  "business_problem": "...",
  "ax_target_task": ["...", "..."],
  "business_context": "...",
  "root_cause_factor": ["F01", "F02"],
  "strategy": ["S4", "S5"],
  "ai_technology": ["Forecasting Model"],
  "implementation": "...",
  "outcome": "UNKNOWN",
  "source": "..."
}
```

초기 Pilot 20~30건은 CSV로 시작하고, Evidence 구조가 복잡해지는 시점에 JSONL을 병행하는 것을 기본 방향으로 합니다.

---

## 7. 데이터 작성 순서

사례 한 건을 정리할 때는 다음 순서를 권장합니다.

```text
1. Source 확인
2. Business Problem 작성
3. AX Target / Task 작성
4. Business Context 작성
5. Solution View 분리
   - Strategy
   - AI Technology
   - Implementation
   - Outcome
6. Blind RCA 수행
7. Root Cause Factor 부여
8. 품질검토
```

특히 2~4번까지 작성할 때는 Solution View 내용을 섞지 않는 것이 중요합니다.

---

## 8. Pilot 단계에서 확인할 사항

20~30건 Pilot 데이터셋을 만들면서 다음을 확인합니다.

- Business Problem과 AX Target / Task가 실제로 구분되는가?
- Context가 검색 품질에 도움이 될 정도로 일관되게 작성되는가?
- 동일한 Root Cause가 반복적으로 나타나는가?
- Root Cause Factor 수가 지나치게 많아지지 않는가?
- Strategy taxonomy가 실제 사례들을 충분히 표현하는가?
- 한 사례에 복수 Strategy가 필요한 경우가 얼마나 많은가?
- 출처만으로 각 필드의 내용을 재검증할 수 있는가?

Pilot 검증이 끝난 뒤에 Root Cause Factor Dictionary와 Strategy taxonomy를 고정하고 Main Dataset으로 확장합니다.
