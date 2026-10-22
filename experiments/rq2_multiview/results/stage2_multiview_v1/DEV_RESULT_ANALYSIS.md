# Stage 2-1 Multi-view Dense Dev Result Analysis

## 1. 실험 질문

Stage 1 Multi-Perspective Dense와 **완전히 동일한 Generated Perspective**를 replay한 상태에서,
AX Case를 하나의 연결 문서로 임베딩하는 대신
`Business Problem / AX Target Task / Business Context`를 각각 임베딩하고
세 cosine score를 동일가중 평균하면 검색 성능이 개선되는가?

이 실험에서는 LLM을 다시 호출하지 않았다.
따라서 Perspective sampling 차이를 통제하고 Multi-view 표현 방식의 효과만 비교한다.

## 2. 비교 구조

### Stage 1 MP Dense

```text
Generated Perspective
→ [Problem + Task + Context] concatenated Case text
→ BGE-M3
→ cosine
→ branch-balanced unique
→ Top-K
```

### Stage 2-1 Multi-view Equal Dense

```text
Same Generated Perspective
→ query embedding
→ Problem embedding  → cosine
→ Task embedding     → cosine
→ Context embedding  → cosine
→ equal mean (1/3, 1/3, 1/3)
→ branch-balanced unique
→ Top-K
```

## 3. Macro Recall

| System | Recall@5 | Recall@10 | Recall@20 |
|---|---:|---:|---:|
| Stage 1 MP Dense | 0.323267 | 0.502667 | 0.656546 |
| Stage 2-1 Multi-view Equal Dense | 0.323467 | 0.499295 | 0.659976 |
| Delta | +0.000200 | -0.003372 | +0.003430 |

Percentage-point 관점:
- @5: 약 **+0.02 pp**
- @10: 약 **-0.34 pp**
- @20: 약 **+0.34 pp**

즉 동일가중 Multi-view 분리만으로는 **뚜렷한 Recall 개선이 확인되지 않았다.**

## 4. Gold gained / lost vs Stage 1 MP Dense

30개 Query×Run 기준 합계:

| K | 새로 얻은 Gold | 잃은 Gold | Net |
|---|---:|---:|---:|
| @5 | 20 | 19 | +1 |
| @10 | 28 | 27 | +1 |
| @20 | 25 | 27 | -2 |

Multi-view 표현으로 순위가 실제로 바뀌고 새 Gold도 유입되지만,
동시에 비슷한 수의 기존 Gold가 빠져 전체 성능은 거의 상쇄됐다.

## 5. Branch 진단

| Diagnostic | Stage 1 MP Dense | Stage 2-1 Multi-view Equal |
|---|---:|---:|
| Mean branch Top-20 Jaccard | 0.3757 | 0.4035 |
| Mean duplicate candidate rate | 0.4218 | 0.4340 |

Stage 2-1은 branch 간 결과 overlap과 중복 후보 비율이 오히려 소폭 증가했다.

일반 Perspective Coverage와 Strategy Coverage는 Stage 2-1에서도 @5부터 1.0으로
기존 Dev benchmark의 ceiling effect가 지속됐다.

## 6. 해석

이번 결과가 의미하는 것은 "Multi-view가 불필요하다"가 아니다.

Stage 2-1은 세 View를 분리했지만 각 Query/Perspective에 상관없이
`Problem / Task / Context`를 항상 동일한 1/3 가중치로 결합했다.

따라서 현재 결과는 다음 수준으로 해석한다.

> **Case View를 단순히 분리하고 동일 비중으로 평균하는 것만으로는
> Stage 1의 검색 한계를 해결하지 못했다.**

실제로 Query에 따라 중요한 View는 달라질 수 있다.
예를 들어 지식 검색 문제에서는 Problem/Context가 중요할 수 있고,
문서 처리나 조달 문제에서는 Task가 더 중요할 수 있다.

## 7. 다음 단계

다음 controlled ablation은 **Stage 2-2 Gated Fusion / Attention**이다.

목표:
- Query/Perspective별로 Problem / Task / Context의 중요도를 동적으로 조정
- Stage 2-1의 고정 1/3 가중치와 비교
- 동일 Perspective replay / 동일 K / 동일 final selection을 유지하여 Gate 효과만 분리

주의:
- GTQ001~GTQ010은 Dev이므로 같은 Query의 Gold label을 학습과 평가에 동시에 쓰지 않는다.
- 학습형 Gate를 사용할 경우 Query 단위 분리를 적용해 leakage를 방지해야 한다.
- Dev에 수동으로 최적화한 고정 가중치를 "Gated Fusion"으로 간주하지 않는다.

## 8. 결론

Stage 2-1 결과:

> **Multi-view 분리 자체는 검색 순위를 변화시키지만, 동일가중 평균만으로는
> Recall을 의미 있게 높이지 못했다. 따라서 다음 실험에서는 View별 중요도를
> Query/Perspective에 따라 조정하는 Gated Fusion의 추가 효과를 검증한다.**
