# Stage 2-3 Hybrid Retrieval Dev Result Analysis

## 1. 질문

교수 제안 Search Core의 Dense + Sparse Candidate Union이,
같은 retrieval slot budget에서 Multi-view Dense-only보다
관련 AX Case를 Candidate Pool에 더 많이 포함하는가?

## 2. 통제

- AX0001~AX0100 고정
- GTQ001~GTQ010 Dev 고정
- Dev Ground Truth v1 고정
- Stage 1 Generated Perspective 그대로 replay
- Dense: Stage 2-1 Multi-view Equal Dense ranking 재사용
- Sparse: Kiwi BM25
- LLM 재호출 없음
- Stage 2-2 Gate v1 미사용
- Query-Case Interaction 미사용

Stage 2-3은 **최종 ranking 실험이 아니라 candidate retrieval 실험**이다.

## 3. 동일 검색 슬롯 비교

| Hybrid | Dense-only comparator |
|---|---|
| Dense Top-5 + BM25 Top-5 | Dense Top-10 |
| Dense Top-10 + BM25 Top-10 | Dense Top-20 |
| Dense Top-20 + BM25 Top-20 | Dense Top-40 |

모든 Generated Perspective branch에서 같은 규칙을 적용한 뒤
Query 수준에서 candidate를 union했다.

## 4. Candidate Recall

| leg_k | slots/branch | Hybrid Recall | Dense same-slot Recall | Delta |
|---:|---:|---:|---:|---:|
| 5 | 10 | 0.619099 | 0.649538 | -0.030439 |
| 10 | 20 | 0.780287 | 0.793484 | -0.013196 |
| 20 | 40 | 0.916413 | 0.935577 | -0.019164 |

세 budget 모두 Macro 평균에서는 Hybrid가 Dense-only를 넘지 못했다.

## 5. Gold gained / lost

| leg_k | gained | lost | net |
|---:|---:|---:|---:|
| 5 | 28 | 36 | -8 |
| 10 | 23 | 33 | -10 |
| 20 | 12 | 17 | -5 |

Hybrid는 분명 Dense-only에 없던 Gold를 새로 찾았다.
그러나 같은 retrieval slot budget을 Dense와 BM25에 절반씩 배분하면서
Dense ranking의 더 깊은 Gold를 포기한 손실이 더 컸다.

## 6. Dense / Sparse 보완성

Mean branch Jaccard:
- leg_k=5: 0.3483
- leg_k=10: 0.3122
- leg_k=20: 0.3558

즉 Dense와 BM25가 가져오는 후보가 완전히 중복되는 것은 아니다.
Sparse는 실제로 새로운 후보 영역을 제공한다.

예를 들어 일부 Query/Run에서는 Hybrid가 우위였다.
- GTQ002 run1 leg_k=10: +0.3333 Recall
- GTQ006 run1 leg_k=10: +0.1250 Recall
- GTQ008 run1 leg_k=10: +0.1818 Recall
- GTQ008 run2/run3 leg_k=10: +0.0909 Recall

따라서 "Sparse가 아무 가치가 없다"는 결론은 아니다.

## 7. 해석

현재 결과는 다음을 의미한다.

1. **보완성은 있음**
   - BM25가 Dense가 못 찾은 Gold를 실제로 추가함.

2. **고정 50:50 slot allocation은 비효율적**
   - BM25에 슬롯을 주는 만큼 Dense depth가 줄어들어 더 많은 Gold를 잃는 경우가 발생.

3. **Hybrid Retrieval 전체를 기각할 결과는 아님**
   - 교수 아키텍처에서 Hybrid Retrieval의 역할은 Candidate Pool 확보이고,
     다음 Query-Case Interaction이 실제 relevance를 판단해 Top-K를 만든다.

4. **사후 비율 튜닝은 하지 않음**
   - 같은 Dev 결과를 본 뒤 Dense 70% / BM25 30% 같은 비율을 임의로 맞추면
     과적합된 설계가 될 수 있으므로 v1 결과는 그대로 보존한다.

## 8. 다음 단계

Stage 2-4 Query-Case Interaction:

```text
Perspective q_k
+
Hybrid Candidate c_i
        ↓
[q, c, q⊙c, |q-c|]
        ↓
MLP
        ↓
Relevance Score
        ↓
Perspective-specific Top-K
```

Stage 2-3에서 BM25가 새 후보를 가져오는 것은 확인했으므로,
다음 단계에서는 그 후보 중 실제 Gold를 위로 올리고 불필요 후보를 내릴 수 있는지를 검증한다.

## 9. 현재 결론 한 문장

**Dense와 BM25는 서로 다른 후보를 회수하지만, 동일 검색 슬롯을 50:50으로 단순 배분한 Hybrid Candidate Union은 Dense-only보다 평균 Recall이 낮았으며, 따라서 다음 Query-Case Interaction에서 후보의 relevance를 재평가하는 단계가 필요하다.**
