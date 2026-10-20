# AX-research
기업 업무문제 기반 다중관점 AX 사례 추천 모델 연구

## Documents

- [연구계획서](docs/research-plan.md)
- [아키텍처 정리](docs/architecture.md)
- [실험 로드맵](docs/experiments.md)
- [작업일지](worklog/README.md)
- [학습용 쉬운 설명](study/README.md)

## Repository Structure

```text
AX-research/
├─ AGENTS.md
├─ README.md
├─ docs/
├─ data/
├─ worklog/
├─ study/
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
- 교수 Word 코멘트(BM25/Dense 단일질의 한계) 연구계획서 반영 완료
- 평가 기준에 Single-query BM25 및 Perspective Coverage@K 반영

### 현재 단계

**Retrieval Ground Truth 구축**

Main Dataset v1은 AX0001~AX0100의 100건으로 고정해 검색·추천 실험에 사용한다.

다음 작업:
1. Ground Truth 라벨링 규칙 및 평가용 Business Problem Query 설계
2. GTQ001 Perspective Adjudication 및 Gold 관점 확정
3. GTQ001 Pilot 300개 라벨 검토 후 GTQ002~GTQ010으로 확대
4. Gold Relevant Cases / Gold Strategy Set 확정
5. 동일 Search Budget에서 Single-query BM25 / Dense Retrieval / GPT-only baseline 구축
6. Recall@K / Perspective Coverage@K / Strategy Coverage@K 비교
