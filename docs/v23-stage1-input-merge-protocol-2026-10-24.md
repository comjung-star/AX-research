# Stage 1 검색 입력 및 결과 결합 진단 실험 — 사전 등록

작성일: 2026-10-24
상태: **PRE-RUN DESIGN FROZEN**

## 연구 질문
1. Stage 1 다중 관점 검색의 원문 정보 축약(제목만 사용)이 Recall@10 저하에 기여했는가?
2. 분기별 round-robin 결합이 상위 10건 관련도 확보에 영향을 주었는가?

## 절대 고정
- 확정 v2.3 사례 84개 및 Dev 문제 10개, AI 3회 독립평가 중앙값 2,520칸.
- 이전 Stage 1에서 생성된 97개 관점 (10문제 × 3회).
- 이전 Stage 1 당시 BGE-M3 문서 임베딩, 이진 정답 기준(>=3).
- 문제/Task/Context 이외의 Solution/Outcome/Strategy 라벨은 임베딩 및 검색 입력에 사용하지 않음.
- 이전 Stage 1 title_only+round_robin의 전체 관점별 순위(각84개), 최종 Top20(각30개)와 정확한 재현 요구.
- Fresh encoder vs saved title vector 내적 코사인 최소값 0.999 이상. 만족하지 않으면 모델 버전 불일치로 중단.

## 변경 요인: 3×2 완전 요인 설계
- Title only: 기존 `perspective_title` (control).
- Title + description: `perspective_title + perspective_description`.
- Query + title + description: `business_problem_query + perspective_title + perspective_description`.
- Branch-balanced round-robin: 각 관점 1건씩 가져오며 중복을 제외, 기존 방식.
- Reciprocal Rank Fusion (RRF60): 각 관점의 전체 순위에 대해 `sum(1/(60+rank))`, 높은 순서, 동점은 case_id.

총 6개 조합, 모든 조합의 후보 코퍼스/최대 검색 범위는 동일하며 관점당 84개 사례 전체에 순위 부여.
특정 변경 방식을 유리하게 만들기 위한 평가자료 재구성, 사후 가중치·하이퍼파라미터 조정 금지.

## 평가
- Primary: 10개 Dev 질의별 3회 평균을 구한 뒤, 질의 10개를 같은 가중치로 평균한 Recall@10.
- Secondary: Perspective Coverage@10 및 파생 Strategy Coverage@10, K=5/20 Recall, 분기별 상위 10개 중복도, 질문별 개선/손실/동률.
- 반복 3회를 독립 질의 30개로 처리하지 않음.
- 10개 질문 수준 paired bootstrap(고정 난수 20261024) 95% 변화량 구간은 진단 목적의 불확실성 참고값; 정식 통계적 확정 아님.
- 참조 관점에 정답사례가 하나도 없는 경우는 관점 Coverage 분모에서 제외, 기존 Stage 1 평가와 동일.
- 역사적 Title + RR 기반선의 모든 Top20 정확한 재현, Recall@10=0.4530 확인해야 유효.

## 결과 판정
- 기준선 대비 개선/악화를 **모두** 보존.
- 최대값이 나오더라도 별도 Held-out Test가 없는 개발 데이터 기준 성능임.
- 검색입력과 결과결합만의 효과로 해석할 수 있으며, 교수 제안 아키텍처의 모든 학습형 구성요소 우수성으로 확대하지 않음.
- v2.3 데이터셋/정답/기존 Stage1~4 실험결과는 변경하지 않음.
