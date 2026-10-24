# AX v2.3 Stage 1 교수님 권고 반영: 관점별 검색 결과 분리 재분석 보고서

실험일: 2026-10-24. 상태: **실제 GitHub Actions 수행 성공**. 별도 분기: experiment/v23-stage1-perspective-separation-20261024.

## 1. 배경
기업 업무문제는 지식 접근 지연, 반복작업, 응답품질 등 여러 관점으로 분해된다. Stage1에서 LLM으로 생성한 관점별 검색 결과는 최종 AX 근거 분석과 Query–Case Interaction을 위해 해당 관점의 사례로 보존할 필요가 있다.

## 2. 문제점
동결 원본의 다중관점 Dense 검색은 관점별 결과를 round-robin으로 합쳐 **전체에서 10개만** 선택했다. AI-Silver 기반 Recall@10은 단일 Dense 53.32%, 다중관점 Dense 45.30% (-8.02%p). 다만 이는 관점별 검색 자체의 능력뿐 아니라 **조기 전역 Top-10 절단의 손실**이 함께 반영된 결과다.

## 3. 방안
교수님 권고대로 실행시점 생성한 각 관점의 검색 사례를 그대로 유지하고 관점별 Top-K를 출력한다. 평가 지표 계산에 한해서만 이들 결과의 Case ID를 중복 제거한다. **평가 기준 Silver P1/P2/P3와 런타임 관점 P1/P2/P3의 ID를 동일한 개념이라고 가정하지 않음.**

## 4. 문제 해결을 위한 설계
- **원본 재사용:** Stage 1 동결 원본 `release/ax-v2.3-stage1-to4-dev-20261023`, 84 AX사례, 10 Dev 질문×3회, 생성 관점 97개, 각 관점 Dense/BM25 원본 84개 전체 순위, AI-Silver 판정 2520개. 새로운 LLM 및 임베딩 인코딩은 수행하지 않음.
- **비교:** (1) 기존 MP 전역 Top-K; (2) 각 관점의 Top-K 개별 보존(결과 품질 평가 때만 합집합); (3) Single Dense/BM25 Top-K; (4) **보존 결과의 고유 사례 수 N과 동일한** Single Dense Top-N; (5) 동일 N의 기존 MP round-robin Top-N.
- **K:** 관점별 5/10/20. **관점별 Top-10은 전역 10건과 동의어가 아님.** 상위 10건을 지닌 관점이 여러 개면 합집합의 후보 개수 N은 10보다 커짐.
- **검증:** 원본 전체 MP 전역 Top20 순위 일치; 원본 Stage1 각 K의 recall 정확 일치; 저장된 원문 질의 BGE 임베딩×사례 임베딩으로 복원한 Single Dense Top20이 원본과 일치; 97개 관점·30개 실행 정합성 통과.
- **분석 코드:** `scripts/v23_stage1_perspective_separation.py`, 테스트 `tests/test_v23_stage1_perspective_separation.py`.
- **실행:** [GitHub Actions 40075961511](https://github.com/comjung-star/AX-research/actions/runs/40075961511).

## 5. 비교 결과

### 5.1 Dense 검색: 관점 보존과 후보 예산 비교
| 비교 방식 | 평균 고유 후보 수 | Silver 관련 사례 Recall | 기준 관점 Coverage |
|---|---:|---:|---:|
| 기존 다중 관점 **전역 Top10** | 10.00 | **45.30%** | 92.78% |
| 단일 Dense Top10 | 10.00 | **53.32%** | 100.00% |
| **관점별 Dense Top10 유지** | **22.13** | **70.85%** | **97.78%** |
| Single Dense TopN (**N=22.13 평균, 개별 실행마다 동일 N**) | 22.13 | **71.24%** | 100.00% |
| 기존 MP round-robin TopN (**N=22.13 평균, 개별 실행마다 동일 N**) | 22.13 | **70.13%** | — |

- 전역 Top10 → 관점별 Top10의 recall 차이는 **+25.55%p**이고, Silver-positive 출현 81회를 추가 회수했으며 기존 글로벌에서 찾은 관련 사례의 손실은 0회였다.
- 그러나 평균 후보 수가 10 → 22.13개로 2.21배 증가한 결과이다. 이는 **같은 출력 예산의 순위 품질 개선 증거가 아니다.**
- 동일 후보 수 통제에서는 관점별 보존 **70.85%** vs Single Dense TopN **71.24%** (관점별 **-0.40%p**). 개별 질문×실행 30쌍에서 관점별 승/패/동률은 11/11/8. 관점 분리 검색의 독립적인 우수성을 입증하지 못함.
- 같은 다중관점 검색의 후보 예산 N을 유지하면, 분리 보존 70.85% vs 기존 round-robin TopN 70.13% (**+0.71%p**). 이 차이 역시 규모 작고 Dev 자료만으로 우월성 확정 불가.
- 단일 Dense의 평균 기준 관점 coverage는 Top10과 TopN 모두 100%로 높았다. '관점 분리가 새로운 관점 보존에 있어 무조건 우월'하다는 해석 금지.

### 5.2 K별 Dense 비교 (질문×반복 매크로 평균)
| 관점별 K | 기존 MP 전역@K | 관점별 분리@K 합집합 | 분리 시 고유 N | Single Dense@N |
|---:|---:|---:|---:|---:|
| 5 | 29.84% | 50.63% | 11.93 | 60.06% |
| 10 | 45.30% | 70.85% | 22.13 | 71.24% |
| 20 | 64.65% | 85.16% | 39.43 | 88.41% |

### 5.3 BM25 검색도 동일하게 분석 (새 Hybrid 실험 아님)
| 관점별 K | 기존 MP BM25 전역@K | BM25 관점별 분리@K | 분리 시 고유 N | Single Dense@N |
|---:|---:|---:|---:|---:|
| 5 | 16.12% | 26.00% | 10.87 | 56.63% |
| 10 | 24.70% | 29.37% | 17.80 | 68.70% |
| 20 | 30.41% | 41.09% | 26.57 | 76.63% |

BM25 관점별 보존도 글로벌 절단보다 관련 후보를 더 포함하지만, Dense 기반 비교군에 크게 못 미친다. Dense와 Sparse 결합 후보 실험으로 혼동 금지.

### 5.4 기존 Single Dense@10의 관련 사례를 놓친 원인: 전수 39회
동결 MP-global@10이 놓쳤으나 Single Dense@10에는 있던 **AI-Silver 관련 사례의 query-run-case 출현 39회**를 원본 Dense branch 전체 순위로 역추적했다.

| 해당 사례의 개별 관점 내 최소 순위 | 누락 출현 수 | 관점별 결과로 복구 가능 여부 |
|---|---:|---|
| 개별 관점 **1~10위** | **24회** | 관점별 Top10에 이미 존재, **24회 모두 복구** |
| 개별 관점 **11~20위** | **13회** | 관점별 Top20에서 복구 |
| 모든 개별 관점 **20위 밖** | **2회** | 관점별 Top20만으로 복구 불가 |
| **합계** | **39회** | **Top10 복구 24회 / Top20 복구 37회** |

따라서 원래 떨어진 39개 '사례 출현' 가운데 최소 24개는 **검색기가 아예 발견하지 못한 것이 아니라 전역 병합 시 Top10 잘라내기 때문에 사라진 것**이다. 39는 독립적인 서로 다른 case ID 39건이 아니라 10개 질문 3회 반복 중의 relevant query-run-case 발생 건수다.

### 5.5 실제 사례 예시: 긴 이메일 스레드 문제
- 사용자 질의 `V21D002`: '영업과 서비스 담당자가 긴 이메일 스레드와 첨부 문서를 일일이 읽고 핵심 내용과 후속 조치를 정리하는 데 많은 시간을 쓰고 있다.'
- 관련 AX 사례 `AXV2H_0002_01`: '길고 복잡한 이메일 스레드의 핵심 내용 파악과 후속조치 확인에 시간이 소요됨'.
- 3회차 기준 단일 Dense **1위**, Multi-perspective 생성 **P2 검색 6위**였으나, Stage1 기존 전역 통합 목록에서는 **14위**여서 **global Top10에서 탈락**.
- 관점별 P2 Top10을 별도로 보존하면 해당 사례가 살아남음. 사례의 Silver 관련 판정과 실제 문장 연결까지 확인 가능한 구체적 실패 유형이다.

## 6. 판정 및 다음 연구 단계
**확인됨:** 교수님 권장 관점별 결과 독립 보존은 기존 조기 전역 TopK 절단으로 인한 관련 사례 누락을 줄인다. Stage1의 낮은 MP-global@10 숫자를 '관점별 검색 자체가 관련 사례를 못 찾았다'로만 해석하면 오류.

**아직 확인되지 않음:** 같은 사례 수 예산에서 관점별 분리가 Single Dense보다 좋은가? 현재는 **아니며 근소한 열세**. 또한 출력 목록에 평균 22건이 나타나므로 후단에서 정밀 매칭으로 압축해야 하는 필요성이 커진다.

**다음 실험:** 각 관점을 Query–Case Interaction에 그대로 전달하고 **관점별 Top-K**로 재평가; 후보 크기를 동일하게 통제하면서 Dense-only vs Dense+Sparse hybrid를 별도 효과 검증. 교수님 제안 Multi-view Problem/Task/Context와 learned Gate 입력 품질 확인, 최종 AX 추천 Stage3/4 연결 실험은 그다음.

**정확한 범위:** Stage1 원본 dense는 단일 문서 Dense 임베딩의 관점별 질의 검색이다. 교수님이 제안한 학습형 Multi-view Gate, Hybrid Sparse+Graph, Query–Case MLP, Factor Anchor, Wald, Stage 4 end-to-end 전체 성능 검증은 **이번 재분석에 포함되지 않았다.** 관련도는 기존 AI-Silver Dev로, 독립 인간 Gold/Test 아님.

## 7. 전체 재현 원자료
- `experiments/v23_stage1_perspective_separation/summary.json`: 평균 지표 및 전수 오류 분류.
- `experiments/v23_stage1_perspective_separation/all_comparisons_by_query_run.csv`: 30회 반복×retrieval×K 180건의 paired 실험 비교.
- `experiments/v23_stage1_perspective_separation/all_setting_metrics.csv`: global/separated/single/budget controls 전체 900행.
- `experiments/v23_stage1_perspective_separation/per_perspective_top20_source_rankings.csv`: **관점별 ID, case ID, local rank, 과거 global rank, case text**.
- `experiments/v23_stage1_perspective_separation/old_global_top10_missing_single_relevant_cases.csv`: 실제 놓쳤던 39개 출현의 원인·최소 branch 순위·복구 여부 전수 기록.
- 실험 전 프로토콜: `docs/v23-stage1-perspective-separation-protocol-2026-10-24.md`.
