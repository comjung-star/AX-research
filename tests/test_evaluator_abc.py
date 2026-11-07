"""Synthetic/offline checks only. No held-out text, keys or external calls."""
import copy
import json
import pytest
from scripts import evaluator_abc as run
from scripts import evaluator_abc_analyze as analysis


def decision():
    return {'id':'x','reason':'근거로 판정','evidence_ids':['T1'],'new_core_functions':[],
        'checks':dict.fromkeys(('actual_work_known','action_match','object_match','output_match',
            'direct_core','transfer_core','core_sufficient','auxiliary_only','any_useful_link',
            'temporal_conflict'),False)}


def core():
    return {'id':'k','execution':'CONFIRMED','action':'추출','object':'문서','output':'표',
        'operations':['추출'],'time_type':'NONE','unknowns':[],
        'evidence':{k:['T1'] for k in ('action','object','output','execution')}}


def test_problem_anchor_is_not_performed_evidence():
    a=run.anchors({'Problem':'필요','Task':'추출 수행','Context':'업무'})
    d=decision();d['evidence_ids']=['P1']
    assert run.check_decision(d,'x','C',a)=='SEMANTIC_PROBLEM_AS_PERFORMED'


def test_exact_wrong_field_quote_is_relocated_without_text_change():
    d={'assessments':[{'query_id':'x','id':'x','scope':'AUXILIARY','category':'JUDGEABLE',
        'reason':'근거','query_quotes':['질문'],'claims':[{'field':'Task','quote':'실제 요약 수행'}]}]}
    a=run.anchors({'Task':'추출','Context':'실제 요약 수행'})
    assert run.check_decision(d,'x','A',a,'원문 질문') is None
    claim=d['assessments'][0]
    assert claim['_citations']==['C1']
    assert claim['_field_corrections'][0]['quote_unchanged']


def test_nonliteral_quote_is_not_repaired_by_invention():
    d={'assessments':[{'query_id':'x','id':'x','scope':'NONE','category':'JUDGEABLE',
        'reason':'근거','query_quotes':['질문'],'claims':[{'field':'Task','quote':'원문에 없는 성과'}]}]}
    assert run.check_decision(d,'x','A',run.anchors({'Task':'추출'}),'질문')=='UNSUPPORTED_LITERAL_CITATION'


@pytest.mark.parametrize('status', ['incomplete','failed'])
def test_truncated_outputs_never_synthesized(status):
    assert run.decode({'status':status,'output':[]},'openai')[1]=='TOKEN_LIMIT_OR_INCOMPLETE'


def test_single_complete_fence_with_trailing_explanation_recovered_unchanged():
    raw={'stop_reason':'end_turn','content':[{'type':'text','text':'```json\n{"id":"x"}\n```\n설명: 부가 문장'}]}
    assert run.decode(raw,'claude')==({'id':'x'},None)
    raw['content'][0]['text']+='\n```json\n{"id":"y"}\n```'
    assert run.decode(raw,'claude')[1]=='INVALID_JSON'


def test_current_detection_cannot_score_future_core():
    d=decision();d['checks'].update(actual_work_known=True,direct_core=True,action_match=True,
        object_match=True,output_match=True,any_useful_link=True)
    g,guards=run.score_c(d,{'time_type':'FUTURE'},{**core(),'time_type':'CURRENT'})
    assert g==1 and 'CURRENT_NOT_FUTURE' in guards


def test_unimplemented_new_core_blocks_transfer():
    d=decision();d['checks'].update(actual_work_known=True,transfer_core=True,core_sufficient=True,any_useful_link=True)
    d['new_core_functions']=['예측기 신규 구현']
    assert run.score_c(d,{'time_type':'NONE'},core())==(1,['UNIMPLEMENTED_CORE_FUNCTION'])


def test_unknown_work_is_not_zero():
    d=decision()
    assert run.score_c(d,{'time_type':'NONE'},{**core(),'execution':'UNSPECIFIED'})[0] is None


def test_known_unrelated_work_is_zero():
    d=decision();d['checks']['actual_work_known']=True
    assert run.score_c(d,{'time_type':'NONE'},core())[0]==0


def test_direct_match_requires_supported_output():
    d=decision();d['checks'].update(actual_work_known=True,direct_core=True,action_match=True,
                                  object_match=True,output_match=True)
    assert run.score_c(d,{'time_type':'NONE'},{**core(),'output':None})==(None,['DIRECT_OUTPUT_UNSUPPORTED'])


def test_core_claim_without_anchor_is_rejected():
    d=core();d['evidence']['action']=[]
    assert run.validate_core('case',d,'k',run.anchors({'Task':'추출'}))=='MISSING_EVIDENCE'


def test_core_cannot_use_problem_for_task():
    d=core();d['evidence']['action']=['P1']
    assert run.validate_core('case',d,'k',run.anchors({'Problem':'필요','Task':'추출'}))=='SEMANTIC_PROBLEM_AS_PERFORMED'


def test_boolean_strings_rejected():
    d=decision();d['checks']['action_match']='true'
    assert run.check_decision(d,'x','C',run.anchors({'Task':'추출'}))=='INVALID_SCHEMA'


def test_judged_null_and_abstain_zero_rejected():
    d={'id':'x','reason':'불명','evidence_ids':[],'new_core_functions':[],'status':'ABSTAIN','grade':0}
    assert run.check_decision(d,'x','B',{})=='INVALID_ENUM'
    d.update(status='JUDGED',grade=None)
    assert run.check_decision(d,'x','B',{})=='INVALID_ENUM'


def test_wrong_mapping_rejected():
    assert run.check_decision(decision(),'other','C',{})=='MISSING_OR_WRONG_ID'


def test_incomplete_schema_rejected():
    d=decision();del d['checks']['direct_core']
    assert run.check_decision(d,'x','C',run.anchors({'Task':'抽出'}))=='MISSING_FIELDS'


def test_semantic_disagreement_is_not_technical_retry():
    assert not {'SEMANTIC_PROBLEM_AS_PERFORMED','UNSUPPORTED_LITERAL_CITATION',
                'UNCERTAIN_OR_HTTP_FAILURE','VALID_LOW_SCORE'} & run.TECHNICAL


@pytest.mark.parametrize('failures,expected_calls',[
    (['INVALID_JSON',None],2),(['INVALID_JSON','INVALID_JSON'],2),
    (['UNCERTAIN_OR_HTTP_FAILURE'],1),(['SEMANTIC_PROBLEM_AS_PERFORMED'],1),( [None],1)])
def test_bounded_retry_and_no_semantic_reroll(tmp_path,monkeypatch,failures,expected_calls):
    monkeypatch.setattr(run,'OUT',tmp_path);monkeypatch.setattr(run,'CURRENT_PROVIDER','openai')
    (tmp_path/'openai').mkdir();calls=[]
    monkeypatch.setattr(run.transport,'call',lambda *args:calls.append(args))
    sequence=iter(failures)
    monkeypatch.setattr(run,'read_attempt',lambda *args:({'id':'x'},next(sequence)))
    monkeypatch.setattr(run.time,'sleep',lambda _:None)
    out=run.request('test','prompt',{'id':'x'},100,lambda _:None)
    assert len(calls)==expected_calls
    assert len(out['attempts'])==expected_calls
    if expected_calls==2:assert calls[-1][-1]==200
    # A completed cached result never calls the API again, including failures.
    assert run.request('test','prompt',{'id':'x'},100,lambda _:None)==out
    assert len(calls)==expected_calls


def test_benchmark_abstain_not_counted_as_a_correct_unrelated_grade():
    item={'expected_abstain':False,'expected':[0]}
    assert not analysis.control_pass(item,{'grade':None,'status':'ABSTAIN'})
    item={'expected_abstain':True,'expected':[]}
    assert analysis.dangerous(item,{'grade':0})
    assert analysis.control_pass(item,{'grade':None,'status':'ABSTAIN'})
    assert not analysis.control_pass(item,{'grade':None,'status':'UNJUDGED'})


def test_provider_caps_are_disjoint_and_within_total():
    assert sum(run.CAPS.values())==2


@pytest.mark.parametrize('originally_valid',[True,False])
@pytest.mark.parametrize('validator_failure',[None,'SEMANTIC_PROBLEM_AS_PERFORMED'])
def test_offline_recovery_never_rerolls_or_chooses_a_favorable_grade(tmp_path,monkeypatch,originally_valid,validator_failure):
    from scripts import evaluator_abc_recover as recovery
    from ax_research.heldout import write,read
    monkeypatch.setattr(run,'OUT',tmp_path);monkeypatch.setattr(run,'ROOT',tmp_path)
    monkeypatch.setattr(run,'configure',lambda _:None)
    p=tmp_path/'openai';(p/'results').mkdir(parents=True);(p/'api').mkdir()
    write(tmp_path/'benchmark.json',{'records':[{'id':'x'}]})
    write(tmp_path/'pending_items.json',{'records':[]})
    write(tmp_path/'method_selection.json',{'method':'B'})
    payload={'id':'x'};name='judge_B_x'
    old={'data':{'grade':0},'valid':originally_valid,'failure':None if originally_valid else 'INVALID_JSON',
        'prompt_payload_sha256':run.transport.digest({'prompt':'p','payload':payload}),
        'attempts':[{'id':'openai_'+name,'failure':'INVALID_JSON'},
                    {'id':'openai_'+name+'_technical1','failure':'INVALID_JSON'}]}
    write(p/'results'/(name+'.json'),old)
    for suffix,grade in [('',0),('_technical1',3)]:
        stem='openai_'+name+suffix
        write(p/'api'/(stem+'_receipt.json'),{'state':'RECEIVED'})
        write(p/'api'/(stem+'_response.json'),{'status':'completed','output':[{'content':[{'type':'output_text',
            'text':'```json\n'+json.dumps({'grade':grade})+'\n```\n설명'}]}]})
    def forbidden(*_):raise AssertionError('No new API calls allowed')
    monkeypatch.setattr(run,'request',forbidden)
    monkeypatch.setattr(run,'evaluate_item',lambda *_:run.request(name,'p',payload,100,lambda _:validator_failure))
    recovery.recover('openai')
    rows=read(p/'recovery-v2'/'benchmark_recovered_results.json')['records']
    assert all(r['data']['grade']==0 for r in rows)
    if not originally_valid and validator_failure:
        assert all(r['failure']==validator_failure and not r['valid'] for r in rows)
    assert read(p/'results'/(name+'.json'))==old


def test_offline_replay_cannot_make_a_new_dependent_API_call(tmp_path,monkeypatch):
    from scripts import evaluator_abc_recover as recovery
    from ax_research.heldout import write,read
    monkeypatch.setattr(run,'OUT',tmp_path);monkeypatch.setattr(run,'configure',lambda _:None)
    write(tmp_path/'benchmark.json',{'records':[{'id':'x'}]})
    write(tmp_path/'pending_items.json',{'records':[]})
    write(tmp_path/'method_selection.json',{'method':'B'})
    def forbidden(*_):raise AssertionError('New API forbidden')
    monkeypatch.setattr(run,'request',forbidden)
    monkeypatch.setattr(run,'evaluate_item',lambda *_:run.request('judge_B_x','p',
        {'id':'x','case_core':{'execution':'CONFIRMED','action':'요약'}},100,lambda _:None))
    recovery.recover('openai')
    rows=read(tmp_path/'openai/recovery-v2/benchmark_recovered_results.json')['records']
    assert all(r['failure']=='DEPENDENT_JUDGE_NOT_PREVIOUSLY_EXECUTED' for r in rows)
