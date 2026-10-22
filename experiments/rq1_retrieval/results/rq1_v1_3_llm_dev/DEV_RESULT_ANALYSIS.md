# RQ1 v1.3 Dev Result Analysis

실행일: 2026-10-22  
Workflow: `39708745221` — **SUCCESS**  
결과 커밋: `7bfd8edb49295ff842f1aa9ddd4bd6bef6110d3b`

## 1. 실행 조건

Frozen v1.3 조건을 변경하지 않고 실행했다.

- Dataset: AX0001~AX0100 / 100 cases
- Dev Query: GTQ001~GTQ010 / 10 queries
- Query input: Business Problem only
- Case input: Problem + Task + Context only
- Single BM25: Kiwi
- Single / Multi-Perspective Dense: BAAI/bge-m3
- LLM: gpt-6-luna
- temperature: API default / parameter omitted
- LLM repeat: Query별 3회
- Runtime Perspective: 2~5개 동적 생성
- branch query: Perspective title + description only
- final selection: branch-balanced unique
- K: 5 / 10 / 20

`OPENAI_API_KEY`는 GitHub Actions Secret에서 주입했고 실제 API preflight가 성공했다.

## 2. Recall 결과

| System | Recall@5 | Recall@10 | Recall@20 |
|---|---:|---:|---:|
| Single BM25 | 0.3643 | 0.5119 | 0.6446 |
| Single Dense | 0.3575 | 0.5176 | **0.6947** |
| GPT-only | **0.4270** | **0.6650** | **0.8748** |
| Multi-Perspective BM25 | 0.3063 | 0.4464 | 0.6547 |
| Multi-Perspective Dense | 0.3233 | 0.5027 | 0.6565 |

### RQ1 핵심 비교: Single Dense vs Multi-Perspective Dense

| K | Single Dense | MP Dense | Delta |
|---|---:|---:|---:|
| 5 | 0.3575 | 0.3233 | -0.0342 |
| 10 | 0.5176 | 0.5027 | -0.0149 |
| 20 | 0.6947 | 0.6565 | -0.0382 |

Dev 평균 Recall에서는 Multi-Perspective Dense가 Single Dense를 이기지 못했다.

따라서 현재 Stage 1 결과만 놓고 보면
**“Perspective 분해가 동일 Dense backbone의 총 Gold Recall을 높인다”는 가설은 지지되지 않았다.**

다만 Query별로는 일부 개선이 존재한다.
- @5: 2개 Query 개선 / 2개 동률 / 6개 하락
- @10: 4개 개선 / 0개 동률 / 6개 하락
- @20: 1개 개선 / 4개 동률 / 5개 하락

## 3. GPT-only

GPT-only가 모든 K에서 가장 높은 Recall을 기록했다.

- Recall@5: 0.4270
- Recall@10: 0.6650
- Recall@20: 0.8748

3회 반복의 run-level macro Recall 범위:
- @5: 0.4148 ~ 0.4452
- @10: 0.6569 ~ 0.6748
- @20: 0.8472 ~ 0.8932

temperature를 직접 고정하지 못했지만 3회 반복에서 전체 평균 성능이 극단적으로 흔들리지는 않았다.

주의:
GPT-only는 100개 Case를 LLM이 직접 읽고 판단하므로 Retrieval system과 계산비용/추론방식이 다르다. 성능 비교군으로 해석하되 효율까지 동일한 시스템으로 해석하지 않는다.

## 4. Perspective / Strategy Coverage Ceiling Effect 재확인

모든 시스템에서 일반 Perspective Coverage와 Strategy Coverage가 @5부터 1.0이었다.

따라서 현재 Dev Ground Truth에서는 두 지표가 시스템 차이를 구분하지 못한다.

기존 Primary metric 정의는 변경하지 않고, 사전에 추가한 Dev diagnostic인 Exclusive Perspective Coverage를 함께 계산했다.

| System | Exclusive@5 | Exclusive@10 | Exclusive@20 |
|---|---:|---:|---:|
| Single BM25 | 0.3333 | 0.7333 | 0.9167 |
| Single Dense | **0.4667** | 0.6167 | 0.7333 |
| GPT-only | 0.4444 | **0.7167** | **0.9167** |
| MP BM25 | 0.3389 | 0.6056 | 0.8722 |
| MP Dense | 0.4000 | 0.6222 | 0.8389 |

MP Dense는:
- @5에서는 Single Dense보다 낮음
- @10에서는 거의 동일
- @20에서는 0.8389 vs 0.7333으로 약 +0.1056

즉 Multi-Perspective는 총 Recall을 높이지는 못했지만, 깊은 순위(@20)에서는 서로 다른 Reference Perspective의 고유 사례를 더 넓게 회수하는 신호가 나타났다.

이 값은 **추가 diagnostic**이며 Held-out Test의 Primary metric으로 자동 승격하지 않는다.

## 5. Gold gained / lost

MP Dense가 Single Dense와 다른 Gold를 실제로 찾는지 확인했다.

| K | Gained | Lost | Net |
|---|---:|---:|---:|
| 5 | 23 | 35 | -12 |
| 10 | 24 | 33 | -9 |
| 20 | 34 | 46 | -12 |

해석:
- Perspective 분해가 Single Dense가 놓친 Gold를 실제로 새로 회수하는 것은 확인됨
- 그러나 같은 K budget에서 그보다 더 많은 기존 Gold를 잃음
- 현재 branch-balanced unique 방식은 **새로운 영역 탐색과 기존 핵심 Gold 보존 사이의 trade-off**를 보임

## 6. Branch 진단

### Multi-Perspective Dense
- 30 Query×Run 중 Perspective 수:
  - 3개: 27회
  - 4개: 3회
- 평균 Perspective 수: 3.10
- 평균 branch Top-20 Jaccard: 0.3757
- 평균 duplicate candidate rate: 0.4218

### Multi-Perspective BM25
- Perspective 수:
  - 2개: 2회
  - 3개: 25회
  - 4개: 3회
- 평균 Perspective 수: 3.03
- 평균 branch Top-20 Jaccard: 0.2650
- 평균 duplicate candidate rate: 0.3276

branch 결과가 100% 동일하게 반복되는 문제는 없다.
다만 Dense branch는 BM25보다 branch 간 중복이 더 높았다.

## 7. Dev 단계 결론

현재 RQ1 v1.3 Dev 결과는 다음처럼 해석한다.

1. **Single Dense 대비 MP Dense의 평균 Recall 개선은 확인되지 않았다.**
2. MP Dense는 Single Dense가 놓친 Gold를 추가로 찾지만, 동일 K에서 잃는 Gold가 더 많았다.
3. @20 Exclusive Perspective Coverage는 MP Dense가 Single Dense보다 높아, Perspective 분해의 **관점 다양성 회수 가치**는 일부 신호가 있다.
4. 일반 Perspective Coverage / Strategy Coverage는 ceiling effect 때문에 Dev 변별력이 없다.
5. GPT-only는 가장 높은 Recall을 보였다.
6. Ground Truth는 결과에 맞춰 수정하지 않는다.
7. 다음 단계에서는 실패를 숨기거나 Prompt를 사후조정하기보다, **왜 branch-balanced selection이 핵심 Gold를 잃는지와 다음 Multi-view / Gated Fusion / Hybrid Retrieval이 이 trade-off를 보완할 수 있는지**를 분석한다.

## 8. 다음 분석 포인트

- Query별 MP Dense 개선/악화 원인 분석
- Generated Perspective의 내용 품질 및 Reference Perspective 대응 관계 분석
- branch별 Gold 분포 분석
- branch-balanced unique가 높은 Single Dense 사례를 밀어내는 패턴 분석
- Multi-view / Gated Fusion / Hybrid Retrieval로 넘어가기 전 Stage 1 결과를 연구계획서 논리와 연결
