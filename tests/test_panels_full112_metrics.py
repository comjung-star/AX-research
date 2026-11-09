"""Set metrics must distinguish extra useful discoveries, losses and duplicate views."""
import pytest
from scripts.panels_full112_experiment_20261109 import metrics,ci

def test_same_unique_budget_can_trade_one_useful_case_for_another():
    g={'a':{'grade':3,'perspectives':['P01']},'b':{'grade':2,'perspectives':['P04']},'c':{'grade':0,'perspectives':[]}}
    first=metrics(['a','c'],g);second=metrics(['a','b'],g)
    assert first['recall']==.5 and second['recall']==1
    assert first['view_coverage']==.5 and second['view_coverage']==1
    assert second['f1']==1

def test_duplicate_case_membership_does_not_inflate_precision_or_case_count():
    g={'a':{'grade':2,'perspectives':['P01','P04']}}
    result=metrics(['a','a'],g)
    assert result['returned']==1 and result['hits']==1 and result['view_coverage']==1

def test_empty_output_on_answerable_question_is_failure_not_perfect_abstention():
    g={'a':{'grade':3,'perspectives':['P02']}}
    result=metrics([],g)
    assert result['recall']==0 and result['f1']==0 and result['precision']==0

def test_no_relevant_case_makes_recall_undefined_not_one():
    result=metrics([],{'a':{'grade':0,'perspectives':[]}})
    assert result['recall'] is None and result['f1'] is None
    assert result['view_coverage'] is None

def test_paired_interval_is_reproducible_and_zero_for_equal_methods():
    assert ci([0,0,0])=={'n':3,'mean':0.,'paired_bootstrap95':[0.,0.]}
    assert ci([-.5,.5])==ci([-.5,.5])
