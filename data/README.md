# Data

AX 사례 데이터셋을 관리하는 영역입니다.

## Documents

- [데이터 스키마 및 작성 기준](schema.md)
- [Core Pilot 사례 데이터셋 42건](pilot_cases.csv)
- [공개 PDF/XLSX Source Screening](public_source_screening.md)
- [Supplemental 후보 Pool](supplemental_candidate_pool.csv)
- [Main 후보 Pool](main_candidate_pool.csv)
- [Main Dataset v1 QA](main_qa_metadata_v1.csv)
- [Main Dataset v1 — 현재 52건](main_cases_v1.csv)
- [Supplemental 공공부문 사례 3건](supplemental_public_cases.csv)
- [데이터 원천 카탈로그](source_catalog.md)
- [Pilot 데이터 검증 결과](pilot_validation.md)
- [Pilot QA 메타데이터](qa_metadata.csv)
- [Root Cause Factor Dictionary](root_cause_factors.csv)
- [Root Cause Dictionary v1 snapshot](root_cause_factors_v1.csv)
- [Strategy Taxonomy](strategy_taxonomy.csv)
- [Strategy Taxonomy v1 snapshot](strategy_taxonomy_v1.csv)
- [Taxonomy Freeze v1](taxonomy_freeze_v1.md)

## 기본 원칙

- 원문 전체를 무단으로 저장하지 않습니다.
- 구조화된 연구용 필드, 라벨, 메타데이터, 출처 정보를 중심으로 관리합니다.
- 사내 비공개 정보와 개인정보를 저장하지 않습니다.
- 원문에 없는 값은 임의 생성하지 않고 `UNKNOWN` 등으로 명시합니다.

예정 핵심 필드:

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

Core Pilot 42건과 Supplemental Public 3건의 Pilot 검증을 완료했고, Root Cause Dictionary v1(9종)과 Strategy Taxonomy v1(6종)을 Freeze했습니다. 공개 PDF/XLSX 원천을 추가 분석해 검증된 10건을 Main Dataset v1에 편입했으며 현재 Main Dataset은 52건입니다. 다음 목표는 동일한 v1 기준으로 100~150건까지 확장하는 것입니다.
