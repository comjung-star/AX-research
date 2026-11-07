import copy

import pytest

from scripts import autonomous_ax_gate as run
from scripts import autonomous_ax_analyze as analysis


def example():
    data={'query_id':'q','business_problem':'문서를 검토한다.','cases':[
        {'id':'c','Task':'Review documents and return a list.','Context':'A human approves.','Problem':'Need to save time.'}]}
    row={'query_id':'q','id':'c','scope':'TRANSFER_CORE','category':'JUDGEABLE','reason':'업무 전이 판단',
         'query_quotes':['문서를 검토한다'],'claims':[
             {'role':'ACTION','field':'Task','quote':'Review documents'},
             {'role':'OBJECT','field':'Task','quote':'documents'},
             {'role':'OUTPUT','field':'Task','quote':'return a list'}],
         'missing_information':[],'expert_question':None}
    return data,row


def test_complete_prefix_recovery_never_fills_a_truncated_item():
    text='{"assessments":[{"id":"a","reason":"braces } and comma ,"},{"id":"b"},{"id":"c","reason":"cut'
    result=run.recover_complete_objects(text)
    assert [r['id'] for r in result['assessments']]==['a','b']
    assert result['_no_missing_item_synthesized'] is True
    for item,(start,end) in zip(result['assessments'],result['_complete_object_spans']):
        assert run.json.loads(text[start:end])==item


def test_non_schema_text_is_not_salvaged_as_an_assessment():
    assert run.recover_complete_objects('a note {"id":"invented"}') is None


def test_claims_from_problem_needs_cannot_prove_performed_work():
    data,row=example();row['claims'][0]={'role':'ACTION','field':'Problem','quote':'Need to save time'}
    with pytest.raises(AssertionError):run.validate(row,data)


def test_case_claim_copied_only_from_question_is_rejected():
    data,row=example();row['claims'][0]['quote']='문서를 검토한다'
    with pytest.raises(AssertionError):run.validate(row,data)


def test_evidence_count_does_not_promote_the_semantic_scope_grade():
    data,row=example()
    assert run.validate(row,data)==2
    row['scope']='FULL_CORE';row['claims']=row['claims'][:2]
    with pytest.raises(AssertionError):run.validate(row,data)


def test_critical_current_detection_vs_prediction_example_remains_a_failed_gate():
    outcome=run.read(run.OUT/'policy_fixture_results.json')
    failure=next(r for r in outcome['records'] if r['id']=='F03' and r['provider']=='claude')
    assert failure['grade']==2 and not failure['policy_example_passed']
    assert run.read(run.OUT/'entry_gate.json')['decision']=='STOP_BEFORE_PERFORMANCE_TUNING'


def test_source_evidence_and_previous_results_remain_unchanged():
    for path,digest in run.read(run.OUT/'preregistration.json')['protected_sha256'].items():
        assert run.sha(run.ROOT/path)==digest,path


def test_label_scenarios_are_reproducible_and_never_rewrite_real_qrels():
    ids=[f'c{i}' for i in range(112)]
    prediction={'case_ids':ids,'query_ids':['fixture'],'systems':{
        c:[{'query_id':'fixture','ranking':ids if c!='E' else ids[1:6]+ids[:1]+ids[6:]}] for c in 'ABCE'}}
    labels=[{'query_id':'fixture','case_id':cid,'grade':3 if i==0 else None if i==5 else 0,
             'status':'ABSTAIN' if i==5 else 'JUDGED'} for i,cid in enumerate(ids)]
    before=copy.deepcopy(labels)
    first=analysis.label_scenarios(prediction,labels,128)
    second=analysis.label_scenarios(prediction,labels,128)
    assert first==second and labels==before
    assert all(w['not_real_labels'] for w in first['witnesses'])
    assert first['fixed_question_count']==1  # Scenarios never become independent questions.


def test_failed_reliability_gate_does_not_count_api_reviews_as_improvement_runs():
    status=run.read(run.OUT/'status.json')
    iterations=run.read(run.OUT/'iterations.json')
    assert status['improvement_iterations']==0 and not status['new_Test_executed']
    assert iterations['executed']==0 and len(iterations['records'])==5
    assert all(r['F1@5'] is None and not r['adopted'] for r in iterations['records'])


def test_expert_packet_contains_no_fabricated_human_scores():
    rows=run.jsonl(run.OUT/'expert_review_packet.jsonl')
    assert len(rows)==75
    assert all(r['grade'] is None and r['status']=='UNREVIEWED' and
               r['label_source']=='HUMAN_NOT_REVIEWED' for r in rows)
    assert all(not {'ranking','condition','old_grade','provider'} & set(r) for r in rows)
