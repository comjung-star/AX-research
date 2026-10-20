# Experiment Plan

구성요소를 한 번에 모두 구현하지 않고 단계별로 효과를 검증합니다.

## 권장 진행 순서

1. Dataset / Retrieval Ground Truth 준비
2. Single-query BM25 baseline
3. Single-query Dense Retrieval baseline
4. GPT-only baseline
5. Multi-Perspective Query
6. Multi-view Embedding
7. View Combination
8. Hybrid Retrieval
9. Query-Case Interaction
10. Factor Anchor / Wald Evidence
11. Evidence Fusion / Recommendation Head
12. Ablation 및 최종 평가

## Ground Truth 원칙

- `GTQ001~GTQ010`은 Dev/Pilot Query로 사용하며 최종 Test Query와 분리합니다.
- 최종 Held-out Test Query는 모델·Prompt·평가규칙을 Freeze한 뒤 별도로 생성하고, Test 결과를 보고 모델을 다시 조정하지 않습니다.
- Main Dataset v1 `AX0001~AX0100`을 고정하여 사용합니다.
- 평가 Query와 Gold Label은 모델 검색결과와 분리된 절차로 구축합니다.
- Query별 Reference/Gold Perspective를 별도로 유지하되, 이를 가능한 모든 관점의 폐쇄형 목록으로 간주하지 않습니다.
- Runtime LLM은 Query마다 관점의 수와 종류를 동적으로 생성하며, Reference에 없는 관점도 Query 근거성·비중복성·추가 Relevant Case 회수 여부를 별도로 검토합니다.
- Perspective × Case 관련도는 0~4 척도로 기록하고, Gold threshold는 Ground Truth protocol에서 사전에 고정합니다.
- Retrieval 관련도 판정은 Problem View를 중심으로 하여 Solution View 누출을 최소화합니다.
- Gold Relevant Cases 확정 후 frozen Strategy taxonomy를 이용해 Gold Strategy Set을 구성합니다.

## 핵심 평가 지표

- `Recall@K`
- `Perspective Coverage@K`
- `Strategy Coverage@K`

Baseline과 제안모델은 동일한 Search Budget / 출력 건수 조건에서 비교합니다.

## 평가 데이터 분리

```text
Dev/Pilot Query (GTQ001~GTQ010)
→ Ground Truth/Prompt/모델 설계 검증
→ 모델·평가규칙 Freeze
→ 별도 Held-out Test Query + Ground Truth Freeze
→ 최종 평가
```

Test 결과를 본 뒤 모델을 수정해야 한다면 해당 Query는 Dev로 이동시키고 새로운 Held-out Test를 준비합니다.
