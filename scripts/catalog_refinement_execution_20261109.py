"""Complete failed-only fit delivery after Claude HTTP400; no valid prediction is replaced."""
import argparse
import json

from scripts import catalog_refinement_service_fallback_20261109 as service
from scripts import catalog_refinement_20261109 as run
from scripts.task_alignment_20261109 import sha

run.MODELS['gemini']='gemini-3-flash-preview'
run.RATES['gemini']=(.5,3)
base_body=service.body


def body(provider,system,payload,cap=6144,schema=None):
 result=base_body(provider,system,payload,cap,schema)
 if provider=='openai' and schema:
  result['text']={'format':{'type':'json_schema','name':'case_fit','strict':True,'schema':schema}}
 return result


run.body=body


def amendment():
 service.guarded();assert not (run.OUT/'predictions.json').exists()
 failures=run.load('fit-failures.json');assert len(failures)==29
 run.save(run.OUT/'execution-amendment.json',{'state':'FAILED_DELIVERY_ONLY_RECOVERY_BEFORE_RANKING_OR_LABEL_EVALUATION',
  'failure_count':29,'valid_claude_fit_responses_preserved':43,'recover_fit_with':'gpt-5.4/high',
  'fresh_judges':['gpt-5.4/high','gemini-3-flash-preview/high'],'author':'claude-sonnet-5-5 after GeminiPro429',
  'reason':'Claude HTTP400 on last29 fit requests; no valid result replacement or performance tuning',
  'fit_before_recovery_sha256':sha(run.OUT/'fits.json'),'script_sha256':sha(__file__),
  'service_amendment_sha256':sha(run.OUT/'service-amendment.json'),'budget_usd':15,
  'case_fit_criteria_thresholds_or_ranking_changed':False,
  'limits':'Mixed fit providers; fresh OpenAI fits share provider with one judge; GeminiFlash is lower tier than unavailable GeminiPro.'})


def guarded():
 service.guarded();a=run.load('execution-amendment.json');assert a['script_sha256']==sha(__file__)


def recover():
 guarded();ids=sorted(run.inputs()[2]['cases']);reg=run.inputs()[3];qs=run.questions();failed=run.load('fit-failures.json')
 jobs=[('fit_recovery_'+q,'openai',body('openai',run.FIT_SYSTEM,run.fit_payload(qs[q]['text'],ids,reg),schema=run.fit_schema())) for q in failed]
 run.batch('fit-recovery',jobs)
 before=run.load('fits.json');assert sha(run.OUT/'fits.json')==run.load('execution-amendment.json')['fit_before_recovery_sha256']
 run.save(run.OUT/'fits-before-recovery.json',before)
 combined=dict(before);left={};provider={q:'claude' for q in before}
 for q in failed:
  try:
   combined[q]=run.parse_fit(run.load('calls/fit_recovery_'+q+'-data.json'),qs[q]['text'],ids,reg);provider[q]='openai'
  except Exception as e:left[q]=type(e).__name__
 assert all(combined[q]==v for q,v in before.items())
 (run.OUT/'fits.json').write_text(json.dumps(combined,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 run.save(run.OUT/'fit-recovery-summary.json',{'provider_by_query':provider,'still_failed':left,'original_valid_preserved':True,
  'before_sha256':sha(run.OUT/'fits-before-recovery.json'),'after_sha256':sha(run.OUT/'fits.json')})
 print('FITS_AFTER_RECOVERY',len(combined),'STILL_FAILED',left,flush=True)


def judge():
 guarded();assert (run.OUT/'predictions.json').exists()
 ids=sorted(run.inputs()[2]['cases']);reg=run.inputs()[3];jobs=[]
 for provider in ('openai','gemini'):
  for q,r in run.load('fresh-questions.json').items():
   jobs.append(('judge_'+provider+'_'+q,provider,body(provider,run.JUDGE_SYSTEM,run.fit_payload(r['text'],run.judge_order(q,ids),reg))))
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
  'actual_providers':{'openai':'gpt-5.4/high','gemini':'gemini-3-flash-preview/high'}})
 print('FRESH_JUDGES',{p:len(g) for p,g in labels.items()},'FAILURES',failed,flush=True)


def evaluation_compute(raw,old_labels,fresh):
 pred=raw['questions'];ids=raw['case_ids']
 dev={n:run.assess({q:r for q,r in pred.items() if q in g},g,ids) for n,g in old_labels.items()}
 new={p:run.assess({q:pred[q] for q in g},g,ids) for p,g in fresh.items()}
 fully=sorted(set.intersection(*(set(g) for g in fresh.values())))
 positive=[q for q in fully if all(any(v>=2 for v in fresh[p][q].values()) for p in fresh)]
 common={p:run.assess({q:pred[q] for q in positive},{q:g[q] for q in positive},ids) for p,g in fresh.items()}
 sensitivity={}
 for mode,fn in [('intersection',all),('union',any)]:
  g={q:{c:2 if fn(fresh[p][q][c]>=2 for p in fresh) else 0 for c in ids} for q in fully}
  sensitivity[mode]=run.assess({q:pred[q] for q in g},g,ids)
 differences=[{'query_id':q,'case_id':c,'openai':fresh['openai'][q][c],'gemini':fresh['gemini'][q][c]}
  for q in fully for c in ids if (fresh['openai'][q][c]>=2)!=(fresh['gemini'][q][c]>=2)]
 return {'state':'ALL_FOUR_AUTHORIZED_STEPS_COMPLETE','development60':dev,'fresh12':new,'fresh_common_positive':common,
  'fresh_common_positive_queries':positive,'fresh_binary_sensitivity':sensitivity,'fresh_binary_disagreements':differences,
  'fresh_complete_questions_both':fully,
  'G_equals_H_rankings':sum(r['systems']['G_WidenedFit']['ranking']==r['systems']['H_GlobalFit']['ranking'] for r in pred.values()),
  'G_equals_H_sets':sum(set(r['systems']['G_WidenedFit']['ranking'])==set(r['systems']['H_GlobalFit']['ranking']) for r in pred.values()),
  'questions':len(pred),'human_gold':False,'independent_final_test':False,'new_training':False,'test15_read':False,
  'technical_provider_amendments':True,'fit_providers':run.load('fit-recovery-summary.json')['provider_by_query'],
  'limits':['New questions fixed after method freeze; AI-authored and view-scope-targeted, not real-work submissions',
   '43 Claude fits+29 failed-only OpenAI recoveries; mixed-provider effect, not a single-model causal claim',
   'OpenAI fits and one judge share provider; GeminiFlash is a separate lower-tier rater, no human Gold',
   'GeminiPro author429 and Claude29fit HTTP400 retained; criteria and valid outputs unchanged',
   'Only17 cases; no full112 expansion; bootstrap is small-sample descriptive, not final independent-test proof']}


run.evaluation_compute=evaluation_compute


def verify():
 guarded()
 # Base verifier parses each saved fit via its initial filename. Map failed-only
 # deliveries to their recovery file; no received valid source is replaced.
 original_load=run.load
 recovered=set(original_load('fit-failures.json'))
 def routed(name):
  if name.startswith('calls/fit_') and name.endswith('-data.json'):
   q=name[len('calls/fit_'):-len('-data.json')]
   if q in recovered:name='calls/fit_recovery_'+q+'-data.json'
  return original_load(name)
 run.load=routed
 run.verify()
 report=original_load('verification.json');report['actual_fit_provider_counts']={'claude':43,'openai':29}
 report['technical_provider_changes_preserved']=True
 (run.OUT/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['amendment','recover','infer','judge','evaluate','verify'])
 phase=parser.parse_args().phase
 if phase=='amendment':amendment()
 else:
  guarded()
  if phase in ('recover','judge','verify'):globals()[phase]()
  else:getattr(run,phase)()
