"""Pre-outcome technical amendment after Gemini author HTTP429: Claude author, OpenAI judge."""
import argparse
import hashlib
import json
import os
import re
import urllib.error
import urllib.request
from difflib import SequenceMatcher

from scripts import catalog_refinement_20261109 as run
from scripts.task_alignment_20261109 import sha

original_body=run.body
original_call=run.one_call
original_response_data=run.response_data
run.MODELS['openai']='gpt-5.4'
run.RATES['openai']=(2.5,15)


def body(provider,system,payload,cap=6144,schema=None):
 if provider!='openai':return original_body(provider,system,payload,cap,schema)
 return {'model':'gpt-5.4','instructions':system,'input':json.dumps(payload,ensure_ascii=False),
  'reasoning':{'effort':'high'},'max_output_tokens':cap,'store':False,'text':{'format':{'type':'json_object'}}}


def reservation(provider,request):
 cap=request.get('max_tokens',request.get('max_output_tokens',request.get('generationConfig',{}).get('maxOutputTokens',0)))
 upper=len(json.dumps(request,ensure_ascii=False).encode())+8192
 return (upper*run.RATES[provider][0]+cap*run.RATES[provider][1])/1e6


def response_data(provider,response):
 if provider!='openai':return original_response_data(provider,response)
 if response.get('status')!='completed':raise ValueError('OpenAI response not completed')
 text=''.join(c.get('text','') for m in response.get('output',[]) if m.get('type')=='message' for c in m.get('content',[]) if c.get('type')=='output_text')
 return json.loads(text)


def one_call(name,provider,request):
 if provider!='openai':return original_call(name,provider,request)
 path=run.OUT/'calls';reserve=reservation(provider,request)
 run.save(path/(name+'-attempt.json'),{'provider':provider,'reserved_usd':reserve,'started_utc':run.now()})
 run.save(path/(name+'-request.json'),request)
 req=urllib.request.Request('https://api.openai.com/v1/responses',json.dumps(request).encode(),
  headers={'Authorization':'Bearer '+os.environ['OPENAI_API_KEY'],'Content-Type':'application/json'})
 try:
  with urllib.request.urlopen(req,timeout=180) as r:raw=json.load(r)
 except urllib.error.HTTPError as e:
  run.save(path/(name+'-failure.json'),{'state':'HTTP_FAILURE_NO_RETRY','status':e.code,'reservation_retained':True})
  return {'name':name,'state':'HTTP_FAILURE','status':e.code}
 except Exception:
  run.save(path/(name+'-failure.json'),{'state':'UNKNOWN_DELIVERY_NO_RETRY','reservation_retained':True})
  return {'name':name,'state':'UNKNOWN_DELIVERY'}
 run.save(path/(name+'-response.json'),raw)
 u=raw.get('usage',{});cost=(u.get('input_tokens',0)*2.5+u.get('output_tokens',0)*15)/1e6
 run.save(path/(name+'-receipt.json'),{'provider':provider,'model':raw.get('model'),'usage':u,'estimated_usd':cost,'reserved_usd':reserve,'finished_utc':run.now()})
 try:
  data=response_data(provider,raw);run.save(path/(name+'-data.json'),data)
  return {'name':name,'state':'JSON_RECEIVED','estimated_usd':cost}
 except Exception as e:
  run.save(path/(name+'-parse-failure.json'),{'state':'RESPONSE_RETAINED_NO_RETRY','error':type(e).__name__})
  return {'name':name,'state':'OUTPUT_PARSE_FAILURE','estimated_usd':cost}


run.body=body;run.reservation=reservation;run.response_data=response_data;run.one_call=one_call


def amendment():
 run.frozen()
 assert not (run.OUT/'fresh-questions.json').exists()
 failure=run.load('calls/author-failure.json');assert failure['status']==429
 run.save(run.OUT/'service-amendment.json',{'state':'TECHNICAL_PROVIDER_FALLBACK_BEFORE_NEW_QUESTIONS_OR_RANKINGS',
  'initial_author_failure':'Gemini3.1Pro HTTP429; not resent', 'author_provider':'claude-sonnet-5-5',
  'fresh_judges':['claude-sonnet-5-5','gpt-5.4'],'openai_reasoning_effort':'high',
  'max_total_attempts_including_failed_Gemini':110,'budget_usd':15,'method_case_fit_prompt_thresholds_changed':False,
  'initial_freeze_sha256':sha(run.OUT/'freeze.json'),'amendment_script_sha256':sha(__file__),
  'openai_rate_per_million':[2.5,15],'official_source':'https://developers.openai.com/api/docs/models/gpt-5.4',
  'limits':'Claude now shares author/selector/fit/one judge; OpenAI supplies a separate-provider blind judge. Not human Gold.'})


def guarded():
 run.frozen();a=run.load('service-amendment.json');assert a['amendment_script_sha256']==sha(__file__)


def author():
 guarded()
 request=body('claude',run.AUTHOR_SYSTEM,{'task':'Generate twelve questions now, without access to cases or prior questions.'})
 run.batch('author-fallback',[('author_fallback','claude',request)],1)
 rows=run.load('calls/author_fallback-data.json')['questions']
 assert [r['id'] for r in rows]==[f'NQ{i:03d}' for i in range(1,13)]
 assert len({r['question'] for r in rows})==12 and all(0<len(r['question'].encode())<=1200 for r in rows)
 norm=lambda s:re.sub(r'\W+','',s).lower()
 old=run.read(run.PREV+'/questions.json')
 novelty={r['id']:{'exact_old_duplicate':any(norm(r['question'])==norm(v['text']) for v in old.values()),
  'max_character_similarity_to_old':max(SequenceMatcher(None,norm(r['question']),norm(v['text'])).ratio() for v in old.values())} for r in rows}
 run.save(run.OUT/'fresh-questions.json',{r['id']:{'scope':'fresh12','text':r['question']} for r in rows})
 run.save(run.OUT/'fresh-novelty.json',{'checks':novelty,'questions_dropped_or_rewritten':0,'semantic_independence_certified':False,
  'author_provider':'Claude after Gemini429; generated after method and service amendment freeze'})
 print('NEW_12_QUESTIONS_FROZEN',flush=True)


def judge():
 guarded();assert (run.OUT/'predictions.json').exists()
 ids=sorted(run.inputs()[2]['cases']);reg=run.inputs()[3];jobs=[]
 for provider in ('claude','openai'):
  for q,r in run.load('fresh-questions.json').items():
   order=run.judge_order(q,ids)
   jobs.append(('judge_'+provider+'_'+q,provider,body(provider,run.JUDGE_SYSTEM,run.fit_payload(r['text'],order,reg))))
 run.batch('judge',jobs,2)
 labels={};failures={}
 for provider in ('claude','openai'):
  labels[provider]={}
  for q in run.load('fresh-questions.json'):
   try:
    rows=run.load('calls/judge_'+provider+'_'+q+'-data.json')['rows'];order=run.judge_order(q,ids)
    assert len(rows)==17 and {r['position'] for r in rows}==set(range(17))
    grades={}
    for row in rows:
     c=order[row['position']];assert row['grade'] in (0,1,2,3)
     if row['grade']>=2:assert row['task_quote'] and row['task_quote'] in reg[c]['task']
     grades[c]=row['grade']
    labels[provider][q]=grades
   except Exception as e:failures[provider+'_'+q]=type(e).__name__
 run.save(run.OUT/'fresh-labels.json',{'labels':labels,'failures':failures,'human_gold':False,'rankings_sent':False,'service_amendment':True})
 print('BLIND_JUDGES',{p:len(g) for p,g in labels.items()},'FAILURES',failures,flush=True)


def evaluation_compute(raw,old_labels,fresh):
 pred=raw['questions'];ids=raw['case_ids']
 dev={name:run.assess({q:r for q,r in pred.items() if q in g},g,ids) for name,g in old_labels.items()}
 new={p:run.assess({q:pred[q] for q in g},g,ids) for p,g in fresh.items()}
 fully=sorted(set.intersection(*(set(g) for g in fresh.values())))
 positive=[q for q in fully if all(any(v>=2 for v in fresh[p][q].values()) for p in fresh)]
 common={p:run.assess({q:pred[q] for q in positive},{q:g[q] for q in positive},ids) for p,g in fresh.items()}
 sensitivity={}
 for mode,fn in [('intersection',all),('union',any)]:
  g={q:{c:2 if fn(fresh[p][q][c]>=2 for p in fresh) else 0 for c in ids} for q in fully}
  sensitivity[mode]=run.assess({q:pred[q] for q in g},g,ids)
 disagreements=[{'query_id':q,'case_id':c,'claude':fresh['claude'][q][c],'openai':fresh['openai'][q][c]}
  for q in fully for c in ids if (fresh['claude'][q][c]>=2)!=(fresh['openai'][q][c]>=2)]
 return {'state':'ALL_FOUR_AUTHORIZED_STEPS_COMPLETE','development60':dev,'fresh12':new,'fresh_common_positive':common,
  'fresh_common_positive_queries':positive,'fresh_binary_sensitivity':sensitivity,'fresh_binary_disagreements':disagreements,
  'fresh_complete_questions_both':fully,'G_equals_H_rankings':sum(r['systems']['G_WidenedFit']['ranking']==r['systems']['H_GlobalFit']['ranking'] for r in pred.values()),
  'G_equals_H_sets':sum(set(r['systems']['G_WidenedFit']['ranking'])==set(r['systems']['H_GlobalFit']['ranking']) for r in pred.values()),
  'questions':len(pred),'human_gold':False,'independent_final_test':False,'new_training':False,'test15_read':False,
  'service_amendment':'Gemini author429 before outcomes; Claude author and Claude/OpenAI blind judges',
  'limits':['Fresh questions generated after method and provider-amendment freeze but AI-authored and view-scope-targeted',
   'Claude shares author/selector/fit/judge; OpenAI is a separate provider, neither is human Gold',
   'Only17 cases; no full112 expansion','Development and bootstrap estimates are not unbiased final-test claims']}


run.evaluation_compute=evaluation_compute


if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['amendment','author','select','fit','infer','judge','evaluate','verify'])
 phase=parser.parse_args().phase
 if phase=='amendment':amendment()
 else:
  guarded()
  if phase in ('author','judge'):globals()[phase]()
  else:getattr(run,phase)()
