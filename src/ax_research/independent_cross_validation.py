"""Fixed-output precision bounds and question-level paired uncertainty."""
from collections import Counter
import numpy as np


def utility(grade):
    if grade in (None,'ABSTAIN'):return None
    if int(grade) not in range(4):raise ValueError('invalid grade')
    return int(int(grade)>=2)


def score_question(a,b,grades,omit=None):
    assert len(a)==len(set(a))==len(b)==len(set(b)) and len(a)>0
    k=len(a);omit=set(omit or [])
    def method(ids):
        values=[utility(grades.get(c)) for c in ids]
        hits=sum(v==1 for v in values);unknown=sum(v is None for v in values)
        return {'K':k,'known_useful':hits,'unresolved':unknown,'precision_lower':hits/k,'precision_upper':(hits+unknown)/k,
                'judged_only_precision_descriptive':hits/(k-unknown) if k>unknown else None}
    lo=hi=0;new=[];lost=[];unew=[];ulost=[]
    for c in set(a)|set(b):
        coefficient=int(c in b)-int(c in a)
        if c in omit:continue
        value=utility(grades.get(c))
        if value is None:
            lo+=min(0,coefficient);hi+=max(0,coefficient)
            if coefficient>0:unew.append(c)
            if coefficient<0:ulost.append(c)
        else:
            lo+=coefficient*value;hi+=coefficient*value
            if coefficient>0 and value:new.append(c)
            if coefficient<0 and value:lost.append(c)
    return {'A':method(a),'B':method(b),'delta_lower':lo/k,'delta_upper':hi/k,
            'known_new_useful':sorted(new),'known_lost_useful':sorted(lost),'unresolved_new':sorted(unew),'unresolved_lost':sorted(ulost)}


def bootstrap_bounds(rows,seed=20261110,n=20000):
    lower=np.array([r['delta_lower'] for r in rows]);upper=np.array([r['delta_upper'] for r in rows])
    idx=np.random.default_rng(seed).integers(0,len(rows),size=(n,len(rows)))
    lowmeans=lower[idx].mean(axis=1);himeans=upper[idx].mean(axis=1)
    return {'n_questions':len(rows),'replicates':n,'seed':seed,'mean_delta_lower':float(lower.mean()),'mean_delta_upper':float(upper.mean()),
            'paired_bootstrap95_envelope':[float(np.quantile(lowmeans,.025)),float(np.quantile(himeans,.975))],
            'point_delta':float(lower.mean()) if np.array_equal(lower,upper) else None,
            'interpretation':'Question-resampled percentile envelope over worst/best unresolved assignments. Shared unresolved pair utility is identical in A/B and cancels; not an independence assumption for repeated cases.'}


def agreement(left,right):
    keys=sorted(set(left)&set(right));eligible=[k for k in keys if utility(left[k]) is not None and utility(right[k]) is not None]
    matrix=np.zeros((4,4),dtype=int)
    for k in eligible:matrix[int(left[k]),int(right[k])]+=1
    n=int(matrix.sum())
    if not n:return {'overlapping_keys':len(keys),'eligible_nonabstain':0,'binary_agreement':None,'exact_score_agreement':None,'unweighted_kappa':None,'quadratic_weighted_kappa':None,'confusion_0to3':matrix.tolist()}
    observed=matrix/n;expected=np.outer(observed.sum(axis=1),observed.sum(axis=0));weights=np.fromfunction(lambda i,j:1-(i-j)**2/9,(4,4))
    po=float(np.trace(observed));pe=float(np.trace(expected));pw=float((observed*weights).sum());ew=float((expected*weights).sum())
    binary=sum(utility(left[k])==utility(right[k]) for k in eligible)/n
    return {'overlapping_keys':len(keys),'eligible_nonabstain':n,'binary_agreement':binary,'exact_score_agreement':po,
            'unweighted_kappa':(po-pe)/(1-pe) if pe<1 else None,'quadratic_weighted_kappa':(pw-ew)/(1-ew) if ew<1 else None,'confusion_0to3':matrix.tolist()}


def summarize(recommendations,grades_by_question):
    rows={q:score_question(v['A'],v['B'],grades_by_question.get(q,{})) for q,v in recommendations.items()}
    result={'per_question':rows,'statistics':bootstrap_bounds(list(rows.values())),'macro':{}}
    for m in ('A','B'):
        result['macro'][m]={k:sum(r[m][k] for r in rows.values())/len(rows) for k in ('precision_lower','precision_upper')}
        result['macro'][m]['known_useful_pairs']=sum(r[m]['known_useful'] for r in rows.values())
        result['macro'][m]['unresolved_recommendations']=sum(r[m]['unresolved'] for r in rows.values())
    result['question_decisions']={'improved':sum(r['delta_lower']>0 for r in rows.values()),'worsened':sum(r['delta_upper']<0 for r in rows.values()),
                                  'same':sum(r['delta_lower']==r['delta_upper']==0 for r in rows.values()),'uncertain':sum(not(r['delta_lower']>0 or r['delta_upper']<0 or r['delta_lower']==r['delta_upper']==0) for r in rows.values())}
    result['useful_pairs']={k:sum(len(r[k]) for r in rows.values()) for k in ('known_new_useful','known_lost_useful','unresolved_new','unresolved_lost')}
    return result
