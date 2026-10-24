# v2.3 실행 관점–AX 사례 8,148쌍 관련도 구축: 사전 계획

2026-10-24 | branch `experiment/v23-runtime-perspective-qrels-20261024` | 기존 release/실험 결과 보존.

## 목적과 범위
- Stage1에서 실제 LLM이 **동적으로 만든 97개 관점**(10개 원질의 × 각 3회)의 원문 제목·설명에 84개 동결 AX 사례의 Problem/Task/Context를 일대일 연결한다. 정확한 8,148 `(query_id,run_id,runtime_perspective_id,case_id)` 키.
- **기존 draft reference perspectives 30개에 붙은 2,520개 AI-Silver를 runtime P1..P5로 이름만 바꿔 재사용하지 않는다.** 새 관점 자체를 의미 기준으로 **새로 블라인드 채점**.
- 불변 corpus v2.3 사례 84개; query 10개, 각 run 3개, 동적으로 생성된 perspective 총 97개. solution/implementation/outcome/전략/원인 분류/기존 Silver 점수/Dense 점수/검색 순위는 judge에 절대 입력 금지.

## 판정 기준 및 프로토콜
- 신규 유료 API AI 판정 2회 **서로 독립적으로** 시행. 질문-반복별 관점 2~5개와 사례 12개씩, 7개 배치/회, 총 30 query-run ×7 batch×2 pass=420 API 요청을 계획; 오류 재시도 추가 가능. 다른 pass 점수/답변을 공개하지 않는다.
- 0: 주요 문제·과업 무관, 1: 주변/간접 공통점, 2: 일부 문제/과업 겹침이나 핵심 작업 다름, 3: 핵심 문제 또는 AX 대상 작업 상당히 관련, 4: 문제·과업과 업무 맥락이 직접 일치.
- 평가 대상은 **원문 사용자 질의에 근거한 특정 runtime 관점** 및 사례 `problem/task/context`만. 같은 사례를 다른 관점이 다른 점수로 판정할 수 있고, 관심 없으면 모두 0이어도 됨.
- 근거 1문장, 특히 관련 판정은 사례의 원문 Problem/Task를 근거로 구체적인 공통점 기록. 브랜드·전략 라벨·성과·해결책으로 관련성을 추정하지 않음.
- 2회 모두 `>=3`이면 provisional-positive; 2회 모두 `<3`이면 provisional-negative. 양/음이 갈리면 `UNCERTAIN_THRESHOLD_FLIP`으로 **학습에서 제외**. 같은 양/음 내부에서 점수 불일치하면 두 점수를 그대로 기록, `grade_for_training=min(pass1, pass2)` (보수적). 이 규칙은 결과 확인 전에 고정.
- 두 채점은 동일 모델과 rubric이라 **독립적인 인간 검증이 아님**. 정확도가 확립되지 않았으므로 AI-Silver TRAIN 후보로만 기록하고 `human_gold=false` 고정.
- 불확실성/차이 심한 사례 `abs(s1-s2)>=2`, threshold flip, 거의 점수 2/3인 것 중 리뷰 우선순위 별도 생성. 다수의 긍정 라벨을 맞추기 위한 강제 할당 금지.

## 검증과 산출물
- `runtime_qrels_8148.csv`: 모든 키, 2회 실제 점수, 보수적 학습 점수, 학습 포함 여부, 한국어 판단 근거 2개, 응답 ID, 증거 필드, 상태/출처, 출처 파일 버전.
- `positive_pairs_for_training.csv`: 2회 모두 관련 `>=3`인 데이터(훈련용 임시 positive). 불확실 판정은 제외. negative/ambiguous 구분하여 학습 batch 만드는 곳에 누수 방지.
- `review_priority.csv`: 2회 의견 충돌 또는 큰 점수차, 사람이 평가하려면 이 파일에서 별도 리뷰. **사람이 필수적으로 8,148개를 검토해야 한다는 뜻은 아님.**
- `view_answerability.csv`: 관점별 분포, 관련 후보 수, 불확실 비율, 모두 0인 관점도 그대로 유지.
- `label_quality_report.json`: coverage, exact grade agreement, binary agreement, threshold flips, positive count, zero-positive perspectives, duplicate case texts, AI-Silver old reference와 **독립적으로** 비교할 수 있는 진단 지표 (동일 관점 ID 매칭 금지).
- 원시 판단 `raw_passes/`와 manifest 별도 저장. 모든 짝 중복·누락 없이 8148, 실제 원시 16,296 판정, 출처 및 model response id 검사. API 실패 시 합성 라벨로 채우지 않고 실패 처리.
- 학습/검증은 97개 관점 단위 무작위 분할이 아니라 **사용자 원질의 10개를 기준으로 분할**. 같은 질문의 3회 생성 관점은 언제나 같은 fold. 기존 10 Dev 질문의 평가성능을 독립 Test라고 부르지 말 것.
- 현재 84사례 코퍼스/10질문은 작은 개발 데이터; 관점별 평점 8,148개가 독립 업무 문제 8,148개를 의미하지 않음. 지도 평가의 신뢰성을 높이려면 질문/사례가 독립적인 외부 Test와 소규모 사람 검증이 추가 필요.

## 실행 조건
- 동결 원본 `release/ax-v2.3-stage1-to4-dev-20261023` 복사 브랜치 위에서만 신규 디렉터리 `experiments/v23_runtime_perspective_qrels/` 생성.
- GitHub Actions의 기존 `OPENAI_API_KEY` repository secret이 유효해야 함. secret이 없거나 모델 API 실패 시 '완료' 보고 금지.
- 모델은 기존 v2.3 평가와 동일하게 `gpt-6-luna`를 요청하고 observed model ID/응답 ID를 남긴다.
- 60개 실행 단위(10 question ×3 runs ×2 passes); 요청당 최대 12 사례와 해당 runtime 관점들. 모델 입력에 reference GT 누설 금지.

본 문서는 결과 확인 **이전**에 작성한 사전 등록 계획이다.
