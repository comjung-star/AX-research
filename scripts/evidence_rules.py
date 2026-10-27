"""Scores from source-linked semantic evidence, never from model score fields."""
import re
from scripts import aoo_experiment as old

CFG=old.api.read_json(old.ROOT/'configs/evidence_rules_20261027.json')

def parse_evidence(data,job):
    if set(data)!={'qid','target','items'} or data['qid']!=job['qid'] or data['target']!=job['target']:
        raise ValueError('QUERY_OR_SCOPE_MAPPING')
    rows=data['items']
    if not isinstance(rows,list) or len(rows)!=len(job['items']):raise ValueError('MISSING_ITEMS')
    if len({r.get('id') for r in rows})!=len(rows) or {r.get('id') for r in rows}!=set(job['items']):raise ValueError('DUPLICATE_OR_WRONG_CASE_ID')
    for r in rows:
        if set(r)!={'id','ops','links'}:raise ValueError('UNKNOWN_KEYS_OR_MODEL_SCORE')
        c=job['items'][r['id']]
        if not isinstance(r['ops'],list) or len(r['ops'])>4 or not isinstance(r['links'],list):raise ValueError('ARRAY_FORMAT')
        for op in r['ops']:
            if not isinstance(op,list) or len(op)!=5 or not all(isinstance(v,str) and v.strip() for v in op):raise ValueError('OP_FORMAT')
            family,action,obj,output,quote=op
            if family not in CFG['families']:raise ValueError('UNKNOWN_FAMILY')
            if len(quote)<2 or not any(quote in c[f] for f in ('task','context')):raise ValueError('OP_NOT_STATED_IN_TASK_OR_CONTEXT')
            if any(len(v.split())>10 for v in (action,obj,output)):raise ValueError('ATOM_TOO_LONG')
        seen=set()
        for link in r['links']:
            if not isinstance(link,list) or len(link)!=5:raise ValueError('LINK_FORMAT')
            tid,index,mask,relation,why=link
            if tid not in job['tasks'] or type(index)is not int or index not in range(len(r['ops'])):raise ValueError('BAD_OP_OR_TARGET_LINK')
            if (tid,index) in seen:raise ValueError('DUPLICATE_LINK')
            seen.add((tid,index))
            if not isinstance(mask,str) or not re.fullmatch('[ESD]{3}',mask) or relation not in ('DIRECT','SUPPORT','BROAD'):raise ValueError('BAD_SEMANTIC_RELATION')
            if not isinstance(why,str) or not 1<=len(why.split())<=18:raise ValueError('REASON_LENGTH')
            if re.search(r'\b(reduc\w*|improv\w*|free[sd]?|freeing|boost\w*|sav\w*)\s+(staff|support|workload|capacity|time|cost|quality)',why,re.I):raise ValueError('UNSTATED_EFFECT_REASON')
    return rows

def score(row,job):
    c=job['items'][row['id']];direct=[];support=[];broad=[];flags=[]
    for tid,i,mask,relation,why in row['links']:
        family,a,o,y,quote=row['ops'][i]
        if relation=='DIRECT' and mask=='EEE':
            if family not in CFG['target_families'][tid]:
                flags.append({'kind':'INCOMPATIBLE_DIRECT_FAMILY','target':tid,'family':family,'op':i});continue
            direct.append({'target':tid,'op':i,'family':family,'quote':quote,'why':why})
        elif relation=='SUPPORT' and any(x in mask for x in 'ES'):
            support.append({'target':tid,'op':i,'mask':mask,'why':why})
        elif any(x in mask for x in 'ES'):broad.append({'target':tid,'op':i,'why':why})
    if flags:return {'score':None,'relevant':None,'status':'HOLD_SEMANTIC_CONTRADICTION','flags':flags}
    value=3 if direct else 2 if support else 1 if broad else 0
    rule='GROUNDED_DIRECT_AOO' if direct else 'GROUNDED_SUPPORT' if support else 'BROAD_OPERATIONAL_LINK' if broad else 'NO_OPERATIONAL_LINK'
    fourth=[]
    if direct:
        for x in direct:
            for z in direct:
                if x['target']!=z['target'] and x['family']!=z['family'] and x['quote']!=z['quote']:
                    fourth.append({'type':'ADDITIONAL_DISTINCT_CORE_TASK','first':x,'second':z})
        for w in CFG['context_witnesses']:
            if w['qid']==job['qid'] and w['target']==job['target'] and w['cid']==row['id']:
                if w['quote'] not in c[w['field']]:raise ValueError('CURATED_CONTEXT_SOURCE_CHANGED')
                fourth.append({'type':'PREVERIFIED_PROBLEM_FACT','source':w})
        if fourth:value=4;rule='DIRECT_PLUS_GROUNDED_ADDITIONAL_EVIDENCE'
    return {'score':value,'relevant':value>=3,'status':'AI_EVIDENCE_PROGRAM_SCORE_NOT_HUMAN_GOLD','rule':rule,'direct':direct,'support':support,'broad':broad,'fourth_point_evidence':fourth,'flags':[]}
