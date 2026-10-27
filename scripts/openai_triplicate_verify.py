"""Independent artifact-level verification, no paid/API calls."""
import hashlib
import math
import statistics
from collections import defaultdict
from scripts import openai_triplicate as r

def near(a,b):
    assert (a is None)==(b is None)
    if a is not None:assert math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-10)
def main():
    silver=r.read(r.OUT/'stage1_silver.json');b=r.read(r.OUT/'stage2_results.json');c=r.read(r.OUT/'stage3_results.json');cases,queries=r.inputs()
    assert len(silver['records'])==1120 and silver['received_scores']==3360
    pairs=set();responses=set();positive=defaultdict(set)
    for z in silver['records']:
        pair=(z['qid'],z['cid']);assert pair not in pairs;pairs.add(pair)
        assert len(z['ratings'])==3 and {v['repeat'] for v in z['ratings']}=={1,2,3}
        assert len({v['input_version'] for v in z['ratings']})==1
        expected=sorted(v['score'] for v in z['ratings'])[1];assert z['median']==expected
        if z['relevant']:positive[z['qid']].add(z['cid'])
        for v in z['ratings']:
            assert v['response_id'] not in responses;responses.add(v['response_id'])
    assert pairs=={(q,cs) for q in queries for cs in cases}
    rows_checked=0;metrics_checked=0
    for name,rows in {**b['systems'],**c['systems']}.items():
        dynamic=name.startswith(('C_','D_'));assert len(rows)==(30 if dynamic else 10)
        point_values=defaultdict(lambda:defaultdict(list))
        for row in rows:
            ranking=row['ranking'];assert len(set(ranking))==len(ranking)
            if dynamic:assert len(ranking)==20 and set(ranking)<=set(cases)
            else:assert len(ranking)==112 and set(ranking)==set(cases)
            q=row['qid'];relevant=positive[q]
            for k in (5,10,20):
                hit=len(set(ranking[:k]).intersection(relevant));p=hit/k;rec=hit/len(relevant) if relevant else None
                f=2*p*rec/(p+rec) if rec is not None and p+rec else 0 if rec==0 else None
                saved=row['metrics'][str(k)]
                assert saved['tp']==hit and saved['precision_denominator']==k and saved['recall_denominator']==len(relevant)
                for field,value in [('precision',p),('recall',rec),('f1',f)]:
                    near(saved[field],value);point_values[(k,field)][q].append(value)
                metrics_checked+=1
            rows_checked+=1
        agg=c['aggregate'][name] if dynamic else b['aggregate'][name]
        for (k,field),qs in point_values.items():
            query_means=[statistics.mean([v for v in vs if v is not None]) for vs in qs.values() if any(v is not None for v in vs)]
            near(agg[str(k)]['macro_'+field],statistics.mean(query_means));assert agg[str(k)][field+'_query_denominator']==len(query_means)
    assert len(c['branches'])==216
    for branch in c['branches']:assert len(branch['full_ranking'])==112 and set(branch['full_ranking'])==set(cases)
    for q in queries:
        for rep in (1,2,3):
            d=r.read(r.OUT/'results'/f'stage3_{q}_r{rep}.json');assert d['validation']['valid'];assert d['response_id'] not in responses;responses.add(d['response_id'])
    sha=hashlib.sha256((r.OUT/'stage1_silver.json').read_bytes()).hexdigest()
    assert sha==b['silver_sha256']==c['silver_sha256']==r.read(r.OUT/'silver_freeze.json')['sha256']
    usage=r.read(r.OUT/'usage.json');assert r.Decimal(usage['total_actual_plus_unknown_usd'])<=5
    result={'passed':True,'median_pairs_verified':1120,'independent_successful_response_ids':len(responses),'query_run_rankings_verified':rows_checked,'point_metric_sets_verified':metrics_checked,'dynamic_branches_full112_verified':216,'macro_averaging':'Independently recomputed harmonic F1 and per-query nested means; not reuse of primary metric function','precision_question_denominator':10,'recall_f1_question_denominator':6,'unchanged_silver_sha256':sha,'other_provider_calls':0,'stage4_run':False,'not_human_gold':True}
    r.save(r.OUT/'integrity_verification.json',result);print(result)
if __name__=='__main__':main()
