# AX 나침반 · 2026-10-28 실시간 사례 탐색

상단의 **아키텍처 흐름도**, **논문 진행 현황** 버튼으로 안내 팝업을 연다. 닫기 버튼, Esc 또는 팝업 바깥 클릭으로 닫는다. 흐름도는 현재 실행 앱의 경로를 설명하며, 진행 현황은 2026-10-28 연구 스냅샷에 근거한다. 다른 작업 공간의 이후 진행상황이나 원고 완성률을 추측하지 않는다.

## 실시간 관점 생성 업데이트

현재 기본 화면은 자연어 입력 → 실제 OpenAI LLM 관점 생성 → 각 관점의 112개 사례 검색 → 결합 Top5까지 실행한다. 바탕화면의 「AX 나침반」 실행기를 사용한다. 기존 브라우저는 새로고침한다.

기존 AX-prototype의 로컬 환경 설정 또는 Windows 보안 저장 연결을 재사용한다. 키는 화면·로그·Git에 노출하지 않는다. 매 검색마다 입력 업무문제를 OpenAI로 전송하며 기존 계정의 API 사용료가 발생한다. 인터넷과 API 잔액이 필요하다. 실패 시 정적 관점으로 대체하지 않고 오류를 표시한다. 응답 ID·모델·토큰 수를 화면에 표시한다.

기존 `Engine._generate_perspectives`를 호출해 문제별 1~6개 관점을 동적으로 만든다. 관점 제목과 설명을 합쳐 관점별 검색에 사용한다. 원질문도 별도로 검색하고, 전체 후보에 대해 기존 `aggregate`와 `combined_score`로 결합한다. C는 원질문·관점의 규칙 최댓값과 (원질문 의미 + 관점 의미 최댓값)/2를 사용한다. 관점별 Top5와 최종 Top5를 모두 보존한다. 동점은 기존 시연과 동일하게 원질문 Dense 점수와 ID 순이며, 과거 hybrid 동점 실험 전체와 동일한 성능을 재현했다고 주장하지 않는다.

시연은 “자연어로 입력 → 실시간 생성 관점 확인 → 관점별 추천 펼치기 → 결합 추천에서 원문 근거 확인” 순서로 진행한다. 핵심 설명은 ① 실시간 LLM 문제 관점 분해 ② 관점별 로컬 검색과 원질문 보존 ③ 실제 사례 근거를 통한 최종 추천이다. 학습된 QCI·Wald·전략 생성은 여전히 범위 밖이다. 독립 Test 봉인을 유지한다.

실시간 실행 검증은 `scripts/verify_professor_live.py`, 실제 API 응답 및 추천 기록은 `docs/professor-demo-20261028/live-verification.json`을 참고한다. 아래 초기 오프라인 설명과 검증 로그는 첫 버전의 이력이다. `/api/search`는 오프라인 비교용으로 보존하며 기본 화면은 `/api/live-search`를 호출한다.

## 실행

이 작업 폴더에서 PowerShell 한 줄:

```powershell
powershell -ExecutionPolicy Bypass -File .\run_professor_demo.ps1
```

브라우저에서 http://127.0.0.1:8766 을 연다. 준비 완료 표시 후 예시 버튼 또는 직접 입력 → 추천 사례 찾기 → 5개 카드 → 실제 업무 구조를 펼친다. 종료는 실행 창에서 Ctrl+C. 포트 충돌 시 `-Port 8767` 사용.

현재 PC는 옆 AX-prototype의 기존 가상환경과 `.local/models/bge-m3`를 재사용한다. 새 PC에서는 Python 가상환경에 `pip install -r requirements-prototype.txt kiwipiepy rank-bm25 torch pytest` 후 로컬 BGE-M3 모델 디렉터리를 `AX_BGE_MODEL_PATH` 환경변수로 지정한다. 모델은 배포 파일에 포함하지 않으며 최초 다운로드를 자동 실행하지 않는다. 추론은 CPU, 모델은 시작 시 미리 로딩한다. 기존 사례 임베딩을 재사용하며 사용자 입력은 매번 실제 추론한다.

## 짧은 진행 대본

1. “업무문제를 한국어로 입력하면 기존 112개 운영 사례 전체에서 관련 사례를 찾습니다.” 고객 문의 대응 예시를 누르고 검색한다.
2. “이 점수는 상대 추천 점수입니다. 사례 원문과 행동·대상 근거를 함께 봅니다.” 첫 카드의 세부 정보를 열고 Task, Action, Object, Context와 출처 링크를 보여준다.
3. 문서 항목 추출 또는 사내 문서 검색으로 바꿔 다시 실행한다. 검색 방식을 Dense 또는 BM25로 바꿔 결과를 비교한다.

설명할 핵심 세 가지: ① 한국어 자유 입력과 로컬 BGE-M3 실추론 ② 동일 112개 후보에서 기존 규칙 A / 필드 임베딩 B / 결합 C 및 Dense / BM25 비교 ③ 원문 Task의 행동·대상 인용과 출처를 추적하는 근거 표시.

## 최초 오프라인 버전의 구현 범위와 한계 (이력)

아래의 ‘단일 입력’, ‘동적 LLM 범위 밖’, ‘외부 API 없음’은 최초 오프라인 `/api/search`에만 해당한다. 현재 기본 화면은 위 실시간 업데이트의 `/api/live-search`를 사용하며 LLM API 비용이 발생한다. [통합 검토 안내](README.md)를 먼저 확인한다.

기준 스냅샷 ba5308d1619e53ee8b1b6c223480a439f5adcf8b에서 독립 브랜치로 구현했다. 기존 functional_mapping / semantic_mapping / BM25Retriever를 그대로 호출한다. B의 가용 필드 가중치와 C의 결합 공식은 동결 설정 그대로다. 전체 112개에 점수를 매긴다. 단일 입력만 사용하고 동점은 Dense 점수, 사례 ID 순으로 정렬한다. 이는 시연용 동점 규칙이며 과거 hybrid/RRF 실험의 재현을 주장하지 않는다. RRF를 제안 모델로 사용하지 않는다.

규칙이 기능을 인식하지 못해도 5개를 표시하므로 하위 추천의 근거가 부족할 수 있다. Object는 얕은 잔여 구절 추출이며 의미역 정답이 아니다. 없는 Output은 UNKNOWN으로 표시한다. 기존 한국어 설명이 있는 항목만 재사용하고 나머지는 영어 구조화 원문을 보존한다. 새 번역이나 설명 생성 API는 없다. 실제 Task 요약의 근거이며 원 출판물 내용의 재검증이 아니다.

동적 다중관점 LLM 생성, 학습된 QCI, Wald/전략 판단은 이 앱 범위 밖이다. 독립 Test 질문·정답·평가 파일은 읽거나 실행하지 않았다. Gold 정확도/성능 개선을 주장하지 않는다. 외부 API 호출은 없다.

## 보존 및 검증

`demo_manifest.json`의 사례·설정·기존 알고리즘·임베딩·표시 자료 10개 해시를 시작 및 검색 전후 검사한다. 원본 Dev/Test/GT 파일을 수정하지 않는다. 앱은 기존 실험의 질문·정답을 읽지 않고 사례 레지스트리와 사례 벡터만 사용한다. 임베딩 npz에 포함된 과거 쿼리 배열은 접근하지 않는다.

```powershell
$env:PYTHONPATH='src'
..\AX-prototype\.venv\Scripts\python.exe -m pytest tests/test_semantic_mapping.py tests/test_functional_mapping.py tests/test_bm25.py -q
..\AX-prototype\.venv\Scripts\python.exe scripts/verify_professor_demo.py
```

실행 증거는 `docs/professor-demo-20261028/verification.json`. 3개 예시의 실제 추천 5개 및 모든 검색 방식 응답을 보관한다. 이는 기능 확인 로그이며 학술 정답표가 아니다.
