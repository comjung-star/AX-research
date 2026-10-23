# AX 연구 v2.3 — Stage 1~4 전체 개발 실험 종합보고서
실험일 **2026-10-23** | 상태 **STAGE_1_TO_4_DEV_EXECUTED_AND_ARCHIVED**  
기준 코퍼스: `release/ax-v2.3-frozen-20261023`(84개 업무 사례)  
평가 기준: `release/ax-v2.3-dev-silver-gt-20261023`(10개 개발질문 × 3개 참조관점 × 84사례 = 2,520개 LLM 3회 중앙값 평가)  
실행 GitHub Actions: https://github.com/comjung-star/AX-research/actions/runs/39952604227 (**success**)

## 요약 판정
- Stage 1~4: 실제 **전부 실행 완료**, 각 단계별 원자료/설정/분석보고서 저장.
- **성능 관점의 결론:** 현재 Dev 실험에서는 제안하는 다중 관점 Dense/여러 검색 고도화가 단일 Dense 및 GPT-only를 일관되게 능가하지 못함.
- **통계의 결론:** Factor 11 × Strategy 7 = 77 조합 중 3개만 사전 Wald 최소 2×2 셀 5건 기준을 충족. 다중 검정 BH 보정 후 유의한 조합 **0개**.
- **추천의 결론:** 근거 추적형 LLM은 제한된 추천에서 높은 Strategy Precision을 보였으나 Strategy Recall은 단순 사례 빈도 방식보다 낮음. Wald 근거의 추가 기여가 확인되지 않음.
- **학술 해석:** 모두 **개발용 AI 관련도 기준**으로 얻은 탐색적 성능이며, 독립 Test/인간 확정 Gold나 전략 인과관계 입증이 아니다. 결과가 불리하다고 기존 데이터셋/라벨을 바꾸지 않음.

## Stage 1 — 비교 검색
고정 조건: 84개 사례 Problem/Task/Context만 검색 입력; BM25는 Kiwi 형태소, Dense는 `BAAI/bge-m3`, LLM은 `gpt-6-luna`. GPT-only와 MP는 질문당 3회 반복(개별 30회). LLM 생성 관점은 평가용 사전 참조 관점을 보지 않음. 검색 결과 K=5/10/20, 아래는 **K=10**.

| 방식 | Recall@10 | Perspective Coverage@10 | Strategy Coverage@10* |
|---|---:|---:|---:|
| GPT-only | **0.7235** | 0.9667 | 0.8600 |
| Single Dense | 0.5332 | **1.0000** | **0.8667** |
| Multi-Perspective Dense | 0.4530 | 0.9278 | 0.8383 |
| Multi-Perspective BM25 | 0.2470 | 0.6833 | 0.7183 |
| Single BM25 | 0.2378 | 0.6500 | 0.6433 |

- Multi-Perspective Dense - Single Dense의 평균 Recall@10 차이: **-0.0802**.
- 10개 질문별: MP Dense 개선 **3**, 하락 **5**, 거의 동률 **2**. 반복 3회를 독립 질문 30개로 해석하지 않음.
- **판정:** 다중 관점의 보편적 우월성 **미입증**. GPT-only 비교군이 가장 높은 Recall@10.
- 최초 실행은 GPT-only가 존재하지 않는 사례 ID를 생성해 자동검사에서 실패(https://github.com/comjung-star/AX-research/actions/runs/39950487263). 입력 코퍼스를 바꾸거나 가짜 ID를 다른 사례로 치환하지 않고, Pydantic 동적 enum으로 **84개 허용 ID만 출력**하도록 제약해 재실행함. 최종 성공한 실행만 수치에 포함.
- 원본: [Stage1 상세](../experiments/v23_dev/stage1/DEV_RESULT_ANALYSIS.md), `stage1/rankings_top20.csv`, `stage1/metrics_by_query.csv`, `stage1/generated_runtime_perspectives.json`, `stage1/branch_rankings.csv`, `stage1/fixed_bge_m3_embeddings.npz`.

## Stage 2 — 검색 구조 구성요소 대조
Stage 1의 동일 생성관점을 재사용해 LLM 변동을 통제. 학습형 gate/MLP는 질문별 Leave-One-Query-Out(9개 Dev 질의 학습 / 남은 질의 평가). MLP는 CPU 재현성을 위해 BGE 임베딩에 시드 42 고정 랜덤 사영 48차원을 거친 후 `[q,c,q*c,|q-c|]`를 사용함(기존 v1 전체 차원 모델 그대로가 아니라 **v2.3 구현상 축소 투영**).

| 세부 구현 | Recall@10 | Perspective Coverage@10 | 판정 |
|---|---:|---:|---|
| 2-1 Multi-view Equal | 0.4240 | 0.8222 | MP Dense 대비 개선 없음 |
| 2-2 Learned Gated Fusion (LOQO) | 0.3190 | 0.7389 | Equal보다 낮음 |
| 2-4 같은 후보 RRF 참고순위 | 0.3866 | 0.8444 | MLP 공정 비교군 |
| 2-4 Query-Case MLP (LOQO) | 0.2459 | 0.6056 | 같은 후보 RRF보다 낮음 |

**2-3 Hybrid 후보 풀:** 관점당 동등한 검색 슬롯 20개를 유지하고 Dense-only 20개 vs Dense 10+BM25 10으로 비교. 질문×반복 **30회에서 후보 Recall 평균 차이 -0.1066**, Hybrid가 더 나은 회차 **0**, 더 나쁜 회차 **18**, 동률 **12**. Hybrid가 새로 얻은 관련 사례 카운트 합 **13**, 잃은 관련 사례 카운트 합 **53**(회차별 합으로 독립 사례 개수 아님). 서로 다른 관점의 후보 중복으로 최종 고유 후보 수도 달라질 수 있음.
- **판정:** v2.3에서 이 버전의 Equal/Gate/50:50 Hybrid/MLP 조합을 성능 향상 성공으로 채택하지 않음. 모델 실패를 숨기지 않고 다음 구조 설계의 근거로 남김.
- 원본: [Stage2 상세](../experiments/v23_dev/stage2/DEV_RESULT_ANALYSIS.md), `stage2/summary.csv`, `candidate_union_metrics.csv`, `leave_one_query_out_folds.csv`, `rankings_top20.csv`.

## Stage 3 — Factor/Wald 근거 연결
- 사례 84개, 원인 11종, 전략 7종, **77개 2×2 교차표**.
- 사전 최소 셀 수 5건을 만족하여 Wald 가능: **3개**; 나머지 **74개 SPARSE_ABSTAIN**.
- 3개 가능한 조합:
  1. F01–S3: OR 2.40, p 0.0992, BH q 1.000
  2. F01–S6: OR 2.52, p 0.1352, BH q 1.000
  3. F08–S6: OR 5.90, p 0.00721, **BH q 0.555** (보정 후 유의하지 않음)
- 다중검정을 통과한 유의 결과 **0개**. 유의하지 않은 OR을 확정적 추천 효과로 표현하지 않음.
- 10질문 × 3반복 × 검색방법 2개 × Top-10 = **600건**의 고유 랭킹 위치를 추적해 **653개** 사례→Factor→Strategy 연결 행과 공개 출처 URL을 기록. 이 중 **472개 연결 행에서 Wald 근거 표본 부족**으로 통계적 판단 보류.
- **판정:** 출처/원인/전략 **추적성은 구현·검증**, Wald 기반 추천 가중치의 통계적 근거는 현 표본에서 미확보.
- 원본: [Stage3 상세](../experiments/v23_dev/stage3/DEV_RESULT_ANALYSIS.md), `stage3/factor_strategy_wald_77_pairs.csv`, `source_factor_strategy_trace.csv`.

## Stage 4 — 근거 통합 및 AX Strategy 추천
입력: 해당 질문의 Stage2 같은 후보 RRF Top-10 결과와 해당 사례의 공개 출처, 사전 Factor/Strategy, Stage3 Wald의 해석 가능/불가 판단. LLM 추천에 개발용 관련도 점수나 정답 Strategy Set은 전달하지 않음. 10질문 × 3반복 = **30회** 실제 LLM 추천 수행; 93개 추천–사례 근거 링크 검증.

| 방식 | Strategy Recall@3 | Strategy Precision@3 |
|---|---:|---:|
| 단순 검색사례 전략 빈도 | **0.6183** | 0.6556 |
| Wald-safe Evidence Fusion | **0.6183** | 0.6556 |
| 근거 기반 LLM 전략 추천 | 0.5450 | **0.9778** |

- **Wald-safe Fusion vs 빈도**: 완전히 동일한 수치. 사전 규칙상 양의 OR 및 BH q<0.05인 검증 근거만 추가 가중하는데, 해당 근거가 하나도 없기 때문에 성능이 같음. **Wald가 추천을 개선했다고 주장하지 않음**.
- **LLM**: 상대적으로 적은 전략을 선택해 Precision은 높지만 Recall은 낮아짐. 두 지표를 함께 해석해야 함. 출력 전략은 실제 검색 사례에서 사용한 전략과 연결되며 출처를 남김.
- Strategy 평가 기준 자체가 **AI 관련도 3점 이상인 기업 사례들의 사전 Strategy 라벨 합집합**이므로 추천과 평가 사이의 구조적 연관성이 존재함. 0.9778을 독립적인 AX 전략 타당성 정확도 또는 인간 검증 Precision이라고 주장하면 안 됨.
- **판정:** Stage4 추천 기능·근거추적 API 실행 **완료**. 정확도 개선, Wald 기여, 실제 도입 적합성 및 일반화 성능은 **미입증**.
- 원본: [Stage4 상세](../experiments/v23_dev/stage4/DEV_RESULT_ANALYSIS.md), `stage4/final_strategy_recommendations.csv`, `full_llm_answers.json`, `recommendation_case_evidence_trace.csv`, `summary.csv`.

## 공통 실행·검증 및 연구 조건
1. 실제 GitHub Actions 전체 성공: [run #39952604227](https://github.com/comjung-star/AX-research/actions/runs/39952604227); 각 Stage 저장 커밋을 Git 이력에 기록. 원본 `data/v2_3` 동결 데이터셋 및 AI 평가자료는 변경하지 않음.
2. v2.3 라벨은 LLM 독립 채점 3회 중앙값으로 만든 **개발용 평가 기준**. 이전 사용자 요청에 따라 'Ground Truth 평가자료'라고 대화할 수 있으나, 논문에는 LLM 기반으로 생성되었음을 명시.
3. **평가단위:** 10개 고유 문제. 반복 3회를 독립 질문 30개로 간주하거나 통계적 유의성의 근거로 사용하지 않음.
4. K=5/10/20을 모두 측정, 위 본문에는 공정한 비교를 위해 K=10 또는 @3 위주로 요약하고 전체 행은 CSV에 보관.
5. **최종 Held-out Test 실험은 실시하지 않았음.** 개발 질문과 코퍼스 선정에 편향이 있으므로 논문의 최종 모델 개선 주장 전 별도 테스트가 필요.
6. Stage 2의 축소 MLP·학습 방식 및 Stage4의 Wald-safe Evidence Fusion은 이번 v2.3 **재실험용 구현 결정**이다. 교수 제안 모든 하이퍼파라미터와 구조의 정식 최종안이 검증됐다고 오인하면 안 됨.
7. 모든 부정적/기대와 다른 결과를 보존했다. 추가 튜닝이나 데이터 선정을 통해 보이는 결과를 바꾸지 않음.

## 실무 최종 판정
**Stage 1~4 실행 및 기록 업무: 완료.** 논문 가설 중 다중관점 검색·고도화의 일관된 우수성 및 Wald 근거 결합의 증분 효과는 **이 개발 실험으로 입증되지 않았음**. 후속 단계에서는 성능이 좋은 단일 Dense와 GPT-only를 반드시 비교군으로 유지하고, 별도 독립 Test 설계와 실패원인 분석을 우선 고려해야 한다.
