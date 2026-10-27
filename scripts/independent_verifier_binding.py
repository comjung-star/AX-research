"""Bind single-case responses to their sole request, not model-generated case IDs."""
import json
from decimal import Decimal
from scripts import independent_verifier_resume as prev
v=prev.v;V4=v.OUT;ROOTS=(*prev.ROOTS,V4)
v.OUT=ROOTS[0]/'single-case-binding-v5';v.r.OUT=v.OUT
OLD_VALIDATE=v.validate;OLD_MAKE=v.make_job
def make_job(*args,**kwargs):
    j=OLD_MAKE(*args,**kwargs)
    # Keep the semantic instructions; replace only the output interface.
    j['system']=v.SYSTEM.split('Return exactly')[0]+'''Review every requirement using explicit IDs. Return every real connection; omit unrelated links. A link is [requirement_ID,relation,actual_action,functional_object,produced_output,exact_Task_or_Context_quote,reason]. relation is DIRECT (functional equivalence), SUPPORT (concrete partial/upstream/downstream help), BROAD (wide operational resemblance). Each atom <=8 English words, reason <=32 English words. extra is [] or [exact_Problem_or_Context_quote,reason<=32words] for an additional query-matching concrete condition, never an inferred benefit. No scores, no invented functions. reviewed must list ALL supplied requirement IDs. Preserve qid and target. '''
    j['system']+=('The optional query-blind inventory is advisory; raw Task/Context is authoritative. ' if j['role']=='evaluation' else 'Blind independent review: no other model answer or inventory is supplied. ')
    if len(j['items'])==1:
        j['system']+='There is exactly ONE source case. Return exactly {"qid":"copy","target":"copy","reviewed":["all requirement IDs"],"links":[],"extra":[]}, replacing links with supported connections. No case ID or items array is needed; the request uniquely binds the source case. Unrelated case has links:[]; do not omit the root fields.'
    else:
        j['system']+='Return exactly {"qid":"copy","target":"copy","reviewed":["all requirement IDs"],"cases":{"EXACT_CASE_KEY":{"links":[],"extra":[]}}}. Include every supplied case key once even when links:[]. Never use a requirement ID as a case key.'
    j['input_version']=v.digest({k:z for k,z in j.items() if k!='input_version'});return j
v.make_job=make_job
def reject_duplicate_keys(pairs):
    d={}
    for k,z in pairs:
        if k in d:raise ValueError('DUPLICATE_JSON_KEY')
        d[k]=z
    return d
def validate(text,j):
    try:
        d=json.loads(text.strip().removeprefix('```json').removesuffix('```').strip(),object_pairs_hook=reject_duplicate_keys)
        assert d['qid']==j['qid'] and d['target']==j['target']
        if len(j['items'])==1:
            assert set(d)=={'qid','target','reviewed','links','extra'}
            rows=[{'id':next(iter(j['items'])),'links':d['links'],'extra':d['extra']}]
        else:
            assert set(d)=={'qid','target','reviewed','cases'} and set(d['cases'])==set(j['items'])
            rows=[]
            for cid,row in d['cases'].items():
                assert set(row)=={'links','extra'};rows.append({'id':cid,**row})
        checked=OLD_VALIDATE(json.dumps({'qid':d['qid'],'target':d['target'],'reviewed':d['reviewed'],'items':rows},ensure_ascii=False),j)
        if checked['valid']:checked['binding']='Sole request case' if len(j['items'])==1 else 'Exact case-key set'
        return checked
    except (ValueError,KeyError,TypeError,AssertionError,AttributeError):return {'valid':False,'data':None,'derived':None,'errors':['ROOT_CASE_BINDING_OR_JSON_FORMAT']}
v.validate=validate;v.r.validate=validate
def spent(p):
    n=Decimal(0)
    for root in (*ROOTS,v.OUT):
        for f in (root/'attempts'/p).glob('*.json'):
            d=v.api.read_json(f);n+=Decimal((d.get('usage') or {}).get('usage_cost_usd',d.get('reserved_usd','0')))
    return n
v.r.spent=spent
def recover():
    plan=v.prepare()
    for phase in ('panel','stability','pilot'):
        for j in v.jobs(plan,phase):
            path=v.OUT/'results'/j['provider']/(j['job_id']+'.json')
            if path.exists():continue
            for root in reversed(ROOTS):
                f=root/'results'/j['provider']/(j['job_id']+'.json')
                if not f.exists():continue
                d=v.api.read_json(f);valid=OLD_VALIDATE(d.get('response_text',''),j)
                if valid['valid']:
                    v.save(path,{**d,'validation':valid,'known_response_reused_without_new_call':True,'original_source':str(f.relative_to(v.ROOT)).replace('\\','/'),'revalidated_against_input_version':j['input_version'],'binding_revision':'Earlier validated case-ID response retained without alteration. New single-case requests use sole-case request binding.'});break
    v.save(v.OUT/'budget.json',{**v.api.read_json(V4/'budget.json'),'format_revision':'v5 root interface; exact token count and maximum reservation per request; all previous costs and unknown reservations included in hard0.50 validation cap.'})
if __name__=='__main__':
    import sys
    if len(sys.argv)>1 and sys.argv[1]=='recover':recover()
    else:v.main()
