# AX v2.3 — 4단계 관점별 학습 개선 실험 사전 계획 (2026-10-24)

**변경 범위:** 새 브랜치 `experiment/v23-qci-256-four-step-20261024`, 새 스크립트/새 산출물만. Frozen Stage1~4 및 8,148 원시 평가 원본 수정 금지.

## 1단계: zero-positive 18개 관점 및 애매한 17쌍 재검토
- 기존 감사 18개 중 8개 관점만 한쪽 평가가 positive 인정, 나머지 10개는 두 차례 모두 3점 미만. 관점별 의견 불일치 사례 17쌍.
- 관점별 가까운 2점/2점 사례와 3점/2점 사례의 원문 P/T/C, 두 점수/이유 검토용 큐 생성.
- 기존 점수/기존 qrels/검색 순위를 주지 않는 블라인드 별도 AI 판정은 **Silver 보조감사**이지 인간 Gold가 아니다. 사전 규칙: 2회 의견 엇갈린 17쌍에만 독립 3차 점수로 3점 문턱 다수결 적용. 원본 8,148개와 두 AI 점수는 영구 보존. 0개 관점에 억지 양성 추가 금지.

## 2단계: 학습 데이터
- 기존 두 평가가 일치한 7,979쌍, 긍정 311/부정 7,668 및 갈린 169쌍을 구분. 17개에 별도 재판정이 있을 때만 Silver 보조판정을 추가 사용하며 미검토된 152건은 제외.
- 학습과 검증은 원질의 ID LOQO (held 1개 질문의 3회 및 모든 생성 관점 전체 격리).
- 분쟁 판정 제외. Positive 0개 관점은 별도 기록하고 가짜 positive 생성하지 않는다.

## 3단계: 학습형 256d Multi-view & QCI
- 고정 BGE-M3 1024d 임베딩 97 generated views, 84 cases의 Problem/Task/Context 재사용. 48차원 임의 random projection 없음.
- 모델 `gated_qci_256`: 공유 선형 projection 1024→256, 관점–사례 세 view interaction으로 softmax gate 학습, 256d fused case representation, interaction [q,c,q*c,abs(q-c)] 1024→64→1 MLP.
- 모델 `dense_anchor_gated_qci_256`: 동일 QCI 예측 신호를 Dense 3-view cosine mean+0.10*tanh(QCI score)에 결합하는 고정 비교 변형 (결과를 보고 0.10 변경 금지).
- Positive 불균형 반영 BCE + pairwise 순위 로스; 학습 24 epoch, seed 42, LR 0.002, weight decay 0.001. 동일 고정 feature, 독립 테스트 질문으로만 평가; held query label을 모델 학습/파라미터 선택에 노출하지 않는다.

## 4단계: 원래 모델과 동등 조건 평가
- 비교 기준 = **동일 실행 97 관점–84 사례 qrels에 대한 Dense 3-view**, full84 후보, 동일 runtime 관점 Top5/Top10.
- 이전 보고 63.32%는 정적 평가 reference 관점의 질문-level 합집합 Recall이므로, **새 동적 관점별 Silver Recall과 단순히 수치 비교 금지**. 새 Dense Recall도 재계산.
- primary label=원래 **두 차례 AI 평가 합의** 8,148쌍. 3차 보조판정이 있으면 secondary 개발 실험에서 따로 보고.
- 0 positive view 제외 후 macro Recall/Precision@K, positive 0 뷰 수, per query-run 및 10 original query macro, branch 수, fold 홀드아웃 감사.
- 승리하지 못하면 기존 Dense를 유지하고 학습형 QCI 채택 보류.

**공통 제약:** API-Silver 데이터는 사람 독립 Gold가 아니며, 10개 개발 질문 반복은 독립 Test가 아니다. 교수님이 제안한 핵심 모듈의 목적을 따르는 실험적 구체 구현이지 교수님 코드의 완전한 재현이라고 과장하지 않는다.
