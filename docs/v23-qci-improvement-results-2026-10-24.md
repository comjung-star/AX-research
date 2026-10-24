# AX v2.3 정밀 매칭(QCI) 개선 실험 최종 결과 (2026-10-24)

## 실행 개요 및 결론
실험 완료·GitHub Actions 성공. 84개 AX 사례 / 10 Dev 업무 질문×3회 / GPT 생성 실행 관점 97개 / 기존 AI-Silver 평가 2,520개. **기존 MLP의 일부 개선에는 성공했으나 Dense 유사도 단독 기준(63.32%)을 능가하지는 못했다.** 따라서 개량 QCI를 채택하지 않고 현재 Dense를 안전한 비교 기준으로 유지한다.

**핵심:** 기존 48차원 MLP 9.71% → 전체 BGE-M3 임베딩 MLP 22.29%(+12.58%p). 관점별 약지도 라벨 MLP 15.51%(+5.80%p). Dense 중심 pairwise 보정 Top10 58.98%(기준 63.32%보다 -4.33%p), 그러나 Top5에서 50.69%로 Dense 48.45%보다 +2.24%p. 개선의 효과와 한계가 혼재하며, 학습형 정밀 매칭의 문제는 아직 해결되지 않았다.

## 1. 배경
교수님 제안의 LLM 관점분해 → Multi-view 검색 → Dense/Sparse 후보 선택 → Query–Case Interaction → **관점별 Top-K 출력**에서 QCI가 관련 사례를 정확하게 선정해야 한다. 이전 full84 개발 실험에서는 후보 보존 Recall 100%였음에도 기존 MLP의 관점별 Top10 합집합 Recall이 9.71%에 불과했다.

## 2. 문제점 분석

### 학습 라벨 불일치 점검
기존 QCI는 실제 runtime 생성 관점마다 서로 다른 의미를 갖더라도 **해당 업무 질문의 평가용 reference 관점 3개 positive 합집합**을 모두 똑같은 positive target으로 학습했다. Silver qrels를 점검한 결과:

| Silver reference 관점 3개 중 해당 케이스가 관련인 관점 수 | 질문별 고유 관련 사례 합산 건수 |
|---|---:|
| 딱 1개 관점만 관련 | **53** |
| 2개 관점에 관련 | **31** |
| 3개 관점 모두 관련 | **24** |

질문별 평균으로 관련 사례 중 **83.68%**는 reference 3관점 모두에 관련된 것이 아니었다. 즉, 전체 합집합을 각 runtime 관점의 학습 정답으로 사용하는 방식은 관점의 차이를 학습하지 못할 가능성이 크다. **이 숫자만으로 라벨 자체가 잘못됐거나 원인을 확정했다는 뜻은 아니다.**

또한 runtime 관점 P1~P5는 reference qrels 관점 P1~P3와 다른 정의이므로 단순한 P번호 연결 금지. 참고로 훈련 질문에서만 Silver-positive 사례 임베딩 중심점을 만들어 가장 가까운 reference 관점을 할당하는 실험도 실시했으나 평균 1·2위 유사도 차이가 **0.0333**으로 작아 매핑이 불안정할 가능성이 있다. 이러한 매핑은 검증된 관점별 정답이 아닌 **약지도 실험용 임시 타깃**이다.

### 임베딩 축소·학습 제약
기존 MLP는 BGE-M3 1024차원 임베딩을 임의 행렬로 48차원으로 줄여 특징 벡터 `[q,c,q×c,|q-c|]`를 만든 뒤 BCE로 양/음 관련 여부를 배웠다. 축소 과정의 정보 손실 여부를 직접 검증했다. 훈련에 활용되는 개발 질문은 fold당 9개로 작고, 독립 사람이 평가한 관점 정답은 없다는 한계가 있다.

## 3. 방안
연구 아키텍처의 주요 블록을 바꾸지 않고 학습 대상의 세부 구현만 변경하여 원인별 비교. 모든 학습형 모델은 **10-fold Leave-One-Query-Out(LOQO)**를 사용했고, 평가할 질문 1개와 그 3회 반복은 학습에서 배제했다. 동일 학습 모델로 full84 / Dense20 / Dense20+BM25(점수 양수)20 후보를 모두 평가했다. 후보 조건별 별도 재학습 금지.

## 4. 문제 해결을 위한 설계
| scorer | 변경점과 검증 가설 |
|---|---|
| `dense_3view` | Frozen Problem/Task/Context 3-view 유사도 평균, **비학습 기준선** |
| `legacy_48_pooled` | 과거 동일 48차원 랜덤 투영 MLP, 질문 전체 positive 합집합 라벨 |
| `fullvec_pooled` | **투영 축소 제거**, BGE-M3 **원래 1024차원 임베딩 그대로** 4096→64→1 MLP |
| `legacy_48_pseudoview` | 48차원 모델 유지, 훈련질의에 한해서 Silver reference centroid로 약지도 target 매핑 |
| `anchor_pairwise_010` | Dense 3-view 점수 + 작은 learned residual(0.10), 관련/비관련 **쌍별 순위 학습** |
| `anchor_pairwise_025` | 동일 pairwise 학습모델의 보정 강도 0.25, 사전 정의 민감도 분석 |

단순 본문 재서술로 만드는 GPT 평가는 추가하지 않았다. 전체 84개 데이터 임베딩, 실행 관점, BM25 스코어 모두 frozen 재사용. 두 anchor scorer는 Dense score 기반에 학습된 **작은 보정**을 추가하므로 전체 별도 QCI MLP나 교수님 최종 1024→256→64→1 모델과 동등하다고 주장하지 않는다.

## 5. 결과 비교

### 5.1 핵심: 전체 84개 후보를 관점별로 모두 재평가 (Top10)

| 평가 모델 | 관점별 Top10 합집합 Recall | 기존 MLP 대비 |
|---|---:|---:|
| **비학습 Dense 3-view** | **63.32%** | +53.60%p |
| 기존 48차원 MLP | **9.71%** | 기준 |
| **1024차원 Full-vector MLP** | **22.29%** | **+12.58%p** |
| **관점별 약지도 48차원 MLP** | **15.51%** | **+5.80%p** |
| Dense + Pairwise 보정 0.10 | **58.98%** | +49.27%p |
| Dense + Pairwise 보정 0.25 | **54.73%** | +45.02%p |

**해석:** 축소를 제거하자 MLP는 큰 폭으로 개선됐으므로 **정보 손실이 성능 저하에 기여했을 가능성**이 커졌다. 단, 1024차원 입력으로 바꾼 동시에 신경망 입력 가중치 수가 변하므로 직접적 인과관계가 완전히 증명된 것은 아니다. 약지도 관점 타깃 역시 기존보다 좋지만 충분하지 않다. Dense-anchored 학습은 비교적 높은 성능이지만 **원래 Dense score보다 떨어져 채택 불가**.

### 5.2 Top5에서는 결론이 약간 다름
| 모델 | full84의 관점별 Top5 합집합 Recall |
|---|---:|
| Dense 3-view 기준선 | **48.45%** |
| 기존 48차원 MLP | 4.28% |
| 1024차원 MLP | 12.19% |
| 관점별 약지도 48차원 MLP | 6.09% |
| **Dense+Pairwise(0.10)** | **50.69%** |
| Dense+Pairwise(0.25) | 40.32% |

Pairwise(0.10)는 Top5에서 Dense 단독 대비 **+2.24%p**이지만, Top10에서는 **-4.33%p**다. 하나의 K에서 국소 이점이 있더라도 종합 우수성을 확인한 것은 아니다. 다양한 모델들을 개발용 같은 자료로 시도했으므로 이 차이를 논문에서 확정적 개선으로 주장하지 않는다.

### 5.3 후보 축소 조건에서의 비교 (관점별 Top10 합집합 Recall)
| scorer | 전체84 | Dense20 | Dense20+Sparse20 |
|---|---:|---:|---:|
| Dense 3-view | **63.32%** | **63.32%** | **63.32%** |
| 기존 48d MLP | 9.71% | 39.04% | 23.51% |
| 개선 1024d MLP | 22.29% | **43.99%** | 34.87% |
| 관점 약지도 48d MLP | 15.51% | 35.18% | 22.44% |
| Pairwise 0.10 | 58.98% | 60.45% | 58.98% |
| Pairwise 0.25 | 54.73% | 60.84% | 54.73% |

이 실험에서 후보 확보 Recall은 full84 100%, Dense20 79.98%, Dense20+Sparse20 83.13%이고, 평균 후단 평가쌍 수는 각각 271.6, 64.7, 97.7이었다. 전체 후보를 평가하는 것이 후보 누락을 막지만 미흡한 MLP 순위 품질을 자동으로 해결하지 못한다.

### 5.4 질문별 편차 (전체84 / 관점별 Top10)
- V21D002(긴 이메일/후속조치): 비학습 Dense **60.0%**, 개선 1024d MLP **0.0%**, Pairwise 0.10 **53.33%**.
- V21D003(지식/매뉴얼 검색): Dense **25.49%**, 개선 1024d MLP **27.45%**, Pairwise 0.10 **31.37%**.
- V21D007: Dense **94.44%**, 개선 1024d MLP **0.0%**, Pairwise 0.10 **61.11%**.
- V21D009: Dense **45.45%**, 개선 1024d MLP **24.24%**, Pairwise 0.10 **57.58%**.
10개 질문 기준 Pairwise(0.10)는 Dense 단독보다 우세 2개, 동률 4개, 열세 4개였다. 평균만 보고 모든 유형에서 개선됐다고 주장할 수 없다.

## 6. 종합 판단 및 연구 방향
1. **문제 발견:** 질문 전체 양성 사례를 모든 runtime 관점의 정답으로 쓰는 기존 학습 방식은 관점 구분이라는 목표와 맞지 않을 수 있다. Silver reference와 runtime 관점의 근본적 정의 차이 때문에 개선에는 실제 관점-사례 정답 설계가 필요하다.
2. **부분 개선:** 전체 임베딩 사용으로 QCI MLP 9.71%→22.29% 개선, 학습관점 약지도 9.71%→15.51%. 그러나 둘 다 낮아서 본 모델 채택은 보류.
3. **현행 권고:** 새로운 관점별 relevance judgement가 확보되기 전에는 **비학습 Dense 3-view 유사도**를 강한 비교 기준으로 보존하고, 검증되지 않은 QCI가 최종 결과를 덮어쓰지 않도록 한다.
4. **다음 실험:** 실제 runtime 관점과 case ID에 대한 정답 레이블 마련(소규모 대표 샘플 인간 평가 또는 문서화된 독립 절차). 그 다음 full 1024d 또는 교수님 256d learned multi-view representation, rank loss/in-batch contrastive를 정식 훈련하고 독립 Test와 paired query-level 통계를 평가.

### 연구 제한
이번 성능 수치는 **AI-Silver 개발용**이며 10개 질문×3회는 통계적으로 독립적인 질문 30개가 아니다. 과거 Stage1 전역 Top10 Recall과 관점별 Top10 합집합 Recall은 다른 지표. 학습 임베딩 게이트, 독립 Test/Human Gold, Graph, FAME-AX Factor Anchor/Wald, Stage3/4 end-to-end 성능은 이 실험에서 실행되지 않았다.

## 7. 증거/재현
- [실험 전 고정된 프로토콜](v23-qci-improvement-protocol-2026-10-24.md)
- [검증 성공한 GitHub Actions 실행](https://github.com/comjung-star/AX-research/actions/runs/40079857963)
- 코드 `scripts/v23_qci_improvement_audit.py`, 테스트 `tests/test_v23_qci_improvement_audit.py`
- 산출물 폴더 `experiments/v23_qci_improvement_audit/`: `summary.json`, `silver_reference_label_audit.csv`, `runtime_pseudo_reference_view_mapping.csv`, `train_holdout_audit.csv`, `candidate_pool_metrics.csv`, `model_metrics_by_query_run.csv`, `per_perspective_top10_rankings.csv`.
- 원본 frozen Stage1~4 미수정, 별도 브랜치 `experiment/v23-qci-improvement-audit-20261024`.
