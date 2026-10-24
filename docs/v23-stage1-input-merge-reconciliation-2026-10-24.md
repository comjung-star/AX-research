# AX v2.3 · Stage 1 검색 입력 및 결과 결합 재검증 — 교차 기록 점검 (2026-10-24)

> 상태: **기존에 실제 실행·저장된 두 개발용 진단 실험의 교차 점검 및 해석 기록**. 이 문서 자체는 새 임베딩 실행 결과를 주장하지 않는다.
>
> 기준: `release/ax-v2.3-stage1-to4-dev-20261023` (`a3cd87ae5a31e0ee8b2029c166b517fdc4ab71a9`).

## 0. 원본 보존과 실험 실행 증거

- **2026-10-24 사전 등록 + 실행:** `experiment/v23-stage1-input-merge-20261024`, [실제 성공한 Actions run #40062958835](https://github.com/comjung-star/AX-research/actions/runs/40062958835). [프로토콜](../docs/v23-stage1-input-merge-protocol-2026-10-24.md) / [실행 코드](../scripts/v23_stage1_input_merge_diagnostic.py) / [수치 보고서](../experiments/v23_dev/stage1_input_merge_diagnostic/DEV_DIAGNOSTIC_RESULT.md).
- **2026-10-23 독립 실행 기록:** `release/ax-v2.3-stage1-input-fusion-audit-20261023`, [성공한 Actions run #39960201745](https://github.com/comjung-star/AX-research/actions/runs/39960201745), [보고서](https://github.com/comjung-star/AX-research/blob/release/ax-v2.3-stage1-input-fusion-audit-20261023/docs/v23-stage1-input-fusion-diagnostic-2026-10-23.md) / [실행 코드](https://github.com/comjung-star/AX-research/blob/release/ax-v2.3-stage1-input-fusion-audit-20261023/scripts/v23_stage1_input_fusion_audit.py).
- **원본 정확히 동일함을 Git 객체 SHA로 확인:** 세 ref(기준·10/23 진단·10/24 진단)의 7개 핵심 파일 blob SHA가 일치함.
  - `main_cases_v2_3.json`: `1705888f3338b219d3715fe4422641865c3075e2`
  - `dev_query_candidates_v2_3.json`: `952c6305172f17e93237b9ca49b6d0120d85e727`
  - `silver_dev_qrels_2520.csv`: `9cdf60dc6f6da7bb5c3950f8d337f12ccf02df91`
  - `generated_runtime_perspectives.json`: `0bca50f107a9d66147dcf05b1d3a933fe857402a`
  - `fixed_bge_m3_embeddings.npz`: `bbc97ac5af4906616c3fffd500c9cf385daba73a`
  - `rankings_top20.csv`: `08b71c2a1c6e9b9ad4e658bbfdc5c47844555e92`
  - `branch_rankings.csv`: `958e5e325f6d571af02e149fdb8edb739186fb34`
- 84사례, Dev 10문제, LLM 3회 평가 중앙값 2,520개, Stage 1에서 생성한 97관점, BGE-M3, 평가 임계값 3점 이상, K=5/10/20 및 3회 반복 조건 유지.
- 실험 스크립트들은 원본 `title_only + round_robin`의 관점별 84개 전체 정렬, 30개 Top20 출력을 재현한다. 10/24의 현재 인코더와 기존 제목 벡터 최소 코사인은 0.99999970으로 보고됐다.
- 기존 Stage 1–4 결과, 원본 데이터셋, 관련도 표, 교수 제안 아키텍처는 이 기록을 위해 수정하지 않음.

## 1. 검색 입력 검증 — 기존 Branch-balanced 고정

**우선 비교할 결과:** 10/24에 실행된 사전 등록 실험. 30회 관측치를 독립 표본으로 부풀리지 않고, 문제 10개 각각 3회 평균을 구한 뒤 문제 평균으로 집계함.

| 검색 입력 | Recall@10 | 원래 45.30% 대비 | Perspective Coverage@10 |
|---|---:|---:|---:|
| 관점 제목만 (`title_only`) | **0.4530** | 기준 | 0.9278 |
| 관점 제목 + 설명 (`title_description`) | **0.4445** | **-0.85%p** | 0.9167 |
| 원문 업무문제 + 제목 + 설명 (`query_title_description`) | **0.4766** | **+2.37%p** | 0.9889 |
| 비교 기준: Single Dense (기존 Stage 1, 재실행 아님) | **0.5332** | +8.02%p | 1.0000 |

- 제목+설명: 질문별 개선 3 / 하락 4 / 동률 3. 기준 대비 짝지은 질문단위 bootstrap 95% 구간 **[-0.0892, +0.0743]**.
- 원문+제목+설명: 개선 4 / 하락 5 / 동률 1. 기준 대비 **[-0.0687, +0.1368]**.
- 해석: 설명 추가 효과는 일관되지 않으며, 원문 맥락을 다시 넣은 효과도 일부 개선된 개발용 관찰에 불과하다. 95% 구간들은 0을 포함한다.

## 2. 결과 결합 검증 — 검색 입력을 고정

| 검색 입력 | 기존 분기 균등 round-robin | 비교용 RRF60 | RRF − 기존 |
|---|---:|---:|---:|
| 관점 제목만 | 0.4530 | **0.4787** | **+2.57%p** |
| 제목+설명 | 0.4445 | **0.4772** | **+3.27%p** |
| 원문+제목+설명 | **0.4766** | 0.4666 | **-1.00%p** |

- 원래 입력인 제목만에서 결합 방법만 바꾼 질문별 결과: 개선 **5**, 하락 **4**, 동률 **1**; 질문단위 paired bootstrap 95% 구간 **[-0.0231, +0.0790]**.
- 분기 균등 결합은 관점별 후보를 순서대로 교대 선택하고 중복을 제거한다. RRF60은 관점별 순위의 `1/(60+rank)` 합계로 전체 사례를 정렬한다. 후보 코퍼스 84개 접근권은 같고, RRF는 진단 비교군일 뿐이다.
- **아키텍처 제약:** `AGENTS.md`에 따라 RRF/Weighted RRF를 교수님 제안 모델로 채택해서는 안 되며, 관점별 Branch 식별·증거는 제안 모델에서 보존해야 한다. 현재 실험은 설계 대체 승인이 아니다.
- 결론: 결합 변경만으로 단일 Dense의 0.5332에 도달하지 못하며, 고정된 입력에 따라 RRF의 이익이 달라진다.

## 3. 특이사항 — 기존 두 결과표의 숫자가 다른 이유

**이 현상은 '같은 검색 텍스트·같은 조건에서 서로 다른 결과'가 아니다.** 두 실행은 원본 데이터/임베딩/관점은 동일하지만, 신규 비교 입력의 **문자열 템플릿이 달랐다.**

| 항목 | 2026-10-23 진단 | 2026-10-24 진단 |
|---|---|---|
| 제목만 | 원래 제목 벡터 그대로 | 원래 제목 벡터 그대로 |
| 제목+설명 | `[PERSPECTIVE] {title}\n[DESCRIPTION] {description}` (`strip()`) | `{title}\n{description}` |
| 원문+제목+설명 | `[BUSINESS PROBLEM] ...\n[PERSPECTIVE] ...\n[DESCRIPTION] ...` | `업무 문제: ...\n문제 관점: ...\n관점 설명: ...` |
| 제목만+Round-robin Recall@10 | 0.4530 | 0.4530 |
| 제목만+RRF60 Recall@10 | 0.4787 | 0.4787 |
| 제목+설명+Round-robin Recall@10 | **0.4295** | **0.4445** |
| 원문+제목+설명+Round-robin Recall@10 | **0.5401** | **0.4766** |

- 따라서 **10/23의 54.01%와 10/24의 47.66%는 같은 검색 입력의 재현 실패가 아니라 서로 다른 문자열 실험에서 산출된 수치**다. 변수명만 보고 한 표로 묶거나 한쪽을 재현 실패·오류로 단정하면 안 된다.
- 검색 문장 형식이 바뀐 사실이 **비교 조건 불일치의 확인된 원인**이다. 그 자체가 성능 차이 전부의 인과적 설명임을 증명한 것은 아니다. 인코딩 batch 크기/실행 환경 영향 등을 분리한 전용 실험도 아직 없다.
- 실험 결과 해석에서는 각각의 템플릿을 명시하고, 사후 최고 성능 0.5401을 대표 성능으로 골라 주장하지 않는다. 10/23 실험은 **문자열 템플릿 민감도**를 보여주는 추가 증거로 보관한다.

## 4. 중복도와 저성능의 원인 후보

10/24 결과 파일 `branch_overlap_diagnostics.csv`의 30개 문제×반복별 관점 간 Top10 **Jaccard 평균**을 다시 집계하면 다음과 같다.

| 입력 | 관점 간 평균 Top10 Jaccard | 평균 분기 검색문자 길이 |
|---|---:|---:|
| 제목만 | 0.214 | 14.57 |
| 제목+설명 | 0.325 | 70.24 |
| 원문+제목+설명 | 0.584 | 192.44 |

- 제목만 쓰면 원래 문제의 맥락이 축약되어 일부 관련 사례를 놓칠 수 있다. 다만 이 실험만으로 모든 검색 하락의 원인이 제목 축약이라고 단정할 수 없다.
- 동일한 원문을 매 분기에 붙이면 분기 간 상위 검색결과 중복이 크게 늘어난다. 원문 추가가 Recall을 일부 올려도 관점별 **고유 기여**를 증명하지는 못한다.
- Branch-balanced의 상위 10 슬롯 배분과 RRF의 반복 노출 우대는 서로 다른 후보를 밀어내거나 올릴 수 있다. 실제로 입력에 따라 우열이 바뀌므로 **고정적 합성 방식만 원인**이라고 말할 수 없다.
- 핵심 연구가설(다중 관점이 단일 Dense보다 일관되게 좋다는 주장)은 10/24 개발용 실험에서 **여전히 미입증**. GPT-only 0.7235도 기존 비교군으로 유지해야 함.

## 5. 결론 및 해결 방안

1. **이번 요청 2개 비교의 현 상태:** 10/24 GitHub Actions 성공 결과와 정량 자료가 기존에 이미 존재한다. 이 문서는 기준 릴리스 대조·1번 검색 입력 → 2번 결과 결합 순서의 해석·10/23 기록 간 수치 차이의 원인을 추가로 정리한다. 별도로 신경망을 재실행했다고 주장하지 않는다.
2. **현재 확정 가능한 내용:** 같은 원본에서 문자열 템플릿이 달라지면 결과가 달라질 수 있고, 결합 변경 이익은 입력 조건에 의존한다. 10/24 최고 조합도 Single Dense에 못 미쳤으며 모든 주요 질문단위 변화 구간이 0을 포함했다.
3. **필요한 해결 검증:** 검색 입력 템플릿의 구분표시/언어/공백을 독립 요인으로 **사전 등록**하고 같은 인코더 버전·배치 조건에서 재실험. 그 다음 기준을 고정해 Branch 고유 관련 사례 신규 회수·중복·손실을 질문별로 분석. 최종적으로 별도 Held-out Test에서 비교한다.
4. **운영 원칙:** 데이터셋/평가자료 수정 금지, 기존 Stage 1~4 수치 불변, 부정적 결과도 모두 보존, 교수님 아키텍처의 관점 분기 보존 유지. 비교 결과만으로 새 결합을 최종안으로 승인하지 않음.

**원자료:** [2026-10-24 6조합 실행 결과](../experiments/v23_dev/stage1_input_merge_diagnostic/summary_18_combinations.csv), [질문별 3회 평균](../experiments/v23_dev/stage1_input_merge_diagnostic/query_level_metrics.csv), [질문단위 구간](../experiments/v23_dev/stage1_input_merge_diagnostic/paired_query_deltas_vs_original.csv), [분기 중복도](../experiments/v23_dev/stage1_input_merge_diagnostic/branch_overlap_diagnostics.csv).
