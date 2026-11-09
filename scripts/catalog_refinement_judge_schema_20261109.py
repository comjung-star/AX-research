"""Technical output-schema correction for rejected OpenAI judge requests only."""
import json
import os
from concurrent.futures import ThreadPoolExecutor,as_completed

from scripts import catalog_refinement_complete_20261109 as complete
from scripts import catalog_refinement_20261109 as run
from scripts.task_alignment_20261109 import sha


def request(q):
    ids=sorted(run.inputs()[2]['cases']);r=run.load('fresh-questions.json')[q]
    b=complete.medium_body('openai',run.JUDGE_SYSTEM,run.fit_payload(r['text'],run.judge_order(q,ids),run.inputs()[3]),4096)
    row={'type':'object','properties':{'position':{'type':'integer'},'grade':{'type':'integer','enum':[0,1,2,3]},
      'task_quote':{'type':'string'},'reason':{'type':'string'}},'required':['position','grade','task_quote','reason'],'additionalProperties':False}
    b['text']={'format':{'type':'json_schema','name':'blind_case_grades','strict':True,
      'schema':{'type':'object','properties':{'rows':{'type':'array','items':row}},'required':['rows'],'additionalProperties':False}}}
    return b


def one(q,b):
    from openai import OpenAI,APIStatusError
    name='judge_schema_openai_'+q;path=run.OUT/'calls';reserve=run.reservation('openai',b)
    run.save(path/(name+'-attempt.json'),{'provider':'openai','reserved_usd':reserve,'started_utc':run.now()})
    run.save(path/(name+'-request.json'),b)
    try:
      raw=OpenAI(api_key=os.environ['OPENAI_API_KEY'],max_retries=0,timeout=180).responses.create(**b).model_dump(mode='json')
    except APIStatusError as e:
      detail=e.body
      text=json.dumps(detail,ensure_ascii=False)
      for key in ('OPENAI_API_KEY','ANTHROPIC_API_KEY','GEMINI_API_KEY'):
        if os.environ.get(key):text=text.replace(os.environ[key],'[REDACTED]')
      run.save(path/(name+'-failure.json'),{'state':'HTTP_FAILURE_NO_RETRY','status':e.status_code,'detail':text[:1500]})
      return {'name':name,'state':'HTTP_FAILURE','status':e.status_code}
    except Exception as e:
      run.save(path/(name+'-failure.json'),{'state':'UNKNOWN_DELIVERY_NO_RETRY','error_type':type(e).__name__})
      return {'name':name,'state':'UNKNOWN_DELIVERY'}
    run.save(path/(name+'-response.json'),raw);u=raw.get('usage',{});cost=(u.get('input_tokens',0)*2.5+u.get('output_tokens',0)*15)/1e6
    run.save(path/(name+'-receipt.json'),{'provider':'openai','model':raw.get('model'),'usage':u,'estimated_usd':cost,'reserved_usd':reserve})
    try:
      data=run.response_data('openai',raw);run.save(path/(name+'-data.json'),data)
      return {'name':name,'state':'JSON_RECEIVED','estimated_usd':cost}
    except Exception as e:
      run.save(path/(name+'-parse-failure.json'),{'state':'OUTPUT_RETAINED','error_type':type(e).__name__})
      return {'name':name,'state':'OUTPUT_PARSE_FAILURE','estimated_usd':cost}


if __name__=='__main__':
    complete.guarded();fresh=run.load('fresh-questions.json');bodies={q:request(q) for q in fresh}
    attempts=list((run.OUT/'calls').glob('*-attempt.json'))
    spent=sum(json.loads(p.read_text(encoding='utf-8'))['reserved_usd'] for p in attempts)
    judge_reserve=run.load('judge-final-start.json')['reserved_usd']
    judge_started=sum(json.loads(p.read_text(encoding='utf-8'))['reserved_usd'] for p in attempts if p.name.startswith('judge_'))
    pending=max(0,judge_reserve-judge_started)
    extra=sum(run.reservation('openai',b) for b in bodies.values())
    assert spent+pending+extra<=15,(spent,pending,extra)
    run.save(run.OUT/'judge-schema-amendment.json',{'state':'OUTPUT_FORMAT_ONLY_FOR_REJECTED_OPENAI_JUDGE_CALLS',
      'script_sha256':sha(__file__),'previous_successful_OpenAI_grades_replaced':0,'max_output_tokens':4096,'reasoning':'medium',
      'grading_rubric_or_case_order_changed':False,'reserved_upper_usd':extra,'total_including_pending_reserved_usd':spent+pending+extra})
    qs=list(fresh);results=[]
    first=one(qs[0],bodies[qs[0]]);results.append(first);print(json.dumps(first),flush=True)
    # A fixed compatibility failure is not chased across further alternatives.
    if first['state']=='JSON_RECEIVED':
      with ThreadPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(one,q,bodies[q]) for q in qs[1:]]
        for f in as_completed(futures):r=f.result();results.append(r);print(json.dumps(r),flush=True)
    run.save(run.OUT/'judge-schema-run.json',{'results':results,'no_performance_based_regeneration':True})
