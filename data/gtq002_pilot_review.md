# GTQ002 Ground Truth Pilot Review

검토일: **2026-10-20**

## Query

> 영업과 서비스 담당자가 긴 이메일 스레드와 첨부 문서를 일일이 읽고 핵심 내용과 후속 조치를 정리하는 데 많은 시간을 쓰고 있다.

## Gold Perspectives

- **P1_UNSTRUCTURED_COMMUNICATION_COMPLEXITY** — 긴 비정형 커뮤니케이션 이해 부담
- **P2_ACTION_ITEM_EXTRACTION** — 후속조치 식별 부담
- **P3_REPETITIVE_SUMMARIZATION** — 반복 요약·정리 업무

세 Perspective는 각각 **이해 → 행동 식별 → 요약 반복부담**이라는 서로 다른 문제차원을 나타낸다.

## 라벨링 범위

- Main Dataset v1: AX0001~AX0100
- 3 Perspectives × 100 Cases = **300개**
- 관련도: 0~4
- Gold 후보 threshold: **3점 이상**
- 판정 입력: Problem View만 사용

## 점수 분포

### P1

| 점수 | 건수 |
|---:|---:|
| 0 | 42 |
| 1 | 19 |
| 2 | 30 |
| 3 | 6 |
| 4 | 3 |

Gold: **9건**

`AX0002, AX0042, AX0057, AX0062, AX0069, AX0074, AX0075, AX0081, AX0092`

### P2

| 점수 | 건수 |
|---:|---:|
| 0 | 67 |
| 1 | 23 |
| 2 | 7 |
| 3 | 1 |
| 4 | 2 |

Gold: **3건**

`AX0002, AX0057, AX0069`

P2는 정답 사례 수가 적지만 세 사례 모두 커뮤니케이션에서 후속조치 또는 액션아이템을 식별하는 업무가 직접 포함되어 있어 높은 정밀도의 Perspective로 유지한다.

### P3

| 점수 | 건수 |
|---:|---:|
| 0 | 55 |
| 1 | 31 |
| 2 | 3 |
| 3 | 4 |
| 4 | 7 |

Gold: **11건**

`AX0002, AX0042, AX0048, AX0057, AX0058, AX0061, AX0062, AX0069, AX0075, AX0081, AX0092`

## Query-level Gold Relevant Cases

중복 제거 후 **12건**:

`AX0002, AX0042, AX0048, AX0057, AX0058, AX0061, AX0062, AX0069, AX0074, AX0075, AX0081, AX0092`

## Perspective Overlap

P2의 3개 Gold Case는 모두 P1 또는 P3와 겹친다.

이는 P2를 제거해야 한다는 뜻이 아니다.

액션아이템 추출은 실제로 긴 커뮤니케이션 이해나 요약과 함께 발생하는 경우가 많고, GTQ002 문장에 **"후속 조치"**가 명시되어 있어 별도 문제관점으로 유지할 근거가 충분하다.

따라서:
- Perspective overlap 허용
- P2 유지
- Coverage 해석 시 overlap 별도 기록

GTQ001과 동일한 규칙이 재현되었다.

## Gold Strategy Adjudication

관련사례의 Strategy label 전체에는 S1/S2/S3/S5/S6이 나타났지만 Query의 핵심 해결방식과 직접 연결되는 것은 다음 두 개로 판정했다.

- **S3_DOCUMENT_INTELLIGENCE**
- **S6_WORKFLOW_PROCESS_AUTOMATION**

### 제외
- S1: 일부 사례의 지식검색 부가 기능
- S2: 일부 사례의 대화형 기능
- S5: 일부 사례의 의사결정지원 부가 기능

Strategy co-label을 단순 union하지 않고 Query와 직접 관련된 핵심 Strategy만 Gold로 유지하는 GTQ001 규칙을 그대로 적용했다.

## Pilot 재현성 판단

GTQ001에서 정한 다음 규칙이 GTQ002에서도 적용 가능했다.

- 0~4 관련도 척도: 유지 가능
- 3점 이상 threshold: 유지 가능
- Gold Perspective overlap 허용: 유지 가능
- Strategy co-label 제거: 적용 가능
- Problem View 기반 relevance 판정: 적용 가능

따라서 Ground Truth Protocol v0.1을 GTQ003~GTQ010에 확대 적용해도 된다고 판단한다.

## 상태

`PILOT_GOLD_ADJUDICATED`

## 다음 단계

GTQ003부터 동일한 Protocol로 Ground Truth를 확대한다.

## 한 줄 결론

**GTQ002도 300개 라벨링과 Adjudication을 완료했으며, GTQ001에서 만든 Ground Truth 규칙이 두 번째 Query에서도 안정적으로 적용됐다.**
