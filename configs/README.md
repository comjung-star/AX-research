# Configs

모델과 실험 설정을 관리합니다.

## 현재 실험

- `experiment_rq1_v1_draft.yaml`
  - RQ1 Retrieval Experiment 명세에 대응하는 실행설정 초안
  - 아직 `DRAFT_FOR_REVIEW`
  - 사용자 승인 후 frozen config를 별도 버전으로 확정

관리 대상 예:
- embedding model
- BM25 tokenizer
- Top-K
- Search / Output Budget
- LLM model / temperature / repeat count
- random seed
- loss weight(후속 학습 단계)

하이퍼파라미터는 연구계획서의 확정값으로 간주하지 않고 **실험 설정**으로 관리합니다.

API key / token / credential은 이 폴더에 저장하지 않습니다.
