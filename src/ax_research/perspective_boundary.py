"""Isolated business-intent boundary repair; preserves historical panel contracts."""
import json
from ax_research.perspective_panels import request_body

BOUNDARY_RULE='''\n업무 범위 판단 규칙:
1. 사용자가 회사에서 겪는 실제 문제·수행 업무와, 당신에게 하는 자료 요청(사례 찾아줘, 자료 보여줘, 적용 사례 설명해줘)을 구분하세요. 후자는 검색 대상 업무가 아닙니다. '기업 AX 사례를 찾고 싶다'만으로 P01을 선택하지 마세요.
2. 각 관점의 include_if/exclude_if를 적용하세요. '정보/데이터/검토/확인' 같은 포괄어만으로 연결하지 마세요. 정비 예측/물리 영상검사를 문서 대조 업무로 바꾸거나, 재고 수요예측을 문서검색 업무로 바꾸지 마세요.
3. 카드 include_if에 쓰인 Problem/Task는 사례 자체를 분류하는 기준입니다. 사용자 질문에 카드와 같은 수단·작업 단어가 반드시 있어야 한다는 조건이 아닙니다. 증상이나 일반 업무(접수 오류, 수기 등록, 반복문의)가 제시되면, 자료 추출·구조화 또는 지식검색이 그 부담에 도움이 될 구체적 경로가 있을 때 PROBLEM_HYPOTHESIS와 확인할 가정으로 선택할 수 있습니다. 질문이 예측 등 특정 목표 업무의 사례만 명시한 경우에는 그 목표를 다른 업무로 대체하지 마세요. 원문 사례의 수행 기능은 새로 가정하지 마세요.
4. 네 관점 중 대응할 근거가 없으면 NOT_SELECTED, 정보가 부족하면 PENDING입니다. 매번 하나 이상 고를 필요는 없습니다. unsupported_work는 관점 목록이 다루지 못하는 회사 업무를 뜻하며 '지금 모듈은 사례 설명을 못함' 같은 시스템 기능 범위가 아닙니다.
5. 사례의 정확한 업종·PDF·시간대·세부 필드가 미확인이라는 이유로 참고를 탈락시키지 마세요. 기존 참고 기준은 유지합니다. anchor_quote는 회사의 문제/업무/제약을 인용해야 하며, 단순 자료요청 문구를 업무 근거로 쓰지 마세요.
6. constraints.quote와 모든 anchor_quote/unsupported_work.quote는 질문에 실제로 있는 연속 문자열만 복사하세요. 추정 확인사항은 missing_information에 씁니다. 이유는 한두 문장, 가정/확인사항은 핵심만 간결하게 쓰세요.'''

def corrected_request(question,catalog):
    draft=request_body(question,catalog)
    payload=json.loads(draft['messages'][0]['content'])
    cards={c['id']:c for c in catalog['cards']}
    for c in payload['perspectives']:
        c['include_if']=cards[c['id']]['include_if']
        c['exclude_if']=cards[c['id']]['exclude_if']
    return draft['system']+BOUNDARY_RULE,payload
