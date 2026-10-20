# GTQ003 Ground Truth Review

검토일: **2026-10-20**

## Query

> 업무에 필요한 규정과 매뉴얼, 과거 사례가 여러 시스템과 문서 저장소에 흩어져 있어 직원들이 필요한 정보를 찾는 데 시간이 오래 걸리고 이미 있는 자료를 다시 만드는 경우가 많다.

## Gold Perspectives

- **P1_KNOWLEDGE_FRAGMENTATION** — 정보·지식 분산
- **P2_SEARCH_DELAY** — 업무정보 검색 지연
- **P3_KNOWLEDGE_REUSE_GAP** — 기존 지식 재사용 부족

세 Perspective는 각각 **원인/구조(분산) → 업무영향(검색 지연) → 재사용 문제(재작성·반복검토)**라는 서로 다른 문제차원을 나타낸다.

## 라벨링 범위

- Main Dataset v1: AX0001~AX0100
- 3 Perspectives × 100 Cases = **300개**
- 관련도: 0~4
- Gold threshold: **3점 이상**
- 판정 입력: Problem View만 사용

## 점수 분포

### P1 — Knowledge Fragmentation

| 점수 | 건수 |
|---:|---:|
| 0 | 44 |
| 1 | 30 |
| 2 | 19 |
| 3 | 4 |
| 4 | 3 |

Gold: **7건**

`AX0004, AX0009, AX0049, AX0058, AX0059, AX0066, AX0090`

### P2 — Search Delay

| 점수 | 건수 |
|---:|---:|
| 0 | 23 |
| 1 | 42 |
| 2 | 17 |
| 3 | 8 |
| 4 | 10 |

Gold: **18건**

`AX0004, AX0009, AX0010, AX0016, AX0039, AX0042, AX0049, AX0056, AX0058, AX0059, AX0062, AX0063, AX0066, AX0071, AX0078, AX0090, AX0091, AX0096`

### P3 — Knowledge Reuse Gap

| 점수 | 건수 |
|---:|---:|
| 0 | 57 |
| 1 | 12 |
| 2 | 19 |
| 3 | 7 |
| 4 | 5 |

Gold: **12건**

`AX0004, AX0010, AX0023, AX0039, AX0042, AX0058, AX0059, AX0062, AX0075, AX0090, AX0091, AX0096`

## Query-level Gold Relevant Cases

중복 제거 후 **20건**:

`AX0004, AX0009, AX0010, AX0016, AX0023, AX0039, AX0042, AX0049, AX0056, AX0058, AX0059, AX0062, AX0063, AX0066, AX0071, AX0075, AX0078, AX0090, AX0091, AX0096`

## Perspective Overlap

Pairwise Jaccard:
- P1 ↔ P2: **0.389**
- P1 ↔ P3: **0.267**
- P2 ↔ P3: **0.500**

세 Perspective 모두에 동시에 관련된 사례:
- AX0004
- AX0058
- AX0059
- AX0090

### Perspective별 고유 Gold Case

P1 only:
- 없음

P2 only:
- AX0016
- AX0056
- AX0063
- AX0071
- AX0078

P3 only:
- AX0023
- AX0075

P1은 구조적 원인인 "지식 분산"이므로 실제 사례에서 검색 지연(P2)과 함께 나타나는 경향이 강하다. 고유 Case가 없다는 이유만으로 P1을 제거하지 않는다.

반면 P2와 P3에서는 실제로 다른 관점 때문에 추가 Gold Case가 발생했다. 이는 다중관점이 서로 완전히 배타적일 필요는 없지만, 일부 Perspective가 단일 관점에서 놓칠 수 있는 사례를 추가로 포착할 수 있다는 평가구조를 보여준다.

## Gold Strategy Adjudication

20개 Gold Relevant Case에서 Strategy 빈도:
- S1_KNOWLEDGE_RETRIEVAL_RAG: 18
- S2_AGENT_CONVERSATIONAL_AI: 15
- S3_DOCUMENT_INTELLIGENCE: 6
- S5_OPTIMIZATION_DECISION_SUPPORT: 5
- S6_WORKFLOW_PROCESS_AUTOMATION: 4

Query의 핵심 문제와 직접 관련된 Core Gold Strategy:
- **S1_KNOWLEDGE_RETRIEVAL_RAG**
- **S2_AGENT_CONVERSATIONAL_AI**

S1은 분산된 지식 검색·재사용과 직접 연결되고, S2는 다수 관련사례에서 자연어 기반 지식 접근·질의응답 인터페이스로 반복적으로 나타난다.

S3/S5/S6은 일부 관련사례의 문서처리·의사결정·프로세스 자동화 부가기능으로 판단해 Core Gold에서는 제외한다.

## Adjudication

- 0~4 척도 유지
- 3점 이상 threshold 유지
- P1/P2/P3 모두 유지
- Perspective overlap 허용
- Gold Strategy=S1/S2
- 상태: `PILOT_GOLD_ADJUDICATED`

## 연구적으로 확인된 점

GTQ003에서는 P2-only 5건, P3-only 2건이 확인됐다.

따라서 Ground Truth 자체가 "모든 Perspective가 동일한 정답사례를 갖도록" 만들어진 것이 아니며, 관점에 따라 추가 관련사례를 찾을 수 있는 평가구조를 가진다.

이후 실제 실험에서는 Single Query와 Multi-Perspective Retrieval을 비교해 이러한 고유 관련사례가 실제로 추가 회수되는지 Recall@K / Perspective Coverage@K로 검증한다.

## 다음 단계

GTQ004 Ground Truth 라벨링 및 Adjudication.

## 한 줄 결론

**GTQ003 300개 라벨링과 Gold 확정을 완료했고, 검색 지연(P2)과 지식 재사용(P3) 관점에서 서로 다른 고유 관련사례가 확인되어 다중관점 평가의 실질적 변별 가능성이 나타났다.**
