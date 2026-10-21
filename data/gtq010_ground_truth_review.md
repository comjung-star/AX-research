# GTQ010 Ground Truth Review

검토일: **2026-10-21**

## Replacement Query

제조현장에서 생산·품질·설비 데이터가 여러 시스템에 나뉘어 있어 품질 이상이 발생했을 때 원인을 찾는 데 시간이 오래 걸리고, 주문이나 설비상태가 바뀔 때 생산계획을 다시 조정하는 일도 담당자의 수작업에 크게 의존하고 있다.

## Reference Perspectives

- **P1_MANUFACTURING_DATA_FRAGMENTATION** — 생산·품질·설비 데이터 분산
- **P2_QUALITY_ROOT_CAUSE_DELAY** — 품질 이상 원인분석 지연
- **P3_DYNAMIC_PRODUCTION_PLANNING** — 동적 생산계획 조정 부담

## Gold Relevant Cases

### P1
AX0007, AX0022, AX0025, AX0065, AX0093

### P2
AX0022, AX0034, AX0065, AX0093

### P3
AX0026, AX0028, AX0030, AX0093, AX0094

Query-level union: **10건**

## Branch-only Cases

- P1 only: AX0007, AX0025
- P2 only: AX0034
- P3 only: AX0026, AX0028, AX0030, AX0094

## Perspective Overlap

- P1↔P2 Jaccard: 0.5
- P1↔P3 Jaccard: 0.111
- P2↔P3 Jaccard: 0.125

공통 핵심 사례 overlap은 허용하되 세 branch 모두 추가 Relevant Case가 존재해 Dev Benchmark에서 branch preservation을 평가할 수 있다.

## Strategy Count

- S5_OPTIMIZATION_DECISION_SUPPORT: 10
- S4_PREDICTION_DETECTION: 6
- S6_WORKFLOW_PROCESS_AUTOMATION: 5
- S2_AGENT_CONVERSATIONAL_AI: 3

## Gold Strategy

- S4_PREDICTION_DETECTION
- S5_OPTIMIZATION_DECISION_SUPPORT
- S6_WORKFLOW_PROCESS_AUTOMATION

S4는 품질 이상·결함 분석, S5는 원인분석 및 생산계획 판단, S6는 수작업 계획/운영 workflow 개선과 직접 연결되어 Core로 유지한다.

## Adjudication

- 3점 threshold 유지
- 세 Reference Perspective 유지
- Gold Relevant union: 10건
- Status: `PILOT_GOLD_ADJUDICATED`

기존 다국어 현장 Query는 `RETIRED_SPARSE_BRANCH_SUPPORT_PILOT`로 Archive되어 있다.
