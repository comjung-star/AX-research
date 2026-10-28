# 2026-10-28 BGE-M3 의미 기반 기능 매핑

- 기준 SHA: be64f9c1f742ecaa6410eeaab97da11ebc6e7f13.
- 브랜치: research/query-case-semantic-mapping-20261028.
- 기존 AX-stage123-v3의 깨끗한 기준 체크아웃을 재사용했다. 다른 작업 폴더의 미커밋 파일은 건드리지 않았다.
- configs/semantic_mapping_20261028.json과 protocol.md에 필드 추출·가중치·집계·정렬·결합·평가 분모를 먼저 고정했다.
- 사전봉인: 5035e0d97cb903b9f94c5d5f5d141ef2d5783dfd58c83309151fe2fddb4e7ee3.
- 예측봉인: 59c67315ac3e3b299d7ae2aaafc62bb8d518aa0632f12367ecb27edea2221e5c.
- 로컬 기존 BGE-M3로632개 고유 필드 문장, 1024차원 정규화 CLS 생성. 최대75토큰, 잘림0.
- 118경로×112사례=13,216쌍. 새8조건 합계160개 질문/회차별 전체순위. 과거18조건과 합계26조건 비교.
- 의미 단독 F1@5/10/20=38.7566/31.4413/20.6908%. 규칙46.0979/34.0054/23.2511%. 결합47.5794/35.6721/23.2511%.
- 결합 개선은 Q1에만 관찰. 33개 미인식 사례에 기존 Silver 양성이0쌍이라 회복 효과 판정불가. Output 비교0쌍도 명시.
- 결과 저장 후 inference/config/frozen evaluation은 수정하지 않고 후속 분석 및 재생 검증 테스트만 추가했다.
- 독립 Stage4 Test 접근0, 새 유료 API0, 새 라벨0, 파인튜닝0. 기존 tracked 파일 변경0.
- 결과: docs/query-case-semantic-mapping-2026-10-28/README.md 및 ANALYSIS_KO.md.
- Git 커밋·원격 push는 수행하지 않았다. 새 로컬 연구 브랜치의 파일로 저장했다.
