"""Only existing Dev queries/old AI-Silver. Never uses heldout input or API."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from ax_research.heldout import read, write, sha
from scripts.heldout_run import ROOT


def main():
    p=argparse.ArgumentParser();p.add_argument('--output-root',required=True);args=p.parse_args()
    root=Path(args.output_root).resolve();root.mkdir(exist_ok=False,parents=True)
    dev=read(ROOT/'data/v2_5/research/dev_queries.json')['queries'][:2]
    qpath=root/'dev_questions.jsonl'
    qpath.write_text(''.join(json.dumps({'query_id':q['query_id'],'text':q['query'],'split':'DEV'},ensure_ascii=False)+'\n' for q in dev),encoding='utf-8')
    model=(ROOT/read(ROOT/'configs/semantic_mapping_20261028.json')['model_path']).resolve()
    commands=[]
    def call(arguments,expected=0):
        command=[sys.executable,'-m','scripts.heldout_run',*arguments]
        result=subprocess.run(command,cwd=ROOT,text=True,capture_output=True,encoding='utf-8')
        commands.append({'command':command,'returncode':result.returncode,'stdout':result.stdout,'stderr':result.stderr})
        if (result.returncode==0) != (expected==0):raise RuntimeError(result.stderr)
    base=['--output-root',str(root),'--development']
    for rid in ('infer1','infer2'):
        call(['infer',*base,'--run-id',rid,'--questions',str(qpath),'--model-path',str(model)])
    p1=read(root/'infer1/predictions.json');p2=read(root/'infer2/predictions.json')
    if p1 != p2:raise ValueError('Non-reproducible predictions')
    historical_a=read(ROOT/'docs/query-case-functional-mapping-2026-10-28/stage4_dev/results.json')['systems']
    historical_b=read(ROOT/'docs/query-case-semantic-mapping-2026-10-28/ranking/rankings.json')['systems']
    matches=[]
    for s,old in [('Single Dense',historical_a['single_dense__original']),('A',historical_a['M_O_SINGLE']),('B',historical_b['SEM_O_SINGLE']),('C',historical_b['COMB_O_SINGLE'])]:
        for row in p1['systems'][s]:
            previous=next(r for r in old if r['qid']==row['query_id'])
            if row['ranking'] != previous['ranking']:raise ValueError('Historical rank drift')
            matches.append({'system':s,'query_id':row['query_id'],'all112_equal':True})
    # Old Dev labels are opened ONLY after both prediction seals exist.
    old=read(ROOT/'docs/stage123-openai-triplicate-2026-10-27/stage1_silver.json')['records']
    ids={q['query_id'] for q in dev}; rows=[]
    for row in old:
        if row['qid'] in ids:
            if row['held'] or row['silver_score'] not in range(4):raise ValueError('Cannot silently transform old label')
            rows.append({'query_id':row['qid'],'case_id':row['cid'],'grade':row['silver_score'],'status':'JUDGED','label_source':'AI-Silver','rationale':'Existing Dev same-model triplicate median; reused raw grade only for adapter smoke, threshold2 differs from old Dev3; NOT Test.'})
    qrels=root/'dev_qrels.jsonl';qrels.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows),encoding='utf-8')
    call(['evaluate',*base,'--run-id','eval1','--prediction-run',str(root/'infer1'),'--qrels',str(qrels),'--scope','FULL_CORPUS'])
    call(['infer',*base,'--run-id','infer1','--questions',str(qpath),'--model-path',str(model)],expected=1)
    write(root/'smoke_receipt.json',{'development_only':True,'independent_test_executed':False,'query_count':2,'systems':4,'rankings':8,'candidate_count':112,'repeat_equal':True,'historical_rank_matches':matches,'existing_output_rejected':True,'qrels_rows':len(rows),'metrics_not_test_performance':True,'api_calls':0,'commands':commands,'prediction_sha256':sha(root/'infer1/predictions.json')})
    print(root/'smoke_receipt.json')


if __name__=='__main__':main()
