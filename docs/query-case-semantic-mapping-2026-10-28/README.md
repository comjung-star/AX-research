# BGE-M3 의미 기반 Query–Case 정밀 매핑 Dev 비교

2026-10-28 KST

기준 SHA: `be64f9c1f742ecaa6410eeaab97da11ebc6e7f13`. 연구 브랜치: `research/query-case-semantic-mapping-20261028`.

아래 수치는 기존 AI Silver 기준의 개발 데이터 비교다. 의미 유사도는 실제 업무 적합성 판정 확률이 아니다. 설정은 추론 전 고정하고, 전 예측의 hash를 평가 전 저장했다. 결과를 보고 가중치를 조정하지 않았다.

## 핵심 비교

P는 10질문, R/F1은 양성 6질문 Macro(%). 무양성4질문 R/F1은 NA. 동적3회는 질문별 평균 후 Macro다.

|방식|K|P|R|F1|
|---|---:|---:|---:|---:|
|H_F|5|12.000|45.556|23.373|
|H_F|10|9.667|65.000|22.485|
|H_F|20|5.833|70.556|15.400|
|M_D_SINGLE|5|22.667|88.889|46.098|
|M_D_SINGLE|10|15.000|95.000|34.005|
|M_D_SINGLE|20|9.000|100.000|23.251|
|SEM_D_SINGLE|5|19.333|77.778|38.757|
|SEM_D_SINGLE|10|14.000|89.444|31.441|
|SEM_D_SINGLE|20|8.000|92.778|20.691|
|COMB_D_SINGLE|5|24.000|90.000|47.579|
|COMB_D_SINGLE|10|16.000|96.667|35.672|
|COMB_D_SINGLE|20|9.000|100.000|23.251|

SEM은 Task/Action/Object/Output/Context 필드 cosine 가중평균, COMB는 기존 규칙 강도와 의미점수의 사전 고정 1:1 결합이다. 원질문과 최고 관점점수를 1:1로 유지한다. 기존 검색랭킹 H_F는 참조 조건이며 수정하지 않았다.

## 전체 조건

|조건|F1@5|F1@10|F1@20|
|---|---:|---:|---:|
|single_dense__original|31.468|28.108|19.918|
|single_dense__round_robin|31.468|23.209|17.953|
|single_dense__mean_rrf|27.302|25.031|18.807|
|single_dense__original_plus_mean_rrf|32.024|27.552|18.807|
|three_view_dense__original|41.190|24.775|18.807|
|three_view_dense__round_robin|33.968|23.108|16.246|
|three_view_dense__mean_rrf|29.220|22.738|17.953|
|three_view_dense__original_plus_mean_rrf|39.709|24.219|18.066|
|H_C|21.151|25.078|17.357|
|H_F|23.373|22.485|15.400|
|H_S_C3|18.929|19.736|17.357|
|H_S_F3|25.966|21.744|15.265|
|H_S_BM25_O|23.373|16.706|11.218|
|H_S_BM25_M|20.410|17.059|12.065|
|M_O_SINGLE|45.357|32.339|23.251|
|M_D_SINGLE|46.098|34.005|23.251|
|M_O_THREE|45.357|32.339|23.251|
|M_D_THREE|45.357|32.339|23.251|
|SEM_O_SINGLE|37.024|28.108|22.140|
|COMB_O_SINGLE|47.579|34.005|23.251|
|SEM_D_SINGLE|38.757|31.441|20.691|
|COMB_D_SINGLE|47.579|35.672|23.251|
|SEM_O_THREE|37.024|28.108|22.140|
|COMB_O_THREE|47.579|34.005|23.251|
|SEM_D_THREE|38.757|31.441|20.691|
|COMB_D_THREE|47.579|35.672|23.251|

전26조건 P/R/F1 및 질문별 평균/회차 변동은 evaluation/macro_metrics.csv, query_mean_metrics.csv, results.json에 있다.

## 새로 찾고 잃은 Silver 관련 사례

반복 사건 수는 질문×회차×사례 단위이며 동일 사례가 여러 번 포함될 수 있다. 고유 수는 질문-사례 중복을 제거했다. 서로 다른 회차에서 같은 쌍이 신규와 손실 모두에 나타날 수 있다.

|방식|비교대상|K|신규 사건/고유|유지 사건/고유|손실 사건/고유|
|---|---|---:|---:|---:|---:|
|SEM_D_SINGLE|M_D_SINGLE|5|7/3|22/8|12/5|
|SEM_D_SINGLE|M_D_SINGLE|10|8/3|34/12|11/4|
|SEM_D_SINGLE|M_D_SINGLE|20|0/0|48/16|6/2|
|COMB_D_SINGLE|M_D_SINGLE|5|6/2|30/10|4/2|
|COMB_D_SINGLE|M_D_SINGLE|10|8/3|40/14|5/2|
|COMB_D_SINGLE|M_D_SINGLE|20|0/0|54/18|0/0|
|COMB_D_SINGLE|SEM_D_SINGLE|5|8/3|28/10|1/1|
|COMB_D_SINGLE|SEM_D_SINGLE|10|6/2|42/15|0/0|
|COMB_D_SINGLE|SEM_D_SINGLE|20|6/2|48/16|0/0|

전 사례 ID, 신규 Silver 음성 진입, 질문·회차·K별 내역은 evaluation/related_changes.json, 전112후보 순위변동과 실제 Task는 rank_changes.csv에 있다.

## 규칙 미인식 33사례

Task 전체를 사용해 문법 밖 표현도 비교할 수 있다. 필드가 채워졌다는 사실과 의미 해석이 맞다는 사실은 구분해야 한다.

|사례|실제 Task|기존 Silver 양성 질문|미확인 필드|
|---|---|---|---|
|AXALL_US_OMB_2025_01377|Prioritization of actionable survey comments|없음|output|
|AXV24_1e31f41769aa|투숙객 송장 재발송 요청 처리|없음|output|
|AXV24_523997b7101f|뉴스 기사 영문 번역·현지화|없음|output|
|AXV24_625513e68743|CRM 판촉 캠페인 기획·문안·일정 처리|없음|output|
|AXV24_8ece01418f6d|가맹점 점포 사진 기반 등록 확인|없음|output|
|AXV24_918f26607568|반품 상품 사진 확인 및 환불 요청 처리|없음|output|
|AXV24_ec6533f5c076|여행 상황·제약을 반영한 고객 안내|없음|action, output|
|AXV24_f6f7a1e65ea7|직원 결근·지각 연락 접수 및 시스템 반영|없음|action, output|
|AXV2C_0016_01|Caller self-service computer troubleshooting|없음|output|
|AXV2C_0050_02|Discount near-expiry food on shelves|없음|action, output|
|AXV2C_0068_01|Repair incomplete payment instructions|없음|action, output|
|AXV2C_0074_02|Review merchant websites during onboarding|없음|output|
|AXV2H_0021_01|제조 로봇 예지보전|없음|action, output|
|AXV2H_0078_01|사내 관리데이터 자연어 조회|없음|action, output|
|AXV2N_0103|Reconcile bank transactions at month end|없음|action, output|
|AXV2N_0105|Assist store associates with customer project questions|없음|output|
|AXV2N_0106|Advise online customers on home-improvement projects|없음|action, output|
|AXV2N_0107|Give online home-improvement project advice|없음|action, output|
|AXV2N_0109|Explain personalized job invitations|없음|action, output|
|AXV2N_0115|Produce approved lifestyle images for product advertising|없음|없음|
|AXV2N_0118|Unload cartons from trailers onto conveyors|없음|output|
|AXV2N_0120|Apply herbicide only where weeds are detected|없음|output|
|AXV2N_0128|Check warning-triangle placement in the trunk|없음|output|
|AXV2N_0130|Automate routine support-case administration|없음|output|
|AXV2N_0132|Document medical-care conversations|없음|action, output|
|AXV2N_0133|Investigate escalated claim-processing questions|없음|output|
|AXV2P2_0019_01|Prepare and submit journal entries under approval|없음|action, output|
|AXV2P2_0020_01|Coordinate property insurance claim resolution|없음|action, output|
|AXV2P2_0035_01|Use AI as one reader in breast screening|없음|output|
|AXV2P2_0089_01|Book employee annual leave|없음|action, output|
|AXV2P2_0097_01|Depalletize boxes in a frozen warehouse|없음|action, output|
|AXV2P2_0099_01|Automate steel marking|없음|output|
|AXV2P2_0100_01|Screen and assess applicant self-introductions|없음|action, output|

이 33사례에 속한 기존 Silver 양성 질문-사례는 0쌍이다. 질문별 전체 순위 및 Silver 점수는 evaluation/unknown33_ranks.csv에 저장했다.

## 제조 불량·고객 답변·HR 질문응답

사전 지정된 진단 사례이며 독립 테스트가 아니다. 분야가 달라도 질문응답 행동은 비슷할 수 있지만, 고객 응대와 직원 규정 답변의 적용 맥락은 다르다. 품질이라는 단어만으로 제조 불량 분석이 고객 답변 품질 개선을 수행한다고 해석하지 않는다.

|사례|필드|원문에서 추출한 내용|
|---|---|---|
|AXV2N_0121|task|Answer customer help-centre questions|
|AXV2N_0121|action|Answer|
|AXV2N_0121|object|customer help-centre questions|
|AXV2N_0121|output|UNKNOWN|
|AXV2N_0121|context|Customer-facing help centre, distinct from call summarization.|
|AXV2N_0124|task|Answer employee HR policy questions|
|AXV2N_0124|action|Answer|
|AXV2N_0124|object|employee HR policy questions|
|AXV2N_0124|output|UNKNOWN|
|AXV2N_0124|context|Penny HR chatbot for over 8000 employees in Malaysia and Asia.|
|AXV2C_0093_01|task|Analyze production quality defects and root causes|
|AXV2C_0093_01|action|Analyze|
|AXV2C_0093_01|object|production quality defects and root causes|
|AXV2C_0093_01|output|UNKNOWN|
|AXV2C_0093_01|context|Suzhou Universal MES, ERP and quality systems.|

|방식|회차|사례|순위|Silver|
|---|---:|---|---:|---:|
|H_F|1|AXV2N_0121|2|3|
|H_F|1|AXV2N_0124|60|3|
|H_F|1|AXV2C_0093_01|50|0|
|H_F|2|AXV2N_0121|1|3|
|H_F|2|AXV2N_0124|62|3|
|H_F|2|AXV2C_0093_01|39|0|
|H_F|3|AXV2N_0121|4|3|
|H_F|3|AXV2N_0124|52|3|
|H_F|3|AXV2C_0093_01|40|0|
|M_D_SINGLE|1|AXV2N_0121|3|3|
|M_D_SINGLE|1|AXV2N_0124|15|3|
|M_D_SINGLE|1|AXV2C_0093_01|65|0|
|M_D_SINGLE|2|AXV2N_0121|3|3|
|M_D_SINGLE|2|AXV2N_0124|16|3|
|M_D_SINGLE|2|AXV2C_0093_01|56|0|
|M_D_SINGLE|3|AXV2N_0121|4|3|
|M_D_SINGLE|3|AXV2N_0124|14|3|
|M_D_SINGLE|3|AXV2C_0093_01|59|0|
|SEM_D_SINGLE|1|AXV2N_0121|1|3|
|SEM_D_SINGLE|1|AXV2N_0124|8|3|
|SEM_D_SINGLE|1|AXV2C_0093_01|29|0|
|SEM_D_SINGLE|2|AXV2N_0121|1|3|
|SEM_D_SINGLE|2|AXV2N_0124|6|3|
|SEM_D_SINGLE|2|AXV2C_0093_01|25|0|
|SEM_D_SINGLE|3|AXV2N_0121|1|3|
|SEM_D_SINGLE|3|AXV2N_0124|8|3|
|SEM_D_SINGLE|3|AXV2C_0093_01|26|0|
|COMB_D_SINGLE|1|AXV2N_0121|3|3|
|COMB_D_SINGLE|1|AXV2N_0124|8|3|
|COMB_D_SINGLE|1|AXV2C_0093_01|43|0|
|COMB_D_SINGLE|2|AXV2N_0121|3|3|
|COMB_D_SINGLE|2|AXV2N_0124|7|3|
|COMB_D_SINGLE|2|AXV2C_0093_01|42|0|
|COMB_D_SINGLE|3|AXV2N_0121|3|3|
|COMB_D_SINGLE|3|AXV2N_0124|8|3|
|COMB_D_SINGLE|3|AXV2C_0093_01|42|0|
|SEM_O_SINGLE|0|AXV2N_0121|2|3|
|SEM_O_SINGLE|0|AXV2N_0124|14|3|
|SEM_O_SINGLE|0|AXV2C_0093_01|38|0|
|COMB_O_SINGLE|0|AXV2N_0121|4|3|
|COMB_O_SINGLE|0|AXV2N_0124|11|3|
|COMB_O_SINGLE|0|AXV2C_0093_01|48|0|

원질문 및 모든 Q1 관점의 필드별 cosine과 가용 가중치는 evaluation/mandatory_cases.json에 있다. query_profiles.json/case_profiles.json은 원문 위치를 제공하고 mapping/mappings.jsonl은 전13,216쌍을 제공한다.

## 해석 한계와 다음 결정

- 10 Dev 질문·18양성쌍의 희소한 AI Silver 평가다. 사람 Gold, 독립 공급자 합의, 일반화, 통계적 유의성을 증명하지 않는다.
- 기존 예시와 Dev 결과가 알려진 상태에서 설계했다. 전처리·추론에 Silver를 넣지 않았지만 설계자 수준의 완전 눈가림은 아니다. 학습은 없으므로 학습/검증 분할 성능으로 표현하지 않는다.
- Action은 넓은 표면 패턴, Object는 잔여 구절이다. 의미역과 수식 범위를 정확히 분리했다고 주장하지 않는다. Task 제목이 짧거나 모호하면 대응 의미도 제한된다. 기존 부정/미래 가드는 정상 Task도 과도하게 보류할 수 있다.
- Output은 명시 문자열만 인정해 대부분 UNKNOWN일 수 있다. 산출물을 임의로 채워 완성된 다섯 의미역 비교처럼 제시하지 않는다. 누락 필드별 분모 차이와 query/case Context 추출 비대칭은 점수 비교의 한계다.
- 원질문에서 원하는 작업과 사례가 실제 수행한 작업의 언어적 유사도를 측정한다. 요구사항 전체 충족, 배포 가능성, 보안, 실제 효과나 원 출판물 사실성을 보증하지 않는다. Context는 실행 증거를 대신하지 않는다.
- 최고 관점 연산은 중복 가산을 막지만 우연히 높은 한 관점이 순위를 올릴 수 있다. 가중치·규칙강도/4·cosine 변환은 확률 보정값이 아니다. 1:1 결합은 임의 실험 선택이며 최적값이라고 주장하지 않는다.
- 원질문/관점 Single 및 3View는 동일 매핑을 사용하고 기존 검색점수 동점 처리만 다르다. 이는 BGE 표현을 새로 3View 학습한 실험이 아니다. 저장한 과거 RRF는 역사적 검색 참조다.
- 독립 Stage4 Test는 열람·실행하지 않았다. 새 유료 API, 라벨 생성, 파인튜닝은 0이다. 기존 모델의 CPU 추론은 로컬 자원을 사용했다. 외부 공증 없이 로컬 hash로 실행 순서를 기록했다.

다음 선택은 결과가 좋은 단일 지표만 보고 내리지 않는다. 신규/손실 사례와 Task 근거를 검토하고, 별도 사람 검증 또는 차기 사전등록 실험이 준비된 뒤 확정한다. 이번 Dev 결과만으로 독립 Test를 개봉하지 않는다.

## 재현

저장소 루트에서 기존 AX-prototype 가상환경을 사용한다. PYTHONPATH=src와 HF_HUB_OFFLINE=1을 적용한다.

```text
python -m pytest tests/test_functional_mapping.py tests/test_semantic_mapping.py
python -m scripts.semantic_mapping_run freeze
python -m scripts.semantic_mapping_run run
python -m scripts.semantic_mapping_evaluate
```

freeze는 기준 HEAD와 고정 해시를 요구하며 설정이 바뀐 재실행은 거부한다. 모델·원본 입력 경로·정확한 패키지 버전은 preregistration.json에 있다. Git 커밋 후에는 기존 봉인 파일로 run/evaluate를 재실행한다.
