"""Single-request perspective omission review and branch-preserving equal-count controls."""
from copy import deepcopy
from ax_research.perspective_boundary import corrected_request
from ax_research.perspective_panels import schema,normalize,build_panels

REVIEW_RULE='''\n관점 누락 점검과 검색 역할:
모든 제공 관점을 한 번씩 검토하고 search_role을 MAIN/ADDITIONAL/NONE으로 반환하세요.
MAIN: 질문의 실제 문제·명시 업무에 우선 대응하는 관점입니다. 여러 개나0개가 가능합니다.
ADDITIONAL: 주요 관점만 보면 놓칠 수 있는 구체적이고 유용한 다른 접근입니다. 원인으로 확정하지 말고 PROBLEM_HYPOTHESIS, 원문 anchor_quote, bridge_reason, 확인할 assumptions를 남깁니다.
단순히 덜 직접적이거나 데이터 형식/권한/구현 조건이 미확인이라는 이유만으로 검색을 막지 마세요. 실제 사례 업무가 그 문제에 어떻게 도움이 될 수 있는지 합리적인 연결이 있으면 ADDITIONAL로 살려 검토합니다. 업종·기술·정보라는 포괄어 겹침만으로 추가하지 마세요.
포함 기준은 사례의 수행 기능 범위를 설명하는 기준이지 사용자 질문의 동일 단어 요구가 아닙니다. 질문 증상을 다른 실제 업무에서 검토하는 것은 허용합니다. 다만 명시한 목표업무/제외와 충돌하는 대체업무는 허용하지 않습니다.
자료 요청 자체를 회사의 지식검색 업무로 취급하지 마세요. 특정 예측·물리 검사 사례만 요구하면 문서검색·문서대조 사례로 바꿔 답하지 마세요.
검색할 구체적인 연결이 없으면 NONE으로 남깁니다. MAIN/ADDITIONAL은 status=SELECTED, NONE은PENDING 또는NOT_SELECTED입니다. 추가 관점을 항상 만들거나 정해진 수를 채우지 마세요.
누락 점검은 한 요청 안에서 수행하며, 짧은 판단 근거만 출력합니다. 원문 인용은 정확히 복사하고 추정 확인사항을 사용자 조건 인용에 넣지 마세요.'''

def review_schema():
    s=deepcopy(schema());d=s['properties']['decisions']['items']
    d['properties']['search_role']={'type':'string','enum':['MAIN','ADDITIONAL','NONE']};d['required'].append('search_role')
    return s

def review_request(question,catalog):
    system,payload=corrected_request(question,catalog)
    return system+REVIEW_RULE,payload

def normalize_review(question,data,catalog):
    clean=deepcopy(data);roles={}
    for d in clean['decisions']:
        role=d.pop('search_role');roles[d['id']]=role
        if role not in ('MAIN','ADDITIONAL','NONE'):raise ValueError('Unknown search role')
        if (d['status']=='SELECTED')!=(role in ('MAIN','ADDITIONAL')):raise ValueError('Role and selection disagree')
        if role=='ADDITIONAL' and (d['relation']!='PROBLEM_HYPOTHESIS' or not d['assumptions']):raise ValueError('Additional view needs explicit unconfirmed hypothesis')
    result=normalize(question,clean,catalog,'ACTUAL_SINGLE_OPENAI_REQUEST_OMISSION_REVIEW')
    for d in result['decisions']:d['search_role']=roles[d['id']]
    return result

def fill_from_base(seed,base_order,target):
    out=list(dict.fromkeys(seed))
    if len(out)>target:raise ValueError('Cannot erase branches to meet budget')
    for c in base_order:
        if len(out)==target:break
        if c not in out:out.append(c)
    if len(out)!=target:raise ValueError('Insufficient distinct baseline cases')
    return out

def build_variants(selection,catalog,profiles,registry,scorer,base_order):
    if len(base_order)!=len(set(base_order)) or set(base_order)!=set(registry):raise ValueError('Baseline must rank entire registry once')
    base5=base_order[:5]
    if 'failed' in selection:
        panels={'panels':[],'case_details':{},'failed':selection['failed']}
    else:panels=build_panels(selection,catalog,profiles,registry,scorer)
    role={d['id']:d.get('search_role','NONE') for d in selection.get('decisions',[])}
    main=[];additional=[]
    for p in panels['panels']:
        p['search_role']=role[p['id']]
        for row in p['cases']:
            (main if role[p['id']]=='MAIN' else additional).append(row['case_id'])
    main=list(dict.fromkeys(main));additional=list(dict.fromkeys(additional))
    complete=list(dict.fromkeys(base5+main+additional));u=len(complete)
    a=base_order[:u];b=fill_from_base(base5+main,base_order,u)
    assert len(set(a))==len(set(b))==len(set(complete))==u
    assert set(base5)<=set(a)&set(b)&set(complete)
    assert set(main)<=set(b)&set(complete)
    return {'panels':panels,'base5':base5,'main_cases':main,'additional_cases':additional,'unique_budget':u,
        'sets':{'A_BASE':a,'B_MAIN':b,'C_REVIEW':complete},
        'B_basic_fill':list(c for c in b if c not in set(base5+main)),
        'not_in_main_control':sorted(set(complete)-set(b)),
        'missing_from_review_vs_main_control':sorted(set(b)-set(complete))}
