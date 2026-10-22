# AX Dataset v2 — 독립 원천 근거 전수 판정 보고서 (2026-10-22)

> **결론: 원천 근거 기반 잠정 적격 91 / 수정 보류 4 / 원천 열람 보류 3. 학술적 인간 검토 최종 승인 0.**

## 감사 대상과 결과

- 사용자 확정 정책 A: **실제 기업에서 운영된 업무만 Main Dataset 후보**. 파일럿/PoC는 별도 보존. **한 개의 업무 문제와 그에 적용된 실제 AX 해결을 한 건으로 보존**한다.
- `data/v2/main_cases_v2.json`의 98건 전체를 순서대로 재검토. 근거 메타데이터, 운영 단계, 업무 독립성, Root Cause·Strategy 분리, 직접 관계 근거, 성과 수치 귀속, 원본 계보·중복을 점검.
- 출처 URL 72개 중 공공 HTML 페이지 71개 접근; NIPA 첨부 PDF 1종은 이번 독립 세션에서 열람되지 않음. **웹페이지 열람 자체는 사실증명이나 원문 문장별 독립 감사와 다르다.** 잠정 적격 91건은 최소한 해당 업무의 **원천 문단에서 실제 적용/운영 사실과 구현 메커니즘을 확인하는 범위**의 AI 원천 QA를 통과했음을 뜻한다.
- 원천 QA 결과: **91건 `AI_SOURCE_QA_PASS`**, **4건 `REVIEW_CORRECTION`**, **3건 `REVIEW_PRIMARY_PASSAGE`**.
- 인적 검수·논문 Ground Truth 최종승인: **0건**. 인간 심사 및 독립 성과감사로 오인하지 않도록 선행 frozen v2.0.0 manifest, v1 및 실험을 변경하지 않았다.

| 구분 | 건수 | 사용 제한 |
|---|---:|---|
| 원천 검증 잠정 적격 | **91** | 운영 사례 코퍼스 *후보*로 분리. 사람 최종 승인 전에는 Ground Truth나 확정 논문 코퍼스라고 부르지 않음 |
| 수정 후 재승인 필요 | **4** | 1개 업무 경계, 1개 복합 전략, 2개 성과 해석 |
| 원천 문서 열람 보류 | **3** | NIPA PDF 1종을 기반으로 한 서로 다른 3개 사례 |
| 실제 인간 검토자 승인 | **0** | AI만으로 최종 Ground Truth 승인 불가 |

91건 중 **68건**은 Factor/Strategy 라벨이 모두 있으며, **64건**에는 제한적 직접 적용 관계가 기록되어 있다. Factor ABSTAIN **22건**, Strategy ABSTAIN **2건**은 근거 부족에 대한 명시적 검수 결정으로 계속 유지한다. 대응 관계는 통계적 인과효과나 Wald 검증의 근거가 아니다.

## Q01~Q09 별 판정 정책과 관찰 사항

| 코드 | 전수 점검·해석 | 최종 처리 |
|---|---|---|
| Q01 사례 단위 | 98개 고유 사례, source/company/parent 표본 군집 분할 오류 없음. Sun Life 1건은 전사 챗봇에서 직원 1회 활용을 독립 운영 프로세스로 승격한 우려 | 91 잠정 / Sun Life 보류 |
| Q02 실제 운영 | 91건은 공급사/기업 공식 원문의 구체적 운영 기술을 확인; Wortens/IBM Analyze도 **운영 자체는 확인**이나 성과 충돌로 보류 | 91 잠정 / 7 검토 |
| Q03 근거 위치 | URL과 5개 evidence_anchor 모두 기재. **19건의 과거 anchor에 `Same section`/`Same paragraph` 표현이 있어** 최종 동결 전에 절대 섹션/고유 원문 구절로 재작성 필요; 별도 source passage notes는 이번 QA 원장에 보존 | Q03 재현성 잔여 작업 |
| Q04 업무 문제 | 98건 모두 Problem/Task/Context/Implementation 구분, 의미상 타당성은 Q01/02에 연동 | 구조 확인 |
| Q05 Blind Root Cause | 25/98 ABSTAIN. 잠정 적격 91건에서는 22건 ABSTAIN. 라벨 없는 사례를 F값으로 억지 분류하지 않음 | 허용하되 라벨학습 제외 |
| Q06 실제 전략 | 2/98 ABSTAIN 허용. CATRION 실제 핵심이 문서추출+PO 대조+ERP 갱신인데 단일 S4만 기록; 근거 있는 primary/secondary 구조 재검수 | CATRION 보류 |
| Q07 대응 관계 | 68 전체 적용 근거, 4 명시적 관계 ABSTAIN; 잠정 적격에서는 64 대응 관계. 쌍이 없다고 강제로 만들지 않음 | 정확한 비인과적 적용 뜻 유지 |
| Q08 성과 | 기존 42 세부 outcome_type을 QA sidecar 5대 분류로 정규화. 측정·예상·공동 KPI·캠페인 KPI 출처 한정. Worten·IBM Analyze 수치 모호성 확인 | 2건 보류 |
| Q09 추적성 | 원본 계보, 67 표본군집. 동일 기업/URL/원부모 교차 분할 0건. Pilot/PoC 별도 원장 보존 | 구조 확인 |

### 검수 중 새로 확인한 성과 주의사항

- **AXV2H_0009_01 Worten (수정 보류):** Microsoft 원문의 연 75,000건 검색 × 평균 3.5분은 단순 계산 시 **4,375시간**인데 본문은 **연간 11,000시간 검색/절감**을 말한다. 분모, 검색당 기준, 집계 방식이 맞지 않아 **운영 챗봇은 실재**하지만 11,000시간을 측정된 단독 절감으로 확정하지 않는다. [Microsoft](https://www.microsoft.com/en/customers/story/24385-worten-azure-openai)
- **AXV2N_0129 IBM Analyze SW Support (수정 보류):** IBM 본문은 9개월 사용 및 31분/케이스·11% 감소를 기술하지만 각주 ②는 **추정된 24만 로그 관련 케이스에 대한 31분 예상 절감**으로 기재한다. 운영 사실은 인정하되 31분을 독립 실측으로 분류할 수 있을지 정리해야 한다. [IBM](https://www.ibm.com/case-studies/ibm-software-support)
- **AXV2N_0101 Sun Life (수정 보류):** Sun Life Asks는 전사 배포됐지만 특정 분석가 한 명의 감성 분석 프롬프트를 **별도의 운영 업무가 확립된 사례**라고 보기 부족하다. 업무 단위를 원문에 맞춰 수정하고 재검수하거나 Main에서 제외할 것. [AWS](https://aws.amazon.com/solutions/case-studies/sun-life-case-study/)
- **AXV2N_0102 CATRION (수정 보류):** 실제 매입송장 문서정보 추출, 발주서 대조, ERP 반영이 복합되어 있으므로 현재 S4 단일 라벨의 범위를 다시 정의해야 한다. [Microsoft](https://www.microsoft.com/en/customers/story/24577-catrion-microsoft-power-platform/)

### 원천 파일 접근 보류 3건

- `AXV2P2_0036_01` SuperBin: NIPA 인쇄 20–21쪽, PDF 실제 12페이지
- `AXV2P2_0039_01` Mathpresso: NIPA 인쇄 44–45쪽, PDF 실제 24페이지
- `AXV2P2_0040_01` December & Company: NIPA 인쇄 50–51쪽, PDF 실제 27페이지

과거 Work의 NIPA 다운로드 SHA-256과 추출 기록은 이전 검토로 보존하되, **본 독립 세션의 재대조로는 인정하지 않았다**. 원본 PDF 재열람 뒤 사례별 운영/AI 요소/KPI 범위를 검증해야 한다.

## 잠정 적격에 관한 중요한 제한

1. 91건 중 **19건**의 구형 원본 evidence_anchor가 상대 참조 형태다. 독립 검토용 `primary_source_passage_anchor` 설명을 추가했지만, 최종 연구 동결 전에 **해당 실제 출처의 제목·고유 문장·검증자·확인 일시**를 규칙적으로 재기록해야 한다.
2. `MEASURED` 상위 분류에는 **공급사·기업이 관찰했다고 보고한 사용량/모델 성능**도 있으므로, 객관적인 제3자 감사 수치라 주장할 수 없다. 별도 `reported_by`, `metric_kind`, `outcome_attribution`를 강화해야 한다.
3. 91건은 독립 통계 표본이 아니다. 67개 `sampling_group_id` 단위 분할로 유출을 방지하고, 조건별 유효 표본수를 보고해야 한다.
4. 선행 `FROZEN_SOURCE_CURATED_AI_ANNOTATED_WITH_ABSTENTIONS`는 **데이터 버전 잠금**을 뜻하며, 해당 검수 91건의 실제 인간 GT 승격을 뜻하지 않는다.

## 실제 저장된 결과물

- `data/v2/qa/independent_source_pass3_2026-10-22.json` — 98건 개별 근거·승인/보류 상태 및 사유.
- `data/v2/qa/final_case_adjudication_table_2026-10-22.csv` — 98건 사례별 표 형식 판정표.
- `data/v2/qa/provisional_source_qualified_91_2026-10-22.json` — 원본 v2.0.0을 건드리지 않는 91건 원천 검증 후보 코퍼스.
- `data/v2/qa/pilot_and_scope_hold_registry_2026-10-22.csv` — 실제 파일럿 5, 운영 미확인 1.
- `scripts/validate_v2_source_adjudication.py` + GitHub Actions — 판정 원장과 후보/보류/원본 일치 검증.

**최종 결정:** 본 검수에 의한 연구용 **원천 검증 잠정 적격 91 / 보류 7 / 인간 최종승인 0**. PR #3 계속 Draft. 남은 7건 수정·원문 확보 및 19개 locator 재작성, 인간 독립 검토 이후에만 최종 동결·논문 Ground Truth를 논의할 것.
