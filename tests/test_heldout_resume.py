"""Resume contracts without any live model/API calls."""
import json
from decimal import Decimal
import pytest
from ax_research.heldout import read,sha,jsonl
from scripts.heldout_resume_api import OUT,PRIVATE,PRIOR,PAYLOAD,configure,call_valid,A


@pytest.fixture(autouse=True)
def isolate_api_module_settings():
    previous=(A.OUT,A.OLD,A.request_for_review)
    yield
    A.OUT,A.OLD,A.request_for_review=previous


def test_blind_jobs_cover_all_pairs_and_never_mix_questions():
    jobs=read(PRIVATE/'jobs.json')['jobs'];seen={'missing':set(),'audit45':set()}
    for j in jobs:
        assert set(j['payload'])=={'query_id','business_problem','cases'}
        assert j['query_id']==j['payload']['query_id'] and 1<=len(j['payload']['cases'])<=12
        for c in j['payload']['cases']:
            assert set(c)=={'case_id','Problem','Task','Context'}
            pair=(j['query_id'],c['case_id']);assert pair not in seen[j['category']];seen[j['category']].add(pair)
    assert len(seen['missing'])==1635 and len(seen['audit45'])==45 and not seen['missing']&seen['audit45']


@pytest.mark.parametrize('message',['UNCERTAIN_REQUEST_NO_REPLAY','OPENAI_HTTP_429','BUDGET_CAP'])
def test_uncertain_or_http_errors_are_not_retried(monkeypatch,message):
    calls=[]
    def fake(*args):calls.append(args);raise RuntimeError(message)
    monkeypatch.setattr(A,'call',fake)
    with pytest.raises(RuntimeError,match=message):call_valid('views','fixture',1)
    assert len(calls)==1


def test_only_one_format_retry_for_known_received_response(monkeypatch):
    calls=[]
    def fake(*args):
        calls.append(args)
        if len(calls)==1:raise RuntimeError('RECEIVED_BUT_INVALID_NO_AUTOMATIC_RETRY')
        return {'valid':True}
    monkeypatch.setattr(A,'call',fake);assert call_valid('views','fixture',1)=={'valid':True}
    assert [r[-1] for r in calls]==['','format_retry']


def test_original45_are_preserved_exactly():
    old=jsonl(PAYLOAD/'qrels.jsonl');new=read(PRIVATE/'qrels_completed_v2.json')['records'];by={(r['query_id'],r['case_id']):r for r in new}
    assert len(new)==1680 and len(by)==1680
    for r in old:
        if r['status']=='JUDGED':assert by[r['query_id'],r['case_id']]==r
    assert sha(PAYLOAD/'qrels.jsonl')==read(OUT/'plan.json')['original_qrels_sha256']


def test_all45_views_validate_from_original_query_only():
    configure();qs=jsonl(PRIVATE/'inputs/input/questions.jsonl');count=0
    for rep in (1,2,3):
        for q in qs:
            name=f"views_{q['query_id']}_r{rep}";p=PRIVATE/'api/results'/(name+'.json')
            if not p.exists():name+='_format_retry';p=PRIVATE/'api/results'/(name+'.json')
            r=read(p);A.validate('views',q['query_id'],r['data']);b=read(PRIVATE/'api'/(name+'_request.json'))['body'];d=json.loads(b['input'].split('\nReturn JSON.')[0])
            assert set(d)=={'original_business_problem','format'} and d['original_business_problem']==q['text'];count+=1
    assert count==45


def test_original_rankings_reused_and_all_paths_preserved():
    p=read(OUT/'predictions/rankings.json');old=read(PRIOR/'stage5/predictions/rankings.json')
    assert p['systems']['E1']==old['systems']['T1'] and p['systems']['E3']==old['systems']['T3']
    for n,rows in p['systems'].items():
        assert len(rows)==(45 if n in ('E2','E4','E4_NEUTRAL') else 15)
        for r in rows:
            assert len(r['ranking'])==112 and set(r['ranking'])==set(p['case_ids'])
            for k in (5,10,20):assert r[f'top{k}']==r['ranking'][:k]
    br=read(OUT/'predictions/branch_rankings.json')
    assert len(jsonl(OUT/'predictions/branch_scores.jsonl'))==br['path_count']*112


def test_no_labels_read_during_inference():
    a=read(OUT/'predictions/access_audit.json');assert not a['qrels_read'] and a['network_disabled']
    assert not any('qrels' in p.lower() or 'judgments' in p.lower() for p in a['files_opened'])


@pytest.mark.parametrize('folder',['predictions','evaluation'])
def test_output_hash_seals(folder):
    p=OUT/folder
    for n,h in read(p/'complete.json')['files'].items():assert sha(p/n)==h


def test_cost_bound_and_usage_receipts():
    configure();b=A.budget();assert Decimal(b['conservative_spent_or_reserved_usd'])<=2
    for p in (PRIVATE/'api/attempts').glob('*.json'):
        r=read(p)
        if r['state']=='RECEIVED':assert r['usage']['input_tokens']>=0 and r['usage']['output_tokens']>=0 and r['response_model']=='gpt-6-luna'


def test_metrics_reproducible_and_not_using_unresolved_as_zero():
    from scripts.heldout_resume_evaluate import score
    labels=read(PRIVATE/'qrels_completed_v2.json')['records'];actual=score(read(OUT/'predictions/rankings.json'),labels)
    assert actual==read(OUT/'evaluation/metrics.json')
    for r in actual['per_query']:
        if not r['complete112']:assert r['metrics']['Recall@5'] is None and r['metrics']['F1@5'] is None and r['metrics']['nDCG@10'] is None
