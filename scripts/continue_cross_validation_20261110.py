"""Execution-only amendment: retain valid rows, recover only invalid rows once."""
import argparse
import hashlib
import json
import time
import urllib.request
import urllib.error
from pathlib import Path
from scripts import independent_cross_validation_20261110 as core

OUT=core.OUT

def accepted(receipt,payload):
    if 'raw' not in receipt:return {},[]
    try: parsed=core.parse(receipt['provider'],receipt['raw'])
    except Exception:return {},[{'error':'response not complete JSON'}]
    facts={x['case_id']:x for x in payload['cases']};seen=set();good={};bad=[]
    for row in parsed.get('judgments',[]):
        c=row.get('case_id')
        if c not in facts or c in seen:
            bad.append({'case_id':c,'error':'unknown or duplicate ID'});continue
        seen.add(c)
        try:core.validate({'judgments':[row]},{'cases':[facts[c]]});good[c]=row
        except Exception as e:bad.append({'case_id':c,'error':str(e)})
    for c in facts.keys()-seen:bad.append({'case_id':c,'error':'missing ID'})
    return good,bad

def amend():
    core.verify_frozen()
    p=OUT/'execution-amendment.json'
    assert not p.exists()
    core.save(p,{'at':core.stamp(),'reason':'User requires reuse of valid results and avoidance of duplicate grading. Whole-batch quote validation failed in8/23firstGemini rows;15rows individually valid. No performance/OpenAIlabels inspected.',
       'changes':['Keep every individually valid first-attempt row and never overwrite/regrade it.',
       'For each batch, at most one technical retry containing only failed/missing rows with identical per-pair facts, system prompt, schema, model and output cap. Batch membership changes, so this is not byte-identical full-request replay.',
       'Continue to other untouched question batches after quote-format errors, retaining failed rows as MISSING_VALID_EVIDENCE, not0/ABSTAIN. Stop immediately on HTTP/auth/credit/quota/unknown-delivery/budget failure.',
       'Original whole-batch stop/byte-identical recovery wording superseded only to honor valid-row reuse. No rubric, threshold, question, algorithm,rank,source facts or analysis/decision policy changes.'],
       'budget_cap_usd':core.BUDGET,'max_calls_per_provider':40,'max_accepted_judgments_per_pair':1,'min_gemini_interval_seconds':60,
       'self_sha256':core.sha(__file__),'frozen_original_runner_sha256':core.sha(core.__file__)})

def request(provider,q,payload,ident,reserve):
    dest=OUT/'api'/f'{provider}_{ident}.response.json'
    if dest.exists():return core.read(dest)
    allreceipts=[core.read(p) for p in core.receipt_paths()]
    if sum(x['reserved_usd'] for x in allreceipts)+reserve>core.BUDGET:raise RuntimeError('Budget reservation cap')
    reqbody=core.body(provider,payload)
    core.save(dest.with_name(dest.name.replace('.response.','.request.')),{'provider':provider,'model':core.MODELS[provider],'body':reqbody,'body_sha256':hashlib.sha256(json.dumps(reqbody,ensure_ascii=False).encode()).hexdigest()})
    rec={'provider':provider,'question_id':q,'model_requested':core.MODELS[provider],'started_at':core.stamp(),'status':'STARTED','delivery_unknown':True,'reserved_usd':reserve,'pair_ids':[x['case_id'] for x in payload['cases']]};core.save(dest,rec)
    url='https://api.anthropic.com/v1/messages' if provider=='anthropic' else 'https://generativelanguage.googleapis.com/v1beta/models/'+core.MODELS[provider]+':generateContent'
    try:
        req=urllib.request.Request(url,data=json.dumps(reqbody).encode(),headers=core.headers(provider))
        with urllib.request.urlopen(req,timeout=240) as res:
            raw=json.loads(res.read());rec['rate_headers']={k:v for k,v in res.headers.items() if 'ratelimit' in k.lower() or k.lower()=='retry-after'}
        rec.update(raw=raw,delivery_unknown=False,model_returned=raw.get('model',raw.get('modelVersion','NOT_RETURNED')))
        u=raw.get('usage',{}) if provider=='anthropic' else raw.get('usageMetadata',{})
        if provider=='anthropic':i,o=u.get('input_tokens',0),u.get('output_tokens',0)
        else:i=u.get('promptTokenCount',0);o=max(u.get('totalTokenCount',0)-i,u.get('candidatesTokenCount',0)+u.get('thoughtsTokenCount',0))
        pi,po=core.PRICES[provider];rec['usage']={'raw':u,'input_tokens':i,'output_including_thinking':o,'estimated_cost_usd':(i*pi+o*po)/1e6}
        try:
            parsed=core.parse(provider,raw);core.validate(parsed,payload);rec.update(status='VALID',parsed=parsed)
        except Exception as e:rec.update(status='INVALID_OUTPUT',error=core.clean(type(e).__name__+': '+str(e)))
    except urllib.error.HTTPError as e:rec.update(status='HTTP_ERROR',http_status=e.code,error=core.clean(e.read().decode(errors='replace'))[:8000],delivery_unknown=False)
    except Exception as e:rec.update(status='TRANSPORT_ERROR',error=type(e).__name__)
    rec['finished_at']=core.stamp();core.save(dest,rec)
    print(json.dumps({'provider':provider,'question':q,'attempt':ident,'status':rec['status'],'http':rec.get('http_status'),'cost':rec.get('usage',{}).get('estimated_cost_usd'),'error':rec.get('error','')[:220]},ensure_ascii=False),flush=True)
    return rec

def run(provider):
    core.verify_frozen();am=core.read(OUT/'execution-amendment.json');assert am['self_sha256']==core.sha(__file__)
    conn=core.read(OUT/'connection'/f'{provider}.json')
    assert conn['status']=='MODEL_ACCESSIBLE'
    chosen={};details={};blocked=None;last=0
    def send(q,payload,ident):
        nonlocal last
        path=OUT/'api'/f'{provider}_{ident}.response.json'
        if path.exists():return core.read(path)
        # Persisted timestamps prevent unintended rapid calls across restarts.
        from datetime import datetime,timezone
        starts=[datetime.fromisoformat(core.read(p)['started_at']).timestamp() for p in core.receipt_paths() if p.name.startswith(provider+'_')]
        wait=max(0,60-(datetime.now(timezone.utc).timestamp()-max(starts))) if starts and provider=='gemini' else 0
        while wait>0:time.sleep(min(wait,30));wait=max(0,60-(datetime.now(timezone.utc).timestamp()-max(starts)))
        b=core.body(provider,payload);pi,po=core.PRICES[provider];reserve=((len(json.dumps(b,ensure_ascii=False).encode())+8192)*pi+core.CAP*po)/1e6
        return request(provider,q,payload,ident,reserve)
    for p in sorted((OUT/'blind-inputs').glob('*.json')):
        q=p.stem;payload=core.read(p)
        rec=send(q,payload,q)
        if rec['status'] not in ('VALID','INVALID_OUTPUT'):
            blocked={'question_id':q,'status':rec['status'],'reason':rec.get('error','')};break
        good,bad=accepted(rec,payload);origin={c:q for c in good};remaining=[x for x in payload['cases'] if x['case_id'] not in good]
        if remaining:
            subset={**payload,'cases':remaining};recovery=send(q,subset,q+'_technical1')
            if recovery['status'] not in ('VALID','INVALID_OUTPUT'):
                blocked={'question_id':q,'status':recovery['status'],'reason':recovery.get('error','')}
            extra,fail=accepted(recovery,subset)
            assert not good.keys()&extra.keys()
            good.update(extra);origin.update({c:q+'_technical1' for c in extra});bad=fail
        chosen[q]={'judgments':[good[c] for c in sorted(good)]}
        details[q]={'accepted':len(good),'expected':len(payload['cases']),'accepted_attempt':origin,'remaining_validation_failures':bad}
        core.save(OUT/f'{provider}-accepted-labels.json',chosen);core.save(OUT/f'{provider}-coverage.json',details)
        print(json.dumps({'question':q,'accepted_pairs':len(good),'expected_pairs':len(payload['cases'])},ensure_ascii=False),flush=True)
        if blocked:break
    complete=sum(x['accepted']==x['expected'] for x in details.values())
    core.save(OUT/f'{provider}-run-amended.json',{'status':'COMPLETE' if len(details)==complete==20 else 'BLOCKED' if blocked else 'PARTIAL_EVIDENCE','at':core.stamp(),'completed_questions':complete,'attempted_questions':len(details),'judged_pairs':sum(x['accepted'] for x in details.values()),'blocked':blocked})

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['amend','run']);parser.add_argument('--provider',choices=list(core.MODELS));a=parser.parse_args()
    if a.action=='amend':amend()
    else:run(a.provider)
