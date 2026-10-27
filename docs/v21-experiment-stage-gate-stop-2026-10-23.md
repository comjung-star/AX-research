# AX v2.1 단계별 재실험 — 1단계 Gate 중단 보고서
**작성일:** 2026-10-23 (Asia/Seoul)
**판정:** `STOP_AT_STAGE_1_GROUND_TRUTH` — 사용자 지시: 특이사항 발생 시 후속 단계 실행을 멈추고 상황보고.

## 1. 실제 확인한 현재 상태

- 고정 연구 코퍼스: `data/v2_1/main_cases_v2_1.json`, **91건** (7건 별도 보류), manifest의 고정 Git blob SHA 유지.
- 10개 개발 질의(`V21D001`–`V21D010`) × 3개 **평가용 초안** 문제관점 × 91건 = **2,730개 관련도 평정 칸**. `data/v2_1/dev_relevance_annotation_sheet_v2_1.csv`의 2,730개 항목 모두 `UNJUDGED`; 빈 `relevance_0_4`, annotator, reviewer, evidence.
- 별도 전략 정답: `data/v2_1/dev_strategy_annotation_sheet_v2_1.csv`의 **10개 전부 `UNJUDGED`**.
- 정책 기준: `data/v2_1/ground_truth_protocol_v2_1.md`는 독립적 Blind Annotator + 별도의 Reviewer의 근거 있는 adjudication을 요구. 평가자는 Query·Perspective·Case의 **Problem/Task/Context**만 보아야 하며 Solution/Outcome/Factor/Strategy, 이전 v1 Gold, 모델 랭킹은 보여주지 않음.
- v1의 100개 `AX0001–AX0100` 중에는 실제 운영 증빙·업무 단위상 부적합한 건이 있었고, v2.1은 일부 업무를 나누거나 교체한 `AXV2...` ID를 사용함. 따라서 이전 3,000개 relevance judgment를 ID만 교체하거나 source lineage만으로 이식할 수 없음.
- `scripts/v21_evaluate.py`는 독립 `ADJUDICATED` 기준 미충족 시 `Ground Truth NOT READY`로 명시적 중단하도록 구현됨. 과거 코드의 125개 통과는 프로그램 정합성이지 v2.1 Recall@K 성능 점수가 아님.

## 2. 중단 결정과 수행 범위

| 단계 | 상태 | 판단 |
|---|---|---|
| Stage 1. Ground Truth 재구축 | **BLOCKED / 미완료** | 2,730 관련도 판단과 10개 Gold Strategy 독립 평정 부재 |
| Stage 2. BM25 기준 성능 재실험 | **NOT STARTED** | 동일 데이터·독립 GT 확보 전 성능 측정 중지 |
| Stage 3. BGE-M3 Dense 기준 성능 | **NOT STARTED** | 재현 가능한 정답집 없는 Recall@K는 부적절 |
| Stage 4. GPT-only 기준 성능 | **NOT STARTED** | 정답 확보 전 GPT가 만든 자기평가 금지 |
| Stage 5. Multi-Perspective RQ1 | **NOT STARTED** | 동일 질의·검색 예산·GT 기준 필요 |
| Stage 6. Multi-view/Gated/Hybrid/QCI | **NOT STARTED** | RQ1 및 GT 기준 확정 이후 실행 |
| Stage 7. Factor/Wald/Evidence Fusion/추천 | **NOT STARTED ON v2.1 GT** | 기존 63 셀 진단(2개만 4셀>=5)은 탐색적이므로 모델추천 정확도 입증 아님 |

이 보고서 생성 및 해당 출처/파일 상태 읽기 이외에 **새 Ground Truth 점수 작성, 베이스라인 모델 실행, 새로운 Recall@K/Accuracy/Strategy Coverage 산출은 하지 않음**. 원본 91건, 기존 v1 실험, 이전 평가표는 수정하지 않음.

## 3. 재개에 필요한 조건과 실험설계

1. **독립 관련성 평정**: 2,730개 평정 칸 각각 0–4점, 판정근거, Annotator ID, 독립 Reviewer ID 및 합의 내용을 채우고 `ADJUDICATED` 상태로 잠금.
2. **전략 Gold**: 별도의 10개 질의-전략 정답 집합을 해결책 근거와 구별해 독립 평정. ABSTAIN을 근거 없이 부정 사례로 취급하지 않음.
3. **GT 검증**: `scripts/v21_evaluate.py`의 gate를 통과하고 최종 manifest/sha를 고정. 적합한 Held-out Test 질의는 기존 Dev 10개를 복사하지 않고 평가 전 독립 작성/동결.
4. **실험 재개**: 동일 91건·같은 질의/검색예산·같은 BGE-M3 백본으로 BM25, Single Dense, GPT-only, Multi-Perspective Dense, 후속 Multi-view/Hybrid/QCI 및 근거 기반 Strategy 모델 단계적 비교; branch 정보를 합치거나 RRF를 제안모델에 재도입하지 않음.
5. **주요 결과보존**: 원시 랭킹, 모델·프롬프트 버전, 모든 case/source evidence, K/반복횟수/seed, query-level Recall/Perspective Coverage, 통계와 오판/유출 예시, 보류·해석 제한.

**결론:** 사용자 요청대로 첫 번째 실험 전제조건이 충족되지 않았으므로 단계 1에서 중단했고, 후속 모델의 성능 숫자를 만들어내지 않았다. 이것은 데이터셋 v2.1의 실패가 아니라 **새 코퍼스 기준의 독립 평가 기준이 아직 만들어지지 않은 연구 설계상 Gate**다.
