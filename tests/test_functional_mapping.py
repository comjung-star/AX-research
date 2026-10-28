import json
from pathlib import Path
import pytest
from ax_research.functional_mapping import extract,case_profile,compare,ranking_key

R=json.loads((Path(__file__).resolve().parents[1]/'configs/functional_mapping_20261028.json').read_text(encoding='utf-8-sig'))
def match(query,task,problem='',context=''):
    return compare(extract(query,R),case_profile({'problem':problem,'task':task,'context':context},R))

def test_cross_industry_qa():
    m=match('고객 반복 질문 처리와 답변','Answer employee policy questions')
    assert m['mapping_grade']==3 and m['shared_functions']==['answer_question']

def test_quality_word_does_not_license_qa():
    m=match('고객 질문 답변 품질 유지','Analyze production quality defects and root causes')
    assert m['mapping_grade']<3 and not m['shared_functions']

def test_summary_and_answer_separate():
    assert not match('긴 이메일 핵심 내용 요약','Answer customer questions')['shared_functions']

def test_problem_never_licenses_task():
    assert match('Answer customer questions','Unload cartons','Need to answer questions')['mapping_grade']<3

def test_context_never_licenses_task():
    assert match('Answer customer questions','Unload cartons',context='Answer customer questions')['mapping_grade']<3

@pytest.mark.parametrize('task',['Does not answer customer questions','Plan to answer customer questions in future','고객 문의 응답 도입 예정','Needs to answer employee questions'])
def test_nonexecuted_clauses_held(task):
    assert match('고객 질문 답변',task)['mapping_grade']<3

def test_unrecognized_is_unknown():
    assert match('시간이 오래 걸린다','Automate the workflow')['status']=='UNKNOWN'

def test_partial_question_coverage_not_whole_solution():
    m=match('Summarize email threads; identify follow-up actions','Summarize emails')
    assert m['mapping_grade']>=3 and m['query_uncovered_functions']==['identify_followup']

def test_quotation_spans_are_raw_offsets():
    text='보험 서류 추출·분류; Answer policy questions.'
    p=extract(text,R,executed=True)
    for f in p['functions']:
        for k in ('action','object','clause'):
            e=f[k];assert text[e['start']:e['end']]==e['quote']

def test_duplicate_perspectives_no_count_bonus():
    w={'mapping_grade':1};b={'mapping_grade':3}
    assert ranking_key(w,[b],.01,'x')==ranking_key(w,[b]*5,.01,'x')

def test_no_context_fields_can_change_task_functions():
    p=case_profile({'task':'Answer policy questions','problem':'Detect weld defects','context':'Forecast demand'},R)
    assert p['task']['function_ids']==['answer_question']

def test_output_type_does_not_claim_observed_artifact():
    p=extract('Answer policy questions',R,executed=True)
    assert p['functions'][0]['output_status']=='OPERATION_TYPE_NOT_SEPARATELY_VERIFIED_OUTPUT'
