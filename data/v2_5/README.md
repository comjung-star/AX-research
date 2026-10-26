# v2.5 전체 수집 자료 등록본

다음 작업자는 저장소 루트의 [HANDOFF.md](../../HANDOFF.md)를 먼저 읽으세요.

공공·기업·개인·교육·연구·비영리·구분 미확인 자료를 모두 포함했습니다. 기존 108개 업무와 추가 입력 11,658개를 합친 전체 등록본은 **11,766개 기록**이며, 텍스트와 중복 대표 연결을 고려한 인덱스 대상은 **9,416개**입니다. 고유 AX 성공사례 수가 아닙니다.

- [전체 CSV](main_cases_v2_5.csv) · [검색 대상 CSV](retrieval_cases_v2_5.csv) · [JSON](main_cases_v2_5.json)
- [요약](review_summary.json) · [모든 입력 포함 대조](all_input_coverage.csv) · [해시](release_manifest.json)
- [원천 CSV 5,961개 행 대조](structured_row_audits.json)

`business_scope`/`업무구분`, 운영 단계, AI 여부, 기록 유형, 확인 수준을 컬럼으로 표시했습니다. 자동 분류·원천 보고·개별 AI 검토와 인간 정답은 구별해야 합니다. 이전 파서의 오류 이력 11개를 보존하고 표준 CSV 읽기로 누락 9개를 복원했습니다. 원천 CSV와 기존 동결본은 덮어쓰지 않았습니다.

**인수인계 시점에는 전체 BGE-M3 NPZ와 실제 앱 전환이 아직 미완료입니다.** 전체 등록본이 있다는 이유로 이미 전체 Dense 검색이 동작한다고 해석하지 마세요. `scripts/index_ax_inclusive_release.py`와 `scripts/validate_ax_inclusive_release.py`가 다음 실행 대상입니다. 모델·키·개인 평가 DB는 Git에 포함하지 않습니다.
