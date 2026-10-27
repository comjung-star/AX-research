import copy
import json
import pytest
from scripts import evidence_run as r
from scripts.evidence_rules import parse_evidence,score

def sample(qid='V21D001',cid='AXV2P2_0048_01',target='WHOLE_QUERY'):
    cs,qs=r.cases_queries();j=r.make_job('pilot',0,qid,[cid],cs,qs,target)
    row={'id':cid,'ops':[['ANSWER','answer','shopping inquiries','answers','Answer shopping questions']],'links':[['ANSWER_INQUIRY',0,'EEE','DIRECT','Equivalent question answering and usable answer output across sectors.']]}
    return j,{'qid':qid,'target':target,'items':[row]}

def test_no_ai_score_and_no_unsupported_shop_four():
    j,d=sample();rows=parse_evidence(d,j);s=score(rows[0],j)
    assert s['score']==3 and not s['fourth_point_evidence']
    d['items'][0]['score']=4
    with pytest.raises(ValueError,match='MODEL_SCORE'):parse_evidence(d,j)

def test_problem_need_cannot_be_actual_operation_evidence():
    j,d=sample('V21D002','AXV2H_0002_01')
    d['items'][0]['ops']=[['ACTION_ITEMS','identify','followups','actions','후속조치 확인']]
    d['items'][0]['links']=[['IDENTIFY_FOLLOWUP',0,'EEE','DIRECT','Same identification output.']]
    with pytest.raises(ValueError,match='NOT_STATED'):parse_evidence(d,j)

def test_whole_summary_can_be_four_but_followup_aspect_not():
    j,d=sample('V21D002','AXV2H_0002_01')
    row=d['items'][0];row['ops']=[['SUMMARIZE','summarize','customer emails','summary','고객 이메일 요약']]
    row['links']=[['SUMMARIZE_COMMUNICATION',0,'EEE','DIRECT','Same conversation summarization operation.']]
    assert score(parse_evidence(d,j)[0],j)['score']==4
    j2,d2=sample('V21D002','AXV2H_0002_01','V21D002:FOLLOWUP');d2['items'][0]['ops']=row['ops']
    d2['items'][0]['links']=[['IDENTIFY_FOLLOWUP',0,'SES','SUPPORT','Summary supports finding actions but does not identify them.']]
    assert score(parse_evidence(d2,j2)[0],j2)['score']==2

def test_wrong_direct_semantic_family_is_held_not_promoted():
    j,d=sample('V21D002','AXV2H_0002_01','V21D002:FOLLOWUP')
    d['items'][0]['ops']=[['SUMMARIZE','summarize','emails','summary','고객 이메일 요약']]
    d['items'][0]['links']=[['IDENTIFY_FOLLOWUP',0,'EEE','DIRECT','Both perform the same operation.']]
    s=score(parse_evidence(d,j)[0],j);assert s['score'] is None

def test_query_case_scope_duplication_are_rejected():
    j,d=sample()
    for key in ('qid','target'):
        x=copy.deepcopy(d);x[key]='WRONG'
        with pytest.raises(ValueError):parse_evidence(x,j)
    d['items']*=2
    with pytest.raises(ValueError):parse_evidence(d,j)

def test_plan_exact36_and_three_repeats_without_cases(tmp_path,monkeypatch):
    monkeypatch.setattr(r,'OUT',tmp_path);p=r.prepare()
    assert sum(len(j['items']) for j in p['pilot'])==36
    assert len(p['views'])==30 and p['stage3_repeats']==3
    assert sorted(len(j['items']) for j in p['probe'])==[1,2,4]
    for j in p['views']:assert 'requirements' not in j['user'] and 'case_id' not in j['user']

def test_no_native_claude_complex_schema():
    j,_=sample();b=r.body('claude',j)
    assert 'output_config' not in b and 'tools' not in b

def test_atomic_source_operations_not_checkbox_count():
    j,d=sample();d['items'][0]['links']=[['ANSWER_INQUIRY',0,'EEE','SUPPORT','Supports the request but not directly.']]
    assert score(parse_evidence(d,j)[0],j)['score']==2
    d['items'][0]['links']=[]
    assert score(parse_evidence(d,j)[0],j)['score']==0
