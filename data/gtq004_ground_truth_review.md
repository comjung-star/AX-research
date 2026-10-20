# GTQ004 Ground Truth Review

검토일: **2026-10-20**

## Query

> 심사와 검증 업무에서 여러 형식의 문서를 사람이 읽고 필수 항목과 규정 준수 여부를 일일이 확인해야 해서 처리시간이 길고 누락이나 오류 위험도 높다.

## Reference Perspectives

- **P1_DOCUMENT_REVIEW_BURDEN** — 비정형 문서 검토 부담
- **P2_COMPLIANCE_CHECK_RISK** — 규정·검증 누락 위험
- **P3_MANUAL_VERIFICATION** — 반복 수작업 검증

세 Perspective는 각각 **문서를 읽는 부담 / 규정·기준 판단의 위험 / 반복 확인 작업**이라는 서로 다른 문제차원을 나타낸다.

## 라벨링 범위

- Main Dataset v1: AX0001~AX0100
- 3 Perspectives × 100 Cases = **300개**
- 관련도: 0~4
- Gold threshold: **3점 이상**
- 관련도 판정: Problem View만 사용

## 경계 Calibration

GTQ004는 "문서 업무 일반"이 아니라 "심사·검증"이 핵심이므로 2↔3 경계를 엄격하게 재검토했다.

적용 원칙:
- 단순히 문서를 처리한다는 이유만으로 P1/P3 Gold로 올리지 않음
- 규제산업이라는 이유만으로 P2 Gold로 올리지 않음
- 실제 Problem/Task에서 검토·준수판정·확인/검증 부담이 직접 나타나는지 확인

## 점수 분포

### P1 — Document Review Burden
- 0점: 52
- 1점: 22
- 2점: 9
- 3점: 2
- 4점: 15
- Gold: **17건**

Gold:
`AX0003, AX0008, AX0012, AX0013, AX0014, AX0015, AX0023, AX0024, AX0042, AX0043, AX0045, AX0072, AX0076, AX0080, AX0082, AX0095, AX0100`

### P2 — Compliance Check Risk
- 0점: 37
- 1점: 34
- 2점: 18
- 3점: 4
- 4점: 7
- Gold: **11건**

Gold:
`AX0003, AX0013, AX0019, AX0043, AX0064, AX0068, AX0076, AX0080, AX0082, AX0085, AX0095`

### P3 — Manual Verification
- 0점: 32
- 1점: 25
- 2점: 28
- 3점: 11
- 4점: 4
- Gold: **15건**

Gold:
`AX0003, AX0008, AX0011, AX0019, AX0023, AX0043, AX0058, AX0064, AX0068, AX0074, AX0076, AX0080, AX0082, AX0085, AX0100`

## Query-level Gold Relevant Cases

중복 제거 후 **24건**:

`AX0003, AX0008, AX0011, AX0012, AX0013, AX0014, AX0015, AX0019, AX0023, AX0024, AX0042, AX0043, AX0045, AX0058, AX0064, AX0068, AX0072, AX0074, AX0076, AX0080, AX0082, AX0085, AX0095, AX0100`

## Perspective Overlap

Pairwise Jaccard:
- P1 ↔ P2: **0.333**
- P1 ↔ P3: **0.333**
- P2 ↔ P3: **0.529**

세 Perspective 모두에 관련된 사례:
- AX0003
- AX0043
- AX0076
- AX0080
- AX0082

### Perspective별 고유 Gold Case

P1 only:
- AX0012
- AX0014
- AX0015
- AX0024
- AX0042
- AX0045
- AX0072

P2 only:
- 없음

P3 only:
- AX0011
- AX0058
- AX0074

P2-only Case는 없지만, 규정·준수판정은 Query에 직접 명시된 독립 문제차원이고 P1/P3와 동일 개념이 아니므로 Reference Perspective로 유지한다.

## Gold Strategy Adjudication

24개 Relevant Case의 Strategy 빈도:
- S3_DOCUMENT_INTELLIGENCE: 19
- S6_WORKFLOW_PROCESS_AUTOMATION: 16
- S5_OPTIMIZATION_DECISION_SUPPORT: 15
- S4_PREDICTION_DETECTION: 7
- S2_AGENT_CONVERSATIONAL_AI: 4
- S1_KNOWLEDGE_RETRIEVAL_RAG: 3

Core Gold Strategy:
- **S3_DOCUMENT_INTELLIGENCE**
- **S5_OPTIMIZATION_DECISION_SUPPORT**
- **S6_WORKFLOW_PROCESS_AUTOMATION**

판단:
- S3: 문서 분류·정보추출·해석과 직접 연결
- S5: 추출된 근거를 바탕으로 규정 준수·위험·심사 판단을 지원
- S6: 반복 검토·검증 workflow 자동화와 직접 연결
- S4는 일부 이상/위반 탐지 사례에 해당하지만 Query 전체의 핵심 전략으로 보기에는 범위가 좁아 제외
- S1/S2는 일부 사례의 부가기능으로 제외

## Adjudication

- Reference Perspective P1/P2/P3 유지
- 3점 threshold 유지
- Query-level Gold Relevant Cases: 24건
- Core Gold Strategy: S3/S5/S6
- Status: `PILOT_GOLD_ADJUDICATED`

## 검증 중 이슈

경계 Calibration 자동 집계 과정에서 CSV 컬럼명을 잘못 참조해 임시 계산이 0건으로 표시되는 문제가 발생했다.
즉시 실제 헤더(`relevance_0_4`, `annotator_run`, `reason`)를 확인해 로직을 수정했고, 최종 파일은 다시 계산·검증했다. 잘못된 0건 결과는 최종 Ground Truth에 사용하지 않았다.

## 다음 단계

GTQ005 Dev Ground Truth 라벨링 및 Adjudication.
