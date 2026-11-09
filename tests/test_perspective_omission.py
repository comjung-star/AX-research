import pytest
import ax_research.perspective_omission as module

def test_equal_counts_are_filled_with_baseline_without_dropping_main(monkeypatch):
    ids=[f'c{i}' for i in range(12)];reg={c:{} for c in ids}
    monkeypatch.setattr(module,'build_panels',lambda *a:{'panels':[{'id':'P01','cases':[{'case_id':'c6'}]},{'id':'P03','cases':[{'case_id':'c10'},{'case_id':'c11'}]}],'case_details':{}})
    sel={'decisions':[{'id':'P01','search_role':'MAIN'},{'id':'P03','search_role':'ADDITIONAL'}]}
    r=module.build_variants(sel,{}, {},reg,None,ids)
    assert r['unique_budget']==8
    assert all(len(set(v))==8 for v in r['sets'].values())
    assert all(set(ids[:5])<=set(v) for v in r['sets'].values())
    assert 'c6' in r['sets']['B_MAIN'] and 'c6' in r['sets']['C_REVIEW']
    assert r['B_basic_fill']==['c5','c7']
    assert r['not_in_main_control']==['c10','c11']

def test_no_perspective_still_preserves_real_baseline5():
    ids=[f'c{i}' for i in range(8)]
    r=module.build_variants({'failed':'test'}, {}, {},{c:{} for c in ids},None,ids)
    assert all(v==ids[:5] for v in r['sets'].values())

def test_duplicate_membership_does_not_buy_larger_budget(monkeypatch):
    ids=[f'c{i}' for i in range(10)]
    monkeypatch.setattr(module,'build_panels',lambda *a:{'panels':[{'id':'P01','cases':[{'case_id':'c6'}]},{'id':'P03','cases':[{'case_id':'c6'}]}],'case_details':{}})
    sel={'decisions':[{'id':'P01','search_role':'MAIN'},{'id':'P03','search_role':'ADDITIONAL'}]}
    r=module.build_variants(sel,{}, {},{c:{} for c in ids},None,ids)
    assert r['unique_budget']==6 and r['sets']['C_REVIEW'].count('c6')==1
    assert len(r['panels']['panels'])==2

def test_fill_never_removes_a_branch():
    with pytest.raises(ValueError):module.fill_from_base(['x','y'],['a','b'],1)

def test_additional_view_is_an_unconfirmed_hypothesis():
    d={'id':'P01','status':'SELECTED','relation':'PROBLEM_HYPOTHESIS','anchor_quote':'답변이 늦다','bridge_reason':'근거 탐색 시간이 원인 중 하나라면 참고할 수 있다','assumptions':['답변 근거를 찾는 시간이 지연의 일부인지 확인이 필요하다'],'missing_information':[],'search_role':'ADDITIONAL'}
    payload={'decisions':[d],'constraints':[],'unsupported_work':[]};catalog={'cards':[{'id':'P01'}]}
    r=module.normalize_review('답변이 늦다',payload,catalog)
    assert r['decisions'][0]['confirmed_problem_cause'] is False
    d['assumptions']=[]
    with pytest.raises(ValueError):module.normalize_review('답변이 늦다',payload,catalog)
