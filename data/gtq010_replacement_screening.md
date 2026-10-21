# Replacement GTQ010 Screening — 2026-10-21

## 대체 Query

**Business Problem**

제조현장에서 생산·품질·설비 데이터가 여러 시스템에 나뉘어 있어 품질 이상이 발생했을 때 원인을 찾는 데 시간이 오래 걸리고, 주문이나 설비상태가 바뀔 때 생산계획을 다시 조정하는 일도 담당자의 수작업에 크게 의존하고 있다.

**Goal**  
제조 데이터 활용, 품질 원인분석, 생산계획 대응력 개선

**Context**  
여러 생산·품질·설비 시스템을 함께 운영하며 품질이슈와 동적인 생산계획을 동시에 다뤄야 하는 제조조직

## Reference Perspective 후보

### P1_MANUFACTURING_DATA_FRAGMENTATION
생산·품질·설비 데이터 분산

Preliminary strong candidates:
- AX0007
- AX0022
- AX0025
- AX0065
- AX0093

### P2_QUALITY_ROOT_CAUSE_DELAY
품질 이상 원인분석 지연

Preliminary strong candidates:
- AX0022
- AX0034
- AX0065
- AX0093

### P3_DYNAMIC_PRODUCTION_PLANNING
동적 생산계획 조정 부담

Preliminary strong candidates:
- AX0026
- AX0028
- AX0030
- AX0093
- AX0094

## Screening

Branch-only candidate:
- P1 only: AX0007, AX0025
- P2 only: AX0034
- P3 only: AX0026, AX0028, AX0030, AX0094

공통 핵심 사례:
- AX0093

판정: **PASS**

세 Perspective는 Query에 직접 근거하며 서로 다른 문제차원을 나타내고, Main Dataset 안에서도 branch별 추가 Relevant Case가 존재한다.

주의:
- Screening은 Dev Benchmark 적합성 확인용이다.
- 최종 Gold는 100 Case 전체 0~4 relevance 라벨링 후 확정한다.
