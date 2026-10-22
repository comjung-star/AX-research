# Stage 2-3 Hybrid Retrieval Candidate Union v1 — FROZEN

## 목적

교수 제안 Search Core의 `Hybrid Retrieval = Dense + Sparse Candidate Retrieval → Candidate Union`을 독립적으로 검증한다.

Stage 2-3의 역할은 최종 Relevance Ranking을 확정하는 것이 아니다.
Hybrid Retrieval이 **Dense 단독이 놓친 관련 AX Case를 Candidate Pool에 추가로 확보하는지**를 확인한다.
최종 Candidate 재평가와 Perspective별 Top-K 결정은 다음 Stage의 Query-Case Interaction에서 검증한다.

## 비교 질문

> 동일한 Generated Perspective와 동일한 검색 슬롯 예산에서,
> Multi-view Dense + BM25 Candidate Union이 Multi-view Dense-only보다
> Query-level Gold Case Recall을 높이는가?

## 기준 구조

```text
Generated Perspective
      ├─ Stage 2-1 Multi-view Equal Dense Top-N
      └─ Kiwi BM25 Sparse Top-N
                    ↓
              Candidate Union
                    ↓
         Candidate Pool (Stage 2-3)
                    ↓
     Query-Case Interaction (다음 Stage)
```

## 왜 Stage 2-2 Gate를 사용하지 않는가

Stage 2-2 Gated Fusion v1은 LOQO Dev 결과에서 Equal Fusion보다 Recall이 낮아
현재 구현은 채택하지 않았다.

따라서 Hybrid Retrieval 자체의 효과를 보기 위해 Dense leg는
**Stage 2-1 Multi-view Equal Dense**를 사용한다.
실패한 Gate와 Hybrid를 동시에 결합하면 어느 요소가 결과에 영향을 주었는지 분리하기 어렵다.

## 통제 조건

고정:
- Dataset: `AX0001~AX0100`
- Dev Query: `GTQ001~GTQ010`
- Ground Truth: Dev Ground Truth v1
- Generated Perspective: Stage 1 MP Dense에서 실제 생성된 Perspective replay
- LLM 재호출 없음
- Branch query: Perspective title + description only
- Dense leg: Stage 2-1 Multi-view Equal Dense의 기존 branch ranking 재사용
- Sparse leg: Kiwi + BM25
- Sparse Case document: `Business Problem + AX Target Task + Business Context`
- Gold threshold: relevance >= 3

변경:
- Dense-only Candidate Retrieval
- → Dense + Sparse Candidate Union

## 공정한 검색 슬롯 예산

Hybrid가 단순히 더 많은 후보를 봤기 때문에 유리해지는 것을 막기 위해
**retrieval slot budget**을 맞춘다.

| Hybrid | 동일 슬롯 Dense-only 비교군 |
|---|---|
| Dense Top-5 + BM25 Top-5 | Dense Top-10 |
| Dense Top-10 + BM25 Top-10 | Dense Top-20 |
| Dense Top-20 + BM25 Top-20 | Dense Top-40 |

각 Generated Perspective branch에서 위 규칙을 적용한 뒤,
Query의 모든 Perspective branch candidate를 union한다.

Dense와 Sparse가 같은 Case를 찾으면 candidate는 한 번만 보존하되
`dense_rank`, `sparse_rank`, source provenance를 함께 기록한다.
중복 때문에 Hybrid의 unique candidate 수가 Dense-only보다 작아질 수 있으며,
이를 별도 diagnostic으로 기록한다. 중복 슬롯을 사후 보충하지 않는다.

## Primary Metric

각 Query × Run × leg_k에 대해:

- Hybrid Candidate Recall
- Dense-only Same-slot Candidate Recall
- Recall Delta

`Candidate Recall = |Candidate Pool ∩ Gold| / |Gold|`

여기서 `leg_k`는 각 retriever가 가져오는 후보 수이다.
Hybrid 총 retrieval slot은 branch당 `2 × leg_k`이다.

## Diagnostics

- Gold gained / lost / net vs same-slot Dense-only
- Hybrid unique candidate count
- Dense-only unique candidate count
- Dense/Sparse branch overlap count
- Dense/Sparse branch Jaccard
- Perspective Coverage of candidate pool
- Strategy Coverage of candidate pool
- candidate provenance(Dense / Sparse / Both)

## 해석 원칙

1. Stage 2-3은 Candidate Retrieval 실험이지 최종 Ranking 실험이 아니다.
2. Hybrid Candidate Recall이 올라가면 Sparse가 Dense의 누락을 보완할 수 있다는 근거로 본다.
3. Candidate Pool이 좋아져도 최종 Top-K가 좋아진다고 바로 주장하지 않는다.
4. 최종 Ranking 개선은 다음 Query-Case Interaction 단계에서 검증한다.
5. Dev 결과를 보고 GT나 retrieval budget을 사후 변경하지 않는다.
6. 같은 Dev 결과에 맞춰 BM25/Dense 비율을 임의 튜닝하지 않는다.
