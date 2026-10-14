# Taxonomy Freeze v1

Freeze date: **2026-10-14**

Basis:
- Core Pilot: **42 cases**
- Supplemental Public Set: **3 cases**
- Final diversification batch: **8 NIPA-backed non-MakinaRocks cases**
- Blind RCA performed using Problem View only

## Decision

**Root Cause Dictionary v1: FROZEN**

9 factors are fixed for Main Dataset v1.

| ID | Root Cause | Pilot count |
|---|---|---:|
| F01 | 반복 수작업 | 18 |
| F02 | 정보·지식 분산 | 6 |
| F03 | 전문가 판단 의존 | 11 |
| F04 | 비정형 정보 복잡성 | 10 |
| F05 | 프로세스·시스템 분절 | 7 |
| F06 | 대량 처리·확장성 병목 | 14 |
| F07 | 데이터 가시성·통합 부족 | 5 |
| F08 | 오류·컴플라이언스 위험 | 13 |
| F09 | 예측·최적화 복잡성 | 14 |

F09는 제조 중심 추가 샘플에서 처음 발견되었으나, 마지막 출처 다양화 검증에서 위성영상 분석(SI Analytics), 스마트교통(RexGen), 로보어드바이저(fint), AI 신용평가(AIZEN)에서도 반복적으로 나타났다.

따라서 F09는 제조에만 특화된 임시 라벨이 아니라 여러 산업에서 반복되는 독립 Root Cause로 판단한다.

## Strategy Taxonomy v1: FROZEN

6 strategies are fixed for Main Dataset v1.

| ID | Strategy | Pilot count |
|---|---|---:|
| S1 | 지식검색·RAG | 7 |
| S2 | 에이전트·대화형 AI | 12 |
| S3 | 문서 인텔리전스 | 12 |
| S4 | 예측·탐지 | 16 |
| S5 | 최적화·의사결정 지원 | 22 |
| S6 | 워크플로우·프로세스 자동화 | 21 |

42개의 Core Pilot 사례가 모두 위 6개 Strategy의 단일 또는 Multi-label 조합으로 표현되었으며, 마지막 8개 산업 다변화 사례에서도 새로운 Strategy 범주가 필요하지 않았다.

## Freeze의 의미

Freeze는 **앞으로 절대 수정하지 않는다**는 뜻이 아니다.

Main Dataset v1 100~150건을 구축할 때 동일한 라벨 기준을 유지하여 실험 기준이 중간에 변하지 않도록 한다는 뜻이다.

새 사례가 기존 체계로 명백히 설명되지 않는 경우에만 아래 절차를 따른다.

1. 기존 Factor/Strategy로 표현 가능한지 재검토
2. 최소 3건 이상에서 같은 미분류 패턴이 반복되는지 확인
3. 변경 이유와 영향범위를 문서화
4. v1을 수정하지 않고 필요하면 v2 후보로 관리

## Leakage Guard

Root Cause는 계속 Blind RCA로 부여한다.

Allowed:
- Business Problem
- AX Target / Task
- Business Context

Not allowed during RCA:
- Strategy
- AI Technology
- Implementation
- Outcome

Strategy labeling은 Solution View에서 별도로 수행한다.

## Next Step

Pilot 단계는 종료한다.

다음 단계는 **Main Dataset v1 100~150건 구축**이다.

Main Dataset은 다음 원칙으로 확장한다.

- Source diversity 유지
- 산업 다양성 유지
- 공식/공개 원천 우선
- v1 Dictionary / Taxonomy 동일 적용
- QA metadata 및 출처 추적성 유지
- 원문에 없는 정보는 UNKNOWN
