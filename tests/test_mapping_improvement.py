import json
from pathlib import Path
import pytest
from ax_research.functional_mapping import extract,compare
from ax_research.mapping_improvement import *

ROOT=Path(__file__).resolve().parents[1]
old=json.loads((ROOT/'configs/functional_mapping_20261028.json').read_text(encoding='utf-8-sig'))
cfg=json.loads((ROOT/'configs/mapping_improvement_20261030.json').read_text(encoding='utf-8-sig'))
rules=expanded_rules(old,cfg)


def test_no_old_rule_mutation():
    assert len(rules['functions'])==len(old['functions'])==18
    assert next(f for f in old['functions'] if f['id']=='generate_content')['action']=='generat|draft|creat|write|작성|생성|제작'


@pytest.mark.parametrize('text,function',[
 ('Produce lifestyle images','generate_content'),('Reconcile bank transactions','validate_record'),
 ('Review merchant websites','validate_record'),('사내 데이터 조회','retrieve_knowledge'),
 ('Screen applicant self-introductions','validate_record')])
def test_generic_aliases(text,function):
    assert function not in extract(text,old,executed=True)['function_ids']
    p=extract2_scope(text,rules,executed=True)
    assert function in p['function_ids']
    for f in p['functions']:
        for key in ('action','object','clause'):
            s=f[key];assert text[s['start']:s['end']]==s['quote']
        assert f['output_status']=='OPERATION_CATEGORY_ONLY_ACTUAL_OUTPUT_UNKNOWN'


@pytest.mark.parametrize('text',['planned review of websites','does not produce images','자료 검토 예정','데이터 조회 필요하다'])
def test_nonexecuted(text):assert not extract2_scope(text,rules,executed=True)['function_ids']


def test_english_left_boundary():
    assert 'validate_record' not in extract2_scope('Preview websites',rules,executed=True)['function_ids']


@pytest.mark.parametrize('text',['Translate news articles','Unload cartons','Repair incomplete payment instructions','Book employee leave'])
def test_no_invented_function(text):assert not extract2_scope(text,rules,executed=True)['function_ids']


def test_problem_not_execution():
    case={'problem':'Produce images','task':'not implemented','context':'image generation required'}
    p=case_profile2(case,rules)
    assert not p['task']['function_ids']
    assert compare(extract2('Produce images',rules),p)['mapping_grade']<3


def test_task_cosine_fallback():
    s={'score':.2,'components':{'task':{'cosine':.7}}}
    assert semantic2(s,True,True)==.2
    assert semantic2(s,False,True)==.7
    assert semantic2(s,True,False)==.7
    assert semantic2({'score':-1,'components':{}},False,False)==-1


def test_unknown_is_not_negative():
    assert combination_unknown(0,.4,False)==pytest.approx(.7)
    assert combination_unknown(0,.4,True)==pytest.approx(.35)


def test_metrics_zero_positive_policy():
    from scripts.mapping_improvement_run import metric
    assert metric(['a','b'],set(),5)['recall'] is None
    assert metric(['a','b'],set(),5)['f1'] is None
    assert metric(['a','b'],{'a'},5)['f1']==pytest.approx(2/6)
