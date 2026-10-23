# v2.3 Stage 1 — 검색 입력 × 결과 결합 통제 실험

실험 조건을 바꾼 **추가 진단(Ablation)**이다. 기존 Stage 1의 84사례, 10질문, 97개 LLM 생성관점, BAAI/bge-m3, AI 기반 Ground Truth는 그대로 두었다. 새로운 LLM 호출이나 새 데이터 구축 없이 실행하였다.

## 검증할 질문
1. **검색 입력 검증:** 짧은 관점 제목만 검색해서 관련 정보가 빠진 것은 아닌가?
2. **결과 결합 검증:** 관점별 결과를 돌아가며 1개씩 뽑는 Round-robin이 관련 사례를 밀어낸 것은 아닌가?

## 실험 설계 (3 × 2)
- 입력 A TITLE: 기존처럼 관점 제목만 사용.
- 입력 B TITLE_DESCRIPTION: 같은 관점 제목 + 설명문 사용.
- 입력 C ORIGINAL_QUERY_WITH_PERSPECTIVE: 원래 업무문제 + 관점 제목 + 설명문 사용.
- 결합 1 ROUND_ROBIN: 기존 방식, 관점마다 돌아가며 사례 선정.
- 결합 2 RRF: 관점별 순위에 대한 Reciprocal Rank Fusion(k=60), 여러 관점에서 중복 발견한 사례를 높게 배치.
- 동일한 BGE-M3로 인코딩한 기존 84사례 벡터를 **그대로 재사용**. 검색 관점은 이전 Stage 1에서 생성한 97개를 그대로 사용.
- **원래 TITLE+ROUND_ROBIN의 97개 개별 branch 순위 및 30개 Top20·모든 지표가 기존 Stage1 기록과 정확히 일치하는지 먼저 검증 PASS**.
- Ground Truth, 전략, 구현/효과, 교수의 참조 관점은 어떤 검색 입력이나 결합 점수에도 넣지 않음.
- 10개 문제마다 3번의 기존 LLM 관점을 사용했으며, 30회 반복을 서로 독립된 30문제로 취급하지 않음.

## 결과: 같은 조건에서 입력과 결합만 변경한 Recall@10
| 검색 입력 | 결과 결합 | Recall@10 | 관점 Coverage@10 | 전략 Coverage@10* |
|---|---|---:|---:|---:|
| TITLE | ROUND_ROBIN | 0.4530 | 0.9278 | 0.8383 |
| TITLE | RRF | 0.4787 | 0.9500 | 0.8889 |
| TITLE_DESCRIPTION | ROUND_ROBIN | 0.4295 | 0.8944 | 0.8011 |
| TITLE_DESCRIPTION | RRF | 0.4349 | 0.8944 | 0.8161 |
| ORIGINAL_QUERY_WITH_PERSPECTIVE | ROUND_ROBIN | 0.5401 | 1.0000 | 0.8861 |
| ORIGINAL_QUERY_WITH_PERSPECTIVE | RRF | 0.5333 | 0.9667 | 0.8528 |

*Strategy Coverage는 **AI 관련도 양성 사례에서 파생한 전략 유형**과의 중복이다. 독립적 전략 추천 정확도가 아니다.

**비교용 기존 모델 (재실행 아님, 같은 동결 Stage 1 기록):** Single Dense Recall@10 **0.5332**, GPT-only Recall@10 **0.7235**.

## 변화량: 원인 분리를 위한 짝지은 비교
| 바뀐 조건 | Recall@10 평균 변화 | 개선 질문 | 하락 질문 | 동일 질문 | 질문단위 bootstrap 95% 구간 |
|---|---:|---:|---:|---:|---:|
| INPUT_TITLE_DESCRIPTION_VS_TITLE_AT_RR | -0.0235 | 4 | 5 | 1 | [-0.1141, +0.0688] |
| INPUT_ORIGINAL_PLUS_PERSPECTIVE_VS_TITLE_AT_RR | +0.0871 | 5 | 3 | 2 | [-0.0073, +0.2023] |
| FUSION_RRF_VS_RR_AT_TITLE | +0.0257 | 5 | 4 | 1 | [-0.0241, +0.0778] |
| FUSION_RRF_VS_RR_AT_TITLE_DESCRIPTION | +0.0055 | 4 | 4 | 2 | [-0.0467, +0.0575] |
| FUSION_RRF_VS_RR_AT_ORIGINAL_PLUS_PERSPECTIVE | -0.0067 | 3 | 2 | 5 | [-0.0593, +0.0366] |
| JOINT_TITLE_DESCRIPTION_RRF_VS_ORIGINAL | -0.0181 | 3 | 6 | 1 | [-0.1029, +0.0778] |
| JOINT_ORIGINAL_PLUS_PERSPECTIVE_RRF_VS_ORIGINAL | +0.0803 | 6 | 2 | 2 | [-0.0078, +0.1927] |

Bootstrap 구간은 **개발용 10질문의 차이**를 설명하기 위한 탐색적 구간이다. 새로운 문제에 대한 일반화의 통계적 보증이나 모델 선정의 최종 검증으로 사용하지 않는다.

## 추가 점검
- Top10 기존 대비 새로 찾은 정답 사례(gained)와 잃은 사례(lost)를 **동시에** 기록하였다.
- 관점별 검색결과의 중복률과 최종 상위 사례가 어느 관점의 후보였는지 기록하였다.
- 신규 검색 문장의 길이와 SHA256을 \`input_text_audit.csv\`에 남겼다.
- Reference Perspective 중 정답 사례가 0개인 하나의 관점은 Coverage 분모에서 제외하였다(억지 정답 생성 금지).

## 해석 및 연구 설계상 주의
- 이 실험은 **교수 제안 아키텍처의 원리 검증**을 위한 진단이며 RRF로 교수의 branch 보존 구조를 최종 대체한다는 뜻은 아니다.
- RRF가 유리해도 다중 관점의 식별성과 분기별 근거를 별도로 보존·검증해야 한다.
- TITLE+DESCRIPTION과 원문 추가 간 차이는 모델/정답을 바꾸지 않은 상태에서 검색 텍스트의 정보량 효과이다.
- Stage1/2/3/4 완료 기록 및 동결 데이터셋은 변경하지 않음. Dev 실험에서 보이는 최고값을 최종 Test 성능으로 주장하지 않음.

## 재현 파일
- \`factorial_summary.csv\`: 입력 3 × 결합 2 × K 3.
- \`query_level_means.csv\`: 질문별(3회 평균) 지표.
- \`metrics_by_query_and_run.csv\`: 180개 질문-반복-실험조건 × K 3 평가.
- \`replayed_rankings_top20.csv\`: 실제 검색 사례 순위/관점 출처.
- \`top10_gain_loss_vs_original.csv\`: 사례 수준 gain/loss 진단.
- \`paired_contrasts_recall10.csv\`: 변인 통제와 질문별 효과.
- \`input_text_audit.csv\`: 사용한 검색 텍스트 길이 및 해시.
- \`manifest.json\`: 동결 원본 파일 SHA256 및 재현 조건.

