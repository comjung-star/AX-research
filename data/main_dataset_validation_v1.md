# Main Dataset v1 Validation

검증일: **2026-10-19**

## 1. 최종 판정

**PASS — Main Dataset v1 100건 구축 완료 / v1 Freeze**

연구계획서의 목표 범위인 **100~150건** 중 최소 목표인 100건을 충족했다.

이제 모델 실험을 위해 데이터 구성 규칙을 고정하고, 다음 단계인 **Retrieval Ground Truth 구축**으로 이동한다.

추가 사례가 발견되더라도 Main Dataset v1 100건은 그대로 유지하며, 필요 시 v1.1 또는 확장셋으로 별도 관리한다.

## 2. 구조 검증

- 총 사례: **100건**
- Case ID: **AX0001 ~ AX0100 연속**
- 필수 11개 필드 누락: **0**
- Case ID 중복: **0**
- Business Problem 완전 중복: **0**
- AX Target/Task 완전 중복: **0**
- Main QA Metadata: **100건**
- Root Cause Dictionary: **v1 9종 유지**
- Strategy Taxonomy: **v1 6종 유지**
- 신규 Root Cause 필요 사례: **0**
- 신규 Strategy 필요 사례: **0**

## 3. 이번 확장 배치

기존 52건에 **48건**을 추가했다.

### 실전 AX 리포트 검증 편입
- AX0053 롯데마트 육류 Vision AI
- AX0054 건설 특화 실시간 AI 번역
- AX0055 Vision AI 스마트팜
- AX0056 금융권 온프레미스 AI
- AX0057 AI 회의록
- AX0058 딥리서치/보고서/PPT
- AX0059 조직 지식관리 AI

PART 5의 나머지 사례:
- BOOK001 문화센터 추천: HOLD — 외부 원출처 부족
- BOOK003 Apps in ChatGPT 24개 계열사: HOLD — 정확한 24개 앱 외부 검증 부족
- BOOK005 한도견본 라벨검토: HOLD — 기업/원출처 부족
- BOOK008 공항철도: HOLD — 공개자료와 책의 3축 구성이 완전히 일치하지 않음
- BOOK009 수영장 안전: **PUB0004 Supplemental 편입**
- BOOK013 Onflow: HOLD — 현재는 개별 AX 업무사례보다 플랫폼/제품 성격이 강함

### 공식 고객사례 추가
- Microsoft: 10건
- AWS: 8건
- Google Cloud: 11건
- IBM: 8건
- 국내 기업 공개사례: 4건

## 4. Root Cause 분포

| Factor | Count |
|---|---:|
| F01 반복 수작업 | 48 |
| F02 정보·지식 분산 | 20 |
| F03 전문가 판단 의존 | 29 |
| F04 비정형 정보 복잡성 | 28 |
| F05 프로세스·시스템 분절 | 21 |
| F06 대량 처리·확장성 병목 | 52 |
| F07 데이터 가시성·통합 부족 | 12 |
| F08 오류·컴플라이언스 위험 | 34 |
| F09 예측·최적화 복잡성 | 28 |

모든 v1 Factor가 Main Dataset에서 유지된다.

## 5. Strategy 분포

| Strategy | Count |
|---|---:|
| S1 지식검색·RAG | 23 |
| S2 Agent·Conversational AI | 37 |
| S3 Document Intelligence | 31 |
| S4 Prediction·Detection | 35 |
| S5 Optimization·Decision Support | 49 |
| S6 Workflow·Process Automation | 56 |

모든 v1 Strategy가 충분한 사례를 확보했고, 신규 Strategy 범주는 필요하지 않았다.

## 6. Source / Industry 다양성

주요 원천 그룹은 Microsoft, Google Cloud, AWS, MakinaRocks, IBM, NIPA, 『실전 AX 리포트』 검증사례, CMES 등으로 구성된다.

단일 최대 그룹은 Microsoft 24건으로 **24%**이며, 하나의 출처가 절반 이상을 차지하던 초기 Pilot 편향은 크게 줄었다.

산업은 제조, 유통, 금융, 통신, 헬스케어, 법률, 교육, 농업, 물류, 건설, HR, 항공, 소프트웨어 등으로 확장됐다.

## 7. Leakage Guard

Root Cause는 계속 아래 Problem View만으로 판정했다.

- Business Problem
- AX Target / Task
- Business Context

다음 Solution 정보는 Blind RCA 판정에서 배제한다.

- Strategy
- AI Technology
- Implementation
- Outcome

## 8. Freeze 의미

**Main Dataset v1 100건을 모델 실험용 고정 데이터셋으로 사용한다.**

이는 앞으로 절대 사례를 추가하지 않는다는 의미가 아니다.

- 현재 논문의 v1 실험: 100건 고정
- 추가 검증 사례: 별도 후보/확장셋 관리
- Ground Truth와 실험 도중에는 AX0001~AX0100의 데이터 규칙을 임의로 바꾸지 않음

## 9. 다음 단계

**Retrieval Ground Truth 구축**

1. 평가용 Business Problem Query 설계
2. Query별 Multi-Perspective 정답 관점 정의
3. Perspective × Case 관련도 0~4 라벨 생성
4. Gold Relevant Cases 확정
5. Gold Strategy Set 확정
6. LLM 반복평가 + 사람 검토 절차 확정
7. Single-query Dense Retrieval baseline 실험 시작
