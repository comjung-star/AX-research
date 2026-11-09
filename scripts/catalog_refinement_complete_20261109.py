"""Finish only unattempted deliveries; retain truncations and unknown deliveries as failures."""
import argparse
import json
import threading
import time

from scripts import catalog_refinement_execution_20261109 as execution
from scripts import catalog_refinement_20261109 as run
from scripts.task_alignment_20261109 import sha


def medium_body(provider,system,payload,cap=6144,schema=None):
    b=execution.body(provider,system,payload,cap,schema)
    if provider=='openai':b['reasoning']['effort']='medium'
    return b


def amendment():
    execution.guarded();assert not (run.OUT/'predictions.json').exists()
    run.save(run.OUT/'completion-amendment.json',{'state':'UNATTEMPTED_ONLY_CONTINUATION_AFTER_OUTPUT_TRUNCATION',
      'script_sha256':sha(__file__),'reason':'GPT5.4 high hit max_output_tokens; running worker stopped to avoid further truncated requests',
      'unattempted_setting':'GPT5.4 medium6144; same fit schema and substantive criteria',
      'already_attempted_questions_not_resent':True,'fresh_judge_openai_setting':'medium6144',
      'actual_judges':['gpt-5.4/medium','gemini-3-flash-preview/high'],
      'ranking_policy_or_fit_threshold_changed':False,'API_settings_changed_after_fresh_questions':True,
      'clean_single_model_preregistered_test':False,'budget_usd':15})


def guarded():
    execution.guarded();assert run.load('completion-amendment.json')['script_sha256']==sha(__file__)


def complete():
    guarded();failed=run.load('fit-failures.json');qs=run.questions();ids=sorted(run.inputs()[2]['cases']);reg=run.inputs()[3]
    before=run.load('fits.json');run.save(run.OUT/'fits-before-recovery.json',before)
    unattempted=[q for q in failed if not (run.OUT/'calls'/('fit_recovery_'+q+'-attempt.json')).exists()]
    run.batch('fit-unattempted', [('fit_continuation_'+q,'openai',medium_body('openai',run.FIT_SYSTEM,
      run.fit_payload(qs[q]['text'],ids,reg),schema=run.fit_schema())) for q in unattempted])
    combined=dict(before);providers={q:'claude/high' for q in before};sources={q:'calls/fit_'+q+'-data.json' for q in before};left={}
    for q in failed:
        source='calls/'+('fit_continuation_' if q in unattempted else 'fit_recovery_')+q+'-data.json'
        try:
            combined[q]=run.parse_fit(run.load(source),qs[q]['text'],ids,reg)
            providers[q]='openai/medium' if q in unattempted else 'openai/high';sources[q]=source
        except Exception as e:left[q]=type(e).__name__
    assert all(combined[q]==v for q,v in before.items())
    (run.OUT/'fits.json').write_text(json.dumps(combined,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    run.save(run.OUT/'fit-recovery-summary.json',{'provider_by_query':providers,'source_by_query':sources,'still_failed':left,
      'original_valid_preserved':True,'before_sha256':sha(run.OUT/'fits-before-recovery.json'),'after_sha256':sha(run.OUT/'fits.json')})
    print('FITS_VALID',len(combined),'RETAINED_TECHNICAL_FAILURES',left,flush=True)


def judge():
    guarded();assert (run.OUT/'predictions.json').exists()
    ids=sorted(run.inputs()[2]['cases']);reg=run.inputs()[3];jobs=[]
    for provider in ('openai','gemini'):
        for q,r in run.load('fresh-questions.json').items():
            jobs.append(('judge_'+provider+'_'+q,provider,medium_body(provider,run.JUDGE_SYSTEM,
              run.fit_payload(r['text'],run.judge_order(q,ids),reg))))
    original=run.one_call;lock=threading.Lock();next_start=[0.]
    def paced(name,p,b):
        if p=='gemini':
            with lock:
                delay=max(0,next_start[0]-time.monotonic())
                if delay:time.sleep(delay)
                next_start[0]=time.monotonic()+15
        return original(name,p,b)
    run.one_call=paced
    run.batch('judge-final',jobs,2)
    labels={};failed={}
    for provider in ('openai','gemini'):
        labels[provider]={}
        for q in run.load('fresh-questions.json'):
            try:
                rows=run.load('calls/judge_'+provider+'_'+q+'-data.json')['rows'];order=run.judge_order(q,ids)
                assert len(rows)==17 and {r['position'] for r in rows}==set(range(17))
                g={}
                for r in rows:
                    c=order[r['position']];assert r['grade'] in (0,1,2,3)
                    if r['grade']>=2:assert r['task_quote'] and r['task_quote'] in reg[c]['task']
                    g[c]=r['grade']
                labels[provider][q]=g
            except Exception as e:failed[provider+'_'+q]=type(e).__name__
    run.save(run.OUT/'fresh-labels.json',{'labels':labels,'failures':failed,'human_gold':False,'rankings_sent':False,
      'actual_providers':{'openai':'gpt-5.4/medium','gemini':'gemini-3-flash-preview/high'}})
    print('BLIND_LABELS',{p:len(v) for p,v in labels.items()},'FAILURES',failed,flush=True)


def verify():
    guarded();original=run.load;sources=original('fit-recovery-summary.json')['source_by_query']
    def routed(name):
        if name.startswith('calls/fit_') and name.endswith('-data.json'):
            q=name[len('calls/fit_'):-len('-data.json')]
            if q in sources:name=sources[q]
        return original(name)
    run.load=routed;run.verify()
    report=original('verification.json')
    report.update({'API_settings_changed_after_fresh_questions':True,'clean_single_model_preregistered_test':False,
      'ranking_policy_changed_after_results':False,'technical_failure_questions':list(original('fit-recovery-summary.json')['still_failed'])})
    (run.OUT/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['amendment','complete','infer','judge','evaluate','verify'])
    p=parser.parse_args().phase
    if p=='amendment':amendment()
    else:
        guarded()
        if p in ('complete','judge','verify'):globals()[p]()
        else:getattr(run,p)()
