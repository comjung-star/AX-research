# 행동 정보 누락 확인 및 추출 보완 — 1~2단계 완료

2026-11-09. **저장된 사례112개 중 행동 필드가 비어 있던24개를 확인하고, 원문에 있는 행동 표현을 추출하는 별도 보완 버전을 만들었다. 보완본의 빈 행동 필드는24개에서0개가 됐다.** 이는 어휘 추출 범위 복원이며, 올바른 의미 이해나 추천 성능 향상을 입증한 결과가 아니다.

## 1. 무엇을 확인했나

기준 원문은 사례 저장소의 구조화된 Task 요약이다. 원출판물 전체를 다시 검증한 작업은 아니다. 각 사례의 기존 semantic profile을 현재 동결 규칙으로 재생성해112개 모두 일치함을 먼저 확인했다. 비어 있던24개는 지원되는 Task 문장이 있는데도 기존 action_pattern과 일치하는 표현이 없었다. 부정/미래계획 문장을 보류해 비어 있던 경우는 이24개에는 없었다.

한국어7개, 영어17개다. 두 종류의 규칙 처리 범위가 달랐다. 기존 기능 규칙 파서는 ‘응대’를 인식하지만, 별도의 의미 필드 추출용 규칙에는 ‘응대’가 없었다. 영어에서도 Resolve, Repair, Anonymize 등 여러 동사가 누락됐다. 기존 행동 필드가 비었다고 원문에 행동이 없다고 해석하면 안 된다.

## 2. 어떻게 고쳤나

- 기존20261028 규칙과 과거 profile을 보존하고, 별도 `literal-action-recovery-v2-20261109`를 만들었다.
- 행동 필드가 빈 경우에만 보완 규칙을 적용했다. 기존 비어 있지 않은88개 profile의 모든 기존 필드와 메타데이터는 그대로다.
- 원문에 존재하는 표현만 사용한다. 각 추출 표현에 인용 문자열, 시작/끝 위치, 적용 규칙, 해당 문장을 기록했다. 예지보전을 ‘예측’으로 바꾸거나 advice를 원문에 없는 Advise로 바꾸지 않았다.
- ‘Book’, ‘Document’, ‘Screen’처럼 명사일 수 있는 영어 표현은 휴가 예약/대화 기록/지원자 심사 문맥으로 제한했다. ‘Book title’, ‘Document title’, ‘Screen dimensions’를 행동으로 복원하지 않는지 확인했다. 한국어는 단어 경계를 확인해 ‘안내문·접수번호·조회수’를 해당 행동으로 잡지 않도록 했다.
- 새 행동 부분은 기존의 얕은 대상 잔여 문자열에서 제외했다. 대상의 의미 역할까지 정확하게 분석했다는 뜻은 아니다. 일부 잔여 문자열에는 접속어/상황어가 남으며 후속 의미 비교에서 그대로 정답으로 취급하면 안 된다.
- 부정/미구현 문장의 보류는 기존 규칙을 유지했다. Context에만 있는 행동을 Task에 끌어오지 않고, 여전히 모르는 표현은 UNKNOWN으로 남긴다. 기존 부정문 처리의 완전성을 새로 보장하는 작업은 아니다.

## 24개 사례별 결과

아래 표현은 모두 해당 Task 원문에 있다. `/`는 서로 다른 원문 조각을 구분한다.

|사례 ID|Task 원문|복원한 행동 표현|
|---|---|---|
|AXV24_71def85d86bd|의료기관의 보험 자격·보장 음성 문의 응대|응대|
|AXV24_df5d48fedff4|RV 고객 문의의 상시 응대 및 상담원 인계|응대 / 인계|
|AXV24_ec6533f5c076|여행 상황·제약을 반영한 고객 안내|안내|
|AXV24_f6f7a1e65ea7|직원 결근·지각 연락 접수 및 시스템 반영|접수 / 반영|
|AXV2C_0017_01|Resolve telecom customer inquiries with remembered context|Resolve|
|AXV2C_0050_02|Discount near-expiry food on shelves|Discount|
|AXV2C_0068_01|Repair incomplete payment instructions|Repair|
|AXV2H_0021_01|제조 로봇 예지보전|예지보전|
|AXV2H_0078_01|사내 관리데이터 자연어 조회|조회|
|AXV2H_0083_01|신규 버그 티켓 팀 라우팅|라우팅|
|AXV2N_0103|Reconcile bank transactions at month end|Reconcile|
|AXV2N_0106|Advise online customers on home-improvement projects|Advise|
|AXV2N_0107|Give online home-improvement project advice|advice|
|AXV2N_0108|Resolve customer service inquiries across channels|Resolve|
|AXV2N_0109|Explain personalized job invitations|Explain|
|AXV2N_0132|Document medical-care conversations|Document|
|AXV2N_0136|Anonymize people in production images|Anonymize|
|AXV2P2_0011_01|Audit freight invoices for overcharges|Audit|
|AXV2P2_0019_01|Prepare and submit journal entries under approval|Prepare / submit|
|AXV2P2_0020_01|Coordinate property insurance claim resolution|Coordinate|
|AXV2P2_0069_01|Create CRM contacts from customer emails|Create|
|AXV2P2_0089_01|Book employee annual leave|Book|
|AXV2P2_0097_01|Depalletize boxes in a frozen warehouse|Depalletize|
|AXV2P2_0100_01|Screen and assess applicant self-introductions|Screen / assess|

## 검증 범위와 남은 한계

추출 결과112개를 원래 Task/Context의 문자 위치와 대조했다. 복원24개의 결과를 모두 원문과 비교하고, 기존88개는 변하지 않았음을 확인했다. 전체112개 재현, 입력/소스 해시 대조, 관련 테스트34개 및 하위 검사6개가 통과했다. 사람이 만든 Gold를 새로 구축하거나 제삼자가 의미 정확도를 독립 평가한 것은 아니다. 개발 사례에서 발견한 어휘를 보완한 규칙이며, 새로운 자료에서도 같은 정확도를 보장하지 않는다.

今回の範囲は1~2段階だけ。質問の要求/除外条件の新しい解析、埋め込み再計算、行動cosineの480ペアの再計算、候補/推薦順変更、F1/nDCG評価は行っていない。旧結果の欠損数値が今回の抽出だけで埋まったわけではない。既存の正解表、新40問、Test15は読んでいない。有料API呼び出し0回。

## 再現資料

- [24件の前後・原文位置・規則根拠](missing24-audit.json)
- [112件の補完profile](case_profiles.json)
- [件数・原本ハッシュ・検証記録](verification.json)
- [追加ルール](../../configs/literal_action_recovery_20261109.json)
- [抽出実装](../../src/ax_research/literal_action_recovery.py)
- [生成スクリプト](../../scripts/recover_case_actions_20261109.py)
- [再現チェッカー](../../scripts/verify_action_recovery_20261109.py)

再生成は `python -m scripts.recover_case_actions_20261109`、既存成果物の照合は `python -m scripts.verify_action_recovery_20261109`。前者は出力先が既存なら上書きを拒否する。いずれもローカルモジュールが読める環境で実行する。GitHubへのアップロードや運用推薦モデルの切り替えはしていない。
