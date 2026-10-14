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

Pilot 검증을 **42건**으로 마무리했습니다.

현재까지:
- Core Pilot 42건
- Supplemental Public 3건
- 공식/공개 원천 기반 구조화
- Problem / Task / Context 분리
- Blind RCA
- Root Cause Dictionary v1 **9종 Freeze**
- Strategy Taxonomy v1 **6종 Freeze**
- QA metadata 기록
- Pilot Validation **PASS**

이제 Pilot 단계는 종료하고 **Main Dataset v1 100~150건 구축**으로 이동합니다.

Main Dataset에서는 Freeze된 v1 기준을 동일하게 적용하며, 새로운 패턴이 반복적으로 확인되는 경우에만 기존 v1을 덮어쓰지 않고 v2 후보로 별도 관리합니다.
