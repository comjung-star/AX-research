# Work A · 2026-10-28

기준1e9523ed, 신규 research/independent-test-runner-20261028. 다른Work와분리한 AX-independent-test-runner Git worktree에서만 작업. 앱 worktree도구가하위저장소를허용하지않아표준Git worktree로분리했다. 기존작업디렉터리수정없음.

1. 기존AGENTS/HANDOFF, 준비감사README/required_actions, frozen pilot/semantic/functional runner와코어/설정검토. 기존코어/데이터/정답수정없음.
2. 질문·정답본문을보지않고 ax-heldout-v1 정책등록. 커밋5fe1942a:0~3,관련>=2,보류/미평가null,완전112판정에만Recall/F1/nDCG. Macro정의가능분모기록. 기존Dev>=3과직접성능차이계산금지.
3. 별도heldout모듈과CLI추가. 기존코어재사용, 네방식112전체순위·Top5/10/20·근거, 모델/입력/설정해시, 외부출력폴더/run-id독점생성, 실패보존, 완료봉인후평가, 출처분리, 네트워크차단. 새Test본문을읽지않음.
4. 신규36검사+기존72검사=108통과. 부분정답·보류·무양성·ID오류·출처·변조·실패·덮어쓰기검사포함. 실제Dev질문2개로CPU BGE-M3/기존벡터 연결, 네방식x2회추천·평가. 모든112순위가재현되며기존Dev순위8/8정확일치. Dev원점수는원본보존한채연결시험에서만새계약으로읽음. 이수치는Test성능이아님.
5. 최종코드버전으로종단간재검사후보고서·원시로그보존. 기존tracked파일변경0, 보호파일SHA동일. 키/WorkB데이터열람0,유료API0,비용0. 비밀패턴검사추가파일·개발로그내0건.

완료기능12묶음. P1/P2/P3/E1/E3/E4프로그램측완료. E2의정답분리·정확중복게이트는구현했지만WorkB의실제독립성/의미중복/출처확인은자료수령후필수다. 새Test자료를만들거나열지않았다. 입력계약충족및독립성승인뒤에만실제Test명령실행. 자동재개는하지않고실패기록보존후새run-id사용.

세부명령/로그/사용법: docs/independent-test-runner-2026-10-28/README.md 및 verification.json, smoke_receipt.json, test_receipt.json, dev-smoke/.
