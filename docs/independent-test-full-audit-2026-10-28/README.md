# 최종 독립 Test 사전 준비 상태 전수 점검

2026-10-28 KST / 점검 브랜치 `research/independent-test-full-audit-20261028`

**결론: Test 질문과 정답만 추가해 바로 실행할 수는 없다. A/B/C 알고리즘을 새로 만들 필요는 없지만, Test 전용 입력·출력·평가 연결과 실행 전 검증이 더 필요하다. 이번에는 코드 수정·독립Test·새추천추론·새질문/정답 생성·유료API를 하지 않았다.**

## 1. 현재 연구 진행 상황

지정한 네 브랜치의 최신 원격 SHA를 확인했다. 현재 기준은 `34bb51dc087680c0d0329b766cba0b40fd431c2f`이며, 기능 매핑 `be64f9c1`, 의미 매핑 `715c4050`, 파일럿 `c0f81b7e`, 직전 준비 점검 `34bb51dc`를 포함한다. 정확한 전체 SHA와 읽은파일 해시는 [source_manifest.json](source_manifest.json)에 있다. 핵심 실행·평가·의존성 파일6개는 GitHub API로 실제 본문도 읽어 고정커밋/로컬 소스와 대조했다([github_source_checks.json](github_source_checks.json)).

112사례·Dev10질문·파일럿5질문, Dense/BM25/Hybrid·관점검색·A/B/C의 **기존 개발 구현과 결과**는 있다. 하지만 독립 Test 전용 묶음과 실행·평가 연결은 준비되지 않았다. `independent_test_readiness_report.py`는 상태 보고용이며 Test 추론 실행기가 아니다.

현재 코어 환경에서 기존 테스트7파일 **72개 통과**. BGE-M3의10개 파일해시를 확인하고 로컬CPU로 로드했다. encode와forward는0회다. 모델 로딩과단위검사는독립추천정확도나Test전체연결검증이아니다.

## 2. 독립 Test 준비 상태 종합표

아래43행은점검대상별상태다. ‘완료’는그행의구성요소가준비됐다는뜻이며전체Test실행준비완료를뜻하지않는다. 이43행과아래필수9개작업묶음은서로다른집계단위다.

|ID|분야|항목|상태|확인 사실·부족한 점|실제 근거|
|---|---|---|---|---|---|
|D01|데이터|미사용 독립 Test 질문|미완료|질문 경로 미확정. 새 Test 본문을 읽거나 질문을 만들지 않음.|[independent_test_readiness_20261028.json:26](https://github.com/comjung-star/AX-research/blob/34bb51dc087680c0d0329b766cba0b40fd431c2f/configs/independent_test_readiness_20261028.json#L26)|
|D02|데이터|독립 정답·판정 출처|미완료|정답 경로 미정. 파일럿103쌍도 사람채점0이며 대체 불가.|[independent_test_readiness_20261028.json:27](https://github.com/comjung-star/AX-research/blob/34bb51dc087680c0d0329b766cba0b40fd431c2f/configs/independent_test_readiness_20261028.json#L27) / [final_status.json:12](https://github.com/comjung-star/AX-research/blob/34bb51dc087680c0d0329b766cba0b40fd431c2f/docs/blind-pilot-five-queries-2026-10-28/final_status.json#L12)|
|D03|데이터|Test 입력 스키마|부분 완료|Dev/pilot 구조는 있으나 일반 Test manifest·입력 검증 계약 없음.|[semantic_mapping_run.py:118](https://github.com/comjung-star/AX-research/blob/34bb51dc087680c0d0329b766cba0b40fd431c2f/scripts/semantic_mapping_run.py#L118) / [blind_pilot_five.py:21](https://github.com/comjung-star/AX-research/blob/34bb51dc087680c0d0329b766cba0b40fd431c2f/scripts/blind_pilot_five.py#L21)|
|D04|데이터|미노출·독립 작성 이력|확인 불가|Test 명세가 없어 미사용·작성자·시점·중복을 실제 확인할 수 없음.|[readiness_gate.json:187](https://github.com/comjung-star/AX-research/blob/34bb51dc087680c0d0329b766cba0b40fd431c2f/docs/independent-test-readiness-2026-10-28/readiness_gate.json#L187)|
|D05|데이터|112사례·기존벡터|완료|112×1024 유한값 case행렬 및 로컬모델 해시 확인. 원본 변경 없음.|[model_check.json](model_check.json)|
|M01|알고리즘|A 규칙 계산·정렬|완료|코어 구현 및 기존 테스트 통과. 의미 정확도 증명은 아님.|[functional_mapping.py:28](https://github.com/comjung-star/AX-research/blob/34bb51dc087680c0d0329b766cba0b40fd431c2f/src/ax_research/functional_mapping.py#L28) / [functional_mapping.py:40](https://github.com/comjung-star/AX-research/blob/34bb51dc087680c0d0329b766cba0b40fd431c2f/src/ax_research/functional_mapping.py#L40)|
|M02|알고리즘|B 필드 임베딩 비교|완료|필드 추출·가용가중치 cosine 구현과 단위 검사 통과.|[semantic_mapping.py:15](https://github.com/comjung-star/AX-research/blob/34bb51dc087680c0d0329b766cba0b40fd431c2f/src/ax_research/semantic_mapping.py#L15) / [semantic_mapping.py:67](https://github.com/comjung-star/AX-research/blob/34bb51dc087680c0d0329b766cba0b40fd431c2f/src/ax_research/semantic_mapping.py#L67)|
|M03|알고리즘|C50:50 결합|완료|결합 함수·범위·동점 테스트 확인. 비율 변경 불필요.|[semantic_mapping.py:87](https://github.com/comjung-star/AX-research/blob/34bb51dc087680c0d0329b766cba0b40fd431c2f/src/ax_research/semantic_mapping.py#L87) / [test_semantic_mapping.py:59](https://github.com/comjung-star/AX-research/blob/34bb51dc087680c0d0329b766cba0b40fd431c2f/tests/test_semantic_mapping.py#L59)|
|M04|알고리즘|기존 알고리즘·모델 동결|완료|기존 파일/모델 해시와 코어 패키지 버전 확인. 새 Test 전체 동결과 구분.|[source_manifest.json](source_manifest.json) / [model_check.json](model_check.json)|
|M05|알고리즘|Dense/BM25·후보결합 구성요소|완료|case벡터·Kiwi초기화·기존560점검산기록·결합테스트 확인. Test연결실행은 안 함.|[blind_pilot_five.py:76](https://github.com/comjung-star/AX-research/blob/34bb51dc087680c0d0329b766cba0b40fd431c2f/scripts/blind_pilot_five.py#L76) / [bm25.py:44](https://github.com/comjung-star/AX-research/blob/34bb51dc087680c0d0329b766cba0b40fd431c2f/src/ax_research/retrieval/bm25.py#L44) / [verification.json:6](https://github.com/comjung-star/AX-research/blob/34bb51dc087680c0d0329b766cba0b40fd431c2f/docs/blind-pilot-five-queries-2026-10-28/verification.json#L6)|
|M06|알고리즘|원질문·관점 집계|완료|전체와 최고관점1:1 및 중복가산 없음 구현. Test관점 생성은 별도.|[semantic_mapping.py:83](https://github.com/comjung-star/AX-research/blob/34bb51dc087680c0d0329b766cba0b40fd431c2f/src/ax_research/semantic_mapping.py#L83) / [test_semantic_mapping.py:53](https://github.com/comjung-star/AX-research/blob/34bb51dc087680c0d0329b766cba0b40fd431c2f/tests/test_semantic_mapping.py#L53)|
|M07|알고리즘|새 Test 다중관점 절차|부분 완료|기존생성은OpenAI유료/3회반복. 승인·예산·신규관점캐시 필요. Dev관점 재사용 금지.|[openai_triplicate.py:57](https://github.com/comjung-star/AX-research/blob/34bb51dc087680c0d0329b766cba0b40fd431c2f/scripts/openai_triplicate.py#L57) / [openai_triplicate.py:76](https://github.com/comjung-star/AX-research/blob/34bb51dc087680c0d0329b766cba0b40fd431c2f/scripts/openai_triplicate.py#L76) / [openai_triplicate_search.py:83](https://github.com/comjung-star/AX-research/blob/34bb51dc087680c0d0329b766cba0b40fd431c2f/scripts/openai_triplicate_search.py#L83)|
|R01|실행기|독립 Test 전용 진입점|미완료|semantic CLI는freeze/run뿐이고 Dev118경로고정. readiness는보고프로그램.|[semantic_mapping_run.py:120](https://github.com/comjung-star/AX-research/blob/34bb51dc087680c0d0329b766cba0b40fd431c2f/scripts/semantic_mapping_run.py#L120) / [semantic_mapping_run.py:204](https://github.com/comjung-star/AX-research/blob/34bb51dc087680c0d0329b766cba0b40fd431c2f/scripts/semantic_mapping_run.py#L204) / [independent_test_readiness_report.py:26](https://github.com/comjung-star/AX-research/blob/34bb51dc087680c0d0329b766cba0b40fd431c2f/scripts/independent_test_readiness_report.py#L26)|
|R02|실행기|새 질문 파일 주입|부분 완료|파일럿 성공 구현은 있으나 config5질문·고정OUT 전용. 입력파일옵션 없음.|[blind_pilot_five.py:54](https://github.com/comjung-star/AX-research/blob/34bb51dc087680c0d0329b766cba0b40fd431c2f/scripts/blind_pilot_five.py#L54) / [blind_pilot_five_help.txt](blind_pilot_five_help.txt)|
|R03|실행기|Dense+A/B/C 동일조건 일괄 출력|부분 완료|pilot은ABC만;Dense는retrieval기록에만 있어 공식4조건출력·평가가 미연결.|[blind_pilot_five.py:74](https://github.com/comjung-star/AX-research/blob/34bb51dc087680c0d0329b766cba0b40fd431c2f/scripts/blind_pilot_five.py#L74) / [blind_pilot_five.py:84](https://github.com/comjung-star/AX-research/blob/34bb51dc087680c0d0329b766cba0b40fd431c2f/scripts/blind_pilot_five.py#L84)|
|R04|실행기|Top5/10/20 명시 저장|부분 완료|pilot은5/10명시.112순위에서20추출가능하지만 Test출력계약 없음.|[blind_pilot_five.py:85](https://github.com/comjung-star/AX-research/blob/34bb51dc087680c0d0329b766cba0b40fd431c2f/scripts/blind_pilot_five.py#L85) / [functional_mapping_run.py:107](https://github.com/comjung-star/AX-research/blob/34bb51dc087680c0d0329b766cba0b40fd431c2f/scripts/functional_mapping_run.py#L107)|
|R05|실행기|전체112순위·근거 보존|완료|기존15개전체순위·560쌍근거 구현/저장물 확인. 새 Test 결과는 아님.|[blind_pilot_five.py:85](https://github.com/comjung-star/AX-research/blob/34bb51dc087680c0d0329b766cba0b40fd431c2f/scripts/blind_pilot_five.py#L85) / [verification.json:5](https://github.com/comjung-star/AX-research/blob/34bb51dc087680c0d0329b766cba0b40fd431c2f/docs/blind-pilot-five-queries-2026-10-28/verification.json#L5)|
|R06|실행기|현재브랜치에서옛freeze명령 재사용|부분 완료|semantic freeze는HEAD==옛base를 요구. 현재HEAD불일치로 해당명령 그대로는 거부됨. 의도된보호장치.|[semantic_mapping_run.py:69](https://github.com/comjung-star/AX-research/blob/34bb51dc087680c0d0329b766cba0b40fd431c2f/scripts/semantic_mapping_run.py#L69) / [semantic_mapping_20261028.json:3](https://github.com/comjung-star/AX-research/blob/34bb51dc087680c0d0329b766cba0b40fd431c2f/configs/semantic_mapping_20261028.json#L3)|
|R07|실행기|Test ID·중복·완전성 검증|부분 완료|pilot ID검사는 있으나 일반N×112정답·미지qid·중복·부분정답 coverage 게이트 없음.|[blind_pilot_analyze.py:61](https://github.com/comjung-star/AX-research/blob/34bb51dc087680c0d0329b766cba0b40fd431c2f/scripts/blind_pilot_analyze.py#L61) / [semantic_mapping_evaluate.py:49](https://github.com/comjung-star/AX-research/blob/34bb51dc087680c0d0329b766cba0b40fd431c2f/scripts/semantic_mapping_evaluate.py#L49)|
|R08|실행기|새폴더·덮어쓰기·안전재개|부분 완료|분석기는기존출력거부. 예측save는고정경로쓰기이며 독립run-id·출력거부/재개계약 없음.|[blind_pilot_analyze.py:105](https://github.com/comjung-star/AX-research/blob/34bb51dc087680c0d0329b766cba0b40fd431c2f/scripts/blind_pilot_analyze.py#L105) / [semantic_mapping_run.py:38](https://github.com/comjung-star/AX-research/blob/34bb51dc087680c0d0329b766cba0b40fd431c2f/scripts/semantic_mapping_run.py#L38) / [blind_pilot_five.py:27](https://github.com/comjung-star/AX-research/blob/34bb51dc087680c0d0329b766cba0b40fd431c2f/scripts/blind_pilot_five.py#L27)|
|R09|실행기|실제 Test 명령·결과경로|미완료|검증된Test용CLI/전용경로계약 없음. 가상의 명령을 실행 가능하다고 안내할 수 없음.|[semantic_mapping_run_help.txt](semantic_mapping_run_help.txt) / [blind_pilot_five_help.txt](blind_pilot_five_help.txt)|
|V01|평가|P/R/F1@5/10/20|부분 완료|수식은 있으나Dev10문항/1120쌍/18양성과분모10·6고정.|[semantic_mapping_evaluate.py:22](https://github.com/comjung-star/AX-research/blob/34bb51dc087680c0d0329b766cba0b40fd431c2f/scripts/semantic_mapping_evaluate.py#L22) / [semantic_mapping_evaluate.py:53](https://github.com/comjung-star/AX-research/blob/34bb51dc087680c0d0329b766cba0b40fd431c2f/scripts/semantic_mapping_evaluate.py#L53)|
|V02|평가|nDCG@5/10|부분 완료|pilot 평가풀 IDCG함수는 있음. Test전체112/부분풀선택 및 정답입력 연결 없음.|[blind_pilot_analyze.py:54](https://github.com/comjung-star/AX-research/blob/34bb51dc087680c0d0329b766cba0b40fd431c2f/scripts/blind_pilot_analyze.py#L54) / [blind_pilot_analyze.py:78](https://github.com/comjung-star/AX-research/blob/34bb51dc087680c0d0329b766cba0b40fd431c2f/scripts/blind_pilot_analyze.py#L78)|
|V03|평가|질문수·Macro분모 일반화|미완료|Dev10/6,파일럿5 고정. 실제N·지표정의가능문항수로 계산하는Test평가기 없음.|[semantic_mapping_evaluate.py:77](https://github.com/comjung-star/AX-research/blob/34bb51dc087680c0d0329b766cba0b40fd431c2f/scripts/semantic_mapping_evaluate.py#L77) / [blind_pilot_analyze.py:86](https://github.com/comjung-star/AX-research/blob/34bb51dc087680c0d0329b766cba0b40fd431c2f/scripts/blind_pilot_analyze.py#L86)|
|V04|평가|미평가·보류 처리|부분 완료|pilot은미정처리. Dev는held를거부하고부분정답coverage정보를받지않음.|[blind_pilot_analyze.py:45](https://github.com/comjung-star/AX-research/blob/34bb51dc087680c0d0329b766cba0b40fd431c2f/scripts/blind_pilot_analyze.py#L45) / [semantic_mapping_evaluate.py:49](https://github.com/comjung-star/AX-research/blob/34bb51dc087680c0d0329b766cba0b40fd431c2f/scripts/semantic_mapping_evaluate.py#L49)|
|V05|평가|양성0 정책 통일|부분 완료|최근Dev는None. 구공통Recall은빈Gold에서0.0을반환함을경계호출로확인.|[evaluation.py:55](https://github.com/comjung-star/AX-research/blob/34bb51dc087680c0d0329b766cba0b40fd431c2f/src/ax_research/evaluation.py#L55) / [semantic_mapping_evaluate.py:25](https://github.com/comjung-star/AX-research/blob/34bb51dc087680c0d0329b766cba0b40fd431c2f/scripts/semantic_mapping_evaluate.py#L25) / [policy_probe.json](policy_probe.json)|
|V06|평가|질문별·알고리즘별 비교|부분 완료|Dev/pilot비교 구현은 있으나 Test4조건·실제N으로 연결되지 않음.|[semantic_mapping_evaluate.py:65](https://github.com/comjung-star/AX-research/blob/34bb51dc087680c0d0329b766cba0b40fd431c2f/scripts/semantic_mapping_evaluate.py#L65) / [blind_pilot_analyze.py:74](https://github.com/comjung-star/AX-research/blob/34bb51dc087680c0d0329b766cba0b40fd431c2f/scripts/blind_pilot_analyze.py#L74)|
|V07|평가|Dev vs 실제 Test 비교|부분 완료|현상태보고는Test칸null인표. 실제Test지표·정답기준차이 연결 기능은 없음.|[independent_test_readiness_report.py:72](https://github.com/comjung-star/AX-research/blob/34bb51dc087680c0d0329b766cba0b40fd431c2f/scripts/independent_test_readiness_report.py#L72)|
|V08|평가|Test 척도·임계값·평가범위|미완료|Dev>=3,pilot>=2 서로다름. Test척도/임계값/GT범위·O/D선택 미정.|[independent_test_readiness_20261028.json:29](https://github.com/comjung-star/AX-research/blob/34bb51dc087680c0d0329b766cba0b40fd431c2f/configs/independent_test_readiness_20261028.json#L29) / [blind_pilot_analyze.py:108](https://github.com/comjung-star/AX-research/blob/34bb51dc087680c0d0329b766cba0b40fd431c2f/scripts/blind_pilot_analyze.py#L108)|
|X01|환경|Python·설치 의존성|완료|Python3.13.13과모든v25고정패키지일치. 실제import/기존검사 정상.|[environment.json](environment.json) / [dependency_profiles.json](dependency_profiles.json)|
|X02|환경|BGE-M3 파일·로딩|완료|10파일해시일치,CPU float32로드성공,CLS1024/max4096. encode/forward0회.|[model_check.json](model_check.json)|
|X03|환경|CPU/GPU 요건|완료|현재CPU로로드 가능하며 GPU필수 아님. 현재cuda_available=false.|[semantic_mapping_20261028.json:17](https://github.com/comjung-star/AX-research/blob/34bb51dc087680c0d0329b766cba0b40fd431c2f/configs/semantic_mapping_20261028.json#L17) / [model_check.json](model_check.json)|
|X04|환경|실제Test시간·최대RAM·GPU성능|확인 불가|Test추론/부하시험 금지로 미측정. 모델파일약2.29GB가 총RAM최소요건은 아님.|[model_check.json](model_check.json)|
|X05|환경|비용 없는 범위|완료|원질문Dense/BM25/ABC는로컬실행가능. 새관점은별도유료경로. 이번키/유료호출0.|[blind_pilot_five.py:67](https://github.com/comjung-star/AX-research/blob/34bb51dc087680c0d0329b766cba0b40fd431c2f/scripts/blind_pilot_five.py#L67) / [openai_triplicate.py:76](https://github.com/comjung-star/AX-research/blob/34bb51dc087680c0d0329b766cba0b40fd431c2f/scripts/openai_triplicate.py#L76)|
|X06|환경|프로필 선택·다른PC재현|부분 완료|v25는정확pin이며현환경일치. rq1 SDK하한과v25고정버전은충돌. 현재오프라인ABC오류는 아님.|[requirements-rq1.txt:11](https://github.com/comjung-star/AX-research/blob/34bb51dc087680c0d0329b766cba0b40fd431c2f/requirements-rq1.txt#L11) / [requirements-v25-dev.txt:9](https://github.com/comjung-star/AX-research/blob/34bb51dc087680c0d0329b766cba0b40fd431c2f/requirements-v25-dev.txt#L9) / [dependency_profiles.json](dependency_profiles.json)|
|X07|환경|긴 입력·결측 사전 처리|부분 완료|4096초과는assert중단. UNKNOWN은지원하나Test입력검사·중단/제외정책을미리정해야함.|[semantic_mapping_run.py:137](https://github.com/comjung-star/AX-research/blob/34bb51dc087680c0d0329b766cba0b40fd431c2f/scripts/semantic_mapping_run.py#L137) / [semantic_mapping.py:69](https://github.com/comjung-star/AX-research/blob/34bb51dc087680c0d0329b766cba0b40fd431c2f/src/ax_research/semantic_mapping.py#L69)|
|G01|검증|안전한 기존검사|완료|기존7개테스트파일72개통과. CLI도움말3종확인. 독립정확도/새통합검사와는 다름.|[existing_tests.json](existing_tests.json) / [semantic_mapping_run_help.txt](semantic_mapping_run_help.txt)|
|G02|검증|독립Test 접근·누수게이트|부분 완료|원칙/Dev그룹감사는있으나 새Test의질문/출처/노출이력·중복검증 게이트없음.|[independent_test_readiness_20261028.json:39](https://github.com/comjung-star/AX-research/blob/34bb51dc087680c0d0329b766cba0b40fd431c2f/configs/independent_test_readiness_20261028.json#L39) / [leakage_audit.json:2](https://github.com/comjung-star/AX-research/blob/34bb51dc087680c0d0329b766cba0b40fd431c2f/docs/query-case-functional-mapping-2026-10-28/stage4_dev/leakage_audit.json#L2)|
|G03|검증|Test 전체 실행·평가 동결|부분 완료|코어는고정됐지만 Test연결부/입력계약/실제명령/출력run/평가기준의 최종manifest없음.|[freeze_snapshot.json:3](https://github.com/comjung-star/AX-research/blob/34bb51dc087680c0d0329b766cba0b40fd431c2f/docs/independent-test-readiness-2026-10-28/freeze_snapshot.json#L3)|
|G04|검증|예측 봉인 후 정답 개봉|부분 완료|영수증선검사 패턴은 있음. 구CLI/Dev검색은정답부터읽어 Test분리연결 필요.|[semantic_mapping_evaluate.py:38](https://github.com/comjung-star/AX-research/blob/34bb51dc087680c0d0329b766cba0b40fd431c2f/scripts/semantic_mapping_evaluate.py#L38) / [openai_triplicate_search.py:60](https://github.com/comjung-star/AX-research/blob/34bb51dc087680c0d0329b766cba0b40fd431c2f/scripts/openai_triplicate_search.py#L60) / [cli.py:75](https://github.com/comjung-star/AX-research/blob/34bb51dc087680c0d0329b766cba0b40fd431c2f/src/ax_research/cli.py#L75)|
|G05|검증|전용연결부의 전체 흐름 사전검사|미완료|전용연결부가 없어 검사불가. 기존Dev/기존fixture로네조건·지표·새폴더 흐름 검증 필요.|[existing_tests.json](existing_tests.json)|
|G06|검증|교수님 추적근거·보고형식|부분 완료|Dev보고/해시/전체순위근거는있음. 실제Test산출물과새run경로/공정비교계약은없음.|[test_execution_record.json:1](https://github.com/comjung-star/AX-research/blob/34bb51dc087680c0d0329b766cba0b40fd431c2f/docs/independent-test-readiness-2026-10-28/test_execution_record.json#L1)|
|G07|검증|독립 일반화·의미 정확도|확인 불가|독립Test/새사람평가없음.72검사와모델로드로정확도를확정하지않음.|[final_status.json:13](https://github.com/comjung-star/AX-research/blob/34bb51dc087680c0d0329b766cba0b40fd431c2f/docs/blind-pilot-five-queries-2026-10-28/final_status.json#L13)|

상태 합계: 완료13 / 부분 완료20 / 미완료7 / 확인 불가3. 이 숫자는 성능 점수도 결함 개수도 아니다. 확인 불가에는 미노출 Test의 실제 이력·일반화 성능과 미실시 부하/GPU성능이 포함된다.

## 3. 이미 준비된 기능과 프로그램

- **코어 A/B/C:** 규칙 계산, 필드 임베딩 비교, 고정 결합, 원질문/관점 집계와 동점 정렬이 구현돼 있다. 이번에 바꾸지 않았다.
- **검색:** 112개 기존 벡터·BM25 구현·후보결합 구성요소와 과거검산자료가 있다. 같은후보 전체순위를 저장하는 코드도 있다.
- **환경:** 실제 연구venv는Python3.13.13. numpy2.4.5 / torch2.12.0 / transformers5.12.0 / sentence-transformers5.7.0 / Kiwi0.24.1 / rank-bm250.2.2. requirements-v25-dev.txt의고정버전은현설치와전부일치했다.
- **모델:** 로컬CPU float32, CLS1024, max4096, threads4를 확인했다. GPU는없으며코드상필수도아니다. 모델파일총약2.29GB는필요전체RAM이나Test실행시간의측정값이아니다.
- **검사:** [기존 테스트 기록](existing_tests.json), [환경](environment.json), [모델 로드·해시](model_check.json), [의존성 프로필](dependency_profiles.json)을 저장했다. CLI `--help` 세 종류에는Test질문/정답/출력경로를받는일반옵션이없다.

기존prototype/CLI가있다는것도독립Test용A/B/C통합실행기의존재를의미하지않는다. 구 `ax_research.cli`는다른v1CSV와이전시스템목록을사용하며,최근112사례A/B/C네조건실행을바로제공하지않는다.

## 4. 추가로 필요한 데이터

다음은 **필요 구조의 설명**이며 이번에 만든 새 Test 데이터가 아니다.

|자료|필요한 내용|
|---|---|
|질문 파일|고유 query_id, 비어 있지 않은 원질문 text. 기존Dev10/pilot5와의관계·사용이력|
|정답 파일|고유(query_id,case_id), grade, 판정상태(판정/보류/미평가), 판정출처·버전|
|Test manifest|test_id, 질문/정답경로·해시, 112후보명세해시, 작성일/작성자·미사용근거, 라벨척도·정답범위|
|coverage 정보|질문별판정대상과누락/보류. 전체Recall/F1을원한다면각질문112후보전체정답이필요|

판정척도는아직미정이다. Dev는0~4점중3이상,파일럿은0~3점중2이상으로서로다르다. Test메타데이터와검증목적에맞춰**본문/점수를보기전에**확정해야한다. 사람이평가하지않았다면사람Gold로부르지않는다. 미평가사례를무관0점으로자동변환하면안된다.

같은112사례를Test검색후보로유지하는것은폐쇄코퍼스검색실험의조건이며그자체가누수는아니다. 분리할대상은질문·정답·튜닝/열람이력이다. 출처그룹은질문작성/판정독립성및향후학습누수를점검하는데사용하며,이번에후보를임의삭제/교체하지않는다.

## 5. 데이터 외 추가로 필요한 작업

### A. Test 전에 반드시 필요한9개 작업묶음

각묶음은별도로확인가능한완료조건을가진다. 동일코드제약이여러점검행에등장해도한묶음으로계산했다. B/C권장작업은총9개에서제외했다.

|ID|분류|필요 작업|왜 필요한가 / 해결 방법|프로그램 변경|데이터만으로 해결|
|---|---|---|---|---|---|
|D1|데이터|미사용 질문·manifest 확보|무엇을 검증하는지 식별하고 기존Dev·파일럿 재사용을 막아야 함 / 질문ID/본문·test_id·생성/노출이력·버전/해시를 별도 준비하고 봉인|이 항목 자체는 없음|이 항목은 데이터로 충족 가능. 전체 Test 실행은 여전히 불가|
|D2|데이터|독립 qrels·판정출처·범위 확보|관련 사례와 미평가를 구분하고 지원 지표를 결정해야 함 / query_id/case_id/grade/status와label_source·척도·판정자/합의·coverage 기록. 전체Recall/F1이면112후보 완전판정 필요|이 항목 자체는 없음|이 항목은 정답자료로 충족 가능. 평가기 연결은P2|
|P1|프로그램 및 환경|Test 전용 추론 입력·출력 연결부|현재Dev118경로/pilot5질문고정이며공식Baseline출력도없음 / 기존코어함수만호출하는별도어댑터. 같은112후보·질문·조건으로4개전체순위와Top5/10/20·점수·근거저장|필요: 실행연결부 추가/보완. 기존A/B/C 알고리즘 변경 불필요|아니오|
|P2|프로그램 및 환경|Test 전용 평가 입력·집계 연결부|Dev10/6/18/1120과pilot5고정. pooled nDCG만연결됨 / 기존수식재사용,일반ID/coverage검증·임계값·결측·동적Macro·4모델비교·Dev/Test출처차이를지원|필요: 평가연결부 추가/보완. 기존Dev평가기의보호assert삭제로대체하지않음|아니오|
|P3|프로그램 및 환경|전용run 경로·기존출력보호·실패보존|현재예측save는고정Dev/pilot경로를덮어쓸수있음 / 독립출력폴더에입력·설정·모델·예측해시와로그저장. 기존결과보존·중단시부분파일표시/같은조건재개정책|필요: 실행관리 부분 보완. 순위계산은 불변|아니오|
|E1|평가·검증|Test 평가 프로토콜 확정|Dev>=3와pilot>=2중임의선택·미평가0점화·불완전Recall을방지 / 질문/정답본문을보기전에메타데이터로정책결정. 원질문4조건최소안; nDCG gain/IDCG범위·0양성·보류·4096초과처리명시|모델 변경 없음. 정책 설정은 새 연결부에 반영|아니오: 판정/설계 결정이 필요|
|E2|평가·검증|독립성·누수·접근 분리 점검|파일럿이나이미본질문을독립Test로쓰지않고예측에정답이섞이지않게해야함 / Dev10·pilot5와질문ID/정규화문장·작성출처/노출이력을확인. 실제본문검사는동결후허용단계에서만. 예측봉인후정답개봉|검증절차/연결부 게이트 필요. 코어 변경 없음|아니오: 독립성 검증 기록이 필요|
|E3|평가·검증|실행 가능한 최종 동결 묶음 기록|옛freeze의HEAD/해시를우회하면동결증거가사라짐 / 기존코어해시는유지하고새연결부/정책/환경프로필/모델·벡터·입력해시/명령/결과경로를Git동결|코어 수정 없음. 완성된 연결부의 설정·해시 기록|아니오: 실행명세/검증승인이 필요|
|E4|평가·검증|기존 자료로 전체 연결 사전검사|72개기존테스트통과만으로새어댑터호환/분모/파일보호를보장못함 / 기존Dev 또는기존테스트fixture로정답비공개예측·ID오류·부분정답·0양성·분모·출력보호를확인. 실제미사용Test는사용안함|기존 코어 변경 없음. 연결부 검사/테스트 추가 가능|아니오|

우선순위는모두P0(최종실행전게이트)다. E1과D1/D2의명세확정, P1/P2/P3준비, E4연결검사와E2/E3최종승인의순서로의존관계를가진다. 데이터가이미봉인돼있다면P1/P2/P3는기존Dev/fixture만으로먼저준비할수있다. 자세한각작업의부족한점·해결·완료기준은 [required_actions.json](required_actions.json)에있다. 이번에는이보완을구현하지않았다.

### B. Test 전 준비하면 좋은 일

|작업|필요성|코드/데이터·우선순위|
|---|---|---|
|B1 파일럿103쌍 사람 채점·기능근거 감사|정밀매핑의의미한계를미리파악하되파일럿을Test로승격하지않음|없음 / 사람평가 입력 필요 / 권장 높음; 독립Test데이터가준비돼있다면기계적실행의필수조건은아님|
|B2 환경 프로필 명시·다른PC 재현 확인|현v25설치정상이나rq1/v25 SDK프로필은혼합불가.로컬모델경로도별도준비필요|환경/실행안내 정리. 코어 수정 없음 / 아니오 / 권장 높음|
|B3 기존 자료 기준 RAM/시간·긴 입력 점검|Test를돌리지않아대량/긴입력부하와GPU성능미확인|검사만, 알고리즘 변경 없음 / 아니오 / 권장 중간|
|B4 반복/질문별 변동·불확실성·실패유형 보고양식|평균만보지않도록질문별득실과라벨차이를명확히설명|분석/보고 보조기능만 선택 / 아니오 / 권장 중간|
|B5 다중관점 Test를 할 경우 별도 승인·예산·프롬프트 동결|원질문4조건만으로는유료호출불필요.관점효과까지주장하려면동일Test에서새관점이필요|생성/캐시 연결부만, 코어 불변 / 아니오 / 관점조건을선택하면해당조건의선행필수.원질문최소안에서는선택|

### C. Test 이후로 미뤄도 되는 일

|작업|이후에 해도 되는 이유|코드 변경|
|---|---|---|
|C1 규칙·가중치·필드추출·추천수 개선|성능개선 과제이며현재모델검증의필수조건아님.같은Test를보고수정하면다음평가는새Test사용|예|
|C2 임베딩파인튜닝/학습형Interaction|새알고리즘연구.현재A/B/C고정검증에불필요|예|
|C3 Factor/Wald/Graph/전략추천 확장|별도연구범위이며현재Test실행조건아님|예|
|C4 프로토타입·UI·배포 개선|명령형실험의필수조건아님|예|

## 6. 실제 확인된 문제점과 위험

### 실제 코드에서 확인한 제약·정책 차이

1. **Dev 전용 고정값:** semantic실행기는118경로·108관점을요구하고평가기는10문항·1120쌍·18양성·평균분모10/6을요구한다. 새Test를그대로넣을수없다.
2. **파일럿 전용 집계:** 파일럿평가기는K5/10,질문수5와분모5를고정한다. 전체112후보Recall/F1을계산하는프로그램이아니다.
3. **명시 출력·대상 부족:** 파일럿은ABC만공식출력하며Top20키가없다. Dense순위와전체112순위가있어추출은가능하지만전용4조건계약은필요하다.
4. **경로/동결 보호:** 예측save는고정연구폴더에쓴다. 옛semantic freeze의HEAD검사는현재브랜치와불일치한다. 이를검사삭제/우회로해결해서는안된다.
5. **빈Gold 정책 차이:** 구공통 `recall_at_k([],[],5)`의실제반환값은0.0이다. 최근Dev함수는양성0이면None이다. 구함수를Test에그대로쓰면요청한‘미정’정책과달라진다. 현재Dev수치가틀렸다는발견은아니다.
6. **환경 프로필 충돌:** rq1의OpenAI>=3.26.0과v25의==2.32.0은동시에만족할수없다. 현재v25프로필과오프라인ABC환경은정상이며,API용프로필을무작정합치는것이위험하다. pyproject.toml의dependencies는빈목록이므로 pip install -e .만으로연구의존성전체가설치되지도않는다. 다른PC에서는정확한프로필과로컬가중치를명시해야한다.

### 발생을 확인하지 않은 위험

미지query_id나중복/누락정답이positive집합에섞여미평가를음성으로취급하는일,고정폴더재실행으로기존예측을덮어쓰는일,4096토큰초과중단,새PC에서모델/프로필경로가달라지는일은**가능성/제약분석**이다. 실제독립Test에서그런오류가났다는뜻은아니다. 테스트72개는기존구현검사이며이위험의새통합경로를검증하지않는다.

모델로드중기존차원조회메서드의FutureWarning이있었으나정상로드됐다. 현재오류가아닌향후버전드리프트주의사항이며,지금코어를고쳐야한다는결론은아니다. 첫Test를위해규칙미인식33개를억지로고치거나결합비율을다시탐색할필요도없다. 그것이현재모델의평가대상이다.

## 7. 실행 가능 여부: 네 가지 질문에 대한 답

**Q1. 질문·정답만 있으면 바로 가능한가? → 아니오.** P1/P2/P3와E1~E4가남아있다. 데이터만추가하면새명세입력·분모·평가정책·출력보호에서다시중단될수있다.

**Q2. 새 알고리즘이 필요한가? → 필요 없다.** 현재코어A/B/C와Dense를그대로호출할수있다. 필요한것은실험용연결부·검증·기록이며새랭킹모델/학습/프로토타입이아니다. 기존Dev보호assert를삭제해Test에맞추는방법은추천하지않는다.

**Q3. 실제 오류나 누락이 있는가? → 기능누락/정책차이는확인됐다.** 일반Test진입점/입력계약/동적집계/전용4조건출력이없고구빈Gold정책이다르다. 반면이번기존72개검사와로컬모델로드는성공했다. 새로운독립Test실행오류나추천오류는관찰하지않았다.

**Q4. 가장 빠르고 안전한 최소순서는? → 다음8절의필수게이트순서다.** 새학습·UI·그래프·가중치최적화는추가하지않는다.

## 8. 반드시 해결할 작업 우선순위

1. **E1 / D1 / D2:** 원질문최소4조건인지·라벨척도/정답범위/임계값·명세를정하고미사용자료를확보한다. 본문은아직봉인한다.
2. **P1 / P2 / P3:** 코어를바꾸지않는추론/평가/저장연결부를별도구현한다. 기존Dev·fixture만사용한다.
3. **E4:** 4조건·일반N·지표·오류/결측·출력보호를처음부터끝까지검사한다.
4. **E2 / E3:** 미노출/독립성근거,예측-정답분리,실제명령·환경·코드/입력/출력해시를확정하고Git동결한다. 허용된개봉시점의실제중복검사는추론전수행한다.
5. 위게이트와별도실행승인후에만독립Test를한번실행하고예측봉인후평가한다. 이번에는실행하지않았다.

## 9. 앞으로의 권장 진행 순서와 비용

가장작은유료0안은**원질문 Single Dense+A/B/C**다. 기존로컬가중치와사례벡터를재사용하고새질문의벡터만후속실험에서계산하면된다. 이번점검에서는그질문벡터도만들지않았다. GPU나새모델다운로드는현재필수가아니다.

새동적관점효과까지주장하려면동일Test에새관점이필요하다. 그조건은기존유료OpenAI절차와동일반복/프롬프트/캐시·예산을별도로승인해야한다. 이번키/유료API호출은0이다. 기존Dev관점을새Test에재사용하거나임의수작업관점으로대체하면안된다.

현재실제로검사한명령은 [existing_tests.json](existing_tests.json)과세도움말기록에있다. 연구venv의절대Python경로도 [environment.json](environment.json)에남겼다. 독립Test의실제실행명령은전용어댑터가없어아직없다. 없는모듈명/옵션을실행법으로제시하지않는다.

규칙·의미역개선이나비율조정은현재모델의Test를보고후속연구로검토할수있지만,그Test를다시최종일반화증거로쓰면안된다. 모델수정후에는새미사용Test가필요하다.

## 10. 결론

**현재 독립 Test를 진행하기 위해 필요한 것은 총 9개 항목이며, 그중 데이터 관련 2개, 프로그램 및 환경 관련 3개, 평가·검증 관련 4개입니다.**

이숫자는위에서정의한9개의필수완료조건묶음이며모든문제의절대개수나개발시간추정이아니다. 환경은현재정상임을확인했으므로‘새GPU구매’나‘새모델학습’을필수로세지않았다. 확인불가인실제Test시간/의미정확도등을임의수치로채우지도않았다.

이번산출물은준비상태점검보고서와근거기록뿐이다. 기존프로그램·정답표·Dev결과·다른연구브랜치/main은수정하지않았다. 독립Test본문/정답은열지않았고,새질문·정답·성능수치·추천추론도만들지않았다.
