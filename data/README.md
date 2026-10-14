# Data

AX 사례 데이터셋을 관리하는 영역입니다.

## Documents

- [데이터 스키마 및 작성 기준](schema.md)
- [Core Pilot 사례 데이터셋 34건](pilot_cases.csv)
- [Supplemental 공공부문 사례 3건](supplemental_public_cases.csv)
- [데이터 원천 카탈로그](source_catalog.md)
- [Pilot 데이터 검증 결과](pilot_validation.md)
- [Pilot QA 메타데이터](qa_metadata.csv)
- [Root Cause Factor Dictionary](root_cause_factors.csv)
- [Strategy Taxonomy](strategy_taxonomy.csv)

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

현재 Core Pilot 34건과 Supplemental Public 3건을 확보했습니다. 출처 다양화용 사례 6~10건을 추가 검증한 뒤 Root Cause Dictionary v1과 Strategy Taxonomy v1을 Freeze하고 Main Dataset 100~150건으로 확대합니다.
