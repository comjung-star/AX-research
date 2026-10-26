# Gemini 404 진단과 실제 생성 테스트

2026-10-27 한국시간. 사용자 추가 요청에 따라 Gemini만 진단했다. **Gemini 3.5 Flash-Lite에서 실제 생성 HTTP200/OK를 확인했다. 전체 정답 평가·다른 공급자 재호출·Stage4 Test는 실행하지 않았다.**

## 확인 결과

| 순서 | 요청 | 결과 | 시간 | 근거 파일 |
|---|---|---|---:|---|
| 1 | 기존 2.5 Flash-Lite, 기존 옵션 그대로 생성 | HTTP404 / NOT_FOUND 재현 | 0.537초 | generation_legacy_original.json |
| 2 | 같은 2.5 모델, thinkingConfig만 제거 | HTTP404 / NOT_FOUND | 0.445초 | generation_legacy_minimal.json |
| 별도 | 3.5 Flash-Lite 단일 모델 정보 GET | HTTP200, generateContent 지원 표시 | 0.350초 | metadata_current_minimal.json |
| 3 | 3.5 Flash-Lite, minimal, 256토큰, 45초 대기 | 응답 전 대기 제한 도달 | 45.183초 | generation_current_minimal.json |
| 4 | 같은 3.5 모델·같은 요청 본문, 120초 대기 | **HTTP200, 실제 OK 응답** | **32.196초** | generation_current_extended_timeout.json |

처음에는 생성 진단 최대3회로 제한했다. 새 모델의 45초 대기 실패 후 사용자가 요청한 오류 분석 범위에서 대기 시간만 늘린 비교1회를 추가했다. 총 생성 POST4회+읽기전용 metadata GET1회이며, 동일 요청의 무제한 자동 재시도는 없다. 진단 전체 비용 사전 예약 추정액은 입력1,000토큰씩 가정해 **$0.0021312**, 제한은 $0.01이었다. 이전 2026-10-26의 3개 공급자 테스트는 다시 실행하지 않았다.

## 원인 분석: 사실과 추정

**확인된 사실**

- 키를 바꾸지 않고 같은 호스트·같은 `v1beta`·같은 `generateContent` 방식에서 새 모델은 생성에 성공했다. 전반적인 키 인증 실패나 URL 형식 오류로 설명할 근거는 없다.
- 2.5는 기존 설정과 thinkingConfig를 제거한 설정 모두404다. 따라서 thinkingBudget 옵션 하나만의 문제라는 설명은 지지되지 않는다.
- 모델 목록/모델 정보 GET200은 생성 가능성 자체를 보장하지 않는다. 2.5의 이전 목록 조회와3.5의 이번 정보 조회를 실제 POST 결과와 분리해 기록했다.
- 3.5의 첫 요청은45초 안에 응답이 도착하지 않았고, 별도 비교 요청은32.196초에 끝났다. 간헐적인 응답 지연이 관찰됐다. 후자의 성공이 항상32초 이내 응답하거나120초 설정만으로 모든 문제가 해결된다는 증거는 아니다.

**공식 문서와 일치하는 유력한 설명**

Google의 [모델 접근/종료 정책](https://ai.google.dev/gemini-api/docs/deprecations)은2.5 계열의 접근을 과거 적극 사용한 사용자로 제한하고 신규 프로젝트에는3.5 Flash-Lite/3.8 Flash를 권장한다고 안내한다. 이번은 신규 발급 키이며2.5 생성만404가 나므로 **기존 모델에 대한 프로젝트별 접근·서비스 제공 조건**이 원인일 가능성이 높다.

다만 실제 오류 응답에는 그 정책의 계정별 적용 이유가 명시되지 않았다. 계정/프로젝트의 내부 권한과 과거 사용 이력을 조회하지 않았으므로 **특정 정책이 이 계정에 적용됐다고 확정할 수는 없다**. 확인 가능한 운영 결론은 '원래2.5 생성은 실패하고, 같은 키의3.5 생성은 성공한다'다. 원인이 사용자의 키 오타라고 단정하거나 Google 전체 장애라고 일반화하지 않는다.

[공식 오류 안내](https://ai.google.dev/gemini-api/docs/generate-content/api-errors)의404는 NOT_FOUND 리소스 오류이며, 인증/결제 문제와 구분된다. 오류의 원문·헤더·프로젝트 식별자는 저장하지 않고 RPC 상태와 제한된 진단 플래그만 보존했다. Google의 공개 상태 페이지도 확인했지만 읽을 수 있는 장애 정보가 없어 전체 장애 여부를 판정하지 않았다.

## 검증된 연결 설정과 사용 범위

`configs/gemini_connection_20261027.json`에 다음 값을 저장했다.

- 모델 `gemini-3.5-flash-lite`, API `v1beta`, 메서드 `generateContent`.
- `thinkingLevel=minimal`, 출력 최대256토큰, 대기120초, 자동재시도0.
- 키는 기존 `GEMINI_API_KEY` 환경변수를 사용하며 `x-goog-api-key` HTTPS 헤더로만 보낸다. 키 값·URL query의 키·원시 오류·응답 본문을 저장하지 않는다. redirect도 차단한다.
- 실제 응답은 비어 있지 않고 `OK`와 일치했으며, 응답 모델도 `gemini-3.5-flash-lite`였다.

이 설정은 **연결 검증용**이다. 관련도 판정의 한국어 품질, 구조화 출력, 대량 처리 rate limit, 라벨 신뢰성은 검증하지 않았다. 세 공급자의 생성 연결은 각각 성공 기록을 갖지만, 그것이 전체 정답 평가 실행 승인이나 완료를 뜻하지 않는다. 연구 Stage1의 라벨·검증 조건은 별도로 유지한다.

기존 `scripts/test_stage1_api_connections.py`와2026-10-26 결과/ledger는 당시2.5 실패 이력으로 보존했다. 이번의 확인용 현재 모델 설정은 위 새 JSON과 `scripts/diagnose_gemini_connection.py --case current_extended_timeout`을 기준으로 한다. 이미 실행한 진단 case는 별도 예약 파일로 재호출을 막는다. 사용자가 새로 승인한 범위 없이 ledger를 삭제해 재실행하지 않는다.

## 비용

성공한 요청은 입력 **5토큰**, 출력/보고된 생각 토큰 합계 **1토큰**이다. [공식 Gemini3.5 Flash-Lite 표준요율](https://ai.google.dev/gemini-api/docs/pricing)인 입력100만토큰당$0.30·출력$2.50 기준 **$0.000004**다. 이것은 성공 요청 사용량의 가격 환산이며, 무료 tier 여부나 최종 청구액을 확인한 것은 아니다.45초 대기 실패 요청은 서버에서 처리가 계속됐을 가능성이 있어 과금0으로 확정하지 않는다.404 요청의 실제 청구도 확인하지 않았다.

이전의 전체 Stage1 예상액은 Gemini2.5 요율을 사용했다. Gemini3.5를 실제 평가에 채택한다면, 모델당4,480판정·판정당입력1,000/출력150 가정의 Gemini 비용은 **$3.024**, 기존 OpenAI·Claude 추정과 합계는 **$11.648**다. 세금·재시도·생각 토큰 추가·batch 공유·별도 reference검증 비용은 달라질 수 있다. 총$15 초기안은 제안이며 모델별 배분은 재검토해야 한다. **이번에 전체 정답 평가를 시작하지 않았다.**

## 재현·보존

새 진단 코드·case별 요청 해시·RPC 오류 요약·응답 사용량·설정·테스트를 저장했다. timeout을 제외한3.5 두 요청 본문 해시는 같으며 비교할 수 있다. 키 설정은 변경하지 않았다. 기존 원본/동결 데이터·qrels·과거 실험·기존 연결 결과는 보존했다. GitHub 업로드나 main 병합은 수행하지 않았다.

현재 도구 실행은 기존 예약 때문에 같은 case의 추가요청을 거절한다. 단위 테스트는 가짜 응답만 사용하며 API를 호출하지 않는다.

```powershell
$env:PYTHONPATH='src;.'
& ..\AX-prototype\.venv\Scripts\python.exe -m pytest tests/test_gemini_diagnosis.py tests/test_stage1_api_connections.py tests/test_reduced_stage123_audit.py -q
```
