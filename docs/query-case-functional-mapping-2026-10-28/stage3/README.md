# Stage3: 기능 근거 기반 최종 후보

주 조건 M_D_SINGLE은 원질문과 각 관점의 기능 매핑을 함께 사용한다. 관점점수를 합산하지 않고 최고 근거를 사용한다. 원질문 근거도 정렬에 남긴다. 같은 매핑 근거끼리는 기존 하이브리드 검색점수로 정렬한다. 원질문만 사용하는 조건과 3View 조건도 별도 보존했다.

전체80개 질문/회차 순위와112후보 설명을 먼저 저장했다. Silver는 아직 읽지 않았다. Top5/10/20을 동일 순위에서 자르고 ID중복을 제거했다. 기능 근거가 낮은 항목으로 채운 경우 low_support_padding=true이며 적합한 추천이라고 보증하지 않는다.

아래는 주 조건의 첫 생성 회차 Top5 예시다. 모든3회×질문×Top20의 실제Task·전체/관점근거·기존검색순위·주의사항은 top20_explanations.csv/jsonl에 있다. 상세원문 인용은 Stage2 프로필과 연결된다.

## V21D001

|순위|사례|실제 Task|전체/관점 근거 점수|
|---:|---|---|---|
|1|AXV2H_0071_01|결제 기술문의 검색·답변|4/4|
|2|AXV2H_0070_01|배달원 음성 상담 자동응답|4/4|
|3|AXV2N_0121|Answer customer help-centre questions|3/3|
|4|AXV24_df5d48fedff4|RV 고객 문의의 상시 응대 및 상담원 인계|3/3|
|5|AXV2H_0090_01|Answer routine employee HR policy questions|3/3|

## V21D002

|순위|사례|실제 Task|전체/관점 근거 점수|
|---:|---|---|---|
|1|AXV2H_0002_01|고객 이메일 요약|4/4|
|2|AXV2N_0111|Summarize client meetings and prepare follow-ups|4/3|
|3|AXV2H_0003_01|직원 신원조회 보고서 검증|1/4|
|4|AXV24_36c7ef329920|채용 지원서·증빙 자료 대조 검토|1/4|
|5|AXV2P2_0011_01|Audit freight invoices for overcharges|1/4|

## V21D003

|순위|사례|실제 Task|전체/관점 근거 점수|
|---:|---|---|---|
|1|AXV24_f27ca1e6fb82|여러 사내 업무 시스템의 지식 통합 검색|4/3|
|2|AXALL_US_OMB_2025_02663|Document retrieval and cross-reference support|4/3|
|3|AXV2N_0110|Retrieve internal knowledge for financial advisors|4/3|
|4|AXV2P2_0010_01|Retrieve CAD/CAM product support knowledge|3/3|
|5|AXV2H_0003_01|직원 신원조회 보고서 검증|2/2|

## V21D004

|순위|사례|실제 Task|전체/관점 근거 점수|
|---:|---|---|---|
|1|AXV2H_0003_01|직원 신원조회 보고서 검증|4/4|
|2|AXV24_36c7ef329920|채용 지원서·증빙 자료 대조 검토|4/4|
|3|AXV2C_0080_02|Flag document details for sanctions screening|4/4|
|4|AXV2P2_0011_01|Audit freight invoices for overcharges|4/4|
|5|AXV24_28baf265c6cf|보험 인수심사용 신청 서류 추출·분류|3/3|

## V21D005

|순위|사례|실제 Task|전체/관점 근거 점수|
|---:|---|---|---|
|1|AXV2H_0078_01|사내 관리데이터 자연어 조회|1/1|
|2|AXV2H_0008_01|세무 문서 데이터 추출|1/1|
|3|AXV24_f27ca1e6fb82|여러 사내 업무 시스템의 지식 통합 검색|1/1|
|4|AXALL_US_OMB_2025_01589|Loan document data extraction for examination analytics|1/1|
|5|AXV24_7a64efedc8a2|보험 상품 설계용 과거 의료 청구 데이터 구조화|1/1|

## V21D006

|순위|사례|실제 Task|전체/관점 근거 점수|
|---:|---|---|---|
|1|AXV2H_0084_01|고객 상품 위치 검색|4/4|
|2|AXV2H_0086_01|고객 상품 검색·발견|3/3|
|3|AXV24_98092b8ca357|상품 카탈로그 속성 추출·분류|3/3|
|4|AXV24_f27ca1e6fb82|여러 사내 업무 시스템의 지식 통합 검색|3/3|
|5|AXV24_06318a4a88a8|기업 경비 제출·분류 처리|3/3|

## V21D007

|순위|사례|실제 Task|전체/관점 근거 점수|
|---:|---|---|---|
|1|AXV2N_0111|Summarize client meetings and prepare follow-ups|4/3|
|2|AXV24_36c7ef329920|채용 지원서·증빙 자료 대조 검토|2/4|
|3|AXV2H_0003_01|직원 신원조회 보고서 검증|1/4|
|4|AXV2P2_0011_01|Audit freight invoices for overcharges|1/4|
|5|AXV2C_0080_02|Flag document details for sanctions screening|1/4|

## V21D008

|순위|사례|실제 Task|전체/관점 근거 점수|
|---:|---|---|---|
|1|AXV2C_0094_02|Prepare manufacturing production plans|4/1|
|2|AXV2C_0093_02|Adjust production schedules with validation|4/1|
|3|AXV24_a3975df095c3|식품 공급망 수요 예측|3/3|
|4|AXV24_2be1ea1c5140|임대 전력·온도조절 장비의 고장 위험 예측|3/3|
|5|AXV2C_0050_01|Forecast daily store-item demand|3/3|

## V21D009

|순위|사례|실제 Task|전체/관점 근거 점수|
|---:|---|---|---|
|1|AXV24_f27ca1e6fb82|여러 사내 업무 시스템의 지식 통합 검색|3/3|
|2|AXV24_14dca9ee14fc|감사 자료 반려·재제출 안내문 작성|2/1|
|3|AXV2N_0114|Generate branded lifestyle advertising images|2/0|
|4|AXV2C_0094_01|Draft customer manufacturing quotes|2/0|
|5|AXV2N_0125|Create sales-meeting recaps and next steps|2/0|

## V21D010

|순위|사례|실제 Task|전체/관점 근거 점수|
|---:|---|---|---|
|1|AXV2C_0094_02|Prepare manufacturing production plans|4/4|
|2|AXV2C_0093_02|Adjust production schedules with validation|4/4|
|3|AXV2C_0093_01|Analyze production quality defects and root causes|4/3|
|4|AXV2P2_0065_01|Investigate paint-quality defect drivers and support root-cause decisions|3/3|
|5|AXV2H_0003_01|직원 신원조회 보고서 검증|2/2|

