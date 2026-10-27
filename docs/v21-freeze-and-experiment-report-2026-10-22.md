# AX 연구 v2.1 — 최종 코퍼스 고정·후속 실험 이관 종합 보고서

**기준일:** 2026-10-22  
**진행 의사결정:** 연구자는 Q01~Q09 원천 검수의 잠정 적격 91건을 연구용 데이터셋으로 고정하며, 추가적인 후보 사례 보충·7건 재검토를 요구하지 않음. GT/모델 실험 관련 후속 작업은 별도 질문 없이 기존 설계를 유지해 진행.

## Executive Summary

1. **AX Dataset v2.1.0 연구 코퍼스 고정 — 완료.** 91건 JSON·CSV, 소스 QA 출처 이력, 7건 제외 원장, Git blob SHA를 저장. 기존 v2.0.0(98건)과 v1 및 과거 Dev 실험 **무수정**.
2. **근거 추적 — 완료.** 91건에 대해 Problem/Task/Context/Implementation, 실제 운영 근거, 원문 URL, 성과 한정, 기존 AI Blind RCA/Strategy 검토 이력을 csv에 정리. 검증된 `F–S` 직접 적용 경로 64건 분리. 원래 데이터에 남아 있는 상대 locator 19건은 한계로 공개.
3. **데이터 라벨 분포 — 완료.** 63 source/organization/parent 군집, Root Cause 명시적 ABSTAIN 22, Strategy ABSTAIN 2, 모두 분류된 사례 68건, 근거 있는 비인과 적용 링크 64건. 스스로 만든 새 `Ground Truth`로 승격하지 않음.
4. **Wald/F–S 오프라인 진단 — 수행.** 두 라벨이 있는 **n=68**에서 9개 F×7개 S = 63 교차표 계산. 일반적인 4셀 모두 5 이상 요건을 충족한 조합은 **2/63**뿐. `F01↔S3` (a,b,c,d=8,12,12,36; 조잡 OR=2.00), `F01↔S6` (5,15,7,41; 조잡 OR≈1.95). **나머지 61/63은 희소성 기준 미달.** 한 회사/출처에서 여러 사례가 나오는 편의표본이므로 클러스터 보정된 추론이나 통계적 유의성·인과성을 주장하지 않는다. 이 진단은 **추천의 성능을 입증하지 않는다.**
5. **v2.1 Dev 질의/GT 표 준비 — 완료, 정답 평정은 미완료.** v1에서 사용하던 **질의 문장** 10개만 개발용으로 이월, v2.1 Case ID 기준 10×3 Draft Perspective×91 = **2,730**개의 독립 관련도 평정 칸을 `UNJUDGED`로 신규 생성. v1의 3,000개 관련도 점수나 정답 Case ID는 신규 데이터셋에 재사용하지 않음. 별도 Gold Strategy 10개 항목도 `UNJUDGED`. 이 GT가 채워지기 전에는 Recall@K, Perspective Coverage, Strategy Coverage 성능을 새 코퍼스의 실험 결과라고 발표하지 않는다.
6. **v2.1 검색/전략 근거 추적 진단 — 구현·단위 테스트.** Problem/Task/Context만 검색 입력으로 사용하고 solution/outcome/GT 필드 유출 금지. 단일 질의와 가상의 분기 두 개를 사용하는 *wiring smoke* 검증, per-perspective 결과/후보 합집합/64개의 검증된 적용 근거를 출처 링크와 함께 보존. `char_ngram`은 모델 비교용이 **아닌** 의존성 없는 wiring 검증기. 연구원본과 맞는 BM25(Kiwi), BAAI/bge-m3 Dense는 기존 모듈과 연결 가능하나 여기서 실제 새 코퍼스 성능을 실측했다고 주장하지 않는다. **RRF로 분기를 강제 통합하지 않음.**
7. **Ground Truth 무결성 가드 — 구현·검증.** 모든 2,730개 관련도 항목이 `ADJUDICATED`, 0–4점, 독립 annotator/reviewer·근거를 갖추기 전에는 평가 지표를 계산하지 않고 명시적으로 오류를 발생시키게 함. v1 Gold ID를 새 v2.1 사례 ID로 간주하는 실수를 차단함.

## 버전 기록과 검증 근거

| 항목 | 근거 |
|---|---|
| 91건 최종 연구 코퍼스 | `data/v2_1/main_cases_v2_1.json`, `main_cases_v2_1.csv` |
| 데이터 무결성/원천 Git blob SHA | `data/v2_1/release_manifest_v2_1.json` |
| 91건 문제·운영·성과 문단별 근거 | `data/v2_1/source_evidence_index_v2_1.csv` |
| 64개 factor–strategy 근거 및 세션 식별자 | `data/v2_1/factor_strategy_evidence_v2_1.csv` |
| 보류·제외 7건 및 이유 | `data/v2/qa/independent_source_pass3_2026-10-22.json` |
| 63개 Wald 셀 및 최소 셀 크기 | `experiments/rq3_evidence/results/v21_wald_contingency_2026-10-22.csv` |
| Dev Query 신규 10건 | `data/v2_1/dev_query_candidates_v2_1.json` |
| 관련도 평가 준비 2,730칸 | `data/v2_1/dev_relevance_annotation_sheet_v2_1.csv` |
| Gold Strategy 독립 평가 준비 10칸 | `data/v2_1/dev_strategy_annotation_sheet_v2_1.csv` |
| Frozen 검증 / GT 분리·평가 차단 | `scripts/validate_v21_freeze.py`, `scripts/v21_evaluate.py`, `tests/test_v21_gt_guard.py` |
| v2.1 검색·증거 추적 smoke | `scripts/v21_retrieval_smoke.py`, `tests/test_v21_pipeline.py` |
| 자동 검증 | `.github/workflows/validate-v21.yml` (성공한 실행만 통과로 기록하고 queued/in progress는 통과로 쓰지 않는다) |

## Q08 성과 분류: 원본을 보존한 상위 기준

| 성과 기준 | 91건 |
|---|---:|
| MEASURED (공급사·기업·사용자 보고 운영 수치 포함, 독립 감사 수치 아님) | 48 |
| UNKNOWN (해당 업무 단위의 독립적인 수치 근거가 없거나 성과 미확정) | 38 |
| ESTIMATED (예상·추정) | 3 |
| AGGREGATE (캠페인·제품군 등 통합 효과) | 1 |
| PILOT (운영 체계 내 테스트된 시스템 기술 성능으로서 production business KPI 아님) | 1 |

`PILOT` KPI 1건이 있다고 Main에 PoC 배포를 허용한 것이 아니다. 배포 단계는 전부 `PRODUCTION`으로 따로 검증된 원천 코퍼스이고, **기술 시험 수치와 실제 운영 결과를 구분한 값**이다.

## 방법론과 논문 기술 시 주의사항

- 코퍼스는 편의·목적표집된 기업 운영업무 91건이다. 독립 연구자 검증을 거친 절대적인 사실관계 집합이나 전체 산업에 대한 대표표본은 아니다.
- `F` 라벨은 문제 텍스트만 본 AI Blind RCA, `S` 라벨은 구현된 해결책만 본 AI 분류 결과다. 라벨 오류율은 검증되지 않았고 정확도 값으로 인용하지 않는다.
- 22건 F/2건 S ABSTAIN을 억지 분류하지 않으며 분석에는 각 단계의 유효 표본수 N을 함께 제시한다.
- 독립 검수 승인 수: **인간 Ground Truth = 0**. 사용자 승인한 것은 **코퍼스 선정/버전 동결**이지 인적 적합성 판정이나 모든 성과효과 입증이 아니다.
- `S7_GENERATIVE_CONTENT_CREATION` 사례 4건은 v2.0 라벨 체계를 그대로 이월했다. v1의 S1~S6과 일치하지 않으므로 동일 실험에서 섞어 계산할 때는 **S7 신규 범주**라는 사실을 보고한다. 교수 제안으로 확정된 분류라고 주장하지 않는다.
- v1 100건/Dev GT와 기존 Stage1~3 성능은 **역사적 기준**으로만 남긴다. v2.1 91건에 대한 정확도, 다중관점 개선효과, Strategy Coverage 상승, 신뢰구간, held-out Test 결과와 혼동하면 안 된다.

## 단계별 완료 상태 및 객관적 미완료 이유

| 단계 | 상태 | 완료 가능한 것 / 미완료 사유 |
|---|---|---|
| AX 운영 사례 수집·선정 | **DONE** | 91건 고정, 7건 제외 근거 보존 |
| 데이터 파일·출처·계보 동결 | **DONE** | 버전 2.1.0, Git blob 해시 검증 |
| F/S 주석·직접 연결 증빙 | **DONE(기존 AI 검토 범위)** | 68건 양쪽 라벨, 64 대응, abstention 기록 |
| Wald 희소성 진단 | **DONE(탐색)** | 63표 중 2개 기준 충족; 추론적/인과적 결론 없음 |
| v2.1 검색 인터페이스·진단 | **DONE(코드/스모크)** | 원본 Solution 입력 금지, Evidence 원천 추적 |
| v2.1 정답 GT 및 재평정 | **NOT DONE** | 2,730칸 실제 독립 평정 0; 평가 결과를 본 뒤 만드는 정답 금지 |
| 신규 BGE-M3 및 BM25 비교 | **NOT DONE ON V2.1 GT** | Ground Truth 없으므로 신규 Recall/Coverage 성능 주장 불가; optional backend 코드는 준비 |
| Stage 3-2B/Stage 4 추천모델 효과 입증 | **NOT DONE ON V2.1** | 새 GT, 제한적 Wald 통계, LLM 실행·실험 로그가 필요 |
| 인간 제2평가자 확정 | **NOT DONE** | AI 검수를 인간 서명으로 대체하지 않음 |
| v2.1 Held-out 최종 Test | **NOT DONE** | 현재 10 query는 Dev 재활용이며 Held-out 재사용 불가 |

### 후속 연구 실행 시 기준

외부 검토자가 실제 평가할 수 있게 독립 평정 템플릿을 고정했다. 새 라벨이 채워지면 **모든 방법이 동일한 91건 코퍼스·동일 Dev/held-out 질의·동일 Top-K·동일 Dense 백본**을 사용해야 한다. 런타임의 Perspective는 질의에서 동적으로 생성하며 Draft/Gold Perspective를 런타임 입력에 몰래 제공하지 않는다.

최종 판단: **데이터셋 구축은 종결했고 모델 개발/평가는 이어갈 준비가 되어 있으나, 논문 성능 결과까지 완료한 것처럼 보고하지 않는다.** 별도 확인을 요구하지 않고 구현 가능한 저장소·검증·진단 작업은 완료했으며, 사람의 독립 정답 평정과 실제 모델의 평가 실행은 현재 검증자료로 대체할 수 없는 사항이다.
