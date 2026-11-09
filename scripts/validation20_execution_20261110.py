"""Pre-metric technical recovery and execution-only parallelism; semantic method unchanged."""
import argparse,json,shutil
from datetime import datetime,timezone
from scripts.perspective_omission_validation20_20261110 import OUT,read,save,guard,api,trial,sha

def recover_selector():
    guard();assert not (OUT/'rankings.json').exists() and not (OUT/'metrics.json').exists()
    path=OUT/'fresh-selections.json';s=read(path);snapshot=OUT/'fresh-selections-before-technical-recovery.json'
    if not snapshot.exists():shutil.copyfile(path,snapshot)
    cat,_,_=trial.sources();log=[]
    for q,selection in s.items():
        if 'failed' not in selection:continue
        request=read(OUT/f'api/openai_fresh_{q}.request.json');ident='fresh_'+q+'_retry1'
        response=api.call('openai',ident,request['system'],request['payload'],request['schema'],request['body']['max_output_tokens'])
        assert read(OUT/f'api/openai_{ident}.request.json')==request
        try:
            assert response['status']=='VALID_JSON';fixed=trial.normalize_review(selection['question'],response['parsed'],cat);s[q]=fixed;valid=True;error=''
        except Exception as e:valid=False;error=str(e)
        log.append({'question':q,'initial_error':selection['failed'],'same_body':True,'one_retry_only':True,'valid_after_retry':valid,'error':error})
    save(path,s);save(OUT/'selector-technical-recovery.json',log);print('SELECTOR_RECOVERY',json.dumps(log),flush=True)

def judge():
    guard();assert not (OUT/'metrics.json').exists()
    # Parallelism changes transport throughput only, before any new judgment is read.
    amendment={'at':datetime.now(timezone.utc).isoformat(),'kind':'Execution concurrency only','original_workers':4,'judge_workers':8,
        'reason':'20 questions require80 independent batches; reduce elapsed time while keeping requests fixed.',
        'before_first_judge_call':not any((OUT/'api').glob('openai_judge_*.json')),
        'unchanged':['model','effort','token cap','questions','case ordering','judge prompt','schema','grades','rankings','metrics'],'budget_usd':api.BUDGET}
    path=OUT/'judge-execution-amendment.json'
    if not path.exists():save(path,amendment)
    trial.WORKERS=8;trial.judge()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['recover-selector','judge']);a=p.parse_args()
    {'recover-selector':recover_selector,'judge':judge}[a.action]()
