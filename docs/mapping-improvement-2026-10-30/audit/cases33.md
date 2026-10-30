# 미인식33개 전수 분석

AI 분석이며 사람 정답이 아니다. 원 출판물 대신 기존 Task/Context 구조화 원문을 확인했다. 미인식은 추천 부적합을 의미하지 않는다. B의 비교 가능은 점수 산출 가능이지 정확성 보장이 아니다.

|사례|실제Task|행동 / 대상(원문)|Output|Context|원인 / 처리|B비교|
|---|---|---|---|---|---|---|
|AXALL_US_OMB_2025_01377|Prioritization of actionable survey comments|Prioritization / actionable survey comments|명시없음; 추정하지 않음|Bureau of Labor Statistics staff reviewing website satisfaction feedback.|OUTSIDE18: 의견 우선순위화는18기능에 없다. 분류나 요약으로 바꾸지 않는다.|True|
|AXV24_1e31f41769aa|투숙객 송장 재발송 요청 처리|재발송 / 송장|명시없음; 추정하지 않음|최근 60일 내 투숙 여부를 확인해 PDF 송장을 보내는 고객지원 업무.|OUTSIDE18: 기존 송장 재발송은 검색·생성·문서검증과 다른 업무다.|True|
|AXV24_523997b7101f|뉴스 기사 영문 번역·현지화|번역·현지화 / 뉴스 기사|명시없음; 추정하지 않음|한국어 기사와 뉴스룸 용어집을 사용하는 영문 뉴스 발행 업무.|OUTSIDE18: 번역·현지화 기능이 없다. 요약과 구분해야 한다.|True|
|AXV24_625513e68743|CRM 판촉 캠페인 기획·문안·일정 처리|기획 / CRM 판촉 캠페인|명시없음; 추정하지 않음|전자상거래 고객 대상 판촉 캠페인 운영.|UNDERSPECIFIED_ACTION: 문안이라는 명사는 있으나 실제 작성 동작은 Task에 명시되지 않았다. 일정 처리의 세부 동작도 부족하다.|True|
|AXV24_8ece01418f6d|가맹점 점포 사진 기반 등록 확인|확인 / 가맹점 점포 사진|명시없음; 추정하지 않음|인도 오프라인 가맹점의 디지털 결제 서비스 가입 업무.|OUTSIDE18: 사진 기반 등록 확인은 시각 검증이다. 문서 검증과 같은 기능으로 자동 승격하지 않는다.|True|
|AXV24_918f26607568|반품 상품 사진 확인 및 환불 요청 처리|확인 / 반품 상품 사진|명시없음; 추정하지 않음|미용 상품의 손상·유효기간을 확인하는 전자상거래 반품 업무.|OUTSIDE18: 사진 확인과 환불 요청 처리는 문서 검증·응답만으로 표현되지 않는다.|True|
|AXV24_ec6533f5c076|여행 상황·제약을 반영한 고객 안내|안내 / 고객|명시없음; 추정하지 않음|Trip.com의 여행 서비스 운영에서 시간·예산·인원·선호에 맞는 고객 안내.|UNDERSPECIFIED_ACTION: 여행 상황 기반 안내다. 질문 응답인지 신규 문안 작성인지 Task만으로 확정하기 어렵다.|True|
|AXV24_f6f7a1e65ea7|직원 결근·지각 연락 접수 및 시스템 반영|접수 / 직원 결근·지각 연락|명시없음; 추정하지 않음|계절 근로자가 많은 놀이공원 운영의 근무 연락 업무.|OUTSIDE18: 연락 접수·시스템 반영은 단순 질의응답이나 시스템 통합과 다르다.|True|
|AXV2C_0016_01|Caller self-service computer troubleshooting|troubleshooting / computer|명시없음; 추정하지 않음|Best Buy customers calling for computer assistance.|OUTSIDE18: 컴퓨터 문제 해결은 품질 불량 원인 분석용 기존 문법 범위와 다르다.|True|
|AXV2C_0050_02|Discount near-expiry food on shelves|Discount / near-expiry food|명시없음; 추정하지 않음|Albert Heijn stores with electronic shelf labels.|OUTSIDE18: 가격 할인은 추천이나 수량 예측이 아니다.|True|
|AXV2C_0068_01|Repair incomplete payment instructions|Repair / incomplete payment instructions|명시없음; 추정하지 않음|BNY cross-border payment processing.|OUTSIDE18: 지급지시 보완은 검증 이후의 수정 작업이다. 확인과 수정 구분 필요.|True|
|AXV2C_0074_02|Review merchant websites during onboarding|Review / merchant websites|명시없음; 추정하지 않음|Cashfree Payments onboarding Indian merchants; payment data stays in India.|LEXICAL_OBJECT: 검토 동사는 기존에 있으나 웹사이트라는 문서 대상을 문법이 포함하지 않는다.|True|
|AXV2H_0021_01|제조 로봇 예지보전|예지보전 / 제조 로봇|명시없음; 추정하지 않음|현대차 자동차 공장 다수 로봇팔의 공정 진단|COMPOUND_INSUFFICIENT_DETAIL: 압축된 전문 복합어다. 어떤 데이터를 사용해 무엇을 예측하는지 별도 행동·대상 근거가 없다.|True|
|AXV2H_0078_01|사내 관리데이터 자연어 조회|조회 / 사내 관리데이터|명시없음; 추정하지 않음|Kohl's의 여러 매장·업무 부서가 거버넌스된 엔터프라이즈 데이터에 접근|LEXICAL_OBJECT: 조회 동사는 있지만 데이터가 지식 검색의 대상 표현에서 빠져 있다.|True|
|AXV2N_0103|Reconcile bank transactions at month end|Reconcile / bank transactions|명시없음; 추정하지 않음|U.S. AutoForce accounting team running US Bank reconciliations for three months.|LEXICAL_OBJECT: 대조 동사는 있으나 거래 기록 표현이 대상에서 빠져 있다.|True|
|AXV2N_0105|Assist store associates with customer project questions|Assist / store associates|명시없음; 추정하지 않음|Mylow Companion on associate sales-floor devices across over 1700 stores.|UNDERSPECIFIED_ACTION: 질문 관련 직원 지원만 명시. 실제 답변·검색·조치를 무엇으로 수행하는지는 확정하기 어렵다.|True|
|AXV2N_0106|Advise online customers on home-improvement projects|Advise / online customers|명시없음; 추정하지 않음|Customer-facing Mylow virtual advisor, distinct from the associate application.|OUTSIDE18: 프로젝트 조언을 질문 응답과 동일하다고 단정할 수 없다.|True|
|AXV2N_0107|Give online home-improvement project advice|Give / home-improvement project advice|명시없음; 추정하지 않음|Magic Apron on Home Depot digital platforms.|OUTSIDE18: 조언 제공이다. 구체적인 질의응답 동작까지 원문에서 보장하지 않는다.|True|
|AXV2N_0109|Explain personalized job invitations|Explain / personalized job invitations|명시없음; 추정하지 않음|Invite to Apply production messages at marketplace scale.|OUTSIDE18: 초대 이유 설명은 기존18기능과 직접 대응되지 않는다.|True|
|AXV2N_0115|Produce approved lifestyle images for product advertising|Produce / approved lifestyle images|approved lifestyle images|Onkata manages FyterTech advertising and obtains brand approval.|LEXICAL_ACTION: 이미지는 기존 생성 대상이지만 produce 동의어가 생성 동사에서 빠져 있다.|True|
|AXV2N_0118|Unload cartons from trailers onto conveyors|Unload / cartons|명시없음; 추정하지 않음|First commercial Stretch deployment in January 2023.|OUTSIDE18: 물리적 하역 기능은18개 정보업무 규칙에 없다.|True|
|AXV2N_0120|Apply herbicide only where weeds are detected|Apply / herbicide|명시없음; 추정하지 않음|See and Spray used across over five million acres in the 2025 season.|OUTSIDE18: 잡초 감지 조건에 따른 제초제 살포는 물리적 적용 작업이다. 감지를 Task의 주 동작으로만 바꾸면 안 된다.|True|
|AXV2N_0128|Check warning-triangle placement in the trunk|Check / warning-triangle placement|명시없음; 추정하지 않음|BMW series-production image inspection described in December 2019.|OUTSIDE18: 물체 위치 검사는 문서 검증 대상이 아니다.|True|
|AXV2N_0130|Automate routine support-case administration|Automate / routine support-case administration|명시없음; 추정하지 않음|Automate SW Support deployed to 2800 engineers worldwide.|UNDERSPECIFIED_ACTION: 행정 자동화의 구체적 수행 기능이 없다. 문의 답변을 수행했다고 추정하면 안 된다.|True|
|AXV2N_0132|Document medical-care conversations|Document / medical-care conversations|명시없음; 추정하지 않음|Oscar clinical staff documenting care interactions.|OUTSIDE18: 대화를 기록하는 업무다. 요약·전사·새 문안 생성 중 무엇인지 미확정이다.|True|
|AXV2N_0133|Investigate escalated claim-processing questions|Investigate / escalated claim-processing questions|명시없음; 추정하지 않음|Oscar claims team answering questions about a claim's processing history.|OUTSIDE18: 보험처리 질문 조사는 제조 불량 원인 분석과 다른 대상·목적이다.|True|
|AXV2P2_0019_01|Prepare and submit journal entries under approval|Prepare and submit / journal entries|명시없음; 추정하지 않음|IBM Finance Jobotx deployment in early 2025|OUTSIDE18: 회계분개 작성·제출 기능이 없다. 승인 조건은 검증 수행의 증거가 아니다.|True|
|AXV2P2_0020_01|Coordinate property insurance claim resolution|Coordinate / property insurance claim resolution|명시없음; 추정하지 않음|Claims Connection Group policyholders, claim handlers and assigned vendors|OUTSIDE18: 보험 청구 해결 조정 기능이 없다.|True|
|AXV2P2_0035_01|Use AI as one reader in breast screening|Use AI as one reader / breast screening|명시없음; 추정하지 않음|Capio S:t Göran Hospital, Sweden, full integration since mid-2023 after ScreenTrustCAD trial|OUTSIDE18: 영상 판독 기능이 없다. screening을 일반 서류심사로 오인하지 않아야 한다.|True|
|AXV2P2_0089_01|Book employee annual leave|Book / employee annual leave|명시없음; 추정하지 않음|Inspire internal employee HR portal|OUTSIDE18: 연차 예약·등록 업무다. 직원이라는 대상 공통점만으로 지식검색과 일치시킬 수 없다.|True|
|AXV2P2_0097_01|Depalletize boxes in a frozen warehouse|Depalletize / boxes|명시없음; 추정하지 않음|CMES deployment with Hyundai Movex; ten systems in an actual cold logistics center|OUTSIDE18: 물리적 상자 분리 기능이 없다.|True|
|AXV2P2_0099_01|Automate steel marking|Automate / steel marking|명시없음; 추정하지 않음|SeAH Besteel steel manufacturing line|OUTSIDE18: 강재 마킹 기능이 없다. 정보 생성과 물리적 표기는 구분한다.|True|
|AXV2P2_0100_01|Screen and assess applicant self-introductions|Screen and assess / applicant self-introductions|명시없음; 추정하지 않음|Saramin 등용문S recruitment management integrated with Muhayu Prism|LEXICAL_OBJECT: 심사 동사가 있으나 자기소개서 표현은 기존 문서 대상에 포함되지 않았다. applicant만으로 모든 채용을 심사로 매칭하지 않는다.|True|
