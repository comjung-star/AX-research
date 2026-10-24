# 2026-10-24 Query–Case Interaction 성능저하 원인 검증 및 개선 실험 사전계획

**본 문서는 결과 확인 전에 고정.** Original frozen `release/ax-v2.3-stage1-to4-dev-20261023` 및 이전 실험 결과 변경 금지.

## 배경 → 문제점 → 방안 → 설계 → 비교
- **배경:** 관점별 AX 검색 사례를 Query–Case Interaction로 재평가하는 교수님 구조.
- **문제:** 최근 실험의 전체84+48d MLP 관점별 Top10 합집합 AI-Silver recall 9.71%, 동등 조건 Dense score 63.32%. 또한 학습 라벨은 각 LLM 생성 관점에서 동일한 질문 전체 positive union을 사용해 관점별 차이를 반영하지 못함.
- **방안:** (1) 라벨 불일치 실제 수치 점검, (2) 48d 랜덤 축소를 제거한 full-vector MLP 비교, (3) reference Silver 관점의 관련 사례 중심점을 이용한 *명시적 약지도 관점 라벨 매핑* 실험, (4) Dense 3-view 점수에 작은 순위 학습 보정을 가하는 Pairwise RankNet 진단.
- **설계:** 84 cases, 10 Dev query ×3 runs, GPT 생성 97 runtime perspectives, 기존 BGE-M3 frozen NPZ와 Kiwi BM25 frozen 점수. 외부 API/임베딩 재생성 없음. 모든 learned methods는 query-level LOQO (9개 질의 훈련, 1개 질의 모두 제외) 동일 적용.
- **비교:** 모든 후보를 관점별로 평가하는 full84 및 Dense20, Dense20+Sparse-score-positive20 후보 풀을 동일한 모델들로 각각 비교; 최종 관점별 Top5/Top10 합집합 Recall, precision, reference view coverage.

## Label audit (학습 정답 구조 확인)
- qrels의 reference P1/P2/P3 relevance>=3: 케이스별 positive view 개수 1/2/3, 모든 reference 관점 간 positive Jaccard, 각 질문별 positive union sizes 산출.
- 이전 QCI 지도라벨은 각 runtime perspective P1..P5에 reference view 전체 union을 동일하게 부여했음. Reference P1과 runtime P1을 ID로 직접 맞추지 않음.
- Pseudo-view training label은 **훈련 질문에서만** reference 각 관점 positive case의 frozen document embeddings centroid와 현재 runtime generated perspective vector 간 cosine으로 가장 가까운 reference 관점 하나를 선택. 그 reference 관점의 case labels를 그 runtime 관점 학습 타깃으로 사용. 이는 새 AI/인간 Gold가 아니며 정답을 복구했다는 주장을 하지 않음.
- 홀드아웃 질문의 Silver 데이터는 그 fold의 학습과 pseudo-view centroid 구축에 절대 사용하지 않음.

## 사전 정의한 scorer
1. `dense_3view`: frozen query–case Problem/Task/Context cosine equal mean (고정 비학습 baseline).
2. `legacy_48_pooled`: frozen 48d 랜덤 projection Q–C MLP 192→64→1, BCE epochs32; 질의 전체 pooled union label. 기존 full84 9.71% 재현.
3. `fullvec_pooled`: 랜덤 차원축소 제거, full 1024-dimensional frozen embeddings를 그대로 사용한 Q–C MLP 4096→64→1, BCE epochs32, 동일 조건, train held-out exclusion.
4. `legacy_48_pseudoview`: 48d Q–C MLP 동일하되, training target만 훈련질의의 reference view centroid 기반 pseudo-view labels로 교체.
5. `anchor_pairwise_010`: Dense equal-mean score + 0.10*tanh(linear 3-view cosine + sparse rank features), training-query reference *union* positive/negative pairwise softplus with L2 penalty 0.01, epochs80. Dense score anchor가 있기 때문에 Pairwise RankNet의 작은 보정만 가능.
6. `anchor_pairwise_025`: `anchor_pairwise_010` 동일 학습 모델 점수에서 사전 지정 계수 0.25를 곱하는 보정 민감도 분석; 사후 선택 금지.

RankNet training: 전체 pair 전체 조합 대신 질의별 runtime branch마다 관련 사례 1건과 비관련 사례 3건을 고정시드로 선택해 매 epoch 학습하는 reproducible pair sampling; 같은 훈련 모델을 full84/Dense20/hybrid에 적용한다. 참고: reference 관점별 pseudo target은 실제 LLM 생성 관점과 1:1 정답이라고 주장할 수 없고 query 전체 Silver 평가에서는 불리할 수도 있다.

## Acceptance
- 10 LOQO folds, 9 train question IDs in each fold, held query label never used in model training. Baseline `legacy_48_pooled` full84 Top10 9.71% ± 0.01%p 재현.
- 97 generated perspectives, 84 cases per runtime branch, per-view Top5/10 output with provenance.
- Same feature and scorer irrespective of candidate pooling, and no evaluated query's qrels in candidate selection. Dense20 and hybrid use frozen 3-view Dense and positive-score BM25.
- 정확한 기존 Baseline Dense full84 Top10=63.32% ±0.01%p 재현.
- 모델 개선이 없다면 실패를 그대로 기록하고 모델을 임의 튜닝하지 않음; 사전 지정 결과와 Test 성능 절대 혼동하지 않음.
- GitHub Actions에서 실행, 결과만 별도 브랜치 `experiment/v23-qci-improvement-audit-20261024`에 저장. Stage3/4 추가 검증이나 교수님 학습형 Gated Fusion 최종 검증을 했다고 주장하지 않음.

## Outputs
`scripts/v23_qci_improvement_audit.py` · `tests/test_v23_qci_improvement_audit.py` · `.github/workflows/v23-qci-improvement-audit.yml` · `experiments/v23_qci_improvement_audit/` · `docs/v23-qci-improvement-results-2026-10-24.md`.
