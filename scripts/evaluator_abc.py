"""Small-item ABC evaluator experiment with isolated query/case extraction."""
import argparse
from collections import Counter
from decimal import Decimal
import json
import re
import time

from ax_research.heldout import read, write, jsonl, sha
from scripts import e_validation as transport
from scripts import evaluator_abc_prompts as prompts

ROOT=transport.ROOT
OUT=ROOT/'docs/evaluator-reliability-abc-2026-11-07'
PRIOR=ROOT/'docs/autonomous-ax-study-2026-11-07'
VALIDATION=ROOT/'docs/core-preserved-e-validation-2026-11-07'
CAPS={'openai':Decimal('.30'),'claude':Decimal('1.70')}
SCOPE={'FULL_CORE':3,'TRANSFER_CORE':2,'AUXILIARY':1,'NONE':0,'UNCERTAIN':None}
CURRENT_PROVIDER=None


def configure(provider):
    global CURRENT_PROVIDER
    CURRENT_PROVIDER=provider
    transport.OUT=OUT/provider
    transport.OUT.mkdir(exist_ok=True);(transport.OUT/'api').mkdir(exist_ok=True)
    actual_ledger=transport.ledger
    def guarded_ledger():
        actual=actual_ledger()
        # The unchanged transport's2USD guard becomes a provider-specific cap.
        return {**actual,'conservative_spent_or_reserved_usd':str(
            Decimal(actual['conservative_spent_or_reserved_usd'])+2-CAPS[provider])}
    transport.ledger=guarded_ledger


def anchors(case):
    return {prefix+'1':{'field':field,'start':0,'end':len(case[field]),'quote':case[field]}
            for prefix,field in [('T','Task'),('C','Context'),('P','Problem')] if case.get(field)}


def decode(raw,provider):
    complete=raw.get('status')=='completed' if provider=='openai' else raw.get('stop_reason')=='end_turn'
    if not complete:return None,'TOKEN_LIMIT_OR_INCOMPLETE'
    text=(''.join(c.get('text','') for x in raw.get('output',[]) for c in x.get('content',[])
                  if c.get('type')=='output_text') if provider=='openai' else
          ''.join(c.get('text','') for c in raw.get('content',[]) if c.get('type')=='text'))
    text=text.strip()
    if text.startswith('```'):
        # A complete fenced JSON object may be followed by explanatory prose.
        # Read the single unchanged fenced object only; never synthesize braces,
        # merge objects, or choose between multiple alternative answers.
        blocks=re.findall(r'```(?:json)?\s*\n(.*?)```',text,re.DOTALL)
        if len(blocks)!=1:return None,'INVALID_JSON'
        text=blocks[0].strip()
    try:return json.loads(text),None
    except ValueError:return None,'INVALID_JSON'


def read_attempt(provider,identifier):
    directory=OUT/provider/'api';receipt=directory/(provider+'_'+identifier+'_receipt.json')
    if not receipt.exists():return None,'NOT_REQUESTED'
    meta=read(receipt)
    if meta['state']!='RECEIVED':
        return None,'HTTP_429' if meta.get('http_status')==429 else 'UNCERTAIN_OR_HTTP_FAILURE'
    return decode(read(directory/(provider+'_'+identifier+'_response.json')),provider)


def validate_core(kind,data,identifier,available):
    if not isinstance(data,dict) or data.get('id')!=identifier:return 'MISSING_OR_WRONG_ID'
    if not {'action','object','output','time_type'}<=set(data):return 'MISSING_FIELDS'
    if data['time_type'] not in ('CURRENT','FUTURE','NONE','UNKNOWN'):return 'INVALID_ENUM'
    if any(data[f] is not None and not isinstance(data[f],str) for f in ('action','object','output')):return 'INVALID_SCHEMA'
    if kind=='query':
        if not {'required_operations','constraints'}<=set(data):return 'MISSING_FIELDS'
        if any(not isinstance(data[f],list) or any(not isinstance(v,str) for v in data[f])
               for f in ('required_operations','constraints')):return 'INVALID_SCHEMA'
    if kind=='case':
        if not {'execution','evidence','operations','unknowns'}<=set(data):return 'MISSING_FIELDS'
        if data['execution'] not in ('CONFIRMED','PROPOSAL_STUDY','UNSPECIFIED'):return 'INVALID_ENUM'
        if any(not isinstance(data[f],list) or any(not isinstance(v,str) for v in data[f])
               for f in ('operations','unknowns')):return 'INVALID_SCHEMA'
        evidence=data['evidence']
        if not isinstance(evidence,dict) or not {'action','object','output','execution'}<=set(evidence):return 'MISSING_FIELDS'
        for field,ids in evidence.items():
            if not isinstance(ids,list):return 'INVALID_SCHEMA'
            for anchor in ids:
                if not isinstance(anchor,str):return 'INVALID_SCHEMA'
                if anchor not in available:return 'UNKNOWN_ANCHOR'
                if available[anchor]['field']=='Problem':return 'SEMANTIC_PROBLEM_AS_PERFORMED'
            if field in ('action','object','output') and data.get(field) is not None and not ids:
                return 'MISSING_EVIDENCE'
    return None


TECHNICAL={'TOKEN_LIMIT_OR_INCOMPLETE','INVALID_JSON','MISSING_OR_WRONG_ID','MISSING_FIELDS','INVALID_ENUM','INVALID_SCHEMA','HTTP_429'}


def request(identifier,prompt,payload,limit,validator):
    provider=CURRENT_PROVIDER
    result_path=OUT/provider/'results'/(identifier+'.json')
    result_path.parent.mkdir(exist_ok=True)
    if result_path.exists():
        cached=read(result_path)
        assert cached['prompt_payload_sha256']==transport.digest({'prompt':prompt,'payload':payload})
        return cached
    attempts=[];data=None;failure=None
    for attempt in range(2):
        name=identifier if attempt==0 else identifier+'_technical1'
        transport.call(provider,name,prompt,payload,limit if attempt==0 else limit*2)
        data,failure=read_attempt(provider,name)
        if failure is None:
            try:failure=validator(data)
            except (AssertionError,KeyError,TypeError,ValueError):failure='INVALID_SCHEMA'
        attempts.append({'id':provider+'_'+name,'failure':failure})
        if failure is None or failure not in TECHNICAL:break
        if attempt==0:time.sleep(2)
    result={'data':data,'valid':failure is None,'failure':failure,'attempts':attempts,
            'retry_is_technical_only':True,'prompt_payload_sha256':transport.digest({'prompt':prompt,'payload':payload})}
    write(result_path,result)
    return result


def query_core(question):
    identifier='Q'+transport.digest(question)[:14]
    return request('qcore_'+identifier,prompts.QUERY,{'id':identifier,'question':question},700,
                   lambda d:validate_core('query',d,identifier,{}))


def case_core(case):
    identifier='K'+transport.digest(case)[:14];available=anchors(case)
    return request('ccore_'+identifier,prompts.CASE,{'id':identifier,'case':case,'anchors':available},900,
                   lambda d:validate_core('case',d,identifier,available))


def check_decision(data,identifier,method,available,question=''):
    if method=='A':
        if not isinstance(data,dict) or not isinstance(data.get('assessments'),list) or len(data['assessments'])!=1:
            return 'MISSING_FIELDS'
        d=data['assessments'][0]
        if d.get('id')!=identifier or d.get('query_id')!=identifier:return 'MISSING_OR_WRONG_ID'
        if not {'scope','category','reason','claims','query_quotes'}<=set(d):return 'MISSING_FIELDS'
        if d['scope'] not in SCOPE:return 'INVALID_ENUM'
        if d['category'] not in ('JUDGEABLE','POLICY_BOUNDARY','SOURCE_INSUFFICIENT','EXPERT_REVIEW'):return 'INVALID_ENUM'
        if not isinstance(d['query_quotes'],list) or not d['query_quotes']:return 'INVALID_SCHEMA'
        if any(not isinstance(q,str) or not q or q not in question for q in d['query_quotes']):return 'UNSUPPORTED_QUERY_CITATION'
        if not isinstance(d['claims'],list):return 'INVALID_SCHEMA'
        # Wrong-field quotations are relocated only if the exact unchanged text
        # occurs in another permitted field. Never manufacture a source quote.
        citations=[];corrections=[]
        for claim in d['claims']:
            if claim.get('field')=='Problem':return 'SEMANTIC_PROBLEM_AS_PERFORMED'
            quote=claim.get('quote')
            matches=[key for key,a in available.items() if a['field'] in ('Task','Context')
                     and isinstance(quote,str) and quote and quote in a['quote']]
            if not matches:return 'UNSUPPORTED_LITERAL_CITATION'
            exact=[key for key in matches if available[key]['field']==claim.get('field')]
            selected=exact[0] if exact else matches[0]
            citations.append(selected)
            if not exact:corrections.append({'original':claim,'resolved_field':available[selected]['field'],
                                              'quote_unchanged':True})
        d['_citations']=citations;d['_field_corrections']=corrections
        return None
    if not isinstance(data,dict) or data.get('id')!=identifier:return 'MISSING_OR_WRONG_ID'
    required={'reason','evidence_ids','new_core_functions'} | ({'grade','status'} if method=='B' else {'checks'})
    if not required<=set(data):return 'MISSING_FIELDS'
    if not isinstance(data['evidence_ids'],list) or not isinstance(data['new_core_functions'],list):return 'INVALID_SCHEMA'
    for key in data['evidence_ids']:
        if key not in available:return 'UNKNOWN_ANCHOR'
        if available[key]['field']=='Problem':return 'SEMANTIC_PROBLEM_AS_PERFORMED'
    if method=='B':
        if data['status'] not in ('JUDGED','ABSTAIN'):return 'INVALID_ENUM'
        if data['status']=='JUDGED' and (type(data['grade']) is not int or data['grade'] not in range(4)):return 'INVALID_ENUM'
        if data['status']=='ABSTAIN' and data['grade'] is not None:return 'INVALID_ENUM'
    else:
        fields={'actual_work_known','action_match','object_match','output_match','direct_core',
                'transfer_core','core_sufficient','auxiliary_only','any_useful_link','temporal_conflict'}
        if not isinstance(data['checks'],dict) or set(data['checks'])!=fields:return 'MISSING_FIELDS'
        if any(type(v) is not bool for v in data['checks'].values()):return 'INVALID_SCHEMA'
    return None


def score_c(data,qcore,ccore):
    c=data['checks']
    if ccore['execution']!='CONFIRMED' or ccore['action'] is None or not c['actual_work_known']:
        return None,[]
    conflict=c['temporal_conflict'] or {qcore['time_type'],ccore['time_type']}=={'CURRENT','FUTURE'}
    guard=[]
    if conflict and (c['direct_core'] or c['transfer_core']):guard.append('CURRENT_NOT_FUTURE')
    if data['new_core_functions'] and (c['direct_core'] or c['transfer_core']):guard.append('UNIMPLEMENTED_CORE_FUNCTION')
    if c['direct_core'] and all(c[f] for f in ('action_match','object_match','output_match')) and not conflict and not data['new_core_functions']:
        if ccore['output'] is None:return None,['DIRECT_OUTPUT_UNSUPPORTED']
        return 3,guard
    if c['transfer_core'] and c['core_sufficient'] and not conflict and not data['new_core_functions']:
        return 2,guard
    return (1 if c['auxiliary_only'] or c['any_useful_link'] else 0),guard


def evaluate_item(item,method):
    identifier=item['id'];case=item['case'];available=anchors(case)
    q=c=None
    if method in ('B','C'):
        q=query_core(item['text']);c=case_core(case)
        if not q['valid'] or not c['valid']:
            return {'id':identifier,'method':method,'grade':None,'status':'UNJUDGED',
                    'failure':'CORE_EXTRACTION_FAILED','query_core':q,'case_core':c,'human_approved':False}
    payload={'id':identifier,'query_id':identifier,'business_problem':item['text'],'case':case,'anchors':available}
    if method=='A':
        payload={'query_id':identifier,'business_problem':item['text'],'cases':[{'id':identifier,**case}]}
    else:payload.update(query_core=q['data'],case_core=c['data'])
    result=request('judge_'+method+'_'+identifier,getattr(prompts,method),payload,1600 if method=='A' else 1000,
                   lambda d:check_decision(d,identifier,method,available,item['text']))
    grade=None;guard=[];status='UNJUDGED';citations=[];reason=''
    if result['valid']:
        d=result['data'];status='ABSTAIN'
        if method=='A':
            d=d['assessments'][0]
            grade=SCOPE[d['scope']] if d['category']=='JUDGEABLE' else None
            citations=d['_citations']
        elif method=='B':
            grade=d['grade'] if d['status']=='JUDGED' and c['data']['execution']=='CONFIRMED' and c['data']['action'] is not None else None
            citations=d['evidence_ids']
        else:
            grade,guard=score_c(d,q['data'],c['data']);citations=d['evidence_ids']
        reason=d['reason']
        if grade is not None and not citations:
            grade=None;guard.append('MISSING_PERFORMED_EVIDENCE')
        status='JUDGED' if grade is not None else 'ABSTAIN'
    return {'id':identifier,'method':method,'grade':grade,'status':status,'failure':result['failure'],
            'reason':reason,'citations':[{'anchor_id':a,**available[a]} for a in citations],
            'policy_guards':guard,'raw_decision':result,'query_core':q,'case_core':c,
            'human_approved':False,'label_source':'AI-Silver provisional'}


def benchmark(provider):
    configure(provider);items=read(OUT/'benchmark.json')['records']
    results=[]
    for item in items:
        for method in 'ABC':
            record=evaluate_item(item,method);results.append(record)
            print(provider,item['id'],method,record['grade'],record['status'],flush=True)
    write(OUT/provider/'benchmark_results.json',{'records':results,'human_approved':False})


def pending(provider):
    configure(provider);choice=read(OUT/'method_selection.json')['method']
    results=[]
    for item in read(OUT/'pending_items.json')['records']:
        record=evaluate_item(item,choice);results.append(record)
        print(provider,item['id'],choice,record['grade'],record['status'],flush=True)
    write(OUT/provider/'pending_results.json',{'records':results,'human_approved':False})


def aggregate_cost():
    rows=[]
    for provider in CAPS:
        directory=OUT/provider/'api'
        rows.extend(read(p) for p in sorted(directory.glob('*_receipt.json')))
    return {'calls':rows,'call_count':len(rows),
            'estimated_usd':str(sum((Decimal(x.get('cost_usd','0')) for x in rows),Decimal())),
            'spent_or_reserved_usd':str(sum((Decimal(x['held_or_cost_usd']) for x in rows),Decimal())),
            'unconfirmed_reserved_usd':str(sum((Decimal(x['held_or_cost_usd']) for x in rows if x['state']!='RECEIVED'),Decimal())),
            'work_cap_usd':2,'provider_caps':{k:str(v) for k,v in CAPS.items()}}


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('stage',choices=['benchmark','pending']);parser.add_argument('--provider',choices=list(CAPS),required=True)
    args=parser.parse_args()
    (benchmark if args.stage=='benchmark' else pending)(args.provider)
