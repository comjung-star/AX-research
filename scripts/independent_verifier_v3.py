"""Explicit empty-case example and larger output allowance; no semantic tuning."""
from decimal import Decimal
from scripts import independent_verifier_v2 as prev
v=prev.v;V1=prev.V1;V2=v.OUT
v.OUT=V1/'format-v3';v.r.OUT=v.OUT
v.SYSTEM+=' Exact empty-case example: {"qid":"copy","target":"copy","reviewed":["supplied requirement ID"],"items":[{"id":"supplied CASE ID","links":[],"extra":[]}]}. Even an unrelated case MUST appear once with links:[]; items:[] is forbidden when cases are supplied. Keep one case item, not one item per requirement. Additional source condition belongs in extra, never appended to a link.'
MAKE=v.make_job
def make_job(*args,**kwargs):
    j=MAKE(*args,**kwargs);j['output_cap']=384*len(j['items'])+128;j['input_version']=v.digest({k:x for k,x in j.items() if k!='input_version'});return j
v.make_job=make_job
def spent(p):
    amount=Decimal(0)
    for root in (V1,V2,v.OUT):
        for f in (root/'attempts'/p).glob('*.json'):
            d=v.api.read_json(f);amount+=Decimal((d.get('usage') or {}).get('usage_cost_usd',d.get('reserved_usd','0')))
    return amount
v.r.spent=spent
def recover():
    plan=v.prepare()
    for phase in ('panel','stability','pilot'):
        for j in v.jobs(plan,phase):
            dest=v.OUT/'results'/j['provider']/(j['job_id']+'.json')
            if dest.exists():continue
            for root in (V2,V1):
                sources=[root/'results'/j['provider']/(j['job_id']+'.json')]
                sources+=sorted((root/'attempts'/j['provider']).glob(j['job_id']+'_a*.json'),reverse=True)
                done=False
                for f in sources:
                    if not f.exists():continue
                    d=v.api.read_json(f)
                    if d.get('state')!='RECEIVED' or not d.get('usage'):continue
                    checked=v.validate(d.get('response_text',''),j)
                    if checked['valid']:
                        v.save(dest,{**d,'validation':checked,'known_response_reused_without_new_call':True,'original_source':str(f.relative_to(v.ROOT)).replace('\\','/'),'revalidated_against_input_version':j['input_version'],'format_revision':'v3 retains valid earlier responses unchanged; empty-case example, output allowance and reason bound are technical changes only.'});done=True;break
                if done:break
    old=v.api.read_json(V1/'budget.json')
    v.save(v.OUT/'budget.json',{**old,'small_validation_fits':True,'small_validation_hard_cap_usd':'0.50','full_plan_fits':False,'format_revision':'v3 exact request count and reservation before dispatch; cumulative cap0.50 includes all v1/v2 failures. Output allowance raised to avoid truncation. Original full forecast is not an exact v3 forecast.'})
if __name__=='__main__':
    import sys
    if len(sys.argv)>1 and sys.argv[1]=='recover':recover()
    else:v.main()
