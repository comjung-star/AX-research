# GTQ001 Ground Truth Pilot Review

검토일: **2026-10-20**

## 1. Pilot 목적

GTQ001 한 건을 이용해 다음을 먼저 검증했다.

- Query별 Perspective 정의가 실제 Main Dataset v1 100건에서 구분 가능한가?
- Perspective × Case 관련도 0~4 기준을 일관되게 적용할 수 있는가?
- Pilot 기준인 `3점 이상 = Gold Relevant 후보`가 지나치게 넓거나 좁지 않은가?
- Perspective Coverage@K를 계산할 수 있을 만큼 Perspective별 정답사례가 구분되는가?

GTQ001은 아직 Final Gold가 아니라 **Pilot Ground Truth**다.

---

## 2. GTQ001

### Query

> 고객 문의가 빠르게 늘면서 상담 인력이 반복 질문 처리에 대부분의 시간을 쓰고 있어 복잡한 문제 대응이 늦어지고 답변 품질도 일정하게 유지하기 어렵다.

### Draft Perspectives

- **P1_HIGH_VOLUME_SUPPORT_BOTTLENECK** — 대량 문의 처리 병목
- **P2_REPETITIVE_SUPPORT_WORK** — 반복 응대 업무 부담
- **P3_SUPPORT_KNOWLEDGE_CONSISTENCY** — 지원 지식 접근 및 답변 일관성

---

## 3. 라벨링 범위

```text
3 Perspectives × 100 Main Cases = 300 relevance judgments
```

판정 입력:
- Business Problem
- AX Target / Task
- Business Context

판정에서 Solution View는 사용하지 않았다.
- Strategy
- AI Technology
- Implementation
- Outcome

이는 검색 Ground Truth에 Solution 정보가 미리 새어 들어가는 Leakage를 줄이기 위한 것이다.

---

## 4. 관련도 분포

### P1 — 대량 문의 처리 병목

| 점수 | 건수 |
|---:|---:|
| 0 | 67 |
| 1 | 14 |
| 2 | 9 |
| 3 | 4 |
| 4 | 6 |

Gold 후보(3점 이상): **10건**

`AX0001, AX0016, AX0017, AX0047, AX0060, AX0066, AX0067, AX0070, AX0074, AX0091`

### P2 — 반복 응대 업무 부담

| 점수 | 건수 |
|---:|---:|
| 0 | 58 |
| 1 | 24 |
| 2 | 10 |
| 3 | 2 |
| 4 | 6 |

Gold 후보(3점 이상): **8건**

`AX0016, AX0047, AX0049, AX0060, AX0066, AX0067, AX0070, AX0091`

경계사례 검토 후:
- AX0049: 2 → 3
- AX0066: 2 → 3

두 사례는 단순한 반복작업이 아니라 고객응대/일반문의 처리와 직접 연결되어 있어 3점 정의에 더 부합한다고 판정했다.

### P3 — 지원 지식 접근 및 답변 일관성

| 점수 | 건수 |
|---:|---:|
| 0 | 60 |
| 1 | 8 |
| 2 | 20 |
| 3 | 2 |
| 4 | 10 |

Gold 후보(3점 이상): **12건**

`AX0004, AX0009, AX0010, AX0016, AX0049, AX0062, AX0066, AX0067, AX0071, AX0091, AX0092, AX0096`

---

## 5. Query-level Gold Relevant 후보

3개 Perspective의 3점 이상 Case를 합치면 중복 제거 후 **18건**이다.

```text
AX0001
AX0004
AX0009
AX0010
AX0016
AX0017
AX0047
AX0049
AX0060
AX0062
AX0066
AX0067
AX0070
AX0071
AX0074
AX0091
AX0092
AX0096
```

현재 상태는 `PILOT_PROVISIONAL_NOT_FINAL`이다.

---

## 6. Strategy 후보 검토

18개 관련사례의 Strategy label을 모으면 다음이 나타난다.

- S1_KNOWLEDGE_RETRIEVAL_RAG
- S2_AGENT_CONVERSATIONAL_AI
- S3_DOCUMENT_INTELLIGENCE
- S5_OPTIMIZATION_DECISION_SUPPORT
- S6_WORKFLOW_PROCESS_AUTOMATION

하지만 Strategy를 사례에서 기계적으로 합치지 않고 GTQ001과의 직접 관련성을 다시 검토했다.

### Provisional Core Gold Strategy

- **S1_KNOWLEDGE_RETRIEVAL_RAG**
- **S2_AGENT_CONVERSATIONAL_AI**
- **S6_WORKFLOW_PROCESS_AUTOMATION**

### 제외한 부가 co-label

- S3_DOCUMENT_INTELLIGENCE
  - AX0062/AX0074/AX0092의 부가 기능으로 존재하지만 GTQ001의 핵심 문제 자체가 문서처리는 아님.
- S5_OPTIMIZATION_DECISION_SUPPORT
  - AX0062의 부가 label로 존재하나 GTQ001의 고객지원 문제에 대한 핵심 Strategy로 보기 어려움.

따라서 Gold Strategy Set도 아직 Final이 아닌 **Provisional** 상태로 유지한다.

---

## 7. Pilot에서 발견된 중요한 이슈

### 이슈 A — 0~4 척도는 사용 가능

직접 관련(4), 강한 관련(3), 부분 관련(2)을 대부분 구분할 수 있었다.

다만 2↔3 경계는 실제 사례를 보면서 Calibration이 필요했다.

### 이슈 B — 3점 threshold는 현재 사용 가능

3점 이상 기준에서 Perspective별 후보가 8~12건으로 생성됐다.

전체 100건 중 Query-level union이 18건이므로 지나치게 희소하지도, 절반 이상으로 넓지도 않았다.

따라서 **Pilot 기준으로는 3점 threshold를 유지할 수 있다.**

단, 다른 Query에서도 같은 분포가 나오는지 확인한 뒤 v1에서 확정해야 한다.

### 이슈 C — P2의 독립성이 약함

P2 Gold 후보 8건은 모두 P1 또는 P3 Gold 후보와 겹친다.

즉:

> **P2만을 대표하는 독립 Gold Case가 현재 0건**

이다.

또한 다음 사례는 세 Perspective 모두를 커버한다.

- AX0016
- AX0066
- AX0067
- AX0091

이 상태에서 단순 Perspective Coverage@K를 사용하면 위 사례 하나를 검색하는 것만으로 여러 Perspective가 동시에 covered 처리될 수 있다.

따라서 **GTQ001을 바로 Final Gold로 확정하면 안 된다.**

---

## 8. 현재 판정

### 완료

- 300개 Perspective × Case 1차 Pilot 라벨링
- 2↔3 경계사례 일관성 검토
- Provisional Gold Relevant Cases 도출
- Provisional Gold Strategy Set 검토

### 보류

- Gold Perspective 최종 확정
- GTQ001 Final Gold 확정
- Perspective Coverage 평가규칙 확정

### 이유

P2와 다른 Perspective의 관련사례 중첩이 높아 Perspective 분리성이 충분한지 추가 검토가 필요하다.

---

## 9. 다음 작업

1. **GTQ001 Perspective Adjudication**
   - P1/P2/P3 정의를 유지할지 검토
   - 특히 P2를 별도 Perspective로 유지할 연구적 의미 확인
   - 필요 시 문구를 더 명확하게 좁힘

2. **GTQ001 반복평가 / 일관성 검토**
   - 동일 기준으로 재평가
   - 2↔3 경계사례 중심 재검토
   - 반복 LLM 평가를 사용할 경우 각 Run을 분리 저장

3. **GTQ001 Final Gold 확정**
   - Gold Perspectives
   - Gold Relevant Cases
   - Gold Strategy Set

4. GTQ001 기준이 안정된 뒤 GTQ002~GTQ010으로 확대

---

## 한 줄 결론

**GTQ001 300개 Pilot 라벨링은 성공적으로 완료했지만, P2 관련사례가 P1/P3와 모두 겹쳐 Perspective Coverage 평가의 변별력이 약해질 수 있다는 중요한 설계 이슈를 발견했다. 따라서 Final Gold 확정 전에 Perspective Adjudication을 한 번 거치는 것이 필요하다.**


## 10. Adjudication 결과

후속 검토 결과 P1/P2/P3는 모두 유지한다.

- P1: 처리용량/규모 문제
- P2: 반복업무/인력집중 문제
- P3: 지식접근/답변품질 문제

P2의 Gold Case가 P1/P3와 겹치는 것은 제거 사유로 보지 않는다. 하나의 AX 사례가 여러 문제차원을 동시에 해결할 수 있으므로 Case의 복수 Perspective 소속을 허용한다.

다만 Perspective Coverage@K의 과도한 해석을 피하기 위해 Query별 Gold Case overlap을 별도 기록한다.

GTQ001 상태:
- `PILOT_GOLD_ADJUDICATED`

세부 결정은 `data/gtq001_adjudication.md`에 기록한다.
