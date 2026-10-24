# AX 연구 Stage 2: 전체 84개 평가와 Dense·Sparse 후보 축소 비교 결과

실험일 2026-10-24 · 검증된 실제 실행 · Frozen AI-Silver Dev 재생 · 신규 LLM 호출 없음

## 1. 배경
기업 문제를 LLM의 복수 관점으로 분리하고, 각 관점에서 AX 사례를 정밀 매칭하여 개별 Top-K를 산출한다. 교수님 제안의 관점별 결과 보존 방식을 기준으로 비교한다.

## 2. 문제점
이전 Stage1에서는 전역 Top10 병합으로 일부 관련 사례가 탈락했다. 하지만 전 사례를 남기더라도 후단 Query–Case Interaction이 실제 관련 사례를 상위에 선정하는지는 별도로 확인해야 한다.

## 3. 방안 및 설계
84개 AX 사례를 관점마다 전부 평가한 all84 비교군과 Dense20, Dense40, Dense20+Sparse20, 하이브리드와 각 관점별 후보 수를 맞춘 Dense-N, 점수 양수인 Sparse20을 비교했다. 각 관점별 Top5/Top10을 독립 유지했다.

84개 사례, 10개 Dev 질문×3회, 97개 기생성 관점, BGE-M3 임베딩과 Kiwi BM25 기존 순위, AI-Silver 2,520개 라벨을 변경하지 않고 재생했다. Query–Case MLP는 48차원 고정 투영 후 [q,c,q*c,|q-c|] 특징을 쓰는 기존 192→64→1 모델로, 평가 질문을 학습에서 제외하는 LOQO 방식을 사용했다. 후보 방식별로 재학습하지 않았다. 같은 Dense 점수와 RRF로 비학습 대조군도 비교했다.

## 4. 비교 결과

### 후보 단계
| 후보 | 평균 QCI 평가쌍 | 후보 관련사례 Recall |
|---|---:|---:|
| 전체 84개 × 생성 관점 | 271.6 | 100.00% |
| Dense20 | 64.7 | 79.98% |
| Dense40 | 129.3 | 92.40% |
| Dense20+BM25 양성20 | 97.7 | 83.13% |
| 같은 평가량 Dense-N | 97.7 | 89.73% |
| BM25 양성20 | 48.2 | 29.41% |

전체 후보의 100%는 모든 사례를 포함한 결과이지 최종 추천 정확도 100%가 아니다. Dense20+Sparse20은 Dense20보다 확보율이 높지만 같은 평가량 Dense-N보다 6.60%p 낮았다. 여기서 평가쌍 수는 처리시간이 아닌 후단 모델 처리량의 대리지표다.

### 각 관점 Top10 보존 후 결과 합집합 Recall
| 후보 | Query–Case MLP | 동일 후보의 Dense score 정렬 | RRF 정렬 |
|---|---:|---:|---:|
| 전체 84개 | 9.71% | 63.32% | 36.54% |
| Dense20 | 39.04% | 63.32% | 60.51% |
| Dense40 | 19.93% | 63.32% | 47.24% |
| Dense20+BM25 양성20 | 23.51% | 63.32% | 36.54% |
| 비용 동일 Dense-N | 24.57% | 63.32% | 54.33% |
| BM25 양성20 | 23.04% | 27.20% | 28.21% |

## 5. 결론
전체 84개를 관점별로 평가하는 기준 실험과 5개의 후보 축소 실험을 완료했다. **현 QCI 축소형 MLP는 심각한 성능 병목**이며, 전 사례를 평가하면 최종 Recall 9.71%로 단순 3-view Dense 정렬의 63.32%를 크게 밑돈다. Dense20로 후보를 걸러주면 MLP 결과가 39.04%로 개선되지만 Dense 점수 정렬 63.32%보다 낮다. 이는 교수님 원안 전체의 실패가 아니라 현재 학습/표현/재정렬 구현의 실패 신호다. 다음 단계로 기존 데이터 유지와 쿼리 단위 분리 학습을 지키며 MLP 입력·학습 목적·관점별 라벨 정합성을 분석해야 한다.

관점별 Top10 결과는 전역 Top10이 아니다. 97개의 실행시점 관점과 AI-Silver 기준 관점은 1:1로 대응하지 않으므로 결과는 질문 단위 양성 합집합으로 평가했다. 개별 관점의 의미적 적합성 자체를 직접 검증했다고 주장하지 않는다. 인간 Gold나 독립 Test, Graph, learned Gate, Factor Anchor/Wald, Stage3/4 전체 통합 실험은 포함되지 않았다.

## 6. 저장 및 재현
- [사전 실험 프로토콜](v23-stage2-full84-protocol-2026-10-24.md)
- [GitHub Actions 성공 기록](https://github.com/comjung-star/AX-research/actions/runs/40078446507)
- 코드 `scripts/v23_stage2_full84_comparison.py`, 테스트 `tests/test_v23_stage2_full84_comparison.py`
- 결과 `experiments/v23_stage2_full84_comparison/`: `summary.json`, `candidate_metrics_by_query_run.csv`, `candidate_provenance.csv`, `per_perspective_topk.csv`, `final_topk_metrics_by_query_run.csv`, `full84_final_ranking_delta.csv`, `loqo_training_audit.csv`
- 기존 frozen Stage1~4 원본 불변, 새 branch `experiment/v23-stage2-full84-vs-retrieval-20261024`에서만 실행.
