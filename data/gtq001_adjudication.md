# GTQ001 Perspective Adjudication

검토일: **2026-10-20**

## 1. 검토 질문

GTQ001 Pilot에서 P2 관련사례 8건이 모두 P1 또는 P3와 겹쳤다.

검토 질문은 다음과 같다.

> P2가 다른 Perspective와 Gold Case를 공유한다는 이유만으로 P2를 제거하거나 합쳐야 하는가?

## 2. 결론

**P1 / P2 / P3를 모두 유지한다.**

이유는 세 Perspective가 서로 다른 문제차원을 표현하기 때문이다.

| Perspective | 문제차원 | 쉬운 설명 |
|---|---|---|
| P1_HIGH_VOLUME_SUPPORT_BOTTLENECK | Capacity / Scale | 문의량 증가 때문에 처리용량이 부족한가? |
| P2_REPETITIVE_SUPPORT_WORK | Work Pattern / Human Attention | 반복질문 처리 때문에 사람이 고부가가치 업무에 집중하지 못하는가? |
| P3_SUPPORT_KNOWLEDGE_CONSISTENCY | Knowledge / Quality | 필요한 지식을 찾기 어렵거나 답변품질을 일관되게 유지하기 어려운가? |

세 관점은 문장의 서로 다른 부분에 직접 근거한다.

GTQ001:
> 고객 문의가 **빠르게 늘면서** 상담 인력이 **반복 질문 처리에 대부분의 시간을 쓰고** 있어 복잡한 문제 대응이 늦어지고 **답변 품질도 일정하게 유지하기 어렵다.**

- "빠르게 늘면서" → P1
- "반복 질문 처리에 대부분의 시간을 쓰고" → P2
- "답변 품질도 일정하게 유지하기 어렵다" → P3

따라서 P2는 P1/P3의 단순 중복이 아니라 Query에 명시적으로 존재하는 별도 문제관점이다.

## 3. Gold Case 중복에 대한 판정

하나의 AX 사례가 복수 문제를 동시에 해결할 수 있으므로 동일 Case가 여러 Gold Perspective에 속하는 것을 허용한다.

예:
- AX0016: 대량 고객지원 + 반복문의 자동화 + 지식지원
- AX0066: 문의 증가 + 일반문의 자동처리 + 상담원 지식지원
- AX0067: FAQ 반복문의 + 자동응답 + 상담 handoff
- AX0091: 대량 기술지원 + 반복 저복잡도 문의 + 지식검색

이러한 사례가 P1/P2/P3에 동시에 관련되는 것은 라벨링 오류라기보다 실제 AX 사례의 다면성을 반영한다.

## 4. Perspective Coverage@K 해석 규칙

Perspective Coverage@K는 서로 다른 Case 개수를 세는 지표가 아니다.

각 Gold Perspective에 대해 Top-K 안에 관련도 3 이상인 Case가 하나 이상 존재하면 해당 Perspective가 covered 된 것으로 본다.

```text
Perspective Coverage@K
= covered Gold Perspectives / all Gold Perspectives
```

예를 들어 하나의 Case가 P1과 P2 모두에 관련도 3 이상이면 두 Perspective의 근거가 될 수 있다.

다만 이런 overlap 때문에 Coverage가 쉽게 높아질 수 있으므로 다음 값을 함께 기록한다.

- Perspective별 Gold Case 수
- Perspective 간 Gold Case overlap
- 모든 Perspective를 동시에 cover하는 Case 수

이는 Perspective Coverage를 과도하게 해석하지 않기 위한 보조 분석이다.

## 5. Runtime Perspective와 Gold Perspective

중요한 구분:

### 실제 사용
```text
User Business Problem
→ LLM
→ Generated P1 ... Pk
→ Perspective별 Retrieval
```

LLM은 사용자 Query마다 Perspective를 새로 생성한다.

### Ground Truth 평가
```text
GTQ001
→ 사전에 확정한 Gold Perspectives
→ Generated Perspectives / Retrieval 결과 평가
```

Gold Perspective는 모델에 입력하지 않는다.

현재 P1/P2/P3는 **실제 모델의 고정 관점이 아니라 GTQ001 평가용 정답 관점**이다.

## 6. GTQ001 Gold 확정

### Gold Perspectives

- P1_HIGH_VOLUME_SUPPORT_BOTTLENECK
- P2_REPETITIVE_SUPPORT_WORK
- P3_SUPPORT_KNOWLEDGE_CONSISTENCY

### Gold Relevant Cases

총 **18건**

`AX0001, AX0004, AX0009, AX0010, AX0016, AX0017, AX0047, AX0049, AX0060, AX0062, AX0066, AX0067, AX0070, AX0071, AX0074, AX0091, AX0092, AX0096`

### Core Gold Strategy Set

- S1_KNOWLEDGE_RETRIEVAL_RAG
- S2_AGENT_CONVERSATIONAL_AI
- S6_WORKFLOW_PROCESS_AUTOMATION

### 상태

`PILOT_GOLD_ADJUDICATED`

GTQ001은 Ground Truth Pilot 기준으로 Gold를 확정한다.

## 7. 다음 단계

GTQ001에서 정한 규칙을 그대로 GTQ002에 적용해 두 번째 Query에서도 다음이 재현되는지 확인한다.

1. 0~4 관련도 척도
2. 3점 이상 Gold threshold
3. Gold Perspective overlap 허용
4. Perspective Coverage@K 해석
5. Strategy co-label 제거 규칙

GTQ002 결과가 안정적이면 GTQ003~GTQ010으로 확대한다.

## 한 줄 결론

**P1/P2/P3는 서로 다른 문제차원이므로 모두 유지하며, Gold Case의 Perspective 중복은 실제 AX 사례의 다면성을 반영하는 것으로 허용한다. GTQ001은 Pilot Gold로 확정한다.**
