"""Small JSON batches, append-only usage ledger and three-repeat views."""
import argparse
import hashlib
import json
import math
import threading
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor,as_completed
from decimal import Decimal
from pathlib import Path
from scripts import aoo_experiment as prior
from scripts.evidence_rules import CFG,parse_evidence,score

ROOT=prior.ROOT;OUT=ROOT/'docs/stage123-evidence-rules-2026-10-27';DATA=prior.DATA;api=prior.api
LOCK=threading.Lock();STOP=threading.Event();RATE={p:threading.Lock() for p in CFG['models']};LAST={p:0. for p in CFG['models']}
save=prior.save;digest=prior.digest
SYSTEM='''Extract evidence and functional relationships, NOT scores. Never output a score, performance claim, technology guess or benefit. Only this query and named target are in scope. WHOLE_QUERY allows its listed core tasks; an ASPECT allows only its selected task, not other whole-query tasks. Sectors, channels and recipient roles can differ if ACTION, functional OBJECT and OUTPUT really correspond.
List only operations ACTUALLY performed in the case Task or explicit operational Context. A needed operation mentioned in Problem is NOT a performed operation. A summary is not action-item identification; detecting a defect is not diagnosing its cause. Do not add those operations without their own Task/Context evidence. Quotes must be exact short substrings from Task or Context, never Problem. Distinct operations should have distinct minimal quotes. Inferring the linguistic output of a stated action (summarize -> summary; answer -> answer) is allowed; inferring a new capability or improved workload/quality is not.
Return JSON with exactly qid,target,items. Each item has exactly id,ops,links. An op is [family,action,object,output,exact_quote]; use <=10 English words in each atom and a short exact source quote. Family is from the supplied family list. ANSWER includes resolving requests and customer troubleshooting. ACTION_ITEMS means explicitly identifying next steps/follow-ups, not summarizing or sending an existing message. DIAGNOSE means cause analysis, DETECT means finding presence. Quote the actual operation; do not copy a need in Problem. OTHER may describe an unlisted operation; do not force it into a convenient category.
A link is [target_task_id,zero_based_op_index,mask,relation,why]. mask has THREE letters in ACTION/OBJECT/OUTPUT order: E=functionally equivalent, S=concrete supporting, D=different/unstated. relation is DIRECT, SUPPORT or BROAD. DIRECT requires EEE, a compatible operation family and a real functional explanation. SUPPORT identifies a real upstream/downstream or partial operation, not generic time savings. BROAD is a wider operational resemblance. Omit links with no operational relevance: busy people or manual work alone is not a link. why uses <=18 English words, comparing operations/objects/outputs only, no invented gains. No operations may be borrowed from a different case. Return every id once, including unrelated cases. Do not add Markdown.'''
TEMPLATE={'qid':'copy','target':'copy','items':[{'id':'copy','ops':[['FAMILY','actual action','functional object','produced output','exact Task/Context substring']],'links':[['target task',0,'EEE','DIRECT','explain functional action object output correspondence']]}]}
OLD_PLAN=ROOT/'docs/stage123-action-object-output-2026-10-27/schema-safe-v10/plan.json'

def cases_queries():return prior.inputs()
def make_job(phase,index,qid,cids,cases,queries,target='WHOLE_QUERY'):
    tasks=prior.CFG['queries'][qid]['tasks']
    if target!='WHOLE_QUERY':tasks={k:tasks[k] for k in prior.CFG['aspects'][target]['task_ids']}
    requirements={k:{'function':v,'compatible_families':CFG['target_families'][k]} for k,v in tasks.items()}
    items={cid:{'question':queries[qid],**{f:cases[cid][f] for f in ('problem','task','context')}} for cid in cids}
    u={'qid':qid,'target':target,'scope':'WHOLE_QUERY' if target=='WHOLE_QUERY' else 'ASPECT','query':queries[qid],'requirements':requirements,'families':CFG['families'],'cases':items,'output_shape':TEMPLATE}
    j={'job_id':f'{phase}_{index:04d}','phase':phase,'qid':qid,'target':target,'tasks':tasks,'items':items,'system':SYSTEM,'user':json.dumps(u,ensure_ascii=False,separators=(',',':'))+'\nReturn JSON.','output_cap':CFG['output_tokens_per_item']*len(cids)+CFG['output_tokens_overhead']}
    j['input_version']=digest(j);return j
def prepare():
    cases,queries=cases_queries();assert len(cases)==112 and len(queries)==10
    old=api.read_json(OLD_PLAN);groups=defaultdict(list);expected=old['diagnostic_expectations_not_model_inputs']
    for e in expected:groups[(e['query_id'],e['target_id'])].append(e['case_id'])
    pilot=[]
    for (qid,target),cids in groups.items():
        for i in range(0,len(cids),4):pilot.append(make_job('pilot',len(pilot),qid,cids[i:i+4],cases,queries,target))
    newkeys={(j['qid'],j['target'],c) for j in pilot for c in j['items']};assert newkeys=={(e['query_id'],e['target_id'],e['case_id']) for e in expected} and len(newkeys)==36
    probes=[make_job('probe',i,'V21D010',list(prior.PILOT['V21D010'][0]+prior.PILOT['V21D010'][1])[:n],cases,queries) for i,n in enumerate((1,2,4))]
    full=[]
    for qid in sorted(queries):
        for k in range(0,112,4):full.append(make_job('stage1',len(full),qid,sorted(cases)[k:k+4],cases,queries))
    views=[]
    for qid,q in sorted(queries.items()):
        for rep in range(1,4):
            j={'job_id':f'views_{qid}_r{rep}','phase':'views','qid':qid,'repeat':rep,'query':q,'system':'Generate distinct complementary problem perspectives, NOT solutions, using only the supplied problem. Never invent requirements, technology or effects. Return JSON.',
               'user':json.dumps({'query':q,'instruction':'Generate 2 to 5 distinct perspectives. JSON keys: perspectives list with id,title,description,keywords (list),source_quote (exact substring of query). Keep each description concise; no fixed categories, cases or reference aspects.'},ensure_ascii=False)+'\nReturn JSON.','output_cap':1000}
            j['input_version']=digest(j);views.append(j)
    for w in CFG['context_witnesses']:assert w['quote'] in cases[w['cid']][w['field']]
    plan={'version':CFG['version'],'base_commit':CFG['base_commit'],'config_sha256':hashlib.sha256((ROOT/'configs/evidence_rules_20261027.json').read_bytes()).hexdigest(),
          'input_hashes':{str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in (DATA/'dev_problem_views.csv',DATA/'dev_queries.json',DATA/'split_groups.csv',OLD_PLAN)},
          'probe':probes,'pilot':pilot,'stage1':full,'views':views,'pilot_expected_not_inputs':expected,'stage3_repeats':3,'human_gold':False,'stage4_sealed':True}
    path=OUT/'plan.json'
    if path.exists() and api.read_json(path)!=plan:raise ValueError('Frozen evidence plan changed; new version required')
    save(path,plan);return plan
def body(p,j,counting=False,retry=False):
    user=j['user']+('\nFormat correction only: exactly the requested JSON keys; exact source quotes; correct IDs/indices; <=18 words in each functional reason; never include scores.' if retry else '')
    m=CFG['models'][p]
    if p=='openai':
        b={'model':m,'instructions':j['system'],'input':user,'text':{'format':{'type':'json_object'}}}
        if not counting:b.update(max_output_tokens=j['output_cap'],store=False,reasoning={'effort':'none'},service_tier='default')
    elif p=='claude':
        b={'model':m,'system':j['system'],'messages':[{'role':'user','content':user}]}
        if not counting:b['max_tokens']=j['output_cap']
    else:
        b={'systemInstruction':{'parts':[{'text':j['system']}]},'contents':[{'role':'user','parts':[{'text':user}]}],'generationConfig':{'responseMimeType':'application/json','thinkingConfig':{'thinkingLevel':'minimal'},'maxOutputTokens':j['output_cap']}}
        if counting:b={'generateContentRequest':{'model':'models/'+m,**b}}
    return b
def count(p,j,retry=False):
    path=OUT/'counts'/p/(j['job_id']+('_format_retry' if retry else '')+'.json')
    if path.exists():
        result=api.read_json(path)
        if result.get('ok') or result.get('http_status') not in (429,500,502,503,504):return result
        path=path.with_name(path.stem+'_transient_retry1.json')
        if path.exists():return api.read_json(path)
    s,d=api.transport(p,body(p,j,True,retry),True);r={**s,'provider':p,'job_id':j['job_id'],'input_version':j['input_version'],'request_hash':digest(body(p,j,True,retry))}
    if s['ok']:
        n=d.get('totalTokens') if p=='gemini' else d.get('input_tokens');r.update(input_tokens=n,ok=type(n)is int and n>0)
    save(path,r);return r
def spent(p):
    total=Decimal(0)
    for path in (OUT/'attempts'/p).glob('*.json'):
        r=api.read_json(path);total+=Decimal(r.get('usage',{}).get('usage_cost_usd',r['reserved_usd']))
    return total
def halt():return STOP.is_set() or (OUT/'halt.json').exists()
def validate(text,j):
    try:
        d=json.loads(text.strip().removeprefix('```json').removesuffix('```').strip())
        if j['phase']=='views':
            vs=d['perspectives'];assert set(d)=={'perspectives'} and 2<=len(vs)<=5 and len({v['id'] for v in vs})==len(vs)
            assert all(set(v)=={'id','title','description','keywords','source_quote'} and isinstance(v['keywords'],list) and len(v['source_quote'])>=4 and v['source_quote'] in j['query'] and v['title'] and v['description'] for v in vs)
            return {'valid':True,'data':d,'derived':None,'errors':[]}
        rows=parse_evidence(d,j);derived={r['id']:score(r,j) for r in rows}
        if any(v['score'] is None for v in derived.values()):raise ValueError('SEMANTIC_LINK_CONTRADICTION')
        return {'valid':True,'data':d,'derived':derived,'errors':[]}
    except (ValueError,TypeError,KeyError,AssertionError,AttributeError,IndexError) as e:return {'valid':False,'data':None,'derived':None,'errors':[str(e)[:160] if isinstance(e,ValueError) else type(e).__name__]}
def run_job(p,j):
    target=OUT/'results'/p/(j['job_id']+'.json')
    if target.exists():return api.read_json(target)
    for a in (1,2):
        if halt():return None
        path=OUT/'attempts'/p/f"{j['job_id']}_a{a}.json"
        if path.exists():
            old=api.read_json(path)
            if old.get('state')=='RECEIVED' and old.get('usage'):
                v=validate(old['response_text'],j)
                if v['valid']:save(target,{**old,'validation':v,'known_response_reused':True});return api.read_json(target)
                continue
            STOP.set();return None
        c=count(p,j,a==2)
        if not c.get('ok'):STOP.set();return None
        amount=api.token_cost(p,math.ceil(c['input_tokens']*1.10)+96,j['output_cap'])
        with LOCK:
            cap=Decimal(CFG['claude_this_work_cap_usd']) if p=='claude' else Decimal('5')
            if spent(p)+amount>cap:STOP.set();return None
            save(path,{'state':'RESERVED','provider':p,'job_id':j['job_id'],'reserved_usd':api.money(amount),'input_version':j['input_version']})
        with RATE[p]:time.sleep(max(0,3-(time.monotonic()-LAST[p])));LAST[p]=time.monotonic()
        if halt():save(path,{'state':'CANCELLED_BEFORE_DISPATCH','provider':p,'job_id':j['job_id'],'reserved_usd':'0.00000000'});return None
        s,d=api.transport(p,body(p,j,False,a==2),False)
        r={**s,'state':'RECEIVED' if s['ok'] else 'UNCERTAIN_FAILURE','provider':p,'job_id':j['job_id'],'attempt':a,'reserved_usd':api.money(amount),'counted_input_tokens':c['input_tokens'],'input_version':j['input_version'],'request_model':CFG['models'][p],'request_hash':digest(body(p,j,False,a==2)),'human_gold':False}
        if d is not None:
            r.update(usage=api.extract_usage(p,d),response_text=api.extract_text(p,d),response_model=d.get('model',d.get('modelVersion')),response_id=d.get('id',d.get('responseId')))
            r['validation']=validate(r['response_text'],j)
            if not api.model_matches(p,r['response_model']):r['validation']['valid']=False;r['validation']['errors'].append('WRONG_MODEL');STOP.set()
        save(path,r);v=r.get('validation',{})
        print(json.dumps({'provider':p,'job':j['job_id'],'valid':v.get('valid',False),'errors':v.get('errors',[]),'cost':r.get('usage',{}).get('usage_cost_usd')}),flush=True)
        if v.get('valid'):save(target,r);return r
        if not s['ok']:STOP.set();return r
    STOP.set();return r
def budget(plan):
    jobs=[j for phase in ('probe','pilot','stage1','views') for j in plan[phase]];costs={p:{} for p in CFG['models']};fail=[]
    with ThreadPoolExecutor(max_workers=6) as pool:
        fs={pool.submit(count,p,j):(p,j) for p in CFG['models'] for j in jobs}
        for f in as_completed(fs):
            p,j=fs[f];c=f.result()
            if not c.get('ok'):fail.append(c);continue
            t=costs[p].setdefault(j['phase'],{'input_tokens':0,'output_cap_tokens':0,'requests':0,'upper_usd':Decimal(0)})
            t['input_tokens']+=c['input_tokens'];t['output_cap_tokens']+=j['output_cap'];t['requests']+=1;t['upper_usd']+=api.token_cost(p,math.ceil(c['input_tokens']*1.10)+96,j['output_cap'])
    for phases in costs.values():
        for c in phases.values():c['upper_usd']=api.money(c['upper_usd'])
    cl=costs['claude'];needed=sum((Decimal(cl.get(x,{}).get('upper_usd','0'))*2 for x in ('probe','pilot')),Decimal(0))+sum((Decimal(cl.get(x,{}).get('upper_usd','0'))*Decimal('1.25') for x in ('stage1','views')),Decimal(0))
    r={'costs':costs,'failed_counts':fail,'claude_new_upper_with_retries':api.money(needed),'prior_reserved':CFG['claude_prior_actual_plus_reserved_usd'],'safety':'0.50','fits':not fail and needed<=Decimal(CFG['claude_this_work_cap_usd']),'account_balance_checked':False,'stage3_repeats':3,'stage3_generation_requests':90}
    save(OUT/'budget.json',r);print(json.dumps(r,ensure_ascii=False),flush=True);return r
def execute(plan,phase):
    if halt():raise ValueError('Active hold')
    if not api.read_json(OUT/'budget.json')['fits']:raise ValueError('Budget gate')
    if phase=='pilot' and not api.read_json(OUT/'probe_gate.json')['passed']:raise ValueError('Probe gate')
    if phase in ('stage1','views') and not api.read_json(OUT/'pilot_gate.json')['passed']:raise ValueError('Pilot gate')
    if phase=='views' and not (OUT/'stage2_results.json').exists():raise ValueError('Stage2 required')
    def lane(p,js):
        for j in js:
            if halt():break
            run_job(p,j)
    with ThreadPoolExecutor(max_workers=6) as pool:
        fs=[pool.submit(lane,p,plan[phase][i::2]) for p in CFG['models'] for i in (0,1)]
        for f in as_completed(fs):f.result()
    if STOP.is_set():save(OUT/'halt.json',{'active':True,'reason':'API_OR_OUTPUT_OR_BUDGET_FAILURE','no_unknown_replay':True})
    return not STOP.is_set()
def summary(plan,phase):
    expected={(j['qid'],j.get('target','WHOLE_QUERY'),c):{} for j in plan[phase] for c in j.get('items',{})};records=[]
    for p in CFG['models']:
        for j in plan[phase]:
            f=OUT/'results'/p/(j['job_id']+'.json')
            if not f.exists():continue
            r=api.read_json(f)
            for row in r['validation']['data']['items']:
                d=r['validation']['derived'][row['id']];key=(j['qid'],j['target'],row['id']);expected[key][p]=d['score']
                records.append({'provider':p,'qid':key[0],'target':key[1],'case_id':key[2],'evidence':row,'computed':d,'input_version':j['input_version'],'source':str(f.relative_to(ROOT)).replace('\\','/')})
    complete=[v for v in expected.values() if len(v)==3]
    out={'phase':phase,'expected_scores':len(expected)*3,'received_scores':len(records),'complete_pairs':len(complete),'grade_agreement':sum(len(set(v.values()))==1 for v in complete),'binary_agreement':sum(len({s>=3 for s in v.values()})==1 for v in complete),'pairs':[{'qid':q,'target':t,'case_id':c,'scores':v} for (q,t,c),v in expected.items()],'records':records,'human_gold':False,'approved_silver':False}
    save(OUT/(phase+'_summary.json'),out);print(json.dumps({k:v for k,v in out.items() if k not in ('pairs','records')},ensure_ascii=False));return out
def main():
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['prepare','count','probe','pilot','pilot-summary','stage1','stage1-summary','views']);a=parser.parse_args()
    if a.phase not in ('prepare','pilot-summary','stage1-summary') and (OUT/'halt.json').exists():print('HOLD: no new API calls');return 2
    plan=prepare()
    if a.phase=='prepare':print('Prepared exact36; full1120; probes1/2/4; views30/model =90.');return 0
    if a.phase=='count':return 0 if budget(plan)['fits'] else 2
    if a.phase.endswith('-summary'):summary(plan,a.phase.split('-')[0]);return 0
    return 0 if execute(plan,a.phase) else 2
if __name__=='__main__':raise SystemExit(main())
