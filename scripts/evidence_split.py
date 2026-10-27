"""Query-blind inventory followed by query-specific links; plain JSON only."""
import argparse
import json
import math
import re
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor,as_completed
from decimal import Decimal
from scripts import evidence_run as r
from scripts.evidence_rules import parse_evidence,score,CFG

BASE=r.OUT;V12=BASE/'query-blind-v12';OUT=BASE/'query-blind-v13';api=r.api;save=r.save;digest=r.digest
INV_SYSTEM='''Extract actual performed operations from Task and Context ONLY. You are NOT given any user problem or case Problem. Do not invent missing operations, technology, goals or effects. Normalize actions, functional objects and produced outputs into concise ASCII English, <=64 characters each. Inferring summarize -> summary or answer -> answer is linguistic entailment; inventing a capability is not. Use the supplied source ID for the exact supporting Task/Context clause; never rewrite a quote. Prefer a short Task clause. Two distinct operations should use their own clauses when present. Merge repeated instances of the same action. ANSWER includes solving user requests/troubleshooting. ACTION_ITEMS means explicitly identifying or preparing next steps; summarizing alone is not that. DIAGNOSE means reasons/causes, DETECT is only presence. Return JSON exactly {"items":[{"id":"case id","ops":[["FAMILY","actual action","functional object","produced output","source ID"]]}]}. No scores, no links, no other keys. Each item once; at most3 operations. Use only the supplied families and source IDs. No Markdown.'''
MATCH_SYSTEM='''Compare a single query/target to the fixed performed-operation inventory for each case. NEVER create or change an operation. The inventory was extracted without seeing this query. Problem describes needs/background, not additional capabilities. WHOLE_QUERY allows any listed core task; ASPECT permits only its selected task. Different sectors, recipient roles and channels are allowed if functional ACTION, OBJECT and OUTPUT correspond. Do not equate summarizing with identifying next actions, detecting a defect with cause diagnosis, or generic effort savings with task relevance.
Return JSON exactly {"qid":"copy","target":"copy","items":[{"id":"case id","links":[[target_index,operation_index,"EEE","DIRECT","short functional comparison"]]}]}. Target and operation indices are the numeric positions in their supplied lists, never case IDs. Mask has ACTION/OBJECT/OUTPUT letters E=equivalent, S=concrete supporting, D=different/unstated. relation DIRECT requires EEE and compatible family. SUPPORT is a real partial/upstream/downstream operation; BROAD is broader operational resemblance. Omit unrelated links; busy people/industry alone is not a link. Explain functional correspondence in <=18 English words per link, never benefits, technologies or outcomes. Do not output scores or operations. Preserve qid,target and each case ID exactly. No Markdown.'''
MATCH_SYSTEM=MATCH_SYSTEM.replace(' and compatible family','')+' Inventory entries shown here are [actual action,functional object,produced output,source ID]. Normalized atoms can be imprecise: verify the actual operation against Task and the referenced source clause. The raw Task/Context is authoritative. Linguistically entailed outputs are allowed, new capabilities/benefits are not. No category label is a substitute for functional meaning.'

def semantic_score(row,job):
    direct=[];support=[];broad=[];warnings=[]
    for tid,i,mask,relation,why in row['links']:
        fam,a,o,y,quote=row['ops'][i]
        evidence={'target':tid,'op':i,'action':a,'object':o,'output':y,'quote':quote,'why':why}
        if relation=='DIRECT' and mask=='EEE':
            direct.append(evidence)
            if fam not in CFG['target_families'][tid]:warnings.append({'kind':'INVENTORY_CATEGORY_DISAGREEMENT_NOT_A_SCORE_RULE','family':fam,'target':tid,'source':quote})
        elif relation=='SUPPORT' and any(v in mask for v in 'ES'):support.append(evidence)
        elif any(v in mask for v in 'ES'):broad.append(evidence)
    value=3 if direct else 2 if support else 1 if broad else 0
    rule='SOURCE_GROUNDED_FUNCTIONAL_AOO' if direct else 'GROUNDED_SUPPORT' if support else 'BROAD_OPERATIONAL_LINK' if broad else 'NO_OPERATIONAL_LINK';fourth=[]
    if direct:
        for x in direct:
            for z in direct:
                if x['target']!=z['target'] and x['op']!=z['op'] and x['quote']!=z['quote'] and x['action'].casefold()!=z['action'].casefold():
                    fourth.append({'type':'DISTINCT_ADDITIONAL_CORE_OPERATION','first':x,'second':z})
        for w in CFG['context_witnesses']:
            if w['qid']==job['qid'] and w['target']==job['target'] and w['cid']==row['id']:
                assert w['quote'] in job['items'][row['id']][w['field']]
                fourth.append({'type':'PREVERIFIED_SCOPE_CONDITION','source':w})
        if fourth:value=4;rule='DIRECT_PLUS_GROUNDED_ADDITIONAL_EVIDENCE'
    return {'score':value,'relevant':value>=3,'status':'AI_FUNCTION_JUDGMENT_PROGRAM_SCORE_NOT_HUMAN_GOLD','score_rule_version':'functional-evidence-v14','rule':rule,'direct':direct,'support':support,'broad':broad,'fourth_point_evidence':fourth,'flags':warnings}
score=semantic_score

def sources(c):
    out={'T0':c['task'],'C0':c['context']}
    parts=re.split(r'\s+and\s+|·',c['task'])
    if len(parts)>1:
        for i,s in enumerate(parts,1):
            if s.strip():out['T'+str(i)]=s.strip()
    return out
def inventory_job(phase,i,cids,cs):
    items={c:{'task':cs[c]['task'],'context':cs[c]['context'],'sources':sources(cs[c])} for c in cids}
    j={'job_id':f'{phase}_{i:04d}','phase':phase,'items':items,'system':INV_SYSTEM,'user':json.dumps({'families':CFG['families'],'cases':items},ensure_ascii=False,separators=(',',':'))+'\nReturn JSON.','output_cap':220*len(items)+128}
    j['input_version']=digest(j);return j
def inventory_validate(text,j):
    d,repair=decode_json(text);assert set(d)=={'items'}
    rows=d['items'];assert len(rows)==len(j['items']) and len({v['id'] for v in rows})==len(rows) and {v['id'] for v in rows}==set(j['items'])
    for v in rows:
        assert set(v)=={'id','ops'} and isinstance(v['ops'],list) and len(v['ops'])<=3
        for op in v['ops']:
            assert len(op)==5 and all(isinstance(x,str) and x.strip() for x in op)
            assert op[0] in CFG['families'] and op[4] in j['items'][v['id']]['sources']
            assert all(x.isascii() and len(x)<=64 and len(x.split())<=10 for x in op[1:4])
            assert not re.search(r'workload reduction|time savings|improved quality|freed capacity|reduced staff', ' '.join(op[1:4]),re.I)
    return {'valid':True,'data':d,'derived':None,'errors':[],'syntax_repair':repair}
def match_validate(text,j):
    d,repair=decode_json(text)
    assert set(d)=={'qid','target','items'} and d['qid']==j['qid'] and d['target']==j['target']
    assert len(d['items'])==len(j['items']) and len({x['id'] for x in d['items']})==len(d['items']) and {x['id'] for x in d['items']}==set(j['items'])
    converted={'qid':j['qid'],'target':j['target'],'items':[]}
    for x in d['items']:
        assert set(x)=={'id','links'}
        ops=[]
        for op in j['inventory'][x['id']]['ops']:
            ops.append(op[:4]+[j['items'][x['id']]['sources'][op[4]]])
        links=[]
        for link in x['links']:
            assert len(link)==5 and type(link[0])is int and link[0] in range(len(j['tasks']))
            links.append([list(j['tasks'])[link[0]],*link[1:]])
        converted['items'].append({'id':x['id'],'ops':ops,'links':links})
    parsed=parse_evidence(converted,j);derived={x['id']:score(x,j) for x in parsed}
    if any(v['score'] is None for v in derived.values()):raise ValueError('SEMANTIC_FAMILY_CONTRADICTION')
    return {'valid':True,'data':converted,'raw_links':d,'derived':derived,'errors':[],'syntax_repair':repair}
def decode_json(text):
    raw=text.strip().removeprefix('```json').removesuffix('```').strip()
    try:return json.loads(raw),[]
    except json.JSONDecodeError:pass
    # Only add missing closing delimiters outside strings. Never add a value,
    # comma, ID, quote or field. Full structural/source validation still follows.
    stack=[];out=[];inside=False;escaped=False;repairs=[]
    for pos,ch in enumerate(raw):
        if inside:
            out.append(ch)
            if escaped:escaped=False
            elif ch=='\\':escaped=True
            elif ch=='"':inside=False
            continue
        if ch=='"':inside=True;out.append(ch);continue
        if ch in '[{':stack.append(ch)
        elif ch in ']}':
            expected='[' if ch==']' else '{'
            while stack and stack[-1]!=expected:
                added=']' if stack.pop()=='[' else '}'
                out.append(added);repairs.append({'position':pos,'inserted':added})
            if not stack:raise ValueError('UNREPAIRABLE_JSON_CLOSURE')
            stack.pop()
        out.append(ch)
    if inside:raise ValueError('TRUNCATED_STRING_NO_REPAIR')
    while stack:
        added=']' if stack.pop()=='[' else '}';out.append(added);repairs.append({'position':len(raw),'inserted':added})
    corrected=''.join(out)
    return json.loads(corrected),repairs
def validate(text,j):
    try:return inventory_validate(text,j) if j['phase'].startswith('inventory') else match_validate(text,j) if j['phase'] not in ('views',) else ORIGINAL_VALIDATE(text,j)
    except (ValueError,AssertionError,TypeError,KeyError,AttributeError,IndexError) as e:return {'valid':False,'data':None,'derived':None,'errors':[str(e)[:140] if isinstance(e,ValueError) else 'JSON_ID_SOURCE_OR_BOUNDED_ATOM_FORMAT']}
ORIGINAL_VALIDATE=r.validate
r.OUT=OUT;r.validate=validate
ORIGINAL_BODY=r.body
def split_body(p,j,counting=False,retry=False):
    if retry:
        if j['phase'].startswith('inventory'):
            reminder='Return only items with id and ops. Each op has exactly5 strings: family, ASCII action, ASCII object, ASCII output, source ID KEY. Use source IDs such as T0/T1/C0, never copied source text. Each normalized atom <=64 ASCII characters. No scores, query links or other keys.'
        elif j['phase']=='views':
            reminder='Return only perspectives, a list of2 to5 entries with id,title,description,keywords list,source_quote copied verbatim from query.'
        else:
            reminder='Return only qid,target,items. Each item has id and links ONLY. A link has numeric target_index,numeric operation_index,3-letter E/S/D mask,relation,reason <=18 English words. Do not invent operations or output scores.'
        j={**j,'user':j['user']+'\nFormat correction: '+reminder+' Return JSON.'}
    return ORIGINAL_BODY(p,j,counting,False)
r.body=split_body
def spent(p):
    total=Decimal(0)
    for base in (BASE,V12,OUT):
        for path in (base/'attempts'/p).glob('*.json'):
            d=api.read_json(path);total+=Decimal(d.get('usage',{}).get('usage_cost_usd',d['reserved_usd']))
    return total
r.spent=spent
ORIGINAL_COUNT=r.count
def versioned_count(p,j,retry=False):
    path=OUT/'counts'/p/(j['job_id']+('_format_retry' if retry else '')+'.json')
    if path.exists() and api.read_json(path).get('input_version')!=j['input_version']:
        # Preserve preliminary empty-profile counts; never bill against stale input.
        variant={**j,'job_id':j['job_id']+'_input_'+j['input_version'][:12]}
        return ORIGINAL_COUNT(p,variant,retry)
    return ORIGINAL_COUNT(p,j,retry)
r.count=versioned_count
def base_plan():
    cs,qs=r.cases_queries();old=api.read_json(r.OLD_PLAN);ex=old['diagnostic_expectations_not_model_inputs'];pilot_ids=sorted({v['case_id'] for v in ex})
    sets={'inventory_probe':[], 'inventory_pilot':[], 'inventory_full':[]}
    probe_ids=[*r.prior.PILOT['V21D010'][0],*r.prior.PILOT['V21D010'][1]][:4]
    for i,n in enumerate((1,2,4)):sets['inventory_probe'].append(inventory_job('inventory_probe',i,probe_ids[:n],cs))
    for phase,ids in (('inventory_pilot',pilot_ids),('inventory_full',sorted(set(cs)-set(pilot_ids)))):
        for off in range(0,len(ids),4):sets[phase].append(inventory_job(phase,len(sets[phase]),ids[off:off+4],cs))
    plan={'version':'query-blind-v13','base_commit':CFG['base_commit'],'pilot_expected':ex,'pilot_ids':pilot_ids,'probe_ids':probe_ids,'sets':sets,
          'input_hashes':{str(p.relative_to(r.ROOT)).replace('\\','/'):r.hashlib.sha256(p.read_bytes()).hexdigest() for p in (r.DATA/'dev_problem_views.csv',r.DATA/'dev_queries.json',r.OLD_PLAN,r.ROOT/'configs/evidence_rules_20261027.json')},'human_gold':False,'stage4_sealed':True,'repeats':3}
    path=OUT/'base_plan.json'
    if path.exists() and api.read_json(path)!=plan:raise ValueError('Frozen source plan changed')
    save(path,plan);return plan
def profiles(p,ids):
    result={}
    for cid in ids:
        d=api.read_json(OUT/'profiles'/p/(cid+'.json'));result[cid]=d
    return result
def match_job(phase,index,qid,target,ids,p,estimate=False):
    cs,qs=r.cases_queries();basic=r.make_job(phase,index,qid,ids,cs,qs,target)
    inv={c:{'ops':[]} for c in ids} if estimate else profiles(p,ids)
    items={c:{**basic['items'][c],'sources':sources(cs[c]),'inventory':[op[1:] for op in inv[c]['ops']]} for c in ids}
    req=[{'id':tid,'function':v} for tid,v in basic['tasks'].items()]
    user=json.dumps({'qid':qid,'target':target,'query':qs[qid],'requirements':req,'cases':items},ensure_ascii=False,separators=(',',':'))+'\nReturn JSON.'
    j={**basic,'items':items,'inventory':inv,'system':MATCH_SYSTEM,'user':user,'output_cap':110*len(ids)+128}
    if estimate:j['job_id']='estimate_'+j['job_id']
    j['input_version']=digest(j);return j
def phase_jobs(plan,phase,p,estimate=False):
    if phase in plan['sets']:return plan['sets'][phase]
    if phase=='views':
        cs,qs=r.cases_queries();out=[]
        for qid,q in sorted(qs.items()):
            for rep in range(1,4):
                j={'job_id':f'views_{qid}_r{rep}','phase':'views','qid':qid,'repeat':rep,'query':q,'system':'Generate 2 to 5 complementary problem perspectives from the original problem alone, not solutions or invented requirements. Return JSON.',
                   'user':json.dumps({'query':q,'output':'JSON {perspectives:[{id,title,description,keywords:[words],source_quote:exact substring of query}]}; concise descriptions; no predefined categories.'},ensure_ascii=False)+'\nReturn JSON.','output_cap':1000};j['input_version']=digest(j);out.append(j)
        return out
    out=[]
    if phase=='match_probe':
        for i,n in enumerate((1,2,4)):out.append(match_job(phase,i,'V21D010','WHOLE_QUERY',plan['probe_ids'][:n],p,estimate))
    elif phase=='pilot':
        groups=defaultdict(list)
        for e in plan['pilot_expected']:groups[(e['query_id'],e['target_id'])].append(e['case_id'])
        for (qid,t),ids in groups.items():
            for k in range(0,len(ids),4):out.append(match_job(phase,len(out),qid,t,ids[k:k+4],p,estimate))
    elif phase=='stage1':
        cs,qs=r.cases_queries()
        for qid in sorted(qs):
            for k in range(0,112,4):out.append(match_job(phase,len(out),qid,'WHOLE_QUERY',sorted(cs)[k:k+4],p,estimate))
    return out
def execute(plan,phase):
    if r.halt():raise ValueError('Active hold')
    if phase in ('inventory_probe','inventory_pilot'):
        if not api.read_json(OUT/'preflight_budget.json')['fits']:raise ValueError('Preflight budget')
    elif phase=='inventory_full':
        if not api.read_json(OUT/'pilot_gate.json')['passed']:raise ValueError('Pilot gate')
    elif phase=='stage1':
        if not api.read_json(OUT/'pilot_gate.json')['passed'] or not api.read_json(OUT/'actual_budget.json')['fits']:raise ValueError('Full gate')
    elif phase=='views' and not (OUT/'stage2_results.json').exists():raise ValueError('Stage2 gate')
    elif phase=='pilot' and not api.read_json(OUT/'probe_gate.json')['passed']:raise ValueError('Probe gate')
    jobs={p:phase_jobs(plan,phase,p) for p in CFG['models']}
    save(OUT/(phase+'_jobs.json'),jobs)
    def lane(p,js):
        for j in js:
            if r.halt():break
            result=r.run_job(p,j)
            if phase in ('inventory_pilot','inventory_full') and result and result.get('validation',{}).get('valid'):
                for row in result['validation']['data']['items']:
                    path=OUT/'profiles'/p/(row['id']+'.json')
                    profile={'ops':row['ops'],'provider':p,'source_job':j['job_id'],'source_input_version':j['input_version'],'task_context_sha256':digest({'task':j['items'][row['id']]['task'],'context':j['items'][row['id']]['context']})}
                    if path.exists():
                        if api.read_json(path)!=profile:raise ValueError('Conflicting profile overwrite forbidden')
                    else:save(path,profile)
    with ThreadPoolExecutor(max_workers=6) as pool:
        fs=[pool.submit(lane,p,jobs[p][i::2]) for p in CFG['models'] for i in (0,1)]
        for f in as_completed(fs):f.result()
    if r.STOP.is_set():save(OUT/'halt.json',{'active':True,'reason':'API_OR_FORMAT_OR_BUDGET_FAILURE','no_unknown_replay':True})
    return not r.STOP.is_set()
def budget(plan,actual=False):
    phases=('inventory_probe','inventory_pilot','inventory_full','match_probe','pilot','stage1','views');costs={p:{} for p in CFG['models']};fail=[];items=[]
    for p in CFG['models']:
        for phase in phases:
            if actual and phase in ('inventory_probe','inventory_pilot','inventory_full','match_probe','pilot'):continue
            for j in phase_jobs(plan,phase,p,not actual and phase in ('match_probe','pilot','stage1')):items.append((p,phase,j))
    with ThreadPoolExecutor(max_workers=6) as pool:
        fs={pool.submit(r.count,p,j):(p,phase,j) for p,phase,j in items}
        for f in as_completed(fs):
            p,phase,j=fs[f];c=f.result()
            if not c.get('ok'):fail.append(c);continue
            t=costs[p].setdefault(phase,{'requests':0,'input_tokens':0,'unknown_profile_token_reserve':0,'upper_usd':Decimal(0)})
            extra=800*len(j['items']) if not actual and phase in ('match_probe','pilot','stage1') else 0
            t['requests']+=1;t['input_tokens']+=c['input_tokens'];t['unknown_profile_token_reserve']+=extra
            t['upper_usd']+=api.token_cost(p,math.ceil((c['input_tokens']+extra)*1.10)+96,j['output_cap'])
    for phases_ in costs.values():
        for t in phases_.values():t['upper_usd']=api.money(t['upper_usd'])
    cl=costs['claude'];need=spent('claude')
    for phase,t in cl.items():need+=Decimal(t['upper_usd'])*(Decimal('1.25') if phase in ('stage1','views') else Decimal('2'))
    out={'version':'actual_profiles' if actual else 'bounded_unknown_profiles','costs':costs,'failed_counts':fail,'claude_this_work_upper':api.money(need),'prior':CFG['claude_prior_actual_plus_reserved_usd'],'buffer':'0.50','fits':not fail and need<=Decimal(CFG['claude_this_work_cap_usd']),'stage3_repeats':3,'generation_requests':90,'unknown_profile_bound':'<=3 ops, ASCII atoms <=64 chars; extra800 tokens per case conservatively exceeds serialized profile bytes; remeasure actual before full score collection'}
    save(OUT/('actual_budget.json' if actual else 'preflight_budget.json'),out);print(json.dumps(out,ensure_ascii=False),flush=True);return out
def summary(plan,phase):
    jobs={p:phase_jobs(plan,phase,p) for p in CFG['models']};pairs={};records=[]
    for p in CFG['models']:
        for j in jobs[p]:
            path=OUT/'results'/p/(j['job_id']+'.json')
            if not path.exists():continue
            d=api.read_json(path)
            for row in d['validation']['data']['items']:
                key=(j['qid'],j['target'],row['id']);derived=d['validation']['derived'][row['id']];pairs.setdefault(key,{})[p]=derived['score']
                records.append({'provider':p,'qid':key[0],'target':key[1],'case_id':key[2],'evidence':row,'computed':derived,'source':str(path.relative_to(r.ROOT)).replace('\\','/'),'input_version':j['input_version']})
    complete=[v for v in pairs.values() if len(v)==3]
    o={'phase':phase,'received_scores':len(records),'complete_pairs':len(complete),'grade_agreement':sum(len(set(v.values()))==1 for v in complete),'binary_agreement':sum(len({s>=3 for s in v.values()})==1 for v in complete),'records':records,'pairs':[{'qid':k[0],'target':k[1],'case_id':k[2],'scores':v} for k,v in pairs.items()],'human_gold':False,'approved':False}
    save(OUT/(phase+'_summary.json'),o);print(json.dumps({k:v for k,v in o.items() if k not in ('records','pairs')}));return o
def main():
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['prepare','count','count-actual','inventory_probe','inventory_pilot','match_probe','pilot','pilot-summary','inventory_full','stage1','stage1-summary','views']);a=p.parse_args()
    if a.phase not in ('prepare','pilot-summary','stage1-summary') and (OUT/'halt.json').exists():print('HOLD: no API calls');return 2
    plan=base_plan()
    if a.phase=='prepare':return 0
    if a.phase in ('count','count-actual'):return 0 if budget(plan,a.phase=='count-actual')['fits'] else 2
    if a.phase.endswith('-summary'):summary(plan,a.phase.split('-')[0]);return 0
    return 0 if execute(plan,a.phase) else 2
if __name__=='__main__':raise SystemExit(main())
