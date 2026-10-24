# 교수님 Search Core Dense + Sparse 후보 보존형 하이브리드 — 실제 실행 결과 (v2.3 Dev)

- 실험일: **2026-10-24**
- 코드 브랜치: \`experiment/v23-professor-hybrid-preserving-20261024\`
- 실제 실행: GitHub Actions [40070758111](https://github.com/comjung-star/AX-research/actions/runs/40070758111), **SUCCESS** (unit tests, frozen Dev replay, separate result commit/push).
- 프로토콜: \`docs/v23-professor-hybrid-preserving-protocol-2026-10-24.md\` (실행 전에 별도 commit)
- 구현: \`scripts/v23_professor_hybrid_preserving.py\`
- 결과: \`experiments/v23_hybrid_preserving/summary.json\`, \`candidate_pool_metrics.csv\`, \`candidate_case_provenance.csv\`, \`rankings_perspective_and_global.csv\`, \`final_diagnostic_metrics.csv\`, \`loqo_training_audit.csv\`
- 레거시 코퍼스/AI 평가/Stage 1~4 frozen 파일 **수정하지 않음**.

## 1. 교수 원안과 연결 상태

LLM-generated perspective(기존 97개 고정) → Problem / Task / Context **3-view equal-mean dense** → **Dense + Kiwi BM25** per-branch hybrid retrieval → **중복제거 Candidate Union(상위 M 슬롯)** → LOQO 학습의 **Query–Case Interaction MLP** → **관점별 Top-K**를 완전 저장했다. 검색된 사례의 Dense/BM25/BOTH 유입 경로와 관점 ID를 저장했다.

모든 실험은 기존 stage1 frozen BGE-M3 view/branch embedding과 BM25 전체 순위를 재생한다. **LLM 및 BGE-M3 추론을 새로 호출하지 않는 재현 실행**이다. Original professor diagram에서 Dense+Sparse Hybrid인 것과, 원문 Single Dense+MP Dense Hybrid라는 추가 가설을 구분한다. **Graph retrieval(전체 FAME-AX), learned Gate/Attention, Stage3/4 end-to-end evidence fusion은 이번 Search Core 재현에서 실행하지 않았다.** 따라서 *교수의 완전한 FAME-AX end-to-end 모델이 검증되었다*고 주장할 수 없다.

## 2. 후보 확보 성능 — 10개 질문, 각 3회 Dev 평균

| 한 관점의 검색 예산 | 후보 합집합 평균(전 관점 중복제거) | Silver 후보 Recall | 동일 슬롯 Dense-only Recall |
|---|---:|---:|---:|
| Dense 20 | 38.30 | **79.98%** | 79.98% |
| Dense 10 + BM25 10, 기존 대체형 | 32.53 | **69.32%** | 79.98% |
| Dense 20 + BM25 10, **보존형** | 46.07 | **82.73%** | **88.65%** (Dense 30) |
| Dense 30 | 51.10 | **88.65%** | 88.65% |
| Dense 20 + BM25 20, **보존형** | 50.03 | **84.46%** | **92.40%** (Dense 40) |
| Dense 40 | 60.60 | **92.40%** | 92.40% |

- 동일 Dense 20 검색 결과를 전부 유지한 뒤 BM25 20을 추가할 때 **후보 Recall 79.98→84.46%, +4.48%p**, 30개 query×run에서 **새로운 Silver 관련 사례 17회 출현**, 해당 질문×run **11회**. Dense Top20이 이미 찾은 사례는 한 개도 후보에서 탈락하지 않는 **집합 포함** 성질을 검증했다.
- 다만 **동일 슬롯 공정 비교**에서는 Dense20+BM2520 (40개 검색 슬롯)이 Dense40보다 **7.95%p 낮음**. Dense20+BM2510 (30개 슬롯)도 Dense30보다 **5.91%p 낮음**.
- 보존형 후보 합집합의 최종 *중복제거* 개수가 Dense-only 40보다 작을 수 있음 (50.03 vs 60.60). 40 retrieval slots/branch를 맞춘 결과이지만 실제 unique 후보의 규모까지 같다는 뜻은 아님.
- Dev 10문제 모두에서 개선되지는 않음. V21D003(업무 지식 검색)은 Dense20에 비해 새로운 관련 후보가 3회 합산 9회 나왔으나, 일부 질문은 BM25가 관련 후보를 전혀 새로 가져오지 못함.
- 위 횟수는 10 질문×3 반복 **사례의 출현 횟수 합계**지 서로 다른 독립 사례 ID 수나 사람 검증 Gold 수가 아님.

## 3. Query–Case Interaction 재평가 (Top10; 전역 결과는 진단 비교용)

모든 관점별 후보를 유지하고 MLP로 각 관점 내 관련도를 재평가한다. 출력 \`rankings_perspective_and_global.csv\`에서 **per-perspective** Top5/10/20 기록을 정식 비교 대상으로 보존하며, 이하 숫자는 다른 시스템과 동일 최종 출력 예산으로 비교하기 위해 branch-balanced unique 전역 Top10을 **부가적으로** 산출한 것이다. 교수 원안이 전역 Top10을 요구한다는 의미가 아니다.

| 후보 방식 | 비학습 RRF 전역 Recall@10 | LOQO Query–Case MLP 전역 Recall@10 |
|---|---:|---:|
| Dense20 | 42.40% | 12.01% |
| 기존 Dense10 + BM25 10 | 41.44% | 15.62% |
| **보존형 Dense20 + BM25 20** | **32.14%** | **8.40%** |
| Dense40 | **42.40%** | **6.39%** |

- 이 MLP는 다른 9개 Dev 질문만 학습하고 대상 질문의 Gold는 사용하지 않았다. **학습 대상/프로젝션 방식/하이퍼파라미터**는 진단 프로토콜에 기록했으며, 10개 폴드 모두 held query in training = 0으로 검증했다.
- 현 MLP는 학습에 실패하거나 일반화가 좋지 못한 것으로 평가해야 한다. 보존형 후보가 늘었다는 것만으로 최종 재정렬이 좋아지지 않는다. **QCI 성능 문제를 별도 해결**해야 한다.
- RRF도 확장된 후보에서 유효 후보의 순서를 충분히 잘 보존하지 못했다. 더 넓은 pool을 채택하더라도 candidate-to-final stage에 검증된 랭킹/필터가 필요하다.
- **주의**: 이번 LOQO MLP는 84개 전체 사례 후보로 학습하는 새로운 축소 실험 구현이며, 과거 Stage2-4의 특정 후보 풀 기반 MLP와 학습 설정이 동일하지 않다. 두 실험 숫자를 인과적으로 직접 비교하지 않는다.

## 4. 실험 판정

1. **구현/검증 성공:** 교수 Search Core가 지정한 *관점별 Dense+Sparse 후보 결합 → 중복 제거 → neural interaction → 관점별 Top-K* 경로를 별도 실험으로 실제 실행하고, Dense 후보 보존 및 provenance, LOQO 분리 조건 검증에 성공.
2. **Dense 보존 효과 확인:** 기존 10+10 대체형에 비해 20+20 보존형의 후보 양성 Recall은 증가. 같은 Dense20에 BM25를 더해 후보를 넓히면 신규 Silver 관련 사례도 발견.
3. **하이브리드의 공정 우월성 미입증:** 같은 retrieval-slot 총합의 Dense-only보다 후보 Recall이 낮음. Sparse가 늘 보완해 주는 것은 아님.
4. **후속 neural ranking 개선 미입증:** Query–Case MLP의 Dev Recall 성능이 낮음. 단순 모델 정확도뿐 아니라 후보 pool과 재정렬의 정합성, 배치, 손실함수, 임베딩 적합성/negative mining이 새로운 독립 연구 이슈. 성능 수치가 좋지 않다고 자료/GT를 바꾸지 않음.
5. **교수 아키텍처의 나머지 모듈 미검증:** 전체 FAME-AX Graph, learned gate, evidence pooling, factor/Wald, LLM 전략 추천을 이번 분기에서 end-to-end 새로 실행하지 않음.

## 5. 다음 논의의 초점

새로운 실험을 또 쌓기 전에 **후보 검색과 QCI 랭킹을 분리해 실패 사례를 살펴보자**. 특히 전체 관련 사례가 후보군에 존재하는데도 후단 점수에서 밀리는 경우와, BM25가 진짜 새로운 문제 관점에 관련된 사례를 발굴했는지의 차이를 점검할 필요가 있다. 교수 원안의 Candidate Union Top-M과 관점별 Retrieved Cases Top-K 수치는 성능을 보고 사후 선택하지 말고 별도 protocol을 고정하여 후속 검증해야 한다.

모든 수치는 **v2.3 AI-Silver 개발평가**이며 최종 Test, 독립적 인간 Gold, 교수원안의 최종 실효성 입증이 아님.
