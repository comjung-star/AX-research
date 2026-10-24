# AX v2.3 — Candidate Union 이후 Top-M 선정 실험 결과

**작성:** 2026-10-24 · **상태:** 실제 GitHub Actions 재현 실행 성공 · **구분:** 교수님 회신 전 임시 해석을 검증하는 탐색적 개발 실험.

- 실험 프로토콜(실행 전 기록): [v23-full-union-topm-protocol-2026-10-24.md](v23-full-union-topm-protocol-2026-10-24.md).
- 코드: [scripts/v23_full_union_topm.py](../scripts/v23_full_union_topm.py), [scripts/v23_full_union_topm_report.py](../scripts/v23_full_union_topm_report.py)
- 실제 실행: [GitHub Actions 40072060378](https://github.com/comjung-star/AX-research/actions/runs/40072060378) (기본 실험 성공), [GitHub Actions 40072248251](https://github.com/comjung-star/AX-research/actions/runs/40072248251) (관점별 Top-K 평가 포함 최종 실행 성공).
- 고정 원본: `release/ax-v2.3-stage1-to4-dev-20261023`; 기존 84개 사례, 10개 개발 질문×각 3회, GPT로 생성했던 97개 관점, 기존 BGE-M3 임베딩 및 Kiwi-BM25 점수, AI-Silver 2,520개 평가항목. **원본 데이터와 Stage 1–4 결과 불변, GPT/임베딩 모델 신규 호출 없음.**
- 새 결과: `experiments/v23_full_union_topm/` 아래 `summary.json`, `candidate_pool_metrics.csv`, `selected_candidate_provenance.csv`, `perspective_topk_rankings.csv`, `perspective_topk_union_metrics.csv`, `perspective_topk_union_summary.json`, `global_shortlist_diagnostics.csv`, `loqo_training_audit.csv`.

## 1. 검증한 교수님 원안 해석

관점별 **Dense 전체 84개 순위**와 **Sparse 전체 84개 순위**를 합쳐 중복 제거 → 각 사례에 Dense rank / Sparse rank / BM25 score 보존 → 결합 점수 또는 교대 할당으로 관점별 **Top-M** 후보 선정 → 같은 Query–Case Interaction MLP가 후보 관련도 점수화 → **관점별 Top-K** 출력 (전역 Top10은 과거 실험과 비교하는 진단용 결과일 뿐 교수님 원안의 최종 형식이 아님).

**주의:** 사례 저장소 전체가 84개라 두 검색기가 84개씩 전체 순위를 반환하면 합집합 역시 84개다. 따라서 `Top-M`이 84 미만인 이상 후보 제거는 발생한다. **사례 보존 여부는 Top-M 선택 규칙과 M이 결정**한다. 교수님은 구체적인 Top-M 결합 공식/숫자를 제안 그림에 고정하지 않았다. RRF와 교대 선정은 임시 구현이다.

BM25 0점 결과는 실질적인 단어 일치 근거가 없으므로 Sparse 순위의 가산점과 교대 선발에 사용하지 않았다. 동결 sparse branch 8,148개 순위 중 6,701개가 0점이어서 이 처리는 중요하다.

## 2. 1차 결과: 후보 확보 Candidate Recall

질문 10개 각각 3회 실행 평균. 각 M은 **한 관점의 Top-M**을 뜻한다. 각 질문의 생성 관점(2~5개)을 합쳐 중복 제거한 후보군에서 AI-Silver 관련 사례를 찾은 비율이다.

| 관점별 M | Dense 단독 | 전체 합집합→RRF Top-M | 전체 합집합→교대 Top-M |
|---:|---:|---:|---:|
| 10 | **63.32%** | 36.54% | 58.63% |
| 20 | **79.98%** | 56.92% | 74.67% |
| 40 | **92.40%** | 92.06% | 92.06% |
| 60 | 98.91% | **99.22%** | **99.22%** |
| 84 | 100% | 100% | 100% |

- **RRF Top-M 선정은 M=10/20에서 중요 관련 후보를 대량 탈락**시켰다. 예를 들어 M20에서 Dense 후보 Recall 79.98% 대 RRF 56.92%; 교대 선정도 74.67%로 더 낮다.
- M40에서 RRF와 교대는 동일 후보 집합(해당 저장된 BM25 양성 제한 및 Dense 잔여 때문에) 결과 92.06%, Dense 단독 92.40%와 근접.
- M60에서 RRF/교대는 99.22%로 Dense 98.91%를 +0.30%p 상회, 관련 출현 1회 추가·0회 누락. 그러나 **84개 중 평균 75.73개를 이미 최종 후보로 보존하는 설정**이라 검색의 실질적인 변별력을 보여주지 못한다.
- M84는 전 사례 84개를 관점별 후보로 전달하기 때문에 100%이고, 이 자체로 Hybrid가 우수해졌다는 뜻이 절대 아니다.
- 후보 합집합의 평균 고유 후보 수(M40)는 Dense 60.60건, RRF/교대 58.23건이고, M60은 Dense 76.60건, RRF/교대 75.73건. 관점 간 중복이 있기 때문에 단순히 동일 M이어도 고유 후보 수가 달라진다.

## 3. 교수님 원안의 진짜 출력: 관점별 Top-K 이후 관련 사례 보존

여기서는 각 생성 관점의 Top10 결과를 **합쳐 중복 제거**하여 질문의 관련 사례를 얼마나 보존했는지 계산했다. 한 질문에 생성 관점이 2~5개이므로 **아래 Top10은 전역 사례 10개가 아니라 각 관점 10개씩**이다.

### 비학습 RRF 재정렬 후, 관점별 Top10 합집합 Recall

| 관점별 후보 M | Dense Top-M 후보에서 후단 RRF | Hybrid RRF Top-M 후보에서 후단 RRF | Hybrid 교대 Top-M 후보에서 후단 RRF |
|---:|---:|---:|---:|
| 20 | **60.51%** | 36.54% | 36.95% |
| 40 | **47.24%** | 36.54% | 36.54% |
| 60 | **38.88%** | 36.54% | 36.54% |
| 84 | 36.54% | 36.54% | 36.54% |

이 RRF 후단 참고순위는 Dense를 선택한 후보에도 Sparse rank를 활용한 RRF를 적용한 **공정 동일 후단 점수 비교**이다. 따라서 이 표의 'Dense Top-M'을 순수 Dense final ranking이라고 혼동하지 말 것.

### LOQO Query–Case MLP 재정렬 후, 관점별 Top10 합집합 Recall

| 관점별 후보 M | Dense 후보 | Hybrid RRF 후보 | Hybrid 교대 후보 |
|---:|---:|---:|---:|
| 20 | 39.04% | 26.85% | 39.06% |
| 40 | 19.93% | 16.87% | 16.87% |
| 60 | 11.86% | 11.86% | 11.86% |
| 84 | 9.71% | 9.71% | 9.71% |

- **후보를 많이 보존한다고 최종 Top10의 관련도 품질이 상승하지 않는다.** 오히려 현재 QCI MLP는 후보가 늘어날수록 관련 사례를 상위에 놓지 못하는 뚜렷한 오류가 있다.
- 학습 시 9개 다른 Dev 질문의 AI-Silver 양성을 이용하고, 평가 대상 질문의 관련도는 학습에 포함하지 않는 LOQO를 검증했다. 다만 이 MLP는 **기존 축소 구현을 재현한 실험모형일 뿐**, 교수님 설계의 학습형 Query–Case 네트워크 전체가 무효하다는 결론이 아니다.
- Dense 순위만 따르는 과거 Stage2-1 동일 뷰 기준 전역 Recall@10은 42.40%였다는 별도 frozen 결과가 있다. 위 표는 *관점별 Top10 합집합*이라 비교 단위가 다르며 직접 우열 비교 금지.

## 4. 전역 Top10 진단 (교수님 원안의 공식 출력이 아님)

M40일 때 branch-balanced unique 방식으로 전역 10개만 선정한 진단 값:

| 방법 | RRF global Recall@10 | QCI MLP global Recall@10 |
|---|---:|---:|
| Dense Top40 후보 | 28.20% | 6.39% |
| Hybrid RRF Top40 후보 | 26.81% | 8.18% |
| Hybrid 교대 Top40 후보 | 26.81% | 8.18% |

전역 10개는 관점별 10개와 다르다. 교수님 원안은 **관점별 branch와 Top-K를 유지**하도록 설계됐으므로 이 결과만으로 최종 결론을 내리지 않는다.

## 5. 이번 실험 판정

1. **구현과 자동검증 성공**: 풀 Dense/Sparse 순위를 결합한 다음 Top-M을 뽑는 우리 해석을 실행, 관점별 출처 보존 및 Query–Case Interaction 통과, 상세 로그·원자료 저장.
2. **후보 크기 M과 Top-M 선발 규칙이 결정적**: 작은 M에서 RRF가 잘못된 후보를 우선할 수 있다. 단순 합집합이 모든 관련 사례를 보존한다는 생각은 틀림.
3. **하이브리드가 Dense 단독보다 우수하다는 결과는 아직 나오지 않음**: 같은 관점별 M에서 다수 조건은 Dense 단독 후보 Recall이 높았다. M60의 근소한 차이는 높은 후보 보존량의 영향.
4. **현재 QCI MLP는 가장 시급한 성능 병목**: 관련 사례가 후보 안에 있어도 최종 TopK 상위로 제대로 올라오지 못한다. 훈련 라벨, 관점별 타깃과 전체 질문 타깃 정합성, 입력 품질, pairwise ranking loss, model capacity, hard-negative 등 별도 원인분석 필요. 결과를 좋게 보이도록 임의 재튜닝하지 않았다.
5. **교수님 확인 사항**: Candidate Union(Top-M)의 합집합 범위와 결합 점수/선발 규칙, 관점별 K, 그래프 retrieval의 포함 범위, 본문의 Multi-view learned Gate 조합. 답변 전 지금 방식은 탐색적 구현으로만 유지.

**한계**: v2.3 AI-Silver 개발 평가, 독립 Test·인간 Gold 아님. Learned Gated Fusion/Attention은 이번 재생에서 equal-view로 대체, FAME-AX Stage 3/4 새 end-to-end 전체 테스트하지 않음. 이 문서만으로 교수님의 '완전한 제안 모델 구현'이라고 선언할 수 없다.
