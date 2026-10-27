"""Offline fixed-rank fusion ablation. No model/client/key or encoder imports."""
import argparse
import csv
import hashlib
import json
import socket
import statistics
import subprocess
from collections import Counter,defaultdict
from fractions import Fraction
from pathlib import Path
import numpy as np
from ax_research.selection import branch_balanced_unique

ROOT=Path(__file__).resolve().parents[1]
CONFIG=ROOT/'configs/candidate_fusion_ablation_20261027.json'
CFG=json.loads(CONFIG.read_text(encoding='utf-8-sig'))
SOURCE=ROOT/CFG['input_directory'];OUT=ROOT/CFG['output_directory']
BACKBONES={'single_dense':('A_single_dense','C_dynamic_single_dense'),'three_view_dense':('B_three_view_dense','D_dynamic_three_view_dense')}
INPUTS=[SOURCE/n for n in ('stage2_results.json','stage3_results.json','related_case_changes.json','changed_case_attribution.json','stage1_silver.json','silver_freeze.json','embeddings.npz','plan.json','perspective_review.json')]+[ROOT/'data/v2_5/research'/n for n in ('dev_problem_views.csv','dev_queries.json','split_groups.csv')]

def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def digest(d):return hashlib.sha256(json.dumps(d,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
def save(name,d):
    path=OUT/name;path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def csv_save(name,rows):
    if rows:
        with (OUT/name).open('w',encoding='utf-8-sig',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def prepare():
    inputs=[]
    for p in INPUTS:
        rel=p.relative_to(ROOT).as_posix();original=subprocess.check_output(['git','show',CFG['base_commit']+':'+rel],cwd=ROOT)
        assert original==p.read_bytes(),'Base input modified: '+rel
        inputs.append({'path':rel,'sha256':sha(p),'unchanged_from_base':True})
    manifest={'config':CFG,'config_canonical_sha256':digest(CFG),'preregistered_config_commit':subprocess.check_output(['git','log','-1','--format=%H','--',str(CONFIG.relative_to(ROOT))],cwd=ROOT,text=True).strip(),'inputs':inputs,'network_connections_permitted':False,'api_calls':0,'api_key_reads':0,'stage4_access':False}
    f=OUT/'preregistration.json'
    if f.exists():assert read(f)==manifest,'Frozen input/config manifest changed'
    save('preregistration.json',manifest);return manifest

def load():
    silver=read(SOURCE/'stage1_silver.json');s2=read(SOURCE/'stage2_results.json');s3=read(SOURCE/'stage3_results.json')
    assert sha(SOURCE/'stage1_silver.json')==read(SOURCE/'silver_freeze.json')['sha256']==s2['silver_sha256']==s3['silver_sha256']
    with (ROOT/'data/v2_5/research/dev_problem_views.csv').open(encoding='utf-8-sig',newline='') as f:cases={r['case_id']:r for r in csv.DictReader(f)}
    labels=defaultdict(dict)
    for r in silver['records']:
        assert not r['held'] and type(r['silver_score'])is int
        labels[r['qid']][r['cid']]=r['silver_score']
    assert len(cases)==112 and len(labels)==10 and sum(v>=3 for g in labels.values() for v in g.values())==18
    z=np.load(SOURCE/'embeddings.npz')
    assert set(z['case_ids'].tolist())==set(cases)
    for key in ('single','problem','task','context'):assert z[key].shape==(112,1024) and np.isfinite(z[key]).all()
    groups=defaultdict(dict);details=defaultdict(dict)
    for b in s3['branches']:
        key=(b['system'],b['qid'],b['repeat']);pid=b['perspective']['id']
        assert pid not in groups[key] and len(b['full_ranking'])==112 and set(b['full_ranking'])==set(cases)
        assert set(b['full_scores'])==set(cases)
        expected=sorted(cases,key=lambda c:(-b['full_scores'][c],c));assert expected==b['full_ranking']
        groups[key][pid]=b['full_ranking'];details[key][pid]=b
    assert sum(len(v) for v in groups.values())==216 and len(groups)==60
    return cases,labels,s2,s3,groups,details

def rr_trace(branches,k=112):
    cursors={p:0 for p in branches};seen=set();out=[];round_id=0
    while len(out)<k:
        round_id+=1;added=False
        for pid,ranking in branches.items():
            skipped=[]
            while cursors[pid]<len(ranking):
                cid=ranking[cursors[pid]];cursors[pid]+=1
                if cid in seen:skipped.append(cid);continue
                seen.add(cid);out.append({'selection_rank':len(out)+1,'round':round_id,'perspective_id':pid,'local_rank':cursors[pid],'cid':cid,'skipped_duplicate_case_ids':skipped,'cursors_after_selection':dict(cursors)})
                added=True;break
            if len(out)>=k:break
        if not added:break
    assert [(x['perspective_id'],x['cid']) for x in out]==branch_balanced_unique(branches,k)
    return out

def fuse(branches,original,kappa=60):
    ids=list(original);assert len(ids)==len(set(ids))
    assert all(set(v)==set(ids) and len(v)==len(ids) for v in branches.values())
    ranks={p:{c:i for i,c in enumerate(rank,1)} for p,rank in branches.items()};orig={c:i for i,c in enumerate(original,1)};count=len(branches)
    assert count>0
    multi={c:sum((Fraction(1,kappa+ranks[p][c]) for p in branches),Fraction(0))/count for c in ids}
    anchor={c:Fraction(1,kappa+orig[c]) for c in ids};mixed={c:(multi[c]+anchor[c])/2 for c in ids}
    order=lambda d:sorted(ids,key=lambda c:(-d[c],c))
    return {'mean_rrf':order(multi),'original_plus_mean_rrf':order(mixed)},multi,anchor,mixed,ranks

def metrics(ranking,grades,k):
    ids=ranking[:k];assert len(ids)==k and len(set(ids))==k
    relevant={c for c,s in grades.items() if s>=CFG['relevance_threshold']};tp=len(set(ids)&relevant);r=len(relevant)
    return {'k':k,'true_positives':tp,'precision_denominator':k,'recall_denominator':r,'precision':tp/k,'recall':tp/r if r else None,'f1':2*tp/(k+r) if r else None,'related_ids':sorted(set(ids)&relevant)}

def aggregate(rows):
    # Always average repeats within query first, including any undefined fields.
    out={}
    for k in CFG['K']:
        cell={'original_queries':len({x['qid'] for x in rows}),'query_runs':len(rows)}
        for field in ('precision','recall','f1'):
            by=defaultdict(list)
            for r in rows:
                v=r['metrics'][str(k)][field]
                if v is not None:by[r['qid']].append(v)
            means=[statistics.mean(vs) for vs in by.values()]
            cell['macro_'+field]=statistics.mean(means) if means else None
            cell[field+'_question_denominator']=len(means)
        cell['sum_true_positive_events']=sum(r['metrics'][str(k)]['true_positives'] for r in rows)
        for field in ('new_related','retained_related','lost_related'):
            by=defaultdict(list)
            for r in rows:
                if 'changes' in r:by[r['qid']].append(len(r['changes'][str(k)][field]))
            cell['mean_'+field+'_per_query_run']=statistics.mean(statistics.mean(v) for v in by.values()) if by else None
        out[str(k)]=cell
    return out

def run():
    manifest=prepare();cases,labels,s2,s3,groups,details=load()
    systems={};contributions=[];traces=[];rank_rows=[];events=[];pool_diag=[];query_rows=[]
    baseline={name:{r['qid']:r for r in rows} for name,rows in s2['systems'].items()}
    previous={name:{(r['qid'],r['repeat']):r for r in rows} for name,rows in s3['systems'].items()}
    for backbone,(orig_name,dyn_name) in BACKBONES.items():
        systems[backbone+'__original']=[{'qid':q,'ranking':row['ranking'],'metrics':{str(k):metrics(row['ranking'],labels[q],k) for k in CFG['K']}} for q,row in baseline[orig_name].items()]
        for method in CFG['methods']:systems[backbone+'__'+method]=[]
        for q in sorted(labels):
            for rep in (1,2,3):
                key=(dyn_name,q,rep);branches=groups[key];original=baseline[orig_name][q]['ranking'];relevant={c for c,g in labels[q].items() if g>=3}
                trace=rr_trace(branches);rr=[x['cid'] for x in trace]
                assert rr[:20]==previous[dyn_name][(q,rep)]['ranking'],'Historical RR not reproduced'
                cursors20=trace[19]['cursors_after_selection'];rr20=set(rr[:20]);traces.append({'backbone':backbone,'qid':q,'repeat':rep,'perspective_order':list(branches),'trace':trace,'historical_top20_reproduced':True})
                rankings,multi,anchor,mixed,ranks=fuse(branches,original,CFG['rrf_constant']);rankings={'round_robin':rr,**rankings}
                for cid in sorted(cases):
                    term=[{'perspective_id':p,'title':details[key][p]['perspective']['title'],'rank':ranks[p][cid],'original_similarity':details[key][p]['full_scores'][cid],'reciprocal':float(Fraction(1,60+ranks[p][cid])),'normalized_contribution_exact':str(Fraction(1,60+ranks[p][cid])/len(branches)),'normalized_contribution':float(Fraction(1,60+ranks[p][cid])/len(branches))} for p in branches]
                    contributions.append({'backbone':backbone,'qid':q,'repeat':rep,'cid':cid,'perspectives':len(branches),'original_rank':original.index(cid)+1,'original_path_score':float(anchor[cid]),'original_path_exact':str(anchor[cid]),'multi_mean_score':float(multi[cid]),'multi_mean_exact':str(multi[cid]),'mixed_score':float(mixed[cid]),'mixed_exact':str(mixed[cid]),'original_weight':.5,'multi_group_weight':.5,'terms':term})
                    rank_rows.append({'backbone':backbone,'qid':q,'repeat':rep,'cid':cid,'silver_score':labels[q][cid],'original_rank':original.index(cid)+1,'round_robin_continuation_rank':rr.index(cid)+1,'mean_rrf_rank':rankings['mean_rrf'].index(cid)+1,'original_plus_mean_rrf_rank':rankings['original_plus_mean_rrf'].index(cid)+1,'best_local_rank':min(r[cid] for r in ranks.values()),'mean_local_rank':statistics.mean(r[cid] for r in ranks.values()),'multi_mean_score':float(multi[cid]),'mixed_score':float(mixed[cid])})
                for cutoff in (5,10,20,112):
                    pool={c for ranking in branches.values() for c in ranking[:cutoff]}
                    pool_diag.append({'backbone':backbone,'qid':q,'repeat':rep,'local_depth_diagnostic_only':cutoff,'unique_candidates':len(pool),'known_related_candidates':len(pool&relevant),'recall_denominator':len(relevant),'candidate_coverage':len(pool&relevant)/len(relevant) if relevant else None,'note':'No truncation used in fusion; depth is posthoc pool diagnosis, not final-K performance.'})
                for method,ranking in rankings.items():
                    changes={}
                    for k in CFG['K']:
                        before=set(original[:k])&relevant;after=set(ranking[:k])&relevant
                        changes[str(k)]={'new_related':sorted(after-before),'retained_related':sorted(after&before),'lost_related':sorted(before-after)}
                    result={'qid':q,'repeat':rep,'ranking':ranking,'top_k':{str(k):ranking[:k] for k in CFG['K']},'metrics':{str(k):metrics(ranking,labels[q],k) for k in CFG['K']},'changes':changes}
                    systems[backbone+'__'+method].append(result)
                for cid in sorted((set(original[:20])&relevant)-rr20):
                    local={p:ranks[p][cid] for p in branches};assert all(rank>cursors20[p] for p,rank in local.items())
                    events.append({'backbone':backbone,'qid':q,'repeat':rep,'cid':cid,'actual_task':cases[cid]['task'],'original_rank':original.index(cid)+1,'rr_continuation_rank':rr.index(cid)+1,'local_ranks':local,'rr_branch_cursors_at20':cursors20,'local_top5':min(local.values())<=5,'local_top10':min(local.values())<=10,'local_top20':min(local.values())<=20,'rrf_rank':rankings['mean_rrf'].index(cid)+1,'mixed_rank':rankings['original_plus_mean_rrf'].index(cid)+1,'rescued_by_rrf_at20':cid in rankings['mean_rrf'][:20],'rescued_by_original_mix_at20':cid in rankings['original_plus_mean_rrf'][:20],'exact_rr_exclusion_reason':'Every branch cursor stopped before this case at final20; case was present in all112-candidate rankings, not removed from initial pool.','causal_scope':'Only fusion differs in RR-vs-RRF. Original-mix additionally introduces original-query rank information.'})
    agg={name:aggregate(rows) for name,rows in systems.items()}
    for name,rows in systems.items():
        for r in rows:
            for k in CFG['K']:
                m=r['metrics'][str(k)];ch=r.get('changes',{}).get(str(k),{})
                query_rows.append({'system':name,'qid':r['qid'],'repeat':r.get('repeat',0),'k':k,'precision':m['precision'],'recall':m['recall'],'f1':m['f1'],'true_positives':m['true_positives'],'precision_denominator':k,'recall_denominator':m['recall_denominator'],'new_related':len(ch['new_related']) if ch else '', 'retained_related':len(ch['retained_related']) if ch else '', 'lost_related':len(ch['lost_related']) if ch else ''})
    macro=[{'system':n,'k':k,**d} for n,ks in agg.items() for k,d in ks.items()]
    old_counters={}
    for backbone in BACKBONES:
        es=[e for e in events if e['backbone']==backbone]
        old_counters[backbone]={'rr_original_positive_loss_events':len(es),'distinct_qid_case_pairs':len({(e['qid'],e['cid']) for e in es}),'had_any_local_top5':sum(e['local_top5'] for e in es),'had_any_local_top10':sum(e['local_top10'] for e in es),'had_any_local_top20':sum(e['local_top20'] for e in es),'fixed_rrf_rescues':sum(e['rescued_by_rrf_at20'] for e in es),'fixed_original_mix_rescues':sum(e['rescued_by_original_mix_at20'] for e in es),'event_scope':'30 dynamic query-runs compared with the once-evaluated original baseline; repeat references are not independent baseline experiments.'}
    save('results.json',{'config_sha256':digest(CFG),'systems':systems,'aggregate':agg,'human_gold':False,'api_calls':0,'api_cost_usd':'0.00','silver_sha256':sha(SOURCE/'stage1_silver.json'),'normalization':'mean over perspectives; fixed1:1 original versus multi aggregate','parameters_tuned_on_outcomes':False})
    save('rrf_score_details.json',{'rows':contributions,'formula':CFG['mixed_score'],'kappa':60,'exact_fraction_arithmetic':True})
    save('round_robin_trace.json',{'runs':traces,'continuation_to112_is_diagnostic':True})
    save('loss_mechanism.json',{'summary':old_counters,'events':events})
    save('candidate_pool_diagnostics.json',{'rows':pool_diag,'candidate_union_full112_is_trivial':True})
    csv_save('case_rank_changes.csv',rank_rows);csv_save('query_run_metrics.csv',query_rows);csv_save('macro_metrics.csv',macro)
    # Full expected scores and all input bytes are checked again after outputs.
    assert all(sha(ROOT/v['path'])==v['sha256'] for v in manifest['inputs'])
    save('preservation.json',{'passed':True,'inputs':manifest['inputs'],'all_originals_unchanged':True,'stage4_accessed':False,'api_calls':0,'api_keys_read':0,'new_embedding_inference':False})
    print(json.dumps({'macro20':{n:ks['20'] for n,ks in agg.items()},'loss_mechanism':old_counters},ensure_ascii=False))

def no_network(*args,**kwargs):raise RuntimeError('Offline experiment forbids network calls')
def main():
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['prepare','run']);a=p.parse_args()
    old_connect=socket.socket.connect;old_create=socket.create_connection
    socket.socket.connect=no_network;socket.create_connection=no_network
    try:prepare() if a.phase=='prepare' else run()
    finally:socket.socket.connect=old_connect;socket.create_connection=old_create
if __name__=='__main__':main()
