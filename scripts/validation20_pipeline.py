"""New20 Validation pipeline. New query inference and blinded AI grading only."""
import argparse
from collections import Counter
import json
import os
from pathlib import Path
import subprocess
import sys
from ax_research.heldout import read,write,sha,jsonl
from scripts import core_preservation_run as ex
from scripts import validation123_api as api

ROOT=Path(__file__).resolve().parents[1]
STUDY=ROOT/'docs/validation-new20-20261107'
OUT=STUDY/'run'
QUESTIONS=STUDY/'questions.jsonl'
CORPUS=ROOT/'docs/dense-bm25-candidates-2026-10-27/case_registry.json'

def qrels_input(qid,group):
    qs={q['query_id']:q['text'] for q in jsonl(QUESTIONS)}
    cases=read(CORPUS)['cases']
    return {'query_id':qid,'business_problem':qs[qid],
        'cases':[{'case_id':cid,'Problem':cases[cid]['problem'],
            'Task':cases[cid]['task'],'Context':cases[cid]['context']} for cid in group]}

def blind_validator(kind,qid,data):
    payload=ex.ACTIVE_JUDGE_PAYLOAD
    assert payload['query_id']==qid
    cases={c['case_id']:c for c in payload['cases']}
    assert set(data)=={'assessments'}
    rows=data['assessments']
    assert len(rows)==len(cases) and {r['case_id'] for r in rows}==set(cases)
    for r in rows:
        assert set(r)=={'query_id','case_id','grade','status','reason','task_quote'}
        assert r['query_id']==qid and r['status'] in ('JUDGED','ABSTAIN')
        assert ((r['status']=='JUDGED' and type(r['grade']) is int and 0<=r['grade']<=3)
            or (r['status']=='ABSTAIN' and r['grade'] is None))
        assert isinstance(r['reason'],str) and r['reason'].strip()
        assert isinstance(r['task_quote'],str) and r['task_quote'] in cases[r['case_id']]['Task']
        assert len(r['task_quote'])<=140

def setup():
    qs=jsonl(QUESTIONS)
    assert len(qs)==20 and len({q['query_id'] for q in qs})==20
    assert all(q['split']=='NEW_VALIDATION_20' for q in qs)
    ids=sorted(read(CORPUS)['cases'])
    assert len(ids)==112
    ex.OUT=OUT;ex.QUESTIONS=QUESTIONS
    ex.MODEL=Path(os.environ.get('BGE_MODEL_PATH','/nonexistent/model')).resolve()
    ex.REVIEW_VALIDATOR=blind_validator
    ex.configure()
    OUT.mkdir(parents=True,exist_ok=True)
    return qs,ids

def generate():
    qs,_=setup()
    for rep in (1,2,3):
        for q in qs:
            for kind in ('C','X','E'):
                api.call(kind,q['query_id'],rep)
    ex.ledger()
    write(OUT/'generation_finished.json',{'C':60,'X':60,'E':60,'all_new20':True,
        'prior_8_query_rankings_reused':False,'blind_labels_read':False})

def infer():
    qs,_=setup()
    assert (OUT/'generation_finished.json').exists()
    protected=[CORPUS,QUESTIONS,ROOT/'configs/semantic_mapping_20261028.json',
        ROOT/'configs/functional_mapping_20261028.json',
        ROOT/'configs/action_aggregation_20261102.json',
        ROOT/'scripts/core_preservation_prompts.py',
        ROOT/'scripts/validation123_multiview.py',
        ROOT/'src/ax_research/action_aggregation.py']
    write(OUT/'preregistration.json',{'protected_sha256':{
        p.relative_to(ROOT).as_posix():sha(p) for p in protected},
        'cohort':'NEW_VALIDATION_20','case_count':112,'prior_test_protected':True})
    scratch=Path(os.environ.get('RUNNER_TEMP','/tmp'))/'ax-new20-scratch'
    ex.inference(scratch)
    p=read(OUT/'predictions.json')
    assert len(p['query_ids'])==20 and len(p['case_ids'])==112
    assert len(p['systems']['A'])==20 and len(p['systems']['C'])==len(p['systems']['E'])==60
    write(OUT/'new20_prediction_ready.json',{'actual_new_inference':True,
        'predictions_sha256':sha(OUT/'predictions.json'),
        'labels_read_during_inference':False})

def judge():
    qs,_=setup()
    assert read(OUT/'new20_prediction_ready.json')['actual_new_inference']
    ex.judge()
    labels=read(OUT/'labels.json')['records']
    assert len(labels)==2240
    write(OUT/'primary_review_status.json',{'assessed_rows':len(labels),
        'statuses':dict(Counter(r['status'] for r in labels)),
        'model':'gpt-6-luna','rankings_blinded_in_prompt':True,'human_gold':False})

def judge2():
    qs,ids=setup()
    assert (OUT/'labels.json').exists()
    firstbody=ex.body
    firstvalidate=ex.validate
    def secondbody(kind,qid,rep):
        if kind=='judge2':
            b=firstbody('judge',qid,rep);b['model']='gpt-6.1-terra'
            return b
        return firstbody(kind,qid,rep)
    def secondvalidate(kind,qid,data):
        return blind_validator(kind,qid,data) if kind=='judge2' else firstvalidate(kind,qid,data)
    api.body=secondbody;api.validate=secondvalidate
    rows=[]
    for q in qs:
        for start in range(0,len(ids),16):
            ex.ACTIVE_JUDGE_PAYLOAD=qrels_input(q['query_id'],ids[start:start+16])
            r=api.call('judge2',q['query_id'],start//16+1)
            rows.extend(r['data']['assessments'])
    assert len(rows)==2240
    out=[{'query_id':r['query_id'],'case_id':r['case_id'],'grade':r['grade'],
        'status':r['status'],'label_source':'gpt-6.1-terra independent grading request',
        'rationale':r['reason'],'task_quote':r['task_quote']} for r in rows]
    write(OUT/'labels_second.json',{'records':out,'model':'gpt-6.1-terra',
        'same_provider_different_model':True,'human_gold':False})
    ex.ledger()

def compare():
    qs,_=setup()
    pred=OUT/'predictions.json'
    assert sha(pred)==read(OUT/'new20_prediction_ready.json')['predictions_sha256']
    first=read(OUT/'labels.json')['records']
    second=read(OUT/'labels_second.json')['records'] if (OUT/'labels_second.json').exists() else []
    def export(name,records):
        clean=[{'query_id':r['query_id'],'case_id':r['case_id'],
            'grade':r['grade'] if r['status']=='JUDGED' else None,
            'status':'JUDGED' if r['status']=='JUDGED' else 'ABSTAIN'} for r in records]
        assert len(clean)==2240 and len({(r['query_id'],r['case_id']) for r in clean})==2240
        write(OUT/f'blind_{name}.json',{'records':clean})
        subprocess.run([sys.executable,str(ROOT/'scripts/validation20_compare.py'),
            str(pred),str(OUT/f'blind_{name}.json'),
            str(OUT/f'validation_{name}.json')],check=True)
    export('luna',first)
    if second:
        export('terra',second)
        b={(r['query_id'],r['case_id']):r for r in second}
        combined=[];stats=Counter()
        for r in first:
            t=b[r['query_id'],r['case_id']]
            agree=r['status']==t['status']=='JUDGED' and r['grade']==t['grade']
            stats['same_grade' if agree else 'unresolved']+=1
            combined.append({'query_id':r['query_id'],'case_id':r['case_id'],
                'grade':r['grade'] if agree else None,
                'status':'JUDGED' if agree else 'ABSTAIN'})
        write(OUT/'reviewer_agreement.json',{'counts':dict(stats),
            'same_provider_different_models':True,
            'disagreements_not_imputed':True})
        export('agreement',combined)
    write(OUT/'final_status.json',{'validation_questions':20,'case_count':112,
        'original_test_accessed':False,'baseline_E_and_I2_I3':True,
        'actual_new_retrieval_done':True,'blind_primary_done':True,
        'independent_second_model_done':bool(second),
        'note':'AI provisional relevance, not human gold; compare and unresolved rows separately.'})

def main():
    p=argparse.ArgumentParser()
    p.add_argument('stage',choices=['generate','infer','judge','judge2','compare'])
    stage=p.parse_args().stage
    {'generate':generate,'infer':infer,'judge':judge,'judge2':judge2,
     'compare':compare}[stage]()
if __name__=='__main__':main()
