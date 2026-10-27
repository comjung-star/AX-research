import json
import pytest
from scripts import independent_verifier_json as x
v=x.v

def job(ids=None):
    return v.make_job('unit',0,'V21D010','V21D010:INTEGRATION',ids or ['AXV2C_0093_01'],'openai','review')

def test_single_case_cannot_be_rebound_by_model():
    j=job();d={'qid':j['qid'],'target':j['target'],'reviewed':list(j['tasks']),'links':[],'extra':[]}
    z=v.validate(json.dumps(d),j);assert z['valid'] and z['data']['items'][0]['id']=='AXV2C_0093_01'
    d['case_id']='OTHER';assert not v.validate(json.dumps(d),j)['valid']

def test_duplicate_json_key_is_rejected():
    assert not v.validate('{"qid":"a","qid":"b"}',job())['valid']

def test_fenced_json_extra_prose_never_silently_approved():
    j=job();d={'qid':j['qid'],'target':j['target'],'reviewed':list(j['tasks']),'links':[],'extra':[]}
    z=v.validate('```json\n'+json.dumps(d)+'\n```\nUnrequested claim.',j)
    assert z['valid'] and z['extra_prose_present']
    assert z['extra_prose_requires_source_audit']=='Unrequested claim.'

def test_problem_is_not_actual_operation_evidence():
    j=job();d={'qid':j['qid'],'target':j['target'],'reviewed':list(j['tasks']),'links':[['INTEGRATE_PRODUCTION_DATA','DIRECT','integrate','data','dataset',j['items']['AXV2C_0093_01']['problem'],'Unproven data integration.']],'extra':[]}
    assert not v.validate(json.dumps(d),j)['valid']

def test_multiple_cases_require_exact_case_keys():
    j=job(['AXV2C_0093_01','AXV2C_0093_02']);d={'qid':j['qid'],'target':j['target'],'reviewed':list(j['tasks']),'cases':{'WRONG':{'links':[],'extra':[]}}}
    assert not v.validate(json.dumps(d),j)['valid']

def test_failed_gate_blocks_publication_as_silver():
    d=v.api.read_json(x.ROOTS[0]/'final_status.json')
    assert d['approved_silver_scores']==0 and not d['semantic_gate']
