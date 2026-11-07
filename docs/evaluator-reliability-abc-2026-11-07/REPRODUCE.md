# 재현 방법

기준: `76b1cc93a859086d3f07dfe9b315ef6475a58cd0`. 이 브랜치의 기존 원본·실패·최초 복구 결과를 삭제하지 않는다. 결과 저장기는 같은 경로 덮어쓰기를 거부한다.

## API 없이 원문 복구 재현

저장소 루트에서 기존 Python 환경을 사용한다. 새 폴더명은 아직 존재하지 않아야 한다.

```powershell
$env:PYTHONPATH='src;.'
$env:PYTHONIOENCODING='utf-8'
$env:PYTHONDONTWRITEBYTECODE='1'
$python='..\AX-prototype\.venv\Scripts\python.exe'
& $python -m scripts.evaluator_abc_recover --provider openai --output .local/replay-openai-new
& $python -m scripts.evaluator_abc_recover --provider claude --output .local/replay-claude-new
```

기본값은 **오프라인 전용**이다. 저장된 완전 응답만 읽고, 실행하지 않은 후속 판정이 필요하면 미판정으로 남긴다. `--resume-unexecuted`를 사용하지 않는다. 실제 오프라인 재실행에서 두 제공자의 세 결과 파일(총6파일)이 `provider/recovery-v2/`와 바이트 단위로 동일했다. [재현 검사](replay_and_technical_checks.json)

## 자동 검사

```powershell
& $python -m pytest -p no:cacheprovider tests/test_evaluator_abc.py -q
```

기존212개와 신규30개를 합친 전체 명령·실행 결과는 [tests_final_v2.json](tests_final_v2.json)에 있다. 실제 Test 본문이나 정답, 외부 API는 사용하지 않는다. 실패한 테스트 fixture 기록도 별도로 남겼다.

## 이번 실행 순서와 결과 위치

1. `scripts/evaluator_abc_prompts.py`: 공통 기준·A/B/C 설계. 신규 예시보다 먼저 동결.
2. `scripts/evaluator_abc_prepare.py`: 신규16개+재현8개 기대 범위,75개 블라인드 입력, 비용·해시 사전 기록. 이미 존재하는 폴더에서는 덮어쓰기를 거부한다.
3. `python -m scripts.evaluator_abc benchmark --provider <provider>`: 이번에 실제 실행한 유료 요청. 원문은 `openai/api/`, `claude/api/`; 최초 결과는 `benchmark_results.json`. 새 실행에는 별도 계획·예산·결과 폴더가 필요하다. 재현을 위해 무작정 유료 호출하지 않는다.
4. `python -m scripts.evaluator_abc_analyze controls`: 성능 순위 없이 신규 예시의 사전 선정 규칙 적용. 선택을75건 실행 전에 커밋.
5. `python -m scripts.evaluator_abc pending --provider <provider>`:75건 독립 요청. 최초 기록 `pending_results.json`.
6. 완성된 단일 JSON 뒤에 설명이 붙는 파서 오류 복구. 최초 복구 결과와 수정 전 실패 분류는 그대로 보존. 현재 판정은 `provider/recovery-v2/`. 동일 등급 불일치를 유리한 답이 나올 때까지 재요청하지 않음.
7. `scripts/evaluator_abc_analyze.py --recovered` 및 `final` 단계의 최종 산출물은 `final-review/`. 실행 시 이미 파일이 있으면 거부한다. 최초 분석 결과도 루트와 `local-recovery-v1/`에 보존.
8. `scripts/evaluator_abc_report.py`: 최종 Korean README·상태 생성. 기존 결과 파일이 있으면 재생성 대신 별도 출력 버전을 사용해야 한다.

## 평가 규칙과 한계

- 등급0~3, 관련≥2. ABSTAIN/UNJUDGED는0점으로 채우지 않는다.
- 평가 가능한 동일 질문 집합에서만 추천 A/B/C/E를 비교한다. 전체112개 판정이 없는 질문의 전체 Recall/F1은 확정하지 않는다.
- 점수는 AI-Silver 진단이다. 사람 승인·Human-Gold·검증 완료로 부르지 않는다.
- 원문 앵커 일치가 의미적 판단의 정확성을 보장하지 않는다.
- 가상 판정 시나리오는 실제 성능이나 신뢰구간이 아니다.
- 기존 C1·BGE-M3·BM25·가중치·사례·정답·예측·생성 프롬프트를 바꾸지 않았다. Test15/신규Test40을 사용하지 않았다.

## 비용과 비밀정보

작업 전체 $2, 제공자별 OpenAI$0.30·Claude$1.70 예약 상한. 두 프로세스의 예산을 나눠 동시 실행 시 합계 상한이 깨지지 않게 했다. 호출별 입력·출력 토큰과 실제 응답 모델 ID·예상 비용은 [최종 비용표](final-review/cost_summary.json)에 있다. 요청 로그에는 인증 헤더나 키 값을 넣지 않는다. 불확실한 호출은 재호출하지 않고 보수적으로 예약한다. 이번 미확정 예약은0달러다.
