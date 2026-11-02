import copy
from pathlib import Path
import pytest
from ax_research.heldout import read
from ax_research.functional_mapping import extract,compare
from ax_research.action_aggregation import purpose_filter,allowed_branches,compose

ROOT=Path(__file__).resolve().parents[1]
RULES=read(ROOT/'configs/functional_mapping_20261028.json')
CFG=read(ROOT/'configs/action_aggregation_20261102.json')


@pytest.mark.parametrize('text,keep',[
 ('문서 검토 부담\n첨부 문서를 읽어 핵심 내용을 파악한다',False),
 ('Review documents for compliance',True),('Audit invoices for overcharges',True),
 ('직원 신원조회 보고서 검증',True),('여러 형식의 문서를 검토해야 하는 상황',False),
 ('서류의 필수 항목과 규정 준수 여부 확인',True),
 ('보험 인수심사용 신청 서류 추출·분류',False),
 ('Extract documents for validation',False)])
def test_validation_purpose(text,keep):
    old=extract(text,RULES,executed=True)
    assert 'validate_record' in old['function_ids']
    new=purpose_filter(old,CFG)
    assert ('validate_record' in new['function_ids'])==keep
    assert old==extract(text,RULES,executed=True)


def test_query_goal_is_not_execution():
    p=extract('Extract documents for validation',RULES,executed=False)
    assert 'validate_record' in purpose_filter(p,CFG)['function_ids']


@pytest.mark.parametrize('text,keep',[
 ('Create CRM contacts from customer emails',False),
 ('Generate emails from documents',True),
 ('Using documents, generate emails',True)])
def test_input_output_roles(text,keep):
    p=extract(text,RULES,executed=True)
    assert 'generate_content' in p['function_ids']
    new=purpose_filter(p,CFG)
    assert ('generate_content' in new['function_ids'])==keep
    assert new['purpose_audit']['actual_output_status']=='UNKNOWN_UNLESS_SEPARATELY_LITERAL'


@pytest.mark.parametrize('text',['planned audit of invoices','문서 검증 예정','does not review documents'])
def test_existing_nonexecution_guard(text):assert not purpose_filter(extract(text,RULES,executed=True),CFG)['functions']


def test_gate_needs_three_sources():
    f=lambda *ids:{'function_ids':list(ids)}
    assert allowed_branches(f('summarize_content'),{'p':f('validate_record')},f('validate_record'))=={}
    assert allowed_branches(f('summarize_content'),{'p':f('summarize_content')},f('summarize_content'))=={'p':['summarize_content']}
    assert allowed_branches(f(),{'p':f('summarize_content')},f('summarize_content'))=={}


def test_no_branch_is_original():
    assert compose(1,{'p':4},.2,{'p':.9},{})['score']==compose(1,{},.2,{})['score']


def test_old_c_formula():
    from ax_research.semantic_mapping import aggregate,combined_score
    r=compose(1,{'p':4},.2,{'p':.8})
    assert r['score']==combined_score(4,aggregate(.2,[.8]))


def test_duplicate_branch_has_no_bonus():
    a=compose(2,{'p':3},.2,{'p':.8},{'p':True})
    b=compose(2,{'p':3,'duplicate':3},.2,{'p':.8,'duplicate':.8},{'p':True,'duplicate':True})
    assert a['score']==b['score']


def test_only_allowed_components():
    r=compose(1,{'bad':4,'good':2},.2,{'bad':.9,'good':.1},{'good':True})
    assert r['rule_strength']==2 and r['semantic']==pytest.approx(.15)
    assert r['allowed_paths']==['good']


def test_embedding_diagnostic():
    assert compose(1,{},-.9,{},no_embedding=True)['score']==compose(1,{},.9,{},no_embedding=True)['score']
