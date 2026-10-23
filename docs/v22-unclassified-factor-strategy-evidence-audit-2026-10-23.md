# AX 데이터셋 v2.2 — 미분류 Factor/Strategy 25개 출처 재검토 보고
검토 기준일: **2026-10-23** | 상태: **REVIEW_RECOMMENDATIONS_NOT_APPLIED** | 작업 브랜치: `experiment/v22-repeatability-audit`

## 결론
- 93개 원본 중 **고유 미분류 사례 25개**, Factor 누락 **24건**, Strategy 누락 **4건**(중복 포함).
- 기존 91개 중 Factor의 **22건은 고의 ABSTAIN**, Strategy의 **2건은 고의 ABSTAIN**이다. 나머지 각 2건은 신규 Wayfair/제주은행으로 미검토.
- 1차 출처와 기존 frozen taxonomy를 비교한 결과, **기존 분류의 직접 근거가 명확한 변경은 3개 라벨**: 현대무벡스 F01, Wayfair F01, 제주은행 S1.
- 이 권고를 승인·반영해도 **Factor 미분류 22건, Strategy 미분류 3건**은 남는다. 이는 오류 개수가 아니라 불충분한 근거/카테고리 범위의 기록이다. 고유 미분류 사례는 24개로 감소한다.
- **분류 사전 변경 권고는 현재 없음**. 단 광고 소재 제작 병목 F 신규 후보를 시사하는 서로 다른 업체의 **Oneisall·FyterTech·Hisense 3개**가 있다. 기존 사례와의 일관성 감사 후 별도 버전으로 승인할 사안이다.
- **원본 케이스 JSON/CSV, taxonomy, 평가표, GT, release manifest는 수정하지 않았다.** 본 보고는 변경전 검토 근거이며 연구자 최종승인을 대신하지 않는다.

## 분류 원칙
1. Factor는 Problem/Task/Context에 직접 명시된 문제의 원인만 선택한다. 해결기술(Implementation)에서 원인을 거꾸로 추측하지 않는다.
2. Strategy는 해당 업무에서 실제 제공된 기능을 선택한다. 인프라의 세부기술과 사용자에게 제공된 업무기능을 구분한다.
3. 특정 범주에 맞추려고 원문을 고치거나 새로운 분류를 임의 신설하지 않는다.
4. 정당한 `ABSTAIN`과 미실시 `NOT_REVIEWED`는 상태를 구분한다. 분류 미정이 데이터 자체의 무효 또는 검색 관련도 0점은 아니다.
5. 개발용/최종 정답표(2,790 관련도 판단)는 **사례의 Factor·Strategy 부여와 별개**다.

## 사례별 판정 권고 — 전체 25건
| Case ID | 기업·업무 | 권고 | 판단 근거·출처 |
|---|---|---|---|
| `AXV2C_0016_02` | Best Buy | F=ABSTAIN 유지 | 정보 검색 지원은 확실하지만, 해당 세부 업무에서 정보의 분산 또는 전문가 과의존을 명시적으로 입증하지 못함 ([원문](https://cloud.google.com/customers/bestbuy-ai)) |
| `AXV2C_0042_01` | Law&Company | F=ABSTAIN 유지 | 법률 조사 시간·답변 신뢰 요구만으로 원래 업무의 반복성·분산·전문가 의존·규정 사고를 확정하기 어려움. RAG가 겨냥한 환각 문제와 원래 업무 문제를 구분 ([원문](https://www.microsoft.com/ko-kr/customers/story/20335-law-and-company-azure-functions)) |
| `AXV2C_0050_02` | Albert Heijn | F=ABSTAIN 유지 | 폐기 위험과 동적 할인 기능은 확인되지만 기존 F09의 다변수 예측/최적화 부담이 원래 문제로 명시됐다고 단정할 수 없음 ([원문](https://www.microsoft.com/en/customers/story/1739352737304784739-albertheijn-azure-open-ai-service-retailers-en-netherlands)) |
| `AXV2C_0068_02` | BNY | F/S=ABSTAIN 유지 | 거래 문의에 직원·관계자가 관여한 사실과 AI 지원은 확인. 실제 S2 대화형 지원인지 S6 실행형 자동화인지 세부 구현 구분 불가 ([원문](https://www.microsoft.com/en/customers/story/27322-bny-microsoft-365-copilot)) |
| `AXV2C_0074_01` | Cashfree Payments | S=ABSTAIN 유지, 전략 분류공백 기록 | 지원 이메일 자동 작성은 실재하나 S2의 인터랙티브 대화, S3 원문 추출/요약, S7 브랜드 창작물 등 기존 전략 경계와 정확히 일치하지 않음. F06은 유지 ([원문](https://aws.amazon.com/solutions/case-studies/cashfree-case-study/)) |
| `AXV2C_0092_01` | NatWest | F=ABSTAIN 유지 | Cora+ 대화서비스 운영은 확인. 사용자가 세련된 답변을 원한다는 사실만으로 운영상 정보분산 F02 등 특정 원인을 단정하기 어려움 ([원문](https://www.ibm.com/case-studies/natwest)) |
| `AXV2H_0071_01` | BPC | F=ABSTAIN 유지 | 내부정보 기반 정확한 답변과 모델 운영비 부담 확인; F01~F09 중 어떤 실패 메커니즘이 기존 지원 업무에 존재했는지 명확하지 않음 ([원문](https://aws.amazon.com/solutions/case-studies/bpc/)) |
| `AXV2H_0085_01` | Lloyds Banking Group | F=ABSTAIN 유지 | 소득 검증 단계 지연은 확인되지만 지연 원인이 수작업·정보분절 등 무엇인지 공개 근거가 불충분 ([원문](https://cloud.google.com/customers/lloydsbankinggroup)) |
| `AXV2H_0086_01` | THE ICONIC | F=ABSTAIN 유지 | 미보유 브랜드 검색 시 대안 발견 실패는 확인. 전체 데이터 플랫폼의 데이터 연결 이슈를 개별 검색 워크플로의 F07로 전이하지 않음 ([원문](https://cloud.google.com/customers/the-iconic)) |
| `AXV2N_0107` | The Home Depot—project advice | F=ABSTAIN 유지 | 프로젝트 설명 중심 추천의 필요성이지만 숙련전문가 판단 의존 F03의 직접 증거로 보지 않음 ([원문](https://corporate.homedepot.com/news/partnerships/home-depot-and-google-cloud-launch-agentic-ai-tools-help-customers-and-associates)) |
| `AXV2N_0108` | The Home Depot—support menu | F=ABSTAIN 유지 | 메뉴 기반 고객지원의 막다른 길은 UX·인터랙션 문제; 기존 F05의 분리된 프로세스/시스템 간 연계 문제로 억지 대응하지 않음 ([원문](https://corporate.homedepot.com/news/partnerships/home-depot-and-google-cloud-launch-agentic-ai-tools-help-customers-and-associates)) |
| `AXV2N_0109` | Indeed | F=ABSTAIN 유지 | 매칭 결과 설명의 필요성은 입증되나 기존 F01~F09 중 병목 원인으로 강제하지 않음 ([원문](https://openai.com/index/indeed/)) |
| `AXV2N_0112` | Duolingo—Role Play | F=ABSTAIN 유지 | 원어민 대화 기회 부족은 학습 접근성의 문제; 숙련자 판단 의존 F03과는 구분 ([원문](https://openai.com/index/duolingo/)) |
| `AXV2N_0113` | Duolingo—Explain my Answer | F=ABSTAIN 유지 | 맥락적 문법 해설의 필요성이 명백하더라도 기존 분류상의 운영 병목 원인으로 단정하기 어려움 ([원문](https://openai.com/index/duolingo/)) |
| `AXV2N_0114` | Oneisall | F=ABSTAIN 유지; 공통 신규요인 후보군 | 광고 이미지 제작 비용·지연. 다른 2개 독립 사례와 공통으로 '창작 소재 제작 병목' 신설 검토 가치 있으나 자동 확정하지 않음 ([원문](https://advertising.amazon.com/library/case-studies/oneisall)) |
| `AXV2N_0115` | FyterTech / Onkata | F=ABSTAIN 유지; 공통 신규요인 후보군 | 광고 이미지 제작 인력·시간 비용. 위 Oneisall/Hisense와 유사한 새 요인 후보 근거 ([원문](https://advertising.amazon.com/library/case-studies/fytertech-and-onkata)) |
| `AXV2N_0116` | Hisense Mexico / EPA | F=ABSTAIN 유지; 공통 신규요인 후보군 | 현지화 콘텐츠 제작 소요 및 재제작 지연. 3개 기업 근거로 같은 패턴이지만 신규 F 식별자 부여 전 전 코퍼스 일관성 검사가 필요 ([원문](https://advertising.amazon.com/en-gb/library/case-studies/hisense-mexico-and-epa)) |
| `AXV2N_0122` | Starling | F=ABSTAIN 유지 | 고객의 수동 필터/차트 탐색 불편은 확인되나 조직의 반복 수작업 병목이나 데이터 분산으로 동일시할 근거 부족 ([원문](https://cloud.google.com/customers/starling)) |
| `AXV2N_0123` | Hong Leong Bank | F=ABSTAIN 유지 | 정적 지식기반과 답변 지연이 정보분산(F02) 또는 고볼륨(F06)을 직접 뜻하지 않음 ([원문](https://cloud.google.com/customers/hongleongbank)) |
| `AXV2N_0127` | Sandvik / SigmaNEST | F=ABSTAIN 유지 | 신입 영업사원 학습 부담 및 숙련 기술 자료는 확인; 희소 전문가 의존에 의한 병목 F03의 증거는 별도 없음 ([원문](https://www.microsoft.com/en/customers/story/22965-sandvik-azure-open-ai-service)) |
| `AXV2N_0131` | Be My Eyes | F=ABSTAIN 유지 | 시각정보 접근성 문제는 사실이지만 기존 기업 운영 병목 F01~F09에 억지로 대응시키면 분류 왜곡 ([원문](https://www.bemyeyes.com/news/be-my-eyes-releases-winter-25-app-update-promising-significant-new-capabilities-for-blind-users/)) |
| `AXV2N_0140` | Intercom | F=ABSTAIN 유지 | 환불 업무의 다단계 자동 실행과 F05의 시스템/인수인계 분절은 서로 다름; 과정의 복잡함만으로 분절 확정 불가 ([원문](https://openai.com/index/intercom/)) |
| `AXV2P2_0097_01` | Hyundai Movex | F01 적용 권고(강함) | 원문에 영하 냉동창고 장시간 반복 하역작업 명시. F01 '반복 수작업'을 충족; 안전 위험 F08은 잠재 보조요인으로 별도 취급. S6 유지 ([원문](https://blog.cmesrobotics.ai/hyundaimovex-depal-casestudy)) |
| `AXV22_0092_01` | Wayfair | F01 적용 권고(강함); S=ABSTAIN 유지 | 원문에 사람이 상품 색상·스타일을 수작업 태깅한다고 명시. 반면 제품 속성 자동 분류는 문서/원문 분석 S3이나 예측·탐지 S4로 단정하기 어려움; 전략분류 공백 기록 ([원문](https://cloud.google.com/customers/wayfair-ai)) |
| `AXV22_0093_01` | Jeju Bank | S1 적용 권고(강함); F=ABSTAIN 유지 | 망분리 온프레미스에서 내부문서 RAG 업무 질의응답이라는 기능이 확인. F08은 보안/규제 제약을 포함하도록 재정의하지 않고 단순 적용하면 범주 확장 위험; 현재 F 미분류 유지 ([원문](https://labs.plateer.com/en/customers/case/jeju-bank-genai-platform)) |

## 중요한 연구 해석
- **Creative asset bottleneck**: Oneisall, FyterTech, Hisense는 서로 독립적인 업체이고 제작 비용·속도 제약이 공통이다. 신규 F 후보가 성립할 잠재 근거는 있으나, **한 가지 새로운 요인으로 정말 구분 가능한지**, 기존 F01과 중복되지 않는지, 코퍼스 93건 전체에 재분류 영향이 있는지 확인하기 전에는 F10을 확정하지 않는다.
- **Strategy taxonomy gap**: Wayfair의 비문서 상품속성 자동분류와 Cashfree의 고객지원 회신 생성은 서로 다른 기능이므로, 둘을 섞어 하나의 신규 Strategy로 만들지 않는다. 기존 S1~S7을 무리하게 적용하지 않는다.
- **Jeju Bank F08 보류**: 보안·규제 **제약조건**은 공개 원문에서 확인되지만 기존 F08은 오류/컴플라이언스 **위험의 문제 원인**을 정의한다. 해당 정의를 자동 확장하여 채점하면 재현성이 나빠질 수 있다.
- **Hyundai Movex F01**: 원문에 명시된 반복 하역은 F01의 직접적인 문제 근거다. 안전사고 가능성 F08은 부가 후보지만 단일 주된 F01부터 제안한다.
- **출처 한계**: 원문은 Google, Microsoft, AWS, 제품 공급사, 해당 기업 공개자료 등 **기업/공급자 발표**이며, 외부 독립실험으로 모든 성과 KPI가 검증되었다는 뜻은 아니다. 현재 기록의 성과 불확실성을 유지한다.
- 일부 원문은 여러 AX 워크플로를 함께 소개하므로 **동일 출처의 다른 업무 성과를 단일 Case의 성과로 전이하지 않는다.**

## 연구자 승인을 받은 뒤 실행할 최소 변경
1. 3개 권고 라벨의 Problem View/Solution View 증거 식별자와 결정 사유를 버전별 변경이력에 기록.
2. 기존 `ABSTAIN`은 근거 기반 상태로 유지하고, 신규 2개 사례의 나머지 빈 라벨은 **검토 결과 ABSTAIN**으로 상태를 구분(정확한 출처 근거·사유 저장).
3. 93개 Case ID·원문과 출처·분류 정의 간 일관성 테스트 후 **v2.2의 새 패치 버전** 제안 및 최종 승인 요청.
4. 이 과정에서 v1/v2.1 동결 데이터셋과 GT, 그리고 별도의 연구자 50개 관련도 파일은 건드리지 않음.

**최종 판단: 원인·전략이 하나라도 비어 있다는 이유만으로 전체 데이터셋을 폐기하거나 분류율 100%를 강제할 필요가 없다.**
