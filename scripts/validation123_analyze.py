"""Read sealed predictions only after inference; no model tuning."""
from collections import defaultdict
import json
from ax_research.heldout import read,write,sha,jsonl
from ax_research.new_validation import evaluate
from scripts.validation123_api import ROOT,OUT,OLD,budget
from scripts.validation123_metrics import aggregate,complete_ids


def summarize(results,labels,exclude=()):
    # Each question receives equal weight after averaging its three repeats.
    full=[q for q in complete_ids(labels) if q not in exclude];by={(r['condition'],r['query_id'],r['repeat']):r for r in results};names=['E1','E2','E3','E4','E3_NEUTRAL','E4_NEUTRAL'];output=[]
    for metric in results[0]['metrics']:
        per={}
        for n in names:
            for q in full:
                vs=[by[n,q,r]['metrics'][metric] for r in ((1,2,3) if n in ('E2','E4','E4_NEUTRAL') else (0,))]
                per[n,q]=sum(vs)/len(vs) if all(v is not None for v in vs) else None
        valid=[q for q in full if all(per[n,q] is not None for n in names)]
        for n in names:
            v=[per[n,q] for q in valid];reps=[]
            for rep in ((1,2,3) if n in ('E2','E4','E4_NEUTRAL') else (0,)):
                vs=[by[n,q,rep]['metrics'][metric] for q in valid];reps.append(sum(vs)/len(vs) if vs else None)
            output.append({'condition':n,'metric':metric,'value':sum(v)/len(v) if v else None,'defined_questions':len(v),'query_ids':valid,'per_repeat_macro':reps,'repeat_min':min(reps) if all(x is not None for x in reps) else None,'repeat_max':max(reps) if all(x is not None for x in reps) else None})
    return output


def main():
    src=OUT/'stage3/predictions';seal=read(src/'complete.json')
    for n,h in seal['files'].items():assert sha(src/n)==h
    dest=OUT/'stage3/evaluation';dest.mkdir(exist_ok=False);pred=read(src/'rankings.json');labels=read(OUT/'stage1/qrels_v2.json')['records'];qs=pred['query_ids'];labs={(r['query_id'],r['case_id']):r for r in labels};runs=[]
    for rep in (0,1,2,3):
        names=('E1','E3','E3_NEUTRAL') if rep==0 else ('E2','E4','E4_NEUTRAL')
        part={new:[{k:v for k,v in r.items() if k!='repeat'} for r in pred['systems'][old] if rep==0 or r['repeat']==rep] for new,old in zip(('C0','C1','C1_NO_EMBEDDING'),names)}
        evaluated=evaluate({'query_ids':qs,'case_ids':pred['case_ids'],'systems':part},labels)
        write(dest/f'metrics_repeat{rep}.json',evaluated)
        for r in evaluated['per_query']:runs.append({**r,'condition':names[('C0','C1','C1_NO_EMBEDDING').index(r['system'])],'repeat':rep})
    macro=summarize(runs,labels);write(dest/'summary.json',{'macro':macro,'per_query':runs,'label_source':'AI-Silver v2; not Human-Gold','complete_questions':complete_ids(labels),'equal_weight_question_then_repeat':True,'threshold':2,'recall_F1_zero_positive':'undefined','ndcg_gain':'2**grade-1'})
    sensitivity=[]
    for title,exclude in [('exclude_temperature',['NV20261102_10'])]+[(f'leave_out_{q}',[q]) for q in qs]:sensitivity.append({'name':title,'excluded':exclude,'macro':summarize(runs,labels,exclude)})
    write(dest/'sensitivity.json',{'records':sensitivity})
    rankby={(n,r['query_id'],r.get('repeat',0)):r for n,rs in pred['systems'].items() for r in rs};changes=[]
    for old,new in (('E1','E2'),('E3','E4'),('E1','E3'),('E3','E3_NEUTRAL'),('E4','E4_NEUTRAL')):
        for q in qs:
            for rep in ((1,2,3) if new in ('E2','E4','E4_NEUTRAL') else (0,)):
                original=rankby[old,q,rep if old=='E4' else 0]['ranking'];current=rankby[new,q,rep]['ranking'];pos={c for (qid,c),l in labs.items() if qid==q and l['status']=='JUDGED' and l['grade']>=2}
                for k in (5,10,20):
                    a=set(original[:k])&pos;b=set(current[:k])&pos
                    changes.append({'comparison':old+'->'+new,'query_id':q,'repeat':rep,'k':k,'gained_relevant':sorted(b-a),'lost_relevant':sorted(a-b),'retained_relevant':sorted(a&b),'old_grade0':sum(labs[q,c]['grade']==0 for c in original[:k]),'new_grade0':sum(labs[q,c]['grade']==0 for c in current[:k]),'unresolved_old':sum(labs[q,c]['status']!='JUDGED' for c in original[:k]),'unresolved_new':sum(labs[q,c]['status']!='JUDGED' for c in current[:k])})
    write(dest/'gains_losses.json',{'records':changes,'unresolved_not_zero':True,'counts_are_label_conditional':True})
    # Diagnose every generated path against original mapping; observation, not selection.
    paths=read(src/'paths.json')['paths'];br=read(src/'branch_rankings.json')['systems'];branchscores={(r['path_id'],r['case_id']):r for r in jsonl(src/'branch_scores.jsonl')};combined={(r['query_id'],r['repeat'],r['case_id']):r for r in jsonl(src/'combined_scores.jsonl')};pathresults=[]
    branchrank={(n,r['query_id']):r for n,rs in br.items() for r in rs}
    for p in paths:
        q=p['parent_query_id'];pid=p['query_id'];item={**p,'ranking_results':{}}
        for n,orig,dyn in (('C0','E1','E2'),('C1','E3','E4')):
            rank=branchrank[n,pid]['ranking'];ori=rankby[orig,q,0]['ranking'];final=rankby[dyn,q,p['repeat']]['ranking'];pos={c for (qid,c),l in labs.items() if qid==q and l['status']=='JUDGED' and l['grade']>=2}
            item['ranking_results'][n]={'top5':rank[:5],'known_relevant_top5':sorted(pos&set(rank[:5])),'known_gain_vs_original_top5':sorted((pos&set(rank[:5]))-set(ori[:5])),'known_loss_vs_original_top5':sorted((pos&set(ori[:5]))-set(rank[:5])),'final_top5_rule_winner_cases':[c for c in final[:5] if pid in combined[q,p['repeat'],c]['conditions'][dyn]['rule_winner_paths']],'final_top5_semantic_winner_cases':[c for c in final[:5] if pid in combined[q,p['repeat'],c]['conditions'][dyn]['semantic_winner_paths']]}
        pathresults.append(item)
    write(dest/'perspective_diagnostics.json',{'records':pathresults,'warning':'Standalone branch discoveries and winner counts are descriptive attribution, not causal ablation; no label-based path selection'})
    targets=[('NV20261102_01','AXV24_f27ca1e6fb82'),('NV20261102_06','AXV2N_0103'),('NV20261102_10','AXV24_29f79de45110'),('NV20261102_10','AXV2N_0119')];failures=[]
    oe={(r['query_id'],r['case_id']):r for r in read(OLD/'predictions/evidence.json')['records']};oc1={(r['query_id'],r['case_id']):r for r in read(OLD/'predictions/C1_details.json')['records']}
    profiles=read(src/'query_profiles.json')
    for q,c in targets:
        original=oe[q,c];ranks={n:[{'repeat':r.get('repeat',0),'rank':r['ranking'].index(c)+1,'score':r['scores'][c]} for r in rs if r['query_id']==q] for n,rs in pred['systems'].items()}
        failures.append({'query_id':q,'case_id':c,'label':labs[q,c],'case':original['case'],'ranks':ranks,'original_evidence':original,'original_C1':oc1[q,c],'dynamic':[{**combined[q,rep,c],'branches':[{**p,'scores':branchscores[p['query_id'],c],'query_rule_profile':profiles['C1_rule'][p['query_id']],'query_semantic_profile':profiles['semantic'][p['query_id']]} for p in paths if p['parent_query_id']==q and p['repeat']==rep]} for rep in (1,2,3)]})
    write(dest/'failure_cases.json',{'records':failures,'retrieval_candidate_losses':0,'reason':'All112 always scored; topK losses occur within mapping/aggregation/ranking rather than candidate truncation'})
    costs=budget();attempts=[read(p) for p in (OUT/'api/attempts').glob('*.json')]
    costs['successful_HTTP_responses']=sum(r['state']=='RECEIVED' for r in attempts);costs['valid_reviews']=10;costs['valid_view_generations']=30;costs['invalid_received_view_generations']=1;costs['HTTP400_rejections']=2;costs['actual_billing_balance_verified']=False
    costs['usage_tokens']={k:sum(r.get('usage',{}).get(k,0) for r in attempts) for k in ('input_tokens','output_tokens','total_tokens')}
    write(OUT/'api/final_cost.json',costs)
    write(dest/'complete.json',{'complete':True,'prediction_seal_sha256':sha(src/'complete.json'),'qrels_sha256':sha(OUT/'stage1/qrels_v2.json'),'files':{p.name:sha(p) for p in dest.iterdir()},'model_tuned':False})
    for r in macro:
        if r['metric'] in ('Precision@5','Recall@5','F1@5','nDCG@10'):print(r)


if __name__=='__main__':main()
