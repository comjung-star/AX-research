"""Contracts of the frozen new-validation multiview adapter."""
from fractions import Fraction
import json
import pytest
from ax_research.heldout import read,jsonl
from scripts.validation123_api import OUT,OLD,ROOT,body,request_for_review,validate,budget
from scripts.validation123_multiview import load_views,hybrid,mean_tie


def test_historical_all80_pool_exact_reproduction():
    root=ROOT/'docs/dense-bm25-candidates-2026-10-27'
    features={(r['backbone'],r['path_id'],r['case_id']):Fraction(r['hybrid_rrf_exact']) for r in jsonl(root/'candidate_features.jsonl')}
    pools=jsonl(root/'mapping_candidate_pools.jsonl');assert len(pools)==80
    for pool in pools:
        for c,v in pool['final_retrieval_score_exact'].items():
            assert mean_tie([features[pool['backbone'],p,c] for p in pool['path_ids']])==Fraction(v)


def test_all30_view_results_validate_without_original_concatenation():
    paths,sources=load_views();assert len(sources)==30 and len(paths)==107
    qs={q['query_id']:q['text'] for q in jsonl(OLD/'input/questions.jsonl')}
    for p in paths:
        assert p['text']==p['perspective']['title']+'\n'+p['perspective']['description']
        assert qs[p['parent_query_id']] not in p['text']


@pytest.mark.parametrize('kind',['review','views'])
def test_api_input_does_not_leak_ranks_or_prior_grades(kind):
    b=body(kind,'NV20261102_01');d=json.loads(b['input'].split('\nReturn JSON.')[0])
    assert not any(w in json.dumps(d) for w in ('current_grade','current_rationale','ranking','C0','C1','human_reason'))
    assert b['store'] is False and b['model']=='gpt-6-luna' and b['reasoning']['effort']=='none'


def test_review_case_ids_are_one_question_only():
    for q in jsonl(OLD/'input/questions.jsonl'):
        r=request_for_review(q['query_id']);assert r['query_id']==q['query_id']
        assert all(set(c)=={'case_id','Problem','Task','Context'} for c in r['cases'])


def test_invalid_quote_response_rejected_without_rewriting():
    r=read(OUT/'api/views_NV20261102_08_r2_response.json');s=''.join(c.get('text','') for o in r['output'] for c in o.get('content',[]))
    with pytest.raises(AssertionError):validate('views','NV20261102_08',json.loads(s))
    validate('views','NV20261102_08',read(OUT/'api/results/views_NV20261102_08_r2_quote_retry.json')['data'])


def test_budget_includes_failed_reservations_and_invalid_received_usage():
    from decimal import Decimal
    b=budget();assert b['calls']==43 and Decimal(b['unresolved_reserved_usd'])>0
    assert Decimal(b['conservative_spent_or_reserved_usd'])<Decimal('2')
    assert Decimal(b['conservative_spent_or_reserved_usd'])>Decimal(b['standard_usage_usd'])


def test_original_labels_unchanged_outside_declared19():
    old={(r['query_id'],r['case_id']):r for r in read(OLD/'qrels.json')['records']};new={(r['query_id'],r['case_id']):r for r in read(OUT/'stage1/qrels_v2.json')['records']};review={(r['query_id'],r['case_id']) for r in read(OUT/'stage1/review19.json')['records']}
    assert len(new)==len(old)==1120 and len(review)==19
    for k in set(old)-review:assert old[k]==new[k]


def test_incomplete_and_zero_positive_denominators():
    r=read(OUT/'stage2/metrics_v2.json')['per_query']
    for x in r:
        q=x['query_id'][-2:]
        if q in ('08','09'):assert x['metrics']['F1@5'] is None and x['metrics']['nDCG@10'] is None
        if q in ('02','10'):assert x['metrics']['F1@5'] is None and x['undefined_reasons']['F1@5']=='ZERO_POSITIVES'


def test_dynamic_prediction_complete_and_retrieval_exact():
    p=OUT/'stage3/predictions';r=read(p/'rankings.json');ids=set(r['case_ids']);assert len(ids)==112
    for name,runs in r['systems'].items():
        assert len(runs)==(30 if name in ('E2','E4','E4_NEUTRAL') else 10)
        for row in runs:
            assert set(row['ranking'])==set(row['scores'])==ids and len(row['ranking'])==112
            for k in (5,10,20):assert row[f'top{k}']==row['ranking'][:k]
    for row in jsonl(p/'branch_scores.jsonl'):assert hybrid(row['dense_rank'],row['bm25_rank'])==Fraction(row['hybrid_exact'])


def test_original_rankings_reused_exactly_and_label_guard_active():
    p=OUT/'stage3/predictions';new=read(p/'rankings.json')['systems'];old=read(OLD/'predictions/rankings.json')['systems']
    assert new['E1']==old['C0'] and new['E3']==old['C1'] and new['E3_NEUTRAL']==old['C1_NO_EMBEDDING']
    a=read(p/'access_audit.json');assert not a['qrels_read'] and a['network_disabled']
    assert not any('qrels' in x.lower() or 'work_b' in x.lower() for x in a['files_opened'])


def test_repeat_average_has_equal_question_weight():
    from scripts.validation123_analyze import summarize
    result=read(OUT/'stage3/evaluation/summary.json')
    assert summarize(result['per_query'],read(OUT/'stage1/qrels_v2.json')['records'])==result['macro']
    for r in result['macro']:
        assert r['defined_questions']==(6 if r['metric'].startswith(('Recall','F1')) else 8)


def test_prediction_and_evaluation_seals_intact():
    from ax_research.heldout import sha
    for folder in ('predictions','evaluation'):
        p=OUT/'stage3'/folder
        for n,h in read(p/'complete.json')['files'].items():assert sha(p/n)==h
