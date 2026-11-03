"""Follow-up invariants: protected data, genuine partial metrics, honest blocking."""
import subprocess
import pytest
from ax_research.heldout import read,sha
from scripts.stage45_offline import ROOT,OUT,DEV,BASE,inference


def test_stage4_only_one_source_grounded_label_changed():
    a=read(DEV/'stage1/qrels_v2.json')['records'];b=read(OUT/'stage4/qrels_v3.json')['records']
    changed=[(x,y) for x,y in zip(a,b) if x!=y];assert len(changed)==1
    x,y=changed[0];assert x['query_id']=='NV20261102_09' and y['grade']==1 and x['status']=='ABSTAIN'
    assert sum(r['status']=='ABSTAIN' for r in b)==1


def test_old_algorithm_and_original_labels_untouched():
    paths=['src/ax_research/functional_mapping.py','src/ax_research/semantic_mapping.py','src/ax_research/action_aggregation.py','configs/action_aggregation_20261102.json','configs/functional_mapping_20261028.json','configs/semantic_mapping_20261028.json','docs/validation-c0c1-stage1to3-2026-11-03/stage1/qrels_v2.json','docs/dense-bm25-candidates-2026-10-27/case_registry.json']
    for p in paths:
        before=subprocess.check_output(['git','show',BASE+':'+p],cwd=ROOT)
        assert before.replace(b'\r\n',b'\n')==(ROOT/p).read_bytes().replace(b'\r\n',b'\n')


def test_balance_gate_does_not_assert_empty_or_sufficient_credit():
    a=read(OUT/'access_check.json');p=read(OUT/'preregistration/plan.json')
    assert a['actual_credit_balance'] is None and not a['balance_verified']
    assert next(x for x in a['checks'] if x['check']=='model_access')['HTTP']==200
    assert next(x for x in a['checks'] if x['check']=='organization_cost_access')['HTTP']==403
    assert p['paid_calls']==0 and p['paid_work_state']=='BLOCKED_BALANCE_VERIFICATION'


def test_three_available_rankings_and_topk_are_complete():
    p=read(OUT/'stage5/predictions/rankings.json');assert len(p['query_ids'])==15 and len(p['case_ids'])==112
    assert set(p['systems'])=={'T1','T3','T3_NEUTRAL'} and set(p['blocked_conditions'])=={'T2','T4'}
    for rs in p['systems'].values():
        assert len(rs)==15
        for r in rs:
            assert len(r['ranking'])==112 and set(r['ranking'])==set(r['scores'])==set(p['case_ids'])
            for k in (5,10,20):assert r[f'top{k}']==r['ranking'][:k]


def test_inference_read_only_question_payload_not_labels():
    r=read(OUT/'stage5/predictions/inference_receipt.json')
    assert r['qrels_read'] is False and r['network_calls']==r['paid_calls']==0
    assert r['sealed_files_opened_during_inference'] and all(p.endswith(('questions.jsonl','manifest.json')) for p in r['sealed_files_opened_during_inference'])
    assert r['exact_prior_query_duplicates']==[]


def test_no_partial_labels_are_silently_counted_as_zero():
    e=read(OUT/'stage5/evaluation/complete.json');assert e['counts']=={'JUDGED':45,'ABSTAIN':0,'UNJUDGED':1635}
    m=read(OUT/'stage5/evaluation/metrics_partial_original.json')
    assert e['full_evaluable_question_count']==0
    for r in m['per_query']:
        assert r['judged']==3 and not r['complete112']
        assert all(v is None for v in r['metrics'].values())
        assert r['undefined_reasons']['Precision@5']=='TOPK_UNJUDGED_OR_ABSTAIN'
    assert all(r['defined']==0 and r['value'] is None for r in m['macro_common_queries'])


@pytest.mark.parametrize('folder',['stage4','stage5/predictions','stage5/evaluation'])
def test_result_seals_are_valid(folder):
    p=OUT/folder
    for n,h in read(p/'complete.json')['files'].items():assert sha(p/n)==h


def test_existing_run_directory_refuses_overwrite(tmp_path):
    with pytest.raises(FileExistsError):inference(tmp_path)


def test_known_positive_ranks_are_limited_observations_not_metrics():
    r=read(OUT/'stage5/evaluation/known_positive_ranks.json');assert r['never_a_complete_performance_claim']
    assert len(r['records'])==7
    bank=next(x for x in r['records'] if x['query_id']=='HB009');assert bank['ranks']['T1']==bank['ranks']['T3']==1
    bad=next(x for x in r['records'] if x['query_id']=='HB014' and x['grade']==3);assert bad['ranks']['T1']==bad['ranks']['T3']==65
