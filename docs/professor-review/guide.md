# 구현·실행·재현 가이드

[첫 화면](../../README.md) · [한 장 요약](overview.md) · [Work B 공개 요약](work-b-public-summary.md)

## 새 PC 준비

이번 재검증 환경은 Windows와 Python 3.13.13이다. 정확한 역사적 Python·패키지·모델 해시는 [사전등록](../query-case-semantic-mapping-2026-10-28/preregistration.json)에 있다. 설치는 루트의 `requirements-v25-dev.txt`를 사용한다. `pip install -e .`만으로 모든 의존성이 준비되지 않는다. 오래된 rq1 환경과 혼합하지 않는다.

1. 첫 화면의 브랜치 clone·가상환경 설치를 실행한다.
2. BAAI/bge-m3의 SentenceTransformer 모델 전체를 별도 폴더에 준비한다. weights뿐 아니라 tokenizer, config, pooling 등도 필요하다. 온라인 환경에서 모델을 확보한 뒤 모델 디렉터리를 `AX_BGE_MODEL_PATH`로 지정한다. 앱은 `local_files_only=True`, CPU로 로딩한다. 역사적 결과와 엄밀히 비교하려면 사전등록의 10파일 해시를 맞춘다.
3. API 키는 아래처럼 현재 PowerShell 프로세스에만 입력하거나 기존 AX 나침반의 Windows 보안 저장 연결을 사용한다. 실제 키를 파일·문서·화면·로그·Git에 넣지 않는다.

```powershell
$axSecureKey = Read-Host 'OpenAI API 키' -AsSecureString
$env:OPENAI_API_KEY = [System.Net.NetworkCredential]::new('', $axSecureKey).Password
Remove-Variable axSecureKey
$env:AX_LLM_MODEL='gpt-6-luna'
$env:AX_BGE_MODEL_PATH='C:\AX-models\bge-m3'
powershell -ExecutionPolicy Bypass -File .\run_professor_demo.ps1
```

`OPENAI_API_KEY`, `AX_LLM_MODEL`, `AX_BGE_MODEL_PATH` 환경변수가 이미 있으면 로컬 파일보다 우선한다. 앱은 기존 옆 `AX-prototype/.env`, 루트 `.env`와 Windows 보안 저장소를 지원한다. 이 문서는 실제 환경파일을 읽거나 배포하지 않는다. 새 PC에는 옆 작업 폴더가 필요하지 않으며 루트 `.venv`와 명시적 환경변수를 사용한다. 기본 LLM 접근이 불가능하면 계정에서 허용된 구조화 응답 모델을 지정하고 동작을 확인한다. 모델을 바꾸면 역사적 생성과 같은 조건이라고 주장하지 않는다.

브라우저 주소는 `http://127.0.0.1:8766`. 포트 충돌 시 실행기에 `-Port 8767`을 추가한다. 처음 CPU 모델 준비가 끝날 때까지 기다린다. `모델 준비 중` 또는 오류일 때는 검색할 수 없다. 종료는 실행 창의 Ctrl+C. localhost에만 바인딩한다.

실시간 검색은 OpenAI에 입력을 보내므로 비용이 발생한다. 로컬 Dense/BM25 자체에는 API 요금이 없다. 키가 없으면 기본 실시간 화면은 실패를 표시하며 정적 관점으로 대체하지 않는다. `/api/search`는 키 없는 로컬 비교 경로이고 `/api/live-search`가 현재 화면 경로다. 이전 시연 README의 오프라인 내용은 최초 버전 기록이다.

## 검색 정책과 구현 차이

- 원문 Q는 단독 검색. LLM 관점 P는 각각 `title + description`으로 검색한다. Q를 각 P에 붙이지 않는다. 각 경로는 112개 사례 전체에 점수를 매긴다.
- A: [18개 규칙](../../configs/functional_mapping_20261028.json), [구현](../../src/ax_research/functional_mapping.py). Task의 긍정 실행 구절, 행동·대상 기능에 근거한 0~4 강도다. UNKNOWN은 무관 정답이 아니다. 실행을 Problem/Context로 대신 증명하지 않는다.
- B: [설정](../../configs/semantic_mapping_20261028.json), [구현](../../src/ax_research/semantic_mapping.py). Task .4 / Action .2 / Object .2 / Output .1 / Context .1. BGE-M3 CLS 1024차원 L2 정규화 cosine을 양쪽 가용 필드만으로 가중평균한다. Output 미기재는 UNKNOWN, Action은 표면 패턴, Object는 잔여 구절로 추출한다. 정밀 의미역 정답으로 검증된 파서는 아니다.
- 원문+관점 B: `(B(Q,c) + max_i B(P_i,c))/2`. 관점 점수를 모두 더하지 않는다. 원문만인 조건은 B(Q,c)다.
- C: `0.5 * (max 원문/관점 규칙강도 / 4) + 0.5 * ((결합 B + 1)/2)`. 사전 고정 50:50이며 학습·최적화·확률 보정이 아니다.

|구현|결합·동점과 범위|
|---|---|
|실시간 앱|관점별 Top5·최종 Top5 유지. A는 규칙강도 최대, B/C는 위 식. Dense/BM25 선택 시에도 원문 점수와 관점 최고점 평균. 모든 최종 동점은 원질문 Dense 점수 → ID|
|학술 functional 실험|규칙 근거·전체 문제 근거·관점 근거 등 사전 정렬키, 기존 하이브리드 점수·ID. 세부는 functional 결과·코드|
|학술 semantic 실험|B/C 점수 → 변경하지 않은 후보 pool `final_retrieval_score` → ID. 기존 저장 관점 3회 사용|
|과거 Dense/BM25 실험|Kiwi BM25와 Dense의 RRF60 50:50; 관점 기여 평균. 역사적 비교 조건으로 보존하며 제안 모델의 RRF 채택을 의미하지 않음|
|독립 Test 실행기|원질문만 Single Dense/A/B/C. A/B/C 동점에 기존 Dense+BM25 RRF60 50:50 점수·ID 재사용. 다중관점 효과를 측정하는 실행기가 아님|

그러므로 화면 점수/순위와 Dev 표의 완전 일치를 주장하지 않는다. [현재 앱](../../professor_demo.py), [functional 결과](../query-case-functional-mapping-2026-10-28/README.md), [semantic 정의](../query-case-semantic-mapping-report-2026-10-28/README.md), [독립 정책](../../configs/heldout_policy_v1.json)을 각각 확인한다.

목표 연구의 Problem/Task/Context multi-view와 현재 B의 Task/Action/Object/Output/Context 필드 비교는 구분한다. 학습된 Gate/QCI, Factor Anchor, Wald 근거, 최종 전략 추천의 전체 모델은 추가 검증 대상이다. Wald 관계는 인과효과가 아니다.

## 데이터와 결과를 따라가는 순서

1. [데이터 README](../../data/v2_5/research/README.md): 112개는 과거 개별 검토106 + 신규 저장 원천 대조6. 11,766 등록본 전체가 사실 검증된 것은 아니다.
2. [검색 레지스트리](../dense-bm25-candidates-2026-10-27/case_registry.json)의 case_id·evidence_ids를 [Dev 사례](../../data/v2_5/research/dev_cases.json)와 [근거 목록](../../data/v2_5/research/evidence_catalog.jsonl)에 연결한다. 원천 출처·스냅샷·필드 위치와 실제 검토 범위를 구분한다.
3. [functional 결과](../query-case-functional-mapping-2026-10-28/README.md)의 stage2/3/4, [semantic 결과](../query-case-semantic-mapping-2026-10-28/README.md)의 mapping/evaluation, [성능 종합](../query-case-semantic-mapping-report-2026-10-28/README.md)을 확인한다.
4. [독립 실행기](../independent-test-runner-2026-10-28/README.md), [기존 Dev smoke](../independent-test-runner-2026-10-28/smoke_receipt.json), [실시간 API 기록](../professor-demo-20261028/live-validation.md)을 확인한다. Dev smoke는 독립 Test가 아니다.

## 재현 및 검증

첫 화면의 108개 테스트 명령은 기존 단위/산출물 검증을 다시 실행한다. 추가 `test_bm25.py` 3개는 별도 확인 가능하다. 아래 새 통합 확인기는 로컬 실제 추론 HTTP를 호출하고 새 보고서를 표준출력에만 쓰며 기존 결과를 덮어쓰지 않는다. 실시간 API를 호출하지 않으므로 추가 API 요금이 없다.

```powershell
$env:PYTHONPATH='src;.'
.\.venv\Scripts\python.exe scripts/verify_professor_review.py --base-url http://127.0.0.1:8766
```

역사적 실험의 재계산 명령은 다음과 같다. **이 검토 브랜치에서 실행하면 저장 결과를 덮어쓸 수 있어 이번 통합에서는 실행하지 않았다.** 별도 일회용 작업 공간에서 입력/설정/모델·환경 해시를 확인하고 해당 실험의 원래 절차에 따라 실행한다. `freeze`는 현재 검토 HEAD가 아니라 설정의 `base_commit`을 요구한다. 기존 사전등록을 새 값으로 덮어써 통과시키면 같은 실험이 아니다.

```powershell
python -m scripts.dense_bm25_candidates prepare
python -m scripts.dense_bm25_candidates run
python -m scripts.functional_mapping_run prepare
python -m scripts.functional_mapping_run stage2
python -m scripts.functional_mapping_run stage3
python -m scripts.semantic_mapping_run freeze
python -m scripts.semantic_mapping_run run
python -m scripts.semantic_mapping_evaluate
```

독립 실행기의 기능/Dev 연결만 확인하려면 `python -m scripts.heldout_dev_smoke --output-root '../AX-review-dev-smoke-new'`를 사용한다. 출력 폴더가 없어야 하고 저장소 밖이어야 한다. 이 작업은 기존 Dev를 사용한다. 봉인 Work B용 infer/evaluate는 이번 검토에서 실행하지 않았으며 원본 파일도 제공하지 않는다. [정식 실행 계약·명령](../independent-test-runner-2026-10-28/README.md)은 별도 승인된 평가 담당자용이다.

## 통합 기준과 접근

원격 `git ls-remote`와 실제 시연 로컬 HEAD를 확인해 `dd281118c222e59c892e29c93051d7e1323d1346`을 선택했다. 독립 실행기 `ba5308d1`, functional `be64f9c1`, semantic `715c4050`, Dense/BM25 `cf30b73c`의 자료는 이미 이 커밋의 이력에 포함된다. Work B `e322ed65`는 병합하지 않고 공개 README의 집계·한계만 요약했다. 기존 main과 연구 브랜치·데이터·GT·설정·결과를 바꾸지 않았다.

저장소는 private이며 교수님의 GitHub 계정에 저장소 접근 권한과 초대 수락이 필요하다. 브랜치 URL을 전달해야 한다. 모델 가중치·개인정보·실제 환경파일·API 키·봉인 질문/정답을 새로 게시하지 않는다. 기존 README는 루트의 `README-history.md`로 보존해 원래 상대 링크를 유지한다.
