# AX v2.3 Stage2: 모든 84개 관점별 정밀 매칭 vs Dense·Sparse 후보 축소

## 사전 등록 (2026-10-24; 실행 결과 확인 전)

**목적:** 교수님이 권장하신 '관점별 검색결과 분리→정밀매칭→관점별 Top-K'에 따라 전 사례를 점수화하는 경우와 Dense+Sparse가 후보를 줄이는 경우를 엄정하게 비교한다. 84개 데이터에서는 full84를 성능의 상한이 아닌 *후보 보존 기준*으로 사용한다. Query–Case MLP의 품질 문제도 검증한다.

### 1. 연구 흐름
- 배경: 기업 문제를 여러 관점으로 생성하고 각 관점의 관련 AX 사례를 검색.
- 문제: 조기 후보 컷으로 양성 사례가 탈락할 수 있고, 전 사례를 유지하면 재평가 비용과 비관련 후보가 늘어날 수 있다.
- 방안: P1~Pn 결과를 각각 유지하고 같은 정밀 매칭 점수로 full vs retrieval-reduced 후보 풀을 비교.
- 설계: 84 cases × 97 frozen runtime perspectives (10 dev queries ×3), 각 관점에서 후보 집합을 변경하되 정밀 매칭 MLP는 **같은 held-out query에 대해 한 번만 학습하고 모든 후보 전략에 동일 적용**.
- 비교: 동일 per-view 최종 K=5,10에서 recall, coverage, precision, 후보 단계 상한, reranker gap, evaluated query–case pair 수, 개별 positive gain/loss.

### 2. 데이터와 누설 방지
- 고정된 release/ax-v2.3-stage1-to4-dev-20261023의 84 사례, 2520 AI-Silver DEV qrels, 97 GPT 생성 관점, BGE-M3 NPZ, Kiwi BM25 sparse rank/score 재생. 새 LLM/embedding 호출 없음.
- QCI LOQO: 각 held-out 질의는 나머지 9개 질의에서만 학습, held-out의 3회 반복 라벨 전체 학습 제외. 48차원 무감독 고정 projection, feature `[q,c,q*c,abs(q-c)]`, MLP 192→64→1, BCE balanced, epoch32, LR0.003, seed42, 이전 축소 QCI와 구조 동일.
- **런타임 P1~P5**는 AI Silver 평가의 고정 reference P1~P3와 정의가 다르다. 번호가 같다고 같은 관점으로 간주하지 않음. query-level positive set(평가 reference 관점의 relevant>=3 합집합)으로 per-view TopK **합집합의 recall**을 평가.
- 원본·구축 데이터를 수정하지 않고 새 branch `experiment/v23-stage2-full84-vs-retrieval-20261024`, 결과 `experiments/v23_stage2_full84_comparison/`에 저장.

### 3. 후보 구성 (각 런타임 관점별; 기계적 규칙, 정답 라벨 미사용)
1. `all84`: **전체 84개** 모든 관점에 유지 (후보 recall=100% by definition).
2. `dense20`: multi-view cosine mean 관점별 Top20.
3. `dense40`: 같은 점수 상위 40.
4. `hybrid20_20`: Dense20과 **BM25 score>0인** Sparse 상위20의 ID 합집합, 중복 제거; source 유지. BM25 score=0은 '검색어 일치' 증거가 아님.
5. `dense_matched_hybrid_n`: 각 관점의 `hybrid20_20` 실제 고유 후보 수 N과 일치하게 Dense 상위 N개. **실제 재평가 비용(후보 쌍 수)이 정확히 동일**한 공정 대조군.
6. `sparse20_positive`: BM25 양성 score만 있는 상위20 후보. 실제로 K 미만일 경우 반환 가능한 결과만 사용.

전체 후보 84개는 반드시 stage2에서 QCI 점수를 모든 사례에 매긴 뒤 관점별 Top5/10을 선정해야 하며, global 5/10으로 조기 합치지 않는다. 후보 단계에서는 full all84 vs 각 축소 전략의 상대적으로 작은 pool을 만든다.

### 4. 최종 점수 및 공정성
- `mlp`: 교수님 Query–Case Interaction의 실험 축소 구현. query-level LOQO 학습; 후보 방법별 추가 학습/재튜닝 금지.
- `dense_score`: view mean dense similarity 기준선. full84과 후보 전략 모두 같은 사례 score로 정렬, scorer robustness check.
- `rrf`: dense rank + BM25 score-positive lexical rank를 사용하는 고정 RRF(60), 모든 pool에 동일한 case score를 사용. 이건 별도 진단으로 교수님이 지정하신 공식이 아님.
- 관점별 TopK를 모두 CSV로 보존하고 집합의 unique ID로 질의 전체 recall과 reference view coverage 평가. 동일 K는 동일 total output count를 의미하지 않으며, branch count는 세팅 간 같고 고유 수는 달라질 수 있다.
- `candidate_recall`: query-run 내 각 관점 후보 합집합이 커버하는 Silver positive 비율.
- `oracle_per_branch_k_upper`: query-level 긍정 라벨을 알고 관점별 K개를 최적으로 선택할 때의 *낙관적 상한* (단순 각 case positive union 중 선택; 참조 관점 alignment 아님). 모델 성능이 아니라 표기된 이론 비교.
- 실행 비용: reranker 대상 **관점×후보 쌍수**와 full 대비 비율; 실제 타이밍은 별도 측정하지 않으면 주장하지 않음.
- 후보 stage 절감은 성능 향상과 다름. 후보 recall=100%라고 최종 output recall=100%인 것은 아님.

### 5. 완료 판정
- 모든 runtime perspective 97개 x 84 cases의 full scorer가 정확한 ID와 shape로 계산됨.
- `all84` 후보 수는 매 branch 정확히 84개, candidate recall=1; full84의 출력 TopK 점수는 MLP로 정해짐.
- `dense_matched_hybrid_n`의 per-branch 후보 수와 `hybrid20_20` 동일.
- `hybrid20_20`은 Dense20 사례 모두 보존; BM25 zero 기여 없이 sparse-positive top20만 사용.
- 최종 perspective TopK no duplicate within branch, LOQO train query disjoint, all 10x3 runs included.
- H0 결과 포함 실패를 숨기지 않음. Silver Dev로 최종 학술 성능 주장 금지. Learned Gate/Graph/Factor Anchor/Wald/Stage4는 여기서 실행하지 않음.

### 6. 출력
`scripts/v23_stage2_full84_comparison.py`, `tests/test_v23_stage2_full84_comparison.py`, `.github/workflows/v23-stage2-full84-comparison.yml`, `experiments/v23_stage2_full84_comparison/*.csv,*.json`, `docs/v23-stage2-full84-results-2026-10-24.md`.
