# GTQ005 Ground Truth Review

검토일: **2026-10-21**

## Reference Perspective 결과

### P1_DATA_SILO
- Gold >=3: **8건**
- Cases: AX0007, AX0025, AX0046, AX0049, AX0059, AX0065, AX0069, AX0093
- Branch-only: AX0025, AX0059, AX0069

### P2_VISIBILITY_GAP
- Gold >=3: **6건**
- Cases: AX0007, AX0046, AX0049, AX0065, AX0078, AX0093
- Branch-only: 없음

### P3_DECISION_DELAY
- Gold >=3: **6건**
- Cases: AX0007, AX0046, AX0049, AX0065, AX0078, AX0093
- Branch-only: 없음

## Overlap
- P1↔P2 Jaccard: 0.556
- P1↔P3 Jaccard: 0.556
- P2↔P3 Jaccard: 1
- Query-level union: **9건**

## Strategy count in relevant cases
- S5_OPTIMIZATION_DECISION_SUPPORT: 7
- S4_PREDICTION_DETECTION: 4
- S2_AGENT_CONVERSATIONAL_AI: 4
- S6_WORKFLOW_PROCESS_AUTOMATION: 3
- S1_KNOWLEDGE_RETRIEVAL_RAG: 3
- S3_DOCUMENT_INTELLIGENCE: 1

## Gold Strategy
- S5_OPTIMIZATION_DECISION_SUPPORT

## Adjudication
- 3점 threshold 유지
- Perspective overlap 허용
- Reference Perspective 유지
- Status: `PILOT_GOLD_ADJUDICATED`
