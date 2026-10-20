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

## 3. Query 역할과 작성 원칙

### 3.1 Dev / Pilot Query

현재 `GTQ001~GTQ010`은 **개발·검증용 Dev/Pilot Query**다.

- Main Dataset의 여러 AX 사례에서 반복되는 Business Problem 패턴을 바탕으로 연구용 문장으로 재구성한다.
- Ground Truth 기준, Prompt, 모델 구조, threshold 등 개발·검증 과정에서 반복적으로 사용할 수 있다.
- 따라서 최종 성능을 주장하는 Held-out Test Set으로 사용하지 않는다.

### 3.2 Held-out Test Query

최종 Test Query는 **모델·Prompt·평가규칙을 확정한 뒤 별도로 생성**한다.

- 개발 중 사용한 GTQ001~GTQ010과 분리한다.
- 가능하면 새로운 업무문제 시나리오나 독립 작성자가 만든 Query를 사용한다.
- Query 문장을 먼저 Freeze한 뒤 모델 출력과 독립적으로 Ground Truth를 구축한다.
- Test 결과를 확인한 뒤 Prompt나 모델을 다시 조정하지 않는다. 조정이 필요하면 해당 Test는 더 이상 최종 Test가 아니며 Dev로 재분류한다.
- 최종 Test Query 수와 작성자 구성은 실험 직전 별도 확정한다.

### 3.3 공통 Query 작성 원칙

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

## 4. Reference / Gold Perspective

하나의 Business Problem Query에 복수의 타당한 문제관점이 존재할 수 있다.

현재 파일 호환성을 위해 `gold_perspectives`라는 이름을 유지하지만, 의미상 **Reference Perspective(평가용 기준 관점)**로 사용한다.

Reference Perspective는 해당 Query에서 **최소한 놓치지 않기를 기대하는 기준 관점**이며, 가능한 모든 타당한 관점을 닫힌 목록으로 완전 열거한다는 뜻이 아니다.

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

### Reference Perspective 작성 원칙

Reference Perspective는 임의의 고정 Category에서 선택하지 않고, **각 Query 문장에 직접 드러난 독립적인 문제차원**을 분해해 작성한다.

작성 규칙:

1. **Query-grounded**  
   Query 문장 또는 함께 제공된 업무맥락에 직접 근거가 있는 문제요소만 관점 후보로 사용한다.

2. **Problem-oriented**  
   Perspective는 해결책이 아니라 문제를 바라보는 차원이어야 한다.  
   예: `지식 분산`, `검색 지연`, `반복 검증 부담`은 가능하지만 `RAG 도입`, `Agent 구축`은 제외한다.

3. **Semantic independence**  
   같은 뜻을 표현만 바꾼 관점은 중복으로 채택하지 않는다. 서로 다른 원인·부담·위험·업무결과 등 독립적인 문제차원을 우선한다.

4. **No solution leakage**  
   Strategy, AI Technology, Implementation 등 Solution View를 보고 Perspective를 역으로 만들지 않는다.

5. **No fixed perspective count**  
   Reference Perspective 수는 원칙적으로 고정하지 않는다. Query에 근거한 독립 문제차원 수에 따라 달라질 수 있다.  
   현재 `GTQ001~GTQ010`이 모두 3개 Perspective로 작성된 것은 **Pilot 단계의 비교·라벨링 편의를 위한 초기 형식**이며, Runtime 모델의 관점 수를 3개로 제한하는 규칙이 아니다.

6. **Draft → Adjudication**  
   최초 Perspective는 연구자의 해석에 기반한 Draft이며, Perspective × Case relevance 라벨링, 경계사례 검토, overlap 분석을 거쳐 Reference Perspective로 확정한다.

즉 Reference Perspective는 완전한 객관적 자연법칙처럼 자동 생성되는 정답이 아니라, **명시된 작성 규칙에 따라 Query를 분해하고 이후 검토를 거쳐 확정하는 평가용 기준**이다.

### Runtime Perspective와 Gold Perspective 구분

- **Reference / Gold Perspective**: 평가자가 사전에 확정한 최소 기준 관점
- **Generated Perspective**: 실제 사용 시 LLM이 사용자 Query를 보고 동적으로 생성하는 관점

Reference Perspective는 모델 입력에 제공하지 않는다. 실제 모델은 사용자 Query만 보고 `P1 ... Pk`를 동적으로 생성하며, 관점 개수와 종류도 고정하지 않는다.

Ground Truth의 Reference Perspective는 Generated Perspective 및 관점별 검색결과가 최소 기준을 얼마나 잘 포괄했는지 평가하기 위한 Benchmark다. **Ground Truth는 모델 입력용이 아니라 모델 평가용이다.**

### Reference에 없는 새로운 Generated Perspective

LLM이 Reference Perspective에 없는 관점을 생성했다고 해서 자동으로 오답 처리하지 않는다.

새 관점은 다음을 별도로 검토한다.

1. 사용자 Query에 직접적인 근거가 있는가
2. 기존 Reference/Generated Perspective의 단순한 표현 변경이 아닌가
3. 실제로 추가적인 Relevant Case를 회수하거나 독립적인 문제차원을 설명하는가

이 기준을 만족하는 관점은 **Novel Valid Perspective 후보**로 기록할 수 있다. 구체적인 정량화 방식은 Dev 실험에서 검증 후 최종 Test 전에 Freeze한다.

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

### Dev/Pilot
현재 실험안:

1. Query 및 Draft Perspective 생성
2. Perspective × Case relevance 독립 라벨링
3. LLM 반복평가를 수행하는 경우 각 run 결과를 분리 저장
4. threshold(2↔3) 경계 사례와 run 간 큰 불일치 사례를 우선 검토
5. 연구자 검토 후 Gold 확정
6. 확정 전 파일은 `DRAFT` 또는 `PILOT` 상태 유지

반복 횟수와 집계 방식(예: median)은 Pilot 라벨 안정성 확인 후 Dev Ground Truth v1 전에 고정한다.

### Held-out Test
1. 모델·Prompt·평가규칙 Freeze
2. 독립적인 Test Query 작성 및 Query Freeze
3. 모델 결과를 보지 않은 상태에서 Reference Perspective / Case relevance Ground Truth 구축
4. Ground Truth Freeze
5. 최종 모델 1회 평가
6. 결과 확인 후 모델을 다시 조정하지 않음

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

- Protocol: v0.1 작성 + 2026-10-20 교수 피드백 반영(Dev/Test 분리, Reference Perspective, Novel Perspective 처리)
- Query: 10건 Draft 작성
- GTQ001 Perspective × Case 라벨링: 300개 완료
- GTQ001 Gold: PILOT_GOLD_ADJUDICATED
- GTQ002 Perspective × Case 라벨링: 300개 완료
- GTQ002 Gold: PILOT_GOLD_ADJUDICATED
- GTQ003 Perspective × Case 라벨링: 300개 완료
- GTQ003 Gold: PILOT_GOLD_ADJUDICATED
- 누적 라벨: 1200개
- GTQ001~GTQ004에서 0~4 척도 / 3점 threshold / overlap 허용 / Strategy co-label 검토 규칙 재현성 확인
- GTQ004 Perspective × Case 라벨링: 300개 완료
- GTQ004 Gold: PILOT_GOLD_ADJUDICATED
- GTQ005~GTQ010: Draft
- Baseline 실행: Ground Truth v1 확대·확정 후 시작
