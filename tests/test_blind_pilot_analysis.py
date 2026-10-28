import copy
import math
import pytest
from scripts.blind_pilot_analyze import analyze,grade,ndcg,read_review
from scripts import blind_pilot_five as p

def fixture_data():
    public=[];key=[];pred={s:[] for s in 'ABC'}
    for q in range(5):
        qid='SYNTHETIC_Q'+str(q);ids=['SYNTHETIC_C'+str(i) for i in range(112)]
        for s in 'ABC':pred[s].append({'qid':qid,'ranking':ids})
        for i,cid in enumerate(ids[:12]):
            eid=f'SYNTHETIC_{q}_{i}';values=[eid,'仮想質問','仮想説明','仮想Task','仮想Context','仮想出典','','']
            public.append(dict(zip(p.CFG['blind_fields'],values)));key.append({'evaluation_id':eid,'qid':qid,'case_id':cid,'unknown33':i>=10})
    return public,key,pred

def test_empty_not_zero():
    public,key,pred=fixture_data();r=analyze(public,public,key,pred)
    assert r['human_scored_pairs']==0 and all(m['precision'] is None and m['nDCG_judged_pool'] is None for m in r['metrics'])

def test_known_complete_synthetic_metrics():
    public,key,pred=fixture_data();rows=copy.deepcopy(public)
    for r in rows:r['관련성 점수']='3'
    out=analyze(rows,public,key,pred)
    assert all(m['precision']==1 and math.isclose(m['nDCG_judged_pool'],1) for m in out['metrics'])
    assert all(m['precision_official_macro']==1 for m in out['macro'])

def test_zero_is_a_real_judgment():
    assert grade(0)==(0,'SCORED')
    public,key,pred=fixture_data();rows=copy.deepcopy(public)
    for r in rows:r['관련성 점수']='0'
    out=analyze(rows,public,key,pred)
    assert all(m['precision']==0 and m['nDCG_judged_pool'] is None for m in out['metrics'])

def test_hold_does_not_become_zero():
    assert grade('판단 보류')==(None,'HELD')

@pytest.mark.parametrize('value',['4','-1','2.5','nan','inf','=1+1','관련'])
def test_bad_grade_rejected(value):
    with pytest.raises(ValueError):grade(value)

def test_pending_outside_topk_blocks_pool_ndcg_only():
    public,key,pred=fixture_data();rows=copy.deepcopy(public)
    for r in rows:r['관련성 점수']='3'
    rows[11]['관련성 점수']='판단 보류'
    out=analyze(rows,public,key,pred);m=out['metrics'][0]
    assert m['precision']==1 and m['nDCG_judged_pool'] is None

def test_partial_macro_disclosed():
    public,key,pred=fixture_data();rows=copy.deepcopy(public)
    for r in rows:r['관련성 점수']='3'
    rows[0]['관련성 점수']=''
    out=analyze(rows,public,key,pred);m=out['macro'][0]
    assert m['precision_official_macro'] is None and m['precision_available_questions']==4

def test_duplicate_missing_and_unknown_ids_rejected():
    public,key,pred=fixture_data()
    for rows in [public+[public[0]],public[1:],[{**public[0],'평가 ID':'ALIEN'}]+public[1:]]:
        with pytest.raises(ValueError):analyze(rows,public,key,pred)

def test_source_content_edit_rejected():
    public,key,pred=fixture_data();rows=copy.deepcopy(public);rows[0]['실제 수행 Task']='Changed'
    with pytest.raises(ValueError):analyze(rows,public,key,pred)

def test_ndcg_gain_and_discount():
    value=ndcg(['b','a'],{'a':3,'b':1},{'a','b'},2)
    expected=(1+7/math.log2(3))/(7+1/math.log2(3))
    assert math.isclose(value,expected)

def test_reviewer_artifact_is_unfilled():
    public=p.read(p.OUT/'evaluator/review_rows.json')['rows']
    assert len(public)==103 and all(not r['관련성 점수'] and not r['평가 의견'] for r in public)
    assert read_review(p.OUT/'evaluator/blind_review.csv')==public

def test_workbook_roundtrip_same_blind_values():
    assert read_review(p.OUT/'evaluator/blind_review.xlsx')==p.read(p.OUT/'evaluator/review_rows.json')['rows']
