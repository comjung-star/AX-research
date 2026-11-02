"""Frozen C0/C1/C2/C3 Dev experiment. No heldout data, API or new embeddings."""
import argparse
from collections import defaultdict
import csv
import json
import math
from pathlib import Path
import platform
import socket
import subprocess

from ax_research.heldout import read,write,sha
from ax_research.functional_mapping import compare
from ax_research.semantic_mapping import ranking_key
from ax_research.action_aggregation import purpose_filter,allowed_branches,compose

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/action-disambiguation-aggregation-2026-11-02/experiment'
CFG=ROOT/'configs/action_aggregation_20261102.json';HIST=ROOT/'docs/query-case-functional-mapping-2026-10-28';SEM=ROOT/'docs/query-case-semantic-mapping-2026-10-28';RET=ROOT/'docs/dense-bm25-candidates-2026-10-27'
SUFFIX={'C':'O_SINGLE','F':'D_SINGLE','S_C3':'O_THREE','S_F3':'D_THREE'}
METHODS=('C0','C1','C2','C3','C1_NO_EMBEDDING','C3_NO_EMBEDDING')


def loadlines(p):
    with p.open(encoding='utf-8-sig') as s:return [json.loads(l) for l in s if l.strip()]


def csvsave(p,rows):
    with p.open('x',encoding='utf-8',newline='') as s:
        w=csv.DictWriter(s,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)


def state():
    from scripts.heldout_run import freeze
    model=(ROOT/read(ROOT/'configs/semantic_mapping_20261028.json')['model_path']).resolve();baseline=freeze(model)
    paths=[CFG,ROOT/'src/ax_research/action_aggregation.py',Path(__file__),ROOT/'tests/test_action_aggregation.py',ROOT/'docs/action-disambiguation-aggregation-2026-11-02/design.md']
    paths += [HIST/n for n in ('stage2/query_profiles.json','stage2/case_profiles.json','stage2/mappings.jsonl')]
    paths += [SEM/n for n in ('mapping/mappings.jsonl','ranking/rankings.json','ranking/explanations.jsonl')]
    paths += [RET/n for n in ('query_registry.json','case_registry.json','mapping_candidate_pools.jsonl','candidate_features.jsonl')]
    return {'base':read(CFG)['base'],'protected_original':baseline['protected'],'model_files':baseline['model'],'packages':baseline['packages'],'experiment_hashes':{p.relative_to(ROOT).as_posix():sha(p) for p in paths},'python':platform.python_version(),'platform':platform.platform(),'config':read(CFG),'network':'disabled','new_embeddings':0,'labels_read':False,'test_access':False}


def freeze(out):
    out.mkdir(parents=True,exist_ok=False)
    write(out/'freeze.json',{**state(),'implementation_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'design_commit':'515074df','command':'python -m scripts.action_aggregation_run {freeze,predict,evaluate} --output NEW_DIR'})


def verify(out):
    f=read(out/'freeze.json');assert all(f[k]==v for k,v in state().items()),'Frozen code/input/model/environment drift'


def predict(out):
    verify(out)
    if (out/'prediction_receipt.json').exists():raise FileExistsError('Predictions already sealed')
    cfg=read(CFG);cases=read(RET/'case_registry.json')['cases'];qs=read(RET/'query_registry.json')['paths'];ids=sorted(cases)
    oldcp=read(HIST/'stage2/case_profiles.json');oldqp=read(HIST/'stage2/query_profiles.json')
    cp={c:{role:purpose_filter(p,cfg) for role,p in fields.items()} for c,fields in oldcp.items()};qp={p:purpose_filter(q,cfg) for p,q in oldqp.items()}
    old={(r['path_id'],r['case_id']):r for r in loadlines(HIST/'stage2/mappings.jsonl')};sem={(r['path_id'],r['case_id']):r for r in loadlines(SEM/'mapping/mappings.jsonl')}
    new={(p,c):compare(qp[p],cp[c]) for p in qs for c in ids}
    assert len(ids)==112 and len(qs)==118 and len(new)==13216
    systems={};details=[];checks=0;oldrank=read(SEM/'ranking/rankings.json')['systems']
    # C0 score reference is the original semantic experiment, not the previous improvement.
    oldex={(r['condition'],r['qid'],r['repeat'],r['case_id']):r for r in loadlines(SEM/'ranking/explanations.jsonl')}
    for pool in loadlines(RET/'mapping_candidate_pools.jsonl'):
        suf=SUFFIX[pool['condition']];op='o_'+pool['qid'];ps=[p for p in pool['path_ids'] if qs[p]['scope']=='dynamic'];scores={m:{} for m in METHODS};gates={}
        for c in ids:
            bg={p:old[p,c]['mapping_grade'] for p in ps};ng={p:new[p,c]['mapping_grade'] for p in ps};bs={p:sem[p,c]['score'] for p in ps};b0=sem[op,c]['score'];g0=old[op,c]['mapping_grade'];g1=new[op,c]['mapping_grade']
            allow0=allowed_branches(oldqp[op],{p:oldqp[p] for p in ps},oldcp[c]['task']);allow1=allowed_branches(qp[op],{p:qp[p] for p in ps},cp[c]['task'])
            variants={'C0':compose(g0,bg,b0,bs),'C1':compose(g1,ng,b0,bs),'C2':compose(g0,bg,b0,bs,allow0),'C3':compose(g1,ng,b0,bs,allow1),'C1_NO_EMBEDDING':compose(g1,ng,b0,bs,no_embedding=True),'C3_NO_EMBEDDING':compose(g1,ng,b0,bs,allow1,no_embedding=True)}
            assert variants['C0']['score']==oldex[suf,pool['qid'],pool['repeat'],c]['scores']['COMB'];checks+=1
            for m,v in variants.items():scores[m][c]=v['score']
            if not ps:
                assert variants['C0']['score']==variants['C2']['score'];assert variants['C1']['score']==variants['C3']['score']
            details.append({'condition':suf,'qid':pool['qid'],'repeat':pool['repeat'],'case_id':c,'original_path':op,'original_rule_before':g0,'original_rule_after':g1,'original_semantic':b0,'branch_rule_before':bg,'branch_rule_after':ng,'branch_semantic':bs,'allowed_before':allow0,'allowed_after':allow1,'variants':variants,'retrieval_tie':pool['final_retrieval_score'][c]})
        for m,vals in scores.items():
            rank=sorted(ids,key=lambda c:ranking_key(vals[c],pool['final_retrieval_score'][c],c))
            systems.setdefault(m+'_'+suf,[]).append({'qid':pool['qid'],'repeat':pool['repeat'],'ranking':rank,'top_k':{str(k):rank[:k] for k in cfg['k']},'scores':vals,'path_ids':pool['path_ids']})
        ref=next(r for r in oldrank['COMB_'+suf] if r['qid']==pool['qid'] and r['repeat']==pool['repeat'])
        assert systems['C0_'+suf][-1]['ranking']==ref['ranking']
    # Keep every branch's own ranking. Gating never edits its retrieval/profile text.
    features=loadlines(RET/'candidate_features.jsonl');by={}
    for f in features:by.setdefault((f['path_id'],f['backbone']),{})[f['case_id']]=f
    branches=[]
    for (p,backbone),fs in by.items():
        values={c:{'old':compose(old[p,c]['mapping_grade'],{},sem[p,c]['score'],{})['score'],'new':compose(new[p,c]['mapping_grade'],{},sem[p,c]['score'],{})['score']} for c in ids}
        branches.append({'path_id':p,'backbone':backbone,'old_ranking':sorted(ids,key=lambda c:ranking_key(values[c]['old'],fs[c]['hybrid_rrf_score'],c)),'new_ranking':sorted(ids,key=lambda c:ranking_key(values[c]['new'],fs[c]['hybrid_rrf_score'],c)),'scores':values})
    profiles={'cases_before':oldcp,'cases_after':cp,'queries_before':oldqp,'queries_after':qp,'semantic_profiles_reference':'unchanged original semantic/mapping profiles; no concatenation or new vector inference'}
    write(out/'profiles.json',profiles)
    write(out/'rule_mappings.json',{'records':[{'path_id':p,'case_id':c,'before':old[p,c],'after':v} for (p,c),v in new.items()]})
    write(out/'rankings.json',{'systems':systems,'C0_full112_rank_matches':80,'C0_scores_exact':checks,'labels_read':False})
    write(out/'scores.json',{'records':details});write(out/'branch_rankings.json',{'records':branches,'original_and_perspective_separate':True})
    files=['profiles.json','rule_mappings.json','rankings.json','scores.json','branch_rankings.json']
    write(out/'prediction_receipt.json',{'freeze_sha256':sha(out/'freeze.json'),'files':{p:sha(out/p) for p in files},'labels_read':False,'test_access':False,'api_calls':0,'new_embeddings':0})
    print('Sealed480 final rankings; C0 exact80 ranks/8960 scores; branch rankings236*2')


def measures(rank,grades,k):
    pos={c for c,g in grades.items() if g>=3};h=len(set(rank[:k])&pos);n=len(pos)
    return {'precision':h/k,'recall':h/n if n else None,'f1':2*h/(k+n) if n else None,'hits':h}


def ndcg(rank,grades,k):
    dcg=lambda values:sum((2**g-1)/math.log2(i+2) for i,g in enumerate(values))
    ideal=dcg(sorted(grades.values(),reverse=True)[:k]);return dcg([grades[c] for c in rank[:k]])/ideal if ideal else None


def evaluate(out):
    verify(out);receipt=read(out/'prediction_receipt.json');assert sha(out/'freeze.json')==receipt['freeze_sha256']
    for n,h in receipt['files'].items():assert sha(out/n)==h
    ev=out/'evaluation';ev.mkdir(exist_ok=False)
    label=ROOT/'docs/stage123-openai-triplicate-2026-10-27/stage1_silver.json';assert sha(label)==read(label.parent/'silver_freeze.json')['sha256']
    raw=read(label)['records'];grades=defaultdict(dict)
    for r in raw:
        assert not r['held'] and type(r['silver_score']) is int and 0<=r['silver_score']<=4
        assert r['cid'] not in grades[r['qid']];grades[r['qid']][r['cid']]=r['silver_score']
    assert len(raw)==1120 and all(len(v)==112 for v in grades.values()) and sum(v>=3 for g in grades.values() for v in g.values())==18
    systems=read(out/'rankings.json')['systems'];rows=[];qmean=[];macro=[]
    for name,runs in systems.items():
        bucket=defaultdict(list)
        for r in runs:
            q=r['qid'];rank=r['ranking'];assert len(rank)==len(set(rank))==112 and set(rank)==set(grades[q])
            for k in (5,10,20):
                m=measures(rank,grades[q],k)
                if k in (5,10):m['ndcg']=ndcg(rank,grades[q],k)
                rec={'system':name,'qid':q,'repeat':r['repeat'],'k':k,**m};rows.append(rec);bucket[q,k].append(rec)
        for (q,k),recs in bucket.items():
            item={'system':name,'qid':q,'k':k,'repeats':len(recs)}
            for m in ('precision','recall','f1','ndcg'):
                vals=[r[m] for r in recs if r.get(m) is not None];item[m]=sum(vals)/len(vals) if vals else None
            qmean.append(item)
        for k in (5,10,20):
            item={'system':name,'k':k}
            for m in ('precision','recall','f1','ndcg'):
                vals=[r[m] for r in qmean if r['system']==name and r['k']==k and r[m] is not None];item[m]=sum(vals)/len(vals) if vals else None;item[m+'_denominator']=len(vals)
            assert item['precision_denominator']==10 and item['recall_denominator']==item['f1_denominator']==6
            macro.append(item)
    assert abs(next(r['f1'] for r in macro if r['system']=='C0_D_SINGLE' and r['k']==5)-.4757936507936508)<1e-14
    movements=[];events=[];changes=[];tradeoffs=[];promotions=[];scorelookup={(r['condition'],r['qid'],r['repeat'],r['case_id']):r for r in read(out/'scores.json')['records']}
    for name,runs in systems.items():
        suf=next(s for s in SUFFIX.values() if name.endswith('_'+s));method=name[:-(len(suf)+1)]
        if method not in ('C1','C2','C3'):continue
        for r in runs:
            q=r['qid'];rep=r['repeat'];old=next(x for x in systems['C0_'+suf] if x['qid']==q and x['repeat']==rep);before={c:i+1 for i,c in enumerate(old['ranking'])};after={c:i+1 for i,c in enumerate(r['ranking'])}
            for c in r['ranking']:
                movements.append({'system':name,'qid':q,'repeat':rep,'case_id':c,'silver_grade':grades[q][c],'old_rank':before[c],'new_rank':after[c],'rank_gain':before[c]-after[c]})
                d=scorelookup[suf,q,rep,c]
                if d['variants']['C0']['rule_strength']>d['original_rule_before']:
                    promotions.append({'system':name,'qid':q,'repeat':rep,'condition':suf,'case_id':c,'silver_grade':grades[q][c],'old_rank':before[c],'new_rank':after[c],'old_strength':d['variants']['C0']['rule_strength'],'new_strength':d['variants'][method]['rule_strength'],'allowed_paths':d['variants'][method]['allowed_paths']})
            for k in (5,10,20):
                top0=set(old['ranking'][:k]);top1=set(r['ranking'][:k]);p={c for c,g in grades[q].items() if g>=3}
                for c in sorted((top1-top0)|(top0-top1)):
                    events.append({'system':name,'qid':q,'repeat':rep,'k':k,'case_id':c,'silver_grade':grades[q][c],'change':'GAIN' if c in top1 else 'LOSS','related':c in p,'old_rank':before[c],'new_rank':after[c]})
                changes.append({'system':name,'qid':q,'repeat':rep,'k':k,'related_kept':len(top0&top1&p),'related_added':len((top1-top0)&p),'related_lost':len((top0-top1)&p),'grade0_before':sum(grades[q][c]==0 for c in top0),'grade0_after':sum(grades[q][c]==0 for c in top1),'grade1_2_before':sum(0<grades[q][c]<3 for c in top0),'grade1_2_after':sum(0<grades[q][c]<3 for c in top1)})
        for k in (5,10,20):
            oldm=next(r for r in macro if r['system']=='C0_'+suf and r['k']==k);newm=next(r for r in macro if r['system']==name and r['k']==k)
            tradeoffs.append({'system':name,'k':k,**{m+'_delta':newm[m]-oldm[m] for m in ('precision','recall','f1')},'precision_up_recall_down':newm['precision']>oldm['precision'] and newm['recall']<oldm['recall']})
    for p,rs in [('macro_metrics.csv',macro),('query_mean_metrics.csv',qmean),('per_repeat_metrics.csv',rows),('rank_changes.csv',movements),('topk_changes.csv',changes),('tradeoffs.csv',tradeoffs)]:csvsave(ev/p,rs)
    write(ev/'events.json',{'records':events,'unit':'query-repeat-case perK; grade0 distinct from1/2; not human judgments'})
    write(ev/'promotion_changes.json',{'records':promotions})
    result={'macro':macro,'label_source':'existing AI-Silver same-model3repeat median','label_sha256':sha(label),'qrels_rows':1120,'positive_pairs':18,'positive_query_count':6,'zero_positive_queries':sorted(q for q,g in grades.items() if not any(v>=3 for v in g.values())),'ndcg_gain':'2**grade-1; complete112IDCG, zero undefined','one_evaluation':True,'test_access':False,'new_embeddings':0,'api_calls':0}
    write(ev/'results.json',result);write(ev/'complete.json',{'prediction_receipt_sha256':sha(out/'prediction_receipt.json'),'files':{p.name:sha(p) for p in ev.iterdir()},'labels_opened_after_seal':True})
    print(json.dumps([r for r in macro if r['k']==5 and r['system'].endswith('_D_SINGLE')],ensure_ascii=False))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['freeze','predict','evaluate']);p.add_argument('--output',type=Path,default=OUT);a=p.parse_args()
    socket.socket.connect=lambda *a,**k:(_ for _ in ()).throw(RuntimeError('Network disabled'))
    socket.create_connection=socket.socket.connect
    try:{'freeze':freeze,'predict':predict,'evaluate':evaluate}[a.stage](a.output)
    except BaseException as e:
        if a.output.exists() and not (a.output/'failed.json').exists():write(a.output/'failed.json',{'stage':a.stage,'error':type(e).__name__,'message':str(e),'automatic_retry':False})
        raise
