import pytest
from ax_research.new_validation import evaluate,SYSTEMS


def fixture(n=2):
    ids=[f'C{i:03}' for i in range(112)];qs=[f'Q{i}' for i in range(n)]
    pred={'case_ids':ids,'query_ids':qs,'systems':{s:[{'query_id':q,'ranking':ids[:]} for q in qs] for s in SYSTEMS}}
    labels=[{'query_id':q,'case_id':c,'grade':2,'status':'JUDGED','label_source':'AI-Silver','rationale':'Synthetic unit fixture'} for q in qs for c in ids]
    return pred,labels


@pytest.mark.parametrize('n',[1,2,10])
def test_complete(n):
    p,l=fixture(n);r=evaluate(p,l)
    assert len(r['per_query'])==3*n
    row=r['per_query'][0]
    assert row['metrics']['Precision@5']==1
    assert row['metrics']['Recall@5']==5/112
    assert row['metrics']['nDCG@5']==1
    assert all(m['defined']==n for m in r['macro_common_queries'])


@pytest.mark.parametrize('status',['ABSTAIN','UNJUDGED'])
def test_unresolved_not_zero(status):
    p,l=fixture(1);l[0].update(status=status,grade=None)
    r=evaluate(p,l)['per_query'][0]
    assert not r['complete112'] and r['metrics']['Recall@20'] is None and r['metrics']['Precision@5'] is None and r['metrics']['nDCG@5'] is None


def test_partial_only_precision():
    p,l=fixture(1);r=evaluate(p,l[:20])['per_query'][0]
    assert r['metrics']['Precision@20']==1
    assert r['metrics']['Recall@20'] is None and r['metrics']['F1@20'] is None and r['metrics']['nDCG@10'] is None


def test_zero_positives_and_weak_gain():
    p,l=fixture(1)
    for r in l:r['grade']=1
    m=evaluate(p,l)['per_query'][0]['metrics']
    assert m['Precision@5']==0 and m['Recall@5'] is None and m['F1@5'] is None and m['nDCG@5']==1


@pytest.mark.parametrize('kind',['duplicate','grade_bool','bad_status','wrong_source','invalid_id','missing_rationale'])
def test_invalid_qrels(kind):
    p,l=fixture(1)
    if kind=='duplicate':l.append(l[0].copy())
    elif kind=='grade_bool':l[0]['grade']=True
    elif kind=='bad_status':l[0]['status']='DONE'
    elif kind=='wrong_source':l[0]['label_source']='Human-Gold'
    elif kind=='invalid_id':l[0]['case_id']='X'
    else:l[0]['rationale']=''
    with pytest.raises(ValueError):evaluate(p,l)


def test_common_eligible_questions():
    p,l=fixture(2);l[0].update(status='ABSTAIN',grade=None)
    rank=p['systems']['C1'][0]['ranking'];rank[0],rank[30]=rank[30],rank[0]
    r=evaluate(p,l)
    rows=[m for m in r['macro_common_queries'] if m['comparison']=='primary' and m['metric']=='Precision@5']
    assert all(m['included_query_ids']==['Q1'] for m in rows)


def test_zero_idcg():
    p,l=fixture(1)
    for r in l:r['grade']=0
    assert evaluate(p,l)['per_query'][0]['metrics']['nDCG@5'] is None
