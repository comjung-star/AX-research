# AX 나침반 프로토타입 · 실제 완료 결과

**2026-10-25 전략 출력 업데이트:** 사례 추천에서 끝내지 않고 **실제 기업의 해결 방식 → 우리 업무의 적용 전략 → 실행 순서 → 준비사항·한계 → 근거 사례**까지 연결했습니다. 현재 시연 내용은 [전략 출력 업데이트](prototype-strategy-demo-2026-10-25.md)를 우선 참고하세요. 아래의 최초 인도 당시 기능 범위·테스트 수는 이력입니다.

**완료일: 2026-10-24 (KST) · 시연 예정: 2026-10-25 · 이 PC에서 실행 확인**

**2026-10-25 실제 API 최종 확인:** 사용자가 `.env`에 등록한 키를 서버에서 읽어 **실제 `gpt-6-luna` 호출에 성공**했습니다. 연결 확인 요청에서는 3개 관점을 생성했습니다. 별도의 새 업무문제로 **실시간 LLM 관점 2개 → 각 관점의 Dense 사례 3개씩** 추천하는 전체 흐름도 성공했습니다(해당 실제 요청 4.64초, 입력 235 / 출력 113토큰). 키 값은 출력·결과 기록에 포함하지 않았으며 `.env`의 Git 제외도 확인했습니다. 아래의 키 미설정 설명은 최초 인도 당시 기록이며 현재 상태는 이 최종 확인이 우선합니다. [실제 LLM→Dense 결과 JSON](prototype-validation/live-api-result.json) · [연결 성공 화면](prototype-validation/api-connected.jpg) · [최종 검증 기록](prototype-validation/verification.json).

**API 연결 후속 업데이트:** 상단 API 연결 창, 실제 LLM 응답을 이용한 연결 검증, Windows 자격 증명 관리자 저장(선택), 연결 해제, 연결 후 실시간 모드 기본 선택을 추가했습니다. 키는 소스·브라우저 저장소·추천·평가 기록에 저장하지 않습니다. 최초 인도의 환경변수 전용 방식 설명과 키 미설정 기록은 아래에 보존하며, 현재 키 설정은 화면 또는 환경변수로 할 수 있습니다. 성공 표시와 `llm_evidence`는 실제 API 응답을 받은 경우에만 생성합니다. [추가 동작 테스트](prototype-validation/api-connection-tests.xml) · [연결 화면](prototype-validation/api-connection.jpg).

후속 검증: **전체 189개 통과**(프로토타입 28개 + 기존 연구 161개). 모의 API로 연결 등록 전 실제 호출 경로 통과 여부, 실패 시 기존 키 보존, 키 비노출, 연결 해제, 저장 동의·경로, 인증 오류 안내를 검증했습니다. 실제 키를 입력하기 전에는 유료 API 성공으로 표시하지 않습니다. 사용자가 화면에서 키를 연결한 후 `python scripts/validate_prototype_delivery.py --live`를 실행하면 유료 LLM→Dense 요청 1회로 검증하고 `prototype-validation/live-api-result.json`에 키 없는 실행 증거를 저장할 수 있습니다.

바탕화면 **AX나침반.exe**를 실행하면 <http://127.0.0.1:8765>에서 한국어 웹 프로토타입이 열립니다. 실행파일을 통해 실제 서버 시작과 브라우저 자동 열림을 확인했습니다. 이 실행파일은 현재 PC의 Python·프로젝트를 연결하는 Windows 실행기이며, 다른 PC로 exe 하나만 복사하는 독립 설치 패키지는 아닙니다.

## 구현한 흐름

```text
자연어 업무문제
  → 실시간 모드: LLM 동적 문제관점 1~6개
  → 예시 데모: 기존 LLM runtime 관점(run 1) 재생
  → 자유 입력 데모: 로컬 문장 분리 (LLM 아님)
  → 기존 BGE-M3 1024d Problem / Task / Context 개별 유사도
  → 3-view 유사도 평균 Dense 순위
  → 관점별 독립 Top-K (1~10개, 기본 3개)
  → 원본 사례·출처·사례의 Factor/Strategy 분류·근거 경로·한계
  → 유용함 / 부분적 / 무관, 자유의견
  → 로컬 SQLite 저장 및 CSV / JSON 내보내기
```

다른 관점의 사례를 한 전역 순위로 합치거나 중복 제거하지 않습니다. 동일 사례가 두 관점에 등장하면 평가도 관점별로 보존합니다. 검색에 Solution View를 입력하지 않으며, 평가용 reference 관점·qrels도 런타임에서 읽지 않습니다.

학습형 256d QCI는 기본 검색을 덮어쓰지 않습니다. 고급 옵션에서 **기존 예시의 LOQO QCI Top-10 재생**만 선택할 수 있습니다. 저장된 모델 가중치의 새 입력 추론·재학습을 수행했다고 표시하지 않습니다.

최초 인도 당시 전략 영역은 frozen 전략 분류를 묶은 검토 후보였습니다. 10월 25일에는 선택 사례에 근거한 LLM 적용 전략 설명 단계를 연결했습니다. 다만 Wald, 학습형 Factor Anchor/Evidence Fusion의 새로운 성능 검증을 완료했다는 뜻은 아닙니다. 사례 원인 라벨이 사용자의 확정 원인이라는 주장이나 인과효과 주장을 하지 않습니다.

## 실제 검증 결과

| 검증 | 확인한 결과 |
|---|---|
| 전체 회귀 테스트 | **182 passed, 0 failed, 0 skipped** (새 프로토타입 21개 + 기존 연구 161개) |
| 테스트 경고 | 기존 `test_stage2_gated_runner.py`의 Torch 텐서→스칼라 변환 경고 1건. 실패 없음, 기존 코드 변경 안 함 |
| 예시 10개 | 원본 LLM runtime 관점 개수·내용 유지, 각 관점의 Dense 순위를 다시 계산 |
| 기존 결과와 수치 대조 | 원래 256d 비교 실험에 실린 Dense Top-10 사례·순위·점수와 일치 |
| 새 자유 입력 | 실제 BGE-M3 인코더 실행, 문장 2개에서 독립 Dense 추천 확인 |
| 새 질문 첫 상위 사례 | 사내 지식검색 → Morgan Stanley `AXV2N_0110`; 이메일 후속조치 → Epilot `AXV2H_0002_01` |
| 실제 소요시간 예 | 브라우저에서 첫 로컬 모델 준비 포함 57.77초, 같은 프로세스 재검색 약 0.3초. 환경별 차이가 있으며 성능 벤치마크 아님 |
| 인코더 호환성 | 저장된 `V21D001 / run1 / P1` 임베딩과 재계산 임베딩 코사인 약 1.0000001 (부동소수점 오차) |
| 실제 화면 동작 | 예시 선택 → 추천 → 근거 펼치기 → 사례 평가 저장 → 자유의견 저장 → CSV 다운로드 확인 |
| 평가 보존 | 동일 관점·사례의 수정은 중복 없이 갱신, DB를 다시 열어도 기록 유지 |
| 작은 화면 | 가로 390px에서 콘텐츠 가로 넘침 없이 추천 카드 배치 확인 |
| 브라우저 오류 | 최종 화면에서 JavaScript error 로그 없음 |
| 실시간 LLM | 동적 스키마 파싱·호출 인자·오류 메시지의 키 비노출은 모의 테스트 통과. **키 미설정으로 실제 유료 API 호출은 미검증** |
| 키 없는 오류 처리 | 실시간 모드를 선택하면 키 설정 안내. 예시 재생으로 조용히 대체하지 않음 |

새 질문 검증 원문과 실제 결과는 [실제 Dense 결과 JSON](prototype-validation/custom-dense-result.json)에 있습니다. [기계 판독 검증 기록](prototype-validation/verification.json), [전체 테스트 원시 결과 XML](prototype-validation/tests.xml)도 제공합니다. 검증 스크립트는 실행 중인 로컬 앱을 통해 결과를 다시 확인하고 Git 원본 보존 여부를 검사합니다.

## 연구 자료 보존

- 기준은 GitHub `experiment/v23-runtime-perspective-qrels-20261024`의 커밋 [`000b7f42f594bd4b57aa55df1661d7ff3750353c`](https://github.com/comjung-star/AX-research/commit/000b7f42f594bd4b57aa55df1661d7ff3750353c)입니다. 최신 256d QCI 비교 결과를 포함합니다.
- 기존 `AX-research` 폴더의 작업을 유지하고, 별도 **`AX-prototype`** 작업본에서 구현했습니다. 기존 폴더의 미추적 감사 문서·스크립트 3개도 그대로 남습니다.
- frozen 84개 사례, 분류사전, 원본 관점·임베딩, 실험·연구 코드 등 **추적된 연구 파일 1,496개**에 변경이 없음을 확인했습니다. 주요 입력 6개 SHA-256을 검증 JSON에 기록했습니다.
- 새로운 한국어 읽기용 카드 요약은 `prototype/case_display_ko.json`에 분리했습니다. 84개 원본·라벨·검색 인덱스를 덮어쓰지 않았습니다.
- GitHub의 기존 브랜치·결과·Actions를 변경하지 않았습니다. **신규 구현은 로컬 완료 상태이며 commit/push하지 않았습니다.**

## 평가 기록과 보안 동작

실제 시연용 DB는 `.local/ax-prototype/feedback.sqlite3`이며 인도 시 저장 평가 **0건**으로 준비했습니다. 자동 브라우저 점검 데이터는 `.local/qa-feedback.sqlite3`에 분리했습니다. 저장 동의를 하고 저장 버튼을 눌렀을 때만 해당 입력·추천과 평가를 영구 기록합니다. 기록은 연구 정답표로 자동 반영하지 않습니다.

API키는 서버 환경변수에서만 읽으며 화면·소스·실행파일·평가 내보내기에 넣지 않습니다. 오류 메시지에 상위 API의 예외 본문을 노출하지 않습니다. 입력·댓글에 붙은 알려진 키 형식은 저장 전에 가립니다. localhost 전용 바인딩, Host/Origin 검사, 요청 토큰, 정적 파일 허용 목록, 요청 크기 제한, HTML 텍스트 안전 출력, CSV 수식 주입 방어를 적용하고 관련 동작을 테스트했습니다. 민감정보 자동 비식별화나 외부 공개 서비스 보안을 인증한 것은 아닙니다.

## 화면과 실행 안내

- [실행·모드 구분·평가 방법·API키 설정·재현 안내](prototype-demo-guide-2026-10-24.md)
- [시작 화면](prototype-validation/home.jpg)
- [예시 추천 화면](prototype-validation/example-results.jpg)
- [새 질문의 실제 Dense 화면](prototype-validation/custom-dense.jpg)
- [작은 화면](prototype-validation/mobile.jpg)
- [이전 256d QCI 연구 결과](https://github.com/comjung-star/AX-research/blob/000b7f42f594bd4b57aa55df1661d7ff3750353c/docs/v23-qci256-four-step-final-results-2026-10-24.md)
- [이전 연구의 성공한 GitHub Actions](https://github.com/comjung-star/AX-research/actions/runs/40096426618)

내일은 예시 1~2개로 연구 목적을 설명한 뒤, 자유 입력과 사례 평가를 함께 시도하면 됩니다. 현재 프로토타입은 사용자의 유용성 의견을 받을 수 있는 실행 결과이며, 추천 성능 개선이나 독립 Test 완료를 주장하는 결과는 아닙니다.
