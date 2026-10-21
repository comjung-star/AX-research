# GTQ010 Dev Query Screening — 2026-10-21

## Query

외국인 근로자와 여러 언어를 사용하는 현장에서 작업지시와 안전정보가 제대로 전달되지 않아 의사소통이 늦어지고 오해로 인한 안전 위험도 있다.

## Draft Perspectives

- P1_LANGUAGE_BARRIER — 언어장벽으로 인한 의사소통 지연
- P2_SAFETY_COMMUNICATION — 안전정보 전달 위험
- P3_REALTIME_FIELD_COMMUNICATION — 현장 실시간 소통 요구

## Preliminary Problem-View Review

### P1_LANGUAGE_BARRIER
강한 후보:
- AX0054 — 건설현장 외국인 근로자, 안전지시·작업정보의 언어장벽
- AX0063 — 여러 지역·언어의 농업인이 전문지식에 접근하기 어려움

P1은 최소한 두 사례에서 언어 접근 문제를 확인할 수 있다.

### P2_SAFETY_COMMUNICATION
강한 후보:
- AX0054

AX0097/AX0098/AX0099에도 작업자 안전위험은 존재하지만 **의사소통/안전정보 전달 문제가 핵심이 아니므로** 3점 이상 후보로 올리지 않는다.

### P3_REALTIME_FIELD_COMMUNICATION
강한 후보:
- AX0054

AX0049는 현장 직원의 즉시 정보접근 문제, AX0063은 다국어 지식접근 문제와 부분 관련되지만 **실시간 현장 의사소통**을 직접 대표하기에는 부족하다.

## Screening Result

- P1: 최소 2건 strong candidate
- P2: 사실상 AX0054 1건
- P3: 사실상 AX0054 1건
- P2/P3 strong candidate set: 동일 singleton

판정: **HOLD — SPARSE BRANCH SUPPORT**

이 Query가 틀렸다는 의미는 아니다. 다만 Main Dataset v1에서 P2/P3를 독립적으로 평가할 사례가 거의 없어 Dev Benchmark에서 Perspective Coverage의 변별력이 매우 낮을 가능성이 높다.

현재 단계에서는 300개 전수 라벨링을 시작하지 않고 보류한다.

가능한 다음 선택:
1. GTQ010을 Low-discrimination/Sparse Pilot로 Archive하고 다른 Dev Query로 교체
2. 그대로 유지하되 Perspective Coverage 변별력이 낮은 Query로 명시
3. Main Dataset을 변경하지 않는 원칙을 유지하면서, Test 단계에서만 이런 자연스러운 sparse Query를 허용
