from collections import OrderedDict
from fractions import Fraction
import pytest
from scripts import candidate_fusion_ablation as c

def test_rrf_formula_and_group_normalization():
    branches=OrderedDict([('p',['a','b','c']),('q',['b','c','a'])])
    rankings,m,o,mix,r=c.fuse(branches,['a','b','c'])
    assert m['a']==(Fraction(1,61)+Fraction(1,63))/2
    assert mix['a']==o['a']/2+m['a']/2
    assert rankings['mean_rrf'][0]=='b'

def test_duplicating_all_views_does_not_dilute_original():
    b={'x':['a','b','c'],'y':['c','a','b']}
    once=c.fuse(b,['b','a','c']);twice=c.fuse({**b,'x2':b['x'],'y2':b['y']},['b','a','c'])
    assert once[0]==twice[0] and once[1]==twice[1] and once[3]==twice[3]

def test_tie_and_branch_reordering_are_deterministic():
    a={'p':['a','b'],'q':['b','a']};b={'q':['b','a'],'p':['a','b']}
    assert c.fuse(a,['b','a'])[0]['mean_rrf']==['a','b']
    assert c.fuse(a,['b','a'])[0]==c.fuse(b,['b','a'])[0]

def test_full_candidate_tail_not_truncated():
    ids=[str(i) for i in range(112)];out=c.fuse({'p':ids,'q':list(reversed(ids))},ids)
    assert len(out[0]['mean_rrf'])==112 and set(out[0]['mean_rrf'])==set(ids)

def test_rr_trace_duplicates_and_prefix():
    b={'p':['a','b','c','d'],'q':['a','c','b','d']};trace=c.rr_trace(b,4)
    assert [(x['perspective_id'],x['cid']) for x in trace[:2]]==[('p','a'),('q','c')]
    assert trace[1]['skipped_duplicate_case_ids']==['a']
    assert len({x['cid'] for x in trace})==4

def test_missing_or_duplicate_branch_candidates_rejected():
    with pytest.raises(AssertionError):c.fuse({'p':['a','a']},['a','b'])

def test_zero_positive_is_undefined_and_macro_is_nested():
    grades={'a':0,'b':0};m=c.metrics(['a','b'],grades,1)
    assert m['precision']==0 and m['recall'] is None and m['f1'] is None
    rows=[]
    for q,values in [('q1',[1.,0.,0.]),('q2',[1.,1.,1.])]:
        for v in values:rows.append({'qid':q,'metrics':{str(k):{'precision':v,'recall':v,'f1':v,'true_positives':int(v)} for k in c.CFG['K']}})
    assert c.aggregate(rows)['20']['macro_f1']==pytest.approx(2/3)

def test_network_is_explicitly_forbidden():
    with pytest.raises(RuntimeError):c.no_network('https://api.openai.com')
