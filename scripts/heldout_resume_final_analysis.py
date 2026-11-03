"""Free deterministic analysis of the final cautious label version."""
from ax_research.heldout import read,write
from scripts.heldout_resume_api import OUT,PRIVATE
from scripts.validation123_analyze import summarize


def save_or_verify(path,data):
    if path.exists():assert read(path)==data,'Existing artifact drift'
    else:write(path,data)


def main():
    pred=read(OUT/'predictions/rankings.json');labels=read(PRIVATE/'qrels_final_cautious_v4.json')['records'];by={(r['query_id'],r['case_id']):r for r in labels};lookup={(n,r['query_id'],r.get('repeat',0)):r for n,rs in pred['systems'].items() for r in rs};changes=[]
    for old,new in [('E1','E2'),('E3','E4'),('E2','E4')]:
        for q in pred['query_ids']:
            pos={r['case_id'] for r in labels if r['query_id']==q and r['grade'] is not None and r['grade']>=2}
            for rep in (1,2,3):
                a=lookup[old,q,rep if old=='E2' else 0]['ranking'];b=lookup[new,q,rep]['ranking']
                for k in (5,10,20):
                    x=set(a[:k])&pos;y=set(b[:k])&pos;changes.append({'comparison':old+'->'+new,'query_id':q,'repeat':rep,'k':k,'gained':sorted(y-x),'lost':sorted(x-y),'retained':sorted(x&y),'unresolved_old':sum(by[q,c]['grade'] is None for c in a[:k]),'unresolved_new':sum(by[q,c]['grade'] is None for c in b[:k])})
    save_or_verify(OUT/'final_gains_losses.json',{'label_version':'source-cautious-v4','records':changes,'unknown_never_negative':True,'event_counts_not_unique_cases':True})
    m=read(OUT/'quality_final/metrics.json');qs=[]
    for q in pred['query_ids']:
        rows=[r for r in labels if r['query_id']==q];qs.append({'query_id':q,'judged':sum(r['status']=='JUDGED' for r in rows),'ABSTAIN':sum(r['status']=='ABSTAIN' for r in rows),'known_positive':sum(r['grade'] is not None and r['grade']>=2 for r in rows),'positive_absence_confirmed_only_within_AI_Silver':all(r['status']=='JUDGED' for r in rows) and not any(r['grade'] is not None and r['grade']>=2 for r in rows)})
    leave_one_out=[{'excluded':q,'macro':summarize(m['per_query'],labels,[q])} for q in pred['query_ids']]
    coverage=read(OUT/'component_coverage.json')
    save_or_verify(OUT/'final_analysis.json',{'query_coverage':qs,'no_positive_complete_questions':[q['query_id'] for q in qs if q['positive_absence_confirmed_only_within_AI_Silver']],'leave_one_question_out':leave_one_out,'candidate_truncation_losses':0,'candidate_count_every_path':112,'no_recognized_C1_function_paths':coverage['no_C1_rule_function_paths'],'total_perspective_paths':coverage['perspective_paths'],'causal_limit':'Component values and rank movements are descriptive; no tuning or per-stage replacement test'})


if __name__=='__main__':main()
