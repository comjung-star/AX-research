"""Execution-only queue handoff: same frozen prompts/models/caps, no duplicate calls."""
import json
import random
from datetime import datetime,timezone
from concurrent.futures import ThreadPoolExecutor
from scripts.panels_full112_experiment_20261109 import guard,sources,JUDGE_SYSTEM,JUDGE_CAP,JUDGE_BATCH,judge_schema
from scripts.panels_full112_api_20261109 import OUT,save,read,call,MODELS,body

def run():
    guard();assert not (OUT/'stage6/metrics.json').exists()
    cat,reg=sources();ranks=read(OUT/'stage6/rankings.json');jobs=[]
    # Atomic exclusive files reserve only calls not already started by original queue.
    for q,row in ranks.items():
        ids=sorted(reg);random.Random(20261109+int(q[-3:])).shuffle(ids)
        for i in range(0,112,JUDGE_BATCH):
            ident=f'judge_{q}_b{i//JUDGE_BATCH:02d}';path=OUT/f'api/openai_{ident}.json'
            claim={'id':'openai_'+ident,'provider':'openai','model':MODELS['openai'],'status':'DELEGATED_NOT_SENT',
                   'delivery_unknown':False,'reserved_usd':0,'execution_receipt':'stage6/parallel-receipts/openai_'+ident+'_worker.json'}
            try:
                with path.open('x',encoding='utf-8') as f:json.dump(claim,f)
            except FileExistsError:continue
            subset=ids[i:i+JUDGE_BATCH]
            payload={'question':row['question'],'perspective_definitions':[{k:c[k] for k in ('id','definition','exclude_if')} for c in cat['cards']],
                     'cases':[{'position':j,**{f:reg[c][f] for f in ('problem','task','context')}} for j,c in enumerate(subset)]}
            request={'system':JUDGE_SYSTEM,'payload':payload,'schema':judge_schema(),'body':body('openai',JUDGE_SYSTEM,payload,judge_schema(),JUDGE_CAP)}
            save(path.with_name(path.stem+'.request.json'),request);jobs.append((ident,payload,path))
    amendment={'at':datetime.now(timezone.utc).isoformat(),'reason':'Execution latency; independent Gemini check is quota-blocked. Complete remaining feasible OpenAI evaluation without changing semantic method.',
       'original_concurrency':2,'worker_concurrency':4,'temporary_peak_concurrency':6,'before_any_metrics_computed':True,
       'unchanged':['model','reasoning effort','system prompt','question','source cases and ordering','schema','token cap','grades','rankings','metrics'],
       'claimed_original_ids':[ident for ident,_,_ in jobs],'duplicate_prevention':'exclusive original-path claim before worker request; original queue sees claimed path and never sends it',
       'receipt_policy':'worker response preserved outside ledger; original path carries the one billed attempt for budget accounting'}
    save(OUT/'stage6/execution-concurrency-amendment.json',amendment)
    def work(job):
        ident,payload,path=job
        response=call('openai',ident+'_worker',JUDGE_SYSTEM,payload,judge_schema(),JUDGE_CAP)
        alias=OUT/f'api/openai_{ident}_worker.json';dest=OUT/f'stage6/parallel-receipts/{alias.name}'
        dest.parent.mkdir(parents=True,exist_ok=True)
        save(path,{**response,'id':'openai_'+ident,'transport_record_id':response['id'],'execution_only_queue_handoff':True})
        alias.replace(dest)
    print('CLAIMED_FROZEN_REQUESTS',len(jobs),flush=True)
    with ThreadPoolExecutor(max_workers=4) as executor:
        for result in executor.map(work,jobs):pass
    print('PARALLEL_EXECUTION_FINISHED',flush=True)

if __name__=='__main__':run()
