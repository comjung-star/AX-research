# Stage 2-1 Multi-view Dense Experiment v1 — FROZEN

## 목적

Stage 1에서 확인한 Multi-Perspective 검색의 탐색 이점을 유지하면서,
AX Case의 `Problem / Task / Context`를 분리 표현했을 때 검색 품질이
개선되는지 독립적으로 검증한다.

이 실험은 **Stage 2 전체 모델의 완성본이 아니다.**
Gated Fusion / Hybrid Retrieval / Query-Case Interaction을 넣기 전에
Multi-view 분리 자체의 효과만 확인하는 controlled ablation이다.

## 비교 질문

> 동일한 LLM Generated Perspective와 동일한 branch-balanced unique
> selection을 사용할 때, Case를 하나의 연결 문서로 임베딩하는 것보다
> Problem / Task / Context를 각각 임베딩하고 고정 동일가중으로 결합하는
> 것이 Recall@K를 개선하는가?

## 통제 조건

Stage 1의 Multi-Perspective Dense와 공정하게 비교하기 위해 다음을 고정한다.

- Dataset: `data/main_cases_v1.csv` (AX0001~AX0100)
- Dev Query: GTQ001~GTQ010
- Ground Truth: Dev Ground Truth v1
- Dense encoder: `BAAI/bge-m3`
- normalized embeddings + cosine similarity
- K = 5 / 10 / 20
- final selection: `branch_balanced_unique`
- Gold threshold: relevance >= 3
- **Stage 1 MP-Dense에서 실제 생성된 Query×Run별 Perspective를 그대로 replay**
- 따라서 Stage 2-1에서는 LLM을 다시 호출하지 않는다.

마지막 항목은 매우 중요하다. Perspective를 다시 생성하면 LLM sampling 차이와
Multi-view 효과가 섞이므로, Stage 2-1에서는
`experiments/rq1_retrieval/results/rq1_v1_3_llm_dev/multi_perspective_dense_branch_rankings.csv`
에 기록된 `branch_query_text`를 재사용한다.

## Stage 1 비교군

Stage 1 MP Dense:

```text
Generated Perspective
→ Case [Problem + Task + Context] concatenated text
→ one BGE-M3 case embedding
→ cosine similarity
→ branch-balanced unique
```

## Stage 2-1 제안 방식

```text
Generated Perspective
        ↓
 BGE-M3 query embedding
        ↓
 ┌───────────────────────────────┐
 │ Case Problem embedding       │ → cosine s_problem
 │ Case Task embedding          │ → cosine s_task
 │ Case Context embedding       │ → cosine s_context
 └───────────────────────────────┘
        ↓
 score = (s_problem + s_task + s_context) / 3
        ↓
 branch ranking
        ↓
 branch-balanced unique
        ↓
 Top-K
```

## 왜 동일가중 평균인가

Stage 2-1에서는 Gated Fusion의 효과를 섞지 않기 위해 세 View를
`1/3, 1/3, 1/3`로 고정한다.

- Stage 2-1: Multi-view 분리 효과
- Stage 2-2: Gated Fusion / Attention 효과

따라서 Stage 2-1에서 성능이 달라지면 최소한
"연결 문서 1개"와 "분리 View 3개"의 표현 차이에 의한 결과로 해석할 수 있다.

## 평가

Primary:
- Recall@5 / @10 / @20
- Perspective Coverage@5 / @10 / @20
- Strategy Coverage@5 / @10 / @20

Diagnostic:
- Stage 1 MP Dense 대비 Gold gained / lost / net
- Branch pairwise Jaccard
- Duplicate candidate rate
- Problem / Task / Context별 cosine score

## 해석 원칙

1. Stage 2-1이 Stage 1 MP Dense보다 높으면 Multi-view 분리가 검색에 기여할 가능성을 본다.
2. 낮거나 동일하더라도 곧바로 Multi-view 전체 가설을 기각하지 않는다.
   동일가중 결합은 학습형 Gated Fusion 전의 ablation이기 때문이다.
3. Dev 결과를 본 뒤 Ground Truth를 수정하지 않는다.
4. Stage 2-2의 Gate를 Dev 정답에 수동으로 맞춘 고정 가중치로 대체하지 않는다.
5. Held-out Test 전에는 Stage 2 전체 구조와 학습/평가 규칙을 다시 Freeze한다.
