from decimal import Decimal

import pytest

from scripts import e_validation as run
from scripts import e_validation_analyze as analysis


def opinion(grade=2, valid=True):
    return {'valid':valid,'assessment':{'status':'JUDGED','grade':grade,'reason':'근거에 따른 판단'}}


def test_grade_disagreement_stays_abstain_even_if_binary_relevance_agrees():
    result=analysis.consensus([opinion(2),opinion(3)])
    assert result['status']=='ABSTAIN' and result['grade'] is None


def test_invalid_second_review_cannot_certify_a_label():
    assert analysis.consensus([opinion(),opinion(valid=False)])['status']=='ABSTAIN'


def test_same_grade_source_valid_reviews_are_explicitly_silver():
    result=analysis.consensus([opinion(),opinion()])
    assert result['grade']==2 and result['review_status']=='TWO_SOURCE_VALID_REVIEWS_AGREE'


def test_relevance_validation_rejects_cross_question_mapping_and_invented_quote():
    payload={'query_id':'q','cases':[{'id':'x','Task':'Review invoice amounts'}]}
    row={'query_id':'other','id':'x','grade':2,'status':'JUDGED','reason':'검토',
         'task_quote':'Review invoice amounts','case_action':'Review','case_object':'invoice',
         'case_output':None,'permission_scope':None}
    with pytest.raises(AssertionError):analysis.validate_relevance(row,payload)
    row['query_id']='q'
    row['task_quote']='Pay the invoice automatically'
    with pytest.raises(AssertionError):analysis.validate_relevance(row,payload)


def test_relevance_validation_rejects_boolean_grade():
    payload={'query_id':'q','cases':[{'id':'x','Task':'Review invoices'}]}
    row={'query_id':'q','id':'x','grade':True,'status':'JUDGED','reason':'검토',
         'task_quote':'Review invoices','case_action':None,'case_object':None,
         'case_output':None,'permission_scope':None}
    with pytest.raises(AssertionError):analysis.validate_relevance(row,payload)


def test_quality_issues_require_real_source_and_candidate_quotes():
    payload={'id':'v','original_business_problem':'A human approves.',
             'views':[{'id':'BUSINESS','title':'Review','description':'A human approves.'}]}
    result={'id':'v','checks':[{'field':f,'score':2,'reason':'보존'} for f in run.QUALITY_FIELDS],
            'issues':[{'type':'CONTRADICTION','source_quote':'A human approves.',
                       'view_quote':'AI approves automatically.','reason':'불일치'}],
            'permission_interpretation':'사람 승인'}
    assert analysis.validate_quality(result,payload)[0]['literal_evidence_valid'] is False
    result['issues']=[]
    assert analysis.validate_quality(result,payload)==[]


def test_blind_payloads_do_not_include_prior_grades_ranks_or_condition_names():
    forbidden={'condition','repeat','selection','grade','score','ranking','old_grade','label_source'}
    def inspect(value):
        if isinstance(value,dict):
            assert not forbidden & set(value)
            for item in value.values():inspect(item)
        elif isinstance(value,list):
            for item in value:inspect(item)
    for missing in (True,False):
        for group in run.batches(missing):
            payload=run.rel_payload(group)
            assert len({x['query_id'] for x in group})==1
            inspect(payload)
    for record in run.read(run.OUT/'selection.json')['quality_mapping']:
        inspect(run.quality_payload(record))


def test_preregistered_full_reservation_bound_fits_two_dollars():
    budget=run.read(run.OUT/'budget_preflight_v2.json')
    assert Decimal(budget['all_call_upper_usd'])<=2
    assert budget['output_limits']=={'relevance':900,'quality':1200}


def test_original_outputs_prompts_corpus_and_algorithms_remain_byte_identical():
    for path,digest in run.read(run.OUT/'protocol.json')['protected_sha256'].items():
        assert run.sha(run.ROOT/path)==digest,path


def test_stage1_missing_labels_preserve_all_prior_867_decisions():
    reviews=analysis.collect_relevance(True)
    versions,_=analysis.label_versions(reviews,True)
    old={(r['query_id'],r['case_id']):r for r in run.read(run.old.OUT/'labels.json')['records']}
    updated=versions['v1_missing_only']
    assert len(updated)==896
    for row in updated:
        original=old[row['query_id'],row['case_id']]
        if original['status']=='JUDGED':
            assert row['grade']==original['grade'] and row['rationale']==original['rationale']
        elif row['status']!='JUDGED':
            assert row['grade'] is None


def test_uncertain_reserved_request_is_never_sent_again(tmp_path,monkeypatch):
    monkeypatch.setattr(run,'OUT',tmp_path)
    (tmp_path/'api').mkdir()
    body=run.request_body('openai','instructions',{'item':'source'},900)
    run.write(tmp_path/'api/openai_fixture_receipt.json',{
        'state':'UNCERTAIN_OR_HTTP_FAILURE','request_sha256':run.digest(body)})
    def no_network(*args,**kwargs):
        raise AssertionError('A saved uncertain request must not use the network')
    monkeypatch.setattr(run.urllib.request,'build_opener',no_network)
    assert run.call('openai','fixture','instructions',{'item':'source'},900) is None


def test_token_limit_recovery_does_not_retry_completed_or_uncertain_calls(tmp_path,monkeypatch):
    monkeypatch.setattr(run,'OUT',tmp_path)
    (tmp_path/'api').mkdir()
    run.write(tmp_path/'technical_recovery_policy.json',{})
    run.write(tmp_path/'api/claude_quality_V001_receipt.json',{
        'id':'claude_quality_V001','provider':'claude','state':'RECEIVED'})
    run.write(tmp_path/'api/claude_quality_V001_response.json',{'stop_reason':'end_turn'})
    run.write(tmp_path/'api/claude_quality_V002_receipt.json',{
        'id':'claude_quality_V002','provider':'claude','state':'UNCERTAIN_OR_HTTP_FAILURE'})
    def no_repeat(*args,**kwargs):
        raise AssertionError('Neither completed nor uncertain responses qualify')
    monkeypatch.setattr(run,'call',no_repeat)
    run.repair('quality')
