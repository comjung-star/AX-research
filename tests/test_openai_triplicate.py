import copy
import json
import pytest
from scripts import openai_triplicate as r
from scripts import openai_triplicate_search as s

def test_same_input_three_requests():
    cs,qs=r.inputs();a=r.job('V21D001','AXV2P2_0048_01',1,cs,qs);b=r.job('V21D001','AXV2P2_0048_01',3,cs,qs)
    assert a['body']==b['body'] and a['id']!=b['id'] and a['input_version']==b['input_version']
    assert 'previous' not in a['body']['input'] and 'perspective' not in a['body']['input']

def test_mapping_and_source_guards():
    cs,qs=r.inputs();j=r.job('V21D001','AXV2P2_0048_01',1,cs,qs)
    d={'qid':j['qid'],'cid':j['cid'],'score':3,'reason':'Answers shopping questions across sectors.','quote':'Answer shopping questions'}
    assert r.validate(json.dumps(d),j)['valid']
    for field in ('qid','cid','quote'):
        other=copy.deepcopy(d);other[field]='WRONG';assert not r.validate(json.dumps(other),j)['valid']

def test_metrics_counts_and_unknown_bounds():
    grades={str(i):int(i<3)*3 for i in range(20)};ranking=list(grades)
    m=s.metrics(ranking,grades,5);assert m['tp']==3 and m['precision']==.6 and m['recall']==1 and m['f1']==.75
    grades['4']=None;m=s.metrics(ranking,grades,5)
    assert m['precision_denominator']==4 and m['unknown_total']==1
    assert m['precision_lower']==.6 and m['precision_upper']==.8

def test_no_relevant_recall_is_undefined():
    g={str(i):0 for i in range(20)};m=s.metrics(list(g),g,5)
    assert m['precision']==0 and m['recall'] is None and m['f1'] is None

def test_duplicate_candidates_rejected():
    with pytest.raises(AssertionError):s.metrics(['a']*5,{'a':3},5)

def test_provider_budget_and_plan():
    p=r.prepare();assert p['providers_called']==['openai'] and p['stage3_generations']==30 and p['batch_size']==1 and p['max_budget_usd']=='5.00'
    assert r.cost(1000000,1000000)==r.Decimal('.60')

def test_missing_usage_keeps_reservation():
    assert r.usage_cost({}) is None
    assert r.usage_cost({'input_tokens':10}) is None
    assert r.usage_cost({'input_tokens':1000,'output_tokens':100})==r.Decimal('.00015')

def test_unknown_metric_bounds_cover_every_assignment():
    from itertools import product
    g={str(i):(3 if i in (0,7) else None if i in (3,8) else 0) for i in range(10)};ranking=list(g)
    bounds=s.metrics(ranking,g,5)
    for bits in product((0,3),repeat=2):
        full={**g,'3':bits[0],'8':bits[1]};m=s.metrics(ranking,full,5)
        for name in ('precision','recall','f1'):assert bounds[name+'_lower']<=m[name]<=bounds[name+'_upper']

def test_actual_format_failure_modes_are_rejected():
    cs,qs=r.inputs();j=r.job('V21D001','AXV2P2_0048_01',1,cs,qs)
    d={'qid':j['qid'],'cid':j['cid'],'score':3,'reason':'word '*33,'quote':'Answer shopping questions'}
    assert not r.validate(json.dumps(d),j)['valid']
    d['reason']='Actual question answering.'
    assert not r.validate(json.dumps(d)+'</assistant>',j)['valid']
