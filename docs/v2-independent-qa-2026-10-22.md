# AX Dataset v2.0.0 — 신규 독립 Q01~Q09 검수 보고 (2026-10-22)

> **판정: PROVISIONAL AI QA 14건 통과 / REVIEW 84건, 인간 독립 검토 최종 승인 0건.** v2.0.0의 `FROZEN_SOURCE_CURATED_AI_ANNOTATED_WITH_ABSTENTIONS`라는 기술적 버전 표시는 학술적인 Ground Truth 검수 승인이 아니다.

## 감사 범위와 재현 기준

- 입력: `data/v2/main_cases_v2.json`, 고정 출발 커밋 `9121c0e93b082207187f947f9507b1f25352e312`, 원본 사례 98건.
- **98건 전체**: 필수 필드, 업무 단위, 출처·근거 anchor 존재, 블라인드 요인/전략 검토 기록, 적용관계, 성과 한정, 계보·표본 군집 정합성 검사. 상세 사례별 판정은 `data/v2/qa/independent_q01_q09_2026-10-22.json` 및 `case_status_2026-10-22.csv`.
- 공개 원문 URL **72종 중 71종은 웹에서 열람**, 국가기관 NIPA 첨부 PDF 1종은 이번 검수 도구로 열람 실패. 그러나 **웹페이지가 열렸다는 사실은 각 주장 내용까지 독립 검증됐다는 뜻이 아니다**. 개별 문제/실행/배포/성과를 독립적으로 문단 대조한 사례는 JSON의 `source_independent_note`에만 기재(25건).
- 별도 2차 AI 검수는 선행 Work의 AI 주석과 다르지만, **인간 평가자·외부 동료검수자의 승인은 아니다**. 인간 승인 필드는 절대 true로 바꾸지 않았다.
- v1 원본, 실험결과, 기존 v2.0.0 JSON/CSV/manifest/해시는 변경하지 않았다. 이번 결과는 별도 sidecar QA 데이터다.

## 검수 결과

| 검수 기준 | 잠정 PASS | REVIEW | FAIL |
|---|---:|---:|---:|
| Q01 독립 업무 경계 | 97 | 1 | 0 |
| Q02 실제 운영 증거 | 25 | 73 | 0 |
| Q03 원천 근거 및 위치 | 24 | 74 | 0 |
| Q04 업무 문제 정의 | 98 | 0 | 0 |
| Q05 Blind Root Cause | 73 | 25 | 0 |
| Q06 Solution Strategy | 95 | 3 | 0 |
| Q07 근거 관계(무리한 결합 금지) | 98 | 0 | 0 |
| Q08 성과 분류 및 귀속 | 98 | 0 | 0 |
| Q09 계보·중복·그룹 | 98 | 0 | 0 |

**주의:** Q07 PASS 98은 *무조건 인과관계 98개*가 아니라, 68건의 제한적 적용 근거 연결과 나머지 무관계/보류의 **정직한 처리**가 구조적으로 적합하다는 뜻이다. 72건이 두 라벨을 갖고, 68건에 제한적 `SUPPORTED_APPLICABILITY`가 기록되며 4건은 관계 검토 후 보류다. Q08 PASS 98도 보고된 수치가 실제 측정되었다고 독립 입증하는 것이 아니라 **성과 유형을 별도 sidecar에 표준 분류**했다는 의미다.

### 표준 성과유형 부여

| 상위 유형 | 건수 |
|---|---:|
| UNKNOWN | 40 |
| MEASURED | 53 |
| ESTIMATED | 3 |
| AGGREGATE | 1 |
| PILOT | 1 |

`MEASURED`는 기업·공급사·사용자가 *운영에서 관찰했다고 보고한* 수치, 서비스 사용량 또는 모델 성능까지 포함하며, 독립 측정·감사나 AI만의 인과효과가 입증됐다는 뜻이 아니다. `PILOT` 1건은 실제 운영되는 로봇의 *시스템 테스트 지표*가 임팩트 지표가 아님을 표시한 것이지, 해당 Main 사례 자체를 PoC로 재분류한 것이 아니다. 더 정확한 표기를 위해 후속 데이터 버전에 `metric_kind`, `measurement_source`, `impact_attribution` 필드를 병행하는 것이 바람직하다.

## 사례별 처리 현황

- **잠정 AI QA 통과 14건** (인간 검토 전): `AXV2C_0006_01`, `AXV2C_0093_01`, `AXV2C_0093_02`, `AXV2N_0105`, `AXV2N_0106`, `AXV2N_0118`, `AXV2N_0120`, `AXV2N_0121`, `AXV2N_0126`, `AXV2P2_0010_01`, `AXV2P2_0035_01`, `AXV2P2_0065_01`, `AXV2P2_0099_01`, `AXV2P2_0100_01`.
- **추가 검토 84건**: 전건이 허위·오류라는 뜻이 아니다. 대부분은 작성자 원문 대조가 있었어도 이번 **독립 2차 문단별 대조**가 끝나지 않았기 때문에 REVIEW 처리했다.
- 25건은 Blind Root Cause ABSTAIN, 2건은 Strategy ABSTAIN이며 해당 결과는 강제 보충하지 않았다. CATRION 1건은 구현이 복합적인데 단일 주 전략만 기록되어 Q06 추가 REVIEW다.
- 동일 기업·출처·부모가 서로 다른 `sampling_group_id`로 배정된 구조 오류는 0건. 새 교체 사례에 `parent_v1_case_id=NULL`이 있는 것은 정상 이력이다.

### 중요한 원문 재대조 쟁점

| 사례 ID | 기업 | 쟁점 |
|---|---| 
| AXV2C_0006_02 | Danone | Q07: confirmed strategy does not directly solve the unstructured order-format issue; mapping correctly abstained |
| AXV2C_0074_02 | Cashfree Payments | Q07: webpage summary does not independently prove completion of compliance and risk-check bottleneck |
| AXV2C_0093_02 | Suzhou Universal | Q07: model class S5 addresses scheduling decisions but F05 fragmentation response partly rests on platform orchestration |
| AXV2N_0101 | Sun Life | Q01: one analyst prompting globally deployed chat service does not establish an independent repeatable market-research workflow |
| AXV2N_0102 | CATRION | Q06: S4 mismatch detection does not represent both AI Vision data extraction (S3) and Power Automate end-to-end workflow (S6) |
| AXV2N_0127 | Sandvik / SigmaNEST | Q01: shares Manufacturing Copilot with support case; separate onboarding task evidenced, but deployment and outcome not independent technology |
| AXV2P2_0010_01 | Sandvik / SigmaNEST | Q01: shares Manufacturing Copilot with onboarding case; support outcome separate |
| AXV2P2_0013_01 | Relativity | Q07: disclosure does not directly establish fatigue-consistency mitigation by this implementation |

- **Sun Life `AXV2N_0101`**: AWS 원문은 전사 챗봇 `Sun Life Asks` 운영을 확인하지만, 데이터셋에 따로 설정한 시장 감성 테마 계수 업무는 **한 분석가의 단일 프롬프트 사용담**이다. 반복되는 업무 운영 프로세스인지 증거가 없으므로 Q01 REVIEW. 해결책은 사례 제거 또는 *전사 직원의 사내정보 질의응답 업무*에 맞춘 재작성과 새 블라인드 라벨 검수다. [AWS](https://aws.amazon.com/solutions/case-studies/sun-life-case-study/)
- **CATRION `AXV2N_0102`**: 실제 운영 대상은 학습된 특정 공급자·송장 양식이다. `Azure AI Vision`으로 PDF/스캔 추출, `Power Automate`로 PO 대조·ERP 갱신을 수행한다. 현재 S4 단일 값은 자동화·문서 이해의 적용 기술을 불완전하게 표현한다. 단일 업무 사례를 유지하면서 `primary_strategy`와 근거 있는 `secondary_strategy`의 관계를 명시하라. [Microsoft](https://www.microsoft.com/en/customers/story/24577-catrion-microsoft-power-platform/)
- **Sandvik `AXV2N_0127` / `AXV2P2_0010_01`**: 한 Manufacturing Copilot 플랫폼을 *신입 영업 교육*과 *제품 기술지원*에 사용한다. **업무 단위는 분리 가능**하나 시스템 자체가 독립 배포 2건인 것으로 해석하면 안 되고 성과의 작업별 귀속을 확인해야 한다. 같은 표본 군집을 유지한다. [Microsoft](https://www.microsoft.com/en/customers/story/22965-sandvik-azure-open-ai-service)
- **수정 없이 유지할 수 있는 근거 방향**: Suzhou 제조 품질/스케줄 2업무 구분, Morrisons 상품 찾기와 고객 의견 요약 구분, Starling 문의·지출·상담요약 3업무 구분, Lowe's 직원용/고객용 AI 서비스 구분. 단 동일 계열 플랫폼을 통계적으로 독립 관측치로 취급하지 않는다.
- **NIPA**: 3건(`AXV2P2_0036_01`, `AXV2P2_0039_01`, `AXV2P2_0040_01`)의 첨부 PDF를 이번 독립 검수에서는 열람하지 못했다. 이전 Work의 로컬 다운로드·페이지 분석은 과거 입력으로 보존하되 2차 원문 확인으로 간주하지 않았다.

## Pilot/POC 분리

`data/v2/qa/pilot_and_scope_hold_registry_2026-10-22.csv`에 **실제 파일럿 제외 5건**(AX0095, AX0096, AX0062, AX0066, Orion Health)과 **운영 전환 미확인 1건**(AX0088)을 별도 관리한다. 이전 데이터셋의 명백히 운영이 확인되지 않은 파일럿을 Main Dataset에 합산하지 않는다. 이것은 파일럿 전체 모집단의 완전한 구축이 아니라 현재 감사에서 발견한 등록원장이다.

## 최종 승인에 필요한 후속 작업

1. Q02/Q03 아직 REVIEW인 **74개 출처-사례 문단**에 대해 작성자와 독립된 상세 원문 대조, 원문/문단별 식별 가능 locator 갱신(상대 locator 19건 우선) 실시.
2. 문제–구현 상관관계 불일치 4건은 강제 연결하지 않고 원문에 비추어 문제 문장·요인·전략 필요 시 수정, 입력 변경 시 독립 요인/전략 재검수.
3. CATRION 등 복합 구현은 *근거 있는 다중 전략* 주/보조 구조 마련. 요인 25건·전략 2건 ABSTAIN은 보존하되 분류체계 확장이 필요한지 연구설계 측면에서 판단.
4. 성과 상위 유형 정규화를 본체 v2.1 schema에 반영(원본 v2.0.0 보존), 테스트/파일럿/합산/예상과 실제 운영 KPI를 엄격히 구분.
5. 독립 전문가/인간 검토자 승인 전 **최종 FROZEN, 학술 Ground Truth 98/98 PASS 또는 PR 병합 주장 금지**.

**본 보고는 검증된 한계까지 마친 2차 AI 검수 결과다. 98개 전체의 학술적 최종 승인 완료를 뜻하지 않는다.**
