"""Offline result tables, frozen-label sensitivity and Korean report artifacts."""
import csv
import hashlib
import statistics
import subprocess
from collections import Counter,defaultdict
import numpy as np
from scripts import openai_triplicate as r
from scripts import openai_triplicate_search as s

def write_csv(name,rows):
    if not rows:return
    with (r.OUT/name).open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def historical():
    with (r.ROOT/'data/v2_3/ground_truth/silver_dev_qrels_2520.csv').open(encoding='utf-8-sig',newline='') as f:old=list(csv.DictReader(f))
    triples=[[int(x[f'score_pass{i}']) for i in (1,2,3)] for x in old]
    d={'dataset':'v2.3 84cases x30reference aspects; not current112x10whole queries','pairs':len(old),'scores':len(old)*3,'exact_agreement_pairs':sum(len(set(x))==1 for x in triples),'binary_flip_pairs':sum(len({v>=3 for v in x})>1 for x in triples),'median_distribution':dict(Counter(int(x['relevance_0_4']) for x in old)),'human_gold':False,'not_direct_performance_improvement_comparison':True}
    r.save(r.OUT/'v23_comparison.json',d);return d

def main():
    labels=s.frozen_labels();silver=r.read(r.OUT/'stage1_silver.json');stage2=r.read(r.OUT/'stage2_results.json');stage3=r.read(r.OUT/'stage3_results.json');old=historical();cs,qs=r.inputs()
    r.usage_report()
    ratings=[]
    for x in silver['records']:
        by={v['repeat']:v for v in x['ratings']}
        ratings.append({'query_id':x['qid'],'case_id':x['cid'],'score_r1':by.get(1,{}).get('score'),'score_r2':by.get(2,{}).get('score'),'score_r3':by.get(3,{}).get('score'),'median':x['median'],'released_silver_score':x['silver_score'],'relevant':x['relevant'],'held':x['held'],'exact_agreement':x['exact_agreement'],'binary_flip':x['binary_flip'],'reason_r1':by.get(1,{}).get('reason'),'reason_r2':by.get(2,{}).get('reason'),'reason_r3':by.get(3,{}).get('reason'),'review_flags':'|'.join(x['review_flags']),'human_gold':False,'model':r.MODEL})
    write_csv('stage1_triplicate_scores.csv',ratings)
    macro=[];query_rows=[]
    allsys={**stage2['systems'],**stage3['systems']}
    for name,rows in allsys.items():
        agg=stage2['aggregate'].get(name,stage3['aggregate'].get(name))
        for k in s.K_VALUES:
            z=agg[str(k)];macro.append({'system':name,'k':k,'macro_precision':z['macro_precision'],'macro_recall':z['macro_recall'],'macro_f1':z['macro_f1'],'original_query_count':10,'generation_repeats':3 if name.startswith(('C_','D_')) else 1,'precision_query_denominator':z['precision_query_denominator'],'recall_query_denominator':z['recall_query_denominator'],'f1_query_denominator':z['f1_query_denominator'],'held_labels':silver['held_pairs']})
        for row in rows:
            for k in s.K_VALUES:
                z=row['metrics'][str(k)];query_rows.append({'system':name,'query_id':row['qid'],'repeat':row.get('repeat',1),'k':k,'precision':z['precision'],'recall':z['recall'],'f1':z['f1'],'true_positives':z['tp'],'precision_denominator':z['precision_denominator'],'recall_denominator':z['recall_denominator'],'unknown_in_top_k':z['unknown_in_top_k'],'scope':z['point_scope']})
    write_csv('macro_metrics.csv',macro);write_csv('query_run_metrics.csv',query_rows)
    # No new labels: same rankings under prespecified threshold/pass sensitivity.
    sensitivity={}
    for labelset in ('median_t2','median_t3','median_t4','pass1_t3','pass2_t3','pass3_t3'):
        threshold=int(labelset[-1]);alt=defaultdict(dict)
        for x in silver['records']:
            grade=x['silver_score']
            if labelset.startswith('pass'):
                passid=int(labelset[4]);grade=next((a['score'] for a in x['ratings'] if a['repeat']==passid),None) if not x['held'] else None
            alt[x['qid']][x['cid']]=grade
        result={}
        for name,rows in allsys.items():result[name]=s.aggregate([{'metrics':{str(k):s.metrics(row['ranking'],alt[row['qid']],k,threshold) for k in s.K_VALUES}} for row in rows])
        sensitivity[labelset]=result
    r.save(r.OUT/'label_sensitivity.json',{'results':sensitivity,'policy':'Frozen scores only; no post-retrieval label editing. Exploratory evaluator/threshold sensitivity, no independent validation.'})
    # Diversity: source-group coverage and document-vector variety are proxies,
    # not relevance or reference-aspect coverage.
    cache=np.load(r.OUT/'embeddings.npz');ids=cache['case_ids'].tolist();index={c:i for i,c in enumerate(ids)};vectors=cache['single'];diversity=[]
    for name,rows in allsys.items():
        for row in rows:
            for k in s.K_VALUES:
                top=row['ranking'][:k];m=vectors[[index[c] for c in top]];sims=m@m.T
                diversity.append({'system':name,'qid':row['qid'],'repeat':row.get('repeat',1),'k':k,'distinct_source_groups':len({cs[c]['leakage_group_id'] for c in top}),'semantic_case_diversity_1_minus_mean_cosine':float(1-(sims.sum()-k)/(k*(k-1)))})
    write_csv('case_diversity.csv',diversity)
    diffs=[]
    baselines={name:{row['qid']:row for row in rows} for name,rows in stage2['systems'].items()}
    for q in sorted(qs):
        a=baselines['A_single_dense'][q];b=baselines['B_three_view_dense'][q];pos={c for c,g in labels[q].items() if g is not None and g>=3}
        for k in s.K_VALUES:
            gain=sorted((set(b['ranking'][:k])-set(a['ranking'][:k]))&pos);loss=sorted((set(a['ranking'][:k])-set(b['ranking'][:k]))&pos)
            diffs.append({'comparison':'B_minus_A','qid':q,'k':k,'new_related':gain,'lost_related':loss,'shared_related':sorted(set(a['ranking'][:k])&set(b['ranking'][:k])&pos),'new_related_tasks':{c:cs[c]['task'] for c in gain},'lost_related_tasks':{c:cs[c]['task'] for c in loss}})
    for name,rows in stage3['systems'].items():
        for row in rows:
            for k in s.K_VALUES:diffs.append({'comparison':'C_minus_A' if name.startswith('C_') else 'D_minus_B','qid':row['qid'],'repeat':row['repeat'],'k':k,**row['related_changes'][str(k)]})
    r.save(r.OUT/'related_case_changes.json',{'records':diffs,'tasks_are_original_source_summaries':True})
    attribution=[]
    branch_map=defaultdict(list)
    for branch in stage3['branches']:branch_map[(branch['system'],branch['qid'],branch['repeat'])].append(branch)
    for name,rows in stage3['systems'].items():
        parent='A_single_dense' if name.startswith('C_') else 'B_three_view_dense'
        for result in rows:
            q=result['qid'];rep=result['repeat'];original=baselines[parent][q]['ranking'];owner={cid:pid for pid,cid in result['selected_with_branch']}
            changes=result['related_changes']['20']
            for change in ('new_related','lost_related'):
                for cid in changes[change]:
                    branches=branch_map[(name,q,rep)]
                    attribution.append({'system':name,'qid':q,'repeat':rep,'k':20,'change':change,'cid':cid,'actual_task':cs[cid]['task'],'silver_score':labels[q][cid],'original_rank':original.index(cid)+1,'dynamic_final_rank':result['ranking'].index(cid)+1 if cid in result['ranking'] else None,'selected_by_perspective':owner.get(cid),'branches':[{'title':b['perspective']['title'],'description':b['perspective']['description'],'local_rank':b['full_ranking'].index(cid)+1} for b in branches],'interpretation':'Ranks and source-backed task show which problem framing gained/lost the case; not a causal attribution or a new relevance judgment.'})
    r.save(r.OUT/'changed_case_attribution.json',{'records':attribution})
    qsummary=[]
    for q in sorted(qs):
        grades=[x for x in silver['records'] if x['qid']==q];d={'qid':q,'question':qs[q],'relevant':sum(x['relevant'] is True for x in grades),'held':sum(x['held'] for x in grades)}
        for name,rows in allsys.items():
            rs=[x for x in rows if x['qid']==q]
            d[name]={str(k):{field:statistics.mean([x['metrics'][str(k)][field] for x in rs if x['metrics'][str(k)][field] is not None]) if any(x['metrics'][str(k)][field] is not None for x in rs) else None for field in ('precision','recall','f1')} for k in s.K_VALUES}
        qsummary.append(d)
    r.save(r.OUT/'question_summary.json',{'records':qsummary})
    manifest=[]
    for path in (r.DATA/'dev_problem_views.csv',r.DATA/'dev_queries.json',r.DATA/'split_groups.csv',r.ROOT/'data/v2_3/ground_truth/silver_dev_qrels_2520.csv'):
        rel=str(path.relative_to(r.ROOT)).replace('\\','/');blob=subprocess.check_output(['git','show',r.BASE+':'+rel],cwd=r.ROOT)
        assert blob==path.read_bytes();manifest.append({'path':rel,'sha256':hashlib.sha256(blob).hexdigest(),'unchanged_from_base':True})
    r.save(r.OUT/'preservation.json',{'inputs':manifest,'stage4_run':False,'other_provider_calls':0})
    r.save(r.OUT/'final_status.json',{'stages_completed':[1,2,3],'model':r.MODEL,'distinct_models':1,'score_repeats':3,'scores':silver['received_scores'],'median_pairs':sum(x['median'] is not None for x in silver['records']),'held_pairs':silver['held_pairs'],'perspective_generations':30,'human_gold':False,'stage4':'sealed','branch':'research/stage123-openai-triplicate-20261027','commit_record':'See publication.json and Git HEAD; commit IDs cannot be embedded in their own tree without a second commit.','silver_sha256':stage2['silver_sha256'],'actual_and_reserved_cost':r.read(r.OUT/'usage.json')['total_actual_plus_unknown_usd']})
    print({'macro':macro,'v23':old})
if __name__=='__main__':main()
