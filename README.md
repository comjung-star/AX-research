# AX-research
기업 업무문제 기반 다중관점 AX 사례 추천 모델 연구

## Documents

- [연구계획서](docs/research-plan.md)
- [아키텍처 정리](docs/architecture.md)
- [실험 로드맵](docs/experiments.md)

## Repository Structure

```text
AX-research/
├─ AGENTS.md
├─ README.md
├─ docs/
│  ├─ research-plan.md
│  ├─ architecture.md
│  └─ experiments.md
├─ data/
│  └─ README.md
├─ src/
│  └─ README.md
├─ configs/
│  └─ README.md
├─ experiments/
│  └─ README.md
├─ tests/
│  └─ README.md
└─ notebooks/
   └─ README.md
```

## Current Step

Pilot 검증 42건을 완료하고 Root Cause Dictionary v1(9종) / Strategy Taxonomy v1(6종)을 Freeze했습니다.

공개 PDF/XLSX 원천(KOSA, NIA, Deloitte, WEF, Federal Reserve 등)을 추가 분석해 기존 42건과 중복을 제거했고, 10건을 검증 후 **AX0043~AX0052**로 Main Dataset v1에 편입했습니다.

현재:
- Core Pilot: 42건 (완료)
- Supplemental Public: 3건
- Main Dataset v1: **52건**
- Main 후보 HOLD/REVIEW: 6건
- Public source screening / QA metadata 기록 완료

다음 목표는 동일한 v1 기준으로 Main Dataset을 **100~150건**까지 확장하는 것입니다. 『실전 AX 리포트』 EPUB가 제공되면 기존 52건과 중복 제거 후 다음 편입 배치로 사용합니다.
