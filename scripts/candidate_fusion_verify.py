"""Independent Decimal arithmetic and metric checks against saved source ranks."""
import csv
import math
import statistics
from collections import defaultdict
from decimal import Decimal,localcontext
from functools import cmp_to_key
from scripts import candidate_fusion_ablation as c

def near(a,b):
    assert (a is None)==(b is None)
    if a is not None:assert math.isclose(float(a),float(b),rel_tol=1e-12,abs_tol=1e-14)
def fractional(s):
    x=s.split('/');return Decimal(x[0])/Decimal(x[1]) if len(x)==2 else Decimal(s)
def decimal_order(values):
    def compare(a,b):
        diff=values[a]-values[b]
        if abs(diff)<Decimal('1e-48'):return (a>b)-(a<b)
        return -1 if diff>0 else 1
    return sorted(values,key=cmp_to_key(compare))

def main():
    manifest=c.read(c.OUT/'preregistration.json');assert c.digest(c.CFG)==manifest['config_canonical_sha256']
    for x in manifest['inputs']:assert c.sha(c.ROOT/x['path'])==x['sha256']
    cases,labels,s2,s3,groups,raw=c.load();result=c.read(c.OUT/'results.json');systems=result['systems'];scores=c.read(c.OUT/'rrf_score_details.json')['rows']
    details={(r['backbone'],r['qid'],r['repeat'],r['cid']):r for r in scores};assert len(details)==6720
    ranking_count=0;metric_count=0
    for system,rows in systems.items():
        backbone,method=system.split('__');dynamic=method!='original';assert len(rows)==(30 if dynamic else 10)
        recomputed=defaultdict(lambda:defaultdict(list))
        for row in rows:
            ranking=row['ranking'];assert len(ranking)==112 and set(ranking)==set(cases)
            relevant={cid for cid,g in labels[row['qid']].items() if g>=3}
            for k in (5,10,20):
                tp=len(set(ranking[:k])&relevant);p=tp/k;r=tp/len(relevant) if relevant else None
                f1=2*p*r/(p+r) if r is not None and p+r else 0 if r==0 else None
                m=row['metrics'][str(k)];assert m['true_positives']==tp and m['precision_denominator']==k and m['recall_denominator']==len(relevant)
                for field,v in [('precision',p),('recall',r),('f1',f1)]:near(m[field],v);recomputed[(k,field)][row['qid']].append(v)
                metric_count+=1
            if method=='round_robin':
                old_name=c.BACKBONES[backbone][1];old=next(x for x in s3['systems'][old_name] if x['qid']==row['qid'] and x['repeat']==row['repeat'])
                assert ranking[:20]==old['ranking']
                for k in (5,10,20):
                    for field in ('precision','recall','f1'):near(row['metrics'][str(k)][field],old['metrics'][str(k)][field])
            ranking_count+=1
        for (k,field),by in recomputed.items():
            means=[statistics.mean(v for v in vs if v is not None) for vs in by.values() if any(v is not None for v in vs)]
            near(result['aggregate'][system][str(k)]['macro_'+field],statistics.mean(means));assert result['aggregate'][system][str(k)][field+'_question_denominator']==len(means)
    with localcontext() as ctx:
        ctx.prec=60
        for backbone,(orig_name,dyn_name) in c.BACKBONES.items():
            originals={r['qid']:r['ranking'] for r in s2['systems'][orig_name]}
            for q in sorted(labels):
                for rep in (1,2,3):
                    key=(dyn_name,q,rep);branches=groups[key];n=Decimal(len(branches));original=originals[q]
                    mp={};mix={}
                    for cid in cases:
                        d=details[(backbone,q,rep,cid)];assert len(d['terms'])==len(branches)
                        v=Decimal(0)
                        for t,(pid,ranks) in zip(d['terms'],branches.items()):
                            rank=ranks.index(cid)+1;term=Decimal(1)/(60+rank)/n
                            assert t['perspective_id']==pid and t['rank']==rank and t['original_similarity']==raw[key][pid]['full_scores'][cid]
                            assert abs(fractional(t['normalized_contribution_exact'])-term)<Decimal('1e-48')
                            v+=term
                        ori=Decimal(1)/(60+original.index(cid)+1);mp[cid]=v;mix[cid]=(ori+v)/2
                        near(d['multi_mean_score'],v);near(d['mixed_score'],mix[cid]);assert abs(fractional(d['mixed_exact'])-mix[cid])<Decimal('1e-48')
                    for method,expected in [('mean_rrf',decimal_order(mp)),('original_plus_mean_rrf',decimal_order(mix))]:
                        saved=next(r for r in systems[backbone+'__'+method] if r['qid']==q and r['repeat']==rep)
                        assert saved['ranking']==expected,'Decimal reordering differs'
    with (c.OUT/'case_rank_changes.csv').open(encoding='utf-8-sig',newline='') as f:rankrows=list(csv.DictReader(f))
    assert len(rankrows)==6720
    targets=c.read(c.OUT/'target_case_walkthrough.json')['cases'];target=next(x for x in targets if x['backbone']=='single_dense' and x['repeat']==1 and x['cid']=='AXV2N_0121')
    assert (target['original_rank'],target['rr_top20_rank'],target['rrf_rank'],target['original_mix_rank'])==(3,None,6,5)
    target2=next(x for x in targets if x['backbone']=='single_dense' and x['repeat']==1 and x['cid']=='AXV2N_0124')
    assert (target2['original_rank'],target2['rr_top20_rank'],target2['rrf_rank'],target2['original_mix_rank'])==(25,13,27,25)
    mismatch=c.read(c.OUT/'functional_mismatch_example.json');assert mismatch['existing_silver_score']==0
    assert tuple(int(mismatch['rank_changes'][k]) for k in ('round_robin_continuation_rank','mean_rrf_rank','original_plus_mean_rrf_rank'))==(7,28,33)
    assert all(c.sha(c.ROOT/x['path'])==x['sha256'] for x in manifest['inputs'])
    out={'passed':True,'unchanged_input_files':len(manifest['inputs']),'reproduced_rr_runs':60,'full_rankings_verified':ranking_count,'metric_sets_independently_verified':metric_count,'rrf_candidate_calculations_verified':6720,'precision':'60-digit Decimal recalculation independent of Fraction fusion implementation','tie_policy':'Differences below1e-48 treated as exact tie; true rational gaps are much larger','candidate_count_each':112,'fixed_original_group_weight':.5,'fixed_multi_group_weight':.5,'precision_questions':10,'recall_f1_questions':6,'required_two_case_examples_verified':True,'api_calls':0,'stage4_access':False}
    c.save('verification.json',out);print(out)
if __name__=='__main__':main()
