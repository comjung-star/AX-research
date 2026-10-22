# Stage 2-2 Query-Conditioned Gated Fusion — Dev Result Analysis

## 실행 요약

- Experiment: `rq2_stage2_gated_v1`
- Dataset: AX0001~AX0100
- Dev Query: GTQ001~GTQ010
- Generated Perspective: Stage 1 MP Dense 실제 branch replay
- View score: Stage 2-1 Problem / Task / Context cosine score 재사용
- Validation: Query-level Leave-One-Out
- Final selection: branch-balanced unique
- K: 5 / 10 / 20
- LLM 재호출 없음

## Recall

| System | @5 | @10 | @20 |
|---|---:|---:|---:|
| Stage 1 MP Dense | 0.323267 | 0.502667 | 0.656546 |
| Stage 2-1 Multi-view Equal | 0.323467 | 0.499295 | 0.659976 |
| Stage 2-2 Query-Conditioned Gate | 0.309681 | 0.464334 | 0.655820 |

Stage 2-2 - Stage 2-1:
- @5: -0.013785
- @10: -0.034962
- @20: -0.004156

Stage 2-2 - Stage 1 MP Dense:
- @5: -0.013586
- @10: -0.038333
- @20: -0.000726

현재 v1에서는 Gated Fusion이 Recall 개선으로 이어지지 않았다.

## Gold gained / lost vs Stage 2-1 Equal

- @5: gained 21 / lost 25 / net -4
- @10: gained 21 / lost 33 / net -12
- @20: gained 19 / lost 19 / net 0

Gate가 ranking을 바꾸면서 새로운 Gold도 유입했지만 특히 @10에서
잃은 Gold가 더 많아 전체 Recall이 하락했다.

## Learned View Weight

평균:
- Problem: 0.5998
- Task: 0.0026
- Context: 0.3976

범위:
- Problem: 0.4652 ~ 0.8103
- Task: 0.0012 ~ 0.0054
- Context: 0.1861 ~ 0.5336

특징:
- Query/Perspective별 가중치 차이는 실제로 생성됨
- 하지만 모든 fold에서 Task weight가 사실상 0에 가까워지는 현상이 나타남
- Gate가 Problem + Context 중심의 2-view 모델처럼 행동

이는 "Task View가 원래 필요 없다"는 결론이 아니다.
현재 학습 target이 Query-level Gold union이므로, Task View의 관점별 고유 기여를
충분히 보상하지 못했을 가능성이 있다. 이 해석은 후속 가설이며 현재 결과만으로
확정하지 않는다.

## Branch Diagnostic

- mean branch Jaccard@20: 0.3744
- duplicate candidate rate@20: 0.4211

Stage 2-1 Equal의 mean Jaccard 0.4035보다 branch overlap은 낮아졌지만,
이 다양성 증가가 Recall 개선으로 이어지지는 않았다.

## 결론

Stage 2-2의 핵심 결론:

> Query-conditioned weighting 자체는 branch ranking을 변화시키지만,
> 현재의 low-parameter semantic-anchor Gate + query-level pairwise objective는
> Equal Fusion보다 좋은 Top-K를 만들지 못했다.

따라서:
1. Stage 2-2 v1 Gate를 현재 제안모델의 우수한 구성요소로 주장하지 않는다.
2. Dev 결과를 보고 같은 v1 hyperparameter를 사후 튜닝하지 않는다.
3. 실패 결과를 ablation으로 보존한다.
4. Stage 2의 다음 독립 구성요소인 Hybrid Retrieval로 진행한다.
5. 향후 Gate를 재설계할 경우 새 version으로 분리하고, branch-specific supervision 또는
   더 큰 학습 데이터의 필요성을 검토한다.

Perspective Coverage와 Strategy Coverage는 기존과 마찬가지로 @5부터 1.0으로
포화되어 이번 실험의 변별 지표로 사용하기 어렵다.
