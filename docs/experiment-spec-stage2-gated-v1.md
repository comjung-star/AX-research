# Stage 2-2 Query-Conditioned Gated Fusion v1 — FROZEN

## 목적

Stage 2-1에서 Problem / Task / Context를 분리했지만 동일가중(1/3, 1/3, 1/3) 결합만으로는 Stage 1 MP Dense 대비 의미 있는 Recall 개선이 확인되지 않았다.

Stage 2-2는 세 View를 항상 동일하게 취급하지 않고, **각 Generated Perspective branch의 내용에 따라 Problem / Task / Context 중요도를 동적으로 결정하는 Query-Conditioned Gate**의 효과를 검증한다.

이 실험은 Hybrid Retrieval이나 Query-Case Interaction을 추가하지 않는다. 바꾸는 요소는 View fusion rule 하나뿐이다.

## 비교 질문

> 동일한 Stage 1 Generated Perspective, 동일한 BGE-M3 view score, 동일한 branch-balanced unique selection을 사용할 때, equal fusion보다 query-conditioned learned gate가 Recall@K를 개선하는가?

## 통제 조건

고정:
- Dataset: AX0001~AX0100
- Dev Query: GTQ001~GTQ010
- Ground Truth: Dev Ground Truth v1
- Generated Perspective: Stage 1 MP Dense 실제 결과 replay
- Dense encoder: BAAI/bge-m3
- Problem / Task / Context별 cosine score: Stage 2-1 결과 재사용
- K = 5 / 10 / 20
- final selection: branch-balanced unique
- Gold threshold: relevance >= 3
- LLM 재호출 없음

변경:
- Stage 2-1: equal mean = (1/3, 1/3, 1/3)
- Stage 2-2: branch query에 따라 Gate가 세 View weight를 생성

## Gate 구조

데이터가 Dev Query 10개로 작기 때문에 1024차원 BGE embedding 전체에 큰 MLP를 붙이지 않는다. 과적합 위험을 낮추기 위해 3개의 고정 semantic view anchor와 branch query 간 cosine similarity를 Gate 입력으로 사용한다.

Anchor:
- Problem: 업무에서 발생하는 문제, 병목, 오류, 지연, 부담, 위험
- Task: 수행해야 하는 업무, 처리 대상 작업, 과업, 업무 기능
- Context: 업무 환경, 운영 조건, 조직 상황, 시스템 제약, 규모, 맥락

구조:

```text
Generated Perspective branch query
        ↓ BGE-M3
3개 semantic anchor와 cosine
        ↓
[problem_anchor_sim, task_anchor_sim, context_anchor_sim]
        ↓
Linear(3 → 3) + Softmax
        ↓
[w_problem, w_task, w_context]
        ↓
w_problem*s_problem + w_task*s_task + w_context*s_context
        ↓
branch ranking
```

Gate는 12개 파라미터(3×3 weight + 3 bias)만 갖는다. 초기값은 모두 0으로 두어 시작 시 Softmax가 정확히 (1/3, 1/3, 1/3)이 되도록 한다.

## 학습 및 누수 방지

GTQ001~GTQ010은 Dev이므로 최종 Test 성능으로 해석하지 않는다. 다만 Gate가 같은 Query의 정답을 보고 그 Query를 평가하는 누수를 막기 위해 **Leave-One-Query-Out(LOQO)** 방식으로 out-of-fold 평가한다.

예:
- GTQ001 평가 → GTQ002~GTQ010으로 Gate 학습
- GTQ002 평가 → GTQ001 + GTQ003~GTQ010으로 Gate 학습
- ...
- GTQ010 평가 → GTQ001~GTQ009로 Gate 학습

한 Query의 3개 LLM run은 전부 같은 fold에 묶는다. 따라서 평가 Query의 relevance label은 해당 fold Gate 학습에 사용되지 않는다.

학습 target:
- Query-level Gold Relevant Case (relevance >= 3의 union)
- generated branch마다 Gold case가 non-Gold case보다 높은 fused score를 갖도록 pairwise logistic ranking loss 사용
- Reference Perspective를 runtime input이나 Gate feature로 사용하지 않는다.

Frozen training settings:
- seed: 42
- optimizer: AdamW
- learning rate: 0.05
- weight decay: 0.01
- epochs: 120
- pairwise scale: 10.0
- query-balanced loss aggregation

## 평가

Primary:
- Recall@5 / @10 / @20
- Perspective Coverage@K
- Strategy Coverage@K

Diagnostic:
- Stage 2-1 Equal Fusion 대비 Gold gained / lost / net
- Stage 1 MP Dense 대비 Gold gained / lost / net
- branch pairwise Jaccard
- duplicate candidate rate
- Query×Run×Perspective별 learned view weights
- 평균/최소/최대 view weight

## 해석 원칙

1. LOQO 결과는 Dev 내부의 out-of-fold diagnostic이다. 최종 Held-out Test가 아니다.
2. Gate가 Equal Fusion보다 좋아질 경우 query-conditioned weighting의 유효 신호로 본다.
3. 좋아지지 않으면 Gate hyperparameter를 같은 Dev 결과에 맞춰 임의 튜닝하지 않는다. 변경이 필요하면 새 버전으로 기록한다.
4. Perspective Coverage / Strategy Coverage가 이미 포화되어 있으면 Recall과 Gold gained/lost를 중심으로 해석한다.
5. Ground Truth는 결과를 본 뒤 수정하지 않는다.
