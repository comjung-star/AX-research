#!/usr/bin/env python3
"""Recompute frozen NEW_VALIDATION_20 rankings using strict/transfer qrels.

No model training, API requests, or retrieval rerun. Python 3.10+ stdlib only.
Run from repository root: python scripts/revalidate_transfer20_20261108.py
"""
import json, math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DOC=ROOT/"docs/ax-transfer-relevance-20261108"
RANK=ROOT/"docs/validation-new20-20261107/measured/predictions_new20.json"
STRICT=ROOT/"docs/stage12-assisted-recheck-20261108/working_qrels_2240.json"
TRANSFER=DOC/"02_working_transfer_qrels_2240.json"

def load(p): return json.loads(p.read_text(encoding="utf-8"))
def avg(xs): return sum(xs)/len(xs) if xs else None
def dcg(grades): return sum((2**g-1)/math.log2(i+2) for i,g in enumerate(grades))
def combine(base, other):
    r1={c:i+1 for i,c in enumerate(base)}
    r2={c:i+1 for i,c in enumerate(other)}
    return sorted(base,key=lambda c:(-(.75/(60+r1[c])+.25/(60+r2[c])),r1[c]))
def compare(pred, labels):
    cases=pred["case_ids"]; queries=pred["query_ids"]
    assert len(cases)==112 and len(set(cases))==112
    assert len(queries)==20 and len(set(queries))==20
    assert len(labels["records"])==2240
    gold={(x["query_id"],x["case_id"]):x["grade"] for x in labels["records"]}
    assert len(gold)==2240 and all(type(v) is int and 0<=v<=3 for v in gold.values())
    systems={}
    for method,expected in (("A",20),("C",60),("E",60)):
        rows=pred["systems"][method]
        assert len(rows)==expected
        systems[method]={(r["query_id"],r.get("repeat",0)):r["ranking"] for r in rows}
        assert len(systems[method])==expected
        for values in systems[method].values():
            assert len(values)==112 and set(values)==set(cases)
    per_query=[]
    for q in queries:
        vals={c:gold[q,c] for c in cases}
        positives=sum(v>=2 for v in vals.values())
        ideal=dcg(sorted(vals.values(),reverse=True)[:10])
        score={m:{"f1":[],"ndcg":[],"p5":[],"recall":[]} for m in ("A","C","E","I2","I3")}
        for i in (1,2,3):
            a=systems["A"][(q,0)]
            c=systems["C"][(q,i)]
            e=systems["E"][(q,i)]
            ranks={"A":a,"C":c,"E":e,"I2":combine(e,c),"I3":combine(e,a)}
            for m,r in ranks.items():
                scores=[vals[x] for x in r[:10]]
                hit=sum(g>=2 for g in scores[:5])
                score[m]["f1"].append(2*hit/(5+positives) if positives else None)
                score[m]["ndcg"].append(dcg(scores)/ideal if positives else None)
                score[m]["p5"].append(hit/5)
                score[m]["recall"].append(hit/positives if positives else None)
        for m,s in score.items():
            for metric,vs in s.items():
                s[metric]=avg([v for v in vs if v is not None])
        per_query.append({"id":q,"positives":positives,"methods":score})
    out={"relevant_questions":sum(row["positives"]>0 for row in per_query),
         "no_positive_questions":[row["id"] for row in per_query if row["positives"]==0],
         "models":{}, "per_query":per_query}
    pos=[row for row in per_query if row["positives"]>0]
    for m in ("A","C","E","I2","I3"):
        out["models"][m]={
          "P_at_5_all20":avg([row["methods"][m]["p5"] for row in per_query]),
          "F1_at_5_eligible_only":avg([row["methods"][m]["f1"] for row in pos]),
          "nDCG_at_10_eligible_only":avg([row["methods"][m]["ndcg"] for row in pos]),
          "Recall_at_5_eligible_only":avg([row["methods"][m]["recall"] for row in pos]),
          "F1_at_5_all20_zero_positive_as_0":avg([row["methods"][m]["f1"] or 0 for row in per_query])
        }
    return out

def main():
    pred=load(RANK)
    report=load(DOC/"03_same20_comparison.json")
    for name,source in (
      ("STRICT_TASK_ASSISTED_QRELS_20261108",STRICT),
      ("STRATEGY_TRANSFER_WORKING_QRELS_20261108",TRANSFER)):
        actual=compare(pred,load(source))
        stored=report["comparison"][name]
        assert actual["relevant_questions"]==stored["eligible"]
        assert len(actual["no_positive_questions"])==stored["zero"]
        for m,r in actual["models"].items():
            for actual_key,stored_key in (
              ("P_at_5_all20","P_at_5_ALL20"),
              ("F1_at_5_eligible_only","F1_at_5_positive_only"),
              ("nDCG_at_10_eligible_only","nDCG_at_10_positive_only"),
              ("Recall_at_5_eligible_only","Recall_at_5_positive_only"),
              ("F1_at_5_all20_zero_positive_as_0","F1_at_5_ALL20_zero_positive_as_0")):
                assert math.isclose(r[actual_key],stored["metrics"][m][stored_key],abs_tol=1e-12), (name,m,actual_key)
        print(name,actual["relevant_questions"],actual["models"])
    print("PASS: 20 queries; 112 cases; all 2240 labels; 5 methods; two qrel protocols")

if __name__=="__main__": main()
