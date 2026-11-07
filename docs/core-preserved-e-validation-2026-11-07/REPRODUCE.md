# 검증 결과 확인과 실행 기록

## 비용 없이 확인하기

저장소 루트에서 기존 Python 환경을 사용한다. 패키지와 모델 환경은 기준 실험의 사전 등록 파일에 남아 있다. 이번 작업에서는 임베딩 계산이나 추천 실행을 다시 하지 않았다.

```powershell
$env:PYTHONPATH = 'src;.'
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONDONTWRITEBYTECODE = '1'
python -m pytest -p no:cacheprovider tests/test_e_validation.py -q
```

기존 검사까지 포함한 정확한 명령과 통과 수는 `tests.json`에 있다. 검사는 저장된 응답과 인공 자료만 사용한다. API 요청과 독립 Test 실행은 포함하지 않는다.

`v0_original`은 원래 판정 기록이다. `v1_missing_only`는 미판정29건만 새로 검토한 버전이다. `v2_reviewed_strict`는 선정180쌍에 대해 두 요청의 근거 검사와 정확한 등급 일치를 요구한다. 불일치·보류·응답 누락은 ABSTAIN이다. 검토하지 않은716쌍은 기존 출처를 이어 사용한다.

`v2_openai_sensitivity`와 `v2_second_reviewer_sensitivity`는 각 검토자의 판단을 따로 적용했을 때의 결과다. 이 버전은 검토자 의존성을 확인하기 위한 자료다. 각 버전은 동일한 봉인 추천을 평가하며 기존 알고리즘의 재실행 결과가 아니다.

## 실제 작업 순서

다음은 이미 실행한 절차의 기록이다. `prepare`와 분석 산출물 저장은 기존 경로가 있으면 거부한다. 기존 결과가 있는 상태에서 처음부터 다시 실행하지 않는다.

```powershell
python -m scripts.e_validation prepare
python -m scripts.e_validation access
python -m scripts.e_validation missing
python -m scripts.e_validation_analyze missing
python -m scripts.e_validation quality
python -m scripts.e_validation repair_quality
python -m scripts.e_validation review
python -m scripts.e_validation repair_review
python -m scripts.e_validation_analyze all
python -m scripts.e_validation_report
```

새 검증 기준과 선정표를 첫 유료 요청 전에 커밋했다. 최초 비용 상한 계산이 $2를 넘어 출력 길이 상한만 조정했고, 수정한 상한도 첫 유료 요청 전에 커밋했다. 관련도 척도와 보존 품질 기준은 바꾸지 않았다. 두 비용 계획을 모두 보존했다.

API 입력에는 해당 질문과 사례의 실제 업무 설명 또는 기존 관점3개만 들어간다. 방식 이름·추천 순위·점수·기존 판정은 전달하지 않는다. 결과와 대응 ID를 연결하는 표는 별도로 관리한다. 같은 질문의 사례를 최대3개까지 묶는다.

API 키는 기존 환경 설정에서 읽고 인증 헤더는 저장하지 않는다. 호출 전에 전체 누적 사용·미확정 예약과 새 요청의 최대 비용을 합해 $2를 넘으면 중단한다. 수신 여부가 불명확한 요청은 자동으로 재전송하지 않는다. 실패·누락·미확정 비용을 남기며 원본 응답을 고쳐 쓰지 않는다.

품질 응답 한 건이 출력 길이 상한에서 종료된 뒤, 성능 재계산 전에 기술 복구 정책을 추가 기록했다. 수신과 비용이 확인되고 출력 한도 종료가 명시된 경우만 동일한 입력·프롬프트로 한 차례 복구한다. 출력 길이만 늘린다. 유효한 낮은 점수, 의견 차이, 원문 근거 위반과 수신 불확실 요청은 복구 대상이 아니다. 원본과 복구 응답·비용을 모두 보존하며 `repairs/`에서 연결한다.

Claude는 기존 Haiku4.5 키와 모델로 접근 점검했다. 기존 기록의 사용·예약액과 최소$0.50 안전 여유를 예산 설명에 함께 남겼다. 실제 계정 잔액을 조회한 값과 구분한다.

## 원문과 검증 한계

`source_registry.json`은 사례의 Problem·Task·Context, 근거 ID, 원본 파일 위치와 URL을 연결한다. 출판물의 최신 웹 페이지를 새로 전수 확인한 자료는 아니다. 구조화된 설명에 없는 실제 구현이나 성과는 확인되지 않은 정보로 남는다.

질문 작성과 기존 판정의 이력을 아는 조정자가 검토 대상을 선정했다. 새 모델 요청은 기존 점수를 가렸지만, 이 연구 전체가 미개봉 독립 검증으로 바뀌지는 않는다. 사람 검증을 수행하지 않았으며 모든 판정 출처는 AI-Silver다.
