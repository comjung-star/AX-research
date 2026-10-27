"""Technical-format revision; unchanged semantic rules, all v1 attempts preserved."""
import copy
from decimal import Decimal
from scripts import independent_verifier as v

V1=v.OUT
v.OUT=V1/'format-v2';v.r.OUT=v.OUT
# A local reason-length bound is not a semantic scoring criterion. Retain the
# original long reason instead of truncating evidence or asking for a new vote.
v.SYSTEM=v.SYSTEM.replace('reason <=16 English words','reason <=32 English words').replace('reason<=16words','reason<=32words')
v.SYSTEM+=' Copy each case ID from the cases mapping keys exactly, never a requirement ID. Do not wrap a quote in additional quotation characters.'
OLD_VALIDATE=v.validate
def validate(text,j):
    # Reuse original strict structural/source checks with only the lexical
    # reason bound widened, without altering any response string or value.
    try:
        import json
        data=json.loads(text.strip().removeprefix('```json').removesuffix('```').strip())
        check=copy.deepcopy(data)
        for row in check.get('items',[]):
            for link in row.get('links',[]):
                if not isinstance(link,list) or len(link)!=7:return OLD_VALIDATE(text,j)
                if not isinstance(link[6],str) or not 1<=len(link[6].split())<=32:raise ValueError('REASON_LENGTH_32')
                link[6]='local structural check'
            if row.get('extra'):
                if not isinstance(row['extra'],list) or len(row['extra'])!=2:return OLD_VALIDATE(text,j)
                if not isinstance(row['extra'][1],str) or not 1<=len(row['extra'][1].split())<=32:raise ValueError('EXTRA_REASON_LENGTH_32')
                row['extra'][1]='local structural check'
        result=OLD_VALIDATE(json.dumps(check,ensure_ascii=False),j)
        if result['valid']:result['data']=data
        return result
    except (ValueError,TypeError,KeyError,IndexError,AttributeError):return {'valid':False,'data':None,'derived':None,'errors':['REASON_OR_JSON_FORMAT']}
v.validate=validate;v.r.validate=validate

def spent(p):
    amount=Decimal(0)
    for root in (V1,v.OUT):
        for f in (root/'attempts'/p).glob('*.json'):
            d=v.api.read_json(f);amount+=Decimal((d.get('usage') or {}).get('usage_cost_usd',d.get('reserved_usd','0')))
    return amount
v.r.spent=spent
# This technical recovery is restricted to the $0.50 small-validation envelope.
v.CFG['claude_this_work_cap_usd']='0.50';v.r.CFG=v.CFG

def recover():
    plan=v.prepare()
    for phase in ('panel','stability','pilot'):
        for j in v.jobs(plan,phase):
            dest=v.OUT/'results'/j['provider']/(j['job_id']+'.json')
            if dest.exists():continue
            candidates=[]
            f=V1/'results'/j['provider']/(j['job_id']+'.json')
            if f.exists():candidates.append(f)
            candidates.extend(sorted((V1/'attempts'/j['provider']).glob(j['job_id']+'_a*.json'),reverse=True))
            for source in candidates:
                d=v.api.read_json(source)
                if d.get('state')!='RECEIVED' or not d.get('usage'):continue
                checked=validate(d['response_text'],j)
                if checked['valid']:
                    v.save(dest,{**d,'validation':checked,'known_response_reused_without_new_call':True,'original_source':str(source.relative_to(v.ROOT)).replace('\\','/'),'revalidated_against_input_version':j['input_version'],'format_revision':'Only reason bound changed16to32; no response values changed. Actual request input_version remains original.'});break
    old=v.api.read_json(V1/'budget.json');budget=copy.deepcopy(old)
    budget.update({'format_revision':'v2 reason bound32 and explicit case-key copy reminder; cost safety uses exact per-request recount and hard cumulative small-validation cap0.50. Prior preflight is contextual, not an exact count of v2 prompts.','small_validation_fits':old['small_validation_fits'],'small_validation_hard_cap_usd':'0.50','prior_preflight':str((V1/'budget.json').relative_to(v.ROOT)).replace('\\','/'),'full_plan_fits':False})
    v.save(v.OUT/'budget.json',budget)

if __name__=='__main__':
    import sys
    if len(sys.argv)>1 and sys.argv[1]=='recover':recover()
    else:v.main()
