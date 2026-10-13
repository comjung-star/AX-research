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

먼저 20~30건 규모의 Pilot AX 사례 데이터셋과 Ground Truth 기준을 정리한 뒤, Single-query Dense Retrieval baseline부터 구현합니다.
