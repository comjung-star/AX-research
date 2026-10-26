# FAME-AX v2.6 실험 입력

원문 근거가 연결된 AI 업무 사례 **117건**을 사용하는 AI-Silver 검색 실험 자료다. 전체 원천 등록 11,766건과 검색 후보 9,416건을 검증 완료 사례 수로 사용하지 않는다. 이전 v2.3 84건, v2.4 108건, v2.5 및 과거 실험은 수정하지 않았다.

## 준비 범위

- 사례의 문제·대상·맥락과 해결·성과를 분리한다. `case_features.csv`에는 검색 입력만 있고 구현·성과·원인·전략·정답은 없다.
- `cases.json`은 출처·근거 위치·원문 검토 방식·운영 보고 수준을 보존한다. 공급사·기관의 운영·성과 보고는 독립 실측으로 승격하지 않는다. 수치 성과가 없는 사례도 명시적으로 유지한다.
- 관련성은 Dev 3,510쌍·Test 3,510쌍을 독립 AI 2개가 각각 판단한 뒤 모든 점수 차이를 조정했다. 원시 판정 14,040개와 조정 근거는 `../final_dataset_audit_20261026/`에 있다.
- 원인 라벨은 Problem-only, 전략은 implementation/outcome-only 독립 검토다. 모호한 라벨은 ABSTAIN으로 남기며 학습용 음성값으로 채우지 않는다. 세부 사용 가능 수는 `release_report.json`에 있다.
- 기존 Dev 10질문과 신규 합성 Test 12질문을 분리했다. Test는 검색 비교 프로토콜 해시 동결 뒤 작성했으며 순위를 보고 만들거나 튜닝하지 않았다. 사례 코퍼스를 공유하는 질의 단위 시험이다. 새 기관 일반화·실제 외부 사용자 질의 시험으로 해석하지 않는다.
- 87개 기관/출처 누수 그룹과 보조 5-fold를 제공한다. 같은 그룹의 업무를 서로 다른 fold에 넣지 않는다. 보조 fold는 노출되지 않은 최종 사례 Test가 아니다.

## 파일

| 파일 | 사용 |
|---|---|
| `case_features.csv`, `case_bge_m3_128.npz` | 117개 P/T/C 검색 입력·정규화 3-view 벡터 |
| `case_labels.csv` | 원인·전략 다중 라벨 및 ABSTAIN 상태 |
| `dev_queries.csv`, `test_queries.csv` | 실행 질의 텍스트 |
| `*_reference_perspectives.json`, `*_qrels.csv` | 평가 전용 reference 및 모든 사례의 0–4 관련성; 실행 프롬프트에 넣지 않음 |
| `reference_strategy_sets.csv` | 관련 사례 확정 후 도출한 종속 AI-Silver 전략 reference |
| `case_group_cv_folds.csv` | 기관·출처 그룹을 지키는 보조 학습 검증 분할 |
| `wald_input.csv`, `wald_sparsity.csv` | 두 라벨이 있는 사례와 77개 원인–전략 조합의 표본 희소성; 인과 증거 아님 |
| `registry_dispositions.csv` | 원본 11,766건의 이전 이유·근거 ID·필드 검사와 현재 사용 여부; 보류를 사실검증 완료로 표시하지 않음 |
| `criteria.json`, `manifest.json`, `environment.json` | 포함 기준·SHA-256·실제 실행 환경 |

## 이 PC에서 재현

프로젝트 루트에서 실행한다. 기존 `.venv`와 로컬 BGE-M3를 사용하며 아래 Dev 검사는 유료 API를 호출하지 않는다.

```powershell
$env:PYTHONPATH='src;.'
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe -m scripts.validate_final_research_dataset
.\.venv\Scripts\python.exe -m scripts.run_final_dataset_baselines --split dev
.\.venv\Scripts\python.exe -m scripts.run_final_dataset_checks
```

Dev 기준선 실제 결과는 `../../docs/prototype-validation/final-dataset-baselines/dev/`, 검사 로그는 `../../docs/prototype-validation/final-dataset-checks/`에 저장한다. 같은 자료·정답·가중치·평가 기준으로 비교한다. BGE-M3는 1024차원, 각 View 128토큰, 정규화, 세 View cosine의 같은 비중 평균이며 BM25는 고정 Kiwi 설정을 쓴다. 이 결과는 전체 FAME-AX 학습형 모델의 성능을 입증하지 않는다.

저장된 판정에서 패키지를 다시 만들 때는 아래 순서를 사용한다. 판정 자체를 새로 생성하거나 수정하는 명령은 아니다. manifest 생성 시각은 재실행 시 바뀌며, 동결 입력·판정·데이터 내용 해시는 유지돼야 한다.

```powershell
.\.venv\Scripts\python.exe -m scripts.merge_final_adjudications --split dev
.\.venv\Scripts\python.exe -m scripts.merge_final_adjudications --split test
.\.venv\Scripts\python.exe -m scripts.compare_final_labels
.\.venv\Scripts\python.exe -m scripts.build_final_research_dataset
.\.venv\Scripts\python.exe -m scripts.validate_final_research_dataset
```

다른 PC는 `requirements-lock.txt`의 실제 실행 버전을 참고한다. 원래 `requirements-rq1.txt`의 OpenAI SDK 최소 버전과 이 PC의 설치 버전은 다르므로 이 파일들을 동시에 설치하지 않는다. 현재 검증한 로컬 Dev 기준선은 OpenAI API를 쓰지 않는다. BGE-M3 가중치는 저작권·용량상 Git에 복제하지 않으며 `environment.json`과 `index_provenance.json`의 SHA로 식별한다. 파일 검사와 저장된 벡터를 쓰는 Dev 실행에는 모델 재다운로드가 필요하지 않다.

## 최종 Test 사용

데이터 준비 과정에서 Test 검색을 실행하지 않았다. 실제 비교 모델의 정확한 가중치·프롬프트·코드·추론 예산을 추가로 봉인한 뒤 한 번에 비교한다. 현재 기준선만 처음 실행하려면 `--split test --release-heldout`를 명시한다. 그 결과를 본 뒤 모델·라벨·질의·임계값을 조정하면 해당 결과를 동일한 미노출 최종 Test 성적으로 다시 보고하지 않는다.

전체 FAME-AX의 학습·최종 평가와 유료 LLM 호출은 이 데이터 준비 작업의 실행 완료 항목이 아니다. 이 PC에서 생성형 로컬 모델은 확인되지 않았으며, 사용 가능한 로컬 모델은 BGE-M3 인코더다.

## 논문에서 지켜야 할 한계

사람이 확인한 Gold는 0건이다. AI 간 일치율은 사람 정답 대비 정확도가 아니다. 새 Test는 사례 분야를 아는 AI가 작성한 합성 질의여서 외부 일반화에 한계가 있다. 전체 등록 자료 중 보류·참고 항목까지 모두 개별 사실검증한 자료로 발표해서는 안 된다. 공급사 성과 보고를 독립 효과 검증·인과 효과로 바꾸지 않는다. Wald는 희소 셀·같은 기관의 의존성·다중 비교를 점검한 연관성 분석으로 한정한다.

이전 감사에서 사람의 연구 승인까지 하나의 최종 건수에 묶어 0으로 표시한 기록은 역사적 상태로 남긴다. 본 릴리스는 실제 완료한 AI-Silver 데이터 준비와 사람의 최종 논문 승인을 별도로 표시한다. 연구자 승인 파일을 대신 작성하지 않는다.
