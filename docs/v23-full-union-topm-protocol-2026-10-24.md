# AX v2.3 — 교수님 Candidate Union(Top-M) 사용자 해석 검증 프로토콜

작성: 2026-10-24. **개발 데이터 탐색 실험**, 교수님 답변 전 임시 해석. 기준 원본: `release/ax-v2.3-stage1-to4-dev-20261023`. 별도 분기 `experiment/v23-hybrid-full-union-topm-20261024`. 이 문서의 비교 방법·M·지표는 **이번 새 실험 결과를 보기 전에 고정**한다. 지난 Dev 결과를 이미 참고한 설계이므로 독립적인 사전등록/최종 검증은 아니다.

## 1. 이번에 검증할 해석

원본 그림의 **LLM 생성 관점 → Multi-view Dense + Sparse Retrieval → 모든 검색 결과의 Candidate Union → 중복 제거 → 통합 후보 가운데 Top-M → Query–Case Interaction → 관점별 Top-K → Evidence Pooling** 순서를 구현한다.

- 구별할 점: 여기서 '전체 검색 결과'는 **동일 코퍼스 84건의 Dense 순위표와 Sparse 순위표를 모두 사용하여 점수를 합치는 것**이다. 이 경우 Case ID 합집합은 매번 전체 84건이므로, **Top-M을 다시 고르는 결합 규칙이 반드시 필요**하다.
- 교수님 그림에 **Top-M/Top-K**는 명시되었지만 구체 M/K 및 결합 공식은 없다. RRF·교대 선발은 *학생 연구상의 잠정 구현*, 교수님 승인된 방식이라고 표현하지 않는다.
- 중요: BM25 **점수 0인 사례가 다수**(동결 랭킹에서 8148개 중 6701개)이며, 0점 후보의 알파벳 tie-break 순위를 Sparse의 유효 근거로 취급하면 왜곡된다. BM25 score>0인 경우에만 Sparse의 순위 기여를 인정한다. dense는 모두 코사인 순위가 있음.
- 연구계획서의 '하이브리드'는 **Dense + Sparse**를 명시한다. 원문 단일 Dense + LLM 다중관점 Dense는 **다른 추가 가설**로 본 실험에 섞지 않는다.
- 동결 v2.3 Stage1의 97개 generated perspectives, 84개 실제 AX cases, 10개 Dev query × 3 runs, BGE-M3 embeddings (Problem/Task/Context equal-mean), Kiwi BM25 순위를 정확히 재생. **새 OpenAI/embedding 호출 없음**. 기존 Stage1~4 자료 불변.

## 2. 후보 Pool 선정법과 M (정답 라벨 비사용)

한 perspective branch의 동일 84개 사례 전체 Dense 순위와 전체 Sparse 순위를 처음부터 읽고 case_id로 결합하며, `dense_rank`, `sparse_rank`, sparse_score, sparse_hit, source, branch_id를 유지.

**Top-M 방법 3개를 모두 같은 M으로 비교:**

1. `dense` (비교군): 기존 Multi-view Dense 전순위에서 M개.
2. `rrf` (하이브리드): `1/(60+dense_rank) + 1/(60+sparse_rank)` 단 Sparse는 BM25 score>0인 경우만 가산. 동점은 Dense rank, Case ID로 판정.
3. `interleave` (하이브리드): Dense 상위부터, Sparse **유효점수(>0)** 상위부터 번갈아 중복 없이 1개씩 선택. Sparse 유효점수 후보가 고갈되면 Dense 순위로 보충. 이 방식은 Sparse에서만 발견하는 후보의 최소한의 진입 기회를 보장하는 진단안.

**M = 10, 20, 40, 60, 84 (branch별)**을 사전 고정한다. M=84이면 모든 방법의 후보 집합이 정확히 84건으로 일치하는 sanity check. **M=84의 후보 Recall 100%는 전체 코퍼스를 모두 포함했기 때문이므로 검색 모델 성능 향상으로 주장하지 않는다.** 공식 출력 K = 5,10,20으로 관점별 결과를 따로 보존. 후보 예산 동일 M 하의 Dense-vs-Hybrid 비교가 기본.

## 3. 단계별 분리 평가

**A. Candidate Pool**: 관점별 Top-M을 만들고 query×run 내 관점들의 집합을 **중복제거한 union**을 별도로 계산. Raw unique count, Silver-positive macro candidate Recall, 추가·누락 관련 사례 vs same M Dense, perspective coverage. 또 최종 관점별 Top-K와 원본쿼리 기반 Single Dense Top10/20을 동일 K로 비교하는 *보조 전역 diagnostic* 제공.

**B. Re-ranking**: 동일 후보에 대해 후보 Top-M 선정법과 독립적으로, 동일한 `Query–Case Interaction` 모형을 사용하여 각 관점별 점수를 계산하고 Top-K만 남긴다. 학습은 **Leave-One-Query-Out** (9개 질의로 학습하고 평가 대상 한 질의의 label 미사용; 반복 3회도 학습에서 제외). 구현 재현성을 위해 기실행 `scripts/v23_professor_hybrid_preserving.py`의 48d projection, interaction features, 학습 하이퍼파라미터를 재사용. 별도 label-blind `rrf` 후보 점수 정렬도 같은 pool에서 비교. **per-perspective Top-K가 본 설계의 공식 출력**, branch-balanced global Top-K는 과거 baseline과 정량 비교를 위한 *부가 diagnostic*이고 교수님 정식 출력은 아님.

**C. 실패 분석**: M별 candidate 관련 사례 증감, 실제 최종 TopK에서의 gain/loss, output candidate upper bound와 reranker gap을 분리. `M=84`에서도 QCI TopK는 고정 K이므로 자동 100%가 아님.

## 4. 범위 및 한계

- 데이터/라벨: 기존 v2.3 **AI-Silver Dev**만 재생; 결과는 독립적인 Gold Test가 아니다.
- equal-mean Multi-view는 learned Gate/Aattention의 성공을 의미하지 않음. 기존 learned gate 성능 미흡 결과는 보존.
- FAME-AX의 Graph Retrieval, Stage 3 Factor/Wald 및 Stage 4 LLM 전략추천을 신규 end-to-end로 실행했다고 주장하지 않음.
- RRF와 interleave는 사용자/교수님 미확정 방식; **교수님 답변에 따라 재설계**할 수 있다. M을 Dev로 사후 선택해 최종 성능 주장 금지.
- 결과에 불리한 설정과 수치를 숨기거나 원본 동결 브랜치에 덮어쓰지 않음.

## 5. 검증 체크

1. 모든 관점의 union case set이 84개이며 정확히 Dense/Sparse 둘 다 온전한 순위를 갖는다.
2. BM25 0점은 Sparse 선택/점수 기여에서 무시하며, Dense로는 선택 가능.
3. M=84는 모든 방식의 case set = 전체 84건. 각 M의 후보·TopK 중복 ID가 없음.
4. 고정된 query-run 30개, 동적 관점 97개, LOQO train/eval 질문 분리.
5. Snapshot 입력 검증과 산출물은 새 `experiments/v23_full_union_topm/`에만 저장.
