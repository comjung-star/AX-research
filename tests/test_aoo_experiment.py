import copy
import json
from decimal import Decimal
import pytest
from scripts import aoo_experiment as r

def example(aspect=False):
    cases,queries=r.inputs()
    job=r.build_job('pilot',0,'V21D010',['AXV2C_0093_01','AXV2C_0093_02'],cases,queries,'V21D010:CAUSE' if aspect else None)
    ratings={}
    for cid,item in job['items'].items():
        ratings[cid]={'score':3,'matched_tasks':['DIAGNOSE_QUALITY_CAUSE'],'relation':'DIRECT','match_mask':'111','problem_context':'NOT_FULLY_SUPPORTED','evidence':item['task'][:180],'reason':'Diagnose causes matches / production defects match / causal findings match'}
    return job,{'query_id':job['query_id'],'target_id':job['target_id'],'ratings':ratings}

def test_scopes_have_different_operation_sets():
    whole,_=example();aspect,_=example(True)
    assert 'ADJUST_PRODUCTION_PLAN' in whole['tasks']
    assert set(aspect['tasks'])=={'DIAGNOSE_QUALITY_CAUSE'}

def test_case_specific_schema_prevents_foreign_evidence_mapping():
    job,d=example();assert r.validate(json.dumps(d),job)['valid']
    a,b=job['items'];d['ratings'][a]['evidence']=r.excerpts(job['items'][b])[0]
    assert not r.validate(json.dumps(d),job)['valid']
    assert r.excerpts(job['items'][b])[0] not in job['schema']['properties']['ratings']['properties'][a]['properties']['evidence']['enum']

def test_wrong_query_target_and_missing_case_are_refused():
    job,d=example()
    for field in ('query_id','target_id'):
        x=copy.deepcopy(d);x[field]='OTHER';assert not r.validate(json.dumps(x),job)['valid']
    d['ratings'].pop(next(iter(d['ratings'])));assert not r.validate(json.dumps(d),job)['valid']

def test_high_grade_requires_all_three_operational_matches():
    job,d=example();next(iter(d['ratings'].values()))['match_mask']='011'
    assert not r.validate(json.dumps(d),job)['valid']

def test_no_unstated_benefit_in_reason_and_consistent_length():
    job,d=example();row=next(iter(d['ratings'].values()))
    row['reason']='Answers match / customer inquiries / reduces staff workload'
    assert not r.validate(json.dumps(d),job)['valid']
    row['reason']=' '.join(['match']*36)+' / object / output'
    assert not r.validate(json.dumps(d),job)['valid']
    assert '35 whitespace' in r.SYSTEM and r.CFG['reason_max_words']==35

def test_balanced_pre_registered_pilot_and_unchanged_corpus(tmp_path,monkeypatch):
    monkeypatch.setattr(r,'OUT',tmp_path)
    p=r.prepare();expect=p['diagnostic_expectations_not_model_inputs']
    assert len(expect)==36
    for b in ('DIRECT','PARTIAL','UNRELATED'):assert sum(e['diagnostic_band']==b for e in expect)==12
    assert sum(len(j['items']) for j in p['stage1'])==1120
    for j in p['pilot']+p['stage1']:
        assert 'diagnostic_band' not in j['user']
        assert all(i['question_text']==r.inputs()[1][j['query_id']] for i in j['items'].values())
    for j in p['views']:
        assert 'target_tasks' not in j['user'] and 'case_id' not in j['user']

def test_unknown_attempt_is_never_replayed(tmp_path,monkeypatch):
    job,_=example();monkeypatch.setattr(r,'OUT',tmp_path);r.STOP.clear()
    path=tmp_path/'attempts/claude/pilot_0000_a1.json';path.parent.mkdir(parents=True)
    path.write_text('{"state":"RESERVED","reserved_usd":"0.1"}',encoding='utf-8')
    monkeypatch.setattr(r.api,'transport',lambda *a:pytest.fail('Unknown billing cannot be replayed'))
    try:assert r.run_job('claude',job) is None
    finally:r.STOP.clear()

def test_prior_cost_and_buffer_arithmetic():
    assert Decimal(r.CFG['claude_prior_actual_or_reserved_usd'])+Decimal(r.CFG['claude_new_work_cap_usd'])+Decimal('.50')==Decimal('5')

def test_grade4_needs_majority_of_selected_core_operations():
    job,d=example();row=next(iter(d['ratings'].values()))
    row.update(score=4,problem_context='SUPPORTED')
    assert len(job['tasks'])==3 and not r.validate(json.dumps(d),job)['valid']

def test_active_hold_blocks_api_phases_before_prepare(tmp_path,monkeypatch):
    import sys
    monkeypatch.setattr(r,'OUT',tmp_path);(tmp_path/'halt.json').write_text('{"active":true}',encoding='utf-8')
    monkeypatch.setattr(r,'prepare',lambda:pytest.fail('Must not prepare or call APIs on hold'))
    monkeypatch.setattr(sys,'argv',['aoo_experiment','stage1']);assert r.main()==2
