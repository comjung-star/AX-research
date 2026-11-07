"""Evaluate frozen fresh 20-Validation A/C/E rankings and blind 112-case labels.
No API calls, no new model training. Refuses missing input or incomplete qrels.
Usage: python scripts/validation20_compare.py predictions_new20.json labels_blind_new20.json result.json
predictions: {case_ids:[112], query_ids:[20], systems:{A:[{query_id,ranking}], C:[{query_id,repeat,ranking}], E:[...]}}
labels: {records:[{query_id,case_id,grade:0..3|None,status:"JUDGED"|"ABSTAIN"}]}.
"""
import json,sys,random,math,statistics
from pathlib import Path

def read(p):return json.loads(Path(p).read_text(encoding="utf8"))
def mean(xs):return sum(xs)/len(xs) if xs else None
def dcg(gs):return sum((2**x-1)/math.log2(i+2) for i,x in enumerate(gs))
def rrf(rs,ws,e):
    order={s:{c:i+1 for i,c in enumerate(r)} for s,r in rs.items()}
    base={c:i for i,c in enumerate(e)}
    return sorted(e,key=lambda c:(-sum(w/(60+order[s][c]) for s,w in ws.items()),base[c]))
def evaluate(r,labels,ids):
    known={c:labels.get(c) for c in ids}
    complete=len(known)==112 and all(isinstance(v,int) and 0<=v<=3 for v in known.values())
    positives=sum(v>=2 for v in known.values() if isinstance(v,int))
    result={"complete":complete,"positive_count":positives}
    for k in (5,10,20):
        top=[known[c] for c in r[:k]]
        hit=sum(v is not None and v>=2 for v in top)
        result[f"P@{k}"]=hit/k if all(isinstance(v,int) for v in top) else None
        result[f"R@{k}"]=hit/positives if complete and positives else None
        result[f"F1@{k}"]=2*hit/(k+positives) if complete and positives else None
        if k<=10:
            ideal=dcg(sorted(known.values(),reverse=True)[:k]) if complete else 0
            result[f"nDCG@{k}"]=dcg(top)/ideal if complete and ideal else None
    return result
def main(p_path,l_path,out_path):
    p=read(p_path);z=read(l_path)
    ids=p["case_ids"];qs=p["query_ids"]
    if len(ids)!=112 or len(set(ids))!=112 or len(qs)!=20 or len(set(qs))!=20:raise ValueError("Frozen dataset cardinality mismatch")
    grades={}
    for x in z["records"]:
        k=x["query_id"],x["case_id"]
        if k in grades or k[0] not in qs or k[1] not in ids:raise ValueError("Unexpected or duplicate qrel")
        status=x["status"];g=x["grade"]
        if status=="JUDGED" and (type(g)!=int or g not in range(4)):raise ValueError("Invalid label grade")
        if status not in ("JUDGED","ABSTAIN") or status=="ABSTAIN" and g is not None:raise ValueError("Bad abstain")
        grades[k]=g
    if len(grades)!=2240:raise ValueError("All 2240 qrels must be represented (abstain allowed)")
    systems=p["systems"]
    ranks={}
    for s,n in (("A",20),("C",60),("E",60)):
        if s not in systems or len(systems[s])!=n:raise ValueError("Missing new rankings "+s)
        for row in systems[s]:
            q=row["query_id"];r=row["ranking"];t=row.get("repeat",0)
            if s=="A" and t!=0:raise ValueError("A repeat must be 0")
            if s!="A" and t not in (1,2,3):raise ValueError("Expected three frozen repeats")
            if len(r)!=112 or set(r)!=set(ids):raise ValueError("Invalid full ranking")
            key=s,q,t
            if key in ranks:raise ValueError("Duplicate ranking")
            ranks[key]=r
    metrics={s:{} for s in ("E","I2","I3")}
    model_ranks={s:{} for s in metrics}
    stability={}
    for q in qs:
        qlabels={c:grades[q,c] for c in ids}
        for t in (1,2,3):
            A=ranks["A",q,0];C=ranks["C",q,t];E=ranks["E",q,t]
            rr={"E":E,"I2":rrf({"E":E,"C":C},{"E":.75,"C":.25},E),"I3":rrf({"E":E,"A":A},{"E":.75,"A":.25},E)}
            for s,r in rr.items():
                metrics[s][q,t]=evaluate(r,qlabels,ids)
                model_ranks[s][q,t]=r
    output={"scope":"New Validation 20; NOT independent final Test","model":{},"questions":qs,"qrels":len(grades),"evaluable_query_count":{},"not_human_gold":True}
    for s in metrics:
        agg={};complete=[]
        for q in qs:
            per=[metrics[s][q,t] for t in (1,2,3)]
            if all(x["complete"] and x["positive_count"]>0 for x in per):complete.append(q)
        output["evaluable_query_count"][s]=len(complete)
        for m in ("F1@5","nDCG@10","P@5","R@5"):
            available=[mean([metrics[s][q,t][m] for t in (1,2,3)]) for q in complete]
            agg[m]=mean(available)
        overlaps=[]
        for q in qs:
            for a,b in ((1,2),(1,3),(2,3)):
                L=set(model_ranks[s][q,a][:5]);R=set(model_ranks[s][q,b][:5]);overlaps.append(len(L&R)/len(L|R))
        agg["top5_jaccard"]=mean(overlaps)
        output["model"][s]=agg
    common=sorted(q for q in qs if all(all(metrics[s][q,t]["complete"] and metrics[s][q,t]["positive_count"]>0 for t in (1,2,3)) for s in metrics))
    output["paired_common_questions"]=common
    output["per_query"]=[{"query_id":q,"model":{s:{"F1@5":mean([metrics[s][q,t]["F1@5"] for t in (1,2,3)]) if q in common else None,"nDCG@10":mean([metrics[s][q,t]["nDCG@10"] for t in (1,2,3)]) if q in common else None} for s in metrics}} for q in qs]
    rng=random.Random(20261107);paired={}
    for s in ("I2","I3"):
        paired[s]={}
        for m in ("F1@5","nDCG@10"):
            deltas=[mean([metrics[s][q,t][m]-metrics["E"][q,t][m] for t in (1,2,3)]) for q in common]
            if deltas:
                boot=sorted(mean([rng.choice(deltas) for _ in deltas]) for _ in range(10000))
                paired[s][m]={"mean_delta":mean(deltas),"bootstrap95":[boot[249],boot[9749]],"not_independent_test":True}
            else:paired[s][m]={"mean_delta":None,"bootstrap95":None}
    output["paired_differences_vs_E"]=paired
    Path(out_path).write_text(json.dumps(output,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print(json.dumps({"models":output["model"],"paired":paired,"common_n":len(common)},ensure_ascii=False,indent=2))
if __name__=="__main__":
    if len(sys.argv)!=4:raise SystemExit("Usage: python validation20_compare.py new_predictions.json blind_qrels.json result.json")
    main(*sys.argv[1:])
