# Data

AX 사례 데이터셋과 평가용 정답 데이터를 관리하는 영역입니다.

## Documents

- [데이터 스키마 및 작성 기준](schema.md)
- [Core Pilot 사례 데이터셋 42건](pilot_cases.csv)
- [Main Dataset v1 — 100건](main_cases_v1.csv)
- [Main Dataset v1 QA — 100건](main_qa_metadata_v1.csv)
- [Main Dataset v1 최종 검증](main_dataset_validation_v1.md)
- [Main Dataset v1 분포](main_dataset_distribution_v1.csv)
- [Supplemental 공공부문 사례 4건](supplemental_public_cases.csv)
- [실전 AX 리포트 PART 5 검증표](ax_report_part5_validation.csv)
- [실전 AX 리포트 PART 5 검증 결과](ax_report_part5_review.md)
- [공개 PDF/XLSX Source Screening](public_source_screening.md)
- [Main 후보 Pool](main_candidate_pool.csv)
- [Supplemental 후보 Pool](supplemental_candidate_pool.csv)
- [데이터 원천 카탈로그](source_catalog.md)
- [Pilot 데이터 검증 결과](pilot_validation.md)
- [Pilot QA 메타데이터](qa_metadata.csv)
- [Root Cause Factor Dictionary](root_cause_factors.csv)
- [Root Cause Dictionary v1 snapshot](root_cause_factors_v1.csv)
- [Strategy Taxonomy](strategy_taxonomy.csv)
- [Strategy Taxonomy v1 snapshot](strategy_taxonomy_v1.csv)
- [Taxonomy Freeze v1](taxonomy_freeze_v1.md)
- [Retrieval Ground Truth Protocol v0.1](ground_truth_protocol.md)
- [Retrieval Query Draft v0.1](retrieval_queries_v0.1.csv)
- [Perspective × Case Relevance v0.1](perspective_case_relevance_v0.1.csv)
- [Retrieval Gold v0.1](retrieval_gold_v0.1.csv)

## 기본 원칙

- 원문 전체를 무단으로 저장하지 않습니다.
- 구조화된 연구용 필드, 라벨, 메타데이터, 출처 정보를 중심으로 관리합니다.
- 사내 비공개 정보와 개인정보를 저장하지 않습니다.
- 원문에 없는 값은 임의 생성하지 않고 `UNKNOWN` 등으로 명시합니다.
- Blind RCA는 Problem View만 사용합니다.
- Main Dataset v1은 Ground Truth/모델 실험 동안 AX0001~AX0100으로 고정합니다.

핵심 필드:

```text
Case ID
Industry
Business Problem
AX Target / Task
Business Context / Condition
Root Cause Factor
Strategy
AI Technology
Implementation
Outcome
Source
```

## Current Status

- Pilot: 42건 / PASS
- Main Dataset v1: **100건 / PASS / FROZEN**
- Main QA: **100건**
- Supplemental: **4건**
- Root Cause v1: 9종
- Strategy v1: 6종
- Retrieval Ground Truth: **Protocol v0.1 / Query Draft 10건 생성**
- Perspective × Case 0~4 라벨링: **다음 작업**
- 다음 단계: **Ground Truth Pilot 라벨링 및 Gold 확정 규칙 검증**
