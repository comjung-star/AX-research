"""Separate conservative ablations; frozen original modules remain untouched."""
import copy
import re
from ax_research.functional_mapping import extract
from ax_research.semantic_mapping import combined_score


def expanded_rules(rules,config):
    result=copy.deepcopy(rules)
    for f in result['functions']:
        for key,extra in config['aliases'].get(f['id'],{}).items():
            if extra:f[key]='(?:'+f[key]+')|(?:'+extra+')'
    return result


def left_boundary_ok(text,start):
    """Do not recognize review inside preview, data inside metadata, etc."""
    return not (start>0 and text[start].isascii() and text[start].isalpha() and text[start-1].isascii() and text[start-1].isalpha())


def extract2(text,rules):
    # executed is passed by wrapper: output is functional type, never an observed output.
    return extract2_scope(text,rules,executed=False)


def extract2_scope(text,rules,*,executed=False):
    p=extract(text,rules,executed=executed)
    p['functions']=[f for f in p['functions'] if left_boundary_ok(text,f['action']['start']) and left_boundary_ok(text,f['object']['start'])]
    for f in p['functions']:
        f['output_status']='OPERATION_CATEGORY_ONLY_ACTUAL_OUTPUT_UNKNOWN'
    p['function_ids']=sorted({f['function'] for f in p['functions']})
    p['action_family_hits']=sorted(f['id'] for f in rules['functions'] if any(left_boundary_ok(text,m.start()) for m in re.finditer(f['action'],text,re.I)))
    p['status']='RECOGNIZED_RULE_FUNCTIONS' if p['functions'] else 'UNKNOWN_NO_SUPPORTED_FUNCTION'
    return p


def case_profile2(case,rules):
    return {k:extract2_scope(case[k],rules,executed=k=='task') for k in ('problem','task','context')}


def semantic2(old,query_known,case_known):
    if query_known and case_known:return old['score']
    task=old['components'].get('task')
    return task['cosine'] if task else -1.0


def combination_unknown(strength,semantic,known):
    return combined_score(strength,semantic) if known else (semantic+1)/2
