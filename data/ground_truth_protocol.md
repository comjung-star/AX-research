# Retrieval Ground Truth Protocol

## 1. 목적

Main Dataset v1(`AX0001~AX0100`)을 대상으로 검색 모델의 성능을 평가하기 위한 독립 Ground Truth를 구축한다.

이 Ground Truth는 다음 비교에 공통으로 사용한다.

1. Single-query BM25
2. Single-query Dense Retrieval
3. GPT-only
4. Multi-Perspective Retrieval
5. 이후 Multi-view / Hybrid Retrieval / Query-Case Interaction 확장 모델

Ground Truth는 **모델의 검색 결과를 본 뒤 정답을 맞추는 방식으로 만들지 않는다.**

---

## 2. 고정 데이터셋

- Dataset: `data/main_cases_v1.csv`
- Version: Main Dataset v1
- Case 범위: `AX0001~AX0100`
- 상태: FROZEN
- Root Cause taxonomy: v1 9종 FROZEN
- Strategy taxonomy: v1 6종 FROZEN

Ground Truth 구축 및 baseline 실험 중에는 Main Dataset v1의 사례 구성과 구조화 필드를 임의로 변경하지 않는다.

---

## 3. Query 작성 원칙

평가 Query는 실제 기업 사용자가 입력할 법한 **Business Problem 중심 문장**으로 작성한다.

### 포함 가능
- 현재 업무문제
- 업무환경/조건
- 개선 목표(선택)

### 포함 금지
- 특정 정답 Case ID
- 기업명/제품명 등 정답 사례를 직접 식별하는 단서
- 정답 Strategy label
- "RAG를 써야 한다", "Agent를 도입한다"와 같은 해결전략 선제 제시

가능하면 Main Dataset의 `business_problem` 문장을 그대로 복사하지 않고, 여러 사례에서 공통적으로 나타나는 실제 업무문제 패턴을 자연스럽게 재서술한다.

---

## 4. Gold Perspective

하나의 Business Problem Query에 복수의 타당한 문제관점이 존재할 수 있다.

각 Query는 다음처럼 Perspective를 별도 Branch로 정의한다.

```text
Q001
├─ P1: 대량 문의 처리 병목
├─ P2: 반복 응대 업무 부담
└─ P3: 지원 지식 접근 및 답변 일관성
```

Perspective는 **해결책이 아니라 문제를 바라보는 관점**이어야 한다.

예:
- O: 반복 수작업 부담
- O: 정보·지식 분산
- O: 대량 처리 병목
- X: RAG 도입
- X: 챗봇 구축

초기 Query 파일의 Perspective는 `DRAFT_UNADJUDICATED` 상태로 시작하고, 관련도 라벨링을 거친 뒤 Gold로 확정한다.

### Runtime Perspective와 Gold Perspective 구분

- **Gold Perspective**: 평가자가 사전에 확정한 평가용 정답 관점
- **Generated Perspective**: 실제 사용 시 LLM이 사용자 Query를 보고 동적으로 생성하는 관점

Gold Perspective는 모델 입력에 제공하지 않는다. 실제 모델은 사용자 Query만 보고 `P1 ... Pk`를 동적으로 생성하며, 관점 개수도 고정하지 않는다.

Ground Truth의 Gold Perspective는 나중에 Generated Perspective 및 관점별 검색결과가 적절했는지 평가하기 위한 기준이다.

---

## 5. Perspective × Case 관련도 0~4

관련도 판정은 원칙적으로 Case의 **Problem View**만 사용한다.

사용 필드:
- `business_problem`
- `ax_target_task`
- `business_context`

관련도 판정 단계에서는 다음 Solution View를 정답 단서로 사용하지 않는다.
- `strategy`
- `ai_technology`
- `implementation`
- `outcome`

### 등급 정의

| 점수 | 의미 | 판정 기준 |
|---:|---|---|
| 4 | 직접 관련 | Perspective의 핵심 문제·업무·맥락이 직접적으로 일치하거나 매우 강하게 대응 |
| 3 | 강한 관련 | 핵심 문제 또는 Task가 강하게 일치하며 Context 차이가 있어도 유사 AX 사례로 활용 가능 |
| 2 | 부분 관련 | 일부 문제요소나 Task는 관련되지만 핵심 Perspective를 충분히 대표하지 못함 |
| 1 | 약한 관련 | 주변적·간접적으로만 관련 |
| 0 | 무관 | 해당 Perspective와 실질적 관련 없음 |

### 초기 Gold threshold

Ground Truth Pilot에서는 **3점 이상을 Gold Relevant 후보**로 사용하는 것을 실험안으로 둔다.

이 threshold는 교수 확정값이 아니라 **Ground Truth Pilot의 실험 규칙**이며, 실제 라벨 분포와 판정 안정성을 확인한 뒤 v1 확정 전에 검토한다.

---

## 6. Gold Relevant Cases

Query별 Gold Relevant Cases는 Perspective별 관련도 라벨을 기반으로 결정한다.

원칙:
- 하나 이상의 Gold Perspective에서 관련도 3 이상인 Case를 Gold Relevant 후보로 본다.
- 단순히 동일 산업이라는 이유만으로 관련 사례로 판정하지 않는다.
- 동일 Strategy를 사용했다는 이유로 관련 사례로 판정하지 않는다.
- Problem View 기준 관련성이 우선이다.

최종 Gold Relevant Cases는 라벨링 반복 결과와 검토 후 확정한다.

---

## 7. Gold Strategy Set

Gold Strategy Set은 Retrieval relevance를 먼저 확정한 후 구성한다.

절차:
1. Gold Relevant Cases를 먼저 고정
2. 해당 Case의 frozen `strategy` label 확인
3. Strategy Taxonomy v1 기준으로 집계
4. Query와 무관하게 우연히 함께 붙은 Strategy가 포함되는지 검토
5. 최종 Gold Strategy Set 확정

Strategy를 먼저 보고 관련 Case를 고르는 역방향 라벨링은 금지한다.

---

## 8. 평가 지표

### Recall@K

`Gold Relevant Cases` 중 Top-K에서 회수한 사례의 비율.

### Perspective Coverage@K

Gold Perspective 중 Top-K 검색 결과에서 **관련 사례(관련도 3 이상)**를 적어도 하나 회수한 Perspective의 비율.

이 지표는 단일 Query가 놓칠 수 있는 복수 관점을 다중관점 검색이 얼마나 보존하는지 확인하기 위한 보조 검색지표다.

### Perspective 중복 허용 원칙

하나의 AX Case가 둘 이상의 Gold Perspective에서 관련도 3 이상을 받을 수 있다. 이는 오류가 아니라 실제 기업 사례가 여러 문제요소를 동시에 해결할 수 있기 때문에 허용한다.

따라서 Perspective Coverage@K는 "서로 다른 Case 수"가 아니라 **각 Gold Perspective를 대표할 수 있는 관련 Case가 Top-K 안에 존재하는지**를 측정한다.

단, 한 Case가 여러 Perspective를 동시에 cover해 지표가 쉽게 높아지는지 확인하기 위해 Query별 Perspective 간 Gold Case overlap을 별도로 기록하고 해석한다.

### Strategy Coverage@K

Gold Strategy Set 중 검색/추천 결과를 통해 발견된 Strategy의 비율.

---

## 9. Annotation / 검토 절차

현재 실험안:

1. Query 및 Draft Perspective 생성
2. Perspective × Case relevance 독립 라벨링
3. LLM 반복평가를 수행하는 경우 각 run 결과를 분리 저장
4. threshold(2↔3) 경계 사례와 run 간 큰 불일치 사례를 우선 검토
5. 연구자 검토 후 Gold 확정
6. 확정 전 파일은 `DRAFT` 또는 `PILOT` 상태 유지

반복 횟수와 집계 방식(예: median)은 Pilot 라벨 안정성 확인 후 v1 전에 고정한다.

---

## 10. 파일 구조

```text
data/
├─ ground_truth_protocol.md
├─ retrieval_queries_v0.1.csv
├─ perspective_case_relevance_v0.1.csv
└─ retrieval_gold_v0.1.csv
```

### retrieval_queries_v0.1.csv
평가 Query와 Draft Perspective 관리.

### perspective_case_relevance_v0.1.csv
Query × Perspective × Case 관련도 0~4 저장.

### retrieval_gold_v0.1.csv
검토 완료 후 Query별 Gold Relevant Cases / Gold Strategy Set / Gold Perspective를 집계.

---

## 11. 현재 상태

- Protocol: v0.1 작성
- Query: 10건 Draft 작성
- GTQ001 Perspective × Case 라벨링: 300개 완료
- GTQ001 Gold: PILOT_GOLD_ADJUDICATED
- GTQ002 Perspective × Case 라벨링: 300개 완료
- GTQ002 Gold: PILOT_GOLD_ADJUDICATED
- 누적 라벨: 600개
- GTQ001~GTQ002에서 0~4 척도 / 3점 threshold / overlap 허용 / Strategy co-label 검토 규칙 재현성 확인
- GTQ003~GTQ010: Draft
- Baseline 실행: Ground Truth v1 확대·확정 후 시작
