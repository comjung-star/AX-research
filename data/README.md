# Data

AX 사례 데이터셋을 관리하는 영역입니다.

## Documents

- [데이터 스키마 및 작성 기준](schema.md)
- [Pilot 사례 데이터 입력 템플릿](pilot_cases.csv)

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

초기에는 20~30건의 Pilot Set부터 구성한 뒤 전체 100~150건으로 확대합니다.
