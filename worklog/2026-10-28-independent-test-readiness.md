# 1차 독립 Test 실행 요청 사전 점검

## 단위1: 원격 및 메타데이터

- 사용자지시서전체확인. 지정3브랜치fetch/ls-remote로최신SHA확인. 기준파일럿c0f81b7e에서신규 research/independent-test-readiness-20261028 생성.
- Test질문/정답본문은읽지않고파일이름/메타데이터만점검. 준비기록의heldout_test_queries0/heldout_testfalse와최신파일럿사람채점0을확인. 과거준비기록은역사적메타데이터로취급.
- 추적경로·data/experiments/configs/.local파일명검사에서독립Test패키지미확인. train_holdout_audit.csv는과거Dev개선감사경로이며독립Test로확인되지않아대체금지. 실제본문미열람.
- 알고리즘동결기록과실행차단평가게이트를먼저커밋한다. Test라벨척도/임계값도없어null로남기며실행용평가프로토콜완료로과장하지않는다. 사용자예외지시에따라추론/평가중단.
