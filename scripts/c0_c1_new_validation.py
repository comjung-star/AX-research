"""Offline new-query adapter, blind source bundle and separately sealed evaluation."""
import argparse
import json
import random
import socket
import subprocess
from pathlib import Path

from ax_research.heldout import read,write,sha,jsonl
from ax_research.functional_mapping import extract,compare
from ax_research.action_aggregation import purpose_filter
from ax_research.semantic_mapping import combined_score,ranking_key
from ax_research.new_validation import evaluate as score_evaluation

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/c0-c1-new-validation-2026-11-02';INPUT=OUT/'input/questions.jsonl';CORPUS=ROOT/'docs/dense-bm25-candidates-2026-10-27/case_registry.json'


def state():
    from scripts.heldout_run import freeze
    model=(ROOT/read(ROOT/'configs/semantic_mapping_20261028.json')['model_path']).resolve();old=freeze(model)
    more=[ROOT/'src/ax_research/action_aggregation.py',ROOT/'configs/action_aggregation_20261102.json',ROOT/'scripts/heldout_run.py',INPUT,OUT/'policy.json',OUT/'preregistration.md',Path(__file__),ROOT/'src/ax_research/new_validation.py']
    return {'model_hashes':old['model'],'packages':old['packages'],'protected':old['protected'],'extra_hashes':{p.relative_to(ROOT).as_posix():sha(p) for p in more},'python':old['python'],'platform':old['platform'],'base':'1e6ad428ac23f493df9a86b1d05fae05f818dd36','policy':read(OUT/'policy.json'),'command':'python -m scripts.c0_c1_new_validation {freeze,predict,bundle,labels,evaluate}','paid_api_calls':0,'dynamic_perspectives':'NOT_RUN','workB_access':False}


def freeze():
    frozen=read(OUT/'input_freeze.json');assert sha(INPUT)==frozen['questions_sha256'] and sha(OUT/'policy.json')==frozen['policy_sha256'] and sha(OUT/'preregistration.md')==frozen['preregistration_sha256']
    write(OUT/'model_freeze.json',{**state(),'question_policy_commit':'bda99829','implementation_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()})


def verify():
    s=read(OUT/'model_freeze.json');assert all(s[k]==v for k,v in state().items()),'Frozen input/code/model drift'


def predict():
    verify();predroot=OUT/'predictions';predroot.mkdir(exist_ok=False)
    from scripts.heldout_run import predict as original_predict
    qs=jsonl(INPUT);model=(ROOT/read(ROOT/'configs/semantic_mapping_20261028.json')['model_path']).resolve()
    base=original_predict(qs,model,predroot)  # no labels supplied/read; old inference core unmodified
    details=read(predroot/'evidence.json')['records'];lookup={(r['query_id'],r['case_id']):r for r in details}
    rules=read(ROOT/'configs/functional_mapping_20261028.json');cfg=read(ROOT/'configs/action_aggregation_20261102.json')
    oldcp=read(ROOT/'docs/query-case-functional-mapping-2026-10-28/stage2/case_profiles.json');cp={c:{role:purpose_filter(p,cfg) for role,p in ps.items()} for c,ps in oldcp.items()};qp={q['query_id']:purpose_filter(extract(q['text'],rules),cfg) for q in qs}
    systems={'C0':base['systems']['C'],'C1':[],'C1_NO_EMBEDDING':[]};full=[]
    for q in qs:
        qid=q['query_id'];scores={s:{} for s in ('C1','C1_NO_EMBEDDING')}
        for c in base['case_ids']:
            x=lookup[qid,c];new=compare(qp[qid],cp[c]);sem=x['semantic']['score']
            assert combined_score(x['rule']['mapping_grade'],sem)==next(r for r in systems['C0'] if r['query_id']==qid)['scores'][c]
            scores['C1'][c]=combined_score(new['mapping_grade'],sem);scores['C1_NO_EMBEDDING'][c]=.5*new['mapping_grade']/4+.25
            full.append({'query_id':qid,'case_id':c,'old_rule':x['rule'],'new_rule':new,'semantic':x['semantic'],'tie':x['retrieval_tie'],'C1':scores['C1'][c],'C1_NO_EMBEDDING':scores['C1_NO_EMBEDDING'][c]})
        for name,values in scores.items():
            rank=sorted(values,key=lambda c:ranking_key(values[c],lookup[qid,c]['retrieval_tie'],c))
            systems[name].append({'query_id':qid,'ranking':rank,**{f'top{k}':rank[:k] for k in (5,10,20)},'scores':values})
    write(predroot/'rankings.json',{'query_ids':base['query_ids'],'case_ids':base['case_ids'],'systems':systems,'scope':'NEW_VALIDATION_ORIGINAL_ONLY'})
    write(predroot/'C1_details.json',{'records':full,'filtered_query_profiles':qp,'filtered_case_profiles':cp})
    write(OUT/'prediction_seal.json',{'model_freeze_sha256':sha(OUT/'model_freeze.json'),'files':{p.name:sha(p) for p in predroot.iterdir() if p.is_file()},'qrels_read':False,'new_validation':True,'not_final_Test':True,'paid_api_calls':0})
    print('Prediction sealed:10queries*3conditions*112; no scores displayed to reviewer')


def bundle():
    # All cases, independent of retrieval; no prediction files opened.
    assert (OUT/'prediction_seal.json').exists();dest=OUT/'blind_review';dest.mkdir(exist_ok=False)
    cases=read(CORPUS)['cases'];ids=sorted(cases);random.Random(20261102).shuffle(ids)
    mapping={f'E{i:03}':c for i,c in enumerate(ids,1)};rows=[]
    for eid,c in mapping.items():rows.append({'review_id':eid,'Problem':cases[c]['problem'],'Task':cases[c]['task'],'Context':cases[c]['context'],'Output':'Only literal Task artifact; no inferred effect/security/implementation','source_note':'Existing structured summaries, not original publication independently audited'})
    write(dest/'cases.json',{'cases':rows,'no_system_rank_or_score':True,'all112_not_pooled':True})
    write(OUT/'review_key.json',mapping)
    print('Blind112source bundle ready; analyst key stored separately')


def labels():
    # Materialize explicit assistant decisions; never fill unspecified items with0.
    matrix=read(OUT/'blind_review/assistant_matrix.json');source=read(OUT/'blind_review/cases.json')['cases'];qids=[q['query_id'] for q in jsonl(INPUT)];key=read(OUT/'review_key.json');rows=[]
    assert set(matrix['decisions'])==set(key) and len(key)==112
    for case in source:
        eid=case['review_id'];d=matrix['decisions'][eid];assert len(d['grades'])==10 and d['source_task']==case['Task']
        for i,qid in enumerate(qids):
            grade=d['grades'][i];assert grade in '0123U';g=None if grade=='U' else int(grade)
            note=d.get('pair_notes',{}).get(str(i+1))
            if g is None or g>0:assert note,'Nonzero/abstain needs pair-specific reasoning'
            rationale=note or f"문항{i+1}의 요청 기능과 다름. 사례의 실제 수행은 ‘{case['Task']}’. 판정자 원문검토: {d['operation_note']}"
            rows.append({'query_id':qid,'case_id':key[eid],'grade':g,'status':'ABSTAIN' if g is None else 'JUDGED','label_source':'AI-Silver','rationale':rationale,'source_task':case['Task'],'review_id':eid})
    write(OUT/'qrels.json',{'records':rows,'source':'Same assistant author/reviewer, ranks/scores not displayed during grading; no independent validation or Human-Gold','matrix_sha256':sha(OUT/'blind_review/assistant_matrix.json'),'pre_prediction_author_context_known':True})
    write(OUT/'label_seal.json',{'qrels_sha256':sha(OUT/'qrels.json'),'prediction_seal_sha256':sha(OUT/'prediction_seal.json'),'matrix_sha256':sha(OUT/'blind_review/assistant_matrix.json'),'post_label_edits_forbidden':True})
    print('Explicit judgments sealed; no ranking opened by label materializer')


def evaluate():
    verify();seal=read(OUT/'prediction_seal.json')
    for name,h in seal['files'].items():assert sha(OUT/'predictions'/name)==h
    assert sha(OUT/'qrels.json')==read(OUT/'label_seal.json')['qrels_sha256']
    dest=OUT/'evaluation';dest.mkdir(exist_ok=False)
    result=score_evaluation(read(OUT/'predictions/rankings.json'),read(OUT/'qrels.json')['records'])
    write(dest/'metrics.json',result);write(dest/'complete.json',{'metrics_sha256':sha(dest/'metrics.json'),'prediction_sha256':sha(OUT/'prediction_seal.json'),'qrels_sha256':sha(OUT/'qrels.json'),'old_models_changed':False,'workB_read':False,'paid_api_calls':0})
    print('New-validation evaluation complete; not final Test')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['freeze','predict','bundle','labels','evaluate']);a=p.parse_args()
    def blocked(*args,**kwargs):raise RuntimeError('Network disabled; no paidAPI')
    socket.socket.connect=blocked;socket.create_connection=blocked
    try:{'freeze':freeze,'predict':predict,'bundle':bundle,'labels':labels,'evaluate':evaluate}[a.stage]()
    except BaseException as e:
        fail=OUT/(a.stage+'_failed.json')
        if not fail.exists():write(fail,{'error':type(e).__name__,'message':str(e),'stage':a.stage,'auto_retry':False})
        raise
