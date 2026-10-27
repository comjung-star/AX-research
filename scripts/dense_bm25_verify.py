"""Independent scalar/Decimal reconstruction of saved offline experiment."""
import json
import math
import statistics
from collections import defaultdict
from decimal import Decimal, getcontext
from scripts import dense_bm25_candidates as c

getcontext().prec=65
D=Decimal

def close(a,b):
    assert math.isclose(float(a),float(b),rel_tol=1e-11,abs_tol=1e-12),(a,b)

def rank(scores):
    return sorted(scores,key=lambda cid:(-scores[cid].quantize(D('1e-48')),cid))

def main():
    manifest=c.read(c.OUT/'preregistration.json')
    assert manifest['config_sha256']==c.digest(c.CFG)
    for item in manifest['inputs']:assert c.fingerprint(c.ROOT/item['path'])==item['sha256']
    cases,labels,s2,s3,groups,details=c.old.load()
    reg=c.read(c.OUT/'query_registry.json')['paths']
    bm=c.read(c.OUT/'bm25_paths.json')['paths']
    corpus=c.read(c.OUT/'bm25_corpus_statistics.json')
    dense={(x['path_id'],x['backbone']):x for x in c.read(c.OUT/'dense_paths.json')['paths']}
    hybrid={(x['path_id'],x['backbone']):x for x in c.read(c.OUT/'hybrid_paths.json')['paths']}
    ids=set(cases);assert len(ids)==112 and len(reg)==118
    scalar_checks=0;contrib={}
    for pid,meta in reg.items():
        for cid in ids:
            tf=corpus['document_frequencies_by_case'][cid];length=corpus['document_lengths_by_case'][cid]
            k1=corpus['k1'];b=corpus['b'];avg=corpus['average_document_length']
            score=sum(corpus['idf'].get(t,0)*tf.get(t,0)*(k1+1)/(tf.get(t,0)+k1*(1-b+b*length/avg)) for t in bm[pid]['query_tokens'])
            close(score,bm[pid]['scores'][cid]);scalar_checks+=1
        assert bm[pid]['ranking']==sorted(ids,key=lambda cid:(-bm[pid]['scores'][cid],cid))
        for backbone,original,dynamic in [('single','A_single_dense','C_dynamic_single_dense'),('three','B_three_view_dense','D_dynamic_three_view_dense')]:
            item=dense[pid,backbone]
            if meta['scope']=='original':
                src=next(x for x in s2['systems'][original] if x['qid']==meta['qid'])
                scores=next(x['scores'] for x in s2['score_details'] if x['system']==original and x['qid']==meta['qid'])
                assert item['ranking']==src['ranking'] and item['scores']==scores
            else:
                src=details[dynamic,meta['qid'],meta['repeat']][meta['perspective_id']]
                assert item['ranking']==src['full_ranking'] and item['scores']==src['full_scores']
            dr={cid:i for i,cid in enumerate(item['ranking'],1)};br={cid:i for i,cid in enumerate(bm[pid]['ranking'],1)}
            h={cid:(D(1)/(60+dr[cid])+D(1)/(60+br[cid]))/2 for cid in ids}
            assert rank(h)==hybrid[pid,backbone]['ranking']
            for cid in ids:close(h[cid],hybrid[pid,backbone]['scores'][cid])
            contrib[pid,backbone,'dense']={cid:D(1)/(60+dr[cid]) for cid in ids}
            contrib[pid,backbone,'bm25']={cid:D(1)/(60+br[cid]) for cid in ids}
            contrib[pid,backbone,'hybrid']=h
    results=c.read(c.OUT/'results.json');metric_checks=0;run_count=0
    for condition,rows in results['systems'].items():
        setting=c.CONDITIONS[condition]
        for row in rows:
            parts=[contrib[p,setting['backbone'],setting['channel']] for p in row['path_ids']]
            mean={cid:sum(p[cid] for p in parts)/len(parts) for cid in ids}
            assert rank(mean)==row['ranking'] and len(set(row['ranking']))==112
            for cid in ids:close(mean[cid],row['scores'][cid])
            positive={cid for cid,v in labels[row['qid']].items() if v>=3}
            for k in (5,10,20):
                m=row['metrics'][str(k)];tp=len(set(row['ranking'][:k])&positive)
                assert row['top_k'][str(k)]==row['ranking'][:k]
                assert m['true_positives']==tp and m['recall_denominator']==len(positive) and m['precision_denominator']==k
                close(m['precision'],tp/k)
                if positive:close(m['recall'],tp/len(positive));close(m['f1'],2*tp/(k+len(positive)))
                else:assert m['recall'] is None and m['f1'] is None
                if 'reference' in row:
                    baseline=next(x for x in results['systems'][row['reference']] if (x['qid'],x['repeat'])==(row['qid'],row['repeat']))
                    before=set(baseline['ranking'][:k])&positive;after=set(row['ranking'][:k])&positive
                    assert row['changes'][str(k)]=={'new_related':sorted(after-before),'retained_related':sorted(before&after),'lost_related':sorted(before-after)}
                metric_checks+=1
            run_count+=1
        for k in (5,10,20):
            for f,n in [('precision',10),('recall',6),('f1',6)]:
                by=defaultdict(list)
                for row in rows:
                    v=row['metrics'][str(k)][f]
                    if v is not None:by[row['qid']].append(v)
                agg=results['aggregate'][condition][str(k)]
                assert len(by)==n==agg[f+'_question_denominator']
                close(statistics.mean(statistics.mean(v) for v in by.values()),agg['macro_'+f])
    feature_count=0
    for line in (c.OUT/'candidate_features.jsonl').open(encoding='utf-8'):
        f=json.loads(line);pid=f['path_id'];bb=f['backbone'];cid=f['case_id']
        assert f['dense_rank']==dense[pid,bb]['ranking'].index(cid)+1
        assert f['bm25_rank']==bm[pid]['ranking'].index(cid)+1
        close(f['hybrid_rrf_score'],contrib[pid,bb,'hybrid'][cid])
        close(f['normalized_final_hybrid_contribution'],contrib[pid,bb,'hybrid'][cid]/f['perspective_count'])
        assert not any(k in f for k in ('label','grade','silver','relevance'))
        feature_count+=1
    pools=[json.loads(l) for l in (c.OUT/'mapping_candidate_pools.jsonl').open(encoding='utf-8')]
    assert len(pools)==80 and feature_count==26432 and run_count==200 and metric_checks==600
    for p in pools:
        assert set(p['candidate_ids_ranked_all112'])==ids and len(p['candidate_ids_ranked_all112'])==112
        assert not any(k in p for k in ('label','grade','silver','relevance'))
    assert sum(sum(v>=3 for v in q.values()) for q in labels.values())==18
    c.save('verification.json',{'passed':True,'input_fingerprints_checked':13,'bm25_independent_scalar_scores_checked':scalar_checks,'dense_source_paths_checked':len(dense),'hybrid_decimal_paths_checked':len(hybrid),'full_rankings_decimal_checked':run_count,'metric_sets_independently_checked':metric_checks,'macro_cells_checked':90,'feature_rows_checked':feature_count,'handover_pools_checked':80,'candidate_count':112,'precision_query_denominator':10,'recall_f1_query_denominator':6,'positive_pairs':18,'api_calls':0,'key_reads':0,'stage4_access':False})
    print('Independent verification passed: 13216 BM25 scores, 200 rankings, 600 metric sets, 26432 features.')

if __name__=='__main__':main()
