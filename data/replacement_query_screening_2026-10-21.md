# Replacement Dev Query Screening — 2026-10-21

## 목적

초기 GTQ006/007/009는 1차 relevance 검토에서 세 Perspective의 Gold 후보 집합이 완전히 동일해 Dev Benchmark의 Perspective Coverage 변별력이 낮았다.

기존 Query와 900개 라벨은 Archive에 보존하고, 아래 대체 후보는 **Query/Reference Perspective 의미를 먼저 설계한 뒤 Problem View만으로 Preliminary relevance를 확인**했다.

Screening 기준:
1. 자연스러운 Business Problem
2. Query-grounded / Problem-oriented / 의미적으로 독립적인 Perspective
3. 각 Perspective에 최소 관련사례 근거 존재
4. 세 Perspective의 관련사례 집합이 완전히 동일하지 않음
5. 적어도 하나의 branch가 다른 branch에 없는 추가 Relevant Case를 가짐

이 단계의 Case 목록은 Screening용 후보이며, 최종 Ground Truth는 100건 전체 0~4 라벨링 및 adjudication 후 확정한다.

## GTQ006 — 상품 카탈로그·검색·개인화 탐색

**Query**  
상품 수가 빠르게 늘면서 신규 상품의 속성 분류와 태깅을 사람이 처리해 온보딩이 느리고, 고객 검색어가 상품 데이터와 잘 연결되지 않아 원하는 상품을 찾지 못하는 경우가 많으며, 고객 상황에 맞는 탐색 지원도 부족하다.

**Reference Perspective 후보**
- P1_CATALOG_ENRICHMENT_BURDEN — 상품 속성 분류·태깅 부담  
  Preliminary relevant: AX0079, AX0095  
  Branch-only: AX0079, AX0095
- P2_SEARCH_FINDABILITY_GAP — 검색어-상품 연결 및 탐색 실패  
  Preliminary relevant: AX0039, AX0048, AX0084, AX0086  
  Branch-only: AX0039, AX0084
- P3_PERSONALIZED_DISCOVERY_GAP — 상황·개인조건 기반 상품발견 부족  
  Preliminary relevant: AX0044, AX0048, AX0086, AX0087  
  Branch-only: AX0044, AX0087

Pairwise Jaccard:
- P1↔P2: 0
- P1↔P3: 0
- P2↔P3: 0.333

Preliminary union: AX0039, AX0044, AX0048, AX0079, AX0084, AX0086, AX0087, AX0095  
Screening: **PASS**

## GTQ007 — 구매·견적 검토와 의사결정

**Query**  
구매와 견적 업무에서 고객 도면·요구사항과 공급업체 제안서처럼 형식이 다른 자료를 사람이 읽고 비교해야 하고, 생산가능성·원가·공급업체 선택 판단이 담당자 경험에 의존하며, 견적 작성과 조달 후속업무까지 수작업으로 이어져 처리시간이 길다.

**Reference Perspective 후보**
- P1_REQUIREMENT_DOCUMENT_REVIEW — 도면·요구사항·제안서 검토 부담  
  Preliminary relevant: AX0023, AX0024, AX0043, AX0045  
  Branch-only: AX0024, AX0043
- P2_EXPERT_COMPARATIVE_DECISION — 비교·선정 판단의 전문가 의존  
  Preliminary relevant: AX0023, AX0041, AX0045, AX0082  
  Branch-only: AX0041, AX0082
- P3_QUOTE_PROCUREMENT_WORKFLOW — 견적·조달 후속업무 수작업 병목  
  Preliminary relevant: AX0023, AX0045, AX0094  
  Branch-only: AX0094

Pairwise Jaccard:
- P1↔P2: 0.333
- P1↔P3: 0.4
- P2↔P3: 0.4

Preliminary union: AX0023, AX0024, AX0041, AX0043, AX0045, AX0082, AX0094  
Screening: **PASS**

## GTQ009 — 기업 생성형 AI의 보안·내부데이터·확산

**Query**  
직원들이 생성형 AI를 업무에 활용하려 하지만 외부 도구에 민감한 내부 데이터를 보낼 수 없고, 내부 문서와 업무시스템을 안전하게 연결하기 어려우며, 부서마다 개별 도구를 만들면 보안과 운영 기준을 일관되게 유지하면서 전사로 확산하기 어렵다.

**Reference Perspective 후보**
- P1_AI_SECURITY_COMPLIANCE_CONSTRAINT — 민감정보·규제에 따른 외부 AI 사용 제약  
  Preliminary relevant: AX0056, AX0071, AX0088  
  Branch-only: AX0071
- P2_INTERNAL_DATA_ACCESS_GAP — 내부 문서·시스템의 안전한 AI 연결 부족  
  Preliminary relevant: AX0004, AX0049, AX0056, AX0059, AX0090  
  Branch-only: AX0004, AX0049, AX0059, AX0090
- P3_ENTERPRISE_AI_SCALE_GOVERNANCE — 부서별 AI를 일관된 기준으로 확산하기 어려움  
  Preliminary relevant: AX0005, AX0018, AX0077, AX0088  
  Branch-only: AX0005, AX0018, AX0077

Pairwise Jaccard:
- P1↔P2: 0.143
- P1↔P3: 0.167
- P2↔P3: 0

Preliminary union: AX0004, AX0005, AX0018, AX0049, AX0056, AX0059, AX0071, AX0077, AX0088, AX0090  
Screening: **PASS**

## 해석

세 대체 후보 모두 Perspective 간 핵심 overlap은 허용하면서도 branch별 추가 사례가 존재해 초기 GTQ006/007/009와 달리 Dev Benchmark에서 branch preservation과 Perspective Coverage 차이를 평가할 여지가 있다.

이 결과를 근거로 세 Query를 Active Dev Query로 교체하고 전체 100 Case relevance 라벨링을 진행한다.
