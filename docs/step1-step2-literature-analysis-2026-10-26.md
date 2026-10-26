# FAME-AX 논문 연구 Step 1·2 — 연구 범위·선행연구 검토 (2026-10-26)

> **상태:** 문헌 검토와 실험 설계 제안 완료. 교수님 최종 승인 전 초안이며, 모델 학습·재실험·독립 정답 확정·성능 개선은 수행하지 않았다.

## Step 1. 이번 논문의 연구 범위(제안)

**제목 후보:** LLM 기반 질의 확장 및 다중관점 생성이 3-View 문장 임베딩 기반 AX 사례 검색 성능에 미치는 영향

**질문:** AX 업무 문제의 검색 입력을 LLM으로 개선하거나 여러 관점으로 분해할 때, Problem·Task·Context로 나눈 사례 검색에서 Precision@10, Recall@10, F1@10 및 관점별 coverage와 비용이 어떻게 달라지는가?

**구분할 두 종류의 관점**
- **Query perspective:** 사용자의 업무 문제를 LLM이 나눈 질문 P1..Pk. 각 분기의 결과를 유지한다.
- **Case 3-view:** AX 사례를 Problem/Task/Context 각각의 텍스트로 구조화한 검색 입력. BGE-M3 모델 이름의 M3와 혼동하지 않는다.

**연구 가설(검증 전, 우월성 주장 아님)**
- RQ1: 원질의 대비 LLM 재작성·확장·코퍼스 기반 확장이 검색 F1@10 등을 개선하는가?
- RQ2: 문서 단일 필드/연결 필드 대비 분리된 3-view는 어떤 검색 품질 및 관점 커버리지 차이를 보이는가?
- RQ3: 관점 선택과 고정 후보 예산 배분으로 정확성-커버리지-비용 간 유의미한 이득을 얻는가? (보조·후속 실험 후보)
- RQ4: 서로 다른 LLM 3종의 독립 관련도 평가와 질의 생성 비교에서 모델 간 일치도·불일치 유형 및 용어별 효과는 무엇인가?

QCI 재학습, Gated Fusion, Root Cause/Wald, Evidence Fusion, AX 전략/로드맵 유용성의 **새 성능 입증은 이번 핵심 논문 범위에서 제외**. 기존 시스템과 산출물은 보존하고 후속연구로 연결한다. 유의미한 검색 개선이 관찰되지 않으면 개선을 주장하지 않고 부정 결과와 한계를 보고한다.

## Step 2. 선행연구 검증 및 도입 판정

| 논문 | 핵심 방법/결과 | AX 연구 도입 | 수준 및 주의 |
|---|---|---|---|
| Thakur et al., **BEIR**, NeurIPS D&B 2021 | 18개 이질적 검색 집합의 dense·sparse 등 공정 비교 | BM25/단일 Dense/3-view 및 비용 비교 설계 | **평가 필수**; 원 연구의 수치를 AX 성능으로 전용 금지 |
| Chen et al., **M3-Embedding**, Findings ACL 2024 | BGE-M3의 다국어·여러 검색 기능·다양한 텍스트 길이 처리 | 기존 BGE-M3 백본 유지, 한국어 질문/영어 사례, 토큰 길이 통제 | **기술 근거**; BGE-M3의 M3는 AX의 3-view가 아님 |
| Wang et al., **Query2doc**, EMNLP 2023 | LLM 가상 설명 생성 후 질의 확장; BM25·Dense에 적용 | 간결한 LLM 질의 확장 비교군 | **우선 비교**; 생성 표현의 원문 근거·환각·길이 체크 |
| Lei et al., **CSQE**, EACL 2024 | 코퍼스의 초기 검색 결과에 근거한 문장으로 질의 확장 | Problem/Task/Context로 제한된 실제 출처 기반 용어 확장 | **우선 적용 제안**; 초기 후보 편향/사전 정답 접근 금지 |
| Ammann et al., **Question Decomposition for RAG**, ACL SRW 2025 | 하위 질문 분해 후 개별 검색·후보 재정렬 | LLM 다중관점 생성과 각 분기 독립 검색 | **우선 비교**; QA에서의 이득이 AX에 직접 전이되는 것은 아님 |
| Gao et al., **HyDE**, ACL 2023 | LLM의 가상 관련 문서를 임베딩하여 실제 문서 검색 | 복잡한 재학습 없는 보조 비교 | **선택 실험**; 가상의 성공 사례가 사실로 오인되지 않게 구분 |
| Petcu et al., **Query Decomposition for RAG: Balancing Exploration-Exploitation**, EACL 2026 | 검색 예산과 하위 질의의 정보 획득 간 균형 | 중복/잡음이 많은 관점의 예산 축소 연구 | **2차**; bandit 학습 전체는 즉시 채택 안 함 |
| Saad-Falcon et al., **ARES**, NAACL 2024 | 자동 판정 보정에 인간 라벨 표본 활용 | 3 LLM 평가 결과의 전문가 검증/편향 확인 근거 | **평가 필수 원리**; 별도 판별기 학습까지 복제하지 않음 |
| Zheng et al., **Judging LLM-as-a-Judge**, NeurIPS 2023 | LLM 평가자의 위치·분량·자기선호 편향 | 모델 블라인드 독립 평가·불일치 표본 점검 | **평가 보조**; 3 AI 다수결은 인간 Gold가 아님 |
| Kuo et al., **MMLF**, Findings NAACL 2025 | 다중 질의·확장과 RRF를 통한 후보 통합 | 하위질의 다양화의 선행 근거로 인용 | **방법 전체 미채택**; 교수님 설계의 분기 유지 및 전역 RRF 미채택 |
| Kim et al., **QuDAR**, ACL 2026 | 원질의·확장질의와 sparse·dense에 쿼리별 적응형 비중 | 후속 적응형 방법과 기존 고정 가중치 비교 근거 | **후속**; 이번 논문을 과도하게 확장하지 않음 |

### 선행연구 URL (공식 프로시딩)
1. BEIR https://datasets-benchmarks-proceedings.neurips.cc/paper_files/paper/2021/hash/65b9eea6e1cc6bb9f0cd2a47751a186f-Abstract-round2.html
2. M3-Embedding https://aclanthology.org/2024.findings-acl.137/
3. Query2doc https://aclanthology.org/2023.emnlp-main.585/
4. CSQE https://aclanthology.org/2024.eacl-short.34/
5. Question Decomposition https://aclanthology.org/2025.acl-srw.32/
6. HyDE https://aclanthology.org/2023.acl-long.99/
7. Adaptive Decomposition https://aclanthology.org/2026.eacl-long.322/
8. ARES https://aclanthology.org/2024.naacl-long.20/
9. LLM-as-a-judge https://proceedings.neurips.cc/paper_files/paper/2023/hash/91f18a1287b398d378ef22505bf41832-Abstract-Datasets_and_Benchmarks.html
10. MMLF https://aclanthology.org/2025.findings-naacl.367/
11. QuDAR https://aclanthology.org/2026.acl-long.1791/
12. 불완전 qrels·pool 편향: NIST https://www.nist.gov/publications/bias-and-limits-pooling-large-collections

## 구체적 도입 우선순위

**핵심 1: 원 질의 → LLM 검색어/서술 확장(Query2doc) vs 초기 원문 근거 용어 확장(CSQE).**
원질의 보존, 내용 추가/삭제 로그, 출처 문자열, 단어별 기여(추가·삭제 ablation), prompt·seed·model 고정. Solution/Outcome/Strategy, 평가 정답, Test 자료의 정답 메타데이터가 query expansion에 노출되지 않게 한다.

**핵심 2: 단일 질의 vs LLM 다중관점 분해 × 3-view.**
Case Problem/Task/Context는 별도 텍스트·임베딩, 질문의 관점 P1..Pk와 혼동하지 않는다. 같은 검색 후보 집합·Top-K·토큰 예산을 유지하고 개별 관점 검색 결과를 기록한다. 공정한 대표 비교에서는 사전 정의된 10개 고유 후보 예산을 분기별로 배분하며 부족 시 사전 규칙대로 보충한다. RRF 전역 통합은 도입하지 않는다. 원 질의만/3-view, 다중관점/3-view, 원 질의+확장/3-view와 단일 텍스트/3-view의 교차 분석으로 기여 분리.

**보조 3: HyDE 및 적응형 관점 선택.**
핵심 우선 실험에서 혼동 요인을 제거한 다음 진행. 과도한 기법 추가로 목표를 다시 확장하지 않는다.

## 다음 실험 설계 제안 (아직 미실행)

1. **자료:** 기존 동결 84개를 과거 재현 비교 기준으로 보존. v2.5의 11,766개는 등록기록, 9,416개는 검색후보(검증된 AX 독립 사례 수 아님), 112개는 *서술적 Dev* 후보이며 정답 라벨이 없다. 성능 수치는 승인 qrels 전 계산 금지.
2. **실험 분리:** 문제·업무·맥락을 인코딩할 때 동일 128-token/1024d/모델·언어·길이 조건. 문서 코퍼스 고정 후 query variation만 변경하는 실험과, 질의 고정 후 case view representation만 변경하는 실험을 별개 수행.
3. **판정:** 서로 다른 제공자/계열의 LLM 최소 3종이 같은 질문-사례 쌍을 서로의 답·검색순위·Solution을 보지 않고 0~4 점수 부여. 원문 근거 문장과 이유 기록. 불일치는 독립 조정, 인간 검증 표본 확보. 과거 AI-Silver 결과를 인간 정답으로 취급 금지.
4. **풀링:** 단일 BM25, 단일 Dense, 3-view, Query2doc, CSQE 등 모든 주요 시스템의 Top-K 합집합과 무작위/경계 사례를 판정 풀에 포함. 미판정은 비관련 0이 아님. 수집 후보 수를 늘려 Recall이 높아 보이는 편향 방지.
5. **지표:** Precision@5/10, Recall@5/10, F1@5/10(동일 qrels·동일 K), nDCG@10, Perspective Coverage(보조), 오류 분석, 고유 후보 수, 토큰/지연시간/비용. 전체 relevant 수 불완전 시 Recall/F1 확정 수치 대신 판정 범위와 한계 보고. 원질의 언어(한국어)·사례의 원문 언어(주로 영어)별 하위분석.
6. **검증:** Dev에서만 prompt·모델·용어·코퍼스 크기 조정. 5,298개의 기존 누수 그룹 링크를 점검하고 동일 기업/출처/동일 업무의 재서술은 Test에 분리 투입하지 않음. 미사용 질문으로 Held-out Test를 만든 후 설정 동결. 모델 학습을 재개한다면 Epoch별 Train/Validation Loss를 별도 기록.
7. **비교 유의성:** 개별 관점·3회 반복을 독립 문제 수로 부풀리지 않고 독립 원질문 단위로 평균·신뢰구간을 보고.

## 현재까지 확인된 불리한 기존 결과 (숫자 혼동 방지)

- Stage1 개발 평가(Reference perspective): GPT-only Recall@10 **72.35%**, single Dense **53.32%**, multi-perspective Dense **45.30%**. 모든 방법이 같은 한 종류 LLM/AI 기반 평가자료를 사용한 개발 실험으로 독립 최종 검증 아님.
- QCI 별도 실험(동적 97관점, 다른 정의의 평가): 3-view Dense **47.64%**, Dense+QCI **45.33%**, QCI 단독 **27.73%**. Stage1의 53.32%와 직접 뺄셈 금지.
- QCI 학습 24 epoch의 fold별 마지막 Train Loss만 확인됨. Epoch별 학습곡선/Validation Loss 미확인.
- 신규 v2.5: 검색 인덱스 9,416 작동/112 Dev 후보 및 BM25·Dense 순위 생성, 신규 승인 qrels 0, Held-out Test 0. **검색 작동과 검색 정확도 검증은 다름.**

## Step 1~2 산출물과 Gate

- 완료: 연구 초점/주제 초안, 검증 가능한 선행연구 비교표, 채택/보류 제안, 연구 가설, 다음 실험 조건.
- 미완료(후속 Step): 교수님 범위 승인, 신규 사람/다중모델 판정, 재현 실험, F1 계산, 모델 학습, 최종 논문 우월성 주장.
- 이전 동결 데이터·연구 코드·실험 자료 변경 없음.
