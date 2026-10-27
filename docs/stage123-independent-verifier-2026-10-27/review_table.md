# 검토용 기준표20개 (AI 작성, 사람 검증 없음)

모든 행은 사람 최종 검토가 필요하다. 예상 점수는 모델에게 제공하지 않으며 독립 정확도 정답이 아니다.

## 1. V21D001 / WHOLE_QUERY / AXV2C_0016_01
유형: DIRECT; 검토용 예상: 3-4; 사람 검토 필요: 예

고객 문의가 빠르게 늘면서 상담 인력이 반복 질문 처리에 대부분의 시간을 쓰고 있어 복잡한 문제 대응이 늦어지고 답변 품질도 일정하게 유지하기 어렵다.

관점 요구: {'ANSWER_INQUIRY': 'Answer or resolve inquiries: questions from a service user -> usable answer or resolution. Internal employees, partners, consumers and specialist question domains are functionally transferable; sector, recipient role and voice/text channel alone do not make this partial. Shopping questions are questions too. A single specific inquiry type can match one core task; no requirement to cover every FAQ. Pure document extraction, summarization, case administration, transaction execution and manual processing without answering inquiries are NOT this operation.'}

원문 Problem: Customers need digital or voice support that can diagnose routine device issues without unnecessary transfers.
원문 Task: Caller self-service computer troubleshooting
원문 Context: Best Buy customers calling for computer assistance.

검토 이유: 상담 기능은 컴퓨터 문제 해결에도 응용 가능

## 2. V21D001 / WHOLE_QUERY / AXV2P2_0048_01
유형: DIRECT; 검토용 예상: 3; 사람 검토 필요: 예

고객 문의가 빠르게 늘면서 상담 인력이 반복 질문 처리에 대부분의 시간을 쓰고 있어 복잡한 문제 대응이 늦어지고 답변 품질도 일정하게 유지하기 어렵다.

관점 요구: {'ANSWER_INQUIRY': 'Answer or resolve inquiries: questions from a service user -> usable answer or resolution. Internal employees, partners, consumers and specialist question domains are functionally transferable; sector, recipient role and voice/text channel alone do not make this partial. Shopping questions are questions too. A single specific inquiry type can match one core task; no requirement to cover every FAQ. Pure document extraction, summarization, case administration, transaction execution and manual processing without answering inquiries are NOT this operation.'}

원문 Problem: 고객이 수많은 상품 정보·리뷰·비교 결과를 직접 종합해야 해 특정 용도에 적합한 상품을 맥락에 맞춰 선택하기 어렵다.
원문 Task: Answer shopping questions and recommend products
원문 Context: Walmart app Ask Sparky button launched across categories in June 2025

검토 이유: 다른 업종 질문응답은 직접 관련; 추가 성과 추정 금지

## 3. V21D002 / WHOLE_QUERY / AXV2N_0125
유형: DIRECT; 검토용 예상: 3-4; 사람 검토 필요: 예

영업과 서비스 담당자가 긴 이메일 스레드와 첨부 문서를 일일이 읽고 핵심 내용과 후속 조치를 정리하는 데 많은 시간을 쓰고 있다.

관점 요구: {'SUMMARIZE_COMMUNICATION': 'Summarize business exchanges: email threads/attachments or functionally equivalent meeting/call conversations -> communication summary. Static contract, review or website summaries have a different functional object and are partial, not direct.', 'IDENTIFY_FOLLOWUP': 'Identify next actions from business exchanges -> explicit action items, next steps or follow-up list. Merely summarizing, extracting contact fields or administering an existing case is not identification of next actions.'}

원문 Problem: Sellers split attention between customers, notes and CRM updates.
원문 Task: Create sales-meeting recaps and next steps
원문 Context: Teams meetings with sales customers, distinct from email-signature contact creation.

검토 이유: 요약과 다음 단계가 수행문에 명시

## 4. V21D004 / WHOLE_QUERY / AXV2C_0006_02
유형: DIRECT; 검토용 예상: 3-4; 사람 검토 필요: 예

심사와 검증 업무에서 여러 형식의 문서를 사람이 읽고 필수 항목과 규정 준수 여부를 일일이 확인해야 해서 처리시간이 길고 누락이나 오류 위험도 높다.

관점 요구: {'VERIFY_DOCUMENT': 'Check documents or equivalent business records against required fields, reference evidence or rules -> validation findings, discrepancies or compliance judgment. Data extraction/classification alone is only a supporting operation. Physical defect detection has a different functional object; generic checking is insufficient.'}

원문 Problem: Orders in varied formats produced pricing inconsistencies and entry errors, followed by disputes and delayed payments.
원문 Task: Validate customer order prices before invoicing
원문 Context: Danone receives thousands of orders daily through email, PDF and EDI.

검토 이유: 문서 검증 기능의 대응을 확인

## 5. V21D010 / V21D010:CAUSE / AXV2P2_0065_01
유형: DIRECT; 검토용 예상: 3-4; 사람 검토 필요: 예

제조현장에서 생산·품질·설비 데이터가 여러 시스템에 나뉘어 있어 품질 이상이 발생했을 때 원인을 찾는 데 시간이 오래 걸리고, 주문이나 설비상태가 바뀔 때 생산계획을 다시 조정하는 일도 담당자의 수작업에 크게 의존하고 있다.

관점 요구: {'DIAGNOSE_QUALITY_CAUSE': 'Analyze reasons/drivers/root causes of quality defects -> causal diagnosis. Detecting that a defect is present is supporting inspection, NOT cause diagnosis. Survey theme summarization is not causal diagnosis.'}

원문 Problem: Fragmented paint-process data hide causes of bumper defects and delay countermeasures.
원문 Task: Investigate paint-quality defect drivers and support root-cause decisions
원문 Context: Toyota Industries Nagakusa Plant bumper production

검토 이유: 도장 품질 원인 분석은 원인 관점에 해당

## 6. V21D001 / WHOLE_QUERY / AXV2H_0002_01
유형: PARTIAL; 검토용 예상: 1-2; 사람 검토 필요: 예

고객 문의가 빠르게 늘면서 상담 인력이 반복 질문 처리에 대부분의 시간을 쓰고 있어 복잡한 문제 대응이 늦어지고 답변 품질도 일정하게 유지하기 어렵다.

관점 요구: {'ANSWER_INQUIRY': 'Answer or resolve inquiries: questions from a service user -> usable answer or resolution. Internal employees, partners, consumers and specialist question domains are functionally transferable; sector, recipient role and voice/text channel alone do not make this partial. Shopping questions are questions too. A single specific inquiry type can match one core task; no requirement to cover every FAQ. Pure document extraction, summarization, case administration, transaction execution and manual processing without answering inquiries are NOT this operation.'}

원문 Problem: 길고 복잡한 이메일 스레드의 핵심 내용 파악과 후속조치 확인에 시간이 소요됨
원문 Task: 고객 이메일 요약
원문 Context: 에너지기업 고객 커뮤니케이션 XRM의 장문 이메일

검토 이유: 고객 이메일 요약은 응답 자체와 구분

## 7. V21D001 / WHOLE_QUERY / AXV2N_0130
유형: PARTIAL; 검토용 예상: 1-2; 사람 검토 필요: 예

고객 문의가 빠르게 늘면서 상담 인력이 반복 질문 처리에 대부분의 시간을 쓰고 있어 복잡한 문제 대응이 늦어지고 답변 품질도 일정하게 유지하기 어렵다.

관점 요구: {'ANSWER_INQUIRY': 'Answer or resolve inquiries: questions from a service user -> usable answer or resolution. Internal employees, partners, consumers and specialist question domains are functionally transferable; sector, recipient role and voice/text channel alone do not make this partial. Shopping questions are questions too. A single specific inquiry type can match one core task; no requirement to cover every FAQ. Pure document extraction, summarization, case administration, transaction execution and manual processing without answering inquiries are NOT this operation.'}

원문 Problem: Follow-ups, status updates, closures and handoffs require repetitive engineer effort.
원문 Task: Automate routine support-case administration
원문 Context: Automate SW Support deployed to 2800 engineers worldwide.

검토 이유: 상담 행정은 직접 답변과 구분

## 8. V21D002 / WHOLE_QUERY / AXV2N_0139
유형: PARTIAL; 검토용 예상: 2-3; 사람 검토 필요: 예

영업과 서비스 담당자가 긴 이메일 스레드와 첨부 문서를 일일이 읽고 핵심 내용과 후속 조치를 정리하는 데 많은 시간을 쓰고 있다.

관점 요구: {'SUMMARIZE_COMMUNICATION': 'Summarize business exchanges: email threads/attachments or functionally equivalent meeting/call conversations -> communication summary. Static contract, review or website summaries have a different functional object and are partial, not direct.', 'IDENTIFY_FOLLOWUP': 'Identify next actions from business exchanges -> explicit action items, next steps or follow-up list. Merely summarizing, extracting contact fields or administering an existing case is not identification of next actions.'}

원문 Problem: Staff need understandable contract content without repeatedly interpreting legal text.
원문 Task: Summarize contracts for internal teams
원문 Context: Contract Companion GPT used within Moderna functions.

검토 이유: 문서 요약의 전이 범위는 사람 검토 필요

## 9. V21D004 / WHOLE_QUERY / AXV2P2_0012_01
유형: PARTIAL; 검토용 예상: 1-2; 사람 검토 필요: 예

심사와 검증 업무에서 여러 형식의 문서를 사람이 읽고 필수 항목과 규정 준수 여부를 일일이 확인해야 해서 처리시간이 길고 누락이나 오류 위험도 높다.

관점 요구: {'VERIFY_DOCUMENT': 'Check documents or equivalent business records against required fields, reference evidence or rules -> validation findings, discrepancies or compliance judgment. Data extraction/classification alone is only a supporting operation. Physical defect detection has a different functional object; generic checking is insufficient.'}

원문 Problem: Varied insurance documents require lengthy manual classification and extraction.
원문 Task: Extract and classify insurance documentation
원문 Context: Shift Technology's operational insurer document-processing platform

검토 이유: 보험 정보 추출은 검증의 보조 단계

## 10. V21D010 / WHOLE_QUERY / AXV2N_0117
유형: PARTIAL; 검토용 예상: 1-2; 사람 검토 필요: 예

제조현장에서 생산·품질·설비 데이터가 여러 시스템에 나뉘어 있어 품질 이상이 발생했을 때 원인을 찾는 데 시간이 오래 걸리고, 주문이나 설비상태가 바뀔 때 생산계획을 다시 조정하는 일도 담당자의 수작업에 크게 의존하고 있다.

관점 요구: {'INTEGRATE_PRODUCTION_DATA': 'Integrate fragmented production/quality/equipment or functionally equivalent operational process data -> unified operational data for diagnosis/planning.', 'DIAGNOSE_QUALITY_CAUSE': 'Analyze reasons/drivers/root causes of quality defects -> causal diagnosis. Detecting that a defect is present is supporting inspection, NOT cause diagnosis. Survey theme summarization is not causal diagnosis.', 'ADJUST_PRODUCTION_PLAN': 'Adjust operational production schedules when orders/equipment/constraints change -> revised schedule or validated schedule adjustments. Other sectors can transfer the same constrained scheduling operation. Generic initial planning without adjustment evidence is supporting.'}

원문 Problem: Manual underbody inspection must locate metal deposits that can damage cables.
원문 Task: Detect weld splatter on vehicle underbodies
원문 Context: Neckarsulm body shop series production as described in May 2025.

검토 이유: 불량 탐지는 원인 분석의 보조 단계

## 11. V21D001 / WHOLE_QUERY / AXV2N_0117
유형: UNRELATED; 검토용 예상: 0; 사람 검토 필요: 예

고객 문의가 빠르게 늘면서 상담 인력이 반복 질문 처리에 대부분의 시간을 쓰고 있어 복잡한 문제 대응이 늦어지고 답변 품질도 일정하게 유지하기 어렵다.

관점 요구: {'ANSWER_INQUIRY': 'Answer or resolve inquiries: questions from a service user -> usable answer or resolution. Internal employees, partners, consumers and specialist question domains are functionally transferable; sector, recipient role and voice/text channel alone do not make this partial. Shopping questions are questions too. A single specific inquiry type can match one core task; no requirement to cover every FAQ. Pure document extraction, summarization, case administration, transaction execution and manual processing without answering inquiries are NOT this operation.'}

원문 Problem: Manual underbody inspection must locate metal deposits that can damage cables.
원문 Task: Detect weld splatter on vehicle underbodies
원문 Context: Neckarsulm body shop series production as described in May 2025.

검토 이유: 용접 결함 탐지는 상담과 다름

## 12. V21D002 / WHOLE_QUERY / AXV2N_0118
유형: UNRELATED; 검토용 예상: 0; 사람 검토 필요: 예

영업과 서비스 담당자가 긴 이메일 스레드와 첨부 문서를 일일이 읽고 핵심 내용과 후속 조치를 정리하는 데 많은 시간을 쓰고 있다.

관점 요구: {'SUMMARIZE_COMMUNICATION': 'Summarize business exchanges: email threads/attachments or functionally equivalent meeting/call conversations -> communication summary. Static contract, review or website summaries have a different functional object and are partial, not direct.', 'IDENTIFY_FOLLOWUP': 'Identify next actions from business exchanges -> explicit action items, next steps or follow-up list. Merely summarizing, extracting contact fields or administering an existing case is not identification of next actions.'}

원문 Problem: Manual box unloading is strenuous and constrained by labor availability.
원문 Task: Unload cartons from trailers onto conveyors
원문 Context: First commercial Stretch deployment in January 2023.

검토 이유: 상자 하역은 이메일 요약과 다름

## 13. V21D004 / WHOLE_QUERY / AXV2N_0114
유형: UNRELATED; 검토용 예상: 0; 사람 검토 필요: 예

심사와 검증 업무에서 여러 형식의 문서를 사람이 읽고 필수 항목과 규정 준수 여부를 일일이 확인해야 해서 처리시간이 길고 누락이나 오류 위험도 높다.

관점 요구: {'VERIFY_DOCUMENT': 'Check documents or equivalent business records against required fields, reference evidence or rules -> validation findings, discrepancies or compliance judgment. Data extraction/classification alone is only a supporting operation. Physical defect detection has a different functional object; generic checking is insufficient.'}

원문 Problem: Photography and design costs delay localized creative production and limit testing variants.
원문 Task: Generate branded lifestyle advertising images
원문 Context: Operational UK/European advertising campaigns for pet products.

검토 이유: 광고 이미지 생성은 문서 검증과 다름

## 14. V21D010 / WHOLE_QUERY / AXV2N_0107
유형: UNRELATED; 검토용 예상: 0; 사람 검토 필요: 예

제조현장에서 생산·품질·설비 데이터가 여러 시스템에 나뉘어 있어 품질 이상이 발생했을 때 원인을 찾는 데 시간이 오래 걸리고, 주문이나 설비상태가 바뀔 때 생산계획을 다시 조정하는 일도 담당자의 수작업에 크게 의존하고 있다.

관점 요구: {'INTEGRATE_PRODUCTION_DATA': 'Integrate fragmented production/quality/equipment or functionally equivalent operational process data -> unified operational data for diagnosis/planning.', 'DIAGNOSE_QUALITY_CAUSE': 'Analyze reasons/drivers/root causes of quality defects -> causal diagnosis. Detecting that a defect is present is supporting inspection, NOT cause diagnosis. Survey theme summarization is not causal diagnosis.', 'ADJUST_PRODUCTION_PLAN': 'Adjust operational production schedules when orders/equipment/constraints change -> revised schedule or validated schedule adjustments. Other sectors can transfer the same constrained scheduling operation. Generic initial planning without adjustment evidence is supporting.'}

원문 Problem: Customers need advice and product recommendations expressed in terms of their project rather than a search keyword.
원문 Task: Give online home-improvement project advice
원문 Context: Magic Apron on Home Depot digital platforms.

검토 이유: 주거 개선 조언은 생산 원인·일정과 다름

## 15. V21D001 / V21D001:ANSWER / AXV2C_0093_01
유형: UNRELATED; 검토용 예상: 0; 사람 검토 필요: 예

고객 문의가 빠르게 늘면서 상담 인력이 반복 질문 처리에 대부분의 시간을 쓰고 있어 복잡한 문제 대응이 늦어지고 답변 품질도 일정하게 유지하기 어렵다.

관점 요구: {'ANSWER_INQUIRY': 'Answer or resolve inquiries: questions from a service user -> usable answer or resolution. Internal employees, partners, consumers and specialist question domains are functionally transferable; sector, recipient role and voice/text channel alone do not make this partial. Shopping questions are questions too. A single specific inquiry type can match one core task; no requirement to cover every FAQ. Pure document extraction, summarization, case administration, transaction execution and manual processing without answering inquiries are NOT this operation.'}

원문 Problem: Scattered production and quality data and manual analysis delay identification of quality issues.
원문 Task: Analyze production quality defects and root causes
원문 Context: Suzhou Universal MES, ERP and quality systems.

검토 이유: 생산 분석은 고객 응답과 다름

## 16. V21D010 / V21D010:INTEGRATION / AXV2C_0093_01
유형: CONFUSABLE; 검토용 예상: 0-2; 사람 검토 필요: 예

제조현장에서 생산·품질·설비 데이터가 여러 시스템에 나뉘어 있어 품질 이상이 발생했을 때 원인을 찾는 데 시간이 오래 걸리고, 주문이나 설비상태가 바뀔 때 생산계획을 다시 조정하는 일도 담당자의 수작업에 크게 의존하고 있다.

관점 요구: {'INTEGRATE_PRODUCTION_DATA': 'Integrate fragmented production/quality/equipment or functionally equivalent operational process data -> unified operational data for diagnosis/planning.'}

원문 Problem: Scattered production and quality data and manual analysis delay identification of quality issues.
원문 Task: Analyze production quality defects and root causes
원문 Context: Suzhou Universal MES, ERP and quality systems.

검토 이유: 원인 분석을 데이터 통합으로 승인하지 않음

## 17. V21D001 / WHOLE_QUERY / AXV24_bc6444cc1b61
유형: CONFUSABLE; 검토용 예상: 0-2; 사람 검토 필요: 예

고객 문의가 빠르게 늘면서 상담 인력이 반복 질문 처리에 대부분의 시간을 쓰고 있어 복잡한 문제 대응이 늦어지고 답변 품질도 일정하게 유지하기 어렵다.

관점 요구: {'ANSWER_INQUIRY': 'Answer or resolve inquiries: questions from a service user -> usable answer or resolution. Internal employees, partners, consumers and specialist question domains are functionally transferable; sector, recipient role and voice/text channel alone do not make this partial. Shopping questions are questions too. A single specific inquiry type can match one core task; no requirement to cover every FAQ. Pure document extraction, summarization, case administration, transaction execution and manual processing without answering inquiries are NOT this operation.'}

원문 Problem: 보험 견적을 위해 다양한 청구서 PDF에서 가입자 정보를 수동 복사했으며, 인력 증가 없이 견적 물량이 늘었다.
원문 Task: 단체 의료보험 견적용 청구서 정보 추출
원문 Context: 18명의 보험심사자가 다양한 보험사 청구서를 처리하는 단체보험 견적 업무.

검토 이유: 보험 견적 추출을 고객 응답으로 승인하지 않음

## 18. V21D002 / V21D002:FOLLOWUP / AXV2H_0002_01
유형: CONFUSABLE; 검토용 예상: 1-2; 사람 검토 필요: 예

영업과 서비스 담당자가 긴 이메일 스레드와 첨부 문서를 일일이 읽고 핵심 내용과 후속 조치를 정리하는 데 많은 시간을 쓰고 있다.

관점 요구: {'IDENTIFY_FOLLOWUP': 'Identify next actions from business exchanges -> explicit action items, next steps or follow-up list. Merely summarizing, extracting contact fields or administering an existing case is not identification of next actions.'}

원문 Problem: 길고 복잡한 이메일 스레드의 핵심 내용 파악과 후속조치 확인에 시간이 소요됨
원문 Task: 고객 이메일 요약
원문 Context: 에너지기업 고객 커뮤니케이션 XRM의 장문 이메일

검토 이유: 요약을 후속조치 식별로 승인하지 않음

## 19. V21D010 / V21D010:CAUSE / AXV2C_0093_02
유형: CONFUSABLE; 검토용 예상: 0-2; 사람 검토 필요: 예

제조현장에서 생산·품질·설비 데이터가 여러 시스템에 나뉘어 있어 품질 이상이 발생했을 때 원인을 찾는 데 시간이 오래 걸리고, 주문이나 설비상태가 바뀔 때 생산계획을 다시 조정하는 일도 담당자의 수작업에 크게 의존하고 있다.

관점 요구: {'DIAGNOSE_QUALITY_CAUSE': 'Analyze reasons/drivers/root causes of quality defects -> causal diagnosis. Detecting that a defect is present is supporting inspection, NOT cause diagnosis. Survey theme summarization is not causal diagnosis.'}

원문 Problem: Schedule changes were slow and error-prone across fragmented manufacturing systems.
원문 Task: Adjust production schedules with validation
원문 Context: Suzhou Universal scheduling teams and APS plans.

검토 이유: 일정 조정은 불량 원인 분석과 다름

## 20. V21D001 / V21D001:ANSWER / AXV2P2_0048_01
유형: CONFUSABLE; 검토용 예상: 3; 사람 검토 필요: 예

고객 문의가 빠르게 늘면서 상담 인력이 반복 질문 처리에 대부분의 시간을 쓰고 있어 복잡한 문제 대응이 늦어지고 답변 품질도 일정하게 유지하기 어렵다.

관점 요구: {'ANSWER_INQUIRY': 'Answer or resolve inquiries: questions from a service user -> usable answer or resolution. Internal employees, partners, consumers and specialist question domains are functionally transferable; sector, recipient role and voice/text channel alone do not make this partial. Shopping questions are questions too. A single specific inquiry type can match one core task; no requirement to cover every FAQ. Pure document extraction, summarization, case administration, transaction execution and manual processing without answering inquiries are NOT this operation.'}

원문 Problem: 고객이 수많은 상품 정보·리뷰·비교 결과를 직접 종합해야 해 특정 용도에 적합한 상품을 맥락에 맞춰 선택하기 어렵다.
원문 Task: Answer shopping questions and recommend products
원문 Context: Walmart app Ask Sparky button launched across categories in June 2025

검토 이유: 질문응답 관련성 인정; 근거 없는 추가 성과로4점 금지
