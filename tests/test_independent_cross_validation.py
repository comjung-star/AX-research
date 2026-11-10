import pytest
from ax_research.independent_cross_validation import utility,score_question,bootstrap_bounds,agreement,summarize


def test_shared_unknown_cancels_in_paired_effect():
    r=score_question(['common','a'],['common','b'],{'a':'0','b':'2'})
    assert r['A']['precision_lower']==0 and r['A']['precision_upper']==.5
    assert r['B']['precision_lower']==.5 and r['B']['precision_upper']==1
    assert r['delta_lower']==r['delta_upper']==.5


def test_unresolved_exclusive_cases_have_adverse_bounds():
    r=score_question(['a','common'],['b','common'],{'common':'3'})
    assert r['delta_lower']==-.5 and r['delta_upper']==.5
    assert r['unresolved_new']==['b'] and r['unresolved_lost']==['a']


def test_abstain_is_not_negative():
    assert utility('ABSTAIN') is None and utility(None) is None
    assert utility('1')==0 and utility('2')==1


def test_repeated_shared_case_not_duplicated_in_bootstrap_unit():
    rec={f'q{i}':{'A':['same','a'],'B':['same','b']} for i in range(20)}
    grades={q:{'same':'3','a':'0','b':'2'} for q in rec}
    m=summarize(rec,grades)
    assert m['statistics']['n_questions']==20
    assert m['statistics']['paired_bootstrap95_envelope']==[.5,.5]


def test_agreement_distinguishes_binary_grade_and_abstain():
    x={'a':'2','b':'0','c':'ABSTAIN'};y={'a':'3','b':'0','c':'0'}
    r=agreement(x,y)
    assert r['eligible_nonabstain']==2 and r['binary_agreement']==1
    assert r['exact_score_agreement']==.5


def test_no_data_has_no_agreement_and_no_zero_score_claim():
    assert agreement({}, {})['binary_agreement'] is None
    r=score_question(['x'],['x'],{})
    assert (r['A']['precision_lower'],r['A']['precision_upper'])==(0,1)
    assert r['delta_lower']==r['delta_upper']==0


def test_unequal_output_counts_rejected():
    with pytest.raises(AssertionError):score_question(['a'],['b','c'],{})


def test_known_gains_losses_preserve_pair_units():
    r=score_question(['a','x'],['b','x'],{'a':'3','b':'2','x':'0'})
    assert r['known_new_useful']==['b'] and r['known_lost_useful']==['a']
    assert r['delta_lower']==r['delta_upper']==0
