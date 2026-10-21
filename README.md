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

현재 진행:
- GTQ001: 300개 라벨 + Adjudication + Pilot Gold 확정
- GTQ002: 300개 라벨 + Adjudication + Pilot Gold 확정
- 누적 Perspective × Case 라벨: **1200개**
- GTQ001~GTQ004 Dev/Pilot Gold 확정 및 Ground Truth 규칙 재현성 확인
- GTQ003에서 관점별 고유 Gold Case 확인(P2-only 5건 / P3-only 2건)

다음 작업:
1. GTQ005~GTQ010 Perspective × Case 관련도 0~4 라벨링
2. Query별 Gold Perspective / Gold Relevant Cases / Gold Strategy Set 확정
3. Ground Truth v1 Freeze
4. 동일 Search Budget에서 Single-query BM25 / Dense Retrieval / GPT-only baseline 구축
5. Recall@K / Perspective Coverage@K / Strategy Coverage@K 비교


### Evaluation split clarification (2026-10-20)

- `GTQ001~GTQ010`: Dev/Pilot Query
- Final Held-out Test: model/prompt/evaluation rule Freeze 후 별도 생성
- Gold Perspective: closed category가 아니라 Reference Perspective(최소 기준 관점)
- Runtime: LLM이 Query마다 `P1...Pk`를 동적으로 생성
- Reference에 없는 Generated Perspective도 자동 오답 처리하지 않고 Query grounding / redundancy / 추가 relevant-case 회수를 검토


### Dev Ground Truth milestone — 2026-10-21

- GTQ001~GTQ010 Active Dev Query: **10/10 Adjudicated**
- Perspective × Case relevance: **3000 labels**
- Low-discrimination Pilot Query는 Archive에 보존하고 screening을 통과한 replacement Query로 교체
- Ground Truth는 Runtime 입력이 아니라 평가 Benchmark
- 다음 실험: Single-query BM25 → Dense → GPT-only → Multi-Perspective 비교
