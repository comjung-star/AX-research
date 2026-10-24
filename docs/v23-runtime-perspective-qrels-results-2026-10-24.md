# v2.3 실제 동적 관점–AX 사례 8,148쌍 매핑 데이터셋: 검증 결과

기준일 2026-10-24 | 별도 실험 브랜치 `experiment/v23-runtime-perspective-qrels-20261024` | **실제로 수행한 두 번의 블라인드 AI 평가**. 사람의 독립 Gold 판정 아님.

## 1. 연구 목적 / 데이터 출처
- 기존 LLM 동적 생성 관점 97개(원문질문 10개 × 3회 반복; 관점 개수는 회차마다 가변) × frozen v2.3 AX 사례 84개 = **8,148개 서로 다른 관점–사례 쌍**.
- 과거 AI-Silver 2,520개는 정적 draft reference 관점의 결과이므로 재활용하지 않음. 실제 runtime의 관점별 제목과 설명, 각 사례의 Problem/Task/Context를 독립적으로 비교.
- API 420회 응답에서 실제 **16,296개** AI 점수(8,148쌍 × 2회)를 수집·원시 자료/모델 ID/응답 ID/입력 프롬프트 해시와 함께 보존.

## 2. 평가 기준 / 품질 관리
- 0=문제·과업 무관, 1=주변 연결, 2=일부 관련, 3=주요 문제나 과업이 밀접, 4=문제·업무·맥락이 직접 일치.
- 동일 모델을 두 번 독립 호출해 블라인드 판정하고 점수·근거를 모두 남김. 서로의 점수와 과거 평가결과는 보여주지 않음. 모델명 `gpt-6-luna`.
- 두 번 모두 3~4점이면 학습 positive, 모두 0~2점이면 학습 negative. 경계(관련/비관련) 판정이 갈라지면 `UNCERTAIN_THRESHOLD_FLIP`으로 **학습에서 제외**.
- 동일 범주 내에서 두 점수가 다르면 더 낮은 점수 선택(보수적). 오판 위험을 줄이는 규칙이지 '정확성 검증'이 아님.

## 3. 실제 집계 결과
| 항목 | 결과 |
|---|---:|
| 전체 매핑 쌍 | **8,148** |
| AI 채점 횟수 | **16,296** |
| 성공적으로 수집한 고유 API 응답 | **420** |
| 0~4점까지 완전 동일하게 평가 | **6,382 (78.33%)** |
| 관련/비관련 기준 일치 | **97.93%** |
| 관련 여부가 뒤집힌 불확실 쌍 | **169 (2.07%)** |
| 임시 학습에 이용 가능한 전체 쌍 | **7,979** |
| 임시 학습 관련(positive) | **311** |
| 임시 학습 비관련(negative) | **7,668** |
| 추가 검토 우선순위에 들어간 쌍 | **1,613** |
| positive 0개인 동적 관점 | **18 / 97** |

두 AI 채점은 동일 계열 모델/루브릭으로 생성되므로 이 수치가 실제 정답 정확도나 인간 간 일치율을 의미하지 않음. 학습 positive는 전체 trainable 7,979개 중 약 3.90%로 매우 희소하므로 QCI 학습 시 class imbalance, hard negative 선택, 관점별 positive가 없는 데이터 처리 정책이 중요.

### 추가 검토 대상의 구성
| 검토 사유 | 쌍 수 |
|---|---:|
| 두 AI 채점 간 3점 관련성 경계가 달라짐 (최우선) | **169** |
| 관련성 경계는 같으나 점수 차이가 2점 이상 | **67** |
| 2점 또는 3점 경계 부근의 유효 점수 포함 | **1,377** |

이는 검토 **우선순위 제안**이지 이미 사람이 검토한 자료는 아님. 사용자에게 8,148쌍 모두 직접 재평가를 요구하지 않음. 특히 positive 0개 관점 18개는 실제 사례 부재와 AI 누락 가능성을 구분할 필요가 있으며, 없는 positive를 임의 생성해서는 안 됨.

## 4. 신뢰성·누수 검사
- 97×84 모든 키가 정확히 한 번씩 포함됨. 60개 grading job 성공. 원시 2회 평가 전수 존재.
- 모델에는 기존 qrels 점수, 검색 순위, 구현 기술, 성과 및 Factor/Strategy 라벨 미제공.
- 서로 다른 실제 채점 응답 ID 420개 검증. 기존 corpus 및 관점 파일 SHA256 일치.
- 학습/검증을 **질문 ID 단위 LOQO 10-fold**로 미리 구성: 같은 질문의 3회 생성 관점을 서로 다른 fold에 분산하지 않음.
- `human_approved=FALSE`, `AI_TWO_INDEPENDENT_BLIND_PASSES_SILVER_NOT_HUMAN_GOLD`로 모든 결과 표시.
- 기존 정적 reference 관점 P1과 새 runtime 관점 P1이 의미상 동일하다고 가정하지 않음.

## 5. 산출물
데이터 폴더 `experiments/v23_runtime_perspective_qrels/`:
- `runtime_qrels_8148.csv`: 주 결과, 8,148쌍, 두 평점과 근거·점수충돌·메타데이터.
- `trainable_pairs_ai_silver.csv`: 의견 불일치 169개 제외한 **7,979개**, 임시 train candidates.
- `positive_pairs_ai_silver.csv`: 두 AI 모두 관련 판정한 **311개**.
- `review_priority.csv`: 추가 검토 **1,613개**, 판정 근거와 원문 필드 포함.
- `per_runtime_view_answerability.csv`: 관점별 positive·negative·uncertain 분포.
- `loqo_split_manifest.csv`: 질의 단위 학습/검증 분리 10fold.
- `api_pass_integrity.csv`: 60개 채점 작업 및 모델·프롬프트 검증.
- `label_quality_report.json`: 검증 통계, 상태와 품질·한계.
- `raw_passes/`: 원시 2회 AI 채점 60개 단위 및 각 API batch 증거.

## 6. 다음 단계 제안
1. **우선 169개 threshold conflict와 positive 0개 관점 18개를 진단**. 기존 1,613개 review queue 중 우선순위를 지켜 대표 표본 검토 및 스키마 검증.
2. 모델 학습에서는 충분하지 않은 positive와 negative 불균형을 보정하고 hard negative를 활용하되, 레이블 자체를 검색 모델의 결과로 재정의하여 학습하면 순환 검증 위험이 있으므로 주의.
3. 7,979개 AI-Silver를 신경망 QCI 지도학습에 사용하되 독립 개발 데이터와 별도 실제 Test, 가능하면 외부 인간 관점별 관련성 검증을 확보.
4. 교수님이 제안한 learned Gated Fusion (Problem/Task/Context)과 query–case interaction을 구성하고 frozen Dense 3-view baseline과 **동일 관점별 Top-K**에서 비교. 임의 48차원 축소 모델은 유지할 이유가 약함.

## 7. 실행 증거
- [최초 AI 평가/원시 데이터 60개 수집](https://github.com/comjung-star/AX-research/actions/runs/40081537471) : 실제 grade job 전부 성공, 최초 자동 통합 경로 문제로 job run 결론은 failure.
- [재실행한 결과 취합과 전체 데이터 검증 성공](https://github.com/comjung-star/AX-research/actions/runs/40083840975).
- [사전계획](../../docs/v23-runtime-perspective-qrels-protocol-2026-10-24.md).
