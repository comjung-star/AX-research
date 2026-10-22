# Stage 2-4 Query-Case Interaction Dev Result Analysis

## 1. 질문

교수 제안 Search Core의
`[q,c,q⊙c,|q-c|] → MLP → Relevance Score` 구조가,
동일한 Hybrid Candidate Pool에서 비학습 RRF보다
관련 AX Case를 Top-K 상위로 더 잘 재정렬하는가?

## 2. 통제

- AX0001~AX0100 고정
- GTQ001~GTQ010 Dev 고정
- Dev Ground Truth v1 고정
- Stage 1 Generated Perspective 그대로 replay
- Stage 2-3 Hybrid Candidate Pool 그대로 재사용
- leg_k = 5 / 10 / 20 모두 평가
- BGE-M3 동일
- Case = Problem / Task / Context equal-mean representation
- Corpus-only PCA 64-d
- Query-level LOQO
- final cross-branch selection = branch-balanced unique
- LLM 재호출 없음
- Stage 2-2 Gate v1 미사용

평가 Query의 Gold label은 해당 fold의 MLP 학습에 사용하지 않았다.

## 3. 같은 Candidate Pool 비교

QCI:
```text
q, c (64-d)
→ [q,c,q⊙c,|q-c|] (256-d)
→ MLP 256→32→1
→ Relevance Score
```

Baseline:
```text
same Hybrid candidates
→ RRF(dense_rank, sparse_rank), constant=60
```

두 방식 모두 이후 동일한 branch-balanced unique로 최종 Top-K를 만든다.

## 4. Recall 결과

### leg_k = 5

| Final K | QCI MLP | Same-pool RRF | Delta |
|---:|---:|---:|---:|
| 5 | 0.243504 | 0.321087 | -0.077583 |
| 10 | 0.428052 | 0.476863 | -0.048811 |
| 20 | 0.619099 | 0.619099 | 0.000000 |

Top-20이 동일한 이유는 이 작은 candidate budget에서는 최종 unique pool 자체가 20개 이하인 경우가 많아,
순서가 달라도 K=20에서 사실상 같은 후보를 모두 포함하기 때문이다.

### leg_k = 10

| Final K | QCI MLP | Same-pool RRF | Delta |
|---:|---:|---:|---:|
| 5 | 0.219441 | 0.316405 | -0.096964 |
| 10 | 0.363484 | 0.506004 | -0.142520 |
| 20 | 0.585269 | 0.685974 | -0.100705 |

### leg_k = 20

| Final K | QCI MLP | Same-pool RRF | Delta |
|---:|---:|---:|---:|
| 5 | 0.204402 | 0.319923 | -0.115521 |
| 10 | 0.333520 | 0.517393 | -0.183873 |
| 20 | 0.548902 | 0.693165 | -0.144263 |

모든 실질 비교에서 QCI MLP v1이 RRF보다 낮았다.

## 5. Gold gained / lost vs RRF

| leg_k | Final K | gained | lost | net |
|---:|---:|---:|---:|---:|
| 5 | 5 | 32 | 57 | -25 |
| 5 | 10 | 23 | 38 | -15 |
| 5 | 20 | 0 | 0 | 0 |
| 10 | 5 | 29 | 58 | -29 |
| 10 | 10 | 33 | 79 | -46 |
| 10 | 20 | 21 | 53 | -32 |
| 20 | 5 | 32 | 68 | -36 |
| 20 | 10 | 36 | 96 | -60 |
| 20 | 20 | 35 | 89 | -54 |

QCI도 RRF가 놓친 Gold를 새로 올리는 경우는 있었지만,
그보다 RRF가 이미 잘 올려두었던 Gold를 더 많이 아래로 밀었다.

## 6. Coverage

RRF는 모든 budget / K에서 Perspective Coverage가 1.0이었다.

QCI는 후보가 커질수록 낮은 K에서 관점 Coverage도 감소했다.
예:
- leg_k=10, K=5: 0.8667
- leg_k=20, K=5: 0.8111
- leg_k=20, K=10: 0.9111

Strategy Coverage는 대부분 포화되어 변별력이 낮았다.

## 7. 해석

현재 결과는 **Query-Case Interaction이라는 아이디어 자체를 기각하는 결과가 아니라,
현재 v1 구현이 현재 데이터 규모와 supervision에서 일반화되지 않았다는 결과**로 해석한다.

가능한 원인은 다음과 같지만, 현 Dev 결과만으로 원인을 확정하지 않는다.

1. **Branch-specific supervision 부족**
   - Generated Perspective와 Reference Perspective를 직접 대응시키지 않기 때문에,
     각 branch의 positive label을 Query-level Gold union으로 학습했다.
   - 서로 다른 branch가 같은 positive set을 보게 되어 perspective-specific relevance 학습이 약해질 수 있다.

2. **작은 Query 수**
   - LOQO 한 fold당 학습 Query가 9개뿐이다.
   - 약 4천 개 수준의 MLP 파라미터도 Query-level 일반화에는 데이터가 부족할 수 있다.

3. **64-d Corpus PCA**
   - 과적합 억제를 위해 사용했지만 interaction에 필요한 일부 의미축을 줄였을 가능성이 있다.

4. **RRF baseline의 강한 rank prior**
   - Dense/BM25가 이미 만든 유용한 순위정보를 직접 보존한다.
   - QCI v1은 이 rank 정보를 feature로 사용하지 않고 semantic interaction만으로 다시 학습했다.

위 항목은 후속 가설이며 같은 Dev 결과를 보고 즉시 hyperparameter를 조정해 재실험하지 않는다.

## 8. 채택 판단

- Stage 2-4 QCI MLP v1: **현재 채택하지 않음**
- Same-pool RRF: **현 Dev에서 더 안정적인 ranking reference**
- 교수 제안 Query-Case Interaction 구성요소: **아키텍처에서 유지하되 v1 구현은 failed ablation으로 기록**
- 향후 더 많은 Training Query / branch-level supervision이 확보되면 별도 버전으로 재검증 가능

## 9. Stage 2 전체 요약

```text
Stage 2-1 Multi-view Equal
→ 뚜렷한 Recall 개선 없음

Stage 2-2 Gated Fusion v1
→ Equal보다 악화

Stage 2-3 Hybrid Candidate Union
→ Sparse 보완성 확인
→ 50:50 slot에서는 Dense-only보다 평균 Candidate Recall 낮음

Stage 2-4 Query-Case Interaction v1
→ Same-pool RRF보다 악화
```

Stage 2에서는 교수 제안 Search Core의 각 구성요소를 실제로 분리 검증했고,
현재 100 Case / 10 Dev Query 조건에서는 복잡한 학습형 결합보다
비학습 retrieval rank를 보존하는 방식이 더 안정적이었다.

## 10. 현재 결론 한 문장

**Query-Case Interaction MLP v1은 동일 Hybrid Candidate Pool의 RRF보다 Recall과 낮은 K의 Perspective Coverage가 낮았으며, 현재 Dev 규모에서는 학습형 interaction의 일반화 효과를 확인하지 못했다.**
