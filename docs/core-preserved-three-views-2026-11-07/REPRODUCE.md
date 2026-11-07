# 실행 및 결과 확인 방법

## 저장한 결과만 다시 계산하기

저장소 루트에서 다음 명령을 실행한다. Python과 패키지 버전은 `preregistration.json`에 기록했다. 아래 두 명령은 저장된 추천·AI 판정을 읽으며 유료 API를 호출하지 않는다. 평가 파일이 이미 있으면 덮어쓰기를 거부하므로, 재검증할 때는 별도 복사본에서 파생 평가 파일만 제외하고 실행한다. 원본 기록은 보존한다.

```powershell
$env:PYTHONPATH = 'src;.'
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONDONTWRITEBYTECODE = '1'
python -m scripts.core_preservation_evaluate
python -m scripts.core_preservation_report
```

자동 테스트의 정확한 파일 목록과 실행 결과는 `tests.json`에 있다. 새로운 코드의 검사는 다음과 같다.

```powershell
python -m pytest -p no:cacheprovider tests/test_core_preservation.py -q
```

## 처음 실행한 순서

실험 전 프롬프트를 커밋하고, 그 뒤 새 개발 질문 8개를 작성했다. 사전 등록 후 생성하고, 추천 결과를 봉인한 뒤 관련도를 판정했다. 이 순서를 바꾸면 이번 실험과 같은 절차로 볼 수 없다.

```powershell
python -m scripts.core_preservation_run prepare
python -m scripts.core_preservation_run generate
python -m scripts.core_preservation_run infer --scratch ../AX-core-preserved-20261107-scratch
python -m scripts.core_preservation_run judge
python -m scripts.core_preservation_quality
python -m scripts.core_preservation_evaluate
python -m scripts.core_preservation_report
```

위 명령은 실제 실행 순서의 기록이다. 저장소에 결과가 이미 있어 처음부터 다시 실행할 수 없다. 새 실험은 별도 작업본·결과 경로·비용 한도를 먼저 등록해야 한다. API 단계는 환경에 안전하게 설정한 `OPENAI_API_KEY`를 읽는다. 키를 명령이나 파일에 적지 않는다. 수신 여부가 불명확한 요청은 자동으로 다시 호출하지 않는다.

`infer`는 사전 등록된 BGE-M3 경로를 사용하며 외부 연결을 차단한다. 기존 모델 경로는 `../AX-prototype/.local/models/bge-m3`다. 실제 가중치 해시와 환경은 사전 등록 파일에 있다. 기존 C1 코어와 검색·결합 규칙은 재사용했다.

## 결과 파일

- `predictions.json`은 A·B·C·E의 전체 112개 순위와 Top-5/10/20이다.
- `prediction_seal.json`은 판정 전에 저장한 추천 결과의 해시다.
- `inference/branch_rankings.json`과 `branch_scores.jsonl`은 216개 관점 경로의 순위와 사례별 점수다.
- `slots.json`은 방식·질문·회차·관점을 연결한다.
- `api/`는 호출별 입력, 실제 응답, 사용량과 처리 상태다. 인증 헤더는 저장하지 않는다.
- `labels.json`은 순위와 방식명을 가린 896개 AI-Silver 판정이다.
- `quality.json`은 순위를 가린 별도 품질 점검이다. 같은 모델의 평가라는 한계가 있다.
- `evaluation.json`은 지표별 분모, 질문별 점수, 세 회차 변화, 질문 재표집 구간이다.
- `discovery.json`은 관점별 발견·진입·이탈과 기능 인식을 구분한다.
- `api_ledger.json`은 호출별 추정 비용과 누적 비용이다. 실제 청구서 잔액은 아니다.

이번 자료는 새 개발 실험이며 신규 독립 Test는 수행하지 않았다. AI 판정은 사람 검증 정답으로 사용할 수 없다.
