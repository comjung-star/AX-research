"""Untrained functional-production baseline. No model, files, IDs or labels."""
import re

def extract(text, rules, *, executed=False):
    functions=[];held=[]
    for clause in re.finditer(r'[^.;。；\n]+',text):
        raw=clause.group();offset=clause.start()
        if executed and re.search(rules['negation_guard'],raw,re.I):
            held.append({'quote':raw,'start':offset,'end':clause.end(),'reason':'negated_or_nonexecuted_clause'})
            continue
        for f in rules['functions']:
            am=list(re.finditer(f['action'],raw,re.I));om=list(re.finditer(f['object'],raw,re.I))
            pairs=[(a,o) for a in am for o in om if max(a.end(),o.end())-min(a.start(),o.start())<=rules['max_action_object_span']]
            if not pairs:continue
            a,o=min(pairs,key=lambda z:(max(z[0].end(),z[1].end())-min(z[0].start(),z[1].start()),z[0].start(),z[1].start()))
            def evidence(m):return {'quote':m.group(),'start':offset+m.start(),'end':offset+m.end()}
            functions.append({'function':f['id'],'action':evidence(a),'object':evidence(o),'clause':{'quote':raw,'start':offset,'end':clause.end()},'output_type':f['output'],'output_status':'OPERATION_TYPE_NOT_SEPARATELY_VERIFIED_OUTPUT','meaning':f['meaning']})
    domains={}
    for key,pat in rules['object_domains'].items():
        m=re.search(pat,text,re.I)
        if m:domains[key]={'quote':m.group(),'start':m.start(),'end':m.end()}
    actions=sorted({f['id']:True for f in rules['functions'] if re.search(f['action'],text,re.I)})
    return {'text':text,'functions':functions,'function_ids':sorted({f['function'] for f in functions}),'domains':domains,'action_family_hits':actions,'held_clauses':held,'status':'RECOGNIZED_RULE_FUNCTIONS' if functions else 'UNKNOWN_NO_SUPPORTED_FUNCTION','executed_evidence_required':executed}

def case_profile(case,rules):
    return {k:extract(case[k],rules,executed=k=='task') for k in ('problem','task','context')}

def compare(query, case):
    task=case['task'];q=set(query['function_ids']);t=set(task['function_ids']);shared=sorted(q&t)
    domains=sorted(set(query['domains'])&set(task['domains']))
    context_shared=sorted(q & (set(case['problem']['function_ids'])|set(case['context']['function_ids'])))
    if shared:grade=4 if domains and set(context_shared)&set(shared) else 3
    elif q and t and set(query['action_family_hits'])&set(task['action_family_hits']):grade=2
    elif domains:grade=1
    else:grade=0
    if not q or not t:grade=min(grade,1)
    status='SUPPORTED_FUNCTIONAL_OVERLAP' if shared else ('UNKNOWN' if not q or not t else 'NO_COMMON_RECOGNIZED_FUNCTION')
    return {'mapping_grade':grade,'status':status,'shared_functions':shared,'query_uncovered_functions':sorted(q-t),'case_other_functions':sorted(t-q),'recognized_query_function_coverage':len(shared)/len(q) if q else None,'shared_task_domains':domains,'problem_context_support_functions':context_shared,'criteria':{'Business Problem':{'shared_functions':sorted(q&set(case['problem']['function_ids'])),'licenses_execution':False},'AX Target / Task':{'shared_functions':shared,'execution_source':'task_only'},'Business Context':{'shared_domains':sorted(set(query['domains'])&set(case['context']['domains'])),'unknown_conditions':'No security, deployment or outcome facts inferred'},'Action':{'supported_production_ids':shared},'Object':{'functional_object_families':shared,'shared_domains':domains,'cross_industry_transfer_allowed':True},'Output':{'types':[f['output_type'] for f in task['functions'] if f['function'] in shared],'status':'NORMALIZED_OPERATION_TYPE_NOT_INDEPENDENT_OUTPUT_EVIDENCE'}},'reason':'Task 원문의 행동·대상 조합에서 규칙 근거 확인' if shared else 'No supported shared operation; unknown does not prove irrelevance'}

def ranking_key(whole,branches,retrieval_score,cid):
    best=max((b['mapping_grade'] for b in branches),default=0)
    return (-max(whole['mapping_grade'],best),-whole['mapping_grade'],-best,-retrieval_score,cid)
