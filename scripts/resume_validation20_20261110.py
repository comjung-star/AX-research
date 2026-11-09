"""Prepare/resume only the24 missing credit-blocked validation judgments; no score tuning."""
import argparse,json,shutil
from datetime import datetime,timezone
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from scripts.perspective_omission_validation20_20261110 import OUT,ROOT,N,read,save,sha,guard,api,trial,verify

def prepare():
    guard();assert not (OUT/'metrics.json').exists(),'No partial performance calculation before entire run'
    ranks=read(OUT/'rankings.json');assert len(ranks)==20
    existing={p.name:sha(p) for p in (OUT/'api').glob('*.json') if not p.name.endswith('.request.json')}
    jobs=[];expected=0.;a,b=api.PRICES['openai']
    for q in ranks:
        for batch in range(4):
            ident=f'judge_{q}_b{batch:02}';path=OUT/f'api/openai_{ident}.json'
            old=read(path) if path.exists() else {'status':'NOT_ATTEMPTED'}
            if old['status']=='VALID_JSON':continue
            assert old['status'] in ('HTTP_ERROR','NOT_ATTEMPTED')
            planned=OUT/f'planned-requests/{ident}.json';request=read(planned)
            assert api.body('openai',request['system'],request['payload'],request['schema'],12288)==request['body']
            retry_id=ident+'_resume1';retry_path=OUT/f'api/openai_{retry_id}.json'
            if not retry_path.exists():expected+=(len(json.dumps(request['body'],ensure_ascii=False).encode())*a+12288*b)/1e6
            jobs.append({'original_id':ident,'resumed_id':retry_id,'original_status':old['status'],'input_path':str(planned.relative_to(OUT)),'sha256':sha(planned)})
    assert len(jobs)==24;assert api.ledger()['reserved_usd']+expected<=api.BUDGET
    plan={'at':datetime.now(timezone.utc).isoformat(),'missing_batches':jobs,'count':len(jobs),'missing_case_pairs':28*len(jobs),
        'existing_api_receipt_hashes':existing,'successful_judge_batches':56,'http_credit_errors':8,'not_attempted':16,
        'existing_reserved_usd':api.ledger()['reserved_usd'],'additional_reserved_usd':expected,'budget_usd':api.BUDGET,
        'all_questions_and_method_unchanged':True,'valid_responses_will_not_be_regenerated':True,'partial_performance_computed':False,
        'requires':'User reports API credit restored; no automatic topup or repeated probing'}
    if not (OUT/'resume-plan.json').exists():save(OUT/'resume-plan.json',plan)
    if (OUT/'labels.json').exists() and not (OUT/'labels-before-resume.json').exists():shutil.copyfile(OUT/'labels.json',OUT/'labels-before-resume.json')
    save(OUT/'pause-status.json',{'state':'PAUSED_EXTERNAL_API_CREDIT','full112_judged_questions':14,'remaining_questions':['VQ015','VQ016','VQ017','VQ018','VQ019','VQ020'],'remaining_batches':24,'remaining_case_judgments':672,'running_requests':0,'cost':api.ledger(),'no_partial_score_calculation':True})
    print('RESUME_PLAN_READY24',flush=True)

def run():
    guard();plan=read(OUT/'resume-plan.json');assert not (OUT/'metrics.json').exists()
    for i in range(0,plan['count'],8):
        def work(job):
            p=OUT/job['input_path'];assert sha(p)==job['sha256'];r=read(p)
            return api.call('openai',job['resumed_id'],r['system'],r['payload'],r['schema'],12288)
        with ThreadPoolExecutor(max_workers=8) as ex:rows=list(ex.map(work,plan['missing_batches'][i:i+8]))
        if any(r['status']=='HTTP_ERROR' and any(t in r.get('error','') for t in ['credit_balance','insufficient_quota']) for r in rows):
            save(OUT/'resume-credit-stop.json',{'at':datetime.now(timezone.utc).isoformat(),'group':i//8,'no_more_groups_submitted':True});raise RuntimeError('Provider credit still exhausted')
    assert all(sha(OUT/'api'/p)==h for p,h in plan['existing_api_receipt_hashes'].items())
    save(OUT/'resume-run.json',{'all_original_receipts_unchanged':True,'results':{j['resumed_id']:read(OUT/f"api/openai_{j['resumed_id']}.json")['status'] for j in plan['missing_batches']},'cost':api.ledger()});print('RESUMED24',flush=True)

def collect():
    guard();ranks=read(OUT/'rankings.json');plan=read(OUT/'resume-plan.json');overrides={j['original_id']:j for j in plan['missing_batches']};_,reg,_=trial.sources();labels={}
    for q in ranks:
        import random
        ids=sorted(reg);random.Random(20261109+int(q[-3:])).shuffle(ids);cases={};errors=[]
        for i in range(0,112,28):
            ident=f'judge_{q}_b{i//28:02}'
            try:
                if ident in overrides:
                    j=overrides[ident];req=read(OUT/j['input_path']);path=OUT/f"api/openai_{j['resumed_id']}.json";r=read(path)
                    saved=read(path.with_name(path.stem+'.request.json'));assert all(saved[k]==req[k] for k in ['system','payload','schema','body'])
                else:r=read(OUT/f'api/openai_{ident}.json')
                assert r['status']=='VALID_JSON',r.get('error',r['status']);rows=r['parsed']['rows'];assert len(rows)==28 and {x['position'] for x in rows}==set(range(28))
                for x in rows:
                    c=ids[i+x['position']];assert x['grade'] in (0,1,2,3);assert len(set(x['perspectives']))==len(x['perspectives']);cases[c]={**x,'bound_source_task':reg[c]['task']}
            except Exception as e:errors.append({'batch':i//28,'error':str(e)[:250]})
        labels[q]={'cases':cases,'complete':len(cases)==112,'errors':errors}
    old=read(OUT/'labels-before-resume.json');assert all(labels[q]['cases'][c]==r for q,v in old.items() for c,r in v['cases'].items())
    save(OUT/'labels.json',labels);print('COMPLETED_LABELS',[(q,len(v['cases'])) for q,v in labels.items()],flush=True)

def structure():
    guard();rs=read(OUT/'rankings.json');f=read(OUT/'rank-freeze.json');assert sha(OUT/'rankings.json')==f['rankings_sha256'] and sha(OUT/'vectors.npz')==f['vectors_sha256']
    cat,reg,profiles=trial.sources();ss=read(OUT/'fresh-selections.json')
    with np.load(OUT/'vectors.npz',allow_pickle=False) as a:bank=dict(zip(a['texts'].tolist(),a['vectors']))
    def score(p,t,ids):return {c:float(np.clip(bank[t]@bank[reg[c]['task']],-1,1)) for c in ids}
    for q,row in rs.items():
        scores={c:float(np.mean([bank[row['question']]@bank[r[k]] for k in ['problem','task','context']])) for c,r in reg.items()};order=sorted(reg,key=lambda c:(-scores[c],c))
        replay=trial.build_variants(ss[q],cat,profiles,reg,score,order);replay.update({'question':row['question'],'base_order':order,'base_scores':scores});assert replay==row
    save(OUT/'structure-verification-before-resume.json',{'all20_frozen_rankings_replayed':True,'all_counts_equal':True,'no_performance_score_computed':True,'paid_calls':0});print('STRUCTURE_PASS20_NO_SCORE_CALCULATION',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','run','collect','structure']);a=p.parse_args();{'prepare':prepare,'run':run,'collect':collect,'structure':structure}[a.action]()
