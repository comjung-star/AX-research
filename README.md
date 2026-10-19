# AX-research
기업 업무문제 기반 다중관점 AX 사례 추천 모델 연구

## Documents

- [연구계획서](docs/research-plan.md)
- [아키텍처 정리](docs/architecture.md)
- [실험 로드맵](docs/experiments.md)
- [작업일지](worklog/README.md)

## Repository Structure

```text
AX-research/
├─ AGENTS.md
├─ README.md
├─ docs/
├─ data/
├─ worklog/
├─ src/
├─ configs/
├─ experiments/
├─ tests/
└─ notebooks/
```

## Current Step

### 완료

- 교수 제안 아키텍처 기준 연구 방향 확정
- RRF / Weighted-RRF 폐기
- Core Pilot 42건 검증 완료
- Root Cause Dictionary v1 9종 Freeze
- Strategy Taxonomy v1 6종 Freeze
- 공개 PDF/XLSX 사례원천 검증
- 『실전 AX 리포트』 PART 5 13개 사례 검증 완료
  - Main 7건
  - Supplemental 1건
  - HOLD 5건
- Main Dataset v1 **100건 구축 및 Freeze**
- Main QA Metadata **100건**
- Supplemental Public **4건**

### 현재 단계

**Retrieval Ground Truth 구축**

Main Dataset v1은 AX0001~AX0100의 100건으로 고정해 검색·추천 실험에 사용한다.

다음 작업:
1. 평가용 Business Problem Query 설계
2. Query별 Multi-Perspective 정답 관점 정의
3. Perspective × Case 관련도 0~4 라벨링
4. Gold Relevant Cases / Gold Strategy Set 확정
5. Single-query Dense Retrieval baseline 구축
