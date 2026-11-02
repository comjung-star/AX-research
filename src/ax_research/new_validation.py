"""New-validation0-3>=2 evaluator; incomplete/abstain never silently zero."""
import math
from collections import defaultdict

SYSTEMS=('C0','C1','C1_NO_EMBEDDING')


def evaluate(pred,rows):
    ids=pred['case_ids'];qs=pred['query_ids'];labels={q:{} for q in qs}
    if len(ids)!=112 or len(set(ids))!=112 or not qs or len(qs)!=len(set(qs)) or set(pred['systems'])!=set(SYSTEMS):raise ValueError('Invalid registry/systems')
    for row in rows:
        q=row['query_id'];c=row['case_id'];status=row['status'];g=row['grade']
        if q not in labels or c not in ids or c in labels[q]:raise ValueError('Invalid/duplicate label ID')
        if row['label_source']!='AI-Silver':raise ValueError('Expected explicitly non-human source')
        if status=='JUDGED':
            if type(g) is not int or g not in range(4):raise ValueError('Invalid grade')
        elif status in ('ABSTAIN','UNJUDGED'):
            if g is not None:raise ValueError('Abstain/unjudged must be null')
        else:raise ValueError('Invalid status')
        if not isinstance(row['rationale'],str) or (status!='UNJUDGED' and not row['rationale'].strip()):raise ValueError('Rationale required')
        labels[q][c]=g if status=='JUDGED' else None
    results=[]
    for name,runs in pred['systems'].items():
        if len(runs)!=len(qs) or {r['query_id'] for r in runs}!=set(qs):raise ValueError('Invalid question mapping')
        for r in runs:
            q=r['query_id'];rank=r['ranking'];g=labels[q]
            if len(rank)!=112 or set(rank)!=set(ids):raise ValueError('Invalid ranking')
            full=len(g)==112 and all(v is not None for v in g.values());pos={c for c,v in g.items() if v is not None and v>=2};metrics={};reasons={};counts={}
            for k in (5,10,20):
                top=[g.get(c) for c in rank[:k]];judged=all(v is not None for v in top)
                p=sum(v>=2 for v in top)/k if judged else None
                recall=sum(v>=2 for v in top)/len(pos) if full and pos else None
                f1=2*sum(v>=2 for v in top)/(k+len(pos)) if full and pos else None
                metrics.update({f'Precision@{k}':p,f'Recall@{k}':recall,f'F1@{k}':f1})
                counts[str(k)]={'grade0':sum(v==0 for v in top),'grade1':sum(v==1 for v in top),'grade2':sum(v==2 for v in top),'grade3':sum(v==3 for v in top),'unresolved':sum(v is None for v in top)}
                if p is None:reasons[f'Precision@{k}']='TOPK_UNJUDGED_OR_ABSTAIN'
                if recall is None:reasons[f'Recall@{k}']=reasons[f'F1@{k}']='ZERO_POSITIVES' if full else 'INCOMPLETE_QRELS'
                if k in (5,10):
                    dcg=lambda seq:sum((2**v-1)/math.log2(i+2) for i,v in enumerate(seq))
                    den=dcg(sorted(g.values(),reverse=True)[:k]) if full else None
                    metrics[f'nDCG@{k}']=dcg(top)/den if full and den else None
                    if metrics[f'nDCG@{k}'] is None:reasons[f'nDCG@{k}']='ZERO_IDCG' if full else 'INCOMPLETE_QRELS'
            results.append({'system':name,'query_id':q,'judged':sum(v is not None for v in g.values()),'complete112':full,'positive_count':len(pos),'metrics':metrics,'undefined_reasons':reasons,'topk_grade_counts':counts,'strong_grade3_ranks':{c:rank.index(c)+1 for c,v in g.items() if v==3}})
    lookup={(r['system'],r['query_id']):r for r in results};macro=[]
    for group,names in [('primary',('C0','C1')),('embedding',('C1','C1_NO_EMBEDDING'))]:
        for metric in results[0]['metrics']:
            eligible=[q for q in qs if all(lookup[n,q]['metrics'][metric] is not None for n in names)]
            for name in names:
                vals=[lookup[name,q]['metrics'][metric] for q in eligible]
                macro.append({'comparison':group,'system':name,'metric':metric,'value':sum(vals)/len(vals) if vals else None,'defined':len(vals),'total':len(qs),'included_query_ids':eligible,'excluded_query_ids':[q for q in qs if q not in eligible]})
    return {'per_query':results,'macro_common_queries':macro,'label_source':'AI-Silver same author/reviewer; not independent Gold','threshold':2,'grade_scale':[0,1,2,3],'question_count':len(qs),'qrel_rows':len(rows)}
