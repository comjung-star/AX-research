# GTQ008 Ground Truth Review

검토일: **2026-10-21**

## Reference Perspective 결과

### P1_FORECAST_UNCERTAINTY
- Gold >=3: **5건**
- Cases: AX0031, AX0050, AX0051, AX0052, AX0055
- Branch-only: 없음

### P2_PLANNING_OPTIMIZATION
- Gold >=3: **11건**
- Cases: AX0026, AX0028, AX0030, AX0031, AX0040, AX0050, AX0051, AX0052, AX0055, AX0093, AX0094
- Branch-only: AX0030, AX0040

### P3_EXPERT_RULE_LIMITATION
- Gold >=3: **9건**
- Cases: AX0026, AX0028, AX0031, AX0050, AX0051, AX0052, AX0055, AX0093, AX0094
- Branch-only: 없음

## Overlap
- P1↔P2 Jaccard: 0.455
- P1↔P3 Jaccard: 0.556
- P2↔P3 Jaccard: 0.818
- Query-level union: **11건**

## Strategy count in relevant cases
- S5_OPTIMIZATION_DECISION_SUPPORT: 10
- S4_PREDICTION_DETECTION: 8
- S6_WORKFLOW_PROCESS_AUTOMATION: 7
- S2_AGENT_CONVERSATIONAL_AI: 2

## Gold Strategy
- S4_PREDICTION_DETECTION
- S5_OPTIMIZATION_DECISION_SUPPORT

## Adjudication
- 3점 threshold 유지
- Perspective overlap 허용
- Reference Perspective 유지
- Status: `PILOT_GOLD_ADJUDICATED`
