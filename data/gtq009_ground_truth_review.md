# GTQ009 Ground Truth Review

검토일: **2026-10-21**

## Reference Perspective 결과

### P1_AI_SECURITY_COMPLIANCE_CONSTRAINT
- Gold >=3: **3건**
- Cases: AX0056, AX0071, AX0088
- Branch-only: AX0071

### P2_INTERNAL_DATA_ACCESS_GAP
- Gold >=3: **5건**
- Cases: AX0004, AX0049, AX0056, AX0059, AX0090
- Branch-only: AX0004, AX0049, AX0059, AX0090

### P3_ENTERPRISE_AI_SCALE_GOVERNANCE
- Gold >=3: **4건**
- Cases: AX0005, AX0018, AX0077, AX0088
- Branch-only: AX0005, AX0018, AX0077

## Overlap
- P1↔P2 Jaccard: 0.143
- P1↔P3 Jaccard: 0.167
- P2↔P3 Jaccard: 0
- Query-level union: **10건**

## Strategy count in relevant cases
- S2_AGENT_CONVERSATIONAL_AI: 9
- S1_KNOWLEDGE_RETRIEVAL_RAG: 8
- S6_WORKFLOW_PROCESS_AUTOMATION: 5
- S5_OPTIMIZATION_DECISION_SUPPORT: 1

## Gold Strategy
- S1_KNOWLEDGE_RETRIEVAL_RAG
- S2_AGENT_CONVERSATIONAL_AI

## Adjudication
- 3점 threshold 유지
- Perspective overlap 허용
- Reference Perspective 유지
- Status: `PILOT_GOLD_ADJUDICATED`
