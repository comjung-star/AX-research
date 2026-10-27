# v2 source re-label pilot — ten specific business workflows (2026-10-22)

**STATUS: ONE-PASS SOURCE-CHECKED, NOT V2 FROZEN / NOT SECOND-REVIEWER APPROVED.**

`data/v2/source_relabel_pilot_v2.csv` reconstructs 10 candidate business workflow units from public original-source text, retaining v1 parent lineage but writing new single-workflow Problem/Task/Context and Solution fields. It classifies primary and secondary Factor and Strategy **as hypotheses justified by separate Problem/Solution original content**. All proposed direct Factor→Strategy relations remain `NOT_ESTABLISHED` pending passage-level explicit alignment, and second-reviewer approval is `NO`.

Rebuilt single-workflow parents: AX0001, AX0002, AX0003, AX0004, AX0008, AX0009, AX0021, AX0027, AX0075, AX0081. These are part of the 75 parent candidates, not extra new approved data points. As a strict anti-leakage practice, root factors were reasoned from Problem/Task/Context; implemented strategies from solution text. All source titles and section locator keywords accompany the rows.

## Important corrected interpretations

- **AX0004 / Orion Health**: 500k+ internal records retrieved under one minute is a presented capability. **The 50 staff hours per day saving is explicitly framed as *expected* in the source Outcome section**. The original v1 record already uses an expectation qualifier, so do NOT transform it into measured realized savings.
- **AX0021 / Hyundai–MakinaRocks**: source reports model predictions up to five days in advance with 90%+ accuracy; the broad 1,400-robot footprint is described as a **phased rollout**, not evidence all 1,400 robots are in production on that date.
- **AX0003 / Genpact**: AWS story also mentions a separate general GenAI Playground platform. Our unit contains **background-check report validation only**.
- **AX0081 / Starling**: Google story includes Scam Intelligence, Spending Intelligence and customer-service knowledge assistant as **other distinct workflows**. Only customer call transcript summarization and its monthly 8,000-hour saving are carried into this row.
- **AX0009 / Worten**: source includes earlier estimated search workload and claimed benefit; preserve vendor attribution and avoid presenting it as a separate independent study.
- **AX0075 / Chime**: source reports over 250k annual hours from customer call summarization, separate from overall customer satisfaction metrics.
- No second reviewer; no frozen v2 case IDs; no downstream retrieval/Wald retraining on these entries yet.

Next requirement: expand this exact workflow-level original evidence reconstruction from 10 to all remaining candidates and split children, adjudicate any unsupported or ambiguous labels, then freeze an independent verified v2 corpus.

## 2026-10-22 추가 원천자료 직접 대조 — 14건

- 추가 원천 대조: AX0070, AX0071, AX0072, AX0078, AX0079, AX0083, AX0084, AX0085, AX0086, AX0087, AX0090, AX0091, AX0095, AX0096. 기존 10건과 합계 **24개 부모 사례**를 소스 기반으로 다시 기술했으며 2차 독립 승인은 여전히 0건이다.
- **AX0070 DoorDash**: '하루 수십만 건'은 기존 콜센터 문의량이지 신설 GenAI 솔루션의 실제 처리량이 아님. AWS는 생산 A/B 테스트 적합 구조와 2.5초 지연·개발시간 50% 감소를 제시한다.
- **AX0071 BPC**: 소스 기사에는 기술지원 RAG 챗봇과 Amazon Q Developer 개발 코드 보조가 동시에 나오지만 본 Case는 **고객 기술지원 RAG만** 다룬다. 코드 4천 줄/수용률 46%와 66% 챗봇 모델 비용 절감치를 합쳐선 안 된다.
- **AX0072 BDM**: 범산업 공급사 제품소개보다 **브라질 금융기관의 법인계좌 개설 및 신용 서류심사 업무**를 실제 한 업무 단위로 좁히고, 원문 해당 현장의 운영노력 40% 절감 주장만 귀속. 일반 LOUIS 플랫폼 속도 85%/정확도 98%는 별도.
- **AX0079 Wayfair**: Gemini 제품속성 태깅 3천만 개/67%는 단일 업무 근거. 고객 시각 디자인 제품 Muse 파일럿·상거래 표준프로토콜은 별도 업무. 속성 분류는 현행 S3/S4 taxonomy와 의미 경계가 애매해 사전 점검 필요.
- **AX0083 Gelato**: 버그 티켓 분류/라우팅 주당 120시간 절감·정확도 60→90이 단일 업무 KPI. Vertex AI MLOps 배포기간 축소는 다른 개선 활동.
- **AX0084 Morrisons**: Product Finder의 5만 회/일 사용 실적은 유지 가능하나, BigQuery/Looker 98.96% 보고 지연 절감·ML 수요 예측은 해당 상품 위치 검색 작업과 구별.
- **AX0085 Lloyds**: 모기지 소득검증 수일→수초 단일업무 KPI와 전사 ML 플랫폼 탄소배출 감축/다운타임 0은 별도.
- **AX0087 Black Eyewear**: 실제 생성형 이미지 *virtual try-on*. 현행 S5 최적화는 사용한 AI 기술과 맞지 않아 **UNMAPPED_GENERATIVE_IMAGE_TAXONOMY_GAP**으로 임시 보류. 기존 분류에 억지로 맞추지 않음.
- **AX0090 AskHR**: HR 헬프데스크는 통합 서비스이므로 현재 1건 유지 가능. 연속 4년 운영비 절감/2016년 이후 티켓 감소/2025 agentic 업데이트를 같은 시점 효과로 환산하면 안 됨.
- **AX0091 IBM Software Support**: 실제 4개월 사례당 평균 10분 절감은 유지. '연 1만 7천 시간'은 응답 가정에 기초한 미래 **projected** 수치이므로 실측 주장 삭제.
- **AX0095 DOC**: source says **6-week co-creation pilot**. 고객사 프로덕션 도입이 확인되지 않아 `PILOT_NOT_CONFIRMED_CUSTOMER_PRODUCTION`으로 별도 검토 필요. 사용자의 '실제 도입 사례' 연구범위 편입 여부 미확정.
- **AX0096 Sicredi**: 20일/6,500명 **파일럿** 지표의 10~12%는 고객 재방문율이 아니라 *상품전문가 이관 없이 해결된 상담 비율* 증가. 운영 전체로 일반화 금지.

이 24건은 소스 기반 1차 **재기술**이므로 신뢰할 수 있는 최종 정답 라벨(인과 대응) 또는 연구용 frozen corpus가 아님. 나머지 70개 부모 후보 및 업무 분할 가설은 상세 검증 미완료.
