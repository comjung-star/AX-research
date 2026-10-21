# RQ1 v1.2 Baseline Validation

실행일: 2026-10-21

## 실행 검증

GitHub Actions에서 Frozen v1.2 조건으로 Single-query BM25와 Single-query Dense를 실제 실행했다.

- Dataset: AX0001~AX0100 / 100 cases
- Dev Query: GTQ001~GTQ010
- BM25 tokenizer: Kiwi
- Dense: BAAI/bge-m3
- Query input: business_problem_query only
- Case input: Problem / Task / Context only
- K: 5 / 10 / 20

Workflow run: `39570488930` — SUCCESS

## Macro Recall

| K | BM25 | Dense | Dense-BM25 |
|---:|---:|---:|---:|
| 5 | 0.3643 | 0.3575 | -0.0069 |
| 10 | 0.5119 | 0.5176 | +0.0057 |
| 20 | 0.6446 | 0.6947 | +0.0501 |

Query별 Dense vs BM25:
- @5: Dense 우세 3 / 동률 4 / BM25 우세 3
- @10: Dense 우세 5 / 동률 2 / BM25 우세 3
- @20: Dense 우세 4 / 동률 3 / BM25 우세 3

해석:
- @5에서는 두 방식이 사실상 비슷하다.
- @10도 평균 차이가 매우 작다.
- @20에서는 Dense가 약 +5.0%p 높아, 더 깊은 순위에서 의미기반 회수 이점이 나타난다.
- 다만 Dev Query 10개뿐이므로 통계적 우월성으로 해석하지 않는다.

## 발견된 Ceiling Effect

기존 `Perspective Coverage@K`와 `Strategy Coverage@K`가 BM25/Dense 모두 **@5부터 전 Query 1.0**이었다.

이는 구현 오류라기보다 현재 Ground Truth의 특성과 metric 정의가 결합된 결과로 확인했다.
Reference Perspective 사이에 공유 Gold Case가 존재하고, Coverage는 Perspective당 관련 Case 1개만 있어도 covered로 판단하기 때문에 Single-query baseline도 매우 쉽게 100%에 도달한다.

따라서 현재 Dev에서는 이 두 지표만으로 Multi-Perspective의 관점 회수 이득을 구분하기 어렵다.

## 추가 Dev Diagnostic: Exclusive Perspective Coverage

Primary metric을 바꾸지는 않고, **각 Reference Perspective에만 속하는 Gold Case**를 실제로 회수했는지 보는 진단지표를 추가 계산했다.

정의:
- 특정 Perspective의 Gold 중 다른 Perspective Gold에는 포함되지 않는 Case를 Exclusive Gold로 정의
- Exclusive Gold가 1개 이상 존재하는 Perspective만 분모에 포함
- Top-K가 해당 Exclusive Gold를 하나 이상 회수하면 그 Perspective를 covered로 판정

Macro 결과:

| K | BM25 | Dense |
|---:|---:|---:|
| 5 | 0.3333 | 0.4667 |
| 10 | 0.7333 | 0.6167 |
| 20 | 0.9167 | 0.7333 |

이 지표는 기존 Perspective Coverage와 달리 saturation되지 않아 Multi-Perspective가 **서로 다른 관점의 고유 사례를 추가로 회수하는지** 분석하는 데 유용하다.

주의:
- 본 지표는 Dev 결과를 본 뒤 Primary metric을 바꾼 것이 아니다.
- 기존 Recall / Perspective Coverage / Strategy Coverage는 그대로 유지한다.
- Exclusive Perspective Coverage는 ceiling effect를 설명하기 위한 **추가 진단 지표**로만 사용한다.
- 최종 논문에서 핵심 평가 지표로 승격하려면 Held-out Test 설계 전에 별도로 Freeze해야 한다.

## Baseline 결론

현재 baseline 자체는 정상 동작한다.

1. BM25와 Dense가 동일 입력/동일 Ground Truth/동일 K로 실행됨
2. Recall은 Query와 K에 따라 차이가 나타나므로 정상적인 변별력이 있음
3. Dense는 특히 @20에서 BM25보다 높은 평균 Recall
4. 기존 Perspective Coverage와 Strategy Coverage는 Dev에서 ceiling effect 발생
5. 이후 Multi-Perspective 분석에서는 Recall과 함께 Gold gained/lost/net, branch overlap, Exclusive Perspective Coverage를 같이 확인할 필요가 있음
