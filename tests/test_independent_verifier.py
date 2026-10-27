import copy
import json
import pytest
from scripts import independent_verifier as v

def job(role='review'):
    return v.make_job('unit',0,'V21D010','V21D010:INTEGRATION',['AXV2C_0093_01'],'openai',role)

def test_reviewer_is_different_and_blind():
    j=job();assert j['provider']=='gemini'
    assert 'prior_query_blind_operations' not in j['user']
    assert 'evaluation_result' not in j['user'] and 'expected_review_only' not in j['user']

def test_reject_index_and_question_quote():
    j=job();row={'id':'AXV2C_0093_01','links':[[0,'DIRECT','analyze','quality','causes','Analyze production quality defects','Actual analysis.']],'extra':[]}
    d={'qid':j['qid'],'target':j['target'],'reviewed':list(j['tasks']),'items':[row]}
    assert not v.validate(json.dumps(d),j)['valid']
    row['links'][0][0]='INTEGRATE_PRODUCTION_DATA'
    row['links'][0][5]='생산·품질·설비 데이터가 여러 시스템에 나뉘어 있어'
    assert not v.validate(json.dumps(d),j)['valid']

def test_disagreement_is_hold_not_negative():
    a={'links':[['X','DIRECT','a','o','y','source','why']],'extra':[]}
    b=copy.deepcopy(a);b['links'][0][1]='SUPPORT'
    assert v.score_pair(a,b)['score'] is None
    assert v.score_pair(a,{'links':[],'extra':[]})['score'] is None

def test_agreement_not_automatic_gold():
    a={'links':[['X','DIRECT','a','o','y','source','why']],'extra':[]}
    assert v.score_pair(a,a)['score']==3
    assert 'REQUIRES_SOURCE_AUDIT' in v.score_pair(a,a)['state']

def test_panel_balanced_and_separate_from_inputs():
    p=v.panel();assert len(p)==20
    assert all(sum(r['diagnostic_type']==kind for r in p)==5 for kind in ('DIRECT','PARTIAL','UNRELATED','CONFUSABLE'))
    assert all(not x['human_gold'] and x['human_review_needed'] for x in p)
    assert 'expected_review_only' not in job('evaluation')['user']

def test_four_needs_additional_evidence():
    a={'links':[['X','DIRECT','answer','questions','answers','Answer questions','Equivalent inquiry response.']],'extra':[]}
    assert v.score_pair(a,a)['score']==3
    b=copy.deepcopy(a);b['extra']=['stated condition','Matching condition.']
    assert v.score_pair(a,b)['score']==3

def test_original_halt_not_removed():
    assert v.api.read_json(v.OLD/'halt.json')['active']
