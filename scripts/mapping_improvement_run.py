"""One fixed Dev experiment: freeze -> label-free predictions -> Silver analysis."""
import argparse
from collections import Counter,defaultdict
import csv
import json
import platform
import socket
import subprocess
from pathlib import Path

import numpy as np
from ax_research.functional_mapping import compare,ranking_key as akey
from ax_research.semantic_mapping import aggregate,combined_score,ranking_key as skey
from ax_research.mapping_improvement import expanded_rules,extract2,case_profile2,semantic2,combination_unknown
from ax_research.heldout import read,sha,write

ROOT=Path(__file__).resolve().parents[1]
HIST=ROOT/'docs/query-case-functional-mapping-2026-10-28'
SEM=ROOT/'docs/query-case-semantic-mapping-2026-10-28'
RET=ROOT/'docs/dense-bm25-candidates-2026-10-27'
CONFIG=ROOT/'configs/mapping_improvement_20261030.json'
DEFAULT=ROOT/'docs/mapping-improvement-2026-10-30/experiment'


def lines(p):
    with Path(p).open(encoding='utf-8-sig') as s:return [json.loads(x) for x in s if x.strip()]


def csvwrite(path,rows):
    with Path(path).open('x',encoding='utf-8',newline='') as s:
        w=csv.DictWriter(s,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)


def block(*a,**k):raise RuntimeError('No network/API permitted')


def state():
    from scripts.heldout_run import PROTECTED,freeze
    model=(ROOT/read(ROOT/'configs/semantic_mapping_20261028.json')['model_path']).resolve()
    old=freeze(model)
    paths=[CONFIG,ROOT/'src/ax_research/mapping_improvement.py',Path(__file__),ROOT/'scripts/mapping_improvement_audit.py',ROOT/'docs/mapping-improvement-2026-10-30/design.md']
    paths += [RET/n for n in ('query_registry.json','mapping_candidate_pools.jsonl','candidate_features.jsonl')]
    paths += [HIST/n for n in ('stage2/query_profiles.json','stage2/mappings.jsonl','stage3/rankings.json')]
    paths += [SEM/n for n in ('mapping/query_profiles.json','mapping/mappings.jsonl','ranking/rankings.json')]
    return {'protected':old['protected'],'model':old['model'],'packages':old['packages'],'new_and_additional_sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in paths},'config':read(CONFIG),'python':platform.python_version(),'command':'python -m scripts.mapping_improvement_run {freeze,predict,evaluate} --output NEW_PATH','base':read(CONFIG)['base'],'sealed_test_read':False,'api_calls':0,'new_model_inference':0}


def freeze(out):
    out.mkdir(parents=True,exist_ok=False)
    write(out/'preregistration.json',{**state(),'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'labels_read':False})


def verify(out):
    f=read(out/'preregistration.json');assert all(f[k]==v for k,v in state().items()),'Frozen input/code drift'
    return f


def predict(out):
    verify(out)
    if (out/'prediction_receipt.json').exists():raise FileExistsError('Predictions already sealed')
    cfg=read(CONFIG);rules=read(ROOT/'configs/functional_mapping_20261028.json');rules2=expanded_rules(rules,cfg)
    cases=read(RET/'case_registry.json')['cases'];queries=read(RET/'query_registry.json')['paths'];ids=sorted(cases)
    oldcp=read(HIST/'stage2/case_profiles.json');oldqp=read(HIST/'stage2/query_profiles.json')
    cp={c:case_profile2(case,rules2) for c,case in cases.items()};qp={p:extract2(q['query_text'],rules2) for p,q in queries.items()}
    oldmaps={(r['path_id'],r['case_id']):r for r in lines(HIST/'stage2/mappings.jsonl')}
    sems={(r['path_id'],r['case_id']):r for r in lines(SEM/'mapping/mappings.jsonl')}
    maps={(p,c):compare(qp[p],cp[c]) for p in queries for c in ids}
    sb={(p,c):semantic2(sems[p,c],bool(oldqp[p]['function_ids']),bool(oldcp[c]['task']['function_ids'])) for p in queries for c in ids}
    assert len(maps)==13216 and len(queries)==118 and len(ids)==112
    systems={};details=[];branchrows=[]
    pools=lines(RET/'mapping_candidate_pools.jsonl');suffix={'C':'O_SINGLE','F':'D_SINGLE','S_C3':'O_THREE','S_F3':'D_THREE'}
    for pool in pools:
        suf=suffix[pool['condition']];op='o_'+pool['qid'];branches=[p for p in pool['path_ids'] if queries[p]['scope']=='dynamic']
        assert set(pool['candidate_ids_ranked_all112'])==set(ids)
        grades={c:oldmaps[op,c] for c in ids};newg={c:maps[op,c] for c in ids}
        semscore={};newsem={};combined={x:{} for x in ('C0','C_R','C_S','C_U','C_ALL')}
        for c in ids:
            whole=sems[op,c]['score'];bs=[sems[p,c]['score'] for p in branches];s=aggregate(whole,bs);s2=aggregate(sb[op,c],[sb[p,c] for p in branches]);semscore[c]=s;newsem[c]=s2
            strength=max([grades[c]['mapping_grade']]+[oldmaps[p,c]['mapping_grade'] for p in branches]);r2=max([newg[c]['mapping_grade']]+[maps[p,c]['mapping_grade'] for p in branches])
            known=bool(oldcp[c]['task']['function_ids']) and any(oldqp[p]['function_ids'] for p in [op,*branches])
            known2=bool(cp[c]['task']['function_ids']) and any(qp[p]['function_ids'] for p in [op,*branches])
            vals={'C0':combined_score(strength,s),'C_R':combined_score(r2,s),'C_S':combined_score(strength,s2),'C_U':combination_unknown(strength,s,known),'C_ALL':combination_unknown(r2,s2,known2)}
            for method,value in vals.items():combined[method][c]=value
            details.append({'condition':suf,'qid':pool['qid'],'repeat':pool['repeat'],'case_id':c,'old_rule_strength':strength,'new_rule_strength':r2,'old_semantic':s,'new_semantic':s2,'old_known':known,'new_known':known2,'combined_scores':vals,'whole_path':op,'branch_scores':{p:{'old_rule':oldmaps[p,c]['mapping_grade'],'new_rule':maps[p,c]['mapping_grade'],'old_semantic':sems[p,c]['score'],'new_semantic':sb[p,c]} for p in branches},'whole_scores':{'old_rule':grades[c]['mapping_grade'],'new_rule':newg[c]['mapping_grade'],'old_semantic':whole,'new_semantic':sb[op,c]},'retrieval_score':pool['final_retrieval_score'][c]})
        ranks={
            'A0':sorted(ids,key=lambda c:akey(grades[c],[oldmaps[p,c] for p in branches],pool['final_retrieval_score'][c],c)),
            'A2':sorted(ids,key=lambda c:akey(newg[c],[maps[p,c] for p in branches],pool['final_retrieval_score'][c],c)),
            'B0':sorted(ids,key=lambda c:skey(semscore[c],pool['final_retrieval_score'][c],c)),
            'B2':sorted(ids,key=lambda c:skey(newsem[c],pool['final_retrieval_score'][c],c))}
        ranks.update({m:sorted(ids,key=lambda c:skey(scores[c],pool['final_retrieval_score'][c],c)) for m,scores in combined.items()})
        for method,rank in ranks.items():
            systems.setdefault(method+'_'+suf,[]).append({'qid':pool['qid'],'repeat':pool['repeat'],'ranking':rank,'top_k':{str(k):rank[:k] for k in cfg['k']},'path_ids':pool['path_ids']})
    # Reconstruct every previous A/B/C ranking, not just rounded headline metrics.
    olda=read(HIST/'stage3/rankings.json')['systems'];oldb=read(SEM/'ranking/rankings.json')['systems'];matches=0
    for suf in suffix.values():
        for current,old in [('A0',olda['M_'+suf]),('B0',oldb['SEM_'+suf]),('C0',oldb['COMB_'+suf])]:
            for row in systems[current+'_'+suf]:
                ref=next(r for r in old if r['qid']==row['qid'] and r['repeat']==row['repeat']);assert row['ranking']==ref['ranking'],(current,suf,row['qid'],row['repeat']);matches+=1
    # Preserve all branch-local scores/rankings. Final aggregation unchanged.
    features=lines(RET/'candidate_features.jsonl');by={}
    for f in features:by.setdefault((f['path_id'],f['backbone']),{})[f['case_id']]=f
    for (p,backbone),feat in by.items():
        orders={'A2':sorted(ids,key=lambda c:(-maps[p,c]['mapping_grade'],-feat[c]['hybrid_rrf_score'],c)), 'B2':sorted(ids,key=lambda c:skey(sb[p,c],feat[c]['hybrid_rrf_score'],c))}
        branchrows.append({'path_id':p,'backbone':backbone,'rankings':orders})
    unknown=[c for c in ids if not oldcp[c]['task']['function_ids']]
    recognized=[c for c in unknown if cp[c]['task']['function_ids']]
    stats={'cases_before':sum(bool(p['task']['function_ids']) for p in oldcp.values()),'cases_after':sum(bool(p['task']['function_ids']) for p in cp.values()),'paths_before':sum(bool(p['function_ids']) for p in oldqp.values()),'paths_after':sum(bool(p['function_ids']) for p in qp.values()),'newly_recognized_unknown33':recognized,'still_unknown33':[c for c in unknown if c not in recognized],'lost_case_recognition':[c for c in ids if oldcp[c]['task']['function_ids'] and not cp[c]['task']['function_ids']],'historical_full112_rank_matches':matches,'embedding_fallback_pairs':sum(not oldqp[p]['function_ids'] or not oldcp[c]['task']['function_ids'] for p,c in maps),'functional_correctness':'AI source-grounded review only, not human Gold or automatic accuracy measurement'}
    for name,data in [('profiles.json',{'cases':cp,'queries':qp}),('mappings.json',{'records':[{'path_id':p,'case_id':c,**v,'B2_score':sb[p,c]} for (p,c),v in maps.items()]}),('rankings.json',{'systems':systems}),('score_details.json',{'records':details}),('branch_rankings.json',{'records':branchrows}),('recognition.json',stats)]:write(out/name,data)
    artifact_names=['profiles.json','mappings.json','rankings.json','score_details.json','branch_rankings.json','recognition.json']
    write(out/'prediction_receipt.json',{'artifact_sha256':{n:sha(out/n) for n in artifact_names},'preregistration_sha256':sha(out/'preregistration.json'),'labels_read':False,'sealed_test_read':False,'api_calls':0,'new_model_inference':0})
    print(json.dumps(stats,ensure_ascii=False))


def metric(rank,positive,k):
    hits=len(set(rank[:k])&positive)
    return {'precision':hits/k,'recall':hits/len(positive) if positive else None,'f1':2*hits/(k+len(positive)) if positive else None,'hits':hits}


def evaluate(out):
    verify(out);receipt=read(out/'prediction_receipt.json')
    for n,h in receipt['artifact_sha256'].items():assert sha(out/n)==h
    assert sha(out/'preregistration.json')==receipt['preregistration_sha256']
    if (out/'evaluation').exists():raise FileExistsError('Evaluation exists; no automatic re-evaluation/tuning')
    ev=out/'evaluation';ev.mkdir()
    labelpath=ROOT/'docs/stage123-openai-triplicate-2026-10-27/stage1_silver.json'
    assert sha(labelpath)==read(labelpath.parent/'silver_freeze.json')['sha256']
    raw=read(labelpath)['records'];grades=defaultdict(dict)
    for r in raw:
        assert not r['held'] and r['silver_score'] is not None
        assert r['cid'] not in grades[r['qid']];grades[r['qid']][r['cid']]=r['silver_score']
    assert len(raw)==1120 and len(grades)==10 and all(len(g)==112 for g in grades.values())
    positive={q:{c for c,g in gs.items() if g>=3} for q,gs in grades.items()};assert sum(map(len,positive.values()))==18
    systems=read(out/'rankings.json')['systems']
    historical=read(HIST/'stage4_dev/results.json')['systems'];systems['SingleDense_original']=historical['single_dense__original']
    allrows=[];queryrows=[];macro=[]
    for name,rows in systems.items():
        buckets=defaultdict(list)
        for row in rows:
            q=row['qid'];rank=row['ranking'];assert len(rank)==len(set(rank))==112 and set(rank)==set(grades[q])
            for k in (5,10,20):
                m=metric(rank,positive[q],k);record={'system':name,'qid':q,'repeat':row['repeat'],'k':k,'positive_count':len(positive[q]),**m};allrows.append(record);buckets[q,k].append(record)
        for (q,k),rs in buckets.items():
            row={'system':name,'qid':q,'k':k,'repeats':len(rs),'positive_count':len(positive[q])}
            for m in ('precision','recall','f1'):
                vals=[r[m] for r in rs if r[m] is not None];row[m]=sum(vals)/len(vals) if vals else None
            queryrows.append(row)
        for k in (5,10,20):
            rs=[r for r in queryrows if r['system']==name and r['k']==k];row={'system':name,'k':k}
            for m in ('precision','recall','f1'):
                vals=[r[m] for r in rs if r[m] is not None];row[m]=sum(vals)/len(vals) if vals else None;row[m+'_denominator']=len(vals)
            assert row['precision_denominator']==10 and row['recall_denominator']==6 and row['f1_denominator']==6
            macro.append(row)
    # Validate published numbers before interpreting changes.
    expected={'SingleDense_original':.3146825396825397,'A0_D_SINGLE':.460978835978836,'B0_D_SINGLE':.3875661375661376,'C0_D_SINGLE':.4757936507936508}
    for name,value in expected.items():assert abs(next(r['f1'] for r in macro if r['system']==name and r['k']==5)-value)<.00001,(name,value)
    changes=[];events=[];error_rows=[]
    cases=read(RET/'case_registry.json')['cases'];oldmaps={(r['path_id'],r['case_id']):r for r in lines(HIST/'stage2/mappings.jsonl')}
    unknown=set(read(SEM/'mapping/unknown33.json')['case_ids'])
    comparisons={'A2':'A0','B2':'B0','C_R':'C0','C_S':'C0','C_U':'C0','C_ALL':'C0'}
    # all query/case ranks, not just improvements or positive examples
    for name,rs in systems.items():
        suffix=next((s for s in ('O_SINGLE','D_SINGLE','O_THREE','D_THREE') if name.endswith('_'+s)),None)
        if suffix is None:continue
        method=name[:-(len(suffix)+1)];suf=suffix
        if method not in comparisons:continue
        old=systems[comparisons[method]+'_'+suf]
        for r in rs:
            ref=next(x for x in old if x['qid']==r['qid'] and x['repeat']==r['repeat']);q=r['qid']
            for c in r['ranking']:
                before=ref['ranking'].index(c)+1;after=r['ranking'].index(c)+1
                changes.append({'system':name,'qid':q,'repeat':r['repeat'],'case_id':c,'silver_grade':grades[q][c],'related':c in positive[q],'was_unknown33':c in unknown,'old_rank':before,'new_rank':after,'rank_gain':before-after})
            for k in (5,10,20):
                gained=(set(r['ranking'][:k])-set(ref['ranking'][:k]))&positive[q];lost=(set(ref['ranking'][:k])-set(r['ranking'][:k]))&positive[q]
                for c in sorted(gained|lost):events.append({'system':name,'qid':q,'repeat':r['repeat'],'k':k,'case_id':c,'change':'GAIN' if c in gained else 'LOSS','task':cases[c]['task']})
    for suf in ('O_SINGLE','D_SINGLE','O_THREE','D_THREE'):
        for a in systems['A0_'+suf]:
            q=a['qid'];rep=a['repeat'];b=next(x for x in systems['B0_'+suf] if x['qid']==q and x['repeat']==rep);c0=next(x for x in systems['C0_'+suf] if x['qid']==q and x['repeat']==rep)
            for cid in a['ranking']:
                ar=a['ranking'].index(cid)+1;br=b['ranking'].index(cid)+1;cr=c0['ranking'].index(cid)+1;rel=cid in positive[q]
                flags=[]
                if rel and ar>5:flags.append('RELATED_BELOW_TOP5_A')
                if not rel and ar<=5:flags.append('SILVER_NEGATIVE_TOP5_A')
                if abs(ar-br)>=20:flags.append('A_B_RANK_GAP_GE20')
                if cr<ar:flags.append('C_UP_VS_A')
                if cr>ar:flags.append('C_DOWN_VS_A')
                if flags:
                    pid='o_'+q;rm=oldmaps[pid,cid]
                    error_rows.append({'condition':suf,'qid':q,'repeat':rep,'case_id':cid,'task':cases[cid]['task'],'silver_grade':grades[q][cid],'related':rel,'A_rank':ar,'B_rank':br,'C_rank':cr,'whole_rule_grade':rm['mapping_grade'],'whole_mapping_status':rm['status'],'flags':flags,'localization':'all112 retrieved; functional extraction UNKNOWN' if rm['status']=='UNKNOWN' else 'all112 retrieved; mapping/semantic scoring and combination/TopK; generation causality not established','source_evidence':rm['shared_functions']})
    csvwrite(ev/'macro_metrics.csv',macro);csvwrite(ev/'query_mean_metrics.csv',queryrows);csvwrite(ev/'per_repeat_metrics.csv',allrows);csvwrite(ev/'rank_changes.csv',changes)
    write(ev/'gain_loss.json',{'records':events,'unit':'query-repeat-case events; not unique cases; K separate'})
    write(ev/'old_error_analysis.json',{'records':error_rows,'negative_means':'below old Dev Silver threshold3; not independently proven irrelevant','stage_attribution_limit':'candidate112 complete; not proof generator semantic error; score aggregation causality inspected separately'})
    summary={'label_source':'AI-Silver one model3-repeat median, not human Gold','threshold':3,'qrels_rows':1120,'positives':18,'positive_questions':6,'zero_positive_questions':sorted(q for q,p in positive.items() if not p),'macro':macro,'label_sha256':sha(labelpath),'api_calls':0,'test_access':False,'post_result_tuning':False}
    write(ev/'results.json',summary)
    write(ev/'complete.json',{'prediction_receipt_sha256':sha(out/'prediction_receipt.json'),'files':{p.name:sha(p) for p in ev.iterdir()},'labels_only_after_prediction_seal':True})
    print(json.dumps([r for r in macro if r['k']==5 and ('D_SINGLE' in r['system'] or r['system']=='SingleDense_original')],ensure_ascii=False))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['freeze','predict','evaluate']);p.add_argument('--output',type=Path,default=DEFAULT);args=p.parse_args()
    socket.socket.connect=block;socket.create_connection=block
    try:{'freeze':freeze,'predict':predict,'evaluate':evaluate}[args.stage](args.output)
    except BaseException as e:
        if args.output.exists() and not (args.output/'failed.json').exists():write(args.output/'failed.json',{'stage':args.stage,'error':type(e).__name__,'message':str(e),'automatic_retry':False})
        raise
