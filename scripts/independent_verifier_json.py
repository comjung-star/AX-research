"""Extract a complete fenced JSON block, preserving and flagging extra prose."""
import re
from decimal import Decimal
from scripts import independent_verifier_binding as prev
v=prev.v;V5=v.OUT;ROOTS=(*prev.ROOTS,V5)
v.OUT=ROOTS[0]/'json-normalization-v6';v.r.OUT=v.OUT
VALIDATE=v.validate;LEGACY=prev.OLD_VALIDATE;MAKE=v.make_job
def validate(text,j):
    raw=text.strip();match=re.match(r'\A```json\s*([\s\S]*?)```',raw)
    content=match.group(1).strip() if match else raw
    d=VALIDATE(content,j)
    if d['valid']:
        trailing=raw[match.end():].strip() if match else ''
        d['extra_prose_present']=bool(trailing)
        d['extra_prose_requires_source_audit']=trailing
        d['normalization']='Complete fenced JSON only; no values invented or truncated. Raw response preserved.'
    return d
v.validate=validate;v.r.validate=validate
def make_job(*args,**kwargs):
    j=MAKE(*args,**kwargs);j['system']+=' Emit JSON only, no Markdown, no text before or after JSON. Put any functional reason only in its JSON reason field.';j['input_version']=v.digest({k:z for k,z in j.items() if k!='input_version'});return j
v.make_job=make_job
def spent(p):
    total=Decimal(0)
    for root in (*ROOTS,v.OUT):
        for f in (root/'attempts'/p).glob('*.json'):
            d=v.api.read_json(f);total+=Decimal((d.get('usage') or {}).get('usage_cost_usd',d.get('reserved_usd','0')))
    return total
v.r.spent=spent
def recover():
    plan=v.prepare()
    for phase in ('panel','stability','pilot'):
        for j in v.jobs(plan,phase):
            target=v.OUT/'results'/j['provider']/(j['job_id']+'.json')
            if target.exists():continue
            done=False
            for root in reversed(ROOTS):
                paths=[root/'results'/j['provider']/(j['job_id']+'.json')]
                paths+=sorted((root/'attempts'/j['provider']).glob(j['job_id']+'_a*.json'),reverse=True)
                for f in paths:
                    if not f.exists():continue
                    d=v.api.read_json(f)
                    if d.get('state')!='RECEIVED' or not d.get('usage'):continue
                    checked=validate(d.get('response_text',''),j)
                    if not checked['valid']:checked=LEGACY(d.get('response_text',''),j)
                    if checked['valid']:
                        v.save(target,{**d,'validation':checked,'known_response_reused_without_new_call':True,'original_source':str(f.relative_to(v.ROOT)).replace('\\','/'),'revalidated_against_input_version':j['input_version'],'normalization_revision':'Complete existing JSON only, raw response retained; any outside prose is separately flagged for source audit. No generated ID, claim or score rewritten.'});done=True;break
                if done:break
    v.save(v.OUT/'budget.json',{**v.api.read_json(V5/'budget.json'),'format_revision':'v6 complete fenced JSON extraction; extra prose flagged, not approved. All earlier attempts included in cumulative validation cap0.50.'})
if __name__=='__main__':
    import sys
    if len(sys.argv)>1 and sys.argv[1]=='recover':recover()
    else:v.main()
