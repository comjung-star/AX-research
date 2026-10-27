# AX 연구·프로토타입 인수인계 · 2026-10-26

> **축소 논문 후속 감사:** `research/reduced-stage123-audit-20261026`의 [감사·중단 보고](docs/reduced-stage123-2026-10-26/README.md)와 [신규 프로토콜](docs/reduced-stage123-2026-10-26/protocol.md)을 먼저 확인한다. 신규 Stage1은 입력 감사 후 서로 다른 LLM3종 접근/독립라벨 미확보로 중단, Stage2/3 미실행, 최종 Test(Stage4) 봉인이다. 과거 Stage4 추천 Dev를 최종 Test로 해석하지 않는다. 아래 전체 인덱스 동작 확인은 검색 성능 검증 완료를 의미하지 않는다.

> 후속 상태: `research/v25-experiment-ready-20261026`에서 전체 9,416건 Dense 인덱스와 HTTP/브라우저 검색을 검증했다. 기록별 판정, Dev 112건과 미판정 qrels, 재현 실행은 [연구 입력 안내](data/v2_5/research/README.md), [당일 작업일지](worklog/2026-10-26.md)를 확인한다. 아래 본문과 `docs/handoff-state-2026-10-26.json`은 최초 인계 시점의 역사적 상태다. 신규 전수 사실검증과 최종 Test는 여전히 미완료다.

이 문서를 새 대화의 시작점으로 사용하세요. **현재 작업을 이어가기 위한 코드·원천 자료·판정 결과를 이 브랜치에 보존했습니다.** 전체 수집 자료의 등록과 점검은 끝났지만, v2.5 전체 Dense 인덱스 생성과 실제 앱 전환·최종 동작 검증은 아직 남아 있습니다.

## 1. 먼저 알아야 하는 사용자 결정

사용자는 처음에 신규 수집 자료를 기존 기업 업무 기준으로 검토·반영해 달라고 요청했습니다. 당시 기업 실제 운영만 적용해 24개를 추가한 것은 최종 요구가 아닙니다. 이후 사용자가 다음과 같이 명확하게 변경했습니다.

> “1차 2차 나누지말고 새로 수집한 모든 데이터 확인해달라는거야. SI 사업을 할때 공공기관도 SI 사업하니까 공공기관이라고 해서 따로 빼지말고 모두 추가해줘. 공공기관이나 기업업무가 아닌것도 다 포함시켜. 데이터셋에 컬럼을 하나 추가해서 업무기준을 따로 표시하던가”

따라서 **공공·기업·개인·교육·연구·비영리·구분 미확인 자료를 모두 포함**합니다. 기관 유형, 업무 범위, 운영/시험/계획/중단 단계, AI 여부를 제외 조건으로 사용하지 말고 컬럼으로 구분합니다. 개수를 예전 연구계획의 100~150건에 맞춰 제한하지 마세요. 기존 v2.3 84개와 과거 연구 결과는 그대로 보존합니다.

원문에 없는 업무 문제·구현·성과·원인·전략을 만들어 채우라는 뜻은 아닙니다. 참고자료, 링크, 미확인 값과 자동 분류를 명시하고, 고유 사례 수와 원천 기록 수를 혼동하지 마세요. 사용자 요청은 일부만 반영하고 다음 차수로 미루는 방식이 아니라 전체 입력을 끝까지 처리하는 것입니다.

정책 문서: [전체 자료 포함 정책](docs/inclusive-data-policy-2026-10-26.md).

## 2. 저장소와 작업 기준

- GitHub: `comjung-star/AX-research`, **비공개 저장소**. 공개 전환·main 병합·force push는 수행하지 않았습니다.
- 인수인계 브랜치: `handoff/ax-inclusive-20261026`.
- 작업 기준 커밋: `000b7f42f594bd4b57aa55df1661d7ff3750353c`.
- 기준 실험 브랜치: `experiment/v23-qci-256-four-step-20261024`.
- 확인 당시 `main`은 `dfe256a8e4554f8e6e65ed6cf32f43a7c6cd90b3`으로 더 이전 상태였습니다. **main만 읽으면 이 대화의 최신 연구·프로토타입 상태를 볼 수 없습니다. 이 인수인계 브랜치를 읽으세요.** 다른 실험 브랜치들은 변경하지 않았습니다.
- 로컬 프로젝트: `C:\Users\iovek\OneDrive\문서\ChatGPT\AI공부\AX-prototype`.
- 별도 기존 저장소 `...\AI공부\AX-research`는 이 작업의 실제 실행 폴더가 아닙니다.
- 바탕화면 실행파일: `C:\Users\iovek\OneDrive\바탕 화면\AX나침반.exe`. 이 프로젝트의 `run_prototype.py`를 실행하는 런처입니다.

## 3. 정확한 완료 상태

### 완료

| 항목 | 저장 결과 |
|---|---:|
| 기존 개별 검토 업무 | 108개 = frozen 84개 + v2.4 신규 24개 |
| 전체 추가 입력 기록 | 11,658개 |
| v2.5 전체 등록 기록 | **11,766개** |
| 텍스트가 있고 중복 대표 연결을 적용한 검색 인덱스 대상 | **9,416개** = 기존 108개 + 추가 9,308개 |
| 업무 범위로 제외한 기록 | **0개** |
| 웹 출처 접근 확인 | **5,686 / 5,686**, 누락 0 |
| 원천 CSV 행 대조 | **5,961개** = 미국 3,611개 + EU 2,350개 |
| 이 처리 과정의 유료 AI API 호출 | **0회** |

11,658개 입력의 구성은 기업 페이지 처리 기록 1,800개, 사례포털 기록 678개, 원천기관의 구조화 자료 5,961개, 기존에 URL만 발견했던 출처 3,208개, 예전 CSV 파서가 오류로 분리한 행·조각의 이력 11개입니다. 이력 11개는 정상 사례 11개가 아닙니다.

웹 접근 최종 결과는 `FETCHED` 3,826개, HTTP 오류·분량 제한 등 1,859개, 접근 실패 1개입니다. 본문 기준으로는 내용 점검 3,378개, 본문 부족 448개, 본문 접근 불가 1,860개입니다. 일시 실패의 재시도 결과를 **실제 저장 파일에서 다시 집계**했습니다. 옛 중간 progress 값에는 이미 복구된 실패가 남을 수 있으므로 최종 `page_check_summary.json`을 사용하세요.

전량 등록과 프로그램에 의한 스키마·원문 행·접근·본문 점검을 수행했습니다. 이것은 사람이 11,766개 기록의 사실을 전부 정밀 검증했다는 뜻이 아닙니다. 108개 개별 업무도 인간 Gold가 아닙니다.

### 아직 완료하지 않은 것 — 다음 대화의 우선 작업

1. `data/v2_5/inclusive_bge_m3.npz`와 `index_manifest.json` 생성.
2. `Engine(profile="inclusive")`로 전체 검색·업무 구분 필터·근거 없는 전략 생성의 자제를 실제 검증.
3. `scripts/validate_ax_inclusive_release.py`를 실행해 자유 입력 Dense, 평가 저장·내보내기, 자료 버전 보존 확인.
4. 실제 HTTP와 브라우저에서 v2.5를 확인한 뒤 기본 실행을 전환.
5. 최종 검증 결과와 실행 화면·데이터 파일 링크를 사용자에게 보고.

**현재 로컬에서 실행 중인 화면은 v2.4의 108개 버전입니다. v2.5 등록본을 만들었다는 이유로 이미 9,416개 전체가 실시간 검색된다고 보고하지 마세요.** v2.5 실제 인덱스와 통합 검증은 미완료입니다. 인수인계 시점에 수집/재시도/임베딩 준비 작업은 종료됐으며 다음 대화에서 무조건 전체 수집을 다시 시작할 필요는 없습니다.

## 4. 가장 먼저 열 파일

- [v2.5 전체 요약](data/v2_5/review_summary.json)
- [전체 11,766개 등록 CSV](data/v2_5/main_cases_v2_5.csv)
- [9,416개 검색 대상 CSV](data/v2_5/retrieval_cases_v2_5.csv)
- [전체 구조·메타데이터 JSON](data/v2_5/main_cases_v2_5.json)
- [모든 입력 포함 여부 대조표](data/v2_5/all_input_coverage.csv)
- [원천 CSV 5,961개 행의 ID·제목 대조](data/v2_5/structured_row_audits.json)
- [현재 파일·원천 스냅샷 해시](data/v2_5/release_manifest.json)
- [인수인계 시점의 기계 판독 상태](docs/handoff-state-2026-10-26.json) · [업로드 스냅샷 Git blob 목록](docs/handoff-files-2026-10-26.json)
- [웹 출처 확인 최종 집계](collections/ax-review-all-2026-10-26/page_check_summary.json)
- [전체 입력 원장](collections/ax-review-all-2026-10-26/all_inputs.json)
- 웹 출처 개별 기록: `collections/ax-review-all-2026-10-26/page_audits/<candidate_id>.json`.
- [직전 108개 적용 결과](docs/ax-expansion-application-2026-10-26.md), [v2.4 데이터 안내](data/v2_4/README.md).

`collections/ax-expansion-2026-10-25/collection_summary.json`의 1,800개는 과거 제한 수집 실행 기록입니다. 최신 전체 확인은 별도 `ax-review-all-2026-10-26`에 있습니다. 이 차이를 보고 전체 확인이 아직 1,800개라고 잘못 판단하지 마세요.

## 5. CSV 읽기 오류 수정과 9개 복원

`scripts/collect_ax_portals.py`의 옛 `csv.Sniffer` 사용은 헤더에서 추정한 `doublequote=False`까지 적용했습니다. 데이터 본문 안의 표준 이중 따옴표 이스케이프가 잘못 읽혀 EU 자료를 2,341개 정상과 11개 오류 행·조각으로 나누었습니다. 원천 파일이 실제로 깨졌다고 단정한 것은 잘못이었습니다.

구분자만 추정하고 `csv.reader(..., doublequote=True)`를 사용하도록 고쳤습니다. 원천을 다시 읽으면 미국은 3,611개, EU는 **2,350개 정상 행**이고 누락된 EU **9개를 복원**할 수 있습니다. EU의 뒤쪽 41개 기존 기록은 원천 행 번호가 달라져 원천 ID로 다시 연결했습니다. 미국은 기존 행 ID·제목 대조가 모두 일치했습니다.

원천 CSV와 옛 수집 결과는 덮어쓰지 않았습니다. 새 `all_inputs()`에서 정상화하고, 기존 candidate ID를 유지하며, 복원한 9개에는 `RECOVERED_...` ID를 부여했습니다. 옛 11개 행·조각도 `PRIOR_PARSER_ARTIFACT`로 보존해 정상 사례와 구별합니다. 이것을 다시 실제 파손 사례 11개로 세거나 제거하지 마세요.

## 6. 새 스키마와 포함 원칙

- `business_scope`, `business_scope_tags`, `업무구분`: 공공, 기업, 개인/소비자, 교육/연구, 사회/비영리, 복합, 미확인. 자동 분류이므로 독립 판정이 아닙니다. `mixed`나 `unspecified`도 포함됩니다.
- `record_kind`, `analysis_unit`: 검토 업무, 원천기관이 보고한 프로젝트/활용사례, 참고 페이지, 링크, 옛 파서 이력의 단위를 구별합니다.
- `deployment_stage`, `운영단계`: 운영·시험·도입 전·개발·계획·종료·미사용·미확인 모두 보존.
- `ai_status`: 원천의 AI 분류, 비AI/미확인 기술, 단순 AI 언급 등을 구분.
- `annotation_status`, `content_check_status`: 개별 AI 검토·원천기관 보고·자동 본문 점검·접근 불가를 구분.
- `source_description`은 문제와 해결 방식이 섞여 있을 수 있는 원천 설명입니다. 그것을 검증된 Problem View로 취급하지 마세요.
- `problem`, `implementation`은 명시적인 문장을 규칙으로 분리하고 부족하면 UNKNOWN으로 둡니다. 기대효과를 관측 성과로 바꾸지 않습니다.
- 새 원인 라벨 함수는 Problem 텍스트만 입력받습니다. 전략은 원천의 기능 표현을 기존 고정 S1~S7에 규칙으로 매핑한 잠정 라벨입니다. 인간 Gold·독립 Blind RCA·확인적 Wald 라벨이 아닙니다.
- 본문이 없는 링크, 확인 가능한 텍스트가 부족한 기록, 정확한 중복, 개별 검토 업무가 대표하는 상위 출처 페이지는 등록본에 남기고 검색 대표와 연결합니다. 따라서 전체 등록 수와 검색 수가 다릅니다. 업무 범위를 이유로 빠진 자료는 없습니다.

새 qrels는 승인되지 않았으며 기존 84개 Silver를 새 기록에 복사하지 않았습니다. 기존 연구의 47.64% Recall 같은 수치를 v2.5 성능으로 주장하면 안 됩니다.

## 7. 코드 위치와 실행 순서

새 코드의 핵심:

- `scripts/review_all_ax_sources.py`: 전체 입력 통합, CSV 정상화, 누락 복원, 웹 robots·간격·429 backoff를 지키는 접근 점검, 중단 재개.
- `scripts/retry_ax_source_failures.py`: 처음 확인이 끝난 호스트의 일시 오류를 한 번 재시도. 이미 재시도한 항목의 반복 호출 방지.
- `scripts/finalize_ax_source_audits.py`: 본문 일부의 제한된 메타데이터와 최종 집계를 실제 파일에서 재계산.
- `scripts/build_ax_inclusive_release.py`: 전체 등록본·업무 구분·잠정 분류·검색 대상·입력 대조표 생성.
- `scripts/index_ax_inclusive_release.py`: 로컬 BGE-M3 1024d, 추가 텍스트 128토큰, 누락 View=0벡터, 텍스트 해시 기반 SQLite 캐시.
- `prototype/corpus.py`, `prototype/core.py`: frozen / active(108개) / inclusive 프로필, 누락이 아닌 View의 평균 Dense, 업무 구분 필터, 자료 확인 수준 표시.
- `prototype/strategy.py`: 상위 선택 사례만 LLM에 전달. 허용 전략 ID가 없는 관점은 전략 빈 배열로 자제하며 임의 라벨을 만들지 않음.
- `prototype/web/`: 한국어 업무 구분 선택, 기관/기업에 한정되지 않는 표현, 단계·AI 여부·자료 유형·미확인 View 표시.
- `scripts/validate_ax_inclusive_release.py`: 다음에 실행할 실제 통합 검증.

### 새 환경에서 시작

이 브랜치를 체크아웃하고 기존 `requirements-prototype.txt` 및 테스트에 필요한 `requirements-rq1.txt`를 참고해 Python 환경을 준비합니다. 예시 재생은 키 없이 가능합니다. 전체 인덱스 재생성에는 로컬 BGE-M3가 필요합니다.

```powershell
$env:PYTHONPATH='src;.'
.\.venv\Scripts\python.exe scripts/prepare_prototype_model.py --download
.\.venv\Scripts\python.exe -m scripts.index_ax_inclusive_release --threads 8 --batch-size 32
.\.venv\Scripts\python.exe -m scripts.validate_ax_inclusive_release
.\.venv\Scripts\python.exe run_prototype.py --corpus inclusive --port 8766 --no-browser
```

Linux에서는 `.venv/bin/python`, `PYTHONPATH=src:.` 등 환경에 맞는 표기를 사용하세요. 인덱스를 만든 뒤 `http://127.0.0.1:8766`의 실제 bootstrap과 화면에서 v2.5와 검색 수 9,416개가 일치하는지 확인하세요. 기존 8765 서버가 떠 있으면 런처는 그 화면을 다시 열 수 있으므로, 기존 서버를 종료하지 않은 상태에서 단순 실행했다고 새 버전으로 전환됐다고 판단하면 안 됩니다.

필요할 때 데이터 재생성 순서:

```powershell
.\.venv\Scripts\python.exe -m scripts.finalize_ax_source_audits
.\.venv\Scripts\python.exe -m scripts.build_ax_inclusive_release
.\.venv\Scripts\python.exe -m scripts.index_ax_inclusive_release --threads 8 --batch-size 32
```

이미 전체 접근 기록과 등록본이 있으므로 처음부터 웹 수집을 다시 할 이유는 없습니다. 인덱스를 생성한 후 다음 검증을 하세요.

```powershell
.\.venv\Scripts\python.exe -m pytest -q
node --check prototype/web/app.js
node --test tests/prototype_research_ui.test.cjs
```

현재 스크립트는 기존 검토 업무를 108개로 고정한 부분이 있습니다. 이후 v2.4 개별 업무를 추가한다면 `[108:]` 등의 위치와 manifest의 inherited count를 함께 점검해야 합니다.

## 8. 검증 증거와 아직 하지 않은 주장

- 전체 Python 테스트 **233개 통과**: [기록](docs/prototype-validation/handoff-tests.xml).
- 팝업 JavaScript **3개 통과**, `app.js` 문법 검사 통과.
- v2.4에서는 실제 BGE-M3 자유 입력 6개, 예시 10개, HTTP 108개 검색을 확인했습니다. [기존 실행 증거](docs/prototype-validation/expansion-validation.json).
- v2.5는 전 입력 포함·원천 대조·접근 확인과 구조적 단위 테스트를 수행했지만, **v2.5 실제 인덱스·자유 입력 통합 검증·HTTP 전환은 아직 수행하지 않았습니다.**
- `data/v2_3/main_cases_v2_3.json` 작업 사본 SHA-256: `5a4683047e86aea67bbe6ca568d799c74b6d2aba1c4799d31cb96bf4b34987a2`. Git blob은 `1705888f3338b219d3715fe4422641865c3075e2`.
- 기존 추적 데이터·실험·설정·연구 소스는 수정하지 않았습니다. 추가물은 새 버전 폴더에 있습니다.
- 원래 v2.3 검증 스크립트의 직접 Git blob 계산은 Windows CRLF 작업 사본에서 오탐했습니다. `git hash-object --path=...`로 manifest 11개를 대조해 일치를 확인했습니다.

`.gitattributes`는 새 생성 자료의 원래 바이트·해시를 보존하고, 기존 frozen JSON의 체크아웃은 CRLF로 통일합니다. 이는 기존 Git blob을 바꾸지 않고 Windows/Linux에서 고정 SHA가 달라지는 문제를 방지합니다. `.gitattributes`를 무시해 모든 파일을 임의 LF 재저장하면 원천 해시 검증이 실패할 수 있습니다.

## 9. Git에 넣지 않은 것

- `.env`, Windows 자격 증명, API키, `.local`의 평가 SQLite 및 사용자 테스트 원본.
- `.venv`, 약 2.2GB의 `.local/models/bge-m3`, 임시 웹 원문 캐시, 로컬 임베딩 캐시, 빌드된 바탕화면 EXE.
- v2.5 전체 NPZ는 아직 생성되지 않았고 `.gitignore`에서 대용량 재생성 산출물로 제외했습니다. v2.4의 소형 고정 인덱스와 manifest는 포함해 키 없는 기존 예시를 재생할 수 있습니다.

이전 PC를 쓰는 새 대화라면 `.local/ax-inclusive-embedding-cache/vectors.sqlite3`가 있어 인코딩을 재사용할 수 있습니다. 다른 환경에는 이 캐시가 없으므로 재계산해야 합니다. BGE 모델 다운로드와 로컬 계산은 OpenAI 유료 API 호출이 아닙니다.

원천 자료의 출처·이용조건은 각 manifest와 컬럼에 보존했습니다. 웹페이지 원문 전체는 Git에 넣지 않았습니다. 미국 OMB 원천은 공개 연방기관 목록이며 별도 LICENSE를 확인하지 못했다는 표기를 유지했고, EU PSTW는 CC BY 4.0 출처를 유지했습니다.

## 10. 원래 연구와 사용자 테스트 맥락

사용자는 AI 지식이 없어도 자연어 업무 문제에서 사례와 적용 전략을 찾게 하는 프로그램을 원합니다. 수정이와 교수님에게 단순 사례 나열을 넘어 어떤 결과를 보여주려는지 시연하려고 개발했습니다.

현재 연결된 경로는 자연어 입력 → 동적 관점 → 관점별 Dense → 사례의 구현·성과·출처 → 우리 업무의 전략·실행 순서·조건·한계입니다. Dense가 기본이고 학습형 256d QCI는 낮은 Dev 성능 때문에 예시 비교 재생으로만 남겼습니다. 교수님 전체 아키텍처의 학습형 Evidence Fusion·현재 코퍼스의 Wald 통합 효과를 완성·검증했다고 주장하지 않습니다. RRF를 제안 모델로 다시 넣지 마세요.

테스터가 본 “실시간 전략 설명을 완료하지 못해 사례 기반 안내 틀로…”는 LLM 설명/검증 실패 뒤 명시적 템플릿으로 전환했다는 뜻이었습니다. 단순히 사례 수가 적다는 뜻이 아닙니다. 저장된 사용자 테스트 1건은 실제 전략 생성 성공이었고, 보고된 실패 실행 자체는 그 파일에 없었습니다. 사용자 피드백에 후속 질문 제안이 있었으나 그 기능은 아직 구현하지 않았습니다. 사용자 테스트 원본은 개인정보·평가 자료이므로 이 브랜치에 올리지 않았습니다.

이전 완료 확인 자동화 `ax`는 수집 완료 보고 뒤 삭제했습니다. 이 문서를 읽었다는 이유만으로 새 자동화·새 대화·유료 전체 데이터 LLM 처리를 만들지 마세요. 남은 실제 작업은 위 3절의 v2.5 인덱스 생성·검증·적용입니다.

## 11. 2026-10-27 질문 분리 재수행의 최신 상태

이 절은 `research/stage123-query-isolated-20261027`의 후속 연구 상태다. 위 과거 연구·프로토타입의 완료 표시를 이번 축소 Stage1~3의 완료로 해석하지 않는다. 기준은 사용자 지정 `30c57b8de4819523b7e84db3f453de68da657a2b`다.

- [최종 한국어 보고](docs/stage123-query-isolated-2026-10-27/README.md)와 [상세 일지](worklog/2026-10-27-query-isolated.md)를 먼저 읽는다. 같은40쌍 재시험120점 완료, 등급23/40·관련 여부39/40 일치. 전수 수집은872/3,360점에서 방법론 문제로 중단했다. 최종 Silver0, 사람 Gold0, 새 Stage2·3·4 미실행이다.
- 질문 혼합 배치·ID/발췌/출력 구조 검사를 수정했다. 그러나 전수 수집에서 일반적인 인력 부담 감소를 직접 과업으로 취급한 높은 점수와 원문 없는 효과 추론이 발견됐다. 정상 경계 이견도 별도로 보존한다. 과반수 점수를 정답으로 승인하거나 불완전 qrels로 검색 성능을 내지 않는다.
- 활성 중단 파일은 `docs/stage123-query-isolated-2026-10-27/format-v8/halt.json`이다. 기존 파일럿 수집 허용 게이트는 폐기된 과거 단계다. 기본 CLI는 새 API 호출을 차단하며, Silver 미승인 게이트도 검색 실험을 막는다. 해결 전 자동 재개·반복 호출·중단 파일 삭제를 하지 않는다.
- 미확정 생성 예약6개는 청구 가능 전액으로 유지하고 자동 재호출하지 않는다. 세 API 확인비용$0.94403810/보수상한$1.00006820, Claude 이전 사용액 포함 상한$0.723839다. 계정 잔액 조회나 추가 충전은 하지 않았다. 재개할 때 변경 프롬프트 비용을 다시 측정하고 Claude $0.50 여유를 유지한다.
- 다음은 질문별 행동–대상–산출물/보조 단계/결과의 경계를 구체화하고 원문 없는 추론을 점검한 작은 검증이다. 가능하면 전문가·사람의 근거 확인을 받아야 하며 사람 검증이 없다면 AI Silver로만 표시한다. 사용자가 재개를 요청하면 새 입력 버전으로 진행하고 기존 모든 응답·실패·예약을 보존한다.
- 기존112개 사례와10개 질문,30개 참조관점은 변경하지 않았다. 원질문 정답과 참조관점 정답을 섞지 않으며 Reference Coverage를 주요 지표로 삼기 전 별도 검증한다. 새 검색 알고리즘·Query2doc/CSQE/HyDE·Stage4 독립 Test는 실행하지 않는다. 키는 기존 환경변수에서 읽고 파일·GitHub·로그에 기록하지 않는다.

## 12. 2026-10-27 행동·대상·산출물 기준 재개 결과

이 최신 절은 `research/stage123-action-object-output-20261027`의 상태다. 기준은 faf6e69a1b7caf547af391a051d1ee9d3d98fd1e. [새 보고서](docs/stage123-action-object-output-2026-10-27/README.md)와 [작업일지](worklog/2026-10-27-aoo.md)를 우선 읽는다.

- 사용자 재개 지시로 전체 질문/개별 관점 기준을 분리하고 기능적으로 같은 업종 전이를 허용했다.36쌍(직접/부분/무관 각12개)의3모델 독립 파일럿을 계획했으나, 최신 v10 형식검증 점수54/108·삼자공통6쌍으로 미완료/미통과다. 새 Stage1전수점수0, Stage2·3 미실행이다. 예전872개 점수는 그대로 보존한다.
- 현재 중단은 `docs/stage123-action-object-output-2026-10-27/schema-safe-v10/halt.json`, 원인·조건은 같은 폴더의 methodology_hold.json, 실패 게이트는 pilot_gate.json이다. v9 최초 시도와 v10을 섞지 않는다. 기본 실행기는 이 새 중단 경로를 사용한다. 과거 v8 중단 파일도 삭제하지 않는다.
- 남은 것은 전체 질문4점의 실제 문제조건 근거, Problem의 원하는 결과와 Task의 실제 수행 작업을 구분하는 판정 안정성, Claude 최대 생성 구조 호환성이다. Gemini의 쇼핑QA4점, Claude의 요약→후속조치 식별 주장 및 근거를 넘는 효과 서술을 원문과 대조했다. 점수를 임의 수정하거나 다수결로 승인하지 않았다.
- Claude HTTP400은 진단에서 Schema is too complex가 확인됐고 작은 요청은 성공해 인증 실패와 다르다. 토큰 계산만으로 생성 호환성을 확인하지 말고 최대 크기 실제 요청을 먼저 작은 범위에서 시험해야 한다. 새로운 요청은 입력 버전을 달리하고, 기존 실패 비용도 불확실하면 예약한다.
- 이번 작업 확인$0.04424326/보수$0.09181326. Claude 과거 연구 포함 상한$0.787382이며$0.50 여유를 지켰다. 계정 실잔액을 조회하거나 충전하지 않았다. 사용자가 다시 재개를 요청하면 새 프롬프트/스키마 비용을 다시 재고 전문가 근거 확인이 가능하면 받아라. 사람 검증이 없으면 AI Silver로만 표현한다.
- 자동시험71개 통과는 코드 조건 검증이지 모델의 판단 정확도 증명이 아니다. Silver/사람Gold승인0, Stage4봉인 유지, 키는 기존 환경변수에서 읽고 저장하지 않는다. 다음판의 원자 작업별 근거/전체 점수 고정 합산 정책과 작은 생성 구조를 검증하기 전 전수나 검색을 자동 재개하지 않는다.

## 근거 추출 재시험 2026-10-27
새 브랜치 research/stage123-evidence-rules-20261027. docs/stage123-evidence-rules-2026-10-27/README.md 참조. 단순 JSON Claude 시험 성공, 그러나 GPT의 분석→데이터통합 기능 연결 오류로 의미 검증 중단. 활성 halt 유지. 36쌍 본시험 및 Stage1~3 미실행, Stage4 봉인. 이번 Claude 비용 0.036달러. 기존 결과 보존.
