# Stage 2-4 Query-Case Interaction v1 — FROZEN

## 목적

교수 제안 Search Core의 `Query-Case Interaction`을 독립적으로 검증한다.

Stage 2-3에서 Dense + Sparse Candidate Union은 Dense가 놓친 Gold를 실제로 추가했지만,
같은 retrieval slot budget의 Dense-only보다 평균 Candidate Recall은 높지 않았다.
Stage 2-4에서는 Candidate Pool을 그대로 입력으로 사용하고,
각 Generated Perspective branch query와 Candidate Case를 직접 상호작용시켜
**관련도가 높은 Case를 Top-K 위로 재정렬할 수 있는지** 검증한다.

## 교수 제안 구조와의 대응

연구계획서의 Query-Case Interaction:

```text
q_k + c_i
   ↓
[q, c, q⊙c, |q-c|]
   ↓
MLP
   ↓
Relevance Score
   ↓
Perspective-specific Top-K Cases
```

본 v1 실험은 위 구조를 그대로 사용한다.

## 통제 조건

고정:
- Dataset: AX0001~AX0100
- Dev Query: GTQ001~GTQ010
- Ground Truth: Dev Ground Truth v1
- Stage 1 Generated Perspective replay
- LLM 재호출 없음
- Encoder: BAAI/bge-m3
- Case representation: Stage 2-1의 Problem / Task / Context equal-mean representation
- Hybrid Candidate Pool: Stage 2-3 결과 그대로 재사용
- Hybrid leg_k: 5 / 10 / 20 **모두 평가**
- final cross-branch selection: branch-balanced unique
- K = 5 / 10 / 20
- Gold threshold: relevance >= 3

Stage 2-2 Gate v1은 Dev에서 Equal Fusion보다 낮아 사용하지 않는다.

## Interaction Representation

BGE-M3 raw embedding은 1024차원이므로 그대로
`[q,c,q⊙c,|q-c|]`를 만들면 4096차원이 되고, 현재 Dev Query 10개 규모에서는
MLP 파라미터가 지나치게 커질 수 있다.

따라서 라벨을 사용하지 않는 **Corpus-only PCA projection**으로
100개 AX Case representation에서 64차원 basis를 만든다.

- Case raw vector:
  - normalized Problem embedding
  - normalized Task embedding
  - normalized Context embedding
  - 세 벡터의 equal mean
- PCA basis:
  - 100개 Case raw vector만 사용
  - relevance label / Query label 미사용
- q와 c 모두 동일 64-d basis로 projection

그 뒤:

```text
q ∈ R^64
c ∈ R^64

x = [q, c, q⊙c, |q-c|] ∈ R^256
MLP: 256 → 32 → 1
```

## 학습

평가 Query의 Gold label이 학습에 들어가지 않도록
**Leave-One-Query-Out(LOQO)** 로 학습한다.

예:
- GTQ001 평가 → GTQ002~GTQ010만 학습
- ...
- GTQ010 평가 → GTQ001~GTQ009만 학습

한 Query의 3개 LLM run은 동일 fold에 묶는다.

Training label:
- Query-level Gold Relevant Case union
- Generated Perspective와 Reference Perspective의 ID를 직접 대응시키지 않는다.
- 각 branch query는 서로 다르지만, positive 여부는 해당 원 Query의 Gold union 기준이다.

Loss:
- pairwise logistic ranking loss
- 각 branch에서 positive candidate가 negative candidate보다 높은 score를 갖도록 학습
- query-balanced aggregation

Frozen settings:
- projection_dim: 64
- hidden_dim: 32
- dropout: 0.10
- seed: 42
- optimizer: AdamW
- learning_rate: 0.001
- weight_decay: 0.001
- epochs: 150
- pairwise_scale: 5.0

## 같은 Candidate Pool의 비교군

Query-Case Interaction 효과를 분리하기 위해 같은 Hybrid Candidate Pool에
비학습 결합인 Reciprocal Rank Fusion(RRF)을 적용한 baseline을 함께 만든다.

```text
RRF score = 1 / (60 + dense_rank) + 1 / (60 + sparse_rank)
```

해당 retriever에 없는 Case의 항은 0으로 둔다.

중요:
- RRF는 Stage 1의 branch merge 규칙을 대체하지 않는다.
- 각 branch 내부 Candidate 순서를 만드는 baseline일 뿐이다.
- 최종 cross-branch Top-K는 QCI와 RRF 모두 동일한 branch-balanced unique를 사용한다.

## 평가

각 leg_k=5/10/20에 대해:

Primary:
- Recall@5 / @10 / @20
- Perspective Coverage@K
- Strategy Coverage@K

Comparison:
- QCI MLP vs same-pool RRF
- Stage 2-1 Equal Dense 결과는 외부 reference로만 병기

Diagnostics:
- Gold gained / lost / net: QCI vs RRF
- source provenance(Dense / Sparse / Both)별 Top-K 진입
- MLP score distribution
- branch candidate count
- final unique result count

## 해석 원칙

1. Stage 2-4는 Dev 내부 LOQO diagnostic이며 최종 Held-out Test가 아니다.
2. QCI가 RRF보다 높으면 동일 Candidate Pool에서 learned interaction이 ranking에 기여한 신호로 본다.
3. 낮으면 같은 Dev 결과에 맞춰 hyperparameter를 사후 튜닝하지 않는다.
4. 세 candidate budget을 모두 보고 특정 budget만 선택적으로 보고하지 않는다.
5. Candidate Recall 상한보다 높은 final Recall은 나올 수 없으므로 Stage 2-3 Candidate Recall과 함께 해석한다.
6. Ground Truth는 결과에 맞춰 수정하지 않는다.
