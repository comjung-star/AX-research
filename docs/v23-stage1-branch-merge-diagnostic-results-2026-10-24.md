# AX v2.3 Stage 1 — Branch-preserving Final Top10 Merge Exploratory Results

작성: 2026-10-24
사전 고정 진단 프로토콜: [v23-stage1-branch-merge-diagnostic-protocol-2026-10-24.md](v23-stage1-branch-merge-diagnostic-protocol-2026-10-24.md)
원본: `release/ax-v2.3-stage1-to4-dev-20261023`, 기존 GitHub Actions 실행 `39952604227`.
**이 문서는 사전 정의한 3개 결합 대안을, 원래 동결된 Stage 1 검색 랭킹에 적용하여 재선정한 탐색적 Dev 재분석 기록이다. 독립 Held-out Test/인간 Gold가 아니고 새 LLM/BGE 임베딩 실행도 아니다.**

## 1. 실험 구조

- 코퍼스 84건, 질문 10개, MP 질문별 3회, 97개 generated perspectives, 저장된 BGE-M3 dense branch 전체 8,148행(97×84), AI-Silver `qrels=2520`.
- Original query single Dense 1회(rank 0) vs 각 MP run(1/2/3), Top10을 **동일한 10개 unique 사례**로 제한.
- 30개 baseline MP Top10을 원래 branch-balanced round-robin으로 재생성한 결과 **30/30 정확히 일치**.
- B0: original Branch-balanced unique.
- C1: 모든 생성 관점에 선행 최소 1개 사례 배정한 뒤, 개별 branch의 local Top20 후보 합집합 중 **branch local Top10에 등장하는 관점 수가 많은 사례**를 우선; 동률 best local rank, Top20 평균 등장 rank, case ID.
- C2: 동일 관점별 최소 1개 배정 후, 관점 branch별 84개 cosine-score의 z-score를 계산하여 후보의 최대 z-score를 우선. 동률 branch local Top10 support, best local rank, case ID.
- C3: 동일 관점별 최소 1개 배정 후, 동결 Single Dense의 원본 문제 Top20 순위를 후보 평가에 이용. Top20 밖은 rank=21로 취급. **원문 Dense를 합류시킨 hybrid diagnostic, pure MP가 아님.**
- C1/C2/C3은 정답 관련도/Factor/Strategy/평가 참조 관점 목록 없이 원래 순위와 score만 이용. Ref perspective/qrels는 **후속 평가에서만** 사용.
- 30개 실험 모두 10개의 unique 최종 사례 생성, 모든 branch 최소 1개 후보 기여 확인, 기존 B0 replay 30/30 일치; 내부 산출물 무결성 오류 0.
- Label-informed tuning 없이 프로토콜 3개 방식을 모두 기록. Dev 조건에서 '가장 좋아 보이는' 것을 곧바로 최종 아키텍처로 고정하지 않음.

## 2. 주요 비교 지표

| 방식 | Macro Recall@10 | 참조 관점 Coverage@10 | Single 대비 신규 Silver 관련사례 출현 | Single 관련사례 누락 출현 | 기존 B0 A형 24회 누락 중 회복 | B0 최종 Top10과 평균 달라진 칸 수 |
|---|---:|---:|---:|---:|---:|---:|
| B0 기존 Branch-balanced | 0.452987 | 0.927778 | 19 | 39 | 0/24 | 0.00 |
| **C1 관점 1개 보장 + branch consensus** | **0.477182** | **0.950000** | **23** | **37** | **9/24** | 2.27 |
| C2 관점 1개 보장 + branch z-score | 0.472485 | 0.938889 | 21 | 37 | 4/24 | 1.00 |
| C3 관점 1개 보장 + original Single Dense anchor | 0.542696 | 0.988889 | 5 | 2 | 24/24 | 4.13 |

별도의 **Single Dense**는 `Recall@10=0.533226`, 참조 관점 Coverage 1.000000임.

- C1 vs B0 Recall **+0.024196 = +2.42%p**. 신규 Silver 관련사례 출현 19→23, 누락 39→37. 따라서 C1은 이 Dev 조건에서 **전체 Recall과 신규 발견 건수 양쪽에서 탐색적으로 상승**했다.
- C2 vs B0 Recall **+0.019499 = +1.95%p**. 신규 Silver 관련사례 19→21, 누락 39→37.
- C3 vs B0 Recall **+0.089709 = +8.97%p**; Single Dense 자체 대비 **+0.009470 = +0.95%p**. 그러나 새로운 관련사례 발견 19→5로 감소. **Single Dense 랭킹을 직접 사용하므로, 이 결과를 MP 검색 독립 우월성으로 주장할 수 없음**. C3는 anchor/trade-off 진단군.
- C1은 앞서 발견한 A형(각 branch local Top10에 있음에도 최종 Top10에서 빠진 Single 관련사례) 24회 중 9회를 최종 포함시켰으나, 동시에 기존 B0 Top10의 Silver 관련 출현 11회를 잃고 그 밖의 관련 출현 17회를 새로 얻었다. 즉 '복구 9'가 순수 9개 개선이 아니라 **선정 변화의 한 측면**임.
- C1 MP Top10의 Silver 양성 중 단 하나의 참조 관점에서만 양성인 사례 출현 47회, B0 39회, C2 43회, C3 45회. 이는 **선택된 관점 고유 사례의 총 출현 수**로 Single에서만의 추가 발견 수는 아님.

**주의:** Macro Recall은 질문당 3회 MP 결과의 평균을 낸 후 10개 질문에서 macro 평균. 출현 건수는 질문×반복의 합산이므로 사례의 독립 표본 N이 30이나 39가 아니다. v2.3의 AI-Silver 관련도는 인간 승인 Gold나 독립 Test가 아니다.

## 3. 질문별 Recall@10 (질문별 3회 MP 평균)

| 질문 | B0 | C1 | C2 | C3 |
|---|---:|---:|---:|---:|
| V21D001 고객 문의 | 0.2381 | 0.2222 | 0.2222 | 0.3333 |
| V21D002 이메일·후속조치 | 0.4000 | 0.3667 | 0.4000 | 0.5667 |
| V21D003 지식 검색·재사용 | 0.2549 | 0.2549 | 0.2549 | 0.2353 |
| V21D004 문서 심사 | 0.4000 | **0.4500** | 0.4167 | 0.4000 |
| V21D005 데이터 사일로 | 0.1667 | **0.3333** | 0.2222 | 0.6667 |
| V21D006 상품 탐색 | 0.5833 | 0.5417 | **0.6250** | **0.6250** |
| V21D007 구매·견적 | 0.4444 | **0.5000** | 0.4444 | 0.3333 |
| V21D008 예측·계획 | 0.8000 | 0.8000 | **0.8667** | 0.9333 |
| V21D009 기업 AI 확산 | 0.2424 | **0.3030** | 0.2727 | 0.3333 |
| V21D010 제조 데이터 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |

C1에서 전 질문이 개선된 것은 아님. V21D001, V21D002, V21D006은 B0보다 하락. 따라서 이 진단의 평균 성능만으로 C1의 일반적 우월성을 주장하면 안 된다.

## 4. 연구 해석

- **사실:** branch-wise retrieved-but-dropped 원인은 실제로 있었다. Label-blind C1에서 기존 B0 A형 누락 24회 중 9회를 회복하였고, 동시에 Single Dense 기준 새 양성 발견 19→23으로 증가했다.
- **동시에:** C1 Recall@10=0.4772는 여전히 Single Dense=0.5332에 미달. 더 나은 결합만으로 모든 문제를 해결한 것은 아니다.
- **관점 다양성:** C1에서 참조 관점 coverage와 고유 관점 양성 선택 출현이 상승했지만, 전체 관점 품질과 **기존 3개 Reference 밖의 Novel Valid Perspective**는 독립적으로 평가하지 않았다.
- **C3 trade-off:** 원문 단일 검색 순위를 최종 후보 우선순위로 사용하면 핵심 관련사례 보존은 늘지만, MP만의 새로운 관련 사례 기여는 작아진다. 이 기법은 '관점별 동등 분배'의 단순 대체 해법이 아니다.
- **논문 아키텍처:** 교수 제안인 분기 보존, Multi-view/Gated Fusion, Hybrid candidate union, Query–Case interaction 등의 후속 단계와 구분해야 한다. C1/C2는 **Stage 1 합병 메커니즘의 실험적 진단 대안**, C3는 원문 anchor control이며 RRF는 사용하지 않았다. 성능 우세를 교수 제안 아키텍처의 정식 구성 변경으로 오인하지 않는다.

## 5. 후속 연구 행동

1. C1이 회복한 A형 사례와 다른 신규 관련 사례를 맞교환한 사례를 질의별 대조하고 유용성/관점 근거를 확인.
2. 가능하다면 **독립적인 새 Dev 질문** 또는 최종 고정 후 held-out Test에서 B0/C1/C2를 동일 코퍼스·검색 예산으로 재평가. 이번 10개 Dev로 규칙을 고정했다면 이를 Test로 재사용하지 말 것.
3. Stage 2의 제안된 gated fusion으로 이동할 때는 관점별 점수·branch provenance를 유지하고 C1 결과는 **진단 baseline**으로만 비교.
4. Frozen v2.3 데이터셋, AI-Silver, 기존 Stage1~4 결과와 원래 branch 검색 순위는 절대 재작성하지 않는다.

## 6. 최소 재계산 산식

각 (q,r): `S=SingleTop10(q)`, `M=B0/C1/C2/C3 Top10(q,r)`, `G=union over 3 reference perspectives of relevant(case)>=3`.
- `Recall(q,r) = |M∩G|/|G|`
- `MP-only relevant = |(M\\S)∩G|`
- `Single-only relevant = |(S\\M)∩G|`
- `Reference coverage = (# answerable reference perspectives with ≥1 case in M) / (# answerable reference perspectives)`; Silver positives 0개인 P2 in V21D007 is denominator-excluded according to historical Stage1 metric.
- A형 복구 = B0에 없고 S 및 G에 있으며 적어도 하나의 원래 branch local Top10에 들어 있던 사례를 새로운 M이 선택한 횟수.

**재현 범위:** 원래 저장된 query/branch 검색 랭킹과 고정 qrels를 읽어 in-place 변경 없이 순위를 재선정하여 평가했음. 프로토콜 문서는 계산 전에 커밋함. 실제 원래 Stage 1 실행을 다시 수행했다고 주장하지 않음.
