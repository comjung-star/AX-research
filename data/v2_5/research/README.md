# v2.5 연구 입력 · 2026-10-26

**서술적 Dev 검색 실험은 바로 실행 가능하다. 전체 신규 자료의 사실검증과 확인적 평가 준비는 미완료다.**

기준 커밋 `8b40bfbefa82e0cbf710482823f7d97b58f1690b`, 작업 브랜치 `research/v25-experiment-ready-20261026`. 원본 11,766개와 기존 검색 후보 9,416개를 재수집하거나 덮어쓰지 않았다. v2.3 frozen 84건, v2.4 108건, 과거 실험·설정·연구 소스는 그대로다.

## 지금 실행

저장소 루트의 기존 `.venv`에서 PowerShell로 다음을 실행한다.

```powershell
.\run_v25_research.ps1
```

이미 저장된 **112건의 깨끗한 3-view 벡터 + 기존 Dev 질문 10개**를 사용하여 single-query Kiwi BM25와 BGE-M3 Dense의 Top-10을 다시 계산하고 입력·해시·판정·누수 연결을 점검한다. 키나 모델 다운로드가 필요하지 않다. 결과는 `docs/prototype-validation/v25-dev/`에 저장된다. 이 실행은 인간 정답에 대한 성능 평가가 아니다.

현재 PC의 전체 검색 화면은 `http://127.0.0.1:8766`이다. **키 없이 체험 · 데모**를 선택하면 유료 API 없이 로컬 Dense로 검색한다. 기존 8765 서버는 변경하지 않았다. 새 서버를 띄울 때는:

```powershell
.\.venv\Scripts\python.exe -m prototype.server --corpus inclusive --port 8766 --no-browser
```

8766 서버 실행 중 실제 HTTP까지 재검증하려면 `run_v25_research.ps1 -ValidateHttp`를 사용한다. 화면 전체 검색 9,416개와 아래의 연구 Dev 112개는 서로 다른 실험 범위다.

## 판정과 근거

| 판정 | 기록 수 | 의미 |
|---|---:|---|
| 실험 적합 | 112 | 과거 개별 출처 검토 106 + 이번 저장 원천 행 개별 검토 6. 서술적 검색 Dev 전용 |
| 참고 전용 | 3,354 | 읽을 수 있는 페이지 메타데이터. 개별 AX 업무 사실로 확정하지 않음 |
| 보류 | 8,259 | 출처 접근/내용 부족, 실제 문제/구현 결측, AI/단계 미확인, 개별 검토 대기 등 |
| 제외 | 41 | 파서 이력 11, 명시적 중복 11, 기존 개별 업무로 표현한 상위 페이지 19. 분석 대상에서만 제외하며 원본 보존 |

업무 범위 제외 0. 공공·기업·개인·교육·비영리·미확인 범위는 판정의 삭제 조건이 아니다. 실험 적합은 인간 Gold·실제 운영 독립 확인·성과 검증·인과 확인을 의미하지 않는다. 원문이 기대효과만 제시하면 관측 성과는 UNKNOWN이다.

- `dispositions.csv`: 전 기록의 독립적인 적용기준 판정, 복수 사유, 근거 ID, 필드별 확인 상태. 자동 전수 선별은 독립 검토자/인간의 전수 사실검증이 아니다.
- `evidence_catalog.jsonl`: 11,766개 근거 ID와 출처·스냅샷·감사파일 해시·필드 위치. 웹 접근과 개별 사실 확인을 구분한다.
- `source_reviews.json`: 이번 6개 공공 업무의 원천 문서 대조와 판단 이유. 원천기관의 운영/효과 보고를 별도로 교차확인하지 않았다.
- `dev_cases.json`: 문제/대상/맥락과 별도 구현/성과를 가진 112개 Dev 기록. 모든 라벨·성과 검증 플래그는 false.
- `dev_problem_views.csv`: 평가자에게 제공할 Problem/Task/Context만 포함. 구현·성과·원인·전략은 숨긴다.
- `manifest.json`, `dev_index_manifest.json`: 원본/파생 입력·벡터·모델 가중치·설정의 SHA-256. 기존 frozen 모델 가중치와 로컬 BGE-M3 일치도 점검했다.

## 분리와 정답 준비

`split_groups.csv`와 `leakage_links.csv`는 기관, 기존 sampling ID, 개별 출처 URL/리디렉션, 본문 해시, 원천 ID, 명시적 중복·상위/하위 기록을 전이적으로 묶는다. 공통 원천 CSV의 다운로드 URL 자체는 서로 다른 업무를 전부 하나로 묶는 근거로 쓰지 않는다.

5,298개 그룹, 알려진 연결 16,372개에 대해 분할간 누수 0이다. Dev 관련 기록 1,349개, 향후 Test 예약 1,820개, 미배정 8,597개다. **예약은 실제 Test가 아니다.** 의미적으로 비슷한 중복의 전수 판정은 남아 있다. 실험 적합 112개와 이번 검토한 6개는 모두 Dev 전용이다.

`dev_qrels_annotation.csv`는 10질문 × 3개 기존 draft reference perspective × 112사례 = **3,360쌍**이며 점수는 전부 빈칸/UNJUDGED다. 구 84건의 Silver 점수를 복사하지 않았다. 9,416개 전체를 평가하려면 동일한 30개 reference 기준으로 최대 282,480쌍이 필요하며, 현재 양식은 112개 Dev 범위에 한정한다. 미판정은 비관련 0점이 아니다.

`evaluation_policy.json`에 0–4 척도, 양성 기준 >=3, 독립 판단 2회, 등급 불일치/양성 전환 조정, 연구자 승인, 해결 정보 비노출을 사전 기록했다. 기존 관점은 평가 reference이며 runtime 관점으로 주입하지 않는다. 최종 Test 질문은 모델·프롬프트·평가 규칙 동결 뒤 독립적으로 구성해야 한다.

## 전체 재현

현재 PC의 확인 환경은 Python 3.13.13이다. `requirements-v25-dev.txt`에 이번 검증의 직접 의존성 버전을 기록했고 실제 환경은 `docs/prototype-validation/v25-dev/run_report.json`에도 있다. 새 환경에서는 가상환경을 만든 뒤 이 파일을 설치한다. 과거 `requirements-rq1.txt`의 OpenAI 하한과 현재 설치본은 다르므로 두 요구사항 파일을 함께 설치하지 않는다. 이번 로컬 실행은 OpenAI API를 사용하지 않는다.

```powershell
$env:PYTHONPATH='src;.'
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe -m scripts.prepare_v25_research
.\.venv\Scripts\python.exe -m scripts.run_v25_dev_baselines
.\.venv\Scripts\python.exe -m scripts.validate_v25_research
.\.venv\Scripts\python.exe -m pytest -q
node --check prototype/web/app.js
node --test tests/prototype_research_ui.test.cjs
```

깨끗한 Dev 인덱스를 재생성할 때만 로컬 BGE-M3 가중치가 필요하다.

```powershell
.\.venv\Scripts\python.exe -m scripts.run_v25_dev_baselines --rebuild-index
```

전체 9,416개 검색용 56.8MB NPZ는 기존 `.gitignore` 정책에 따라 로컬에 보관하고 Git에는 해시/재현 코드를 저장한다. 새 PC에는 해당 NPZ와 비공개 로컬 임베딩 캐시가 없으므로 다음 실행에 계산 시간이 든다.

```powershell
.\.venv\Scripts\python.exe scripts/prepare_prototype_model.py --download
.\.venv\Scripts\python.exe -m scripts.index_ax_inclusive_release --threads 8 --batch-size 32
.\.venv\Scripts\python.exe -m scripts.validate_ax_inclusive_release
```

전체 검색 인덱스는 과거 벡터와 신규 128토큰 벡터를 합치며 일부 Task에 혼합 source description을 사용한다. 통제 실험용 Dev 인덱스는 이와 별도로 **모든 사례 View/질문을 동일한 128토큰, 1024차원, 정규화, CPU/seed 고정**으로 생성했다. 구현·성과·라벨은 임베딩 입력에서 제외했다. BM25의 한국어 질문/영어 원천 언어 불일치도 성능 해석 시 통제해야 한다.

## 완료되지 않은 연구 조건

1. 8,259개 보류 기록의 개별 원문/필드 검토, 실제 운영·성과의 독립 교차확인. 원본 문제 결측은 9,553건이다. 자동 재구성만으로 내용을 만들어 채울 수 없다.
2. 의미 유사 중복의 전수 확인과 최종 누수 분할 승인.
3. 독립 relevance 판단, reference 검증, 신규 qrels 승인, 이후 Gold Strategy 작성.
4. 원인/전략 라벨 독립 검증·표본 희소성 점검 전 확인적 Wald 분석.
5. 모델/프롬프트/평가 규칙 동결 후 held-out Test 구성과 전체 FAME-AX 비교.

로컬 BGE-M3는 임베딩 모델이다. 프로젝트 모델 폴더와 PATH에서 즉시 사용할 생성형 모델/`ollama`/`lms`는 발견되지 않았다. 유료 전수 LLM 호출을 시작하지 않았고, 자동 분류를 독립 라벨로 승격하지 않았다. 따라서 **Dev 실행 준비 완료와 전체 연구 데이터셋/최종 평가 완료를 구분해야 한다.**
