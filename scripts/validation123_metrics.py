"""Fixed-label metrics, complete-cohort summaries and declared sensitivity."""
import copy
from collections import defaultdict
from pathlib import Path
from ax_research.heldout import read,write,sha
from ax_research.new_validation import evaluate

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/validation-c0c1-stage1to3-2026-11-03';OLD=ROOT/'docs/c0-c1-new-validation-2026-11-02'


def complete_ids(rows):
    by=defaultdict(list)
    for r in rows:by[r['query_id']].append(r)
    return sorted(q for q,rs in by.items() if len(rs)==112 and all(r['status']=='JUDGED' for r in rs))


def aggregate(result,rows,exclude=()):
    qs=[q for q in complete_ids(rows) if q not in exclude];lookup={(r['system'],r['query_id']):r for r in result['per_query']};out=[]
    for metric in result['per_query'][0]['metrics']:
        eligible=[q for q in qs if all(lookup[n,q]['metrics'][metric] is not None for n in ('C0','C1'))]
        for name in ('C0','C1','C1_NO_EMBEDDING'):
            valid=[q for q in eligible if lookup[name,q]['metrics'][metric] is not None];vs=[lookup[name,q]['metrics'][metric] for q in valid]
            out.append({'system':name,'metric':metric,'value':sum(vs)/len(vs) if vs else None,'defined':len(vs),'included_query_ids':valid,'complete_candidates':qs,'excluded_query_ids':[q for q in complete_ids(rows) if q not in valid]})
    return out


def stage2():
    out=OUT/'stage2';out.mkdir(exist_ok=False);pred=read(OLD/'predictions/rankings.json');v2=read(OUT/'stage1/qrels_v2.json')['records'];v1=read(OLD/'qrels.json')['records']
    # Baseline prediction and label seals, never new labels in inference.
    for n,h in read(OLD/'prediction_seal.json')['files'].items():assert sha(OLD/'predictions'/n)==h
    assert sha(OUT/'stage1/qrels_v2.json')==read(OUT/'stage1/complete.json')['qrels_v2_sha256']
    result=evaluate(pred,v2);write(out/'metrics_v2.json',result);base=aggregate(result,v2)
    write(out/'complete_cohort_v2.json',{'complete_queries':complete_ids(v2),'macro':base,'labels':'v2 source-adjudicated AI-Silver; no Human-Gold'})
    sensitivities=[]
    def summarize(name,rows,exclude=(),settings=None):
        r=evaluate(pred,rows);a=aggregate(r,rows,exclude)
        sensitivities.append({'name':name,'settings':settings or {},'macro':a,'not_a_model_change':True,'complete_query_ids':complete_ids(rows),'exclusions':list(exclude)})
    summarize('v1_original_labels',v1)
    summarize('v2_all_complete',v2)
    summarize('v2_exclude_temperature',v2,['NV20261102_10'])
    for q in pred['query_ids']:summarize('v2_leave_out_'+q,v2,[q])
    review=read(OUT/'stage1/review19.json')['records'];critical=[r['case_id'] for r in review if r['review_no'] in (6,7)]
    for a in (2,1,None):
        for b in (2,1,None):
            copyrows=copy.deepcopy(v2)
            for r in copyrows:
                if r['query_id']=='NV20261102_10' and r['case_id'] in critical:
                    grade=(a,b)[critical.index(r['case_id'])];r.update(grade=grade,status='ABSTAIN' if grade is None else 'JUDGED',rationale='Declared counterfactual sensitivity; not replacing actual v2 label')
            summarize('temperature_'+str(a)+'_'+str(b),copyrows,settings={'case_ids':critical,'grades':[a,b],'counterfactual_only':True})
    write(out/'sensitivities.json',{'records':sensitivities,'warning':'ABSTAIN/zero-positive can change metric denominator; compareC1-C0 only within each declared scenario; qrels originals unchanged'})
    write(out/'complete.json',{'complete':True,'full_evaluation_question_count':len(complete_ids(v2)),'qrels_sha256':sha(OUT/'stage1/qrels_v2.json'),'files':{p.name:sha(p) for p in out.iterdir()},'predictions_reused':True,'fresh_original_replay':'../AX-stage123-original-replay-20261103/replay_receipt.json'})
    print('Stage2 complete; full questions',len(complete_ids(v2)))
    for r in base:
        if r['system'] in ('C0','C1') and r['metric'] in ('Precision@5','Recall@5','F1@5','nDCG@10'):print(r['system'],r['metric'],r['value'],r['defined'])


if __name__=='__main__':stage2()
