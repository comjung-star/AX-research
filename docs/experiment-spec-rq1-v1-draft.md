# RQ1 Retrieval Experiment Specification v1 — DRAFT

> 상태: **DRAFT_FOR_REVIEW**  
> 작성일: 2026-10-21  
> 이 문서는 사용자 검토 전 초안이다. 아래 `REVIEW_REQUIRED` 항목은 승인 전까지 최종 Freeze하지 않는다.

## 1. 실험 목적

본 1차 실험의 목적은 다음 연구질문을 검증하는 것이다.

> **하나의 Business Problem Query를 그대로 검색하는 Single-query 방식보다, LLM이 업무문제를 복수 Perspective로 동적 분해하고 Perspective별 검색 branch를 유지하는 방식이 관련 AX 사례의 Recall과 문제관점 Coverage를 향상시키는가?**

본 실험은 전체 FAME-AX 모델을 한 번에 검증하지 않는다. 우선 교수 제안 Search Core에서 가장 앞단의 핵심 가정인 **Multi-Perspective Decomposition + Branch-preserved Retrieval의 효과**를 분리해서 확인한다.

이 단계에서 검증하지 않는 요소:
- Multi-view Embedding / Gated Fusion
- Hybrid Retrieval의 Dense+Sparse 결합
- Query-Case Interaction Neural Network
- Factor Anchor / Wald Evidence
- Evidence Fusion / Recommendation Head

위 요소는 RQ1의 기본 검색효과를 확인한 뒤 단계적으로 추가한다.

---

## 2. 연구 근거와 구분

### 교수 제안/연구계획서에 직접 포함된 비교 방향
- Single-query BM25
- Single-query Dense Retrieval
- GPT-only
- LLM Multi-Perspective Retrieval
- Recall@K
- Perspective Coverage@K
- Strategy Coverage@K
- 비교 시 Search/Output Budget 통제

### 본 명세에서 추가로 정하는 구현·실험 규칙
아래 내용은 교수님이 직접 지정한 값이 아니라 **공정하고 재현 가능한 실험을 위해 연구자가 정하는 실험설계**다.
- 검색 문서의 정확한 텍스트 구성
- Korean BM25 tokenizer
- Dense embedding 모델
- K 값
- Perspective 생성 개수의 상·하한
- branch 결과를 K개 unique case로 만드는 방법
- LLM 반복실행 횟수
- 결과 파일 schema
- 진단용 overlap / marginal recovery 지표

---

## 3. 데이터 및 Freeze 기준

### 3.1 Main Dataset
- 파일: `data/main_cases_v1.csv`
- Case: `AX0001~AX0100`
- 총 100건
- Main Dataset v1 Freeze 유지

### 3.2 Dev Ground Truth
- Query: `GTQ001~GTQ010`
- Active Query: 10건
- Reference Perspective: 현재 Pilot 기준 Query당 3개
- Perspective × Case relevance: 3000 labels
- Gold threshold: relevance >= 3
- Freeze 문서: `data/dev_ground_truth_freeze_v1.md`

Ground Truth는 Runtime 입력으로 사용하지 않는다.

### 3.3 Dev / Test 역할
- 현재 GTQ001~GTQ010: **Dev/Pilot**
- Baseline / Prompt / 모델 설정 검토는 Dev에서 수행
- 모든 규칙을 Freeze한 뒤 별도 Held-out Test Query 구축
- Held-out Test 결과를 본 후 모델이나 Prompt를 재조정하지 않음

---

## 4. 검색 입력 정의

### 4.1 사용자 Query 입력 — Primary ✅ APPROVED
Primary RQ1 실험에서는 다음만 사용한다.

`business_problem_query`

결정: **Business Problem only로 확정**

이유:
- 연구의 핵심 입력이 Business Problem이기 때문
- Goal/Context를 추가했을 때의 이득과 Multi-Perspective 자체의 이득을 섞지 않기 위함
- BM25 / Dense / GPT-only / Multi-Perspective에 동일 원문을 제공하기 위함

### 4.2 Query Goal / Context
`goal`, `context`는 Primary 실험에는 사용하지 않는다.

필요할 경우 후속 sensitivity experiment에서:
- Business Problem only
- Business Problem + Goal + Context
를 비교한다.

### 4.3 AX Case 검색 문서 — Problem View only

각 Case의 검색용 텍스트는 다음 세 필드를 사용한다.

1. `business_problem`
2. `ax_target_task`
3. `business_context`

직렬화 예:

```text
[PROBLEM] ...
[TASK] ...
[CONTEXT] ...
```

Retrieval 시 아래 Solution View는 사용하지 않는다.
- strategy
- ai_technology
- implementation
- outcome

Strategy는 Retrieval 이후 `Strategy Coverage@K` 평가에만 사용한다.

---

## 5. 비교 시스템

### B1. Single-query BM25

```text
Business Problem Query
→ Korean lexical tokenization
→ BM25
→ ranked AX cases
```

목적:
- Sparse lexical single-query baseline

확정 구현:
- Python BM25
- Korean tokenizer: **Kiwi 형태소 토큰화**
- tokenizer / package version 기록

결정: **Kiwi 사용으로 APPROVED**

---

### B2. Single-query Dense Retrieval

```text
Business Problem Query
→ Text Encoder
→ query embedding

Problem View AX Cases
→ same encoder
→ case embeddings

cosine similarity
→ ranked AX cases
```

목적:
- 의미기반 single-query baseline
- Multi-Perspective 효과를 같은 Dense backbone과 직접 비교

초안 Dense model:
- `BAAI/bge-m3`
- Dense embedding 기능만 사용
- embedding normalize 후 cosine similarity

결정: **BAAI/bge-m3 사용으로 APPROVED**

---

### B3. GPT-only

LLM에게 100개 AX Case의 **Problem View만** 제공하고 Business Problem Query와 직접 관련된 Case를 순위화하도록 한다.

입력:
- Business Problem Query
- AX0001~AX0100
- 각 Case의 Problem / Task / Context

금지:
- Gold Perspective
- relevance label
- Gold Strategy
- Ground Truth 파일 내용
- case strategy / implementation / outcome

출력:
- ranked Case IDs
- 간단한 relevance reason(평가용 ranking과 별도 저장)

GPT-only도 100개 Case 전체를 판단하므로 BM25/Dense가 100개 Case를 score하는 것과 corpus access 범위는 동일하다.

LLM 공정성 원칙:
- GPT-only와 Runtime Perspective Generator는 **같은 LLM 모델/버전**을 사용한다.
- 이렇게 해야 LLM 능력 차이가 아니라 `direct judgment`와 `perspective decomposition + retrieval` 구조 차이를 비교하기 쉽다.

`REVIEW_REQUIRED`:
- ~~공통 LLM 모델명/버전~~ → **GPT-5.6 Luna (APPROVED)**
- 1회 deterministic 실행 또는 3회 반복 실행

---

### P1. Multi-Perspective + BM25 — Diagnostic

```text
Business Problem Query
→ LLM Perspective Decomposition
→ P1 ... Pk
→ 각 Perspective를 BM25로 검색
→ branch-preserved unique case set
```

목적:
- Multi-Perspective 효과가 Dense Retriever에만 의존하는지 확인
- Single BM25와 같은 lexical backbone에서 Perspective 분해 효과 측정

이 조건은 제안모델 전체가 아니라 **Perspective decomposition ablation/diagnostic**으로 해석한다.

---

### P2. Multi-Perspective + Dense — Primary Proposed Stage 1

```text
Business Problem Query
→ LLM Perspective Decomposition
→ P1 ... Pk
→ 각 Perspective를 같은 Dense Encoder로 검색
→ branch-preserved unique case set
```

B2와 같은 Dense backbone을 사용한다.

따라서:

`Single Dense vs Multi-Perspective Dense`

비교가 RQ1에서 Perspective decomposition 자체의 효과를 가장 직접적으로 보여준다.

---

## 6. Runtime Perspective Generation

Ground Truth Reference Perspective를 LLM에게 제공하지 않는다.

LLM 입력:
- Business Problem Query only
- Perspective 생성 규칙

모델:
- GPT-only와 **동일한 LLM 모델/버전 사용**
- 공통 LLM 모델: **GPT-5.6 Luna (APPROVED)**

LLM에게 요구하는 Perspective:
- 문제관점이어야 함
- 해결방법/제품/Strategy를 미리 제안하지 않음
- 서로 단순 동의어가 아니어야 함
- Query에 직접 근거해야 함
- 필요한 수만 생성

### 개수

Runtime 원칙은 고정 3개가 아니다.

초안 실험 제약:
- 최소 2개
- 최대 5개
- Query에 따라 동적으로 결정

상·하한은 실험 안정성 및 Search Budget 통제를 위한 실험조건이다.

결정: **Runtime Perspective 2~5개 동적 생성으로 APPROVED**

### 출력 Schema

```json
{
  "perspectives": [
    {
      "id": "P1",
      "title": "...",
      "description": "..."
    }
  ]
}
```

각 실행에서 다음을 반드시 저장:
- 원 Query
- 생성 Perspective 수
- title / description
- LLM model/version
- prompt version/hash
- temperature
- 실행 ID

---

## 7. Search / Output Budget

Multi-Perspective가 단순히 더 많은 결과를 가져와서 유리해지는 것을 방지한다.

### 평가 K

초안:
- K = 5
- K = 10
- K = 20

즉:
- Recall@5 / @10 / @20
- Perspective Coverage@5 / @10 / @20
- Strategy Coverage@5 / @10 / @20

결정: **K={5,10,20}으로 APPROVED**

### Single-query
각 방식은 100 Case를 score/rank하지만 평가 시 상위 K개 unique Case만 사용한다.

### Multi-Perspective
각 branch에서 ranking을 만들되 최종 평가에는 **동일하게 K개의 unique Case만 사용**한다.

초안 branch-preserved selection:
1. 각 Perspective branch의 ranking을 유지한다.
2. branch를 순환하며 각 branch의 최고순위 미선택 Case를 1개씩 채택한다.
3. 중복 Case는 한 번만 센다.
4. K개의 unique Case가 될 때까지 반복한다.
5. branch identity는 별도로 저장한다.

이 방식은 RRF가 아니며 가중점수 융합도 사용하지 않는다.

장점:
- 한 branch가 모든 slot을 독점하지 않음
- 최종 출력 수는 Single-query와 동일
- Perspective branch preservation 자체를 직접 평가 가능

결정: **branch-balanced unique selection으로 APPROVED**

---

## 8. 핵심 평가 지표

### 8.1 Recall@K — Primary

Query q의 Gold Relevant Case union을 `G_q`, 모델 Top-K를 `R_q@K`라 하면:

```text
Recall@K = |G_q ∩ R_q@K| / |G_q|
```

10개 Dev Query에 대해:
- Query별 값 저장
- Macro Average 저장

---

### 8.2 Perspective Coverage@K — Primary/Auxiliary

Reference Perspective p의 relevance >=3 Case가 Top-K 안에 하나 이상 존재하면 해당 Perspective를 covered로 판정한다.

```text
Perspective Coverage@K
= covered Reference Perspectives
  / total Reference Perspectives
```

주의:
- Reference Perspective는 Runtime 생성 Perspective와 동일할 필요가 없음
- Reference에 없는 Generated Perspective는 자동 오답으로 간주하지 않음

---

### 8.3 Strategy Coverage@K

Retrieved Top-K Case들이 가진 frozen Strategy label의 union과 Query Gold Strategy Set을 비교한다.

```text
Strategy Coverage@K
= |Gold Strategy ∩ Retrieved-case Strategy|
  / |Gold Strategy|
```

Strategy는 검색 입력에는 포함하지 않고 평가에만 사용한다.

---

## 9. 진단 지표

핵심 성능지표와 별도로 Multi-Perspective가 실제로 무엇을 바꿨는지 확인한다.

### 9.1 Branch Result Overlap
- Perspective branch별 local Top-N Case set의 pairwise Jaccard
- 완전 동일 결과가 반복되는지 확인

### 9.2 Unique / Marginal Gold Recovery

Single Dense가 찾지 못했지만 Multi-Perspective Dense가 추가로 찾은 Gold Case 수:

```text
MP_unique_gold@K
= (MP@K ∩ Gold) - (SingleDense@K ∩ Gold)
```

반대로 Multi-Perspective 때문에 잃어버린 Gold도 함께 기록한다.

### 9.3 Generated Perspective Count
- Query별 k
- 평균 / 최소 / 최대

### 9.4 Duplicate Candidate Rate
- branch 결과 간 동일 Case 중복률

진단지표는 논문의 핵심 성공판정 지표와 구분해서 해석한다.

---

## 10. LLM 실행 안정성

BM25/Dense는 deterministic하게 실행한다.

LLM이 들어가는:
- GPT-only
- Multi-Perspective Perspective generation

은 실행 변동 가능성이 있다.

### 확정안
- Primary report: 동일 조건 **3회 독립 반복**
- Query별 각 Run metric을 모두 저장하고, summary에서는 mean / min / max 또는 mean ± std 기록
- LLM prompt와 model version 고정
- 가능한 경우 seed 기록
- temperature는 낮게 설정

`APPROVED`:
- repeats = **3** (Query별 독립 Run)

`REVIEW_REQUIRED`:
- temperature 값

Dev에서는 안정성을 확인하고, Held-out Test 전에 실행규칙을 Freeze한다.

---

## 11. 결과 저장 Schema

### 11.1 Ranking 결과

각 실행 결과는 최소 다음 필드를 저장한다.

```text
experiment_id
run_id
query_id
system
model
config_version
prompt_version
perspective_id
perspective_text
rank
case_id
score
selected_in_final_k
timestamp
```

### 11.2 Metric 결과

```text
experiment_id
run_id
query_id
system
k
recall
perspective_coverage
strategy_coverage
unique_gold_recovery
generated_perspective_count
```

### 11.3 Summary

System별:
- Mean Recall@K
- Mean Perspective Coverage@K
- Mean Strategy Coverage@K
- Query별 delta
- LLM 반복실행 variability

을 저장한다.

---

## 12. Dev 결과 해석 원칙

Dev Query가 10개뿐이므로 Dev 결과에 과도한 통계적 일반화를 하지 않는다.

Dev 단계 목적:
- 구현 오류 탐지
- Prompt / 모델 / K / budget 규칙 검토
- Multi-Perspective가 추가 Gold를 실제로 회수하는지 확인
- 다음 아키텍처 단계로 넘어갈 조건 확인

권장:
- Macro mean
- Query별 결과
- paired delta
- 분산/실패사례 분석

통계적 유의성은 Held-out Test 설계와 표본규모를 확정한 후 별도로 판단한다.

---

## 13. Stage 1 성공/실패 판단

Multi-Perspective가 의미 있다고 보기 위한 중심 판단:

1. Single Dense 대비 Recall@K가 일관되게 개선되는가
2. Perspective Coverage@K가 개선되는가
3. Single Dense가 놓친 Gold Case를 추가 회수하는가
4. branch overlap이 100%로 반복되지 않는가
5. 동일 K output 조건에서도 이득이 유지되는가

가능한 결과:

### A. Multi-Perspective 우세
→ Multi-view / Gated Fusion / Hybrid Retrieval 단계로 진행

### B. Recall은 비슷하지만 Coverage 증가
→ 관점 보존 가치가 있는지 후속 분석

### C. 차이 없음
→ Perspective prompt / branch selection / Query 특성 분석

### D. 오히려 악화
→ Multi-Perspective가 핵심 Gold를 분산시키는 원인 분석

어떤 결과도 Ground Truth를 수정해서 맞추지 않는다.

---

## 14. 구현 순서

```text
[0] Experiment Spec Freeze
        ↓
[1] Common Data Loader
        ↓
[2] Common Evaluation Engine
        ↓
[3] Single-query BM25
        ↓
[4] Single-query Dense
        ↓
[5] GPT-only
        ↓
[6] Perspective Generator
        ↓
[7] Multi-Perspective + BM25
        ↓
[8] Multi-Perspective + Dense
        ↓
[9] Common Metrics / Diagnostics
        ↓
[10] Dev Result Review
        ↓
[11] RQ1 Config Freeze
        ↓
[12] Next-stage Multi-view experiment
```

평가기부터 먼저 구현하여 모든 시스템이 동일한 Ground Truth/metric 함수를 사용하도록 한다.

---

## 15. 재현성

모든 실험에 다음을 저장한다.
- Git commit SHA
- Dataset / Ground Truth freeze version
- Python version
- package lock/version
- random seed
- model exact name/version/revision
- prompt text/version/hash
- config file
- execution timestamp
- machine/device 정보(CPU/GPU)

API key, token 등 secret은 Git에 저장하지 않는다.

---

## 16. 승인 전 확인할 항목

사용자 검토가 필요한 값:

1. ~~Primary Query를 `business_problem_query only`로 할지~~ → **APPROVED: Business Problem only**
2. ~~BM25 Korean tokenizer~~ → **APPROVED: Kiwi**
3. ~~Dense baseline model = `BAAI/bge-m3`~~ → **APPROVED: BAAI/bge-m3**
4. ~~K = {5, 10, 20}~~ → **APPROVED: {5, 10, 20}**
5. ~~Runtime Perspective = 2~5개~~ → **APPROVED: 동적 2~5개**
6. ~~branch-balanced unique selection 방식~~ → **APPROVED**
7. ~~GPT-only + Perspective Generator 공통 LLM 모델~~ → **APPROVED: GPT-5.6 Luna**
8. ~~LLM 반복 횟수 = 3~~ → **APPROVED: Query별 3회 독립 실행**
9. LLM temperature
10. Dev Stage 1 성공판정 해석

이 항목을 사용자와 확정한 뒤 본 문서를 `FROZEN` 상태로 바꾸고 구현을 시작한다.
