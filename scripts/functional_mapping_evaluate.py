"""Stage4 DEV only. Silver first enters here, after recommendation commit."""
import csv
import statistics
import socket
import subprocess
from collections import defaultdict,Counter
from scripts import functional_mapping_run as f

NAMES={'single_dense__original':'원질문 Single Dense','three_view_dense__original':'원질문 3-View Dense','single_dense__round_robin':'다중관점 Single Round-robin','three_view_dense__round_robin':'다중관점 3-View Round-robin','single_dense__mean_rrf':'다중관점 Single RRF','three_view_dense__mean_rrf':'다중관점 3-View RRF','single_dense__original_plus_mean_rrf':'원질문+관점 Single RRF','three_view_dense__original_plus_mean_rrf':'원질문+관점 3-View RRF','H_C':'원질문 Single+BM25','H_F':'다중관점 Single+BM25','H_S_C3':'원질문 3-View+BM25','H_S_F3':'다중관점 3-View+BM25','H_S_BM25_O':'원질문 BM25','H_S_BM25_M':'다중관점 BM25','M_O_SINGLE':'원질문 기능 매핑 Single','M_D_SINGLE':'원질문+관점 기능 매핑 Single(주 조건)','M_O_THREE':'원질문 기능 매핑 3-View','M_D_THREE':'원질문+관점 기능 매핑 3-View'}

def csvsave(name,rows):
    if not rows:return
    p=f.OUT/name;p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('w',encoding='utf-8-sig',newline='') as out:
        w=csv.DictWriter(out,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def metric(ranking,positive,k):
    assert len(set(ranking))==len(ranking)==112
    tp=len(set(ranking[:k])&positive)
    return {'precision':tp/k,'recall':tp/len(positive) if positive else None,'f1':2*tp/(k+len(positive)) if positive else None,'true_positives':tp,'precision_denominator':k,'recall_denominator':len(positive),'related_ids':sorted(set(ranking[:k])&positive)}

def main():
    f.prepare();source=f.ROOT/'docs/stage123-openai-triplicate-2026-10-27'
    silver=f.read(source/'stage1_silver.json');assert f.sha(source/'stage1_silver.json')==f.read(source/'silver_freeze.json')['sha256']
    positive=defaultdict(set);grades=defaultdict(dict)
    for x in silver['records']:
        assert not x['held'];grades[x['qid']][x['cid']]=x['silver_score']
        if x['silver_score']>=3:positive[x['qid']].add(x['cid'])
    assert len(grades)==10 and len(silver['records'])==1120 and sum(map(len,positive.values()))==18
    fusion=f.read(f.ROOT/'docs/candidate-fusion-ablation-2026-10-27/results.json')
    hybrid=f.read(f.IN/'results.json');new=f.read(f.OUT/'stage3/rankings.json')
    expected_new_blob=subprocess.check_output(['git','show','HEAD:'+f.CFG['output']+'/stage3/rankings.json'],cwd=f.ROOT)
    # Our generated Windows output was committed through Git's LF text filter.
    # Only this NEW output accepts EOL normalization; all frozen old input hashes remain exact.
    assert expected_new_blob.replace(b'\r\n',b'\n')==(f.OUT/'stage3/rankings.json').read_bytes().replace(b'\r\n',b'\n'),'Uncommitted recommendation content changes before evaluation'
    systems={**fusion['systems'],**{'H_'+k:hybrid['systems'][k] for k in ('C','F','S_C3','S_F3','S_BM25_O','S_BM25_M')},**new['systems']}
    results={};macro={};qrows=[];macro_rows=[];aggregated_queries=[]
    for system,rows in systems.items():
        rs=[]
        for row in rows:
            q=row['qid'];rep=row.get('repeat',0)
            m={str(k):metric(row['ranking'],positive[q],k) for k in f.CFG['K']}
            if 'metrics' in row:
                for k in f.CFG['K']:
                    for field in ('precision','recall','f1'):
                        assert m[str(k)][field]==row['metrics'][str(k)][field],'Historical metric changed'
            rs.append({'qid':q,'repeat':rep,'ranking':row['ranking'],'metrics':m})
            for k,cell in m.items():qrows.append({'system':system,'qid':q,'repeat':rep,'k':int(k),**{x:v for x,v in cell.items() if x!='related_ids'}})
        results[system]=rs;macro[system]={}
        for k in f.CFG['K']:
            cell={}
            for field,den in [('precision',10),('recall',6),('f1',6)]:
                by=defaultdict(list)
                for row in rs:
                    v=row['metrics'][str(k)][field]
                    if v is not None:by[row['qid']].append(v)
                assert len(by)==den
                cell[field]=statistics.mean(statistics.mean(v) for v in by.values());cell[field+'_question_denominator']=den
                for q,values in by.items():aggregated_queries.append({'system':system,'qid':q,'k':k,'metric':field,'mean':statistics.mean(values),'stdev':statistics.stdev(values) if len(values)>1 else None,'repeats':len(values)})
            cell['query_runs']=len(rs);cell['true_positive_events']=sum(row['metrics'][str(k)]['true_positives'] for row in rs)
            macro[system][str(k)]=cell;macro_rows.append({'system':system,'name':NAMES[system],'k':k,**cell})
    f.save('stage4_dev/results.json',{'systems':results,'macro':macro,'names':NAMES,'silver_sha256':f.sha(source/'stage1_silver.json'),'label_source':'SAME_MODEL_TRIPLICATE_MEDIAN_AI_SILVER_NOT_HUMAN_GOLD','independent_test':False})
    csvsave('stage4_dev/macro_metrics.csv',macro_rows);csvsave('stage4_dev/query_run_metrics.csv',qrows);csvsave('stage4_dev/query_mean_metrics.csv',aggregated_queries)
    cases=f.read(f.IN/'case_registry.json')['cases'];events=[];rankchanges=[];summaries=[]
    references={
      'M_D_SINGLE':['single_dense__original','single_dense__round_robin','single_dense__mean_rrf','single_dense__original_plus_mean_rrf','H_F','M_O_SINGLE'],
      'M_D_THREE':['three_view_dense__original','three_view_dense__round_robin','three_view_dense__mean_rrf','three_view_dense__original_plus_mean_rrf','H_S_F3','M_O_THREE'],
      'M_O_SINGLE':['single_dense__original','H_C'], 'M_O_THREE':['three_view_dense__original','H_S_C3']}
    for sys,refs in references.items():
        for ref in refs:
            local=[]
            for row in results[sys]:
                base=next(x for x in results[ref] if x['qid']==row['qid'] and x['repeat']==(row['repeat'] if any(v['repeat']==row['repeat'] for v in results[ref] if v['qid']==row['qid']) else 0))
                before={cid:i for i,cid in enumerate(base['ranking'],1)};after={cid:i for i,cid in enumerate(row['ranking'],1)}
                for cid in row['ranking']:rankchanges.append({'system':sys,'reference':ref,'qid':row['qid'],'repeat':row['repeat'],'case_id':cid,'silver_grade':grades[row['qid']][cid],'before_rank':before[cid],'after_rank':after[cid],'rank_gain':before[cid]-after[cid],'actual_task':cases[cid]['task']})
                for k in f.CFG['K']:
                    prev=set(base['ranking'][:k])&positive[row['qid']];now=set(row['ranking'][:k])&positive[row['qid']]
                    e={'system':sys,'reference':ref,'qid':row['qid'],'repeat':row['repeat'],'k':k,'new':sorted(now-prev),'retained':sorted(now&prev),'lost':sorted(prev-now),'new_tasks':{cid:cases[cid]['task'] for cid in now-prev},'lost_tasks':{cid:cases[cid]['task'] for cid in prev-now}}
                    events.append(e);local.append(e)
            for k in f.CFG['K']:
                rows=[r for r in local if r['k']==k]
                summaries.append({'system':sys,'reference':ref,'k':k,'question_run_events':len(rows),**{field:sum(len(r[field]) for r in rows) for field in ('new','retained','lost')},'unit':'query/repetition event; original deterministic reference repeated to match dynamic runs'})
    f.save('stage4_dev/related_changes.json',{'events':events,'summary':summaries});csvsave('stage4_dev/rank_changes.csv',rankchanges)
    mandatory=[]
    for sys,rows in results.items():
        for row in rows:
            if row['qid']!='V21D001':continue
            for cid in ('AXV2N_0121','AXV2N_0124','AXV2C_0093_01'):mandatory.append({'system':sys,'qid':row['qid'],'repeat':row['repeat'],'case_id':cid,'rank':row['ranking'].index(cid)+1,'existing_silver':grades[row['qid']][cid],'actual_task':cases[cid]['task']})
    f.save('stage4_dev/mandatory_rank_comparison.json',{'records':mandatory})
    padding=[r for r in f.lines('stage3/top20_explanations.jsonl') if r['condition']=='M_D_SINGLE' and r['low_support_padding']]
    grouped=defaultdict(list)
    for cid,case in cases.items():grouped[case['leakage_group_id']].append(cid)
    f.save('stage4_dev/leakage_audit.json',{'training_performed':False,'learned_train_validation_overlap':'NOT_APPLICABLE_NO_TRAINING','shared_source_groups':[{'group':g,'case_ids':ids} for g,ids in grouped.items() if len(ids)>1],'rules_designed_on_known_dev_schema_and_user_supplied_cases':True,'rules_synthetic_tests_are_not_independent_semantic_gold':True,'silver_mapper_input':False,'recommendations_committed_before_evaluation':subprocess.check_output(['git','log','-1','--format=%H','--',f.CFG['output']+'/stage3/rankings.json'],cwd=f.ROOT,text=True).strip(),'positive_pairs':18,'zero_positive_queries':[q for q in grades if not positive[q]],'independent_test_read':False,'raw_embeddings_untouched':True,'generalization_established':False})
    f.save('stage4_dev/status.json',{'complete':True,'comparison_systems':len(systems),'query_runs':sum(map(len,results.values())),'metric_sets':len(qrows),'api_calls':0,'cost_usd':'0.00','independent_test_access':False,'primary_low_support_top20_rows':len(padding),'silver_changed':False})
    print({s:{k:round(v['f1']*100,3) for k,v in a.items()} for s,a in macro.items()})

if __name__=='__main__':
    socket.socket.connect=f.block;socket.create_connection=f.block;main()
