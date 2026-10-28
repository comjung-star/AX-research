# Work A — 독립 Test 실행·평가 연결부

이번 작업은 기존 코어를 바꾸지 않고 입력·저장·평가를 연결한다. 독립 Test 실행, 새 연구 질문/정답 작성, Work B 정답 열람, API 호출은 하지 않는다. 개발용 fixture는 연구 데이터가 아니다.

## 고정 조건과 사전 등록

기준 `1e9523ed2da67ec43fabc901774b1f163edc51ab`. 정책 사전 등록 커밋 `5fe1942a`: `configs/heldout_policy_v1.json`.

- 원질문만 사용, 동일112사례 전체 후보. Single Dense/A/B/C 네 조건.
- A18규칙과 정렬키, B필드 추출·가중치, C50:50 함수를 직접 재사용한다.
- A/B/C 동점은 기존 Dense+BM25 RRF60 50:50 점수와 case_id로 해결한다. 새로운 알고리즘이 아니라 기존 동점 규칙의 재사용이다.
- BGE-M3 CLS1024, 정규화, CPU, seed/threads/batch/max4096과 모델10파일·기존 벡터 해시를 확인한다. 긴 질문은 자르지 않고 거절한다.
- 다중관점 생성/추론은 이번 실행기에 넣지 않았다. 원질문 결과로 관점 효과를 주장하지 않는다.

## 완료 기능: 12개

|번호|기능|검증 근거|
|---|---|---|
|1|ax-heldout-v1 질문·manifest 입력/ID/해시 검증|`tests/test_heldout.py`|
|2|임의 질문 수와 고정112후보|동적N 검사·Dev종단간|
|3|Single Dense/A/B/C 실행|기존 코어 직접호출·Dev8순위|
|4|전체순위와Top5/10/20 별도저장|predictions/top파일|
|5|점수·원문사례·매핑근거 보존|evidence.json|
|6|P/R/F1@5/10/20,nDCG@5/10|수치 정답 fixture|
|7|질문별·방식별Macro/정의가능 분모/제외ID|metrics.json|
|8|미평가·보류·0양성·부분정답 처리|경계조건 검사|
|9|AI-Silver와Human-Gold 분리|출처별 독립집계 검사|
|10|run-id·덮어쓰기거부·실패보존|exclusive파일/실패검사|
|11|예측완료 봉인 후 별도평가·변조검사|seal/hash 검사|
|12|알고리즘·모델·환경동결/오프라인·재현|freeze.json·두번Dev실행|

검사 개수와 실제 실행 기록은 `verification.json`, `pytest.txt`, `smoke_receipt.json` 참조. 기능12개는 위 표의 기능 묶음 수이며 테스트 수와 다르다.

## Work B 입력 계약

UTF-8 JSONL. 질문행은 정확히 `query_id`(비어있지 않은 고유 문자열), `text`(업무문제), `split`=`TEST`. 질문 수는1이상. 중복ID/정규화본문/기존Dev10·pilot5와의 정확한 중복은 거부한다. 의미상 중복·작성 독립성은 사람이 별도 확인해야 한다.

정답행은 정확히 `query_id`, `case_id`, `grade`, `status`, `label_source`, `rationale`. case_id는 기존case_registry의112개 ID. `JUDGED`는 정수0/1/2/3과 근거 필수. `ABSTAIN`은null과 보류근거 필수, `UNJUDGED`는null(근거공란 허용). bool은 점수가 아니다. source는 `AI-Silver` 또는 `Human-Gold`. 여러 출처이면 동일쌍을 각 출처별1회 기록하며 서로 합치지 않는다. 사람의 실제 판정이 없으면 Human-Gold를 쓰지 않는다. 판정자·모델·반복·합의 과정은 manifest의 추가 provenance 필드에 기록한다.

manifest 필드 명세(실제 Test 내용 없는 구조 설명):

|필드|형식|
|---|---|
|schema_version|`ax-heldout-v1`|
|test_id|비어있지 않은 식별문자열|
|files.questions / files.qrels|각각 `{path: manifest기준상대경로 또는 절대경로, sha256: 소문자64자리}`|
|corpus|`{id: ax112, case_count: 112, sha256: case_registry.json의실제파일SHA256}`|
|grade_scale|`[0,1,2,3]`|
|relevant_threshold|`2`|
|judgment_scope|`FULL_CORPUS` 또는 `PARTIAL`|
|label_sources|`[AI-Silver]`, `[Human-Gold]` 또는 두개|
|unused_history|`{previously_used: false, provenance: 작성·미사용근거, exposure_log: 비어있지않은노출이력}`|

manifest는 추론 시 메타데이터만 읽는다. qrels 경로의 존재/해시/본문은 추론에서 읽지 않고, 예측 완료 후 평가에서만 검증한다. 새 Test 작성·노출 이력의 진실성은 프로그램만으로 증명할 수 없다. 추론 담당자에게 qrels 파일 읽기 권한을 주지 않고 별도 평가 담당자가 평가 명령을 실행하는 운영을 권장한다. 코드 분리와 로컬 파일권한은 서로 다르다.

## 평가 정책

2점 이상 관련. Precision은 TopK가 모두JUDGED일 때만 hits/K. 전체112사례가 모두JUDGED이고 manifest도FULL_CORPUS일 때만 Recall/F1/nDCG 계산. PARTIAL이면 실제행이112개여도 전체지표를 계산하지 않는다. 보류/미평가/누락은0점으로 바꾸지 않는다. 관련0개 질문은Recall/F1 미정, IDCG0이면nDCG 미정이다. 완전판정인0양성 질문의Precision은0이다.

nDCG는gain=2^grade-1, log2(rank+1), IDCG는전체112판정에서 계산한다. 이번 버전은부분풀nDCG를 제공하지 않는다. Macro는정의가능질문만 평균하고 defined/total 및제외질문ID를 항상 저장한다. 임의의 source를Human-Gold로 변환하지 않는다. 네방식 비교는동일source 안에서만 한다.

기존Dev는0~4/임계3, 이번계약은0~3/임계2다. 따라서Dev/Test 차이를 일반화 개선 수치처럼 직접 빼지 않는다. Dev연결검사도새Test성능이 아니다.

## 실제 실행 명령 (PowerShell)

저장소 루트에서 기존 연구환경을 사용한다. `pip install -e .`만으로 의존성이 설치되지 않는다. `requirements-v25-dev.txt`를 사용하며 상충하는옛rq1프로필과 혼합하지 않는다. 로컬모델은 자동 다운로드하지 않는다.

```powershell
$env:PYTHONPATH='src;.'
$env:PYTHONIOENCODING='utf-8'
$env:PYTHONDONTWRITEBYTECODE='1'
$py='../AX-prototype/.venv/Scripts/python.exe'
# 아래 Test 명령은 Work B 데이터 검증·미사용이력 승인 뒤에만 실행한다. 이번에는 실행하지 않았다.
& $py -m scripts.heldout_run infer --manifest 'C:/AX-heldout/manifest.json' --model-path '../AX-prototype/.local/models/bge-m3' --output-root 'C:/AX-runs' --run-id 'test01-pred'
# 추천 완료 후 별도 평가 단계에서만 정답을 읽는다.
& $py -m scripts.heldout_run evaluate --manifest 'C:/AX-heldout/manifest.json' --prediction-run 'C:/AX-runs/test01-pred' --output-root 'C:/AX-runs' --run-id 'test01-eval'
```

출력루트는저장소밖이어야 한다. 기존Dev/파일럿파일을덮지 않는다. 같은run-id는거부한다. 실패시started/부분파일/failed.json을남기며complete.json이없으면평가거부. 자동재개하지않는다. 원인을 확인하고새run-id로처음부터 재실행한다. API비용은없다.

```powershell
# 기존 Dev 자료만 사용하는 종단간검사. 출력폴더가 없어야 한다.
& $py -m scripts.heldout_dev_smoke --output-root '../AX-workA-dev-smoke-new'
& $py -m pytest -p no:cacheprovider tests/test_heldout.py -q
```

## 결과와 남은 경계

P1/P2/P3/E1/E3/E4의 프로그램측 구현과 자체검증을 제공한다. E2는정답미접근·예측후평가·정확중복검사를 구현했지만, 아직받지않은Test의미사용/의미중복/작성독립성은 Work B와함께확인해야 한다. D1/D2의 실제자료와출처는이번범위밖이다. 자료가계약에맞고독립성검토가끝나면새알고리즘개발없이실행가능하다. 새환경에서는동결패키지·모델파일을먼저준비해야한다.

기존추천방식의의미정확도를이번코드검사로증명하지않는다. 실제Test를보고규칙·가중치를조정하지않는다. Work B데이터열람/독립Test실행/유료API호출은0회다.
