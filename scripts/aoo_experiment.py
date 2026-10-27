"""Versioned AOO independent judging. No old judgments or Test inputs reused."""
import argparse
import hashlib
import json
import math
import os
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor,as_completed
from decimal import Decimal
from pathlib import Path
from scripts import stage1_cost_pilot as api

ROOT=Path(__file__).resolve().parents[1]
ARCHIVE=ROOT/'docs/stage123-action-object-output-2026-10-27'
OUT=ARCHIVE/'schema-safe-v10'
DATA=ROOT/'data/v2_5/research'
CONFIG_PATH=ROOT/'configs/aoo_task_rubric_20261027.json'
CFG=api.read_json(CONFIG_PATH)
LOCK=threading.Lock();STOP=threading.Event()
RATE={p:threading.Lock() for p in CFG['models']};LAST={p:0. for p in CFG['models']}
SYSTEM='''Judge only this ONE query and named target using the supplied Problem/Task/Context, never unseen implementation, technology or outcomes. WHOLE_QUERY means any explicitly defined core task can give 3; ASPECT means ONLY the selected task, never borrow another task from the whole query. Compare ACTION, FUNCTIONAL OBJECT and OUTPUT. Other sectors, recipient roles and channels can transfer the same operation: answering employee, partner, legal, banking or shopping questions can match inquiry answering. Do not demand an unstated demonstrated benefit for a direct functional match. Conversely, generic manual work, staff capacity, cost/time reduction or industry overlap cannot turn a different task into a direct match. Summarizing, extracting, verifying and identifying next actions are distinct operations; defect detection differs from cause diagnosis.
Grades: 0 no operational link (manual work/industry alone is zero); 1 broad task/object resemblance without a concrete supporting operation; 2 an upstream/downstream supporting operation, or only some A/O/O elements match; 3 direct ACTION plus functionally equivalent OBJECT plus OUTPUT for at least one target task; 4 additionally most target tasks and explicit problem/context requirements are supported in the input. Never invent workload reduction, response quality, complexity-handling gains, AI technology, security or regulation. Static contract/website/review summaries are not business-conversation summaries. A specific inquiry type still counts as inquiry answering; cross-industry usefulness is allowed. Read ALL the raw fields.
Return the exact JSON structure, query and target IDs. Each case has its own schema/evidence choices; never transfer a score or evidence to another case. Set action_match/object_match/output_match to MATCH, SUPPORT, DIFFERENT or UNSTATED. Score>=3 requires all three MATCH and relation DIRECT. matched_task must name a selected task when score>=3, else NONE is permitted. Score4 requires problem_context SUPPORTED, not a hypothesized benefit. Evidence must be one supplied exact source excerpt. reason must be exactly three short phrases separated by ' / ': action comparison / functional object comparison / output comparison. At most 35 whitespace-delimited English words total. Explain only these comparisons, not effects, technologies or speculative purposes. These are AI judgments, not human Gold.'''
SYSTEM=SYSTEM.replace('Set action_match/object_match/output_match to MATCH, SUPPORT, DIFFERENT or UNSTATED. Score>=3 requires all three MATCH and relation DIRECT. matched_task must name a selected task when score>=3, else NONE is permitted.', 'Set match_mask to three digits in ACTION/OBJECT/OUTPUT order: 1 means a direct functional match, 0 means supporting/different/unstated. Score>=3 requires 111 and relation DIRECT. matched_tasks is a unique list of actually performed selected tasks, or [NONE] if none is direct.')
SYSTEM+=' A need or burden in the case Problem is NOT evidence that the case Task performs an action or produces its output. Judge actual actions/outputs from Task and explicit operational Context only; Problem supplies problem/context evidence, not missing capabilities. Grade4 must cover more than half the selected tasks (one of one, both of two, at least two of three), AND its named problem constraints, using stated evidence. One matching task in a two-task whole query gives at most3. Functional transfer across sectors/recipient roles is allowed; do not turn a missing workload/quality outcome into a requirement for grade3.'
ROW_FIELDS={'score','matched_tasks','relation','match_mask','problem_context','evidence','reason'}
PILOT={
 'V21D001':[['AXV2C_0016_01','AXV2P2_0048_01'],['AXV2H_0002_01','AXV2N_0130'],['AXV24_bc6444cc1b61','AXV2N_0117']],
 'V21D002':[['AXV2H_0002_01','AXV2N_0125'],['AXV2N_0139','AXV2P2_0069_01'],['AXV2C_0093_02','AXV2N_0118']],
 'V21D004':[['AXV2C_0006_02'],['AXV2P2_0012_01'],['AXV2N_0117','AXV2N_0114']],
 'V21D010':[['AXV2C_0093_01','AXV2C_0093_02','AXV2P2_0065_01'],['AXV2N_0117','AXV2H_0021_01','AXV2C_0094_02'],['AXV2N_0139','AXV2N_0107']]
}
ASPECT_PILOT={
 'V21D001:ANSWER':['AXV2P2_0048_01','AXV2H_0002_01','AXV2C_0093_01'],
 'V21D002:FOLLOWUP':['AXV2N_0125','AXV2H_0002_01','AXV2C_0093_02'],
 'V21D004:VERIFY':['AXV2C_0006_02','AXV2P2_0012_01','AXV2N_0118'],
 'V21D010:CAUSE':['AXV2P2_0065_01','AXV2N_0117','AXV2C_0093_02']
}

def digest(value):return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def save(path,value):
    text=json.dumps(value,ensure_ascii=False,indent=2)+'\n'
    if any(k and k in text for k in (api.read_key(s['key_env']) for s in api.CONFIG['models'].values())):raise ValueError('Secret rejected')
    path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_name(path.name+'.tmp')
    temporary.write_text(text,encoding='utf-8',newline='\n');os.replace(temporary,path)
def inputs():
    return ({r['case_id']:r for r in api.read_csv(DATA/'dev_problem_views.csv')},
            {r['query_id']:r['query'] for r in api.read_json(DATA/'dev_queries.json')['queries']})
def excerpts(c):return list(dict.fromkeys(c[f][:180] for f in ('task','problem','context') if c[f]))
def schema(job):
    if job['phase']=='views':
        props={'id':{'type':'string'},'title':{'type':'string'},'description':{'type':'string'},'keywords':{'type':'array','items':{'type':'string'}},'source_quote':{'type':'string'}}
        return {'type':'object','properties':{'perspectives':{'type':'array','minItems':1,'items':{'type':'object','properties':props,'required':list(props),'additionalProperties':False}}},'required':['perspectives'],'additionalProperties':False}
    rows={}
    for cid,item in job['items'].items():
        props={'score':{'type':'integer','enum':list(range(5))},'matched_tasks':{'type':'array','minItems':1,'items':{'type':'string','enum':list(job['tasks'])+['NONE']}},'relation':{'type':'string','enum':['DIRECT','SUPPORT','ADJACENT','NONE']},
               'match_mask':{'type':'string','enum':['000','001','010','011','100','101','110','111']},
               'problem_context':{'type':'string','enum':['SUPPORTED','NOT_FULLY_SUPPORTED']},'evidence':{'type':'string','enum':[item['task'][:180]]},
               'reason':{'type':'string'}}
        rows[cid]={'type':'object','properties':props,'required':list(props),'additionalProperties':False}
    props={'query_id':{'type':'string','enum':[job['query_id']]},'target_id':{'type':'string','enum':[job['target_id']]},'ratings':{'type':'object','properties':rows,'required':list(rows),'additionalProperties':False}}
    return {'type':'object','properties':props,'required':list(props),'additionalProperties':False}
def build_job(phase,index,qid,cids,cases,queries,aspect=None):
    tasks=CFG['queries'][qid]['tasks']
    if aspect:
        a=CFG['aspects'][aspect]
        assert a['source_quote'] in queries[qid]
        tasks={k:tasks[k] for k in a['task_ids']}
    target=aspect or 'WHOLE_QUERY'
    items={cid:{'question_text':queries[qid],**{f:cases[cid][f] for f in ('problem','task','context')}} for cid in cids}
    user=json.dumps({'scope':'ASPECT' if aspect else 'WHOLE_QUERY','query_id':qid,'target_id':target,'query':queries[qid],'target_tasks':tasks,'context_for_grade4':CFG['queries'][qid]['context_for_4'] if not aspect else 'The named aspect operation and its explicitly stated constraints must be supported; do not borrow other whole-query tasks.','aspect_source':CFG['aspects'][aspect] if aspect else None,'items':items},ensure_ascii=False,separators=(',',':'))+'\nReturn JSON.'
    job={'job_id':f'{phase}_{index:04d}','phase':phase,'query_id':qid,'target_id':target,'items':items,'tasks':tasks,'system':SYSTEM,'user':user,'output_cap':150*len(items)+192}
    job['schema']=schema(job);job['input_version']=digest(job)
    return job
def prepare():
    cases,queries=inputs();assert len(cases)==112 and len(queries)==10
    pilot=[];expect=[]
    for qid,bands in PILOT.items():
        ids=[c for band in bands for c in band];j=build_job('pilot',len(pilot),qid,ids,cases,queries);pilot.append(j)
        for b,cs in zip(('DIRECT','PARTIAL','UNRELATED'),bands):
            expect.extend({'query_id':qid,'target_id':'WHOLE_QUERY','case_id':c,'diagnostic_band':b} for c in cs)
    for aid,ids in ASPECT_PILOT.items():
        qid=aid.split(':')[0];pilot.append(build_job('pilot',len(pilot),qid,ids,cases,queries,aid))
        expect.extend({'query_id':qid,'target_id':aid,'case_id':c,'diagnostic_band':b} for b,c in zip(('DIRECT','PARTIAL','UNRELATED'),ids))
    full=[]
    for qid in sorted(queries):
        for offset in range(0,112,CFG['batch_size']):full.append(build_job('stage1',len(full),qid,sorted(cases)[offset:offset+CFG['batch_size']],cases,queries))
    views=[]
    for i,(qid,q) in enumerate(sorted(queries.items())):
        j={'job_id':f'views_{i:04d}','phase':'views','query_id':qid,'system':'Generate complementary problem perspectives, not solutions, from the business problem alone. Do not invent requirements, technologies or benefits. Return JSON only.',
           'user':'Business problem: '+q+'\nGenerate 2 to 5 distinct perspectives. Each has id, title, description, keywords, and an EXACT source_quote from the original problem. Do not use predefined categories. Return JSON.','query_text':q,'output_cap':1280}
        j['schema']=schema(j);j['input_version']=digest(j);views.append(j)
    plan={'version':CFG['version']+'.schema-safe-v10','base_commit':CFG['base_commit'],'config_sha256':hashlib.sha256(CONFIG_PATH.read_bytes()).hexdigest(),
          'input_hashes':{str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in (DATA/'dev_problem_views.csv',DATA/'dev_queries.json',DATA/'split_groups.csv',DATA/'dev_qrels_annotation.csv')},
          'pilot':pilot,'stage1':full,'views':views,'diagnostic_expectations_not_model_inputs':expect,'human_gold':False,'test_sealed':True}
    path=OUT/'plan.json'
    if path.exists() and api.read_json(path)!=plan:raise ValueError('Frozen new plan changed; use separate version')
    save(path,plan);return plan
def body(provider,job,counting=False,retry=False):
    user=job['user']+('\nFormatting correction: preserve all keys, exact source evidence, valid score/match consistency, and <=35 English words in the three-part reason. Return JSON.' if retry else '')
    model=CFG['models'][provider]
    if provider=='openai':
        b={'model':model,'instructions':job['system'],'input':user,'text':{'format':{'type':'json_schema','name':'aoo_judgments','strict':True,'schema':job['schema']}}}
        if not counting:b.update(max_output_tokens=job['output_cap'],store=False,reasoning={'effort':'none'},service_tier='default')
    elif provider=='claude':
        b={'model':model,'system':job['system'],'messages':[{'role':'user','content':user}],'output_config':{'format':{'type':'json_schema','schema':job['schema']}}}
        if not counting:b['max_tokens']=job['output_cap']
    else:
        b={'systemInstruction':{'parts':[{'text':job['system']}]},'contents':[{'role':'user','parts':[{'text':user}]}],'generationConfig':{'maxOutputTokens':job['output_cap'],'thinkingConfig':{'thinkingLevel':'minimal'},'responseMimeType':'application/json','responseJsonSchema':job['schema']}}
        if counting:b={'generateContentRequest':{'model':'models/'+model,**b}}
    return b
def count(provider,job,retry=False):
    path=OUT/'counts'/provider/(job['job_id']+('_retry' if retry else '')+'.json')
    if path.exists():return api.read_json(path)
    status,payload=api.transport(provider,body(provider,job,True,retry),True)
    result={**status,'provider':provider,'job_id':job['job_id'],'input_version':job['input_version'],'request_sha256':digest(body(provider,job,True,retry))}
    if status['ok']:
        n=payload.get('totalTokens') if provider=='gemini' else payload.get('input_tokens')
        result.update(input_tokens=n,ok=type(n)is int and n>0)
    save(path,result);return result
def spent(provider):
    total=Decimal(0)
    for p in [p for base in (ARCHIVE,OUT) for p in (base/'attempts'/provider).glob('*.json')]:
        a=api.read_json(p);total+=Decimal(a.get('usage',{}).get('usage_cost_usd',a['reserved_usd']))
    return total
def halted():return STOP.is_set() or (OUT/'halt.json').exists()
def validate(text,job):
    try:
        d=json.loads(text.strip().removeprefix('```json').removesuffix('```').strip())
        if job['phase']=='views':
            rows=d['perspectives'];assert 2<=len(rows)<=5 and len({r['id'] for r in rows})==len(rows)
            assert all(set(r)=={'id','title','description','keywords','source_quote'} and isinstance(r['keywords'],list) and isinstance(r['source_quote'],str) and len(r['source_quote'])>=4 and r['source_quote'] in job['query_text'] and r['title'] and r['description'] for r in rows)
            return {'valid':True,'data':d,'errors':[]}
        assert set(d)=={'query_id','target_id','ratings'} and d['query_id']==job['query_id'] and d['target_id']==job['target_id']
        assert set(d['ratings'])==set(job['items'])
        for cid,r in d['ratings'].items():
            assert set(r)==ROW_FIELDS and type(r['score'])is int and r['score'] in range(5)
            assert r['evidence']==job['items'][cid]['task'][:180]
            assert 0<len(r['reason'].split())<=35 and re.fullmatch(r'[^/]+ / [^/]+ / [^/]+',r['reason'])
            assert r['matched_tasks'] and len(set(r['matched_tasks']))==len(r['matched_tasks']) and set(r['matched_tasks'])<=set(job['tasks'])|{'NONE'}
            assert r['match_mask'] in {'000','001','010','011','100','101','110','111'}
            if r['score']>=3:assert 'NONE' not in r['matched_tasks'] and r['relation']=='DIRECT' and r['match_mask']=='111'
            if r['score']==4:assert r['problem_context']=='SUPPORTED' and len(r['matched_tasks'])>len(job['tasks'])/2
            # Reasons describe operational correspondence, never claimed benefit.
            assert not re.search(r'\b(reduces?|improves?|frees?|boosts?|saves?|enables?)\b',r['reason'],re.I)
        return {'valid':True,'data':d,'errors':[]}
    except (ValueError,TypeError,KeyError,AssertionError,AttributeError):return {'valid':False,'data':None,'errors':['SCHEMA_TARGET_EVIDENCE_OR_OPERATIONAL_REASON_CONSTRAINT']}
def run_job(provider,job):
    target=OUT/'results'/provider/(job['job_id']+'.json')
    if target.exists():return api.read_json(target)
    for attempt in (1,2):
        if halted():return None
        path=OUT/'attempts'/provider/f"{job['job_id']}_a{attempt}.json"
        if path.exists():
            previous=api.read_json(path)
            if previous.get('state')=='RECEIVED' and previous.get('usage'):
                v=validate(previous['response_text'],job)
                if v['valid']:save(target,{**previous,'validation':v,'reused_known_response':True});return api.read_json(target)
                continue
            STOP.set();return None
        c=count(provider,job,attempt==2)
        if not c.get('ok'):STOP.set();return None
        amount=api.token_cost(provider,math.ceil(c['input_tokens']*1.15)+128,job['output_cap'])
        with LOCK:
            cap=Decimal(CFG['claude_pilot_cap_usd'] if job['phase']=='pilot' else CFG['claude_new_work_cap_usd']) if provider=='claude' else Decimal('5')
            if spent(provider)+amount>cap:STOP.set();return None
            save(path,{'state':'RESERVED','provider':provider,'job_id':job['job_id'],'input_version':job['input_version'],'reserved_usd':api.money(amount)})
        with RATE[provider]:
            time.sleep(max(0,3-(time.monotonic()-LAST[provider])));LAST[provider]=time.monotonic()
        if halted():
            save(path,{'state':'CANCELLED_BEFORE_DISPATCH','provider':provider,'job_id':job['job_id'],'reserved_usd':'0.00000000'});return None
        status,payload=api.transport(provider,body(provider,job,False,attempt==2),False)
        result={**status,'state':'RECEIVED' if status['ok'] else 'UNCONFIRMED_FAILURE','provider':provider,'job_id':job['job_id'],'input_version':job['input_version'],'request_model':CFG['models'][provider],'request_sha256':digest(body(provider,job,False,attempt==2)),'reserved_usd':api.money(amount),'counted_input_tokens':c['input_tokens'],'attempt':attempt,'human_gold':False}
        if payload is not None:
            result.update(usage=api.extract_usage(provider,payload),response_text=api.extract_text(provider,payload),response_model=payload.get('model',payload.get('modelVersion')),response_id=payload.get('id',payload.get('responseId')))
            result['validation']=validate(result['response_text'],job)
            if not api.model_matches(provider,result['response_model']):result['validation']={'valid':False,'errors':['WRONG_MODEL'],'data':None};STOP.set()
        save(path,result)
        valid=result.get('validation',{}).get('valid',False)
        print(json.dumps({'provider':provider,'job':job['job_id'],'valid':valid,'cost':result.get('usage',{}).get('usage_cost_usd'),'errors':result.get('validation',{}).get('errors',[])}),flush=True)
        if valid:save(target,result);return result
        if not status['ok']:STOP.set();return result
    STOP.set();return result
def budget(plan):
    costs={p:{} for p in CFG['models']};failed=[]
    jobs=[j for phase in ('pilot','stage1','views') for j in plan[phase]]
    with ThreadPoolExecutor(max_workers=6) as pool:
        pending={pool.submit(count,p,j):(p,j) for p in CFG['models'] for j in jobs}
        for f in as_completed(pending):
            p,j=pending[f];r=f.result()
            if not r.get('ok'):failed.append(r);continue
            c=costs[p].setdefault(j['phase'],{'input_tokens':0,'output_cap_tokens':0,'base_upper_usd':Decimal(0),'requests':0})
            c['input_tokens']+=r['input_tokens'];c['output_cap_tokens']+=j['output_cap'];c['requests']+=1
            c['base_upper_usd']+=api.token_cost(p,math.ceil(r['input_tokens']*1.15)+128,j['output_cap'])
    for phases in costs.values():
        for c in phases.values():c['base_upper_usd']=api.money(c['base_upper_usd'])
    cl=costs['claude'];need=spent('claude')+Decimal(cl.get('pilot',{}).get('base_upper_usd','0'))*2+sum((Decimal(cl.get(p,{}).get('base_upper_usd','0')) for p in ('stage1','views')),Decimal(0))*Decimal('1.25')
    r={'providers':costs,'failed_counts':failed,'new_work_claude_upper_with_retry_usd':api.money(need),'prior_actual_plus_reserved_usd':CFG['claude_prior_actual_or_reserved_usd'],'safety_buffer_usd':'0.50','fits':not failed and need<=Decimal(CFG['claude_new_work_cap_usd']),'account_balance_queried':False}
    save(OUT/'budget.json',r);print(json.dumps(r,ensure_ascii=False),flush=True);return r
def execute(plan,phase):
    if halted():raise ValueError('Active new-run hold; no API dispatch')
    b=api.read_json(OUT/'budget.json')
    if not b['fits']:raise ValueError('Budget/count gate failed')
    if phase!='pilot':
        gate=api.read_json(OUT/'pilot_gate.json')
        if not gate['passed'] or not gate.get('manual_reason_review_complete'):raise ValueError('Pilot not passed and source-review approved')
    if phase=='views' and not (OUT/'stage2_results.json').exists():raise ValueError('Stage2 required before dynamic generation')
    jobs=plan[phase]
    def lane(p,js):
        for job in js:
            if halted():break
            run_job(p,job)
    with ThreadPoolExecutor(max_workers=6) as pool:
        fs=[pool.submit(lane,p,jobs[i::2]) for p in CFG['models'] for i in (0,1)]
        for f in as_completed(fs):f.result()
    if STOP.is_set():
        save(OUT/'halt.json',{'active':True,'reason':'API_OR_OUTPUT_VALIDATION_OR_BUDGET_FAILURE','paid_retry_of_unknown_request':False,'stage4_sealed':True})
    return not STOP.is_set()
def pilot_report(plan):
    rows=[];issues=[];direct={p:0 for p in CFG['models']};direct_received={p:0 for p in CFG['models']}
    for expected in plan['diagnostic_expectations_not_model_inputs']:
        q,t,c=expected['query_id'],expected['target_id'],expected['case_id'];entry={**expected,'scores':{},'reasons':{}}
        for p in CFG['models']:
            j=next(j for j in plan['pilot'] if j['query_id']==q and j['target_id']==t and c in j['items'])
            f=OUT/'results'/p/(j['job_id']+'.json')
            if not f.exists():issues.append({'provider':p,'case_id':c,'kind':'MISSING'});continue
            r=api.read_json(f)['validation']['data']['ratings'][c];s=r['score'];entry['scores'][p]=s;entry['reasons'][p]=r['reason']
            if expected['diagnostic_band']=='DIRECT':direct[p]+=s>=3;direct_received[p]+=1
            elif s>=3:issues.append({'provider':p,'query_id':q,'target_id':t,'case_id':c,'score':s,'kind':'UNSUPPORTED_POSITIVE_DIAGNOSTIC'})
            if c=='AXV2P2_0048_01' and t=='WHOLE_QUERY' and s==4:issues.append({'provider':p,'case_id':c,'kind':'UNSUPPORTED_GRADE4_CONTEXT'})
        rows.append(entry)
    for p,n in direct.items():
        if direct_received[p]==12 and n<10:issues.append({'provider':p,'direct_positive_count':n,'kind':'DIRECT_TRANSFER_GATE'})
    complete=[r for r in rows if len(r['scores'])==3]
    report={'passed':not issues,'manual_reason_review_complete':False,'diagnostic_not_human_gold':True,'expected_scores':108,'received_valid_scores_by_model':{p:sum(p in r['scores'] for r in rows) for p in CFG['models']},'direct_positive_counts':direct,'direct_received_denominators':direct_received,'direct_planned_denominator':12,'issues':issues,'rows':rows,'complete_pairs':len(complete),'grade_agreement_numerator':sum(len(set(r['scores'].values()))==1 for r in complete),'binary_agreement_numerator':sum(len({s>=3 for s in r['scores'].values()})==1 for r in complete)}
    save(OUT/'pilot_diagnostics.json',report);print(json.dumps({k:v for k,v in report.items() if k not in ('rows','issues')},ensure_ascii=False));return report
def main():
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['prepare','count','pilot','pilot-report','stage1','views']);a=p.parse_args()
    if a.phase not in ('prepare','pilot-report') and (OUT/'halt.json').exists():
        print('HOLD: new API calls blocked; inspect methodology_hold.json');return 2
    plan=prepare()
    if a.phase=='prepare':print('Prepared 36 pilot pairs; 1120 new Stage1 pairs; 10 query-only dynamic prompts; no generation calls.');return 0
    if a.phase=='count':return 0 if budget(plan)['fits'] else 2
    if a.phase=='pilot-report':return 0 if pilot_report(plan)['passed'] else 2
    return 0 if execute(plan,a.phase) else 2
if __name__=='__main__':raise SystemExit(main())
