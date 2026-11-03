"""Merge blind Silver without overwriting45 originals; evaluate sealed fixed outputs."""
from collections import Counter
import copy
import json
from ax_research.heldout import read,write,jsonl,sha
from ax_research.new_validation import evaluate
from scripts.validation123_analyze import summarize
from scripts.heldout_resume_api import OUT,PRIVATE,PRIOR,PAYLOAD,export_ledger


def score(pred,labels):
    rows=[]
    for rep in (0,1,2,3):
        ns=('E1','E3','E3_NEUTRAL') if not rep else ('E2','E4','E4_NEUTRAL')
        sy={new:[{k:v for k,v in r.items() if k!='repeat'} for r in pred['systems'][old] if not rep or r['repeat']==rep] for new,old in zip(('C0','C1','C1_NO_EMBEDDING'),ns)}
        result=evaluate({'case_ids':pred['case_ids'],'query_ids':pred['query_ids'],'systems':sy},labels)
        for r in result['per_query']:rows.append({**r,'condition':ns[('C0','C1','C1_NO_EMBEDDING').index(r['system'])],'repeat':rep})
    return {'per_query':rows,'macro':summarize(rows,labels),'source':'AI-Silver, one-model independent requests, not Human-Gold','same_question_weight_then_three_repeat_mean':True}


def main():
    for n,h in read(OUT/'predictions/complete.json')['files'].items():assert sha(OUT/'predictions'/n)==h
    pred=read(OUT/'predictions/rankings.json');old=jsonl(PAYLOAD/'qrels.jsonl');labels=copy.deepcopy(old);by={(r['query_id'],r['case_id']):r for r in labels};original={(r['query_id'],r['case_id']):r for r in old};new=[];audits=[]
    for result in read(PRIVATE/'judgments.json')['results']:
        for r in result['assessments']:
            item=by[r['query_id'],r['case_id']]
            if result['category']=='missing':
                assert item['status']=='UNJUDGED';item.update(grade=r['grade'],status=r['status'],label_source='AI-Silver',rationale=r['reason']);new.append({**r,'api_result_id':result['result_id']})
            else:
                x=original[r['query_id'],r['case_id']];audits.append({**r,'api_result_id':result['result_id'],'original_grade':x['grade'],'original_status':x['status'],'grade_disagreement':x['grade']!=r['grade'],'binary_disagreement':(x['grade']>=2)!=(r['grade']>=2) if r['grade'] is not None else None,'original_unchanged':True})
    assert len(new)==1635 and len(audits)==45 and len({(r['query_id'],r['case_id']) for r in new})==1635
    for k,x in original.items():
        if x['status']=='JUDGED':assert by[k]==x
    write(PRIVATE/'qrels_completed_v2.json',{'records':labels,'original_sha256':sha(PAYLOAD/'qrels.jsonl'),'source':'AI-Silver; notGold'})
    d=OUT/'evaluation';d.mkdir(exist_ok=False);write(d/'metrics.json',score(pred,labels));write(d/'audit45.json',{'records':audits,'never_majority_overwrites':True})
    # Newly created evaluations only, original raw45 remain private.
    write(d/'new1635.json',{'records':new,'question_texts_not_exported':True})
    sens=[]
    for name in ('audit45_alternative','binary_disagreements_abstain','all_new_grade2_as_auxiliary1'):
        alt=copy.deepcopy(labels);lookup={(r['query_id'],r['case_id']):r for r in alt}
        if name=='all_new_grade2_as_auxiliary1':
            for r in new:
                if r['grade']==2:lookup[r['query_id'],r['case_id']]['grade']=1
        for a in audits:
            r=lookup[a['query_id'],a['case_id']]
            if name=='audit45_alternative':r.update(grade=a['grade'],status=a['status'])
            elif name=='binary_disagreements_abstain' and (a['binary_disagreement'] is True or a['grade'] is None):r.update(grade=None,status='ABSTAIN')
        sens.append({'scenario':name,'counterfactual_not_replacing_original':True,**score(pred,alt)})
    write(d/'label_sensitivity.json',{'scenarios':sens})
    cross=[];first={(r['query_id'],r['case_id']):r for r in new}
    for a in read(PRIVATE/'crosscheck.json')['assessments']:
        f=first[a['query_id'],a['case_id']];cross.append({**a,'first_grade':f['grade'],'first_status':f['status'],'grade_disagreement':f['grade']!=a['grade'],'binary_disagreement':(f['grade']>=2)!=(a['grade']>=2) if a['grade'] is not None and f['grade'] is not None else None,'primary_unchanged':True})
    write(d/'new_label_crosscheck.json',{'records':cross,'same_prompt_same_model_separate_requests':True,'human_gold':False})
    alt=copy.deepcopy(labels);lookup={(r['query_id'],r['case_id']):r for r in alt}
    for a in cross:
        if a['binary_disagreement'] is True or a['grade'] is None:lookup[a['query_id'],a['case_id']].update(grade=None,status='ABSTAIN')
    write(d/'new_label_crosscheck_sensitivity.json',{'scenario':'new_positive_binary_disagreements_quarantined_not_main_labels','counterfactual_only':True,**score(pred,alt)})
    cautious=copy.deepcopy(labels);lookup={(r['query_id'],r['case_id']):r for r in cautious};quality=read(OUT/'quality_review.json')
    for pair in quality['source_cautious_ABSTAIN_pairs']:
        assert original[pair['query_id'],pair['case_id']]['status']=='UNJUDGED','Never mask original45 in source-cautious version'
        lookup[pair['query_id'],pair['case_id']].update(grade=None,status='ABSTAIN',rationale=pair['reason'])
    write(PRIVATE/'qrels_source_cautious_v3.json',{'records':cautious,'source_review_holds':quality['source_cautious_ABSTAIN_pairs'],'human_gold':False})
    write(d/'source_cautious_metrics.json',{'label_version':'Separate source-cautious AI-Silver v3; original primary unchanged','ABSTAIN_pairs':quality['source_cautious_ABSTAIN_pairs'],'full_private_sha256':sha(PRIVATE/'qrels_source_cautious_v3.json'),**score(pred,cautious)})
    ranks={(n,r['query_id'],r.get('repeat',0)):r for n,rs in pred['systems'].items() for r in rs};changes=[]
    for nold,nnew in [('E1','E2'),('E3','E4'),('E1','E3'),('E2','E4'),('E3','E3_NEUTRAL'),('E4','E4_NEUTRAL')]:
        for q in pred['query_ids']:
            positives={r['case_id'] for r in labels if r['query_id']==q and r['grade'] is not None and r['grade']>=2}
            for rep in ((1,2,3) if nnew in ('E2','E4','E4_NEUTRAL') else (0,)):
                a=ranks[nold,q,rep if nold in ('E2','E4') else 0]['ranking'];b=ranks[nnew,q,rep]['ranking']
                for k in (5,10,20):
                    x=set(a[:k])&positives;y=set(b[:k])&positives
                    changes.append({'comparison':nold+'->'+nnew,'query_id':q,'repeat':rep,'k':k,'gained':sorted(y-x),'lost':sorted(x-y),'retained':sorted(x&y),'unresolved_old':sum(by[q,c]['grade'] is None for c in a[:k]),'unresolved_new':sum(by[q,c]['grade'] is None for c in b[:k])})
    write(d/'gains_losses.json',{'records':changes,'counts_are_query_case_repeat_events_not_unique_cases':True})
    evidence={(r['query_id'],r['case_id']):r for r in read(PRIOR/'stage5/predictions/score_evidence.json')['records']};combined={(r['query_id'],r['repeat'],r['case_id']):r for r in jsonl(OUT/'predictions/combined_scores.jsonl')};paths=read(PRIVATE/'predictions/paths.json')['paths'];branches={(r['path_id'],r['case_id']):r for r in jsonl(OUT/'predictions/branch_scores.jsonl')};details=[]
    # Every grade>=2 case gets rank/component histories, including failures.
    for r in labels:
        if r['grade'] is None or r['grade']<2:continue
        q,c=r['query_id'],r['case_id'];details.append({'query_id':q,'case_id':c,'grade':r['grade'],'rationale':('Original private label rationale retained locally' if original[q,c]['status']=='JUDGED' else r['rationale']),'label_origin':('original45' if original[q,c]['status']=='JUDGED' else 'new1635'),'ranks':{n:[{'repeat':x.get('repeat',0),'rank':x['ranking'].index(c)+1} for x in rs if x['query_id']==q] for n,rs in pred['systems'].items()},'original':evidence[q,c],'combined':[combined[q,rep,c] for rep in (1,2,3)],'branch_components':[{'path_id':p['query_id'],'repeat':p['repeat'],'scores':branches[p['query_id'],c]} for p in paths if p['parent_query_id']==q]})
    write(d/'relevant_case_diagnostics.json',{'records':details,'all112_candidates_retained':True,'not_a_causal_ablation_of_each_perspective':True})
    status=Counter(r['status'] for r in labels);full=[q for q in pred['query_ids'] if all(r['status']=='JUDGED' for r in labels if r['query_id']==q)];write(d/'label_manifest.json',{'total':1680,'new_evaluated':1635,'original45_preserved':True,'status_counts':dict(status),'grade_counts':dict(Counter(str(r['grade']) for r in labels)),'full_question_ids':full,'full_question_count':len(full),'original_sha256':sha(PAYLOAD/'qrels.jsonl'),'new_full_private_sha256':sha(PRIVATE/'qrels_completed_v2.json'),'human_verified':False,'grade_disagreements_45':sum(r['grade_disagreement'] for r in audits),'binary_disagreements_45':sum(r['binary_disagreement'] is True for r in audits),'ABSTAIN_never_zero':True})
    write(d/'complete.json',{'evaluation_complete':True,'prediction_seal_sha256':sha(OUT/'predictions/complete.json'),'label_version_sha256':sha(PRIVATE/'qrels_completed_v2.json'),'files':{p.name:sha(p) for p in d.iterdir()},'tuned':False})
    export_ledger();print('Evaluation completed',dict(status),'complete questions',len(full))


if __name__=='__main__':main()
