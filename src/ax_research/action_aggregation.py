"""Purpose filtering and one function-anchored aggregation; no file I/O."""
import copy
import re
from ax_research.semantic_mapping import aggregate,combined_score


def marker_spans(text,pattern):
    spans=[]
    for m in re.finditer(pattern,text,re.I):
        stop=re.search(r'[,;。；.\n]',text[m.end():])
        end=m.end()+stop.start() if stop else len(text)
        spans.append({'quote':text[m.start():end],'start':m.start(),'end':end,'marker':m.group()})
    return spans


def purpose_filter(profile,config):
    """Only remove unsupported old candidates; never infer new operations."""
    p=copy.deepcopy(profile);text=p['text'];executed=p['executed_evidence_required']
    cues=[{'quote':m.group(),'start':m.start(),'end':m.end()} for m in re.finditer(config['validation_purpose_pattern'],text,re.I) if not text[m.end():].startswith(config['purpose_modifier_suffix'])]
    purpose=marker_spans(text,config['purpose_marker_pattern']);inputs=marker_spans(text,config['input_marker_pattern'])
    kept=[];held=[]
    for f in p['functions']:
        why=None;fid=f['function'];a=f['action'];o=f['object'];cl=f['clause']
        eligible=[s for s in cues if not executed or (cl['start']<=s['start'] and s['end']<=cl['end'])]
        if fid=='validate_record':
            if executed and (text[a['end']:].startswith(config['purpose_modifier_suffix']) or any(s['start']<=a['start']<s['end'] for s in purpose)):
                why='PURPOSE_ONLY_NOT_EXECUTED_VALIDATION'
            elif not eligible:why='NO_EXPLICIT_VALIDATION_PURPOSE'
        elif fid=='generate_content' and any(s['start']<=o['start']<s['end'] for s in inputs):
            why='MATCHED_CONTENT_IS_INPUT_NOT_GENERATED_OUTPUT'
        f['actual_output_status']='UNKNOWN_UNLESS_SEPARATELY_LITERAL'
        f['validation_purpose_evidence']=eligible if fid=='validate_record' else []
        if why:held.append({'function':fid,'reason':why,'old_evidence':f})
        else:kept.append(f)
    p['functions']=kept;p['function_ids']=sorted({f['function'] for f in kept})
    removed={f['function'] for f in held}-set(p['function_ids'])
    p['action_family_hits']=[f for f in p['action_family_hits'] if f not in removed and (f!='validate_record' or cues)]
    p['status']='RECOGNIZED_RULE_FUNCTIONS' if kept else 'UNKNOWN_NO_SUPPORTED_FUNCTION'
    p['purpose_audit']={'held':held,'validation_cues':cues,'purpose_spans':purpose,'input_spans':inputs,'reading_cues':[m.group() for m in re.finditer(config['reading_pattern'],text,re.I)],'actual_output_status':'UNKNOWN_UNLESS_SEPARATELY_LITERAL','source_only':True}
    return p


def allowed_branches(original,branches,case_task):
    core=set(original['function_ids'])&set(case_task['function_ids'])
    return {pid:sorted(core&set(p['function_ids'])) for pid,p in branches.items() if core&set(p['function_ids'])}


def compose(whole_grade,branch_grades,whole_semantic,branch_semantics,allowed=None,*,no_embedding=False):
    selected=list(branch_grades) if allowed is None else [p for p in branch_grades if p in allowed]
    strength=max([whole_grade]+[branch_grades[p] for p in selected])
    semantic=aggregate(whole_semantic,[branch_semantics[p] for p in selected])
    norm=.5 if no_embedding else (semantic+1)/2
    return {'score':.5*strength/4+.5*norm,'rule_strength':strength,'semantic':semantic,'rule_contribution':.5*strength/4,'embedding_contribution':.5*norm,'allowed_paths':selected,'rule_winner_paths':[p for p in selected if branch_grades[p]==strength], 'semantic_winner_paths':[p for p in selected if branch_semantics[p]==max((branch_semantics[x] for x in selected),default=whole_semantic)],'original_fallback':not selected,'embedding_neutralized':no_embedding}
