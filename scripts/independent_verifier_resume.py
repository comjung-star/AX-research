"""One bounded recovery from explicit HTTP429; never replay transport-unknowns."""
import time
from decimal import Decimal
from scripts import independent_verifier_v3 as prev
v=prev.v;V3=v.OUT;ROOTS=(prev.V1,prev.V2,V3)
v.OUT=prev.V1/'rate-resume-v4';v.r.OUT=v.OUT
TRANSPORT=v.api.transport
def transport(p,body,counting):
    if p=='gemini' and not counting:time.sleep(10)
    return TRANSPORT(p,body,counting)
v.api.transport=transport
def spent(p):
    total=Decimal(0)
    for root in (*ROOTS,v.OUT):
        for f in (root/'attempts'/p).glob('*.json'):
            d=v.api.read_json(f);total+=Decimal((d.get('usage') or {}).get('usage_cost_usd',d.get('reserved_usd','0')))
    return total
v.r.spent=spent
JOBS=v.jobs
def jobs(plan,phase):
    js=JOBS(plan,phase)
    if phase=='panel':
        js.sort(key=lambda j:(0 if int(j['job_id'].split('_')[1])>=15 else 1,j['job_id']))
    return js
v.jobs=jobs
def recover():
    if (v.OUT/'recovery.json').exists():return
    uncertain=[]
    for root in ROOTS:
        for f in (root/'attempts').rglob('*.json'):
            d=v.api.read_json(f)
            if d.get('state')=='UNCERTAIN_FAILURE':
                if d.get('http_status')!=429:raise ValueError('Transport-unknown/non-rate failure: no replay')
                uncertain.append({'source':str(f.relative_to(v.ROOT)).replace('\\','/'),'http_status':429,'reserved_usd':d['reserved_usd'],'rule':'One bounded retry after elapsed cooldown; original full reservation retained, not claimed unbilled. Official Gemini troubleshooting recommends backoff for429; stop on recurrence.'})
    plan=v.prepare();recovered=0
    for phase in ('panel','stability','pilot'):
        for j in jobs(plan,phase):
            target=v.OUT/'results'/j['provider']/(j['job_id']+'.json')
            for root in reversed(ROOTS):
                f=root/'results'/j['provider']/(j['job_id']+'.json')
                if not f.exists():continue
                d=v.api.read_json(f);checked=v.validate(d.get('response_text',''),j)
                if checked['valid']:
                    v.save(target,{**d,'validation':checked,'known_response_reused_without_new_call':True,'original_source':str(f.relative_to(v.ROOT)).replace('\\','/'),'revalidated_against_input_version':j['input_version']});recovered+=1;break
    b=v.api.read_json(V3/'budget.json');v.save(v.OUT/'budget.json',b)
    v.save(v.OUT/'recovery.json',{'explicit_rejections':uncertain,'known_responses_reused':recovered,'cooldown':'Several minutes elapsed since v3 rejection; Gemini generation now has additional10s spacing. One recovery only. No original halt or attempt is changed.'})
if __name__=='__main__':
    import sys
    if len(sys.argv)>1 and sys.argv[1]=='recover':recover()
    else:v.main()
