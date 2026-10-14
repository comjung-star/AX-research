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

Core Pilot을 **34건**으로 확장했고, 공공부문 Supplemental 사례 **3건**을 별도로 확보했습니다.

현재까지:
- 공식/공개 원천 기반 구조화
- Problem / Task / Context 분리
- Blind RCA
- Root Cause Factor 9종 재검증
- Strategy Taxonomy 6종 재검증
- QA metadata 기록

다음 단계는 NIPA 등 다른 국내 원천에서 **출처 다양화용 6~10건**을 보완한 뒤 Root Cause Dictionary v1과 Strategy Taxonomy v1을 Freeze하는 것입니다.
