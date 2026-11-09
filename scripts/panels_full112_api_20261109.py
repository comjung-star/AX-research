"""Isolated bounded API transport; credentials never serialized, no implicit retries."""
import json
import os
import time
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/perspective-panels-full112-20261109'
PRICES={'openai':(2.5,15.0),'anthropic':(2.0,10.0),'gemini':(.5,3.0)}
MODELS={'openai':'gpt-5.4','anthropic':'claude-sonnet-5-5','gemini':'gemini-3-flash-preview'}
BUDGET=15.0

def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')

def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def obj(props):return {'type':'object','properties':props,'required':list(props),'additionalProperties':False}
STR={'type':'string'}

def body(provider,system,payload,schema,cap):
    text=json.dumps(payload,ensure_ascii=False)
    if provider=='openai':
        return {'model':MODELS[provider],'instructions':system,'input':text,'store':False,
            'reasoning':{'effort':'medium'},'max_output_tokens':cap,
            'text':{'format':{'type':'json_schema','name':'research_output','strict':True,'schema':schema}}}
    if provider=='anthropic':
        return {'model':MODELS[provider],'system':system,'messages':[{'role':'user','content':text}],
            'max_tokens':cap,'output_config':{'effort':'high','format':{'type':'json_schema','schema':schema}}}
    return {'systemInstruction':{'parts':[{'text':system}]},'contents':[{'role':'user','parts':[{'text':text}]}],
        'generationConfig':{'maxOutputTokens':cap,'responseMimeType':'application/json','responseJsonSchema':schema,
                            'thinkingConfig':{'thinkingLevel':'high'}}}

def parse(provider,raw):
    if provider=='openai':
        if raw.get('status')!='completed':raise ValueError('response not completed: '+str(raw.get('incomplete_details')))
        text=''.join(c.get('text','') for o in raw['output'] if o.get('type')=='message' for c in o['content'] if c.get('type')=='output_text')
    elif provider=='anthropic':
        if raw.get('stop_reason')!='end_turn':raise ValueError('stop_reason '+str(raw.get('stop_reason')))
        text=''.join(c.get('text','') for c in raw['content'] if c['type']=='text')
    else:
        c=raw['candidates'][0]
        if c.get('finishReason')!='STOP':raise ValueError('finishReason '+str(c.get('finishReason')))
        text=''.join(p.get('text','') for p in c['content']['parts'] if not p.get('thought'))
    return json.loads(text)

def usage(provider,raw):
    if provider=='gemini':
        u=raw.get('usageMetadata',{});i=u.get('promptTokenCount',0)
        o=max(u.get('totalTokenCount',0)-i,u.get('candidatesTokenCount',0)+u.get('thoughtsTokenCount',0))
    else:
        u=raw.get('usage',{});i=u.get('input_tokens',0);o=u.get('output_tokens',0)
    a,b=PRICES[provider]
    return {'input_tokens':i,'output_tokens':o,'known_cost_usd':(i*a+o*b)/1e6}

def ledger():
    items=[read(p) for p in (OUT/'api').glob('*.json') if not p.name.endswith('.request.json')]
    return {'attempts':len(items),'known_cost_usd':sum(x.get('usage',{}).get('known_cost_usd',0) for x in items),
        'reserved_usd':sum(x.get('reserved_usd',0) for x in items),'budget_usd':BUDGET,
        'unresolved_deliveries':[x['id'] for x in items if x.get('delivery_unknown')]}

def call(provider,ident,system,payload,schema,cap=4096):
    path=OUT/'api'/f'{provider}_{ident}.json'
    if path.exists():return read(path)
    reqbody=body(provider,system,payload,schema,cap)
    # Conservative UTF8-byte token bound plus output cap. Reservations never released.
    nbytes=len(json.dumps(reqbody,ensure_ascii=False).encode('utf-8'));a,b=PRICES[provider]
    reserve=(nbytes*a+cap*b)/1e6
    if ledger()['reserved_usd']+reserve>BUDGET:raise RuntimeError('Predeclared budget exceeded')
    stamp=lambda:datetime.now(timezone.utc).isoformat()
    record={'id':f'{provider}_{ident}','provider':provider,'model':MODELS[provider],
            'started_at':stamp(),'reserved_usd':reserve,'delivery_unknown':True,'status':'STARTED'}
    save(path.with_name(path.stem+'.request.json'),{'system':system,'payload':payload,'schema':schema,'body':reqbody})
    save(path,record)
    keyname={'openai':'OPENAI_API_KEY','anthropic':'ANTHROPIC_API_KEY','gemini':'GEMINI_API_KEY'}[provider]
    key=os.environ[keyname]
    urls={'openai':'https://api.openai.com/v1/responses','anthropic':'https://api.anthropic.com/v1/messages',
          'gemini':f'https://generativelanguage.googleapis.com/v1beta/models/{MODELS[provider]}:generateContent'}
    headers={'Content-Type':'application/json'}
    if provider=='openai':headers['Authorization']='Bearer '+key
    elif provider=='anthropic':headers.update({'x-api-key':key,'anthropic-version':'2023-06-01'})
    else:headers['x-goog-api-key']=key
    try:
        req=urllib.request.Request(urls[provider],data=json.dumps(reqbody).encode(),headers=headers)
        with urllib.request.urlopen(req,timeout=210) as response:raw=json.loads(response.read())
        record.update({'raw':raw,'usage':usage(provider,raw),'delivery_unknown':False})
        try:record.update({'parsed':parse(provider,raw),'status':'VALID_JSON'})
        except Exception as e:record.update({'status':'INVALID_OUTPUT','error':str(e)})
    except urllib.error.HTTPError as e:
        detail=e.read().decode('utf-8',errors='replace')
        for name in ('OPENAI_API_KEY','ANTHROPIC_API_KEY','GEMINI_API_KEY'):
            secret=os.getenv(name)
            if secret:detail=detail.replace(secret,'[REDACTED]')
        record.update({'status':'HTTP_ERROR','http_status':e.code,'error':detail[:4000],'delivery_unknown':False})
    except Exception as e:record.update({'status':'TRANSPORT_ERROR','error':type(e).__name__})
    record['finished_at']=stamp();save(path,record)
    print(json.dumps({'id':record['id'],'status':record['status'],'cost':record.get('usage',{}).get('known_cost_usd'),
                      'error':record.get('error','')[:250]},ensure_ascii=False),flush=True)
    return record

if __name__=='__main__':
    import sys
    if sys.argv[1]=='preflight':
        for provider in ('anthropic','openai','gemini'):
            call(provider,'preflight','Return exactly the requested JSON object.',{'instruction':'Set ok true.'},obj({'ok':{'type':'boolean'}}),512)
        print(json.dumps(ledger()),flush=True)
