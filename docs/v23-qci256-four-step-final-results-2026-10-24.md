# AX v2.3 — 관점별 데이터 보완부터 학습·평가까지 4단계 실험 결과보고서

**2026-10-24 | 실행 및 검증 완료 | 연구용 AI-Silver / Dev 실험 (human Gold 아님)**

실험 브랜치: `experiment/v23-qci-256-four-step-20261024`. 원래 v2.3 corpus 84개, 동적 생성 관점 97개, Stage1~4 frozen 산출물 및 원래 8,148개 쌍의 AI 2회 판정을 **수정하거나 삭제하지 않음**. 별도 stage1–4 기록 파일만 신규 생성.

## 전체 결론
**1~2단계: 문제가 있던 관점 중 일부는 학습 데이터 보완에 성공. 3단계: 학습형 256차원 Query–Case Interaction 모델을 실제 구현·학습 완료. 4단계: 공정한 같은 동적 관점 데이터 평가에서는 Dense 단독 검색이 여전히 승리.** 따라서 수정한 학습형 모델을 성능 개선 성공으로 주장하거나 서비스 추천 기본값으로 채택하지 않음.

## 1단계: 관련 사례 0개 관점 18개 재검토
- 원인: 관련 사례 없음의 정확한 정의는 **두 AI가 모두 3점 이상이라고 판단한 사례가 없는 것**이다. 진짜 사례 부재로 단정 금지.
- 기존 18개 zero-positive 관점에서 **이전 두 차례 AI 평점이 3점 기준을 가른 17쌍 + 기존 2점 등 근접 후보 35쌍 = 총 52쌍**을 다시 평가. 5개 질문에 대해 이전 점수·구현기술·검색 결과를 보여주지 않는 **실제 AI API 블라인드 3차 평가**를 5회 실행.
- 두 pass가 일치한 7,979쌍은 그대로, 충돌 17쌍만 사전 정의한 **3회 관련/비관련 다수결**로 별도 Silver label 보완. 3차 역시 인간 심사가 아니며 사례 0개를 일부러 채우지 않음.
- 재검토 후 **0개 관점 18 → 14개**, 즉 4개 관점에 합의 AI-Silver 관련 사례 추가. 나머지 14개는 현재 근거로 강한 관련성 사례를 판정하지 못함.
- 18개 관점은 10개의 원질문에서 파생된 97개 관점 중 일부이므로 18개의 독립 업무문제 실패가 아니다.

## 2단계: 학습 데이터 검증 및 보존
| 분류 | 기존 2-pass | 3차 별도 보조 감사 반영 |
|---|---:|---:|
| 전체 관점–사례 쌍 | 8,148 | 8,148 |
| 지도학습 가능한 쌍 | 7,979 | **7,996** |
| 관련 사례 (3점 이상 합의) | 311 | **317** |
| 비관련 사례 | 7,668 | **7,679** |
| 불확실성으로 제외 | 169 | **152** |
| positive 0개 runtime 관점 | 18 | **14** |

학습용 보조 자료와 원래 2-pass 평점은 함께 보존. **문항 ID 단위 LOQO 10fold**, 동일 질문의 3회 반복 및 생성 관점 모두 한 fold에서 배제; 152개 미해결 충돌은 학습에 편입 금지.

## 3단계: 학습형 256차원 Multi-view와 QCI 구현·실행
- **기존 BGE-M3 1024차원**: 실제 Stage1에서 미리 고정·저장한 임베딩 재활용. Problem, Task, Context 3-view 84개 및 runtime perspective 97개.
- 임의 48차원 랜덤 투영이 아니라 **학습형 공유 1024→256 projection** 사용.
- **동적 실행 관점 q와 각 사례의 3-view**에 대해 **비선형 q×view 상호작용을 포함한 3-view Softmax Gate** 학습. 각 사례의 가중합 256d Case 표현 생성; 관점과 해당 Case의 `[q,c,q*c,|q-c|]` 결합 → 64→1 QCI MLP.
- 학습 objective: Positive class 가중치 BCE + positive vs hard-negative Pairwise ranking, seed 42, 24 epoch, AdamW 0.002, 10fold LOQO. fold별 학습 질문·관점·관련 레이블 수, 모델 파라미터 수, train loss 기록.
- 초기 additive q+c 선형 gate는 Softmax 수학상 관점 q가 소거될 수 있다는 구현 점검에서 밝혀져 **상호작용 포함 비선형 gate로 수정 후 10fold 재실험**. 변경 전 초기 결과는 최종 비교로 사용하지 않음. 테스트에 `관점이 달라지면 3-view gate 가중치가 달라질 수 있어야 한다`는 자동회귀 검증 추가.
- 비교 모델: `gated_qci_256`(학습형 단독)와 `dense_anchor_gated_qci_256`(Dense 기본 점수 + 고정 0.10×tanh(QCI)), 기준 `dense_3view`.

## 4단계: 실제 성능 비교 (동일 84사례·97관점·AI-Silver, full84)
**주 지표는 10개 원질문 각각의 관점별 Recall을 계산한 후 질문 단위 평균(Query macro Recall@K).** 학습할 질문은 9개, 1개는 완전히 제외하여 검증. 원래 2-pass만의 합의 정답을 주 평가로 고정하여 3차 표본 선정 편향을 주 지표에 주입하지 않음. 97개 실행 관점 중 positive가 없는 **18개 관점**은 Recall 분모에서 제외하고 별도 보고.

| 모델 | Top5 Recall | Top10 Recall | Dense 대비 Top10 |
|---|---:|---:|---:|
| **기존 3-view Dense** | **35.16%** | **47.64%** | 기준 |
| 학습형 256d Gated Fusion + QCI | 23.47% | 27.73% | -19.91%p |
| **Dense 기반 + 학습형 256d QCI 보정** | 32.14% | 45.33% | -2.31%p |

**Top10에서 기존 Dense가 가장 높았음.** 256d 학습형 모델의 단독 순위는 불안정하고, Dense 중심의 작은 보정 모델도 근소하게 낮음. Dense 보정 모델의 10개 원질문별 비교는 Dense 대비 **3개 개선, 6개 악화, 1개 동률**이다. V21D005, V21D003, V21D010에선 개선된 사례가 있으나 V21D006 등에서 악화가 커서 평균 우수성이 없음.

### 별도의 보조 분석 (3차 AI-Silver 보완판정 반영)
- 보조 판정에서 zero-positive 관점 14개를 제외한 83개 관점, 같은 Top10: Dense **47.64%**, Dense+256d QCI **45.98%**, 256d QCI **27.79%**.
- 이 수치 역시 Dense 우세이며, 3차 선택적 리뷰가 들어간 보조 실험이라 독립 확증이 아님.

### 왜 이전 보고 Dense 63.32%와 다를까?
지난 **63.32%**는 '고정된 30개 reference 평가 관점에서 나온 질문별 관련 사례 합집합'과 runtime 관점별 Top10 합집합을 비교한 **다른 정의의 지표**였다. 이번 **47.64%**는 실제 LLM 생성 **97개 runtime 관점 각각의 관련 사례 정답**을 대상으로 측정해 질문별 평균한 수치다. 성능이 갑자기 떨어졌다고 해석하거나 63.32%에서 47.64%를 단순 뺄셈하면 안 된다.

## 모델 채택 여부와 앞으로 남은 한계
**결론: 현재는 Dense baseline 유지.** 사용자의 동적 관점을 배우는 모델의 실행과 비교까지 끝났다는 점은 연구 진전이지만, 성능 향상을 입증하지 못했으므로 논문에서 개선 성공 주장 금지.

가능 원인/우선 개선 과제:
1. 긍정 학습쌍 **317개**에 불과하며 **7,679개 negative**에 비해 매우 희소. 84사례/10업무 질문만으로 32만+ 파라미터 모델을 안정 학습하기 어렵다. 이는 추정 원인이지 인과관계 확증 아님.
2. **14개 empty 관점**이 남았고, **152개 충돌쌍**은 판단이 미확정. 실제 코퍼스 공백인지 유사 사례를 충분히 찾지 못했는지 조사해야 함.
3. AI 평가 2~3회 일치는 **사람이 판정한 실제 정답 Gold가 아님**. 사후 선정된 near-miss 3차 평가는 데이터 누출 위험을 피하도록 primary와 분리했지만 확증 가능한 독립 Test도 없음.
4. 다음 실험은 **새로운 업무 질문과 별도 Test, 대표 표본의 외부/독립 관련도 검토, 더 다양한 진짜 positive 예시 확충, 작은 모델/정규화**를 사전등록하고 진행. 아직 다른 Stage1~4 전체의 향상, 통계적 유의한 논문 결론, 일반화에 대한 근거 부족.

## 4단계별 실제 산출물 및 실행 증거
- 1단계 `experiments/v23_qci256_four_step/stage1_review_queue.csv`, `stage1_zero_view_audit.csv`, `stage1_review_ai_pass3.csv`, `stage1_review_api_evidence.csv`.
- 2단계 `stage2_training_label_manifest.csv`, `stage12_summary.json`.
- 3단계 `stage34_fold_train_audit.csv`, 학습 재현 코드 `scripts/v23_four_step_qci256.py`, 테스트 `tests/test_v23_four_step_qci256.py`.
- 4단계 `stage34_summary.csv`, `stage34_summary.json`, `stage34_perspective_metrics.csv`, `stage34_query_metrics.csv`, `stage34_top10_rankings.csv`.
- [Stage 1~2 재검토 및 학습 데이터 기록 검증 성공](https://github.com/comjung-star/AX-research/actions/runs/40095885718).
- [Stage 3~4 **수정된 query-conditioned gate** 최종 테스트·훈련·결과 CI 성공](https://github.com/comjung-star/AX-research/actions/runs/40096426618).
- [사전등록 설계](v23-qci256-four-step-preregister-2026-10-24.md).

**연구 보고에 쓸 문장:** 'LLM 동적 관점별 AI-Silver 관계 라벨을 8,148쌍 구축하고, 고위험 경계 사례의 추가 블라인드 평가를 통해 지도학습 후보를 7,996쌍으로 정리했다. 제안된 관점 조건부 학습형 Gated Fusion 256 + QCI를 10개 개발 질의 LOQO로 평가하였으나, 동일 관점별 Top10 Recall에서 Dense 47.64%, Dense+QCI 45.33%, QCI 단독 27.73%로, 학습형 모델의 우월성은 입증되지 않았다.'
