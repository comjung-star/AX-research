# 2026-10-20 교수 피드백 반영 메모

## 교수님이 직접 질문한 핵심

1. Query와 정답이 1:1 매칭인지
2. 전체 관련도 라벨을 만들면 과적합 위험이 없는지
3. Strategy 없이 문제만 보고 Perspective를 만들면 단순 카테고리화가 되는지
4. 미리 정의한 Perspective에 없는 새로운 관점이 생성되면 어떻게 처리할지
5. Ground Truth 구축 단계와 실제 LLM 동적 Perspective 생성 모델이 어떻게 연결되는지

## 기존 설계의 의도

- 실제 Runtime에서는 LLM이 사용자 Query를 보고 Perspective를 동적으로 생성한다.
- Ground Truth의 Perspective는 모델에 입력하는 고정 Category가 아니라 모델의 결과를 평가하기 위한 기준이었다.
- 관련도는 모델 검색결과를 보고 정하지 않고 Problem View 기반으로 사전에 작성해 평가 독립성을 확보하려 했다.
- Query 하나에 여러 Perspective와 여러 Relevant Case가 존재하며 Case 중복도 허용한다.

## 피드백 후 명문화한 보완

### 1. Dev / Test 분리
- GTQ001~GTQ010 = Dev/Pilot
- 모델·Prompt·평가규칙 Freeze 후 별도 Held-out Test 생성
- Test 결과를 본 뒤 모델을 수정하지 않음

### 2. Gold Perspective 의미 보완
- 파일 호환상 Gold 명칭은 유지
- 의미는 Reference Perspective: 최소 평가 기준
- 가능한 모든 관점의 폐쇄형 정답 목록으로 해석하지 않음

### 3. 새로운 관점 처리
Reference에 없는 Generated Perspective를 자동 오답 처리하지 않는다.
- Query에 근거가 있는가
- 기존 관점의 단순 말바꾸기가 아닌가
- 추가 Relevant Case를 찾거나 독립 문제차원을 설명하는가
를 검토한다.

구체적인 Novel Perspective 정량 평가방법은 Dev 실험에서 확인한 뒤 최종 Test 전에 Freeze한다.

## 교수 피드백과 우리 보완의 구분

교수님이 직접 제시한 것은 위의 **질문·우려사항**이다.
Dev/Test 역할 구체화, Reference Perspective 해석, Novel Valid Perspective 검토기준은 그 질문을 반영해 **연구 설계를 명확하게 하기 위해 우리가 정리한 방법론적 보완**이다.
