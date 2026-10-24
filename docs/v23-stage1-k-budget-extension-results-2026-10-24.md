# AX v2.3 Stage1 — Final Top-K budget extension and candidate pool diagnostic results

작성일: 2026-10-24

본 문서는 기존 동결된 `release/ax-v2.3-stage1-to4-dev-20261023` Stage 1 결과만을 다시 분석한 **탐색적 Dev 진단**이다. 신규 BGE-M3/LLM 실행, Frozen 84건 코퍼스 수정, AI-Silver 2520개 관련도 수정, Stage1–4 역사적 결과 수정은 전혀 없다.

관련 분석 프로토콜: [K 예산 확장 진단 조건](v23-stage1-k-budget-extension-protocol-2026-10-24.md); [원래 Top10 병합 실험](v23-stage1-branch-merge-diagnostic-results-2026-10-24.md).

## 1. 진단 방법

- `experiments/v23_dev/stage1/rankings_top20.csv`: 원래 Single Dense(질문별 1회), MP Dense(질문별 3회), Top20 순위를 읽고 K=5/10/15/20에서 동일 출력 개수로 비교.
- `experiments/v23_dev/stage1/branch_rankings.csv`: 97개의 동적 생성 branch 각각에서 84개 AX 사례를 전부 순위화한 기록. Branch-balanced가 20개를 선택하는 상황 및 branch별 TopN 후보 합집합 진단에 사용.
- `data/v2_3/ground_truth/silver_dev_qrels_2520.csv`: 질의별 참조 관점 세 개의 Silver 관련도(3 이상) 사례의 합집합이 G. **전략/평가정답은 검색 및 후보 선정에 사용하지 않음.**
- 표의 Recall@K는 질문 10개 각각에 대해 MP 3회 평균을 구한 macro 수치. '발견 37회' 등 건수는 10개×3회 비교한 **출현 횟수 합계**이며 전역적 고유 사례 수가 아니다.
- S(q,K): Single Dense TopK, M(q,r,K): MP Dense TopK. MP만 찾은 Silver 양성 `(M\\S)∩G`; Single만 찾은 Silver 양성 `(S\\M)∩G`.

## 2. K 확장에 따른 동등 출력 예산 비교

| 최종 K | Single Dense Recall | MP Dense Recall | MP-Single (%p) | MP만의 Silver 관련 사례 출현 | Single 관련 사례 누락 출현 |
|---:|---:|---:|---:|---:|---:|
| 5 | 34.50% | 29.84% | -4.66 | 26 | 39 |
| 10 | 53.32% | 45.30% | -8.02 | 19 | 39 |
| 15 | 65.67% | 55.53% | **-10.14** | 24 | 52 |
| 20 | 68.53% | 64.65% | **-3.88** | **37** | 48 |

@5/10/20은 원래 Stage1 결과와 Recall 값이 일치, @15는 이 재분석에서 새로 계산한 보간값.

- 기존 MP Top10에서 Single Top10의 Silver 관련 사례 누락 **39회** 가운데, MP Top15 확장에서 11회, MP Top20 확장에서 **20회**를 재포함함. 즉 16~20위 확장분만으로 **추가 9회** 재포함. 여전히 **19회**는 MP Top20에서도 보이지 않음.
- 매칭 예산에서 @20 MP Recall이 @10보다 +19.35%p 높아졌으나 Single Dense도 @10보다 +15.21%p 높아진다. 따라서 **후보 수를 늘리면 절대 재현율은 증가하지만, 이것이 MP가 Single보다 우수하다는 뜻은 아니다.**
- @15에서는 동일 예산 차이가 오히려 -10.14%p로 확대되었다가 @20에서 -3.88%p로 축소됨. **후보 수를 15로 늘린다고 상대 성능이 자연스럽게 좋아지는 것이 아니다.**
- 동일 예산 @20에서 MP-only Silver-positive 발견 출현 37, Single-only 누락 출현 48. 기존 @10의 19/39와 다른 평가 집합(Single Top20)을 비교한 것으로 두 행의 건수를 같은 고정 분모처럼 해석하지 말 것.

## 3. Branch 후보 합집합: 최종 추천 개수와 분리

각 L개 local 상위 사례를 **97개 생성 관점 중 해당 질문/반복의 2~5개 branch에 대해 합집합**으로 만들었을 때 30회 실행의 후보군 평균:

| 각 관점 local Top-L | 중복제거 후 후보 평균 | 후보군 Silver Recall (macro) | Single Dense Top20 바깥의 새로운 Silver 관련사례 출현 |
|---:|---:|---:|---:|
| 3 | 7.47 | 38.21% | 7 |
| 5 | 11.93 | 50.63% | 19 |
| 10 | **22.13** | **70.85%** | **44** |
| 20 | **39.43** | **85.16%** | **73** |

**동일 예산을 맞춘 결과가 아님.** 관점별 Top10 합집합은 평균 22.13개로 Single Top20 20개보다 크며, local Top20 합집합은 평균 39.43개로 두 배 가까움. 이 수치를 Single Top20보다 뛰어난 모델의 증거로 사용하지 않는다.

이 진단이 보여주는 것은 **관점 분기 내부의 후보 발견과 최종 TopK 선발을 분리할 여지가 충분하다**는 사실이다. 합집합 후보를 실제로 얼마나 정확히 20개→최종 10개로 좁히는지는 **별도 동일 예산 rerank 평가가 필요**하다. 원래 Stage2 구조는 branch별 Top20 후보군을 이용해 gated/interactions와 hybrid candidate union 등을 수행하지만, 기존 Stage3 및 4에서 활용한 Top10 제한이 실제로 사라진 것은 아니다.

## 4. K20 동등 예산 결합법 진단 (프로토콜의 label-blind C1/C2)

원래 MP branch 전체 순위를 고정한 채 Top20만 다시 선정했다. 각 생성 관점에서 최소 한 사례를 우선 할당하며 나머지 20개까지 원래 각 branch local Top20 합집합에서 선택한다. GT/참조 관점 평가 기준은 선정에 주입하지 않는다.

| 선정법 | MP Recall@20 | Single Dense Recall@20 | MP만 찾은 Silver 관련사례 출현 | Single 관련사례 누락 출현 | Coverage@20 |
|---|---:|---:|---:|---:|---:|
| 원래 branch-balanced (B0) | **64.65%** | 68.53% | **37** | 48 | 97.78% |
| C1: 1관점 1개+여러 branch 공통 상위 후보 | 64.12% | 68.53% | 33 | 47 | 97.78% |
| C2: 1관점 1개+branch별 점수 표준화 | **65.41%** | 68.53% | 35 | **45** | 97.78% |

- C1은 지난 Top10 진단에서 Recall 상승(+2.42%p)했지만 **Top20에서는 B0보다 -0.53%p 하락**하여 일반적인 개선 규칙으로 확정할 수 없다.
- C2는 B0보다 +0.76%p 올라갔지만 Single Dense에는 -3.12%p 못 미치고, MP만 찾은 관련 사례 출현은 37→35로 감소. Dev 10개 질문에 대해 의미 있는 우월성을 입증한 것은 아니다.
- 30회 모두 각 방법의 Top20에 중복 ID가 없고 각 branch의 선행 1개 사례 선택 조건을 만족. 당시 저장된 84개×97개 branch를 같은 후보 공간으로 활용했으며 새 쿼리 생성/임베딩 계산은 없음.

## 5. 단계 아키텍처 관점의 제안

사용자가 제안한 `최종 후보 Top20` 확장은 **검색 후보 집합 크기를 늘리는 것**과 **사용자에게 최종 추천 결과 20개를 보여주는 것**으로 나누어야 한다.

우선순위:
1. Stage1 후보군은 branch 별로 유지하고, **20개 내외의 공정하게 선택된 global shortlist**를 별도 산출한다. 원본 Stage1 Top20과 branch local Top10/20 union도 비교군으로 보존.
2. **Stage2: 원래 교수 제안 Gated Fusion / Query–Case Interaction 등을 활용하여 후보 20개를 rerank**, 필요시 최대 20개를 증거 추적으로 전달하고 최종 추천 설명에 쓰이는 유효 사례 Top5/10은 별도 선정한다. 정확한 20→10 단일 경로는 신규 설계/실험이 필요하며 현행 Stage2–4에 이미 end-to-end 적용했다고 표현하면 안 된다.
3. 평가 지표는 `Candidate Recall@20`, `Exclusive/MP-only Relevant Recovery@20`, `Rerank Recall/Precision@10`, Perspective Coverage, 근거 trace 및 Stage4 추천 정확성을 함께 측정. **각 단계의 예산을 명시**, 서로 다른 K/후보 수를 같은 기준으로 우열 평가하지 않음.
4. Stage2/3/4는 기존 10개 Dev Silver를 기준으로 실험했으므로, K20 후보를 그대로 공급할 경우 **후속 모델/LLM의 근거 선택·추천 품질이 자동으로 증가한다고 주장할 수 없다.** 연결 후 별도 평가가 필수.

**현재 결정:** K20 확장은 충분히 시도할 만한 유효한 설계 후보이지만, "MP 최종 추천 20개 고정"을 즉시 공식 아키텍처로 변경하지 않는다. 후보 Pool 20+ 최종 근거 사례 5~10을 분리하는 **계층형 설계**의 검증을 제안한다.

## 6. 한계/변경 관리

- AI-Silver 2520개는 인간 평가 Gold가 아님; 초기 코퍼스가 Dev 탐색에 영향을 받은 편향 있음.
- 같은 10개 Dev 질문을 3회 반복한 수치로 독립 Test 유의성을 주장하지 않음.
- 이 문서는 원래 Stage1–4의 수행결과를 재기록/대체하지 않는 별도 개발 진단 결과다. 새 Stage2–4 실행/효과 검증 완료라고 말하지 않는다.
