# 관점별 참고 사례 표시 예시

수동 동작 예시와 이전 실제 LLM 응답을 구분한다. 새 기준으로 LLM을 호출하거나 검색 성능을 평가한 결과가 아니다.

## manual_alternative_for_one_problem

> 고객 문의 답변이 늦어져 대기가 길어집니다. 참고할 실제 사례를 보고 싶습니다.

**출처:** 수동으로 구성한 동작 예시

**표시:** 관점 2개 / 관점별 표시 합계 7개 / 중복 제외 사례 7개

### P01 업무 지식이 길고 분산돼 필요한 근거를 찾는 데 시간이 걸림

**연결 유형:** 다른 관점에서 검토할 가설

**질문 근거:** “고객 문의 답변이 늦어져”

답변 근거를 찾는 시간이 지연 요인이라면 내부 지식 검색 사례가 참고가 될 수 있습니다.

**확인하지 않은 가정:**

- 직원이 답변 근거를 찾는 시간이 지연의 일부인지 아직 확인되지 않았습니다.

|순위|참고 사례|다른 연결 관점|
|---|---|---|
|1|AXALL_US_OMB_2025_02663 — Document retrieval and cross-reference support|없음|
|2|AXV2N_0110 — Retrieve internal knowledge for financial advisors|없음|
|3|AXV2P2_0010_01 — Retrieve CAD/CAM product support knowledge|없음|

**AXALL_US_OMB_2025_02663를 참고하는 이유:** 답변 근거를 찾는 시간이 지연 요인이라면 내부 지식 검색 사례가 참고가 될 수 있습니다. 이 사례에서 실제 확인된 업무: 문서 검색 및 교차참조 지원.

**차이·확인할 조건:**

- 정책 승인이나 규제 적합성 확정 기능까지 뜻하지 않음
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.
- 이 관점의 원인 가정은 확인되지 않았습니다: 직원이 답변 근거를 찾는 시간이 지연의 일부인지 아직 확인되지 않았습니다.

**AXV2N_0110를 참고하는 이유:** 답변 근거를 찾는 시간이 지연 요인이라면 내부 지식 검색 사례가 참고가 될 수 있습니다. 이 사례에서 실제 확인된 업무: 내부 지식 검색.

**차이·확인할 조건:**

- 외부 고객의 금융판단 대행으로 확대하지 않음
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.
- 이 관점의 원인 가정은 확인되지 않았습니다: 직원이 답변 근거를 찾는 시간이 지연의 일부인지 아직 확인되지 않았습니다.

**AXV2P2_0010_01를 참고하는 이유:** 답변 근거를 찾는 시간이 지연 요인이라면 내부 지식 검색 사례가 참고가 될 수 있습니다. 이 사례에서 실제 확인된 업무: CAD/CAM 지원지식 검색.

**차이·확인할 조건:**

- 제품 조작·설계 변경의 자동 실행은 미확인
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.
- 이 관점의 원인 가정은 확인되지 않았습니다: 직원이 답변 근거를 찾는 시간이 지연의 일부인지 아직 확인되지 않았습니다.

### P04 문의량·접수 시간대가 응대 가능 용량을 넘어 대기·누락이 생김

**연결 유형:** 질문에 명시된 문제·업무

**질문 근거:** “고객 문의 답변이 늦어져 대기가 길어집니다”

문의 응대 지연과 대기가 질문에 명시돼 있어 응대 용량·공백 대응 사례를 살펴봅니다.

|순위|참고 사례|다른 연결 관점|
|---|---|---|
|1|AXV2P2_0060_01 — Answer airline customer service questions|없음|
|2|AXV2H_0001_01 — 고객 문의 자율응답|없음|
|3|AXV24_71def85d86bd — 의료기관의 보험 자격·보장 음성 문의 응대|없음|
|4|AXV24_df5d48fedff4 — RV 고객 문의의 상시 응대 및 상담원 인계|없음|

**AXV2P2_0060_01를 참고하는 이유:** 문의 응대 지연과 대기가 질문에 명시돼 있어 응대 용량·공백 대응 사례를 살펴봅니다. 이 사례에서 실제 확인된 업무: 항공 고객서비스 질문 응답.

**차이·확인할 조건:**

- 이 요약만으로 야간·모든 채널·예약변경 실행을 보장하지 않음
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV2H_0001_01를 참고하는 이유:** 문의 응대 지연과 대기가 질문에 명시돼 있어 응대 용량·공백 대응 사례를 살펴봅니다. 이 사례에서 실제 확인된 업무: 서면 고객 문의 응답.

**차이·확인할 조건:**

- 음성이나 CRM변경 기능으로 확대하지 않음
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV24_71def85d86bd를 참고하는 이유:** 문의 응대 지연과 대기가 질문에 명시돼 있어 응대 용량·공백 대응 사례를 살펴봅니다. 이 사례에서 실제 확인된 업무: 보험 자격·보장 음성 문의 응대.

**차이·확인할 조건:**

- 청구 승인·보험금 지급·24시간 지원은 이 요약에서 확정하지 않음
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV24_df5d48fedff4를 참고하는 이유:** 문의 응대 지연과 대기가 질문에 명시돼 있어 응대 용량·공백 대응 사례를 살펴봅니다. 이 사례에서 실제 확인된 업무: 상시 문의 응대·상담원 인계.

**차이·확인할 조건:**

- 인계 자체는 명시됐지만 인계 시 맥락 손실 해결 효과까지 증명하지 않음
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

### 중복을 합친 사례 상세 근거

**AXALL_US_OMB_2025_02663**

> 실제 수행 업무: Document retrieval and cross-reference support

- P01 연결 근거: 긴 문서·정책의 탐색 병목과 검색·교차참조 작업이 함께 명시됨.
  - problem: “Staff must search and cross-reference lengthy documents and policies, creating a time-consuming information bottleneck.”
  - task: “Document retrieval and cross-reference support”
  - context: “Nuclear Regulatory Commission staff supporting licensing and oversight work.”

**AXV2N_0110**

> 실제 수행 업무: Retrieve internal knowledge for financial advisors

- P01 연결 근거: 금융자문 직원의 내부문서 탐색 시간이 문제이고 지식 검색을 수행함.
  - problem: “Advisors spend hours searching a large internal document corpus.”
  - task: “Retrieve internal knowledge for financial advisors”
  - context: “Wealth management advisor teams using AI at Morgan Stanley Assistant.”

**AXV2P2_0010_01**

> 실제 수행 업무: Retrieve CAD/CAM product support knowledge

- P01 연결 근거: 접근하기 어려운 제품 전문지식을 검색하는 작업이 명시됨.
  - problem: “Complex manufacturing product knowledge is difficult to access as expertise and skills become scarce.”
  - task: “Retrieve CAD/CAM product support knowledge”
  - context: “Sandvik manufacturing software support teams and customers”

**AXV2P2_0060_01**

> 실제 수행 업무: Answer airline customer service questions

- P04 연결 근거: 대량 고객 문의가 지원조직을 압도하고 지연을 만들며 고객응대를 수행함.
  - problem: “Millions of customer questions overwhelmed airline support, increasing costs and response delays.”
  - task: “Answer airline customer service questions”
  - context: “Air India AI.g customer support”

**AXV2H_0001_01**

> 실제 수행 업무: 고객 문의 자율응답

- P04 연결 근거: 대량 문의로 정시/영업외 대응 유지가 어려우며 문의 자율응답을 수행함.
  - problem: “하루 최대 600건의 문의로 소규모 지원팀이 정시와 영업시간 외 고객대응을 유지하기 어려움”
  - task: “고객 문의 자율응답”
  - context: “전자청구 SaaS 서비스의 대량 서면 문의와 야간 문의”

**AXV24_71def85d86bd**

> 실제 수행 업무: 의료기관의 보험 자격·보장 음성 문의 응대

- P04 연결 근거: 정형 자격·보장 문의의 상담원 쏠림으로 대기 부담이 있고 음성 문의에 응대함.
  - problem: “기존 IVR에서 다수의 정형적 자격·보장 문의가 상담원에게 넘어가 비용과 대기 부담이 커졌다.”
  - task: “의료기관의 보험 자격·보장 음성 문의 응대”
  - context: “의료기관 행정직원이 가입자의 보험 정보를 확인하는 보험사 서비스 운영.”

**AXV24_df5d48fedff4**

> 실제 수행 업무: RV 고객 문의의 상시 응대 및 상담원 인계

- P04 연결 근거: 계절성 문의와 야간 공백으로 대기·누락이 생기며 상시 응대 및 인계 Task가 명시됨.
  - problem: “계절성 문의 증가와 야간 상담 공백으로 고객 대기가 길어지고 일부 문의가 누락됐다.”
  - task: “RV 고객 문의의 상시 응대 및 상담원 인계”
  - context: “여러 사업 부문의 웹·문자 채널에서 들어오는 고객지원 문의.”

## manual_shared_case_two_views

> 의뢰 자료의 자유서술 항목을 구조화하고 필수 항목의 누락을 확인해주세요.

**출처:** 수동으로 구성한 동작 예시

**표시:** 관점 2개 / 관점별 표시 합계 10개 / 중복 제외 사례 9개

### P02 비정형 자료를 수기로 옮기고 업무 정보로 정리하는 부담

**연결 유형:** 질문에 명시된 문제·업무

**질문 근거:** “의뢰 자료의 자유서술 항목을 구조화”

자유서술 자료를 업무 항목으로 구조화하는 방법을 참고합니다.

|순위|참고 사례|다른 연결 관점|
|---|---|---|
|1|AXALL_US_OMB_2025_01754 — Referral data structuring and completeness checks|P03|
|2|AXALL_US_OMB_2025_01589 — Loan document data extraction for examination analytics|없음|
|3|AXV24_bc6444cc1b61 — 단체 의료보험 견적용 청구서 정보 추출|없음|
|4|AXV24_28baf265c6cf — 보험 인수심사용 신청 서류 추출·분류|없음|
|5|AXV24_98092b8ca357 — 상품 카탈로그 속성 추출·분류|없음|

**AXALL_US_OMB_2025_01754를 참고하는 이유:** 자유서술 자료를 업무 항목으로 구조화하는 방법을 참고합니다. 이 사례에서 실제 확인된 업무: 의뢰 자료 데이터 구조화.

**차이·확인할 조건:**

- 필수항목 확인도 별도 명시되어 P03과 중복 연결하되 역할을 구분
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXALL_US_OMB_2025_01589를 참고하는 이유:** 자유서술 자료를 업무 항목으로 구조화하는 방법을 참고합니다. 이 사례에서 실제 확인된 업무: 대출 문서 데이터 추출.

**차이·확인할 조건:**

- 대출 승인·사실 확인까지 수행한다고 해석하지 않음
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV24_bc6444cc1b61를 참고하는 이유:** 자유서술 자료를 업무 항목으로 구조화하는 방법을 참고합니다. 이 사례에서 실제 확인된 업무: 견적용 청구서 정보 추출.

**차이·확인할 조건:**

- 보험 견적 산정이나 심사 판단 자체는 미확인
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV24_28baf265c6cf를 참고하는 이유:** 자유서술 자료를 업무 항목으로 구조화하는 방법을 참고합니다. 이 사례에서 실제 확인된 업무: 보험 신청 서류 추출·분류.

**차이·확인할 조건:**

- 최종 보험 인수 결정은 미확인
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV24_98092b8ca357를 참고하는 이유:** 자유서술 자료를 업무 항목으로 구조화하는 방법을 참고합니다. 이 사례에서 실제 확인된 업무: 상품 속성 추출·분류.

**차이·확인할 조건:**

- 상품 검색·추천 기능 자체의 증거는 아님
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

### P03 업무 자료를 기준·다른 자료와 대조하는 검증 부담

**연결 유형:** 질문에 명시된 문제·업무

**질문 근거:** “필수 항목의 누락을 확인”

필수 항목과 자료를 대조해 누락을 확인하는 방법을 참고합니다.

|순위|참고 사례|다른 연결 관점|
|---|---|---|
|1|AXV24_36c7ef329920 — 채용 지원서·증빙 자료 대조 검토|없음|
|2|AXALL_US_OMB_2025_01754 — Referral data structuring and completeness checks|P02|
|3|AXV2H_0003_01 — 직원 신원조회 보고서 검증|없음|
|4|AXV2P2_0011_01 — Audit freight invoices for overcharges|없음|
|5|AXV2C_0006_02 — Validate customer order prices before invoicing|없음|

**AXV24_36c7ef329920를 참고하는 이유:** 필수 항목과 자료를 대조해 누락을 확인하는 방법을 참고합니다. 이 사례에서 실제 확인된 업무: 지원서·증빙 자료 대조.

**차이·확인할 조건:**

- 지원자의 최종 합격판정과 별개
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXALL_US_OMB_2025_01754를 참고하는 이유:** 필수 항목과 자료를 대조해 누락을 확인하는 방법을 참고합니다. 이 사례에서 실제 확인된 업무: 필수항목 완전성 점검.

**차이·확인할 조건:**

- 구조화 자체는 P02, 내용 누락 확인은 P03의 별도 근거
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV2H_0003_01를 참고하는 이유:** 필수 항목과 자료를 대조해 누락을 확인하는 방법을 참고합니다. 이 사례에서 실제 확인된 업무: 신원조회 보고서의 기준 대조 검증.

**차이·확인할 조건:**

- 채용 의사결정·신원 사실의 절대 보장으로 해석하지 않음
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV2P2_0011_01를 참고하는 이유:** 필수 항목과 자료를 대조해 누락을 확인하는 방법을 참고합니다. 이 사례에서 실제 확인된 업무: 청구서 과다청구 감사.

**차이·확인할 조건:**

- 환급·대금차감 자동 실행은 미확인
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV2C_0006_02를 참고하는 이유:** 필수 항목과 자료를 대조해 누락을 확인하는 방법을 참고합니다. 이 사례에서 실제 확인된 업무: 고객 주문가격 검증.

**차이·확인할 조건:**

- 가격 자동변경·대금 지급 실행은 미확인
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

### 중복을 합친 사례 상세 근거

**AXALL_US_OMB_2025_01754**

> 실제 수행 업무: Referral data structuring and completeness checks

- P02 연결 근거: 자유서술 자료의 수동·불일치 추적에 대해 데이터 구조화를 수행함.
  - problem: “Required referral information arrives as free text and is tracked manually and inconsistently, leaving missing fields to be checked.”
  - task: “Referral data structuring and completeness checks”
  - context: “HHS Office of Refugee Resettlement intake staff reviewing referral records from CBP.”
- P03 연결 근거: 필수 의뢰항목 누락이 문제이고 Task에 완전성 점검이 명시됨.
  - problem: “Required referral information arrives as free text and is tracked manually and inconsistently, leaving missing fields to be checked.”
  - task: “Referral data structuring and completeness checks”
  - context: “HHS Office of Refugee Resettlement intake staff reviewing referral records from CBP.”

**AXALL_US_OMB_2025_01589**

> 실제 수행 업무: Loan document data extraction for examination analytics

- P02 연결 근거: 신청 PDF의 수기 전사로 지연·오류가 생기며 문서 데이터 추출을 수행함.
  - problem: “Manual transcription from loan application PDFs causes delays, errors and staff costs in examination data collection.”
  - task: “Loan document data extraction for examination analytics”
  - context: “FDIC consumer protection personnel preparing loan data for compliance and fair lending reviews.”

**AXV24_bc6444cc1b61**

> 실제 수행 업무: 단체 의료보험 견적용 청구서 정보 추출

- P02 연결 근거: 다양한 청구서 PDF에서 가입자 정보를 수동 복사하는 부담과 추출 Task가 일치함.
  - problem: “보험 견적을 위해 다양한 청구서 PDF에서 가입자 정보를 수동 복사했으며, 인력 증가 없이 견적 물량이 늘었다.”
  - task: “단체 의료보험 견적용 청구서 정보 추출”
  - context: “18명의 보험심사자가 다양한 보험사 청구서를 처리하는 단체보험 견적 업무.”

**AXV24_28baf265c6cf**

> 실제 수행 업무: 보험 인수심사용 신청 서류 추출·분류

- P02 연결 근거: 형식이 다른 보험 자료를 수작업으로 추출하는 부담과 추출·분류 Task가 명시됨.
  - problem: “형식과 주기가 다른 보험 신청 자료에서 담당자가 직접 정보를 추출했으며, 증가하는 접수량을 수작업으로 처리하기 어려웠다.”
  - task: “보험 인수심사용 신청 서류 추출·분류”
  - context: “시니어 리빙 시설의 배상책임보험을 인수하는 심사팀.”

**AXV24_98092b8ca357**

> 실제 수행 업무: 상품 카탈로그 속성 추출·분류

- P02 연결 근거: 카탈로그 세부정보의 수동 추출·정리 부담과 속성 추출·분류가 명시됨.
  - problem: “상품 등록 담당자가 카탈로그의 세부 정보를 수동으로 추출·정리하는 데 많은 시간을 사용했다.”
  - task: “상품 카탈로그 속성 추출·분류”
  - context: “가격 비교 서비스 다나와의 상품 메타데이터 운영.”

**AXV24_36c7ef329920**

> 실제 수행 업무: 채용 지원서·증빙 자료 대조 검토

- P03 연결 근거: 대량 지원서·증빙 검토의 인력 부담과 대조 검토 Task가 명시됨.
  - problem: “3주 안에 150만 건의 채용 지원서와 증빙을 검토해야 했으며 수작업 방식으로는 대규모 인력이 필요했다.”
  - task: “채용 지원서·증빙 자료 대조 검토”
  - context: “고객사의 대량 채용 서류 검토를 수행하는 BPO 기업의 운영 업무.”

**AXV2H_0003_01**

> 실제 수행 업무: 직원 신원조회 보고서 검증

- P03 연결 근거: 다수 파일과 검증기준을 수작업 대조하는 부담이 있고 보고서 검증을 수행함.
  - problem: “다수 파일과 검증 기준을 수작업 대조하면서 검증 지연과 준수 부담이 발생함”
  - task: “직원 신원조회 보고서 검증”
  - context: “업무별 검증 조건과 컴플라이언스 준수가 필수인 전문서비스”

**AXV2P2_0011_01**

> 실제 수행 업무: Audit freight invoices for overcharges

- P03 연결 근거: 운송 청구서와 약정요율 불일치를 확인하는 수기 부담과 감사 Task가 명시됨.
  - problem: “Freight invoices may not match negotiated rates and manual checking burdens logistics staff.”
  - task: “Audit freight invoices for overcharges”
  - context: “Dow logistics spending and emailed PDF invoices”

**AXV2C_0006_02**

> 실제 수행 업무: Validate customer order prices before invoicing

- P03 연결 근거: 주문가격 불일치·입력 오류 문제에 대해 청구 전 가격 검증을 수행함.
  - problem: “Orders in varied formats produced pricing inconsistencies and entry errors, followed by disputes and delayed payments.”
  - task: “Validate customer order prices before invoicing”
  - context: “Danone receives thousands of orders daily through email, PDF and EDI.”

## manual_separate_pdf_and_night

> 보험 청구서 PDF에서 정보를 추출해주세요. 별도로 야간 고객 문의가 누락돼 문의에 응대하고 싶습니다.

**출처:** 수동으로 구성한 동작 예시

**표시:** 관점 2개 / 관점별 표시 합계 9개 / 중복 제외 사례 9개

### P02 비정형 자료를 수기로 옮기고 업무 정보로 정리하는 부담

**연결 유형:** 질문에 명시된 문제·업무

**질문 근거:** “보험 청구서 PDF에서 정보를 추출”

원문 자료에서 항목을 꺼내 정리한 사례를 참고합니다.

|순위|참고 사례|다른 연결 관점|
|---|---|---|
|1|AXV24_bc6444cc1b61 — 단체 의료보험 견적용 청구서 정보 추출|없음|
|2|AXALL_US_OMB_2025_01589 — Loan document data extraction for examination analytics|없음|
|3|AXV24_28baf265c6cf — 보험 인수심사용 신청 서류 추출·분류|없음|
|4|AXV2C_0080_01 — Extract fields from trade finance documents|없음|
|5|AXALL_US_OMB_2025_01754 — Referral data structuring and completeness checks|없음|

**AXV24_bc6444cc1b61를 참고하는 이유:** 원문 자료에서 항목을 꺼내 정리한 사례를 참고합니다. 이 사례에서 실제 확인된 업무: 견적용 청구서 정보 추출.

**차이·확인할 조건:**

- 보험 견적 산정이나 심사 판단 자체는 미확인
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 질문 조건의 지원 여부는 별도 확인: 보험 청구서 PDF
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXALL_US_OMB_2025_01589를 참고하는 이유:** 원문 자료에서 항목을 꺼내 정리한 사례를 참고합니다. 이 사례에서 실제 확인된 업무: 대출 문서 데이터 추출.

**차이·확인할 조건:**

- 대출 승인·사실 확인까지 수행한다고 해석하지 않음
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 질문 조건의 지원 여부는 별도 확인: 보험 청구서 PDF
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV24_28baf265c6cf를 참고하는 이유:** 원문 자료에서 항목을 꺼내 정리한 사례를 참고합니다. 이 사례에서 실제 확인된 업무: 보험 신청 서류 추출·분류.

**차이·확인할 조건:**

- 최종 보험 인수 결정은 미확인
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 질문 조건의 지원 여부는 별도 확인: 보험 청구서 PDF
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV2C_0080_01를 참고하는 이유:** 원문 자료에서 항목을 꺼내 정리한 사례를 참고합니다. 이 사례에서 실제 확인된 업무: 무역금융 문서 필드 추출.

**차이·확인할 조건:**

- 규제위험 판단·제재 심사로 확대하지 않음
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 질문 조건의 지원 여부는 별도 확인: 보험 청구서 PDF
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXALL_US_OMB_2025_01754를 참고하는 이유:** 원문 자료에서 항목을 꺼내 정리한 사례를 참고합니다. 이 사례에서 실제 확인된 업무: 의뢰 자료 데이터 구조화.

**차이·확인할 조건:**

- 필수항목 확인도 별도 명시되어 P03과 중복 연결하되 역할을 구분
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 질문 조건의 지원 여부는 별도 확인: 보험 청구서 PDF
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

### P04 문의량·접수 시간대가 응대 가능 용량을 넘어 대기·누락이 생김

**연결 유형:** 질문에 명시된 문제·업무

**질문 근거:** “야간 고객 문의가 누락돼 문의에 응대”

응대 시간대 공백과 누락을 줄인 사례를 참고합니다.

|순위|참고 사례|다른 연결 관점|
|---|---|---|
|1|AXV24_71def85d86bd — 의료기관의 보험 자격·보장 음성 문의 응대|없음|
|2|AXV2H_0001_01 — 고객 문의 자율응답|없음|
|3|AXV2P2_0060_01 — Answer airline customer service questions|없음|
|4|AXV24_df5d48fedff4 — RV 고객 문의의 상시 응대 및 상담원 인계|없음|

**AXV24_71def85d86bd를 참고하는 이유:** 응대 시간대 공백과 누락을 줄인 사례를 참고합니다. 이 사례에서 실제 확인된 업무: 보험 자격·보장 음성 문의 응대.

**차이·확인할 조건:**

- 청구 승인·보험금 지급·24시간 지원은 이 요약에서 확정하지 않음
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 질문 조건의 지원 여부는 별도 확인: 야간 고객 문의
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV2H_0001_01를 참고하는 이유:** 응대 시간대 공백과 누락을 줄인 사례를 참고합니다. 이 사례에서 실제 확인된 업무: 서면 고객 문의 응답.

**차이·확인할 조건:**

- 음성이나 CRM변경 기능으로 확대하지 않음
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 질문 조건의 지원 여부는 별도 확인: 야간 고객 문의
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV2P2_0060_01를 참고하는 이유:** 응대 시간대 공백과 누락을 줄인 사례를 참고합니다. 이 사례에서 실제 확인된 업무: 항공 고객서비스 질문 응답.

**차이·확인할 조건:**

- 이 요약만으로 야간·모든 채널·예약변경 실행을 보장하지 않음
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 질문 조건의 지원 여부는 별도 확인: 야간 고객 문의
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV24_df5d48fedff4를 참고하는 이유:** 응대 시간대 공백과 누락을 줄인 사례를 참고합니다. 이 사례에서 실제 확인된 업무: 상시 문의 응대·상담원 인계.

**차이·확인할 조건:**

- 인계 자체는 명시됐지만 인계 시 맥락 손실 해결 효과까지 증명하지 않음
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 질문 조건의 지원 여부는 별도 확인: 야간 고객 문의
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

### 중복을 합친 사례 상세 근거

**AXV24_bc6444cc1b61**

> 실제 수행 업무: 단체 의료보험 견적용 청구서 정보 추출

- P02 연결 근거: 다양한 청구서 PDF에서 가입자 정보를 수동 복사하는 부담과 추출 Task가 일치함.
  - problem: “보험 견적을 위해 다양한 청구서 PDF에서 가입자 정보를 수동 복사했으며, 인력 증가 없이 견적 물량이 늘었다.”
  - task: “단체 의료보험 견적용 청구서 정보 추출”
  - context: “18명의 보험심사자가 다양한 보험사 청구서를 처리하는 단체보험 견적 업무.”

**AXALL_US_OMB_2025_01589**

> 실제 수행 업무: Loan document data extraction for examination analytics

- P02 연결 근거: 신청 PDF의 수기 전사로 지연·오류가 생기며 문서 데이터 추출을 수행함.
  - problem: “Manual transcription from loan application PDFs causes delays, errors and staff costs in examination data collection.”
  - task: “Loan document data extraction for examination analytics”
  - context: “FDIC consumer protection personnel preparing loan data for compliance and fair lending reviews.”

**AXV24_28baf265c6cf**

> 실제 수행 업무: 보험 인수심사용 신청 서류 추출·분류

- P02 연결 근거: 형식이 다른 보험 자료를 수작업으로 추출하는 부담과 추출·분류 Task가 명시됨.
  - problem: “형식과 주기가 다른 보험 신청 자료에서 담당자가 직접 정보를 추출했으며, 증가하는 접수량을 수작업으로 처리하기 어려웠다.”
  - task: “보험 인수심사용 신청 서류 추출·분류”
  - context: “시니어 리빙 시설의 배상책임보험을 인수하는 심사팀.”

**AXV2C_0080_01**

> 실제 수행 업무: Extract fields from trade finance documents

- P02 연결 근거: 대량 무역문서의 수기 입력 부담에 대해 필드 추출을 수행함.
  - problem: “High-volume invoices and shipping forms require slow manual entry and are vulnerable to human errors.”
  - task: “Extract fields from trade finance documents”
  - context: “Hong Leong Bank trade operations, multilingual financial documents.”

**AXALL_US_OMB_2025_01754**

> 실제 수행 업무: Referral data structuring and completeness checks

- P02 연결 근거: 자유서술 자료의 수동·불일치 추적에 대해 데이터 구조화를 수행함.
  - problem: “Required referral information arrives as free text and is tracked manually and inconsistently, leaving missing fields to be checked.”
  - task: “Referral data structuring and completeness checks”
  - context: “HHS Office of Refugee Resettlement intake staff reviewing referral records from CBP.”

**AXV24_71def85d86bd**

> 실제 수행 업무: 의료기관의 보험 자격·보장 음성 문의 응대

- P04 연결 근거: 정형 자격·보장 문의의 상담원 쏠림으로 대기 부담이 있고 음성 문의에 응대함.
  - problem: “기존 IVR에서 다수의 정형적 자격·보장 문의가 상담원에게 넘어가 비용과 대기 부담이 커졌다.”
  - task: “의료기관의 보험 자격·보장 음성 문의 응대”
  - context: “의료기관 행정직원이 가입자의 보험 정보를 확인하는 보험사 서비스 운영.”

**AXV2H_0001_01**

> 실제 수행 업무: 고객 문의 자율응답

- P04 연결 근거: 대량 문의로 정시/영업외 대응 유지가 어려우며 문의 자율응답을 수행함.
  - problem: “하루 최대 600건의 문의로 소규모 지원팀이 정시와 영업시간 외 고객대응을 유지하기 어려움”
  - task: “고객 문의 자율응답”
  - context: “전자청구 SaaS 서비스의 대량 서면 문의와 야간 문의”

**AXV2P2_0060_01**

> 실제 수행 업무: Answer airline customer service questions

- P04 연결 근거: 대량 고객 문의가 지원조직을 압도하고 지연을 만들며 고객응대를 수행함.
  - problem: “Millions of customer questions overwhelmed airline support, increasing costs and response delays.”
  - task: “Answer airline customer service questions”
  - context: “Air India AI.g customer support”

**AXV24_df5d48fedff4**

> 실제 수행 업무: RV 고객 문의의 상시 응대 및 상담원 인계

- P04 연결 근거: 계절성 문의와 야간 공백으로 대기·누락이 생기며 상시 응대 및 인계 Task가 명시됨.
  - problem: “계절성 문의 증가와 야간 상담 공백으로 고객 대기가 길어지고 일부 문의가 누락됐다.”
  - task: “RV 고객 문의의 상시 응대 및 상담원 인계”
  - context: “여러 사업 부문의 웹·문자 채널에서 들어오는 고객지원 문의.”

## manual_four_views_no_global_five

> 사내 규정을 검색하고 청구서 금액을 추출한 뒤 계약 기준과 대조해주세요. 야간 문의도 누락돼 고객 문의에 응답하고 싶습니다.

**출처:** 수동으로 구성한 동작 예시

**표시:** 관점 4개 / 관점별 표시 합계 17개 / 중복 제외 사례 16개

### P01 업무 지식이 길고 분산돼 필요한 근거를 찾는 데 시간이 걸림

**연결 유형:** 질문에 명시된 문제·업무

**질문 근거:** “사내 규정을 검색”

기존 지침에서 필요한 근거를 찾는 방법을 참고합니다.

|순위|참고 사례|다른 연결 관점|
|---|---|---|
|1|AXV2N_0110 — Retrieve internal knowledge for financial advisors|없음|
|2|AXALL_US_OMB_2025_02663 — Document retrieval and cross-reference support|없음|
|3|AXV2P2_0010_01 — Retrieve CAD/CAM product support knowledge|없음|

**AXV2N_0110를 참고하는 이유:** 기존 지침에서 필요한 근거를 찾는 방법을 참고합니다. 이 사례에서 실제 확인된 업무: 내부 지식 검색.

**차이·확인할 조건:**

- 외부 고객의 금융판단 대행으로 확대하지 않음
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXALL_US_OMB_2025_02663를 참고하는 이유:** 기존 지침에서 필요한 근거를 찾는 방법을 참고합니다. 이 사례에서 실제 확인된 업무: 문서 검색 및 교차참조 지원.

**차이·확인할 조건:**

- 정책 승인이나 규제 적합성 확정 기능까지 뜻하지 않음
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV2P2_0010_01를 참고하는 이유:** 기존 지침에서 필요한 근거를 찾는 방법을 참고합니다. 이 사례에서 실제 확인된 업무: CAD/CAM 지원지식 검색.

**차이·확인할 조건:**

- 제품 조작·설계 변경의 자동 실행은 미확인
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

### P02 비정형 자료를 수기로 옮기고 업무 정보로 정리하는 부담

**연결 유형:** 질문에 명시된 문제·업무

**질문 근거:** “청구서 금액을 추출”

원자료의 금액을 항목화한 방법을 참고합니다.

|순위|참고 사례|다른 연결 관점|
|---|---|---|
|1|AXV24_bc6444cc1b61 — 단체 의료보험 견적용 청구서 정보 추출|없음|
|2|AXALL_US_OMB_2025_01589 — Loan document data extraction for examination analytics|없음|
|3|AXV24_28baf265c6cf — 보험 인수심사용 신청 서류 추출·분류|없음|
|4|AXALL_US_OMB_2025_01754 — Referral data structuring and completeness checks|P03|
|5|AXV2C_0080_01 — Extract fields from trade finance documents|없음|

**AXV24_bc6444cc1b61를 참고하는 이유:** 원자료의 금액을 항목화한 방법을 참고합니다. 이 사례에서 실제 확인된 업무: 견적용 청구서 정보 추출.

**차이·확인할 조건:**

- 보험 견적 산정이나 심사 판단 자체는 미확인
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXALL_US_OMB_2025_01589를 참고하는 이유:** 원자료의 금액을 항목화한 방법을 참고합니다. 이 사례에서 실제 확인된 업무: 대출 문서 데이터 추출.

**차이·확인할 조건:**

- 대출 승인·사실 확인까지 수행한다고 해석하지 않음
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV24_28baf265c6cf를 참고하는 이유:** 원자료의 금액을 항목화한 방법을 참고합니다. 이 사례에서 실제 확인된 업무: 보험 신청 서류 추출·분류.

**차이·확인할 조건:**

- 최종 보험 인수 결정은 미확인
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXALL_US_OMB_2025_01754를 참고하는 이유:** 원자료의 금액을 항목화한 방법을 참고합니다. 이 사례에서 실제 확인된 업무: 의뢰 자료 데이터 구조화.

**차이·확인할 조건:**

- 필수항목 확인도 별도 명시되어 P03과 중복 연결하되 역할을 구분
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV2C_0080_01를 참고하는 이유:** 원자료의 금액을 항목화한 방법을 참고합니다. 이 사례에서 실제 확인된 업무: 무역금융 문서 필드 추출.

**차이·확인할 조건:**

- 규제위험 판단·제재 심사로 확대하지 않음
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

### P03 업무 자료를 기준·다른 자료와 대조하는 검증 부담

**연결 유형:** 질문에 명시된 문제·업무

**질문 근거:** “계약 기준과 대조”

자료를 기준과 대조하는 방법을 참고합니다.

|순위|참고 사례|다른 연결 관점|
|---|---|---|
|1|AXV24_36c7ef329920 — 채용 지원서·증빙 자료 대조 검토|없음|
|2|AXV2H_0003_01 — 직원 신원조회 보고서 검증|없음|
|3|AXV2C_0006_02 — Validate customer order prices before invoicing|없음|
|4|AXV2P2_0011_01 — Audit freight invoices for overcharges|없음|
|5|AXALL_US_OMB_2025_01754 — Referral data structuring and completeness checks|P02|

**AXV24_36c7ef329920를 참고하는 이유:** 자료를 기준과 대조하는 방법을 참고합니다. 이 사례에서 실제 확인된 업무: 지원서·증빙 자료 대조.

**차이·확인할 조건:**

- 지원자의 최종 합격판정과 별개
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV2H_0003_01를 참고하는 이유:** 자료를 기준과 대조하는 방법을 참고합니다. 이 사례에서 실제 확인된 업무: 신원조회 보고서의 기준 대조 검증.

**차이·확인할 조건:**

- 채용 의사결정·신원 사실의 절대 보장으로 해석하지 않음
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV2C_0006_02를 참고하는 이유:** 자료를 기준과 대조하는 방법을 참고합니다. 이 사례에서 실제 확인된 업무: 고객 주문가격 검증.

**차이·확인할 조건:**

- 가격 자동변경·대금 지급 실행은 미확인
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV2P2_0011_01를 참고하는 이유:** 자료를 기준과 대조하는 방법을 참고합니다. 이 사례에서 실제 확인된 업무: 청구서 과다청구 감사.

**차이·확인할 조건:**

- 환급·대금차감 자동 실행은 미확인
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXALL_US_OMB_2025_01754를 참고하는 이유:** 자료를 기준과 대조하는 방법을 참고합니다. 이 사례에서 실제 확인된 업무: 필수항목 완전성 점검.

**차이·확인할 조건:**

- 구조화 자체는 P02, 내용 누락 확인은 P03의 별도 근거
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

### P04 문의량·접수 시간대가 응대 가능 용량을 넘어 대기·누락이 생김

**연결 유형:** 질문에 명시된 문제·업무

**질문 근거:** “야간 문의도 누락돼 고객 문의에 응답”

야간 응대 공백에 대응한 방법을 참고합니다.

|순위|참고 사례|다른 연결 관점|
|---|---|---|
|1|AXV2P2_0060_01 — Answer airline customer service questions|없음|
|2|AXV2H_0001_01 — 고객 문의 자율응답|없음|
|3|AXV24_71def85d86bd — 의료기관의 보험 자격·보장 음성 문의 응대|없음|
|4|AXV24_df5d48fedff4 — RV 고객 문의의 상시 응대 및 상담원 인계|없음|

**AXV2P2_0060_01를 참고하는 이유:** 야간 응대 공백에 대응한 방법을 참고합니다. 이 사례에서 실제 확인된 업무: 항공 고객서비스 질문 응답.

**차이·확인할 조건:**

- 이 요약만으로 야간·모든 채널·예약변경 실행을 보장하지 않음
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV2H_0001_01를 참고하는 이유:** 야간 응대 공백에 대응한 방법을 참고합니다. 이 사례에서 실제 확인된 업무: 서면 고객 문의 응답.

**차이·확인할 조건:**

- 음성이나 CRM변경 기능으로 확대하지 않음
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV24_71def85d86bd를 참고하는 이유:** 야간 응대 공백에 대응한 방법을 참고합니다. 이 사례에서 실제 확인된 업무: 보험 자격·보장 음성 문의 응대.

**차이·확인할 조건:**

- 청구 승인·보험금 지급·24시간 지원은 이 요약에서 확정하지 않음
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV24_df5d48fedff4를 참고하는 이유:** 야간 응대 공백에 대응한 방법을 참고합니다. 이 사례에서 실제 확인된 업무: 상시 문의 응대·상담원 인계.

**차이·확인할 조건:**

- 인계 자체는 명시됐지만 인계 시 맥락 손실 해결 효과까지 증명하지 않음
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

### 중복을 합친 사례 상세 근거

**AXV2N_0110**

> 실제 수행 업무: Retrieve internal knowledge for financial advisors

- P01 연결 근거: 금융자문 직원의 내부문서 탐색 시간이 문제이고 지식 검색을 수행함.
  - problem: “Advisors spend hours searching a large internal document corpus.”
  - task: “Retrieve internal knowledge for financial advisors”
  - context: “Wealth management advisor teams using AI at Morgan Stanley Assistant.”

**AXALL_US_OMB_2025_02663**

> 실제 수행 업무: Document retrieval and cross-reference support

- P01 연결 근거: 긴 문서·정책의 탐색 병목과 검색·교차참조 작업이 함께 명시됨.
  - problem: “Staff must search and cross-reference lengthy documents and policies, creating a time-consuming information bottleneck.”
  - task: “Document retrieval and cross-reference support”
  - context: “Nuclear Regulatory Commission staff supporting licensing and oversight work.”

**AXV2P2_0010_01**

> 실제 수행 업무: Retrieve CAD/CAM product support knowledge

- P01 연결 근거: 접근하기 어려운 제품 전문지식을 검색하는 작업이 명시됨.
  - problem: “Complex manufacturing product knowledge is difficult to access as expertise and skills become scarce.”
  - task: “Retrieve CAD/CAM product support knowledge”
  - context: “Sandvik manufacturing software support teams and customers”

**AXV24_bc6444cc1b61**

> 실제 수행 업무: 단체 의료보험 견적용 청구서 정보 추출

- P02 연결 근거: 다양한 청구서 PDF에서 가입자 정보를 수동 복사하는 부담과 추출 Task가 일치함.
  - problem: “보험 견적을 위해 다양한 청구서 PDF에서 가입자 정보를 수동 복사했으며, 인력 증가 없이 견적 물량이 늘었다.”
  - task: “단체 의료보험 견적용 청구서 정보 추출”
  - context: “18명의 보험심사자가 다양한 보험사 청구서를 처리하는 단체보험 견적 업무.”

**AXALL_US_OMB_2025_01589**

> 실제 수행 업무: Loan document data extraction for examination analytics

- P02 연결 근거: 신청 PDF의 수기 전사로 지연·오류가 생기며 문서 데이터 추출을 수행함.
  - problem: “Manual transcription from loan application PDFs causes delays, errors and staff costs in examination data collection.”
  - task: “Loan document data extraction for examination analytics”
  - context: “FDIC consumer protection personnel preparing loan data for compliance and fair lending reviews.”

**AXV24_28baf265c6cf**

> 실제 수행 업무: 보험 인수심사용 신청 서류 추출·분류

- P02 연결 근거: 형식이 다른 보험 자료를 수작업으로 추출하는 부담과 추출·분류 Task가 명시됨.
  - problem: “형식과 주기가 다른 보험 신청 자료에서 담당자가 직접 정보를 추출했으며, 증가하는 접수량을 수작업으로 처리하기 어려웠다.”
  - task: “보험 인수심사용 신청 서류 추출·분류”
  - context: “시니어 리빙 시설의 배상책임보험을 인수하는 심사팀.”

**AXALL_US_OMB_2025_01754**

> 실제 수행 업무: Referral data structuring and completeness checks

- P02 연결 근거: 자유서술 자료의 수동·불일치 추적에 대해 데이터 구조화를 수행함.
  - problem: “Required referral information arrives as free text and is tracked manually and inconsistently, leaving missing fields to be checked.”
  - task: “Referral data structuring and completeness checks”
  - context: “HHS Office of Refugee Resettlement intake staff reviewing referral records from CBP.”
- P03 연결 근거: 필수 의뢰항목 누락이 문제이고 Task에 완전성 점검이 명시됨.
  - problem: “Required referral information arrives as free text and is tracked manually and inconsistently, leaving missing fields to be checked.”
  - task: “Referral data structuring and completeness checks”
  - context: “HHS Office of Refugee Resettlement intake staff reviewing referral records from CBP.”

**AXV2C_0080_01**

> 실제 수행 업무: Extract fields from trade finance documents

- P02 연결 근거: 대량 무역문서의 수기 입력 부담에 대해 필드 추출을 수행함.
  - problem: “High-volume invoices and shipping forms require slow manual entry and are vulnerable to human errors.”
  - task: “Extract fields from trade finance documents”
  - context: “Hong Leong Bank trade operations, multilingual financial documents.”

**AXV24_36c7ef329920**

> 실제 수행 업무: 채용 지원서·증빙 자료 대조 검토

- P03 연결 근거: 대량 지원서·증빙 검토의 인력 부담과 대조 검토 Task가 명시됨.
  - problem: “3주 안에 150만 건의 채용 지원서와 증빙을 검토해야 했으며 수작업 방식으로는 대규모 인력이 필요했다.”
  - task: “채용 지원서·증빙 자료 대조 검토”
  - context: “고객사의 대량 채용 서류 검토를 수행하는 BPO 기업의 운영 업무.”

**AXV2H_0003_01**

> 실제 수행 업무: 직원 신원조회 보고서 검증

- P03 연결 근거: 다수 파일과 검증기준을 수작업 대조하는 부담이 있고 보고서 검증을 수행함.
  - problem: “다수 파일과 검증 기준을 수작업 대조하면서 검증 지연과 준수 부담이 발생함”
  - task: “직원 신원조회 보고서 검증”
  - context: “업무별 검증 조건과 컴플라이언스 준수가 필수인 전문서비스”

**AXV2C_0006_02**

> 실제 수행 업무: Validate customer order prices before invoicing

- P03 연결 근거: 주문가격 불일치·입력 오류 문제에 대해 청구 전 가격 검증을 수행함.
  - problem: “Orders in varied formats produced pricing inconsistencies and entry errors, followed by disputes and delayed payments.”
  - task: “Validate customer order prices before invoicing”
  - context: “Danone receives thousands of orders daily through email, PDF and EDI.”

**AXV2P2_0011_01**

> 실제 수행 업무: Audit freight invoices for overcharges

- P03 연결 근거: 운송 청구서와 약정요율 불일치를 확인하는 수기 부담과 감사 Task가 명시됨.
  - problem: “Freight invoices may not match negotiated rates and manual checking burdens logistics staff.”
  - task: “Audit freight invoices for overcharges”
  - context: “Dow logistics spending and emailed PDF invoices”

**AXV2P2_0060_01**

> 실제 수행 업무: Answer airline customer service questions

- P04 연결 근거: 대량 고객 문의가 지원조직을 압도하고 지연을 만들며 고객응대를 수행함.
  - problem: “Millions of customer questions overwhelmed airline support, increasing costs and response delays.”
  - task: “Answer airline customer service questions”
  - context: “Air India AI.g customer support”

**AXV2H_0001_01**

> 실제 수행 업무: 고객 문의 자율응답

- P04 연결 근거: 대량 문의로 정시/영업외 대응 유지가 어려우며 문의 자율응답을 수행함.
  - problem: “하루 최대 600건의 문의로 소규모 지원팀이 정시와 영업시간 외 고객대응을 유지하기 어려움”
  - task: “고객 문의 자율응답”
  - context: “전자청구 SaaS 서비스의 대량 서면 문의와 야간 문의”

**AXV24_71def85d86bd**

> 실제 수행 업무: 의료기관의 보험 자격·보장 음성 문의 응대

- P04 연결 근거: 정형 자격·보장 문의의 상담원 쏠림으로 대기 부담이 있고 음성 문의에 응대함.
  - problem: “기존 IVR에서 다수의 정형적 자격·보장 문의가 상담원에게 넘어가 비용과 대기 부담이 커졌다.”
  - task: “의료기관의 보험 자격·보장 음성 문의 응대”
  - context: “의료기관 행정직원이 가입자의 보험 정보를 확인하는 보험사 서비스 운영.”

**AXV24_df5d48fedff4**

> 실제 수행 업무: RV 고객 문의의 상시 응대 및 상담원 인계

- P04 연결 근거: 계절성 문의와 야간 공백으로 대기·누락이 생기며 상시 응대 및 인계 Task가 명시됨.
  - problem: “계절성 문의 증가와 야간 상담 공백으로 고객 대기가 길어지고 일부 문의가 누락됐다.”
  - task: “RV 고객 문의의 상시 응대 및 상담원 인계”
  - context: “여러 사업 부문의 웹·문자 채널에서 들어오는 고객지원 문의.”

## manual_excluded_search

> 고객 문의가 몰려 대기가 깁니다. 응대 사례를 보고 싶지만 문서 검색 관점은 제외해주세요.

**출처:** 수동으로 구성한 동작 예시

**표시:** 관점 1개 / 관점별 표시 합계 4개 / 중복 제외 사례 4개

### P04 문의량·접수 시간대가 응대 가능 용량을 넘어 대기·누락이 생김

**연결 유형:** 질문에 명시된 문제·업무

**질문 근거:** “고객 문의가 몰려 대기가 깁니다”

질문에 명시된 응대 용량 문제에 초점을 맞춥니다.

|순위|참고 사례|다른 연결 관점|
|---|---|---|
|1|AXV2P2_0060_01 — Answer airline customer service questions|없음|
|2|AXV2H_0001_01 — 고객 문의 자율응답|없음|
|3|AXV24_71def85d86bd — 의료기관의 보험 자격·보장 음성 문의 응대|없음|
|4|AXV24_df5d48fedff4 — RV 고객 문의의 상시 응대 및 상담원 인계|없음|

**AXV2P2_0060_01를 참고하는 이유:** 질문에 명시된 응대 용량 문제에 초점을 맞춥니다. 이 사례에서 실제 확인된 업무: 항공 고객서비스 질문 응답.

**차이·확인할 조건:**

- 이 요약만으로 야간·모든 채널·예약변경 실행을 보장하지 않음
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV2H_0001_01를 참고하는 이유:** 질문에 명시된 응대 용량 문제에 초점을 맞춥니다. 이 사례에서 실제 확인된 업무: 서면 고객 문의 응답.

**차이·확인할 조건:**

- 음성이나 CRM변경 기능으로 확대하지 않음
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV24_71def85d86bd를 참고하는 이유:** 질문에 명시된 응대 용량 문제에 초점을 맞춥니다. 이 사례에서 실제 확인된 업무: 보험 자격·보장 음성 문의 응대.

**차이·확인할 조건:**

- 청구 승인·보험금 지급·24시간 지원은 이 요약에서 확정하지 않음
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV24_df5d48fedff4를 참고하는 이유:** 질문에 명시된 응대 용량 문제에 초점을 맞춥니다. 이 사례에서 실제 확인된 업무: 상시 문의 응대·상담원 인계.

**차이·확인할 조건:**

- 인계 자체는 명시됐지만 인계 시 맥락 손실 해결 효과까지 증명하지 않음
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

### 중복을 합친 사례 상세 근거

**AXV2P2_0060_01**

> 실제 수행 업무: Answer airline customer service questions

- P04 연결 근거: 대량 고객 문의가 지원조직을 압도하고 지연을 만들며 고객응대를 수행함.
  - problem: “Millions of customer questions overwhelmed airline support, increasing costs and response delays.”
  - task: “Answer airline customer service questions”
  - context: “Air India AI.g customer support”

**AXV2H_0001_01**

> 실제 수행 업무: 고객 문의 자율응답

- P04 연결 근거: 대량 문의로 정시/영업외 대응 유지가 어려우며 문의 자율응답을 수행함.
  - problem: “하루 최대 600건의 문의로 소규모 지원팀이 정시와 영업시간 외 고객대응을 유지하기 어려움”
  - task: “고객 문의 자율응답”
  - context: “전자청구 SaaS 서비스의 대량 서면 문의와 야간 문의”

**AXV24_71def85d86bd**

> 실제 수행 업무: 의료기관의 보험 자격·보장 음성 문의 응대

- P04 연결 근거: 정형 자격·보장 문의의 상담원 쏠림으로 대기 부담이 있고 음성 문의에 응대함.
  - problem: “기존 IVR에서 다수의 정형적 자격·보장 문의가 상담원에게 넘어가 비용과 대기 부담이 커졌다.”
  - task: “의료기관의 보험 자격·보장 음성 문의 응대”
  - context: “의료기관 행정직원이 가입자의 보험 정보를 확인하는 보험사 서비스 운영.”

**AXV24_df5d48fedff4**

> 실제 수행 업무: RV 고객 문의의 상시 응대 및 상담원 인계

- P04 연결 근거: 계절성 문의와 야간 공백으로 대기·누락이 생기며 상시 응대 및 인계 Task가 명시됨.
  - problem: “계절성 문의 증가와 야간 상담 공백으로 고객 대기가 길어지고 일부 문의가 누락됐다.”
  - task: “RV 고객 문의의 상시 응대 및 상담원 인계”
  - context: “여러 사업 부문의 웹·문자 채널에서 들어오는 고객지원 문의.”

## manual_outside_catalog

> 다음 달 상품 수요를 예측해주세요.

**출처:** 수동으로 구성한 동작 예시

**표시:** 관점 0개 / 관점별 표시 합계 0개 / 중복 제외 사례 0개

선택된 관점이 없어 사례를 억지로 채우지 않았다.

**목록 밖 요청:**

- “다음 달 상품 수요를 예측해주세요”: 미래 수요 예측 관점은 이번 상세 검토한 네 관점의 범위 밖입니다.

### 중복을 합친 사례 상세 근거

## legacy_D01

> 사내 규정에서 출장비 지급 기준과 원문 출처를 검색해주세요.

**출처:** 이전 실제 LLM 선택 응답; 예전 업무형 기준

**표시:** 관점 1개 / 관점별 표시 합계 3개 / 중복 제외 사례 3개

### P01 업무 지식이 길고 분산돼 필요한 근거를 찾는 데 시간이 걸림

**연결 유형:** 질문에 명시된 문제·업무

**질문 근거:** “출장비 지급 기준과 원문 출처를 검색해주세요”

사내 규정이라는 기존 문서에서 출장비 지급 기준과 원문 출처를 찾는 요청이므로 문서·지식 검색에 해당한다.

|순위|참고 사례|다른 연결 관점|
|---|---|---|
|1|AXALL_US_OMB_2025_02663 — Document retrieval and cross-reference support|없음|
|2|AXV2N_0110 — Retrieve internal knowledge for financial advisors|없음|
|3|AXV2P2_0010_01 — Retrieve CAD/CAM product support knowledge|없음|

**AXALL_US_OMB_2025_02663를 참고하는 이유:** 사내 규정이라는 기존 문서에서 출장비 지급 기준과 원문 출처를 찾는 요청이므로 문서·지식 검색에 해당한다. 이 사례에서 실제 확인된 업무: 문서 검색 및 교차참조 지원.

**차이·확인할 조건:**

- 정책 승인이나 규제 적합성 확정 기능까지 뜻하지 않음
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV2N_0110를 참고하는 이유:** 사내 규정이라는 기존 문서에서 출장비 지급 기준과 원문 출처를 찾는 요청이므로 문서·지식 검색에 해당한다. 이 사례에서 실제 확인된 업무: 내부 지식 검색.

**차이·확인할 조건:**

- 외부 고객의 금융판단 대행으로 확대하지 않음
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV2P2_0010_01를 참고하는 이유:** 사내 규정이라는 기존 문서에서 출장비 지급 기준과 원문 출처를 찾는 요청이므로 문서·지식 검색에 해당한다. 이 사례에서 실제 확인된 업무: CAD/CAM 지원지식 검색.

**차이·확인할 조건:**

- 제품 조작·설계 변경의 자동 실행은 미확인
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

### 중복을 합친 사례 상세 근거

**AXALL_US_OMB_2025_02663**

> 실제 수행 업무: Document retrieval and cross-reference support

- P01 연결 근거: 긴 문서·정책의 탐색 병목과 검색·교차참조 작업이 함께 명시됨.
  - problem: “Staff must search and cross-reference lengthy documents and policies, creating a time-consuming information bottleneck.”
  - task: “Document retrieval and cross-reference support”
  - context: “Nuclear Regulatory Commission staff supporting licensing and oversight work.”

**AXV2N_0110**

> 실제 수행 업무: Retrieve internal knowledge for financial advisors

- P01 연결 근거: 금융자문 직원의 내부문서 탐색 시간이 문제이고 지식 검색을 수행함.
  - problem: “Advisors spend hours searching a large internal document corpus.”
  - task: “Retrieve internal knowledge for financial advisors”
  - context: “Wealth management advisor teams using AI at Morgan Stanley Assistant.”

**AXV2P2_0010_01**

> 실제 수행 업무: Retrieve CAD/CAM product support knowledge

- P01 연결 근거: 접근하기 어려운 제품 전문지식을 검색하는 작업이 명시됨.
  - problem: “Complex manufacturing product knowledge is difficult to access as expertise and skills become scarce.”
  - task: “Retrieve CAD/CAM product support knowledge”
  - context: “Sandvik manufacturing software support teams and customers”

## legacy_D02

> 우리 회사 업무지침 중 출장 때 얼마까지 쓸 수 있는지 나온 부분과 원문 위치를 알려주세요.

**출처:** 이전 실제 LLM 선택 응답; 예전 업무형 기준

**표시:** 관점 1개 / 관점별 표시 합계 3개 / 중복 제외 사례 3개

### P01 업무 지식이 길고 분산돼 필요한 근거를 찾는 데 시간이 걸림

**연결 유형:** 질문에 명시된 문제·업무

**질문 근거:** “출장 때 얼마까지 쓸 수 있는지 나온 부분과 원문 위치를 알려주세요”

기존 업무지침에서 출장비 한도 내용과 원문 위치를 찾는 요청이므로 문서 검색에 해당한다.

|순위|참고 사례|다른 연결 관점|
|---|---|---|
|1|AXALL_US_OMB_2025_02663 — Document retrieval and cross-reference support|없음|
|2|AXV2N_0110 — Retrieve internal knowledge for financial advisors|없음|
|3|AXV2P2_0010_01 — Retrieve CAD/CAM product support knowledge|없음|

**AXALL_US_OMB_2025_02663를 참고하는 이유:** 기존 업무지침에서 출장비 한도 내용과 원문 위치를 찾는 요청이므로 문서 검색에 해당한다. 이 사례에서 실제 확인된 업무: 문서 검색 및 교차참조 지원.

**차이·확인할 조건:**

- 정책 승인이나 규제 적합성 확정 기능까지 뜻하지 않음
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV2N_0110를 참고하는 이유:** 기존 업무지침에서 출장비 한도 내용과 원문 위치를 찾는 요청이므로 문서 검색에 해당한다. 이 사례에서 실제 확인된 업무: 내부 지식 검색.

**차이·확인할 조건:**

- 외부 고객의 금융판단 대행으로 확대하지 않음
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV2P2_0010_01를 참고하는 이유:** 기존 업무지침에서 출장비 한도 내용과 원문 위치를 찾는 요청이므로 문서 검색에 해당한다. 이 사례에서 실제 확인된 업무: CAD/CAM 지원지식 검색.

**차이·확인할 조건:**

- 제품 조작·설계 변경의 자동 실행은 미확인
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

### 중복을 합친 사례 상세 근거

**AXALL_US_OMB_2025_02663**

> 실제 수행 업무: Document retrieval and cross-reference support

- P01 연결 근거: 긴 문서·정책의 탐색 병목과 검색·교차참조 작업이 함께 명시됨.
  - problem: “Staff must search and cross-reference lengthy documents and policies, creating a time-consuming information bottleneck.”
  - task: “Document retrieval and cross-reference support”
  - context: “Nuclear Regulatory Commission staff supporting licensing and oversight work.”

**AXV2N_0110**

> 실제 수행 업무: Retrieve internal knowledge for financial advisors

- P01 연결 근거: 금융자문 직원의 내부문서 탐색 시간이 문제이고 지식 검색을 수행함.
  - problem: “Advisors spend hours searching a large internal document corpus.”
  - task: “Retrieve internal knowledge for financial advisors”
  - context: “Wealth management advisor teams using AI at Morgan Stanley Assistant.”

**AXV2P2_0010_01**

> 실제 수행 업무: Retrieve CAD/CAM product support knowledge

- P01 연결 근거: 접근하기 어려운 제품 전문지식을 검색하는 작업이 명시됨.
  - problem: “Complex manufacturing product knowledge is difficult to access as expertise and skills become scarce.”
  - task: “Retrieve CAD/CAM product support knowledge”
  - context: “Sandvik manufacturing software support teams and customers”

## legacy_D03

> PDF 청구서에서 고객명과 청구 금액을 추출해주세요.

**출처:** 이전 실제 LLM 선택 응답; 예전 업무형 기준

**표시:** 관점 1개 / 관점별 표시 합계 5개 / 중복 제외 사례 5개

### P02 비정형 자료를 수기로 옮기고 업무 정보로 정리하는 부담

**연결 유형:** 질문에 명시된 문제·업무

**질문 근거:** “고객명과 청구 금액을 추출해주세요”

PDF 청구서 원자료에서 고객명과 청구 금액을 꺼내 달라는 추출 요청입니다.

|순위|참고 사례|다른 연결 관점|
|---|---|---|
|1|AXV24_bc6444cc1b61 — 단체 의료보험 견적용 청구서 정보 추출|없음|
|2|AXALL_US_OMB_2025_01589 — Loan document data extraction for examination analytics|없음|
|3|AXV2C_0080_01 — Extract fields from trade finance documents|없음|
|4|AXV24_28baf265c6cf — 보험 인수심사용 신청 서류 추출·분류|없음|
|5|AXALL_US_OMB_2025_01754 — Referral data structuring and completeness checks|없음|

**AXV24_bc6444cc1b61를 참고하는 이유:** PDF 청구서 원자료에서 고객명과 청구 금액을 꺼내 달라는 추출 요청입니다. 이 사례에서 실제 확인된 업무: 견적용 청구서 정보 추출.

**차이·확인할 조건:**

- 보험 견적 산정이나 심사 판단 자체는 미확인
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXALL_US_OMB_2025_01589를 참고하는 이유:** PDF 청구서 원자료에서 고객명과 청구 금액을 꺼내 달라는 추출 요청입니다. 이 사례에서 실제 확인된 업무: 대출 문서 데이터 추출.

**차이·확인할 조건:**

- 대출 승인·사실 확인까지 수행한다고 해석하지 않음
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV2C_0080_01를 참고하는 이유:** PDF 청구서 원자료에서 고객명과 청구 금액을 꺼내 달라는 추출 요청입니다. 이 사례에서 실제 확인된 업무: 무역금융 문서 필드 추출.

**차이·확인할 조건:**

- 규제위험 판단·제재 심사로 확대하지 않음
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV24_28baf265c6cf를 참고하는 이유:** PDF 청구서 원자료에서 고객명과 청구 금액을 꺼내 달라는 추출 요청입니다. 이 사례에서 실제 확인된 업무: 보험 신청 서류 추출·분류.

**차이·확인할 조건:**

- 최종 보험 인수 결정은 미확인
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXALL_US_OMB_2025_01754를 참고하는 이유:** PDF 청구서 원자료에서 고객명과 청구 금액을 꺼내 달라는 추출 요청입니다. 이 사례에서 실제 확인된 업무: 의뢰 자료 데이터 구조화.

**차이·확인할 조건:**

- 필수항목 확인도 별도 명시되어 P03과 중복 연결하되 역할을 구분
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

### 중복을 합친 사례 상세 근거

**AXV24_bc6444cc1b61**

> 실제 수행 업무: 단체 의료보험 견적용 청구서 정보 추출

- P02 연결 근거: 다양한 청구서 PDF에서 가입자 정보를 수동 복사하는 부담과 추출 Task가 일치함.
  - problem: “보험 견적을 위해 다양한 청구서 PDF에서 가입자 정보를 수동 복사했으며, 인력 증가 없이 견적 물량이 늘었다.”
  - task: “단체 의료보험 견적용 청구서 정보 추출”
  - context: “18명의 보험심사자가 다양한 보험사 청구서를 처리하는 단체보험 견적 업무.”

**AXALL_US_OMB_2025_01589**

> 실제 수행 업무: Loan document data extraction for examination analytics

- P02 연결 근거: 신청 PDF의 수기 전사로 지연·오류가 생기며 문서 데이터 추출을 수행함.
  - problem: “Manual transcription from loan application PDFs causes delays, errors and staff costs in examination data collection.”
  - task: “Loan document data extraction for examination analytics”
  - context: “FDIC consumer protection personnel preparing loan data for compliance and fair lending reviews.”

**AXV2C_0080_01**

> 실제 수행 업무: Extract fields from trade finance documents

- P02 연결 근거: 대량 무역문서의 수기 입력 부담에 대해 필드 추출을 수행함.
  - problem: “High-volume invoices and shipping forms require slow manual entry and are vulnerable to human errors.”
  - task: “Extract fields from trade finance documents”
  - context: “Hong Leong Bank trade operations, multilingual financial documents.”

**AXV24_28baf265c6cf**

> 실제 수행 업무: 보험 인수심사용 신청 서류 추출·분류

- P02 연결 근거: 형식이 다른 보험 자료를 수작업으로 추출하는 부담과 추출·분류 Task가 명시됨.
  - problem: “형식과 주기가 다른 보험 신청 자료에서 담당자가 직접 정보를 추출했으며, 증가하는 접수량을 수작업으로 처리하기 어려웠다.”
  - task: “보험 인수심사용 신청 서류 추출·분류”
  - context: “시니어 리빙 시설의 배상책임보험을 인수하는 심사팀.”

**AXALL_US_OMB_2025_01754**

> 실제 수행 업무: Referral data structuring and completeness checks

- P02 연결 근거: 자유서술 자료의 수동·불일치 추적에 대해 데이터 구조화를 수행함.
  - problem: “Required referral information arrives as free text and is tracked manually and inconsistently, leaving missing fields to be checked.”
  - task: “Referral data structuring and completeness checks”
  - context: “HHS Office of Refugee Resettlement intake staff reviewing referral records from CBP.”

## legacy_D04

> 협력사가 보낸 상품 정보 파일에서 이름과 규격, 가격을 꺼내 항목별 표로 정리해주세요.

**출처:** 이전 실제 LLM 선택 응답; 예전 업무형 기준

**표시:** 관점 1개 / 관점별 표시 합계 5개 / 중복 제외 사례 5개

### P02 비정형 자료를 수기로 옮기고 업무 정보로 정리하는 부담

**연결 유형:** 질문에 명시된 문제·업무

**질문 근거:** “이름과 규격, 가격을 꺼내 항목별 표로 정리해주세요”

협력사 상품 정보 파일에서 이름·규격·가격을 꺼내 항목별 표로 구조화하려는 요청입니다.

|순위|참고 사례|다른 연결 관점|
|---|---|---|
|1|AXV2C_0080_01 — Extract fields from trade finance documents|없음|
|2|AXV24_98092b8ca357 — 상품 카탈로그 속성 추출·분류|없음|
|3|AXV24_bc6444cc1b61 — 단체 의료보험 견적용 청구서 정보 추출|없음|
|4|AXALL_US_OMB_2025_01589 — Loan document data extraction for examination analytics|없음|
|5|AXALL_US_OMB_2025_01754 — Referral data structuring and completeness checks|없음|

**AXV2C_0080_01를 참고하는 이유:** 협력사 상품 정보 파일에서 이름·규격·가격을 꺼내 항목별 표로 구조화하려는 요청입니다. 이 사례에서 실제 확인된 업무: 무역금융 문서 필드 추출.

**차이·확인할 조건:**

- 규제위험 판단·제재 심사로 확대하지 않음
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV24_98092b8ca357를 참고하는 이유:** 협력사 상품 정보 파일에서 이름·규격·가격을 꺼내 항목별 표로 구조화하려는 요청입니다. 이 사례에서 실제 확인된 업무: 상품 속성 추출·분류.

**차이·확인할 조건:**

- 상품 검색·추천 기능 자체의 증거는 아님
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV24_bc6444cc1b61를 참고하는 이유:** 협력사 상품 정보 파일에서 이름·규격·가격을 꺼내 항목별 표로 구조화하려는 요청입니다. 이 사례에서 실제 확인된 업무: 견적용 청구서 정보 추출.

**차이·확인할 조건:**

- 보험 견적 산정이나 심사 판단 자체는 미확인
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXALL_US_OMB_2025_01589를 참고하는 이유:** 협력사 상품 정보 파일에서 이름·규격·가격을 꺼내 항목별 표로 구조화하려는 요청입니다. 이 사례에서 실제 확인된 업무: 대출 문서 데이터 추출.

**차이·확인할 조건:**

- 대출 승인·사실 확인까지 수행한다고 해석하지 않음
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXALL_US_OMB_2025_01754를 참고하는 이유:** 협력사 상품 정보 파일에서 이름·규격·가격을 꺼내 항목별 표로 구조화하려는 요청입니다. 이 사례에서 실제 확인된 업무: 의뢰 자료 데이터 구조화.

**차이·확인할 조건:**

- 필수항목 확인도 별도 명시되어 P03과 중복 연결하되 역할을 구분
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

### 중복을 합친 사례 상세 근거

**AXV2C_0080_01**

> 실제 수행 업무: Extract fields from trade finance documents

- P02 연결 근거: 대량 무역문서의 수기 입력 부담에 대해 필드 추출을 수행함.
  - problem: “High-volume invoices and shipping forms require slow manual entry and are vulnerable to human errors.”
  - task: “Extract fields from trade finance documents”
  - context: “Hong Leong Bank trade operations, multilingual financial documents.”

**AXV24_98092b8ca357**

> 실제 수행 업무: 상품 카탈로그 속성 추출·분류

- P02 연결 근거: 카탈로그 세부정보의 수동 추출·정리 부담과 속성 추출·분류가 명시됨.
  - problem: “상품 등록 담당자가 카탈로그의 세부 정보를 수동으로 추출·정리하는 데 많은 시간을 사용했다.”
  - task: “상품 카탈로그 속성 추출·분류”
  - context: “가격 비교 서비스 다나와의 상품 메타데이터 운영.”

**AXV24_bc6444cc1b61**

> 실제 수행 업무: 단체 의료보험 견적용 청구서 정보 추출

- P02 연결 근거: 다양한 청구서 PDF에서 가입자 정보를 수동 복사하는 부담과 추출 Task가 일치함.
  - problem: “보험 견적을 위해 다양한 청구서 PDF에서 가입자 정보를 수동 복사했으며, 인력 증가 없이 견적 물량이 늘었다.”
  - task: “단체 의료보험 견적용 청구서 정보 추출”
  - context: “18명의 보험심사자가 다양한 보험사 청구서를 처리하는 단체보험 견적 업무.”

**AXALL_US_OMB_2025_01589**

> 실제 수행 업무: Loan document data extraction for examination analytics

- P02 연결 근거: 신청 PDF의 수기 전사로 지연·오류가 생기며 문서 데이터 추출을 수행함.
  - problem: “Manual transcription from loan application PDFs causes delays, errors and staff costs in examination data collection.”
  - task: “Loan document data extraction for examination analytics”
  - context: “FDIC consumer protection personnel preparing loan data for compliance and fair lending reviews.”

**AXALL_US_OMB_2025_01754**

> 실제 수행 업무: Referral data structuring and completeness checks

- P02 연결 근거: 자유서술 자료의 수동·불일치 추적에 대해 데이터 구조화를 수행함.
  - problem: “Required referral information arrives as free text and is tracked manually and inconsistently, leaving missing fields to be checked.”
  - task: “Referral data structuring and completeness checks”
  - context: “HHS Office of Refugee Resettlement intake staff reviewing referral records from CBP.”

## legacy_D05

> 청구서 금액을 계약 요율로 계산한 금액과 대조해 다른 항목을 알려주세요.

**출처:** 이전 실제 LLM 선택 응답; 예전 업무형 기준

**표시:** 관점 1개 / 관점별 표시 합계 5개 / 중복 제외 사례 5개

### P03 업무 자료를 기준·다른 자료와 대조하는 검증 부담

**연결 유형:** 질문에 명시된 문제·업무

**질문 근거:** “대조해 다른 항목을 알려주세요”

청구서 금액을 계약 요율로 계산한 금액과 대조해 불일치 항목을 확인하려는 요청이며 대조 기준이 명시되어 있다.

|순위|참고 사례|다른 연결 관점|
|---|---|---|
|1|AXV24_36c7ef329920 — 채용 지원서·증빙 자료 대조 검토|없음|
|2|AXV2C_0006_02 — Validate customer order prices before invoicing|없음|
|3|AXALL_US_OMB_2025_01754 — Referral data structuring and completeness checks|없음|
|4|AXV2H_0003_01 — 직원 신원조회 보고서 검증|없음|
|5|AXV2P2_0011_01 — Audit freight invoices for overcharges|없음|

**AXV24_36c7ef329920를 참고하는 이유:** 청구서 금액을 계약 요율로 계산한 금액과 대조해 불일치 항목을 확인하려는 요청이며 대조 기준이 명시되어 있다. 이 사례에서 실제 확인된 업무: 지원서·증빙 자료 대조.

**차이·확인할 조건:**

- 지원자의 최종 합격판정과 별개
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV2C_0006_02를 참고하는 이유:** 청구서 금액을 계약 요율로 계산한 금액과 대조해 불일치 항목을 확인하려는 요청이며 대조 기준이 명시되어 있다. 이 사례에서 실제 확인된 업무: 고객 주문가격 검증.

**차이·확인할 조건:**

- 가격 자동변경·대금 지급 실행은 미확인
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXALL_US_OMB_2025_01754를 참고하는 이유:** 청구서 금액을 계약 요율로 계산한 금액과 대조해 불일치 항목을 확인하려는 요청이며 대조 기준이 명시되어 있다. 이 사례에서 실제 확인된 업무: 필수항목 완전성 점검.

**차이·확인할 조건:**

- 구조화 자체는 P02, 내용 누락 확인은 P03의 별도 근거
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV2H_0003_01를 참고하는 이유:** 청구서 금액을 계약 요율로 계산한 금액과 대조해 불일치 항목을 확인하려는 요청이며 대조 기준이 명시되어 있다. 이 사례에서 실제 확인된 업무: 신원조회 보고서의 기준 대조 검증.

**차이·확인할 조건:**

- 채용 의사결정·신원 사실의 절대 보장으로 해석하지 않음
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV2P2_0011_01를 참고하는 이유:** 청구서 금액을 계약 요율로 계산한 금액과 대조해 불일치 항목을 확인하려는 요청이며 대조 기준이 명시되어 있다. 이 사례에서 실제 확인된 업무: 청구서 과다청구 감사.

**차이·확인할 조건:**

- 환급·대금차감 자동 실행은 미확인
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

### 중복을 합친 사례 상세 근거

**AXV24_36c7ef329920**

> 실제 수행 업무: 채용 지원서·증빙 자료 대조 검토

- P03 연결 근거: 대량 지원서·증빙 검토의 인력 부담과 대조 검토 Task가 명시됨.
  - problem: “3주 안에 150만 건의 채용 지원서와 증빙을 검토해야 했으며 수작업 방식으로는 대규모 인력이 필요했다.”
  - task: “채용 지원서·증빙 자료 대조 검토”
  - context: “고객사의 대량 채용 서류 검토를 수행하는 BPO 기업의 운영 업무.”

**AXV2C_0006_02**

> 실제 수행 업무: Validate customer order prices before invoicing

- P03 연결 근거: 주문가격 불일치·입력 오류 문제에 대해 청구 전 가격 검증을 수행함.
  - problem: “Orders in varied formats produced pricing inconsistencies and entry errors, followed by disputes and delayed payments.”
  - task: “Validate customer order prices before invoicing”
  - context: “Danone receives thousands of orders daily through email, PDF and EDI.”

**AXALL_US_OMB_2025_01754**

> 실제 수행 업무: Referral data structuring and completeness checks

- P03 연결 근거: 필수 의뢰항목 누락이 문제이고 Task에 완전성 점검이 명시됨.
  - problem: “Required referral information arrives as free text and is tracked manually and inconsistently, leaving missing fields to be checked.”
  - task: “Referral data structuring and completeness checks”
  - context: “HHS Office of Refugee Resettlement intake staff reviewing referral records from CBP.”

**AXV2H_0003_01**

> 실제 수행 업무: 직원 신원조회 보고서 검증

- P03 연결 근거: 다수 파일과 검증기준을 수작업 대조하는 부담이 있고 보고서 검증을 수행함.
  - problem: “다수 파일과 검증 기준을 수작업 대조하면서 검증 지연과 준수 부담이 발생함”
  - task: “직원 신원조회 보고서 검증”
  - context: “업무별 검증 조건과 컴플라이언스 준수가 필수인 전문서비스”

**AXV2P2_0011_01**

> 실제 수행 업무: Audit freight invoices for overcharges

- P03 연결 근거: 운송 청구서와 약정요율 불일치를 확인하는 수기 부담과 감사 Task가 명시됨.
  - problem: “Freight invoices may not match negotiated rates and manual checking burdens logistics staff.”
  - task: “Audit freight invoices for overcharges”
  - context: “Dow logistics spending and emailed PDF invoices”

## legacy_D06

> 접수한 지원서의 경력 기재를 직무별 필수 요건과 견주어 충족하지 못한 항목을 표시해주세요.

**출처:** 이전 실제 LLM 선택 응답; 예전 업무형 기준

**표시:** 관점 1개 / 관점별 표시 합계 5개 / 중복 제외 사례 5개

### P03 업무 자료를 기준·다른 자료와 대조하는 검증 부담

**연결 유형:** 질문에 명시된 문제·업무

**질문 근거:** “직무별 필수 요건과 견주어 충족하지 못한 항목을 표시”

접수한 지원서의 경력 기재를 직무별 필수 요건이라는 명시 기준과 대조해 미충족 항목을 표시하려는 요청이다.

|순위|참고 사례|다른 연결 관점|
|---|---|---|
|1|AXV24_36c7ef329920 — 채용 지원서·증빙 자료 대조 검토|없음|
|2|AXV2H_0003_01 — 직원 신원조회 보고서 검증|없음|
|3|AXALL_US_OMB_2025_01754 — Referral data structuring and completeness checks|없음|
|4|AXV2P2_0011_01 — Audit freight invoices for overcharges|없음|
|5|AXV2C_0006_02 — Validate customer order prices before invoicing|없음|

**AXV24_36c7ef329920를 참고하는 이유:** 접수한 지원서의 경력 기재를 직무별 필수 요건이라는 명시 기준과 대조해 미충족 항목을 표시하려는 요청이다. 이 사례에서 실제 확인된 업무: 지원서·증빙 자료 대조.

**차이·확인할 조건:**

- 지원자의 최종 합격판정과 별개
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV2H_0003_01를 참고하는 이유:** 접수한 지원서의 경력 기재를 직무별 필수 요건이라는 명시 기준과 대조해 미충족 항목을 표시하려는 요청이다. 이 사례에서 실제 확인된 업무: 신원조회 보고서의 기준 대조 검증.

**차이·확인할 조건:**

- 채용 의사결정·신원 사실의 절대 보장으로 해석하지 않음
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXALL_US_OMB_2025_01754를 참고하는 이유:** 접수한 지원서의 경력 기재를 직무별 필수 요건이라는 명시 기준과 대조해 미충족 항목을 표시하려는 요청이다. 이 사례에서 실제 확인된 업무: 필수항목 완전성 점검.

**차이·확인할 조건:**

- 구조화 자체는 P02, 내용 누락 확인은 P03의 별도 근거
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV2P2_0011_01를 참고하는 이유:** 접수한 지원서의 경력 기재를 직무별 필수 요건이라는 명시 기준과 대조해 미충족 항목을 표시하려는 요청이다. 이 사례에서 실제 확인된 업무: 청구서 과다청구 감사.

**차이·확인할 조건:**

- 환급·대금차감 자동 실행은 미확인
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV2C_0006_02를 참고하는 이유:** 접수한 지원서의 경력 기재를 직무별 필수 요건이라는 명시 기준과 대조해 미충족 항목을 표시하려는 요청이다. 이 사례에서 실제 확인된 업무: 고객 주문가격 검증.

**차이·확인할 조건:**

- 가격 자동변경·대금 지급 실행은 미확인
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

### 중복을 합친 사례 상세 근거

**AXV24_36c7ef329920**

> 실제 수행 업무: 채용 지원서·증빙 자료 대조 검토

- P03 연결 근거: 대량 지원서·증빙 검토의 인력 부담과 대조 검토 Task가 명시됨.
  - problem: “3주 안에 150만 건의 채용 지원서와 증빙을 검토해야 했으며 수작업 방식으로는 대규모 인력이 필요했다.”
  - task: “채용 지원서·증빙 자료 대조 검토”
  - context: “고객사의 대량 채용 서류 검토를 수행하는 BPO 기업의 운영 업무.”

**AXV2H_0003_01**

> 실제 수행 업무: 직원 신원조회 보고서 검증

- P03 연결 근거: 다수 파일과 검증기준을 수작업 대조하는 부담이 있고 보고서 검증을 수행함.
  - problem: “다수 파일과 검증 기준을 수작업 대조하면서 검증 지연과 준수 부담이 발생함”
  - task: “직원 신원조회 보고서 검증”
  - context: “업무별 검증 조건과 컴플라이언스 준수가 필수인 전문서비스”

**AXALL_US_OMB_2025_01754**

> 실제 수행 업무: Referral data structuring and completeness checks

- P03 연결 근거: 필수 의뢰항목 누락이 문제이고 Task에 완전성 점검이 명시됨.
  - problem: “Required referral information arrives as free text and is tracked manually and inconsistently, leaving missing fields to be checked.”
  - task: “Referral data structuring and completeness checks”
  - context: “HHS Office of Refugee Resettlement intake staff reviewing referral records from CBP.”

**AXV2P2_0011_01**

> 실제 수행 업무: Audit freight invoices for overcharges

- P03 연결 근거: 운송 청구서와 약정요율 불일치를 확인하는 수기 부담과 감사 Task가 명시됨.
  - problem: “Freight invoices may not match negotiated rates and manual checking burdens logistics staff.”
  - task: “Audit freight invoices for overcharges”
  - context: “Dow logistics spending and emailed PDF invoices”

**AXV2C_0006_02**

> 실제 수행 업무: Validate customer order prices before invoicing

- P03 연결 근거: 주문가격 불일치·입력 오류 문제에 대해 청구 전 가격 검증을 수행함.
  - problem: “Orders in varied formats produced pricing inconsistencies and entry errors, followed by disputes and delayed payments.”
  - task: “Validate customer order prices before invoicing”
  - context: “Danone receives thousands of orders daily through email, PDF and EDI.”

## legacy_D07

> 야간에 고객 문의가 누락됩니다. 이 시간에도 문의에 응답하고 싶습니다.

**출처:** 이전 실제 LLM 선택 응답; 예전 업무형 기준

**표시:** 관점 1개 / 관점별 표시 합계 4개 / 중복 제외 사례 4개

### P04 문의량·접수 시간대가 응대 가능 용량을 넘어 대기·누락이 생김

**연결 유형:** 질문에 명시된 문제·업무

**질문 근거:** “이 시간에도 문의에 응답하고 싶습니다”

야간 시간대에 고객 문의가 누락되어 이 시간에도 실제 문의에 응답하려는 요청입니다.

|순위|참고 사례|다른 연결 관점|
|---|---|---|
|1|AXV2P2_0060_01 — Answer airline customer service questions|없음|
|2|AXV2H_0001_01 — 고객 문의 자율응답|없음|
|3|AXV24_71def85d86bd — 의료기관의 보험 자격·보장 음성 문의 응대|없음|
|4|AXV24_df5d48fedff4 — RV 고객 문의의 상시 응대 및 상담원 인계|없음|

**AXV2P2_0060_01를 참고하는 이유:** 야간 시간대에 고객 문의가 누락되어 이 시간에도 실제 문의에 응답하려는 요청입니다. 이 사례에서 실제 확인된 업무: 항공 고객서비스 질문 응답.

**차이·확인할 조건:**

- 이 요약만으로 야간·모든 채널·예약변경 실행을 보장하지 않음
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV2H_0001_01를 참고하는 이유:** 야간 시간대에 고객 문의가 누락되어 이 시간에도 실제 문의에 응답하려는 요청입니다. 이 사례에서 실제 확인된 업무: 서면 고객 문의 응답.

**차이·확인할 조건:**

- 음성이나 CRM변경 기능으로 확대하지 않음
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV24_71def85d86bd를 참고하는 이유:** 야간 시간대에 고객 문의가 누락되어 이 시간에도 실제 문의에 응답하려는 요청입니다. 이 사례에서 실제 확인된 업무: 보험 자격·보장 음성 문의 응대.

**차이·확인할 조건:**

- 청구 승인·보험금 지급·24시간 지원은 이 요약에서 확정하지 않음
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV24_df5d48fedff4를 참고하는 이유:** 야간 시간대에 고객 문의가 누락되어 이 시간에도 실제 문의에 응답하려는 요청입니다. 이 사례에서 실제 확인된 업무: 상시 문의 응대·상담원 인계.

**차이·확인할 조건:**

- 인계 자체는 명시됐지만 인계 시 맥락 손실 해결 효과까지 증명하지 않음
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

### 중복을 합친 사례 상세 근거

**AXV2P2_0060_01**

> 실제 수행 업무: Answer airline customer service questions

- P04 연결 근거: 대량 고객 문의가 지원조직을 압도하고 지연을 만들며 고객응대를 수행함.
  - problem: “Millions of customer questions overwhelmed airline support, increasing costs and response delays.”
  - task: “Answer airline customer service questions”
  - context: “Air India AI.g customer support”

**AXV2H_0001_01**

> 실제 수행 업무: 고객 문의 자율응답

- P04 연결 근거: 대량 문의로 정시/영업외 대응 유지가 어려우며 문의 자율응답을 수행함.
  - problem: “하루 최대 600건의 문의로 소규모 지원팀이 정시와 영업시간 외 고객대응을 유지하기 어려움”
  - task: “고객 문의 자율응답”
  - context: “전자청구 SaaS 서비스의 대량 서면 문의와 야간 문의”

**AXV24_71def85d86bd**

> 실제 수행 업무: 의료기관의 보험 자격·보장 음성 문의 응대

- P04 연결 근거: 정형 자격·보장 문의의 상담원 쏠림으로 대기 부담이 있고 음성 문의에 응대함.
  - problem: “기존 IVR에서 다수의 정형적 자격·보장 문의가 상담원에게 넘어가 비용과 대기 부담이 커졌다.”
  - task: “의료기관의 보험 자격·보장 음성 문의 응대”
  - context: “의료기관 행정직원이 가입자의 보험 정보를 확인하는 보험사 서비스 운영.”

**AXV24_df5d48fedff4**

> 실제 수행 업무: RV 고객 문의의 상시 응대 및 상담원 인계

- P04 연결 근거: 계절성 문의와 야간 공백으로 대기·누락이 생기며 상시 응대 및 인계 Task가 명시됨.
  - problem: “계절성 문의 증가와 야간 상담 공백으로 고객 대기가 길어지고 일부 문의가 누락됐다.”
  - task: “RV 고객 문의의 상시 응대 및 상담원 인계”
  - context: “여러 사업 부문의 웹·문자 채널에서 들어오는 고객지원 문의.”

## legacy_D08

> 주말에는 상담원이 없어 고객이 오래 기다립니다. 들어오는 질문에 답해주고 싶습니다.

**출처:** 이전 실제 LLM 선택 응답; 예전 업무형 기준

**표시:** 관점 1개 / 관점별 표시 합계 4개 / 중복 제외 사례 4개

### P04 문의량·접수 시간대가 응대 가능 용량을 넘어 대기·누락이 생김

**연결 유형:** 질문에 명시된 문제·업무

**질문 근거:** “들어오는 질문에 답해주고 싶습니다”

주말 상담원 부재로 대기가 길어져 고객의 들어오는 질문에 답하려는 요청이다. 응대 필요와 시간대·대기 공백이 모두 확인된다.

|순위|참고 사례|다른 연결 관점|
|---|---|---|
|1|AXV2P2_0060_01 — Answer airline customer service questions|없음|
|2|AXV2H_0001_01 — 고객 문의 자율응답|없음|
|3|AXV24_71def85d86bd — 의료기관의 보험 자격·보장 음성 문의 응대|없음|
|4|AXV24_df5d48fedff4 — RV 고객 문의의 상시 응대 및 상담원 인계|없음|

**AXV2P2_0060_01를 참고하는 이유:** 주말 상담원 부재로 대기가 길어져 고객의 들어오는 질문에 답하려는 요청이다. 응대 필요와 시간대·대기 공백이 모두 확인된다. 이 사례에서 실제 확인된 업무: 항공 고객서비스 질문 응답.

**차이·확인할 조건:**

- 이 요약만으로 야간·모든 채널·예약변경 실행을 보장하지 않음
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV2H_0001_01를 참고하는 이유:** 주말 상담원 부재로 대기가 길어져 고객의 들어오는 질문에 답하려는 요청이다. 응대 필요와 시간대·대기 공백이 모두 확인된다. 이 사례에서 실제 확인된 업무: 서면 고객 문의 응답.

**차이·확인할 조건:**

- 음성이나 CRM변경 기능으로 확대하지 않음
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV24_71def85d86bd를 참고하는 이유:** 주말 상담원 부재로 대기가 길어져 고객의 들어오는 질문에 답하려는 요청이다. 응대 필요와 시간대·대기 공백이 모두 확인된다. 이 사례에서 실제 확인된 업무: 보험 자격·보장 음성 문의 응대.

**차이·확인할 조건:**

- 청구 승인·보험금 지급·24시간 지원은 이 요약에서 확정하지 않음
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV24_df5d48fedff4를 참고하는 이유:** 주말 상담원 부재로 대기가 길어져 고객의 들어오는 질문에 답하려는 요청이다. 응대 필요와 시간대·대기 공백이 모두 확인된다. 이 사례에서 실제 확인된 업무: 상시 문의 응대·상담원 인계.

**차이·확인할 조건:**

- 인계 자체는 명시됐지만 인계 시 맥락 손실 해결 효과까지 증명하지 않음
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

### 중복을 합친 사례 상세 근거

**AXV2P2_0060_01**

> 실제 수행 업무: Answer airline customer service questions

- P04 연결 근거: 대량 고객 문의가 지원조직을 압도하고 지연을 만들며 고객응대를 수행함.
  - problem: “Millions of customer questions overwhelmed airline support, increasing costs and response delays.”
  - task: “Answer airline customer service questions”
  - context: “Air India AI.g customer support”

**AXV2H_0001_01**

> 실제 수행 업무: 고객 문의 자율응답

- P04 연결 근거: 대량 문의로 정시/영업외 대응 유지가 어려우며 문의 자율응답을 수행함.
  - problem: “하루 최대 600건의 문의로 소규모 지원팀이 정시와 영업시간 외 고객대응을 유지하기 어려움”
  - task: “고객 문의 자율응답”
  - context: “전자청구 SaaS 서비스의 대량 서면 문의와 야간 문의”

**AXV24_71def85d86bd**

> 실제 수행 업무: 의료기관의 보험 자격·보장 음성 문의 응대

- P04 연결 근거: 정형 자격·보장 문의의 상담원 쏠림으로 대기 부담이 있고 음성 문의에 응대함.
  - problem: “기존 IVR에서 다수의 정형적 자격·보장 문의가 상담원에게 넘어가 비용과 대기 부담이 커졌다.”
  - task: “의료기관의 보험 자격·보장 음성 문의 응대”
  - context: “의료기관 행정직원이 가입자의 보험 정보를 확인하는 보험사 서비스 운영.”

**AXV24_df5d48fedff4**

> 실제 수행 업무: RV 고객 문의의 상시 응대 및 상담원 인계

- P04 연결 근거: 계절성 문의와 야간 공백으로 대기·누락이 생기며 상시 응대 및 인계 Task가 명시됨.
  - problem: “계절성 문의 증가와 야간 상담 공백으로 고객 대기가 길어지고 일부 문의가 누락됐다.”
  - task: “RV 고객 문의의 상시 응대 및 상담원 인계”
  - context: “여러 사업 부문의 웹·문자 채널에서 들어오는 고객지원 문의.”

## legacy_D09

> 청구서에서 금액을 추출하고 추출한 금액을 계약 기준과 대조해주세요.

**출처:** 이전 실제 LLM 선택 응답; 예전 업무형 기준

**표시:** 관점 2개 / 관점별 표시 합계 10개 / 중복 제외 사례 9개

### P02 비정형 자료를 수기로 옮기고 업무 정보로 정리하는 부담

**연결 유형:** 질문에 명시된 문제·업무

**질문 근거:** “금액을 추출하고”

청구서 원자료에서 금액 항목을 꺼내는 추출 작업을 명확히 요청했다.

|순위|참고 사례|다른 연결 관점|
|---|---|---|
|1|AXV24_bc6444cc1b61 — 단체 의료보험 견적용 청구서 정보 추출|없음|
|2|AXALL_US_OMB_2025_01589 — Loan document data extraction for examination analytics|없음|
|3|AXV24_28baf265c6cf — 보험 인수심사용 신청 서류 추출·분류|없음|
|4|AXALL_US_OMB_2025_01754 — Referral data structuring and completeness checks|P03|
|5|AXV2C_0080_01 — Extract fields from trade finance documents|없음|

**AXV24_bc6444cc1b61를 참고하는 이유:** 청구서 원자료에서 금액 항목을 꺼내는 추출 작업을 명확히 요청했다. 이 사례에서 실제 확인된 업무: 견적용 청구서 정보 추출.

**차이·확인할 조건:**

- 보험 견적 산정이나 심사 판단 자체는 미확인
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXALL_US_OMB_2025_01589를 참고하는 이유:** 청구서 원자료에서 금액 항목을 꺼내는 추출 작업을 명확히 요청했다. 이 사례에서 실제 확인된 업무: 대출 문서 데이터 추출.

**차이·확인할 조건:**

- 대출 승인·사실 확인까지 수행한다고 해석하지 않음
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV24_28baf265c6cf를 참고하는 이유:** 청구서 원자료에서 금액 항목을 꺼내는 추출 작업을 명확히 요청했다. 이 사례에서 실제 확인된 업무: 보험 신청 서류 추출·분류.

**차이·확인할 조건:**

- 최종 보험 인수 결정은 미확인
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXALL_US_OMB_2025_01754를 참고하는 이유:** 청구서 원자료에서 금액 항목을 꺼내는 추출 작업을 명확히 요청했다. 이 사례에서 실제 확인된 업무: 의뢰 자료 데이터 구조화.

**차이·확인할 조건:**

- 필수항목 확인도 별도 명시되어 P03과 중복 연결하되 역할을 구분
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV2C_0080_01를 참고하는 이유:** 청구서 원자료에서 금액 항목을 꺼내는 추출 작업을 명확히 요청했다. 이 사례에서 실제 확인된 업무: 무역금융 문서 필드 추출.

**차이·확인할 조건:**

- 규제위험 판단·제재 심사로 확대하지 않음
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

### P03 업무 자료를 기준·다른 자료와 대조하는 검증 부담

**연결 유형:** 질문에 명시된 문제·업무

**질문 근거:** “대조해주세요”

추출한 금액을 계약 기준과 대조하는 작업을 명확히 요청했다.

|순위|참고 사례|다른 연결 관점|
|---|---|---|
|1|AXV24_36c7ef329920 — 채용 지원서·증빙 자료 대조 검토|없음|
|2|AXALL_US_OMB_2025_01754 — Referral data structuring and completeness checks|P02|
|3|AXV2H_0003_01 — 직원 신원조회 보고서 검증|없음|
|4|AXV2C_0006_02 — Validate customer order prices before invoicing|없음|
|5|AXV2P2_0011_01 — Audit freight invoices for overcharges|없음|

**AXV24_36c7ef329920를 참고하는 이유:** 추출한 금액을 계약 기준과 대조하는 작업을 명확히 요청했다. 이 사례에서 실제 확인된 업무: 지원서·증빙 자료 대조.

**차이·확인할 조건:**

- 지원자의 최종 합격판정과 별개
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXALL_US_OMB_2025_01754를 참고하는 이유:** 추출한 금액을 계약 기준과 대조하는 작업을 명확히 요청했다. 이 사례에서 실제 확인된 업무: 필수항목 완전성 점검.

**차이·확인할 조건:**

- 구조화 자체는 P02, 내용 누락 확인은 P03의 별도 근거
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV2H_0003_01를 참고하는 이유:** 추출한 금액을 계약 기준과 대조하는 작업을 명확히 요청했다. 이 사례에서 실제 확인된 업무: 신원조회 보고서의 기준 대조 검증.

**차이·확인할 조건:**

- 채용 의사결정·신원 사실의 절대 보장으로 해석하지 않음
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV2C_0006_02를 참고하는 이유:** 추출한 금액을 계약 기준과 대조하는 작업을 명확히 요청했다. 이 사례에서 실제 확인된 업무: 고객 주문가격 검증.

**차이·확인할 조건:**

- 가격 자동변경·대금 지급 실행은 미확인
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV2P2_0011_01를 참고하는 이유:** 추출한 금액을 계약 기준과 대조하는 작업을 명확히 요청했다. 이 사례에서 실제 확인된 업무: 청구서 과다청구 감사.

**차이·확인할 조건:**

- 환급·대금차감 자동 실행은 미확인
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

### 중복을 합친 사례 상세 근거

**AXV24_bc6444cc1b61**

> 실제 수행 업무: 단체 의료보험 견적용 청구서 정보 추출

- P02 연결 근거: 다양한 청구서 PDF에서 가입자 정보를 수동 복사하는 부담과 추출 Task가 일치함.
  - problem: “보험 견적을 위해 다양한 청구서 PDF에서 가입자 정보를 수동 복사했으며, 인력 증가 없이 견적 물량이 늘었다.”
  - task: “단체 의료보험 견적용 청구서 정보 추출”
  - context: “18명의 보험심사자가 다양한 보험사 청구서를 처리하는 단체보험 견적 업무.”

**AXALL_US_OMB_2025_01589**

> 실제 수행 업무: Loan document data extraction for examination analytics

- P02 연결 근거: 신청 PDF의 수기 전사로 지연·오류가 생기며 문서 데이터 추출을 수행함.
  - problem: “Manual transcription from loan application PDFs causes delays, errors and staff costs in examination data collection.”
  - task: “Loan document data extraction for examination analytics”
  - context: “FDIC consumer protection personnel preparing loan data for compliance and fair lending reviews.”

**AXV24_28baf265c6cf**

> 실제 수행 업무: 보험 인수심사용 신청 서류 추출·분류

- P02 연결 근거: 형식이 다른 보험 자료를 수작업으로 추출하는 부담과 추출·분류 Task가 명시됨.
  - problem: “형식과 주기가 다른 보험 신청 자료에서 담당자가 직접 정보를 추출했으며, 증가하는 접수량을 수작업으로 처리하기 어려웠다.”
  - task: “보험 인수심사용 신청 서류 추출·분류”
  - context: “시니어 리빙 시설의 배상책임보험을 인수하는 심사팀.”

**AXALL_US_OMB_2025_01754**

> 실제 수행 업무: Referral data structuring and completeness checks

- P02 연결 근거: 자유서술 자료의 수동·불일치 추적에 대해 데이터 구조화를 수행함.
  - problem: “Required referral information arrives as free text and is tracked manually and inconsistently, leaving missing fields to be checked.”
  - task: “Referral data structuring and completeness checks”
  - context: “HHS Office of Refugee Resettlement intake staff reviewing referral records from CBP.”
- P03 연결 근거: 필수 의뢰항목 누락이 문제이고 Task에 완전성 점검이 명시됨.
  - problem: “Required referral information arrives as free text and is tracked manually and inconsistently, leaving missing fields to be checked.”
  - task: “Referral data structuring and completeness checks”
  - context: “HHS Office of Refugee Resettlement intake staff reviewing referral records from CBP.”

**AXV2C_0080_01**

> 실제 수행 업무: Extract fields from trade finance documents

- P02 연결 근거: 대량 무역문서의 수기 입력 부담에 대해 필드 추출을 수행함.
  - problem: “High-volume invoices and shipping forms require slow manual entry and are vulnerable to human errors.”
  - task: “Extract fields from trade finance documents”
  - context: “Hong Leong Bank trade operations, multilingual financial documents.”

**AXV24_36c7ef329920**

> 실제 수행 업무: 채용 지원서·증빙 자료 대조 검토

- P03 연결 근거: 대량 지원서·증빙 검토의 인력 부담과 대조 검토 Task가 명시됨.
  - problem: “3주 안에 150만 건의 채용 지원서와 증빙을 검토해야 했으며 수작업 방식으로는 대규모 인력이 필요했다.”
  - task: “채용 지원서·증빙 자료 대조 검토”
  - context: “고객사의 대량 채용 서류 검토를 수행하는 BPO 기업의 운영 업무.”

**AXV2H_0003_01**

> 실제 수행 업무: 직원 신원조회 보고서 검증

- P03 연결 근거: 다수 파일과 검증기준을 수작업 대조하는 부담이 있고 보고서 검증을 수행함.
  - problem: “다수 파일과 검증 기준을 수작업 대조하면서 검증 지연과 준수 부담이 발생함”
  - task: “직원 신원조회 보고서 검증”
  - context: “업무별 검증 조건과 컴플라이언스 준수가 필수인 전문서비스”

**AXV2C_0006_02**

> 실제 수행 업무: Validate customer order prices before invoicing

- P03 연결 근거: 주문가격 불일치·입력 오류 문제에 대해 청구 전 가격 검증을 수행함.
  - problem: “Orders in varied formats produced pricing inconsistencies and entry errors, followed by disputes and delayed payments.”
  - task: “Validate customer order prices before invoicing”
  - context: “Danone receives thousands of orders daily through email, PDF and EDI.”

**AXV2P2_0011_01**

> 실제 수행 업무: Audit freight invoices for overcharges

- P03 연결 근거: 운송 청구서와 약정요율 불일치를 확인하는 수기 부담과 감사 Task가 명시됨.
  - problem: “Freight invoices may not match negotiated rates and manual checking burdens logistics staff.”
  - task: “Audit freight invoices for overcharges”
  - context: “Dow logistics spending and emailed PDF invoices”

## legacy_D10

> 사내 출장 규정을 검색해주세요. 별도로 직원이 제출한 영수증에서 날짜와 금액을 추출해주세요.

**출처:** 이전 실제 LLM 선택 응답; 예전 업무형 기준

**표시:** 관점 2개 / 관점별 표시 합계 8개 / 중복 제외 사례 8개

### P01 업무 지식이 길고 분산돼 필요한 근거를 찾는 데 시간이 걸림

**연결 유형:** 질문에 명시된 문제·업무

**질문 근거:** “사내 출장 규정을 검색해주세요”

기존 사내 출장 규정 문서에서 내용을 찾으려는 요청이다.

|순위|참고 사례|다른 연결 관점|
|---|---|---|
|1|AXV2N_0110 — Retrieve internal knowledge for financial advisors|없음|
|2|AXALL_US_OMB_2025_02663 — Document retrieval and cross-reference support|없음|
|3|AXV2P2_0010_01 — Retrieve CAD/CAM product support knowledge|없음|

**AXV2N_0110를 참고하는 이유:** 기존 사내 출장 규정 문서에서 내용을 찾으려는 요청이다. 이 사례에서 실제 확인된 업무: 내부 지식 검색.

**차이·확인할 조건:**

- 외부 고객의 금융판단 대행으로 확대하지 않음
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXALL_US_OMB_2025_02663를 참고하는 이유:** 기존 사내 출장 규정 문서에서 내용을 찾으려는 요청이다. 이 사례에서 실제 확인된 업무: 문서 검색 및 교차참조 지원.

**차이·확인할 조건:**

- 정책 승인이나 규제 적합성 확정 기능까지 뜻하지 않음
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV2P2_0010_01를 참고하는 이유:** 기존 사내 출장 규정 문서에서 내용을 찾으려는 요청이다. 이 사례에서 실제 확인된 업무: CAD/CAM 지원지식 검색.

**차이·확인할 조건:**

- 제품 조작·설계 변경의 자동 실행은 미확인
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

### P02 비정형 자료를 수기로 옮기고 업무 정보로 정리하는 부담

**연결 유형:** 질문에 명시된 문제·업무

**질문 근거:** “날짜와 금액을 추출해주세요”

직원이 제출한 영수증 원자료에서 날짜와 금액 항목을 꺼내려는 요청이다.

|순위|참고 사례|다른 연결 관점|
|---|---|---|
|1|AXV24_bc6444cc1b61 — 단체 의료보험 견적용 청구서 정보 추출|없음|
|2|AXALL_US_OMB_2025_01589 — Loan document data extraction for examination analytics|없음|
|3|AXV24_28baf265c6cf — 보험 인수심사용 신청 서류 추출·분류|없음|
|4|AXALL_US_OMB_2025_01754 — Referral data structuring and completeness checks|없음|
|5|AXV2C_0080_01 — Extract fields from trade finance documents|없음|

**AXV24_bc6444cc1b61를 참고하는 이유:** 직원이 제출한 영수증 원자료에서 날짜와 금액 항목을 꺼내려는 요청이다. 이 사례에서 실제 확인된 업무: 견적용 청구서 정보 추출.

**차이·확인할 조건:**

- 보험 견적 산정이나 심사 판단 자체는 미확인
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXALL_US_OMB_2025_01589를 참고하는 이유:** 직원이 제출한 영수증 원자료에서 날짜와 금액 항목을 꺼내려는 요청이다. 이 사례에서 실제 확인된 업무: 대출 문서 데이터 추출.

**차이·확인할 조건:**

- 대출 승인·사실 확인까지 수행한다고 해석하지 않음
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV24_28baf265c6cf를 참고하는 이유:** 직원이 제출한 영수증 원자료에서 날짜와 금액 항목을 꺼내려는 요청이다. 이 사례에서 실제 확인된 업무: 보험 신청 서류 추출·분류.

**차이·확인할 조건:**

- 최종 보험 인수 결정은 미확인
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXALL_US_OMB_2025_01754를 참고하는 이유:** 직원이 제출한 영수증 원자료에서 날짜와 금액 항목을 꺼내려는 요청이다. 이 사례에서 실제 확인된 업무: 의뢰 자료 데이터 구조화.

**차이·확인할 조건:**

- 필수항목 확인도 별도 명시되어 P03과 중복 연결하되 역할을 구분
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV2C_0080_01를 참고하는 이유:** 직원이 제출한 영수증 원자료에서 날짜와 금액 항목을 꺼내려는 요청이다. 이 사례에서 실제 확인된 업무: 무역금융 문서 필드 추출.

**차이·확인할 조건:**

- 규제위험 판단·제재 심사로 확대하지 않음
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

### 중복을 합친 사례 상세 근거

**AXV2N_0110**

> 실제 수행 업무: Retrieve internal knowledge for financial advisors

- P01 연결 근거: 금융자문 직원의 내부문서 탐색 시간이 문제이고 지식 검색을 수행함.
  - problem: “Advisors spend hours searching a large internal document corpus.”
  - task: “Retrieve internal knowledge for financial advisors”
  - context: “Wealth management advisor teams using AI at Morgan Stanley Assistant.”

**AXALL_US_OMB_2025_02663**

> 실제 수행 업무: Document retrieval and cross-reference support

- P01 연결 근거: 긴 문서·정책의 탐색 병목과 검색·교차참조 작업이 함께 명시됨.
  - problem: “Staff must search and cross-reference lengthy documents and policies, creating a time-consuming information bottleneck.”
  - task: “Document retrieval and cross-reference support”
  - context: “Nuclear Regulatory Commission staff supporting licensing and oversight work.”

**AXV2P2_0010_01**

> 실제 수행 업무: Retrieve CAD/CAM product support knowledge

- P01 연결 근거: 접근하기 어려운 제품 전문지식을 검색하는 작업이 명시됨.
  - problem: “Complex manufacturing product knowledge is difficult to access as expertise and skills become scarce.”
  - task: “Retrieve CAD/CAM product support knowledge”
  - context: “Sandvik manufacturing software support teams and customers”

**AXV24_bc6444cc1b61**

> 실제 수행 업무: 단체 의료보험 견적용 청구서 정보 추출

- P02 연결 근거: 다양한 청구서 PDF에서 가입자 정보를 수동 복사하는 부담과 추출 Task가 일치함.
  - problem: “보험 견적을 위해 다양한 청구서 PDF에서 가입자 정보를 수동 복사했으며, 인력 증가 없이 견적 물량이 늘었다.”
  - task: “단체 의료보험 견적용 청구서 정보 추출”
  - context: “18명의 보험심사자가 다양한 보험사 청구서를 처리하는 단체보험 견적 업무.”

**AXALL_US_OMB_2025_01589**

> 실제 수행 업무: Loan document data extraction for examination analytics

- P02 연결 근거: 신청 PDF의 수기 전사로 지연·오류가 생기며 문서 데이터 추출을 수행함.
  - problem: “Manual transcription from loan application PDFs causes delays, errors and staff costs in examination data collection.”
  - task: “Loan document data extraction for examination analytics”
  - context: “FDIC consumer protection personnel preparing loan data for compliance and fair lending reviews.”

**AXV24_28baf265c6cf**

> 실제 수행 업무: 보험 인수심사용 신청 서류 추출·분류

- P02 연결 근거: 형식이 다른 보험 자료를 수작업으로 추출하는 부담과 추출·분류 Task가 명시됨.
  - problem: “형식과 주기가 다른 보험 신청 자료에서 담당자가 직접 정보를 추출했으며, 증가하는 접수량을 수작업으로 처리하기 어려웠다.”
  - task: “보험 인수심사용 신청 서류 추출·분류”
  - context: “시니어 리빙 시설의 배상책임보험을 인수하는 심사팀.”

**AXALL_US_OMB_2025_01754**

> 실제 수행 업무: Referral data structuring and completeness checks

- P02 연결 근거: 자유서술 자료의 수동·불일치 추적에 대해 데이터 구조화를 수행함.
  - problem: “Required referral information arrives as free text and is tracked manually and inconsistently, leaving missing fields to be checked.”
  - task: “Referral data structuring and completeness checks”
  - context: “HHS Office of Refugee Resettlement intake staff reviewing referral records from CBP.”

**AXV2C_0080_01**

> 실제 수행 업무: Extract fields from trade finance documents

- P02 연결 근거: 대량 무역문서의 수기 입력 부담에 대해 필드 추출을 수행함.
  - problem: “High-volume invoices and shipping forms require slow manual entry and are vulnerable to human errors.”
  - task: “Extract fields from trade finance documents”
  - context: “Hong Leong Bank trade operations, multilingual financial documents.”

## legacy_D11

> 사내 출장 규정의 한도 조항을 검색하고, 영수증에서 금액을 추출한 다음 규정 한도와 대조해주세요.

**출처:** 이전 실제 LLM 선택 응답; 예전 업무형 기준

**표시:** 관점 3개 / 관점별 표시 합계 13개 / 중복 제외 사례 12개

### P01 업무 지식이 길고 분산돼 필요한 근거를 찾는 데 시간이 걸림

**연결 유형:** 질문에 명시된 문제·업무

**질문 근거:** “한도 조항을 검색하고”

기존 사내 출장 규정에서 한도 조항을 찾으려는 요청이다.

|순위|참고 사례|다른 연결 관점|
|---|---|---|
|1|AXV2N_0110 — Retrieve internal knowledge for financial advisors|없음|
|2|AXALL_US_OMB_2025_02663 — Document retrieval and cross-reference support|없음|
|3|AXV2P2_0010_01 — Retrieve CAD/CAM product support knowledge|없음|

**AXV2N_0110를 참고하는 이유:** 기존 사내 출장 규정에서 한도 조항을 찾으려는 요청이다. 이 사례에서 실제 확인된 업무: 내부 지식 검색.

**차이·확인할 조건:**

- 외부 고객의 금융판단 대행으로 확대하지 않음
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXALL_US_OMB_2025_02663를 참고하는 이유:** 기존 사내 출장 규정에서 한도 조항을 찾으려는 요청이다. 이 사례에서 실제 확인된 업무: 문서 검색 및 교차참조 지원.

**차이·확인할 조건:**

- 정책 승인이나 규제 적합성 확정 기능까지 뜻하지 않음
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV2P2_0010_01를 참고하는 이유:** 기존 사내 출장 규정에서 한도 조항을 찾으려는 요청이다. 이 사례에서 실제 확인된 업무: CAD/CAM 지원지식 검색.

**차이·확인할 조건:**

- 제품 조작·설계 변경의 자동 실행은 미확인
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

### P02 비정형 자료를 수기로 옮기고 업무 정보로 정리하는 부담

**연결 유형:** 질문에 명시된 문제·업무

**질문 근거:** “영수증에서 금액을 추출한”

영수증 원자료에서 금액 항목을 꺼내는 추출을 명시적으로 요청했다.

|순위|참고 사례|다른 연결 관점|
|---|---|---|
|1|AXV24_bc6444cc1b61 — 단체 의료보험 견적용 청구서 정보 추출|없음|
|2|AXALL_US_OMB_2025_01589 — Loan document data extraction for examination analytics|없음|
|3|AXV24_28baf265c6cf — 보험 인수심사용 신청 서류 추출·분류|없음|
|4|AXALL_US_OMB_2025_01754 — Referral data structuring and completeness checks|P03|
|5|AXV2C_0080_01 — Extract fields from trade finance documents|없음|

**AXV24_bc6444cc1b61를 참고하는 이유:** 영수증 원자료에서 금액 항목을 꺼내는 추출을 명시적으로 요청했다. 이 사례에서 실제 확인된 업무: 견적용 청구서 정보 추출.

**차이·확인할 조건:**

- 보험 견적 산정이나 심사 판단 자체는 미확인
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXALL_US_OMB_2025_01589를 참고하는 이유:** 영수증 원자료에서 금액 항목을 꺼내는 추출을 명시적으로 요청했다. 이 사례에서 실제 확인된 업무: 대출 문서 데이터 추출.

**차이·확인할 조건:**

- 대출 승인·사실 확인까지 수행한다고 해석하지 않음
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV24_28baf265c6cf를 참고하는 이유:** 영수증 원자료에서 금액 항목을 꺼내는 추출을 명시적으로 요청했다. 이 사례에서 실제 확인된 업무: 보험 신청 서류 추출·분류.

**차이·확인할 조건:**

- 최종 보험 인수 결정은 미확인
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXALL_US_OMB_2025_01754를 참고하는 이유:** 영수증 원자료에서 금액 항목을 꺼내는 추출을 명시적으로 요청했다. 이 사례에서 실제 확인된 업무: 의뢰 자료 데이터 구조화.

**차이·확인할 조건:**

- 필수항목 확인도 별도 명시되어 P03과 중복 연결하되 역할을 구분
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV2C_0080_01를 참고하는 이유:** 영수증 원자료에서 금액 항목을 꺼내는 추출을 명시적으로 요청했다. 이 사례에서 실제 확인된 업무: 무역금융 문서 필드 추출.

**차이·확인할 조건:**

- 규제위험 판단·제재 심사로 확대하지 않음
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

### P03 업무 자료를 기준·다른 자료와 대조하는 검증 부담

**연결 유형:** 질문에 명시된 문제·업무

**질문 근거:** “규정 한도와 대조해주세요”

추출한 영수증 금액을 규정 한도 기준과 대조하려는 요청이다.

|순위|참고 사례|다른 연결 관점|
|---|---|---|
|1|AXV24_36c7ef329920 — 채용 지원서·증빙 자료 대조 검토|없음|
|2|AXV2H_0003_01 — 직원 신원조회 보고서 검증|없음|
|3|AXV2P2_0011_01 — Audit freight invoices for overcharges|없음|
|4|AXV2C_0006_02 — Validate customer order prices before invoicing|없음|
|5|AXALL_US_OMB_2025_01754 — Referral data structuring and completeness checks|P02|

**AXV24_36c7ef329920를 참고하는 이유:** 추출한 영수증 금액을 규정 한도 기준과 대조하려는 요청이다. 이 사례에서 실제 확인된 업무: 지원서·증빙 자료 대조.

**차이·확인할 조건:**

- 지원자의 최종 합격판정과 별개
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV2H_0003_01를 참고하는 이유:** 추출한 영수증 금액을 규정 한도 기준과 대조하려는 요청이다. 이 사례에서 실제 확인된 업무: 신원조회 보고서의 기준 대조 검증.

**차이·확인할 조건:**

- 채용 의사결정·신원 사실의 절대 보장으로 해석하지 않음
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV2P2_0011_01를 참고하는 이유:** 추출한 영수증 금액을 규정 한도 기준과 대조하려는 요청이다. 이 사례에서 실제 확인된 업무: 청구서 과다청구 감사.

**차이·확인할 조건:**

- 환급·대금차감 자동 실행은 미확인
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV2C_0006_02를 참고하는 이유:** 추출한 영수증 금액을 규정 한도 기준과 대조하려는 요청이다. 이 사례에서 실제 확인된 업무: 고객 주문가격 검증.

**차이·확인할 조건:**

- 가격 자동변경·대금 지급 실행은 미확인
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXALL_US_OMB_2025_01754를 참고하는 이유:** 추출한 영수증 금액을 규정 한도 기준과 대조하려는 요청이다. 이 사례에서 실제 확인된 업무: 필수항목 완전성 점검.

**차이·확인할 조건:**

- 구조화 자체는 P02, 내용 누락 확인은 P03의 별도 근거
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

### 중복을 합친 사례 상세 근거

**AXV2N_0110**

> 실제 수행 업무: Retrieve internal knowledge for financial advisors

- P01 연결 근거: 금융자문 직원의 내부문서 탐색 시간이 문제이고 지식 검색을 수행함.
  - problem: “Advisors spend hours searching a large internal document corpus.”
  - task: “Retrieve internal knowledge for financial advisors”
  - context: “Wealth management advisor teams using AI at Morgan Stanley Assistant.”

**AXALL_US_OMB_2025_02663**

> 실제 수행 업무: Document retrieval and cross-reference support

- P01 연결 근거: 긴 문서·정책의 탐색 병목과 검색·교차참조 작업이 함께 명시됨.
  - problem: “Staff must search and cross-reference lengthy documents and policies, creating a time-consuming information bottleneck.”
  - task: “Document retrieval and cross-reference support”
  - context: “Nuclear Regulatory Commission staff supporting licensing and oversight work.”

**AXV2P2_0010_01**

> 실제 수행 업무: Retrieve CAD/CAM product support knowledge

- P01 연결 근거: 접근하기 어려운 제품 전문지식을 검색하는 작업이 명시됨.
  - problem: “Complex manufacturing product knowledge is difficult to access as expertise and skills become scarce.”
  - task: “Retrieve CAD/CAM product support knowledge”
  - context: “Sandvik manufacturing software support teams and customers”

**AXV24_bc6444cc1b61**

> 실제 수행 업무: 단체 의료보험 견적용 청구서 정보 추출

- P02 연결 근거: 다양한 청구서 PDF에서 가입자 정보를 수동 복사하는 부담과 추출 Task가 일치함.
  - problem: “보험 견적을 위해 다양한 청구서 PDF에서 가입자 정보를 수동 복사했으며, 인력 증가 없이 견적 물량이 늘었다.”
  - task: “단체 의료보험 견적용 청구서 정보 추출”
  - context: “18명의 보험심사자가 다양한 보험사 청구서를 처리하는 단체보험 견적 업무.”

**AXALL_US_OMB_2025_01589**

> 실제 수행 업무: Loan document data extraction for examination analytics

- P02 연결 근거: 신청 PDF의 수기 전사로 지연·오류가 생기며 문서 데이터 추출을 수행함.
  - problem: “Manual transcription from loan application PDFs causes delays, errors and staff costs in examination data collection.”
  - task: “Loan document data extraction for examination analytics”
  - context: “FDIC consumer protection personnel preparing loan data for compliance and fair lending reviews.”

**AXV24_28baf265c6cf**

> 실제 수행 업무: 보험 인수심사용 신청 서류 추출·분류

- P02 연결 근거: 형식이 다른 보험 자료를 수작업으로 추출하는 부담과 추출·분류 Task가 명시됨.
  - problem: “형식과 주기가 다른 보험 신청 자료에서 담당자가 직접 정보를 추출했으며, 증가하는 접수량을 수작업으로 처리하기 어려웠다.”
  - task: “보험 인수심사용 신청 서류 추출·분류”
  - context: “시니어 리빙 시설의 배상책임보험을 인수하는 심사팀.”

**AXALL_US_OMB_2025_01754**

> 실제 수행 업무: Referral data structuring and completeness checks

- P02 연결 근거: 자유서술 자료의 수동·불일치 추적에 대해 데이터 구조화를 수행함.
  - problem: “Required referral information arrives as free text and is tracked manually and inconsistently, leaving missing fields to be checked.”
  - task: “Referral data structuring and completeness checks”
  - context: “HHS Office of Refugee Resettlement intake staff reviewing referral records from CBP.”
- P03 연결 근거: 필수 의뢰항목 누락이 문제이고 Task에 완전성 점검이 명시됨.
  - problem: “Required referral information arrives as free text and is tracked manually and inconsistently, leaving missing fields to be checked.”
  - task: “Referral data structuring and completeness checks”
  - context: “HHS Office of Refugee Resettlement intake staff reviewing referral records from CBP.”

**AXV2C_0080_01**

> 실제 수행 업무: Extract fields from trade finance documents

- P02 연결 근거: 대량 무역문서의 수기 입력 부담에 대해 필드 추출을 수행함.
  - problem: “High-volume invoices and shipping forms require slow manual entry and are vulnerable to human errors.”
  - task: “Extract fields from trade finance documents”
  - context: “Hong Leong Bank trade operations, multilingual financial documents.”

**AXV24_36c7ef329920**

> 실제 수행 업무: 채용 지원서·증빙 자료 대조 검토

- P03 연결 근거: 대량 지원서·증빙 검토의 인력 부담과 대조 검토 Task가 명시됨.
  - problem: “3주 안에 150만 건의 채용 지원서와 증빙을 검토해야 했으며 수작업 방식으로는 대규모 인력이 필요했다.”
  - task: “채용 지원서·증빙 자료 대조 검토”
  - context: “고객사의 대량 채용 서류 검토를 수행하는 BPO 기업의 운영 업무.”

**AXV2H_0003_01**

> 실제 수행 업무: 직원 신원조회 보고서 검증

- P03 연결 근거: 다수 파일과 검증기준을 수작업 대조하는 부담이 있고 보고서 검증을 수행함.
  - problem: “다수 파일과 검증 기준을 수작업 대조하면서 검증 지연과 준수 부담이 발생함”
  - task: “직원 신원조회 보고서 검증”
  - context: “업무별 검증 조건과 컴플라이언스 준수가 필수인 전문서비스”

**AXV2P2_0011_01**

> 실제 수행 업무: Audit freight invoices for overcharges

- P03 연결 근거: 운송 청구서와 약정요율 불일치를 확인하는 수기 부담과 감사 Task가 명시됨.
  - problem: “Freight invoices may not match negotiated rates and manual checking burdens logistics staff.”
  - task: “Audit freight invoices for overcharges”
  - context: “Dow logistics spending and emailed PDF invoices”

**AXV2C_0006_02**

> 실제 수행 업무: Validate customer order prices before invoicing

- P03 연결 근거: 주문가격 불일치·입력 오류 문제에 대해 청구 전 가격 검증을 수행함.
  - problem: “Orders in varied formats produced pricing inconsistencies and entry errors, followed by disputes and delayed payments.”
  - task: “Validate customer order prices before invoicing”
  - context: “Danone receives thousands of orders daily through email, PDF and EDI.”

## legacy_D12

> 보험 청구서 PDF에서 가입자 정보를 뽑아주세요. 별도로 야간에 누락되는 고객 문의에 응답하고 싶습니다.

**출처:** 이전 실제 LLM 선택 응답; 예전 업무형 기준

**표시:** 관점 2개 / 관점별 표시 합계 9개 / 중복 제외 사례 9개

### P02 비정형 자료를 수기로 옮기고 업무 정보로 정리하는 부담

**연결 유형:** 질문에 명시된 문제·업무

**질문 근거:** “가입자 정보를 뽑아주세요”

PDF 청구서 원자료에서 가입자 정보를 꺼내 달라는 추출 요청입니다.

|순위|참고 사례|다른 연결 관점|
|---|---|---|
|1|AXV24_bc6444cc1b61 — 단체 의료보험 견적용 청구서 정보 추출|없음|
|2|AXALL_US_OMB_2025_01589 — Loan document data extraction for examination analytics|없음|
|3|AXV24_28baf265c6cf — 보험 인수심사용 신청 서류 추출·분류|없음|
|4|AXV2C_0080_01 — Extract fields from trade finance documents|없음|
|5|AXALL_US_OMB_2025_01754 — Referral data structuring and completeness checks|없음|

**AXV24_bc6444cc1b61를 참고하는 이유:** PDF 청구서 원자료에서 가입자 정보를 꺼내 달라는 추출 요청입니다. 이 사례에서 실제 확인된 업무: 견적용 청구서 정보 추출.

**차이·확인할 조건:**

- 보험 견적 산정이나 심사 판단 자체는 미확인
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXALL_US_OMB_2025_01589를 참고하는 이유:** PDF 청구서 원자료에서 가입자 정보를 꺼내 달라는 추출 요청입니다. 이 사례에서 실제 확인된 업무: 대출 문서 데이터 추출.

**차이·확인할 조건:**

- 대출 승인·사실 확인까지 수행한다고 해석하지 않음
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV24_28baf265c6cf를 참고하는 이유:** PDF 청구서 원자료에서 가입자 정보를 꺼내 달라는 추출 요청입니다. 이 사례에서 실제 확인된 업무: 보험 신청 서류 추출·분류.

**차이·확인할 조건:**

- 최종 보험 인수 결정은 미확인
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV2C_0080_01를 참고하는 이유:** PDF 청구서 원자료에서 가입자 정보를 꺼내 달라는 추출 요청입니다. 이 사례에서 실제 확인된 업무: 무역금융 문서 필드 추출.

**차이·확인할 조건:**

- 규제위험 판단·제재 심사로 확대하지 않음
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXALL_US_OMB_2025_01754를 참고하는 이유:** PDF 청구서 원자료에서 가입자 정보를 꺼내 달라는 추출 요청입니다. 이 사례에서 실제 확인된 업무: 의뢰 자료 데이터 구조화.

**차이·확인할 조건:**

- 필수항목 확인도 별도 명시되어 P03과 중복 연결하되 역할을 구분
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

### P04 문의량·접수 시간대가 응대 가능 용량을 넘어 대기·누락이 생김

**연결 유형:** 질문에 명시된 문제·업무

**질문 근거:** “고객 문의에 응답하고 싶습니다”

야간에 누락되는 고객 문의에 응답하려는 필요와 시간대 공백이 함께 나타납니다.

|순위|참고 사례|다른 연결 관점|
|---|---|---|
|1|AXV24_71def85d86bd — 의료기관의 보험 자격·보장 음성 문의 응대|없음|
|2|AXV2H_0001_01 — 고객 문의 자율응답|없음|
|3|AXV2P2_0060_01 — Answer airline customer service questions|없음|
|4|AXV24_df5d48fedff4 — RV 고객 문의의 상시 응대 및 상담원 인계|없음|

**AXV24_71def85d86bd를 참고하는 이유:** 야간에 누락되는 고객 문의에 응답하려는 필요와 시간대 공백이 함께 나타납니다. 이 사례에서 실제 확인된 업무: 보험 자격·보장 음성 문의 응대.

**차이·확인할 조건:**

- 청구 승인·보험금 지급·24시간 지원은 이 요약에서 확정하지 않음
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV2H_0001_01를 참고하는 이유:** 야간에 누락되는 고객 문의에 응답하려는 필요와 시간대 공백이 함께 나타납니다. 이 사례에서 실제 확인된 업무: 서면 고객 문의 응답.

**차이·확인할 조건:**

- 음성이나 CRM변경 기능으로 확대하지 않음
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV2P2_0060_01를 참고하는 이유:** 야간에 누락되는 고객 문의에 응답하려는 필요와 시간대 공백이 함께 나타납니다. 이 사례에서 실제 확인된 업무: 항공 고객서비스 질문 응답.

**차이·확인할 조건:**

- 이 요약만으로 야간·모든 채널·예약변경 실행을 보장하지 않음
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV24_df5d48fedff4를 참고하는 이유:** 야간에 누락되는 고객 문의에 응답하려는 필요와 시간대 공백이 함께 나타납니다. 이 사례에서 실제 확인된 업무: 상시 문의 응대·상담원 인계.

**차이·확인할 조건:**

- 인계 자체는 명시됐지만 인계 시 맥락 손실 해결 효과까지 증명하지 않음
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

### 중복을 합친 사례 상세 근거

**AXV24_bc6444cc1b61**

> 실제 수행 업무: 단체 의료보험 견적용 청구서 정보 추출

- P02 연결 근거: 다양한 청구서 PDF에서 가입자 정보를 수동 복사하는 부담과 추출 Task가 일치함.
  - problem: “보험 견적을 위해 다양한 청구서 PDF에서 가입자 정보를 수동 복사했으며, 인력 증가 없이 견적 물량이 늘었다.”
  - task: “단체 의료보험 견적용 청구서 정보 추출”
  - context: “18명의 보험심사자가 다양한 보험사 청구서를 처리하는 단체보험 견적 업무.”

**AXALL_US_OMB_2025_01589**

> 실제 수행 업무: Loan document data extraction for examination analytics

- P02 연결 근거: 신청 PDF의 수기 전사로 지연·오류가 생기며 문서 데이터 추출을 수행함.
  - problem: “Manual transcription from loan application PDFs causes delays, errors and staff costs in examination data collection.”
  - task: “Loan document data extraction for examination analytics”
  - context: “FDIC consumer protection personnel preparing loan data for compliance and fair lending reviews.”

**AXV24_28baf265c6cf**

> 실제 수행 업무: 보험 인수심사용 신청 서류 추출·분류

- P02 연결 근거: 형식이 다른 보험 자료를 수작업으로 추출하는 부담과 추출·분류 Task가 명시됨.
  - problem: “형식과 주기가 다른 보험 신청 자료에서 담당자가 직접 정보를 추출했으며, 증가하는 접수량을 수작업으로 처리하기 어려웠다.”
  - task: “보험 인수심사용 신청 서류 추출·분류”
  - context: “시니어 리빙 시설의 배상책임보험을 인수하는 심사팀.”

**AXV2C_0080_01**

> 실제 수행 업무: Extract fields from trade finance documents

- P02 연결 근거: 대량 무역문서의 수기 입력 부담에 대해 필드 추출을 수행함.
  - problem: “High-volume invoices and shipping forms require slow manual entry and are vulnerable to human errors.”
  - task: “Extract fields from trade finance documents”
  - context: “Hong Leong Bank trade operations, multilingual financial documents.”

**AXALL_US_OMB_2025_01754**

> 실제 수행 업무: Referral data structuring and completeness checks

- P02 연결 근거: 자유서술 자료의 수동·불일치 추적에 대해 데이터 구조화를 수행함.
  - problem: “Required referral information arrives as free text and is tracked manually and inconsistently, leaving missing fields to be checked.”
  - task: “Referral data structuring and completeness checks”
  - context: “HHS Office of Refugee Resettlement intake staff reviewing referral records from CBP.”

**AXV24_71def85d86bd**

> 실제 수행 업무: 의료기관의 보험 자격·보장 음성 문의 응대

- P04 연결 근거: 정형 자격·보장 문의의 상담원 쏠림으로 대기 부담이 있고 음성 문의에 응대함.
  - problem: “기존 IVR에서 다수의 정형적 자격·보장 문의가 상담원에게 넘어가 비용과 대기 부담이 커졌다.”
  - task: “의료기관의 보험 자격·보장 음성 문의 응대”
  - context: “의료기관 행정직원이 가입자의 보험 정보를 확인하는 보험사 서비스 운영.”

**AXV2H_0001_01**

> 실제 수행 업무: 고객 문의 자율응답

- P04 연결 근거: 대량 문의로 정시/영업외 대응 유지가 어려우며 문의 자율응답을 수행함.
  - problem: “하루 최대 600건의 문의로 소규모 지원팀이 정시와 영업시간 외 고객대응을 유지하기 어려움”
  - task: “고객 문의 자율응답”
  - context: “전자청구 SaaS 서비스의 대량 서면 문의와 야간 문의”

**AXV2P2_0060_01**

> 실제 수행 업무: Answer airline customer service questions

- P04 연결 근거: 대량 고객 문의가 지원조직을 압도하고 지연을 만들며 고객응대를 수행함.
  - problem: “Millions of customer questions overwhelmed airline support, increasing costs and response delays.”
  - task: “Answer airline customer service questions”
  - context: “Air India AI.g customer support”

**AXV24_df5d48fedff4**

> 실제 수행 업무: RV 고객 문의의 상시 응대 및 상담원 인계

- P04 연결 근거: 계절성 문의와 야간 공백으로 대기·누락이 생기며 상시 응대 및 인계 Task가 명시됨.
  - problem: “계절성 문의 증가와 야간 상담 공백으로 고객 대기가 길어지고 일부 문의가 누락됐다.”
  - task: “RV 고객 문의의 상시 응대 및 상담원 인계”
  - context: “여러 사업 부문의 웹·문자 채널에서 들어오는 고객지원 문의.”

## legacy_D13

> 상담 대화록을 세 문장으로 요약해주세요.

**출처:** 이전 실제 LLM 선택 응답; 예전 업무형 기준

**표시:** 관점 0개 / 관점별 표시 합계 0개 / 중복 제외 사례 0개

선택된 관점이 없어 사례를 억지로 채우지 않았다.

**목록 밖 요청:**

- “상담 대화록을 세 문장으로 요약해주세요.”: 단순 요약 요청은 제공된 4개 관점에 포함되지 않습니다.

### 중복을 합친 사례 상세 근거

## legacy_D14

> 다음 달 상품 수요를 예측해주세요.

**출처:** 이전 실제 LLM 선택 응답; 예전 업무형 기준

**표시:** 관점 0개 / 관점별 표시 합계 0개 / 중복 제외 사례 0개

선택된 관점이 없어 사례를 억지로 채우지 않았다.

**목록 밖 요청:**

- “다음 달 상품 수요를 예측해주세요.”: 수요 예측은 제공된 4개 관점에 포함되지 않는 목록 밖 요청입니다.

### 중복을 합친 사례 상세 근거

## legacy_D15

> 문서 처리를 잘하고 싶습니다.

**출처:** 이전 실제 LLM 선택 응답; 예전 업무형 기준

**표시:** 관점 0개 / 관점별 표시 합계 0개 / 중복 제외 사례 0개

선택된 관점이 없어 사례를 억지로 채우지 않았다.

### 중복을 합친 사례 상세 근거

## legacy_D16

> 이 청구서 내용이 맞는지 검증해주세요. 비교 기준이나 대조 자료는 아직 정하지 않았습니다.

**출처:** 이전 실제 LLM 선택 응답; 예전 업무형 기준

**표시:** 관점 0개 / 관점별 표시 합계 0개 / 중복 제외 사례 0개

선택된 관점이 없어 사례를 억지로 채우지 않았다.

**이전 선택기에 기록된 조건 — 적용 관점 미지정:**

- 비교 기준이나 대조 자료는 아직 정하지 않았습니다.

### 중복을 합친 사례 상세 근거

## legacy_D17

> 고객 문의에 답변하고 싶습니다. 대기나 응대 시간대에 관한 문제는 아직 제시하지 않았습니다.

**출처:** 이전 실제 LLM 선택 응답; 예전 업무형 기준

**표시:** 관점 0개 / 관점별 표시 합계 0개 / 중복 제외 사례 0개

선택된 관점이 없어 사례를 억지로 채우지 않았다.

### 중복을 합친 사례 상세 근거

## legacy_D18

> 과거에는 문서를 검색했습니다. 지금 필요한 것은 다음 달 수요 예측입니다.

**출처:** 이전 실제 LLM 선택 응답; 예전 업무형 기준

**표시:** 관점 0개 / 관점별 표시 합계 0개 / 중복 제외 사례 0개

선택된 관점이 없어 사례를 억지로 채우지 않았다.

**목록 밖 요청:**

- “지금 필요한 것은 다음 달 수요 예측입니다.”: 수요 예측은 제공된 4개 관점에 해당하지 않는 목록 밖 요청입니다.

### 중복을 합친 사례 상세 근거

## legacy_D19

> 청구서에서 항목을 추출하지 마세요. 이미 정리된 청구 금액을 계약 요율과 대조해주세요. 최종 수정은 담당자 승인 후에만 합니다.

**출처:** 이전 실제 LLM 선택 응답; 예전 업무형 기준

**표시:** 관점 1개 / 관점별 표시 합계 5개 / 중복 제외 사례 5개

### P03 업무 자료를 기준·다른 자료와 대조하는 검증 부담

**연결 유형:** 질문에 명시된 문제·업무

**질문 근거:** “대조해주세요”

정리된 청구 금액을 계약 요율이라는 기준과 대조하는 요청으로 P03의 포함 사례와 일치한다.

|순위|참고 사례|다른 연결 관점|
|---|---|---|
|1|AXV24_36c7ef329920 — 채용 지원서·증빙 자료 대조 검토|없음|
|2|AXALL_US_OMB_2025_01754 — Referral data structuring and completeness checks|없음|
|3|AXV2C_0006_02 — Validate customer order prices before invoicing|없음|
|4|AXV2H_0003_01 — 직원 신원조회 보고서 검증|없음|
|5|AXV2P2_0011_01 — Audit freight invoices for overcharges|없음|

**AXV24_36c7ef329920를 참고하는 이유:** 정리된 청구 금액을 계약 요율이라는 기준과 대조하는 요청으로 P03의 포함 사례와 일치한다. 이 사례에서 실제 확인된 업무: 지원서·증빙 자료 대조.

**차이·확인할 조건:**

- 지원자의 최종 합격판정과 별개
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXALL_US_OMB_2025_01754를 참고하는 이유:** 정리된 청구 금액을 계약 요율이라는 기준과 대조하는 요청으로 P03의 포함 사례와 일치한다. 이 사례에서 실제 확인된 업무: 필수항목 완전성 점검.

**차이·확인할 조건:**

- 구조화 자체는 P02, 내용 누락 확인은 P03의 별도 근거
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV2C_0006_02를 참고하는 이유:** 정리된 청구 금액을 계약 요율이라는 기준과 대조하는 요청으로 P03의 포함 사례와 일치한다. 이 사례에서 실제 확인된 업무: 고객 주문가격 검증.

**차이·확인할 조건:**

- 가격 자동변경·대금 지급 실행은 미확인
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV2H_0003_01를 참고하는 이유:** 정리된 청구 금액을 계약 요율이라는 기준과 대조하는 요청으로 P03의 포함 사례와 일치한다. 이 사례에서 실제 확인된 업무: 신원조회 보고서의 기준 대조 검증.

**차이·확인할 조건:**

- 채용 의사결정·신원 사실의 절대 보장으로 해석하지 않음
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV2P2_0011_01를 참고하는 이유:** 정리된 청구 금액을 계약 요율이라는 기준과 대조하는 요청으로 P03의 포함 사례와 일치한다. 이 사례에서 실제 확인된 업무: 청구서 과다청구 감사.

**차이·확인할 조건:**

- 환급·대금차감 자동 실행은 미확인
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**이전 선택기에 기록된 조건 — 적용 관점 미지정:**

- 청구서에서 항목을 추출하지 마세요.
- 최종 수정은 담당자 승인 후에만 합니다.

### 중복을 합친 사례 상세 근거

**AXV24_36c7ef329920**

> 실제 수행 업무: 채용 지원서·증빙 자료 대조 검토

- P03 연결 근거: 대량 지원서·증빙 검토의 인력 부담과 대조 검토 Task가 명시됨.
  - problem: “3주 안에 150만 건의 채용 지원서와 증빙을 검토해야 했으며 수작업 방식으로는 대규모 인력이 필요했다.”
  - task: “채용 지원서·증빙 자료 대조 검토”
  - context: “고객사의 대량 채용 서류 검토를 수행하는 BPO 기업의 운영 업무.”

**AXALL_US_OMB_2025_01754**

> 실제 수행 업무: Referral data structuring and completeness checks

- P03 연결 근거: 필수 의뢰항목 누락이 문제이고 Task에 완전성 점검이 명시됨.
  - problem: “Required referral information arrives as free text and is tracked manually and inconsistently, leaving missing fields to be checked.”
  - task: “Referral data structuring and completeness checks”
  - context: “HHS Office of Refugee Resettlement intake staff reviewing referral records from CBP.”

**AXV2C_0006_02**

> 실제 수행 업무: Validate customer order prices before invoicing

- P03 연결 근거: 주문가격 불일치·입력 오류 문제에 대해 청구 전 가격 검증을 수행함.
  - problem: “Orders in varied formats produced pricing inconsistencies and entry errors, followed by disputes and delayed payments.”
  - task: “Validate customer order prices before invoicing”
  - context: “Danone receives thousands of orders daily through email, PDF and EDI.”

**AXV2H_0003_01**

> 실제 수행 업무: 직원 신원조회 보고서 검증

- P03 연결 근거: 다수 파일과 검증기준을 수작업 대조하는 부담이 있고 보고서 검증을 수행함.
  - problem: “다수 파일과 검증 기준을 수작업 대조하면서 검증 지연과 준수 부담이 발생함”
  - task: “직원 신원조회 보고서 검증”
  - context: “업무별 검증 조건과 컴플라이언스 준수가 필수인 전문서비스”

**AXV2P2_0011_01**

> 실제 수행 업무: Audit freight invoices for overcharges

- P03 연결 근거: 운송 청구서와 약정요율 불일치를 확인하는 수기 부담과 감사 Task가 명시됨.
  - problem: “Freight invoices may not match negotiated rates and manual checking burdens logistics staff.”
  - task: “Audit freight invoices for overcharges”
  - context: “Dow logistics spending and emailed PDF invoices”

## legacy_D20

> 고객 문의가 많아 대기가 깁니다. 지금 요청하는 작업은 상담 대화록 요약뿐이고 고객 응대는 하지 않습니다.

**출처:** 이전 실제 LLM 선택 응답; 예전 업무형 기준

**표시:** 관점 0개 / 관점별 표시 합계 0개 / 중복 제외 사례 0개

선택된 관점이 없어 사례를 억지로 채우지 않았다.

**이전 선택기에 기록된 조건 — 적용 관점 미지정:**

- 고객 응대는 하지 않습니다

**목록 밖 요청:**

- “상담 대화록 요약”: 4개 관점에 단순 요약 작업이 없고 요약만 요청하는 경우는 제외 대상이다.

### 중복을 합친 사례 상세 근거

## legacy_R_IVQ010

> 온라인 쇼핑몰의 상품 상세 설명이 협력사마다 형식이 달라 검색과 비교가 어렵습니다. 협력사가 보낸 상품 정보 파일을 표준 항목으로 정리하고 누락 항목을 알려주는 작업 흐름이 필요합니다.

**출처:** 이전 실제 LLM 선택 응답; 예전 업무형 기준

**표시:** 관점 2개 / 관점별 표시 합계 10개 / 중복 제외 사례 9개

### P02 비정형 자료를 수기로 옮기고 업무 정보로 정리하는 부담

**연결 유형:** 질문에 명시된 문제·업무

**질문 근거:** “상품 정보 파일을 표준 항목으로 정리”

협력사의 형식이 다른 상품 정보 파일을 표준 항목으로 정리하려는 요청이며 P02 포함 사례와 일치합니다.

|순위|참고 사례|다른 연결 관점|
|---|---|---|
|1|AXALL_US_OMB_2025_01754 — Referral data structuring and completeness checks|P03|
|2|AXV24_98092b8ca357 — 상품 카탈로그 속성 추출·분류|없음|
|3|AXV2C_0080_01 — Extract fields from trade finance documents|없음|
|4|AXALL_US_OMB_2025_01589 — Loan document data extraction for examination analytics|없음|
|5|AXV24_28baf265c6cf — 보험 인수심사용 신청 서류 추출·분류|없음|

**AXALL_US_OMB_2025_01754를 참고하는 이유:** 협력사의 형식이 다른 상품 정보 파일을 표준 항목으로 정리하려는 요청이며 P02 포함 사례와 일치합니다. 이 사례에서 실제 확인된 업무: 의뢰 자료 데이터 구조화.

**차이·확인할 조건:**

- 필수항목 확인도 별도 명시되어 P03과 중복 연결하되 역할을 구분
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV24_98092b8ca357를 참고하는 이유:** 협력사의 형식이 다른 상품 정보 파일을 표준 항목으로 정리하려는 요청이며 P02 포함 사례와 일치합니다. 이 사례에서 실제 확인된 업무: 상품 속성 추출·분류.

**차이·확인할 조건:**

- 상품 검색·추천 기능 자체의 증거는 아님
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV2C_0080_01를 참고하는 이유:** 협력사의 형식이 다른 상품 정보 파일을 표준 항목으로 정리하려는 요청이며 P02 포함 사례와 일치합니다. 이 사례에서 실제 확인된 업무: 무역금융 문서 필드 추출.

**차이·확인할 조건:**

- 규제위험 판단·제재 심사로 확대하지 않음
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXALL_US_OMB_2025_01589를 참고하는 이유:** 협력사의 형식이 다른 상품 정보 파일을 표준 항목으로 정리하려는 요청이며 P02 포함 사례와 일치합니다. 이 사례에서 실제 확인된 업무: 대출 문서 데이터 추출.

**차이·확인할 조건:**

- 대출 승인·사실 확인까지 수행한다고 해석하지 않음
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV24_28baf265c6cf를 참고하는 이유:** 협력사의 형식이 다른 상품 정보 파일을 표준 항목으로 정리하려는 요청이며 P02 포함 사례와 일치합니다. 이 사례에서 실제 확인된 업무: 보험 신청 서류 추출·분류.

**차이·확인할 조건:**

- 최종 보험 인수 결정은 미확인
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

### P03 업무 자료를 기준·다른 자료와 대조하는 검증 부담

**연결 유형:** 질문에 명시된 문제·업무

**질문 근거:** “누락 항목을 알려주는 작업 흐름”

정리된 표준 항목을 기준으로 빠진 항목을 알려 달라는 누락 검사 요청입니다.

|순위|참고 사례|다른 연결 관점|
|---|---|---|
|1|AXV24_36c7ef329920 — 채용 지원서·증빙 자료 대조 검토|없음|
|2|AXALL_US_OMB_2025_01754 — Referral data structuring and completeness checks|P02|
|3|AXV2H_0003_01 — 직원 신원조회 보고서 검증|없음|
|4|AXV2C_0006_02 — Validate customer order prices before invoicing|없음|
|5|AXV2P2_0011_01 — Audit freight invoices for overcharges|없음|

**AXV24_36c7ef329920를 참고하는 이유:** 정리된 표준 항목을 기준으로 빠진 항목을 알려 달라는 누락 검사 요청입니다. 이 사례에서 실제 확인된 업무: 지원서·증빙 자료 대조.

**차이·확인할 조건:**

- 지원자의 최종 합격판정과 별개
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXALL_US_OMB_2025_01754를 참고하는 이유:** 정리된 표준 항목을 기준으로 빠진 항목을 알려 달라는 누락 검사 요청입니다. 이 사례에서 실제 확인된 업무: 필수항목 완전성 점검.

**차이·확인할 조건:**

- 구조화 자체는 P02, 내용 누락 확인은 P03의 별도 근거
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV2H_0003_01를 참고하는 이유:** 정리된 표준 항목을 기준으로 빠진 항목을 알려 달라는 누락 검사 요청입니다. 이 사례에서 실제 확인된 업무: 신원조회 보고서의 기준 대조 검증.

**차이·확인할 조건:**

- 채용 의사결정·신원 사실의 절대 보장으로 해석하지 않음
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV2C_0006_02를 참고하는 이유:** 정리된 표준 항목을 기준으로 빠진 항목을 알려 달라는 누락 검사 요청입니다. 이 사례에서 실제 확인된 업무: 고객 주문가격 검증.

**차이·확인할 조건:**

- 가격 자동변경·대금 지급 실행은 미확인
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV2P2_0011_01를 참고하는 이유:** 정리된 표준 항목을 기준으로 빠진 항목을 알려 달라는 누락 검사 요청입니다. 이 사례에서 실제 확인된 업무: 청구서 과다청구 감사.

**차이·확인할 조건:**

- 환급·대금차감 자동 실행은 미확인
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

### 중복을 합친 사례 상세 근거

**AXALL_US_OMB_2025_01754**

> 실제 수행 업무: Referral data structuring and completeness checks

- P02 연결 근거: 자유서술 자료의 수동·불일치 추적에 대해 데이터 구조화를 수행함.
  - problem: “Required referral information arrives as free text and is tracked manually and inconsistently, leaving missing fields to be checked.”
  - task: “Referral data structuring and completeness checks”
  - context: “HHS Office of Refugee Resettlement intake staff reviewing referral records from CBP.”
- P03 연결 근거: 필수 의뢰항목 누락이 문제이고 Task에 완전성 점검이 명시됨.
  - problem: “Required referral information arrives as free text and is tracked manually and inconsistently, leaving missing fields to be checked.”
  - task: “Referral data structuring and completeness checks”
  - context: “HHS Office of Refugee Resettlement intake staff reviewing referral records from CBP.”

**AXV24_98092b8ca357**

> 실제 수행 업무: 상품 카탈로그 속성 추출·분류

- P02 연결 근거: 카탈로그 세부정보의 수동 추출·정리 부담과 속성 추출·분류가 명시됨.
  - problem: “상품 등록 담당자가 카탈로그의 세부 정보를 수동으로 추출·정리하는 데 많은 시간을 사용했다.”
  - task: “상품 카탈로그 속성 추출·분류”
  - context: “가격 비교 서비스 다나와의 상품 메타데이터 운영.”

**AXV2C_0080_01**

> 실제 수행 업무: Extract fields from trade finance documents

- P02 연결 근거: 대량 무역문서의 수기 입력 부담에 대해 필드 추출을 수행함.
  - problem: “High-volume invoices and shipping forms require slow manual entry and are vulnerable to human errors.”
  - task: “Extract fields from trade finance documents”
  - context: “Hong Leong Bank trade operations, multilingual financial documents.”

**AXALL_US_OMB_2025_01589**

> 실제 수행 업무: Loan document data extraction for examination analytics

- P02 연결 근거: 신청 PDF의 수기 전사로 지연·오류가 생기며 문서 데이터 추출을 수행함.
  - problem: “Manual transcription from loan application PDFs causes delays, errors and staff costs in examination data collection.”
  - task: “Loan document data extraction for examination analytics”
  - context: “FDIC consumer protection personnel preparing loan data for compliance and fair lending reviews.”

**AXV24_28baf265c6cf**

> 실제 수행 업무: 보험 인수심사용 신청 서류 추출·분류

- P02 연결 근거: 형식이 다른 보험 자료를 수작업으로 추출하는 부담과 추출·분류 Task가 명시됨.
  - problem: “형식과 주기가 다른 보험 신청 자료에서 담당자가 직접 정보를 추출했으며, 증가하는 접수량을 수작업으로 처리하기 어려웠다.”
  - task: “보험 인수심사용 신청 서류 추출·분류”
  - context: “시니어 리빙 시설의 배상책임보험을 인수하는 심사팀.”

**AXV24_36c7ef329920**

> 실제 수행 업무: 채용 지원서·증빙 자료 대조 검토

- P03 연결 근거: 대량 지원서·증빙 검토의 인력 부담과 대조 검토 Task가 명시됨.
  - problem: “3주 안에 150만 건의 채용 지원서와 증빙을 검토해야 했으며 수작업 방식으로는 대규모 인력이 필요했다.”
  - task: “채용 지원서·증빙 자료 대조 검토”
  - context: “고객사의 대량 채용 서류 검토를 수행하는 BPO 기업의 운영 업무.”

**AXV2H_0003_01**

> 실제 수행 업무: 직원 신원조회 보고서 검증

- P03 연결 근거: 다수 파일과 검증기준을 수작업 대조하는 부담이 있고 보고서 검증을 수행함.
  - problem: “다수 파일과 검증 기준을 수작업 대조하면서 검증 지연과 준수 부담이 발생함”
  - task: “직원 신원조회 보고서 검증”
  - context: “업무별 검증 조건과 컴플라이언스 준수가 필수인 전문서비스”

**AXV2C_0006_02**

> 실제 수행 업무: Validate customer order prices before invoicing

- P03 연결 근거: 주문가격 불일치·입력 오류 문제에 대해 청구 전 가격 검증을 수행함.
  - problem: “Orders in varied formats produced pricing inconsistencies and entry errors, followed by disputes and delayed payments.”
  - task: “Validate customer order prices before invoicing”
  - context: “Danone receives thousands of orders daily through email, PDF and EDI.”

**AXV2P2_0011_01**

> 실제 수행 업무: Audit freight invoices for overcharges

- P03 연결 근거: 운송 청구서와 약정요율 불일치를 확인하는 수기 부담과 감사 Task가 명시됨.
  - problem: “Freight invoices may not match negotiated rates and manual checking burdens logistics staff.”
  - task: “Audit freight invoices for overcharges”
  - context: “Dow logistics spending and emailed PDF invoices”

## legacy_R_IVQ015

> 환불 정책이 자주 바뀌어 상담사마다 안내 내용이 다릅니다. 최신 정책 문서와 최근 한 달 문의 사례를 바탕으로 상담사가 자주 틀리는 안내 지점을 찾아 교육 자료 개선안을 만들고 싶습니다.

**출처:** 이전 실제 LLM 선택 응답; 예전 업무형 기준

**표시:** 관점 1개 / 관점별 표시 합계 5개 / 중복 제외 사례 5개

### P03 업무 자료를 기준·다른 자료와 대조하는 검증 부담

**연결 유형:** 질문에 명시된 문제·업무

**질문 근거:** “상담사가 자주 틀리는 안내 지점을 찾아”

최신 정책 문서를 기준으로 최근 문의 사례의 상담사 안내를 대조해 오류 지점을 확인하려는 요청입니다.

|순위|참고 사례|다른 연결 관점|
|---|---|---|
|1|AXV24_36c7ef329920 — 채용 지원서·증빙 자료 대조 검토|없음|
|2|AXALL_US_OMB_2025_01754 — Referral data structuring and completeness checks|없음|
|3|AXV2H_0003_01 — 직원 신원조회 보고서 검증|없음|
|4|AXV2C_0006_02 — Validate customer order prices before invoicing|없음|
|5|AXV2P2_0011_01 — Audit freight invoices for overcharges|없음|

**AXV24_36c7ef329920를 참고하는 이유:** 최신 정책 문서를 기준으로 최근 문의 사례의 상담사 안내를 대조해 오류 지점을 확인하려는 요청입니다. 이 사례에서 실제 확인된 업무: 지원서·증빙 자료 대조.

**차이·확인할 조건:**

- 지원자의 최종 합격판정과 별개
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXALL_US_OMB_2025_01754를 참고하는 이유:** 최신 정책 문서를 기준으로 최근 문의 사례의 상담사 안내를 대조해 오류 지점을 확인하려는 요청입니다. 이 사례에서 실제 확인된 업무: 필수항목 완전성 점검.

**차이·확인할 조건:**

- 구조화 자체는 P02, 내용 누락 확인은 P03의 별도 근거
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV2H_0003_01를 참고하는 이유:** 최신 정책 문서를 기준으로 최근 문의 사례의 상담사 안내를 대조해 오류 지점을 확인하려는 요청입니다. 이 사례에서 실제 확인된 업무: 신원조회 보고서의 기준 대조 검증.

**차이·확인할 조건:**

- 채용 의사결정·신원 사실의 절대 보장으로 해석하지 않음
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV2C_0006_02를 참고하는 이유:** 최신 정책 문서를 기준으로 최근 문의 사례의 상담사 안내를 대조해 오류 지점을 확인하려는 요청입니다. 이 사례에서 실제 확인된 업무: 고객 주문가격 검증.

**차이·확인할 조건:**

- 가격 자동변경·대금 지급 실행은 미확인
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV2P2_0011_01를 참고하는 이유:** 최신 정책 문서를 기준으로 최근 문의 사례의 상담사 안내를 대조해 오류 지점을 확인하려는 요청입니다. 이 사례에서 실제 확인된 업무: 청구서 과다청구 감사.

**차이·확인할 조건:**

- 환급·대금차감 자동 실행은 미확인
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**목록 밖 요청:**

- “교육 자료 개선안을 만들고 싶습니다”: 교육 자료 개선안 작성은 제공된 4개 관점에 포함되지 않는 별도 작업입니다.

### 중복을 합친 사례 상세 근거

**AXV24_36c7ef329920**

> 실제 수행 업무: 채용 지원서·증빙 자료 대조 검토

- P03 연결 근거: 대량 지원서·증빙 검토의 인력 부담과 대조 검토 Task가 명시됨.
  - problem: “3주 안에 150만 건의 채용 지원서와 증빙을 검토해야 했으며 수작업 방식으로는 대규모 인력이 필요했다.”
  - task: “채용 지원서·증빙 자료 대조 검토”
  - context: “고객사의 대량 채용 서류 검토를 수행하는 BPO 기업의 운영 업무.”

**AXALL_US_OMB_2025_01754**

> 실제 수행 업무: Referral data structuring and completeness checks

- P03 연결 근거: 필수 의뢰항목 누락이 문제이고 Task에 완전성 점검이 명시됨.
  - problem: “Required referral information arrives as free text and is tracked manually and inconsistently, leaving missing fields to be checked.”
  - task: “Referral data structuring and completeness checks”
  - context: “HHS Office of Refugee Resettlement intake staff reviewing referral records from CBP.”

**AXV2H_0003_01**

> 실제 수행 업무: 직원 신원조회 보고서 검증

- P03 연결 근거: 다수 파일과 검증기준을 수작업 대조하는 부담이 있고 보고서 검증을 수행함.
  - problem: “다수 파일과 검증 기준을 수작업 대조하면서 검증 지연과 준수 부담이 발생함”
  - task: “직원 신원조회 보고서 검증”
  - context: “업무별 검증 조건과 컴플라이언스 준수가 필수인 전문서비스”

**AXV2C_0006_02**

> 실제 수행 업무: Validate customer order prices before invoicing

- P03 연결 근거: 주문가격 불일치·입력 오류 문제에 대해 청구 전 가격 검증을 수행함.
  - problem: “Orders in varied formats produced pricing inconsistencies and entry errors, followed by disputes and delayed payments.”
  - task: “Validate customer order prices before invoicing”
  - context: “Danone receives thousands of orders daily through email, PDF and EDI.”

**AXV2P2_0011_01**

> 실제 수행 업무: Audit freight invoices for overcharges

- P03 연결 근거: 운송 청구서와 약정요율 불일치를 확인하는 수기 부담과 감사 Task가 명시됨.
  - problem: “Freight invoices may not match negotiated rates and manual checking burdens logistics staff.”
  - task: “Audit freight invoices for overcharges”
  - context: “Dow logistics spending and emailed PDF invoices”

## legacy_R_IVQ020

> 월말 결산에서 은행 입금 내역과 매출 장부의 대사가 맞지 않는 건이 많습니다. 두 데이터를 비교해 자동으로 맞춰지는 건과 사람이 봐야 할 건을 나누고 싶습니다.

**출처:** 이전 실제 LLM 선택 응답; 예전 업무형 기준

**표시:** 관점 1개 / 관점별 표시 합계 5개 / 중복 제외 사례 5개

### P03 업무 자료를 기준·다른 자료와 대조하는 검증 부담

**연결 유형:** 질문에 명시된 문제·업무

**질문 근거:** “두 데이터를 비교해 자동으로 맞춰지는 건과 사람이 봐야 할 건을 나누고 싶습니다”

은행 입금 내역과 매출 장부를 비교해 일치 건과 검토 대상 건을 나누려는 대조 요청이다.

|순위|참고 사례|다른 연결 관점|
|---|---|---|
|1|AXV24_36c7ef329920 — 채용 지원서·증빙 자료 대조 검토|없음|
|2|AXALL_US_OMB_2025_01754 — Referral data structuring and completeness checks|없음|
|3|AXV2H_0003_01 — 직원 신원조회 보고서 검증|없음|
|4|AXV2P2_0011_01 — Audit freight invoices for overcharges|없음|
|5|AXV2C_0006_02 — Validate customer order prices before invoicing|없음|

**AXV24_36c7ef329920를 참고하는 이유:** 은행 입금 내역과 매출 장부를 비교해 일치 건과 검토 대상 건을 나누려는 대조 요청이다. 이 사례에서 실제 확인된 업무: 지원서·증빙 자료 대조.

**차이·확인할 조건:**

- 지원자의 최종 합격판정과 별개
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXALL_US_OMB_2025_01754를 참고하는 이유:** 은행 입금 내역과 매출 장부를 비교해 일치 건과 검토 대상 건을 나누려는 대조 요청이다. 이 사례에서 실제 확인된 업무: 필수항목 완전성 점검.

**차이·확인할 조건:**

- 구조화 자체는 P02, 내용 누락 확인은 P03의 별도 근거
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV2H_0003_01를 참고하는 이유:** 은행 입금 내역과 매출 장부를 비교해 일치 건과 검토 대상 건을 나누려는 대조 요청이다. 이 사례에서 실제 확인된 업무: 신원조회 보고서의 기준 대조 검증.

**차이·확인할 조건:**

- 채용 의사결정·신원 사실의 절대 보장으로 해석하지 않음
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV2P2_0011_01를 참고하는 이유:** 은행 입금 내역과 매출 장부를 비교해 일치 건과 검토 대상 건을 나누려는 대조 요청이다. 이 사례에서 실제 확인된 업무: 청구서 과다청구 감사.

**차이·확인할 조건:**

- 환급·대금차감 자동 실행은 미확인
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV2C_0006_02를 참고하는 이유:** 은행 입금 내역과 매출 장부를 비교해 일치 건과 검토 대상 건을 나누려는 대조 요청이다. 이 사례에서 실제 확인된 업무: 고객 주문가격 검증.

**차이·확인할 조건:**

- 가격 자동변경·대금 지급 실행은 미확인
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**이전 선택기에 기록된 조건 — 적용 관점 미지정:**

- 사람이 봐야 할 건

### 중복을 합친 사례 상세 근거

**AXV24_36c7ef329920**

> 실제 수행 업무: 채용 지원서·증빙 자료 대조 검토

- P03 연결 근거: 대량 지원서·증빙 검토의 인력 부담과 대조 검토 Task가 명시됨.
  - problem: “3주 안에 150만 건의 채용 지원서와 증빙을 검토해야 했으며 수작업 방식으로는 대규모 인력이 필요했다.”
  - task: “채용 지원서·증빙 자료 대조 검토”
  - context: “고객사의 대량 채용 서류 검토를 수행하는 BPO 기업의 운영 업무.”

**AXALL_US_OMB_2025_01754**

> 실제 수행 업무: Referral data structuring and completeness checks

- P03 연결 근거: 필수 의뢰항목 누락이 문제이고 Task에 완전성 점검이 명시됨.
  - problem: “Required referral information arrives as free text and is tracked manually and inconsistently, leaving missing fields to be checked.”
  - task: “Referral data structuring and completeness checks”
  - context: “HHS Office of Refugee Resettlement intake staff reviewing referral records from CBP.”

**AXV2H_0003_01**

> 실제 수행 업무: 직원 신원조회 보고서 검증

- P03 연결 근거: 다수 파일과 검증기준을 수작업 대조하는 부담이 있고 보고서 검증을 수행함.
  - problem: “다수 파일과 검증 기준을 수작업 대조하면서 검증 지연과 준수 부담이 발생함”
  - task: “직원 신원조회 보고서 검증”
  - context: “업무별 검증 조건과 컴플라이언스 준수가 필수인 전문서비스”

**AXV2P2_0011_01**

> 실제 수행 업무: Audit freight invoices for overcharges

- P03 연결 근거: 운송 청구서와 약정요율 불일치를 확인하는 수기 부담과 감사 Task가 명시됨.
  - problem: “Freight invoices may not match negotiated rates and manual checking burdens logistics staff.”
  - task: “Audit freight invoices for overcharges”
  - context: “Dow logistics spending and emailed PDF invoices”

**AXV2C_0006_02**

> 실제 수행 업무: Validate customer order prices before invoicing

- P03 연결 근거: 주문가격 불일치·입력 오류 문제에 대해 청구 전 가격 검증을 수행함.
  - problem: “Orders in varied formats produced pricing inconsistencies and entry errors, followed by disputes and delayed payments.”
  - task: “Validate customer order prices before invoicing”
  - context: “Danone receives thousands of orders daily through email, PDF and EDI.”

## legacy_R_IVQ029

> 연 2회 채용 시즌마다 지원서 검토에 많은 시간이 듭니다. 직무 기준과 지원서의 경력 기재를 대조해 필수 요건 충족 여부를 정리하고, 판단이 애매한 지원서를 따로 표시하고 싶습니다.

**출처:** 이전 실제 LLM 선택 응답; 예전 업무형 기준

**표시:** 관점 1개 / 관점별 표시 합계 5개 / 중복 제외 사례 5개

### P03 업무 자료를 기준·다른 자료와 대조하는 검증 부담

**연결 유형:** 질문에 명시된 문제·업무

**질문 근거:** “직무 기준과 지원서의 경력 기재를 대조해 필수 요건 충족 여부를 정리하고”

지원서의 경력 기재를 직무 기준과 대조해 필수 요건 충족 여부를 정리하고 애매한 건을 표시하려는 요청입니다.

|순위|참고 사례|다른 연결 관점|
|---|---|---|
|1|AXV24_36c7ef329920 — 채용 지원서·증빙 자료 대조 검토|없음|
|2|AXV2H_0003_01 — 직원 신원조회 보고서 검증|없음|
|3|AXALL_US_OMB_2025_01754 — Referral data structuring and completeness checks|없음|
|4|AXV2P2_0011_01 — Audit freight invoices for overcharges|없음|
|5|AXV2C_0006_02 — Validate customer order prices before invoicing|없음|

**AXV24_36c7ef329920를 참고하는 이유:** 지원서의 경력 기재를 직무 기준과 대조해 필수 요건 충족 여부를 정리하고 애매한 건을 표시하려는 요청입니다. 이 사례에서 실제 확인된 업무: 지원서·증빙 자료 대조.

**차이·확인할 조건:**

- 지원자의 최종 합격판정과 별개
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV2H_0003_01를 참고하는 이유:** 지원서의 경력 기재를 직무 기준과 대조해 필수 요건 충족 여부를 정리하고 애매한 건을 표시하려는 요청입니다. 이 사례에서 실제 확인된 업무: 신원조회 보고서의 기준 대조 검증.

**차이·확인할 조건:**

- 채용 의사결정·신원 사실의 절대 보장으로 해석하지 않음
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXALL_US_OMB_2025_01754를 참고하는 이유:** 지원서의 경력 기재를 직무 기준과 대조해 필수 요건 충족 여부를 정리하고 애매한 건을 표시하려는 요청입니다. 이 사례에서 실제 확인된 업무: 필수항목 완전성 점검.

**차이·확인할 조건:**

- 구조화 자체는 P02, 내용 누락 확인은 P03의 별도 근거
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV2P2_0011_01를 참고하는 이유:** 지원서의 경력 기재를 직무 기준과 대조해 필수 요건 충족 여부를 정리하고 애매한 건을 표시하려는 요청입니다. 이 사례에서 실제 확인된 업무: 청구서 과다청구 감사.

**차이·확인할 조건:**

- 환급·대금차감 자동 실행은 미확인
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV2C_0006_02를 참고하는 이유:** 지원서의 경력 기재를 직무 기준과 대조해 필수 요건 충족 여부를 정리하고 애매한 건을 표시하려는 요청입니다. 이 사례에서 실제 확인된 업무: 고객 주문가격 검증.

**차이·확인할 조건:**

- 가격 자동변경·대금 지급 실행은 미확인
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

### 중복을 합친 사례 상세 근거

**AXV24_36c7ef329920**

> 실제 수행 업무: 채용 지원서·증빙 자료 대조 검토

- P03 연결 근거: 대량 지원서·증빙 검토의 인력 부담과 대조 검토 Task가 명시됨.
  - problem: “3주 안에 150만 건의 채용 지원서와 증빙을 검토해야 했으며 수작업 방식으로는 대규모 인력이 필요했다.”
  - task: “채용 지원서·증빙 자료 대조 검토”
  - context: “고객사의 대량 채용 서류 검토를 수행하는 BPO 기업의 운영 업무.”

**AXV2H_0003_01**

> 실제 수행 업무: 직원 신원조회 보고서 검증

- P03 연결 근거: 다수 파일과 검증기준을 수작업 대조하는 부담이 있고 보고서 검증을 수행함.
  - problem: “다수 파일과 검증 기준을 수작업 대조하면서 검증 지연과 준수 부담이 발생함”
  - task: “직원 신원조회 보고서 검증”
  - context: “업무별 검증 조건과 컴플라이언스 준수가 필수인 전문서비스”

**AXALL_US_OMB_2025_01754**

> 실제 수행 업무: Referral data structuring and completeness checks

- P03 연결 근거: 필수 의뢰항목 누락이 문제이고 Task에 완전성 점검이 명시됨.
  - problem: “Required referral information arrives as free text and is tracked manually and inconsistently, leaving missing fields to be checked.”
  - task: “Referral data structuring and completeness checks”
  - context: “HHS Office of Refugee Resettlement intake staff reviewing referral records from CBP.”

**AXV2P2_0011_01**

> 실제 수행 업무: Audit freight invoices for overcharges

- P03 연결 근거: 운송 청구서와 약정요율 불일치를 확인하는 수기 부담과 감사 Task가 명시됨.
  - problem: “Freight invoices may not match negotiated rates and manual checking burdens logistics staff.”
  - task: “Audit freight invoices for overcharges”
  - context: “Dow logistics spending and emailed PDF invoices”

**AXV2C_0006_02**

> 실제 수행 업무: Validate customer order prices before invoicing

- P03 연결 근거: 주문가격 불일치·입력 오류 문제에 대해 청구 전 가격 검증을 수행함.
  - problem: “Orders in varied formats produced pricing inconsistencies and entry errors, followed by disputes and delayed payments.”
  - task: “Validate customer order prices before invoicing”
  - context: “Danone receives thousands of orders daily through email, PDF and EDI.”

## legacy_D01_REVERSE

> 사내 규정에서 출장비 지급 기준과 원문 출처를 검색해주세요.

**출처:** 이전 실제 LLM 선택 응답; 예전 업무형 기준

**표시:** 관점 1개 / 관점별 표시 합계 3개 / 중복 제외 사례 3개

### P01 업무 지식이 길고 분산돼 필요한 근거를 찾는 데 시간이 걸림

**연결 유형:** 질문에 명시된 문제·업무

**질문 근거:** “출장비 지급 기준과 원문 출처를 검색해주세요”

사내 규정에서 출장비 지급 기준과 원문 출처를 찾는 기존 문서 검색 요청이다.

|순위|참고 사례|다른 연결 관점|
|---|---|---|
|1|AXALL_US_OMB_2025_02663 — Document retrieval and cross-reference support|없음|
|2|AXV2N_0110 — Retrieve internal knowledge for financial advisors|없음|
|3|AXV2P2_0010_01 — Retrieve CAD/CAM product support knowledge|없음|

**AXALL_US_OMB_2025_02663를 참고하는 이유:** 사내 규정에서 출장비 지급 기준과 원문 출처를 찾는 기존 문서 검색 요청이다. 이 사례에서 실제 확인된 업무: 문서 검색 및 교차참조 지원.

**차이·확인할 조건:**

- 정책 승인이나 규제 적합성 확정 기능까지 뜻하지 않음
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV2N_0110를 참고하는 이유:** 사내 규정에서 출장비 지급 기준과 원문 출처를 찾는 기존 문서 검색 요청이다. 이 사례에서 실제 확인된 업무: 내부 지식 검색.

**차이·확인할 조건:**

- 외부 고객의 금융판단 대행으로 확대하지 않음
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV2P2_0010_01를 참고하는 이유:** 사내 규정에서 출장비 지급 기준과 원문 출처를 찾는 기존 문서 검색 요청이다. 이 사례에서 실제 확인된 업무: CAD/CAM 지원지식 검색.

**차이·확인할 조건:**

- 제품 조작·설계 변경의 자동 실행은 미확인
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

### 중복을 합친 사례 상세 근거

**AXALL_US_OMB_2025_02663**

> 실제 수행 업무: Document retrieval and cross-reference support

- P01 연결 근거: 긴 문서·정책의 탐색 병목과 검색·교차참조 작업이 함께 명시됨.
  - problem: “Staff must search and cross-reference lengthy documents and policies, creating a time-consuming information bottleneck.”
  - task: “Document retrieval and cross-reference support”
  - context: “Nuclear Regulatory Commission staff supporting licensing and oversight work.”

**AXV2N_0110**

> 실제 수행 업무: Retrieve internal knowledge for financial advisors

- P01 연결 근거: 금융자문 직원의 내부문서 탐색 시간이 문제이고 지식 검색을 수행함.
  - problem: “Advisors spend hours searching a large internal document corpus.”
  - task: “Retrieve internal knowledge for financial advisors”
  - context: “Wealth management advisor teams using AI at Morgan Stanley Assistant.”

**AXV2P2_0010_01**

> 실제 수행 업무: Retrieve CAD/CAM product support knowledge

- P01 연결 근거: 접근하기 어려운 제품 전문지식을 검색하는 작업이 명시됨.
  - problem: “Complex manufacturing product knowledge is difficult to access as expertise and skills become scarce.”
  - task: “Retrieve CAD/CAM product support knowledge”
  - context: “Sandvik manufacturing software support teams and customers”

## legacy_D03_REVERSE

> PDF 청구서에서 고객명과 청구 금액을 추출해주세요.

**출처:** 이전 실제 LLM 선택 응답; 예전 업무형 기준

**표시:** 관점 1개 / 관점별 표시 합계 5개 / 중복 제외 사례 5개

### P02 비정형 자료를 수기로 옮기고 업무 정보로 정리하는 부담

**연결 유형:** 질문에 명시된 문제·업무

**질문 근거:** “고객명과 청구 금액을 추출해주세요”

PDF 청구서 원자료에서 고객명과 청구 금액을 꺼내려는 추출 요청입니다.

|순위|참고 사례|다른 연결 관점|
|---|---|---|
|1|AXV24_bc6444cc1b61 — 단체 의료보험 견적용 청구서 정보 추출|없음|
|2|AXALL_US_OMB_2025_01589 — Loan document data extraction for examination analytics|없음|
|3|AXV2C_0080_01 — Extract fields from trade finance documents|없음|
|4|AXV24_28baf265c6cf — 보험 인수심사용 신청 서류 추출·분류|없음|
|5|AXALL_US_OMB_2025_01754 — Referral data structuring and completeness checks|없음|

**AXV24_bc6444cc1b61를 참고하는 이유:** PDF 청구서 원자료에서 고객명과 청구 금액을 꺼내려는 추출 요청입니다. 이 사례에서 실제 확인된 업무: 견적용 청구서 정보 추출.

**차이·확인할 조건:**

- 보험 견적 산정이나 심사 판단 자체는 미확인
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXALL_US_OMB_2025_01589를 참고하는 이유:** PDF 청구서 원자료에서 고객명과 청구 금액을 꺼내려는 추출 요청입니다. 이 사례에서 실제 확인된 업무: 대출 문서 데이터 추출.

**차이·확인할 조건:**

- 대출 승인·사실 확인까지 수행한다고 해석하지 않음
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV2C_0080_01를 참고하는 이유:** PDF 청구서 원자료에서 고객명과 청구 금액을 꺼내려는 추출 요청입니다. 이 사례에서 실제 확인된 업무: 무역금융 문서 필드 추출.

**차이·확인할 조건:**

- 규제위험 판단·제재 심사로 확대하지 않음
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV24_28baf265c6cf를 참고하는 이유:** PDF 청구서 원자료에서 고객명과 청구 금액을 꺼내려는 추출 요청입니다. 이 사례에서 실제 확인된 업무: 보험 신청 서류 추출·분류.

**차이·확인할 조건:**

- 최종 보험 인수 결정은 미확인
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXALL_US_OMB_2025_01754를 참고하는 이유:** PDF 청구서 원자료에서 고객명과 청구 금액을 꺼내려는 추출 요청입니다. 이 사례에서 실제 확인된 업무: 의뢰 자료 데이터 구조화.

**차이·확인할 조건:**

- 필수항목 확인도 별도 명시되어 P03과 중복 연결하되 역할을 구분
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

### 중복을 합친 사례 상세 근거

**AXV24_bc6444cc1b61**

> 실제 수행 업무: 단체 의료보험 견적용 청구서 정보 추출

- P02 연결 근거: 다양한 청구서 PDF에서 가입자 정보를 수동 복사하는 부담과 추출 Task가 일치함.
  - problem: “보험 견적을 위해 다양한 청구서 PDF에서 가입자 정보를 수동 복사했으며, 인력 증가 없이 견적 물량이 늘었다.”
  - task: “단체 의료보험 견적용 청구서 정보 추출”
  - context: “18명의 보험심사자가 다양한 보험사 청구서를 처리하는 단체보험 견적 업무.”

**AXALL_US_OMB_2025_01589**

> 실제 수행 업무: Loan document data extraction for examination analytics

- P02 연결 근거: 신청 PDF의 수기 전사로 지연·오류가 생기며 문서 데이터 추출을 수행함.
  - problem: “Manual transcription from loan application PDFs causes delays, errors and staff costs in examination data collection.”
  - task: “Loan document data extraction for examination analytics”
  - context: “FDIC consumer protection personnel preparing loan data for compliance and fair lending reviews.”

**AXV2C_0080_01**

> 실제 수행 업무: Extract fields from trade finance documents

- P02 연결 근거: 대량 무역문서의 수기 입력 부담에 대해 필드 추출을 수행함.
  - problem: “High-volume invoices and shipping forms require slow manual entry and are vulnerable to human errors.”
  - task: “Extract fields from trade finance documents”
  - context: “Hong Leong Bank trade operations, multilingual financial documents.”

**AXV24_28baf265c6cf**

> 실제 수행 업무: 보험 인수심사용 신청 서류 추출·분류

- P02 연결 근거: 형식이 다른 보험 자료를 수작업으로 추출하는 부담과 추출·분류 Task가 명시됨.
  - problem: “형식과 주기가 다른 보험 신청 자료에서 담당자가 직접 정보를 추출했으며, 증가하는 접수량을 수작업으로 처리하기 어려웠다.”
  - task: “보험 인수심사용 신청 서류 추출·분류”
  - context: “시니어 리빙 시설의 배상책임보험을 인수하는 심사팀.”

**AXALL_US_OMB_2025_01754**

> 실제 수행 업무: Referral data structuring and completeness checks

- P02 연결 근거: 자유서술 자료의 수동·불일치 추적에 대해 데이터 구조화를 수행함.
  - problem: “Required referral information arrives as free text and is tracked manually and inconsistently, leaving missing fields to be checked.”
  - task: “Referral data structuring and completeness checks”
  - context: “HHS Office of Refugee Resettlement intake staff reviewing referral records from CBP.”

## legacy_D05_REVERSE

> 청구서 금액을 계약 요율로 계산한 금액과 대조해 다른 항목을 알려주세요.

**출처:** 이전 실제 LLM 선택 응답; 예전 업무형 기준

**표시:** 관점 1개 / 관점별 표시 합계 5개 / 중복 제외 사례 5개

### P03 업무 자료를 기준·다른 자료와 대조하는 검증 부담

**연결 유형:** 질문에 명시된 문제·업무

**질문 근거:** “대조해 다른 항목을 알려주세요”

청구서 금액을 계약 요율 기준 계산 금액과 대조해 불일치 항목을 확인하려는 요청입니다.

|순위|참고 사례|다른 연결 관점|
|---|---|---|
|1|AXV24_36c7ef329920 — 채용 지원서·증빙 자료 대조 검토|없음|
|2|AXV2C_0006_02 — Validate customer order prices before invoicing|없음|
|3|AXALL_US_OMB_2025_01754 — Referral data structuring and completeness checks|없음|
|4|AXV2H_0003_01 — 직원 신원조회 보고서 검증|없음|
|5|AXV2P2_0011_01 — Audit freight invoices for overcharges|없음|

**AXV24_36c7ef329920를 참고하는 이유:** 청구서 금액을 계약 요율 기준 계산 금액과 대조해 불일치 항목을 확인하려는 요청입니다. 이 사례에서 실제 확인된 업무: 지원서·증빙 자료 대조.

**차이·확인할 조건:**

- 지원자의 최종 합격판정과 별개
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV2C_0006_02를 참고하는 이유:** 청구서 금액을 계약 요율 기준 계산 금액과 대조해 불일치 항목을 확인하려는 요청입니다. 이 사례에서 실제 확인된 업무: 고객 주문가격 검증.

**차이·확인할 조건:**

- 가격 자동변경·대금 지급 실행은 미확인
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXALL_US_OMB_2025_01754를 참고하는 이유:** 청구서 금액을 계약 요율 기준 계산 금액과 대조해 불일치 항목을 확인하려는 요청입니다. 이 사례에서 실제 확인된 업무: 필수항목 완전성 점검.

**차이·확인할 조건:**

- 구조화 자체는 P02, 내용 누락 확인은 P03의 별도 근거
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV2H_0003_01를 참고하는 이유:** 청구서 금액을 계약 요율 기준 계산 금액과 대조해 불일치 항목을 확인하려는 요청입니다. 이 사례에서 실제 확인된 업무: 신원조회 보고서의 기준 대조 검증.

**차이·확인할 조건:**

- 채용 의사결정·신원 사실의 절대 보장으로 해석하지 않음
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV2P2_0011_01를 참고하는 이유:** 청구서 금액을 계약 요율 기준 계산 금액과 대조해 불일치 항목을 확인하려는 요청입니다. 이 사례에서 실제 확인된 업무: 청구서 과다청구 감사.

**차이·확인할 조건:**

- 환급·대금차감 자동 실행은 미확인
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

### 중복을 합친 사례 상세 근거

**AXV24_36c7ef329920**

> 실제 수행 업무: 채용 지원서·증빙 자료 대조 검토

- P03 연결 근거: 대량 지원서·증빙 검토의 인력 부담과 대조 검토 Task가 명시됨.
  - problem: “3주 안에 150만 건의 채용 지원서와 증빙을 검토해야 했으며 수작업 방식으로는 대규모 인력이 필요했다.”
  - task: “채용 지원서·증빙 자료 대조 검토”
  - context: “고객사의 대량 채용 서류 검토를 수행하는 BPO 기업의 운영 업무.”

**AXV2C_0006_02**

> 실제 수행 업무: Validate customer order prices before invoicing

- P03 연결 근거: 주문가격 불일치·입력 오류 문제에 대해 청구 전 가격 검증을 수행함.
  - problem: “Orders in varied formats produced pricing inconsistencies and entry errors, followed by disputes and delayed payments.”
  - task: “Validate customer order prices before invoicing”
  - context: “Danone receives thousands of orders daily through email, PDF and EDI.”

**AXALL_US_OMB_2025_01754**

> 실제 수행 업무: Referral data structuring and completeness checks

- P03 연결 근거: 필수 의뢰항목 누락이 문제이고 Task에 완전성 점검이 명시됨.
  - problem: “Required referral information arrives as free text and is tracked manually and inconsistently, leaving missing fields to be checked.”
  - task: “Referral data structuring and completeness checks”
  - context: “HHS Office of Refugee Resettlement intake staff reviewing referral records from CBP.”

**AXV2H_0003_01**

> 실제 수행 업무: 직원 신원조회 보고서 검증

- P03 연결 근거: 다수 파일과 검증기준을 수작업 대조하는 부담이 있고 보고서 검증을 수행함.
  - problem: “다수 파일과 검증 기준을 수작업 대조하면서 검증 지연과 준수 부담이 발생함”
  - task: “직원 신원조회 보고서 검증”
  - context: “업무별 검증 조건과 컴플라이언스 준수가 필수인 전문서비스”

**AXV2P2_0011_01**

> 실제 수행 업무: Audit freight invoices for overcharges

- P03 연결 근거: 운송 청구서와 약정요율 불일치를 확인하는 수기 부담과 감사 Task가 명시됨.
  - problem: “Freight invoices may not match negotiated rates and manual checking burdens logistics staff.”
  - task: “Audit freight invoices for overcharges”
  - context: “Dow logistics spending and emailed PDF invoices”

## legacy_D07_REVERSE

> 야간에 고객 문의가 누락됩니다. 이 시간에도 문의에 응답하고 싶습니다.

**출처:** 이전 실제 LLM 선택 응답; 예전 업무형 기준

**표시:** 관점 1개 / 관점별 표시 합계 4개 / 중복 제외 사례 4개

### P04 문의량·접수 시간대가 응대 가능 용량을 넘어 대기·누락이 생김

**연결 유형:** 질문에 명시된 문제·업무

**질문 근거:** “이 시간에도 문의에 응답하고 싶습니다”

야간 시간대에 고객 문의가 누락되어 이 시간에도 응답하려는 실제 응대 필요와 시간대 공백이 함께 있다.

|순위|참고 사례|다른 연결 관점|
|---|---|---|
|1|AXV2P2_0060_01 — Answer airline customer service questions|없음|
|2|AXV2H_0001_01 — 고객 문의 자율응답|없음|
|3|AXV24_71def85d86bd — 의료기관의 보험 자격·보장 음성 문의 응대|없음|
|4|AXV24_df5d48fedff4 — RV 고객 문의의 상시 응대 및 상담원 인계|없음|

**AXV2P2_0060_01를 참고하는 이유:** 야간 시간대에 고객 문의가 누락되어 이 시간에도 응답하려는 실제 응대 필요와 시간대 공백이 함께 있다. 이 사례에서 실제 확인된 업무: 항공 고객서비스 질문 응답.

**차이·확인할 조건:**

- 이 요약만으로 야간·모든 채널·예약변경 실행을 보장하지 않음
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV2H_0001_01를 참고하는 이유:** 야간 시간대에 고객 문의가 누락되어 이 시간에도 응답하려는 실제 응대 필요와 시간대 공백이 함께 있다. 이 사례에서 실제 확인된 업무: 서면 고객 문의 응답.

**차이·확인할 조건:**

- 음성이나 CRM변경 기능으로 확대하지 않음
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV24_71def85d86bd를 참고하는 이유:** 야간 시간대에 고객 문의가 누락되어 이 시간에도 응답하려는 실제 응대 필요와 시간대 공백이 함께 있다. 이 사례에서 실제 확인된 업무: 보험 자격·보장 음성 문의 응대.

**차이·확인할 조건:**

- 청구 승인·보험금 지급·24시간 지원은 이 요약에서 확정하지 않음
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

**AXV24_df5d48fedff4를 참고하는 이유:** 야간 시간대에 고객 문의가 누락되어 이 시간에도 응답하려는 실제 응대 필요와 시간대 공백이 함께 있다. 이 사례에서 실제 확인된 업무: 상시 문의 응대·상담원 인계.

**차이·확인할 조건:**

- 인계 자체는 명시됐지만 인계 시 맥락 손실 해결 효과까지 증명하지 않음
- 원출판물의 전체 구현 범위는 이번에 재검증하지 않음
- 다른 질문에 대한 관련성과 성능은 아직 평가하지 않음
- 자료 형식·세부 항목·채널·시간대·권한은 사례 원문에 확인된 범위만 알 수 있습니다.
- 관점별 참고 연결이며 질문 전체의 해결·직접 적용 가능성을 확정하지 않습니다.

### 중복을 합친 사례 상세 근거

**AXV2P2_0060_01**

> 실제 수행 업무: Answer airline customer service questions

- P04 연결 근거: 대량 고객 문의가 지원조직을 압도하고 지연을 만들며 고객응대를 수행함.
  - problem: “Millions of customer questions overwhelmed airline support, increasing costs and response delays.”
  - task: “Answer airline customer service questions”
  - context: “Air India AI.g customer support”

**AXV2H_0001_01**

> 실제 수행 업무: 고객 문의 자율응답

- P04 연결 근거: 대량 문의로 정시/영업외 대응 유지가 어려우며 문의 자율응답을 수행함.
  - problem: “하루 최대 600건의 문의로 소규모 지원팀이 정시와 영업시간 외 고객대응을 유지하기 어려움”
  - task: “고객 문의 자율응답”
  - context: “전자청구 SaaS 서비스의 대량 서면 문의와 야간 문의”

**AXV24_71def85d86bd**

> 실제 수행 업무: 의료기관의 보험 자격·보장 음성 문의 응대

- P04 연결 근거: 정형 자격·보장 문의의 상담원 쏠림으로 대기 부담이 있고 음성 문의에 응대함.
  - problem: “기존 IVR에서 다수의 정형적 자격·보장 문의가 상담원에게 넘어가 비용과 대기 부담이 커졌다.”
  - task: “의료기관의 보험 자격·보장 음성 문의 응대”
  - context: “의료기관 행정직원이 가입자의 보험 정보를 확인하는 보험사 서비스 운영.”

**AXV24_df5d48fedff4**

> 실제 수행 업무: RV 고객 문의의 상시 응대 및 상담원 인계

- P04 연결 근거: 계절성 문의와 야간 공백으로 대기·누락이 생기며 상시 응대 및 인계 Task가 명시됨.
  - problem: “계절성 문의 증가와 야간 상담 공백으로 고객 대기가 길어지고 일부 문의가 누락됐다.”
  - task: “RV 고객 문의의 상시 응대 및 상담원 인계”
  - context: “여러 사업 부문의 웹·문자 채널에서 들어오는 고객지원 문의.”
