# AX v2.2 미분류 25개: 공개 원문 **전체 맥락** 재검토
기준일: 2026-10-23 KST | 저장 유형: `SOURCE_FULLTEXT_REREVIEW_RECOMMENDATIONS` | **원본 데이터·분류체계·Ground Truth 변경 없음**

## 무엇을 검사했나?
93건 중 Factor 또는 Strategy가 비어 있는 **서로 다른 25건**을 골라 사례마다 원래 등록한 기업/공급사 공개 원문 **전체 페이지의 맥락**을 읽고 문제(Problem), 원인(Factor), 실제 제공 기능(Strategy), 해당 업무 고유의 결과를 분리했다. 하나의 페이지에 여러 업무가 있으면 **서로 다른 업무의 어려움/효과를 합치지 않았다**. 공개 페이지 23개(같은 페이지를 참조하는 기업 사례 포함). 기존 v1의 문구가 현재 v2.2의 원문 근거보다 더 명확하다는 이유로 옛 라벨을 자동 복구하지 않았다.

검토자는 ChatGPT이며 **독립적 인간 교차평가 또는 객관적 사실확정과 동등하다고 주장하지 않는다**. 출처는 기업 공식 게시물과 공급사 고객사례가 중심이므로 벤더의 성과 주장에는 독립 검증 한계가 있다.

## 판단 기준
- 원인은 **문제/업무/배경**에서 확인. 인공지능 해결기술/결과를 보고 과거 원인을 거꾸로 추측하지 않음.
- 전략은 **실제로 도입·제공한 업무 기능**에서 확인. 단순 LLM 또는 RAG를 사용했다고 무조건 해당 전략이 사용자에게 제공된 주전략은 아님.
- **A (직접근거 강함)**: 기존 분류 정의에 근거가 명확해 즉시 수정안으로 제시하되 연구자 승인 전 자동 반영은 금지.
- **B (합리적 후보)**: 원문 전체에서 유력한 근거가 발견되었지만 현행 정의 또는 다른 업무와의 근거 귀속 문제 때문에 승인 전에 한 번 더 검토.
- **C (기존 보류/분류체계 공백 유지)**: 원인/전략 자체가 없는 것이 아니라, 현재의 분류사전 또는 공개 사실과의 정확한 대응에 문제가 있음. 연구에 불필요하거나 부적합하다는 주장과는 다름.

## 요약
| 항목 | 결과 |
|---|---:|
| 재검토한 서로 다른 사례 | **25** |
| A: 직접 근거가 확인되어 수정 권고 | **4 사례**: Hong Leong Bank(F01), Hyundai Movex(F01; F08 보조 근거), Wayfair(F01), Jeju Bank(S1) |
| B: 원문상 합리적 후보, 확정은 조건부 | **6 사례**: Best Buy(F07), Albert Heijn(F09), BNY(F05), NatWest(F02), BPC(F01), Sandvik(F03) |
| C: 분류 공백/원인 근거 부족/연구 범위 확인 | **15 사례** |
| 현행 F 또는 S가 비어 있는 사례 | 25/93 |
| A 제안의 단일 주라벨 4건만 반영 시 F 미분류 | 24 → **21** |
| A 제안의 단일 주라벨 4건만 반영 시 S 미분류 | 4 → **3** |
| A 제안의 단일 주라벨 4건만 반영 시 미분류 존재 사례 | 25 → **23** |

**사례별 독립 표(25건 전체)**

| Case ID | 기업/업무 | 판정(기존 미분류 부분만) | 원문 전체를 읽어 다시 확인한 판단 및 근거 |
|---|---|---|---|
| `AXV2C_0016_02` | Best Buy | **B · 원인 후보 F07** | 고객기록과 사내 정책·문제해결 문서·수리 지식베이스를 연계했다고 명시. 서로 다른 정보의 연계 필요성은 확인되지만 그것이 해당 상담원 업무의 기존 병목 '원인'인지 구체 진술은 부족. F02보다는 F07이 유력 후보. ([공식 원문 — Extending customer care / Staying at the leading edge](https://cloud.google.com/customers/bestbuy-ai)) |
| `AXV2C_0042_01` | Law&Company | **C · 원인 보류** | 법률정보 조사 소요와 생성답변 정확성/환각 위험을 설명. 후자는 AI 적용에 따른 품질위험이므로 과거 법률정보 조사 업무의 근본원인 F08이라고 소급하지 않음. S1 유지. ([공식 원문 — AI 기술로 법률 서비스 품질 고도화 / 할루시네이션 제로가 목표](https://www.microsoft.com/ko-kr/customers/story/20335-law-and-company-azure-functions)) |
| `AXV2C_0050_02` | Albert Heijn | **B · 원인 후보 F09** | 유통기한 임박 상품에 대해 시간에 따라 할인폭을 조정하는 Dynamic Markdown. 시간/재고 손실/할인 의사결정의 동적 최적화라는 F09 근거가 부분적으로 있으나 종래 수동 결정 복잡성이 명시됐는지는 불확실. S5 유지. ([공식 원문 — Using AI at scale](https://www.microsoft.com/en/customers/story/1739352737304784739-albertheijn-azure-open-ai-service-retailers-en-netherlands)) |
| `AXV2C_0068_02` | BNY | **B · 원인 후보 F05 / 전략 보류** | 하나의 문의 해결에 과거 직원과 여러 관계자가 관여. 인수인계·협업 병목을 시사하지만 부서/시스템 분절이라고 단정하기에는 부족. AI 지원/해결은 설명되지만 상담 챗봇(S2)과 작업 실행(S6) 구분 정보가 없어 S 보류. ([공식 원문 — Resolving client transaction inquiries 80% faster](https://www.microsoft.com/en/customers/story/27322-bny-microsoft-365-copilot)) |
| `AXV2C_0074_01` | Cashfree Payments | **C · 전략 분류 공백 유지** | 실제 업무는 고객 문의에 맞는 지원 이메일 생성. 현재 S2는 대화형 상호작용, S3는 기존 문서의 분석, S7은 브랜드 창작물 생산에 한정돼 있어 정확히 일치하지 않음. S7을 임의 확대하거나 S2로 오인하지 않음. F06 유지. ([공식 원문 — Opportunity / Solution](https://aws.amazon.com/solutions/case-studies/cashfree-case-study/)) |
| `AXV2C_0092_01` | NatWest | **B · 원인 후보 F02** | 이전 Cora는 다른 웹페이지로 고객을 보내 스스로 추가 탐색하게 했고, Cora+는 상품·서비스·금융정보 등 여러 정보원을 연결해 대화 내 답변. '정보 접근/분산으로 탐색 지연' F02에 상당히 가깝지만 명시된 저장소 사일로와 시스템 분산 원인을 확정하기 전 후보로 둠. S2 유지. ([공식 원문 — From Cora to Cora+: A big next step](https://www.ibm.com/case-studies/natwest)) |
| `AXV2H_0071_01` | BPC | **B · 원인 후보 F01** | 지원직원이 고객 요청을 챗봇에 입력하고 검토한 답을 고객에게 전달, 지원직원 업무부담 감소 목표가 명시. 반복 문의 처리 업무 F01은 합리적 후보. 단 구형 업무량을 정량 제시하지 않아 확정 전 사례 단위의 인과 귀속 점검. S1 유지. ([공식 원문 — Opportunity | Using Amazon Bedrock to Build an Intelligent Customer Support Chatbot](https://aws.amazon.com/solutions/case-studies/bpc/)) |
| `AXV2H_0085_01` | Lloyds Banking Group | **C · 원인 보류** | 주택담보대출 소득 검증이 수일에서 수초로 단축됐다는 성과는 확인. 기존 검증 지연의 직접 원인이 수기 대조나 시스템 분절이라는 설명은 없음. 다른 ML 플랫폼 현대화 문제를 이 업무의 원인으로 혼용하지 않음. S4 유지. ([공식 원문 — Automating processes to improve customer experiences](https://cloud.google.com/customers/lloydsbankinggroup)) |
| `AXV2H_0086_01` | THE ICONIC | **C · 원인 보류(범위 점검)** | 회사 전체 데이터 플랫폼은 커지는 데이터량과 분산 자료 연결이 문제였음. 그러나 분리된 이 사례는 미보유 브랜드 검색 시 대체상품 발견 실패라는 고객검색 업무이며 해당 F07이 그 검색 실패의 직접 원인이라고 원문은 설명하지 않음. S1 유지; 검색/발견 관련 문제의 별도 분류는 장기 후보. ([공식 원문 — Seamless integration / Customer-first approach](https://cloud.google.com/customers/the-iconic)) |
| `AXV2N_0107` | The Home Depot · Magic Apron | **C · 원인 보류** | 고객이 프로젝트를 말로 설명하면 전문가 수준의 안내 제공. 고객의 프로젝트 상담·검색 UX 수요는 있으나 '희소 전문인력 판단에 대한 과도한 의존' F03을 직접 입증하지 않음. S2 유지; 매장 테스트/미래 기능을 운영 사례의 성과로 포함하지 않음. ([공식 원문 — Magic Apron Assistant](https://corporate.homedepot.com/news/partnerships/home-depot-and-google-cloud-launch-agentic-ai-tools-help-customers-and-associates)) |
| `AXV2N_0108` | The Home Depot · 고객센터 | **C · 원인 보류** | 기존 고정식 메뉴 자동화가 막다른 경로와 대화 의도 처리 마찰을 만든다는 문제는 명확. 그러나 F05의 여러 업무 시스템/단계 간 분절을 단정할 수 없으므로 '상호작용 경직성' 별도 패턴으로 기록. SMS·채팅·전화 서비스의 S2는 유지. ([공식 원문 — Bringing a new level of customer service](https://corporate.homedepot.com/news/partnerships/home-depot-and-google-cloud-launch-agentic-ai-tools-help-customers-and-associates)) |
| `AXV2N_0109` | Indeed | **C · 원인 보류** | 기존 추천의 '왜 적합한지'에 대한 설명이 짧고 부족했다는 사실은 명확. 그러나 F01~F09의 운영 원인으로 직접 매핑하기 어렵고 미설명 추천의 신뢰·설명가능성 공백을 별도로 식별. 기존 S5 유지하되 실제 기능은 추천 결과의 설명문 생성이므로 전략 정합성 추후 별도 점검 필요. ([공식 원문 — Early AI experiments / Fine-tuning for personalized match explanations](https://openai.com/index/indeed/)) |
| `AXV2N_0112` | Duolingo · Role Play | **C · 원인 보류** | 원어민 대화 상대에 접근하기 어렵고 정해진 시나리오의 대화가 제한적이라는 점 확인. 이는 학습기회/상호작용 격차이지 기존 F03의 특정 숙련자 의사결정 의존 문제와 다름. S2 유지. ([공식 원문 — Conversation practice / Role Play](https://openai.com/index/duolingo/)) |
| `AXV2N_0113` | Duolingo · Explain my Answer | **C · 원인 보류** | 개별 학습자 오답에 맞는 문법 설명을 기존 고정 가이드와 초기 AI로 정확히 만들기 어려웠음. 학습 맞춤피드백 부족은 구체적이지만 현행 F 범주 내 운영상의 원인과 같다고 보기는 어려움. S2 유지. ([공식 원문 — Explain my Answer / contextual feedback](https://openai.com/index/duolingo/)) |
| `AXV2N_0114` | Oneisall | **C · 신규 Factor 후보군** | 사진작가·디자이너별 광고 이미지 제작이 느리고 비싸며 소재 변형 시험을 제한했다는 원인이 직접 명시. 현행 F01은 반복적인 '운영 처리 수작업' 중심이므로 창작물 제작 병목을 무리하게 F01로 축약하지 않음. FyterTech/Hisense와 함께 신규 F 후보 검토. S7 유지. ([공식 원문 — Goals](https://advertising.amazon.com/library/case-studies/oneisall)) |
| `AXV2N_0115` | FyterTech / Onkata | **C · 신규 Factor 후보군** | 사진 촬영/디자인 비용·시간으로 광고 소재 대량 확보 어려움. 독립 업체의 창작물 제작 병목 사례로 F 신규 후보를 지지. S7 유지. ([공식 원문 — Goals / Approach](https://advertising.amazon.com/library/case-studies/fytertech-and-onkata)) |
| `AXV2N_0116` | Hisense Mexico / EPA | **C · 신규 Factor 후보군** | 글로벌 이미지를 현지화하는 데 최대 1개월이 소요되고 현지 구매자의 맥락과 불일치. 창작물 현지화/제작 병목이 또 다른 독립 출처로 확인. S7 유지. ([공식 원문 — Goals](https://advertising.amazon.com/en-gb/library/case-studies/hisense-mexico-and-epa)) |
| `AXV2N_0122` | Starling · Spending Intelligence | **C · 원인 보류** | 고객이 소비현황 확인에 필터/차트를 직접 탐색하는 불편을 자연어 질문으로 대체. 개인 사용자 UI의 탐색 부담이지 F01의 조직 운영 반복 수작업이나 F07의 데이터 사일로가 확인된 것은 아님. S2 유지. Starling의 다른 ML 인프라 문제를 전가하지 않음. ([공식 원문 — Spending Intelligence](https://cloud.google.com/customers/starling)) |
| `AXV2N_0123` | Hong Leong Bank · Marina | **A · F01 적용 권고** | 이전 고정형 지식기반의 답변이 느리고 제한적. 공개 사례에 개발자가 지식베이스를 수작업으로 갱신/색인하는 번거로움을 동적 검색으로 제거했다는 설명이 명시되어 F01 반복 수작업(지식 갱신·색인)이 직접 지지됨. S2 유지. 기존 AI 설계의 문제와 기존 고객지원 업무의 병목이라는 층위 차이를 변경이력에 적을 것. ([공식 원문 — The accuracy imperative / Dynamic FAQs](https://cloud.google.com/customers/hongleongbank)) |
| `AXV2N_0127` | Sandvik / SigmaNEST | **B · 원인 후보 F03** | 업계 숙련도 격차, 복잡한 제품, 축적된 전문지식을 신입 영업사원이 접근해야 함. F03 '전문가 판단 의존'의 근거가 있으며 다른 사례보다 분명하지만 '과도한 희소 전문가 의존'까지 정량 입증되지 않아 후보 권고. S1 유지. ([공식 원문 — Addressing complexity / AI in sales and support](https://www.microsoft.com/en/customers/story/22965-sandvik-azure-open-ai-service)) |
| `AXV2N_0131` | Be My Eyes | **C · 원인 보류 + 범위 점검** | 시각정보 접근성 부족 문제는 확실하나 9종 '기업 운영 문제' 요인과 어긋남. B2C 접근성 서비스도 기업 AX 연구의 모집단에 넣는 것이 타당한지 별도 적격성 점검 대상으로 기록. S2 유지. ([공식 원문 — User Experience and Performance / User Data Management](https://www.bemyeyes.com/news/be-my-eyes-releases-winter-25-app-update-promising-significant-new-capabilities-for-blind-users/)) |
| `AXV2N_0140` | Intercom · Fin Tasks | **C · 원인 보류** | 환불 등의 복잡한 고객지원 업무 실행은 확인되나 업무가 왜 분절되었는지/반복 수작업인지에 대한 직접 근거가 약함. F01/F05를 S6 워크플로 실행에서 역추론하지 않음. S6 유지. ([공식 원문 — Lesson 1 / Fin Tasks](https://openai.com/index/intercom/)) |
| `AXV2P2_0097_01` | Hyundai Movex | **A · F01 적용 권고; F08 보조요인 강함** | 냉동 물류센터의 장시간 반복 수작업과 노동 부담이 명시(F01), 동상·근골격계·사고 위험도 구체적으로 명시(F08). 현행 단일 라벨 구조에는 주된 F01 권고, 다중라벨 정책을 도입하면 F08 동시 채택 가능. S6 유지. ([공식 원문 — 냉동 물류센터 자동화가 시급했던 이유](https://blog.cmesrobotics.ai/hyundaimovex-depal-casestudy)) |
| `AXV22_0092_01` | Wayfair | **A · F01 적용 권고; 전략 분류 공백** | 원문에 수작업으로 색상/스타일 속성을 태깅하던 공정을 AI가 대체하고 67% 처리시간 감소 보고. F01 근거 명확. 반면 S3의 '문서/원문 정보 추출·분석'과 실제 '제품 속성 분류/태깅'의 범위 일치 여부가 불명확. 별도 S 후보의 taxonomy 정합성 검토 필요. ([공식 원문 — Taking the friction out of home inspiration / Reinventing the customer journey](https://cloud.google.com/customers/wayfair-ai)) |
| `AXV22_0093_01` | Jeju Bank | **A · S1 적용 권고; F08 후보** | 망분리 온프레미스에서 내부문서를 지식 컬렉션으로 연결해 RAG 질의응답하는 실제 기능은 S1을 직접 지지. 보안/망분리/금융규제 대응이 핵심 제약이므로 F08 컴플라이언스 위험 후보는 있으나 규제 제약을 곧바로 운영상 사고·위반 위험으로 동일시하지 말고 정의 적합성 확인. '은행 전체 AX 플랫폼'을 1개의 Q&A 워크플로 성과로 확대하지 않음. ([공식 원문 — The Challenge / Technology applied / Bank-wide shared agents](https://labs.plateer.com/en/customers/case/jeju-bank-genai-platform)) |

## 과거 짧은 사례 설명과 원문 전체 읽기의 차이 — 핵심 5가지
1. **Hong Leong Bank**: '정적 지식베이스로 답변이 느리다'에서 끝나는 설명보다 더 구체적인 **개발자의 수작업 지식베이스 갱신/색인** 근거가 원문에 존재 → F01을 직접 지지.
2. **Hyundai Movex**: 냉동 하역 자동화의 원인은 막연한 '험든 일'만이 아님. **오래 반복 수행하는 노동 + 신체/산업안전 위험** 둘 다 원문에 명시 → F01 강함, F08 보조로 적격.
3. **NatWest**: '세련된 고객 응답'만의 문제가 아님. 이전 챗봇이 다른 콘텐츠로 이용자를 돌려보냈고, 새 챗봇이 **여러 정보원**에 접근해 답함 → F02 후보 강화.
4. **Sandvik**: 제품 설명을 배우는 일이 어렵다는 요약 외에 공식 원문에 **skills gap / 복잡한 제품 / 축적 전문지식 활용**을 함께 제시 → F03 후보 강화.
5. **Best Buy**: 고객기록과 내부 지식베이스의 **연계 필요**는 사실이나, 그것이 개별 상담원 실시간 지식검색 워크플로의 이전 **직접 병목 원인**이었다고 원문이 명시한 것은 아님. F07은 후보이지 확정 아님.

## 눈에 띄는 분류체계 자체의 문제
- **Factor 9종이 설명하지 못하는 기업 업무 문제**: 창작 소재 제작 원가·시간/현지화 병목(Oneisall/FyterTech/Hisense), 대화형 UX 경직성(Home Depot), 추천 설명 부족(Indeed), 시각접근성(Be My Eyes), 학습 대화/맞춤 피드백(Duolingo) 등은 '문제를 알 수 없다'가 아니라 **현행 Root Cause 사전이 그 문제를 표현하지 못한다**는 가능성을 시사한다.
- **Strategy 7종의 경계**: Cashfree의 맞춤 고객지원 **이메일 작성**과 Wayfair의 **상품 속성 분류/태깅**은 실제 업무가 명백하지만 현재 S1~S7 문구상 부적합하거나 애매하다. '전략 미확인'이 아니라 **전략 사전 포괄범위 문제**일 수 있으므로 해결방향이 달라야 한다.
- **업무 단위 경계가 중요**: THE ICONIC/Starling/Lloyds 페이지의 회사 전체 데이터 플랫폼 문제를 특정 검색/소득검증/소비현황 Q&A 워크플로의 원인으로 자동 이전하면 또다시 v1식 혼합문제가 생긴다.
- **연구 모집단 확인 필요**: Be My Eyes 등 소비자 대상 서비스는 운영 중인 AI 서비스라도 '기업 AX 업무 전환 사례'의 범주에 포함되는지가 별개의 질문. 검색 코퍼스 유지를 선결로 가정하지 않는다.

## 가장 작은 후속 작업(승인 전까지 원본 불변)
1. A등급의 **4개 주 라벨**을 '수정 후보'로 검증보고서에 별도 제시한다. 현대무벡스 F08은 복수 원인 정책 없이는 덮어쓰지 않음.
2. B등급의 6개는 원인과 해당 **업무 단위**의 연결성을 재확인해, *증거로 분류를 확정할 수 있는 경우만* A로 승격한다.
3. C등급은 **출처 부족 vs 기존 분류 사전 부적합 vs 코퍼스 적격성** 사유를 코드로 나누고, 같은 패턴의 3개 이상 사례가 확인되는 범주만 사전 변경을 심사한다. 모든 빈칸을 0이나 틀림으로 해석하지 않는다.
4. 원인/전략 라벨 관리(최종 추천 구조)와 검색 관련도 정답표 관리(2,790개 후보)는 **서로 다른 실험 작업**으로 둔다.
5. 연구자 승인 전에는 `data/v2_2/main_cases_v2_2.json`, `csv`, taxonomy, manifest, Dev/GT, 기존 파일럿 50개는 변경하지 않는다.

## 기술적 제한
- 25건 × 전체 검색결과가 아니라 각 **공개 원문 페이지 전체 문맥**을 봤으며, 출처 서버의 비공개 부록이나 내부 기록까지 본 것은 아니다.
- 동일 공급자 페이지에 여러 실사용 업무가 등장하는 경우 해당 업무만 뽑았다.
- 새로운 `F10` 또는 `S8`을 임의 신설한 적 없다.
- 이 문서는 **검토보고서**, 라벨링 승인이나 연구용 동결 완료가 아니다.
