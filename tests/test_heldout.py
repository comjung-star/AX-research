import json
from pathlib import Path
import pytest
from ax_research.heldout import *


def prediction(n=1):
    ids=[f'C{i:03}' for i in range(112)]
    return {'case_ids':ids,'query_ids':[f'Q{i}' for i in range(n)],'systems':{s:[{'query_id':f'Q{i}','ranking':ids,**{f'top{k}':ids[:k] for k in (5,10,20)}} for i in range(n)] for s in SYSTEMS}}


def labels(p,grade=2,source='AI-Silver'):
    return [{'query_id':q,'case_id':c,'grade':grade,'status':'JUDGED','label_source':source,'rationale':'Synthetic fixture only'} for q in p['query_ids'] for c in p['case_ids']]


@pytest.mark.parametrize('n',[1,2,7])
def test_dynamic_count(n):
    p=prediction(n); r=evaluate(p,labels(p),'FULL_CORPUS',['AI-Silver'])
    assert len(r['per_query'])==4*n
    assert all(m['defined']==n and m['total']==n for m in r['macro'])
    assert r['per_query'][0]['metrics']['Recall@5']==5/112
    assert r['per_query'][0]['metrics']['nDCG@5']==1


def test_zero_positive():
    p=prediction(); r=evaluate(p,labels(p,0),'FULL_CORPUS',['AI-Silver'])['per_query'][0]
    assert r['metrics']['Precision@5']==0
    assert r['metrics']['Recall@5'] is None and r['metrics']['F1@5'] is None
    assert r['metrics']['nDCG@5'] is None


@pytest.mark.parametrize('status',['ABSTAIN','UNJUDGED'])
def test_not_zero(status):
    p=prediction(); rows=labels(p); rows[0].update(grade=None,status=status)
    m=evaluate(p,rows,'FULL_CORPUS',['AI-Silver'])['per_query'][0]['metrics']
    assert all(v is None for v in m.values())


def test_partial():
    p=prediction(); rows=labels(p)[:20]
    m=evaluate(p,rows,'PARTIAL',['AI-Silver'])['per_query'][0]['metrics']
    assert m['Precision@20']==1 and m['Recall@5'] is None and m['nDCG@5'] is None


@pytest.mark.parametrize('change',['duplicate','unknown_query','unknown_case','bool_grade','bad_status','missing_rationale','source'])
def test_invalid_qrels(change):
    p=prediction(); rows=labels(p)
    if change=='duplicate':rows.append(rows[0].copy())
    elif change=='unknown_query':rows[0]['query_id']='X'
    elif change=='unknown_case':rows[0]['case_id']='X'
    elif change=='bool_grade':rows[0]['grade']=True
    elif change=='bad_status':rows[0]['status']='MISSING'
    elif change=='missing_rationale':rows[0]['rationale']=''
    else:rows[0]['label_source']='Human-Gold'
    with pytest.raises(ValueError):evaluate(p,rows,'FULL_CORPUS',['AI-Silver'])


def test_sources_separate():
    p=prediction(); r=evaluate(p,labels(p,2)+labels(p,0,'Human-Gold'),'FULL_CORPUS',['AI-Silver','Human-Gold'])
    assert len(r['macro'])==88
    assert {x['label_source'] for x in r['per_query']}=={'AI-Silver','Human-Gold'}


@pytest.mark.parametrize('kind',['rank','top','system','query'])
def test_prediction_validation(kind):
    p=prediction()
    if kind=='rank':p['systems']['A'][0]['ranking'][0]='X'
    elif kind=='top':p['systems']['A'][0]['top5']=[]
    elif kind=='system':del p['systems']['B']
    else:p['systems']['B'][0]['query_id']='X'
    with pytest.raises(ValueError):validate_predictions(p)


def test_exclusive_output(tmp_path):
    p=tmp_path/'artifact.json';write(p,{'old':True})
    with pytest.raises(FileExistsError):write(p,{'new':True})
    assert read(p)=={'old':True}


@pytest.mark.parametrize('kind',['ok','duplicate','split','overlap','id','empty'])
def test_questions(tmp_path,kind):
    row={'query_id':'fixture','text':'Synthetic fixture','split':'TEST'}
    rows=[row]
    if kind=='duplicate':rows.append(row)
    elif kind=='split':row['split']='DEV'
    elif kind=='id':row['query_id']=''
    elif kind=='empty':row['text']=''
    path=tmp_path/'q.jsonl';path.write_text('\n'.join(json.dumps(r) for r in rows))
    if kind=='ok':assert len(questions(path))==1
    else:
        with pytest.raises(ValueError):questions(path,previous=[row] if kind=='overlap' else [])


def test_metric_known():
    p=prediction(); rows=labels(p,0);rows[0]['grade']=3;rows[10]['grade']=2
    m=evaluate(p,rows,'FULL_CORPUS',['AI-Silver'])['per_query'][0]['metrics']
    assert m['Precision@5']==.2 and m['Recall@5']==.5
    assert m['F1@5']==pytest.approx(2*.2*.5/.7)
    assert m['nDCG@5']==pytest.approx(7/(7+3/math.log2(3)))


@pytest.mark.parametrize('change',['valid','threshold','scope','source','history','corpus','digest'])
def test_manifest_metadata(tmp_path,change):
    m={'schema_version':'ax-heldout-v1','test_id':'fixture_metadata_only',
       'grade_scale':[0,1,2,3],'relevant_threshold':2,'corpus':{'id':'ax112','case_count':112,'sha256':'a'*64},
       'judgment_scope':'FULL_CORPUS','label_sources':['AI-Silver'],
       'unused_history':{'previously_used':False,'provenance':'fixture','exposure_log':['fixture metadata']},
       'files':{k:{'path':k+'.jsonl','sha256':'b'*64} for k in ('questions','qrels')}}
    if change=='threshold':m['relevant_threshold']=3
    elif change=='scope':m['judgment_scope']='POOL'
    elif change=='source':m['label_sources']=['AI pretending Gold']
    elif change=='history':m['unused_history']['previously_used']=True
    elif change=='corpus':m['corpus']['case_count']=111
    elif change=='digest':m['files']['qrels']['sha256']='x'
    path=tmp_path/'metadata.json';write(path,m)
    if change=='valid':assert manifest(path,'a'*64)==m
    else:
        with pytest.raises(ValueError):manifest(path,'a'*64)


def test_inference_and_evaluation_dev_only(tmp_path,monkeypatch):
    from scripts import heldout_run as run
    from types import SimpleNamespace
    p=tmp_path/'dev.jsonl';p.write_text(json.dumps({'query_id':'Q0','text':'synthetic adapter fixture','split':'DEV'}))
    frozen={'adapter':{}}
    monkeypatch.setattr(run,'freeze',lambda path:frozen)
    def fake_predict(qs,model,out):
        assert qs[0]['split']=='DEV'
        write(out/'evidence.json',{'fixture':True})
        return prediction()
    monkeypatch.setattr(run,'predict',fake_predict)
    inf=tmp_path/'inference';inf.mkdir()
    args=SimpleNamespace(model_path=str(tmp_path),development=True,questions=str(p),manifest=None)
    run.inference(args,inf)
    assert read(inf/'complete.json')['qrels_read'] is False
    for k in (5,10,20):assert (inf/f'top{k}.json').exists()
    qrels=tmp_path/'qrels.jsonl';qrels.write_text('\n'.join(json.dumps(r) for r in labels(prediction())))
    ev=tmp_path/'evaluation';ev.mkdir()
    args=SimpleNamespace(prediction_run=str(inf),development=True,qrels=str(qrels),scope='FULL_CORPUS',label_sources=['AI-Silver'])
    run.evaluation(args,ev)
    assert read(ev/'complete.json')['state']=='COMPLETE'
    (inf/'evidence.json').write_text('{}')
    ev2=tmp_path/'evaluation2';ev2.mkdir()
    with pytest.raises(ValueError,match='artifact drift'):run.evaluation(args,ev2)


def test_main_failure_preserved(tmp_path,monkeypatch):
    from scripts import heldout_run as run
    def fail(args,out):raise RuntimeError('fixture failure')
    monkeypatch.setattr(run,'inference',fail)
    monkeypatch.setattr('sys.argv',['heldout_run','infer','--run-id','failure','--output-root',str(tmp_path),'--development','--questions','fixture-unused','--model-path','fixture-unused'])
    with pytest.raises(RuntimeError):run.main()
    assert read(tmp_path/'failure/failed.json')['state']=='FAILED'
    assert not (tmp_path/'failure/complete.json').exists()
    with pytest.raises(FileExistsError):run.main()
