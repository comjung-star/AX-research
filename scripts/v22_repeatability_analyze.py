#!/usr/bin/env python3
"""Validate three independent v2.2 AI draft passes; write blind researcher sample.

This is a REPEATABILITY measurement; nothing is human GT or retrieval accuracy.
"""
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"data/v2_2"
OUT=BASE/"qa/ai_repeatability_2026-10-23"
RUNS=(1,2,3)
SAMPLE_SIZE=50

def read_csv(path):
 with path.open(encoding="utf-8",newline="") as f:
  return list(csv.DictReader(f))

def write_csv(path,rows,fields):
 path.parent.mkdir(parents=True,exist_ok=True)
 with path.open("w",encoding="utf-8",newline="") as f:
  writer=csv.DictWriter(f,fieldnames=fields)
  writer.writeheader(); writer.writerows(rows)

def analyze():
 corpus=json.loads((BASE/"main_cases_v2_2.json").read_text(encoding="utf-8"))
 qs=json.loads((BASE/"dev_query_candidates_v2_2.json").read_text(encoding="utf-8"))["queries"]
 case_by_id={c["case_id"]:c for c in corpus["cases"]}
 q_by_id={q["query_id"]:q for q in qs}
 assert len(case_by_id)==93 and len(q_by_id)==10
 expected={(q["query_id"],p["id"],case_id)
  for q in qs for p in q["draft_perspectives"] for case_id in case_by_id}
 assert len(expected)==2790
 passes={}
 manifests=[]
 for pass_id in RUNS:
  current={}
  for query_id in q_by_id:
   d=OUT/f"v22-repeat-{query_id}-p{pass_id}"
   rows=read_csv(d/"ratings.csv")
   manifest=json.loads((d/"manifest.json").read_text(encoding="utf-8"))
   assert len(rows)==279 and manifest["judgments"]==279
   assert manifest["pass_id"]==pass_id and manifest["query_id"]==query_id
   assert manifest["human_gt_count"]==0
   assert manifest["corpus_git_blob"]=="4761cbf5e9d41f4c75faa26a01023eb0efcada08"
   assert manifest["previous_scores_supplied_to_model"] is False
   assert len(manifest["batch_responses"])==8
   manifests.append(manifest)
   for row in rows:
    key=(row["query_id"],row["perspective_id"],row["case_id"])
    assert key in expected and key not in current, "Missing/duplicate/unexpected"
    assert row["status"]=="AI_REPEATED_DRAFT_NOT_HUMAN_GT"
    assert int(row["pass_id"])==pass_id
    score=int(row["provisional_relevance_0_4"])
    assert 0<=score<=4 and row["evidence_reason"].strip()
    current[key]=score
  assert set(current)==expected,f"Pass {pass_id} incomplete"
  passes[pass_id]=current
 assert len({m["prompt_sha256"] for m in manifests})==1,"Passes used different rubric"
 assert len({m["model_requested"] for m in manifests})==1,"Passes used different models"
 detail=[]
 grouped=defaultdict(list)
 for key in sorted(expected):
  ss=[passes[p][key] for p in RUNS]
  changed=len(set(ss))!=1
  flip=len(set(s>=3 for s in ss))!=1
  record=dict(query_id=key[0],perspective_id=key[1],case_id=key[2],
   pass1=ss[0],pass2=ss[1],pass3=ss[2],exact_agreement=not changed,
   threshold_flip=flip,max_score_gap=max(ss)-min(ss),
   median_score=sorted(ss)[1],all_relevant=all(s>=3 for s in ss))
  detail.append(record)
  grouped[key[0]].append(record)
 exact=sum(x["exact_agreement"] for x in detail)
 flips=sum(x["threshold_flip"] for x in detail)
 disagreements=len(detail)-exact
 counts={"judgments_per_pass":2790,"total_api_grades":8370,
  "exact_agreement_count":exact,"different_score_count":disagreements,
  "threshold_flip_count":flips,"threshold_agreement_count":2790-flips,
  "exact_agreement_rate":round(exact/2790,4),
  "threshold_agreement_rate":round((2790-flips)/2790,4),
  "max_gap_ge_2":sum(x["max_score_gap"]>=2 for x in detail)}
 output={}
 for q,records in sorted(grouped.items()):
  output[q]={"total":len(records),"same_score":sum(x["exact_agreement"] for x in records),
   "different_score":sum(not x["exact_agreement"] for x in records),
   "threshold_flips":sum(x["threshold_flip"] for x in records)}
 write_csv(OUT/"three_pass_comparison.csv",[
   {**r,**{k:str(r[k]).upper() for k in ("exact_agreement","threshold_flip","all_relevant")}}
   for r in detail],list(detail[0]))
 # Retain score-wise evidence independently; the human sheet is *blind*.
 def stable_key(item):
  tie=hashlib.sha256("|".join((item["query_id"],item["perspective_id"],item["case_id"])).encode()).hexdigest()
  return (-item["max_score_gap"],tie)
 def balanced_pick(pool,needed,selected):
  groups=defaultdict(list)
  for r in pool:
   key=(r["query_id"],r["perspective_id"],r["case_id"])
   if key not in selected:groups[r["query_id"]].append(r)
  for rows in groups.values():rows.sort(key=stable_key)
  out=[]
  while len(out)<needed:
   progressed=False
   for q in sorted(groups):
    if len(out)>=needed:break
    if groups[q]:
     r=groups[q].pop(0)
     out.append(r);selected.add((r["query_id"],r["perspective_id"],r["case_id"]))
     progressed=True
   if not progressed:break
  return out
 selected=set()
 chosen=[]
 for qid,pid,cid in [
  ("V21D006","P1_CATALOG_ENRICHMENT_BURDEN","AXV22_0092_01"),
  ("V21D009","P1_AI_SECURITY_COMPLIANCE_CONSTRAINT","AXV22_0093_01")]:
  one=next(x for x in detail if (x["query_id"],x["perspective_id"],x["case_id"])==(qid,pid,cid))
  chosen.append(one);selected.add((qid,pid,cid))
 chosen+=balanced_pick([r for r in detail if r["threshold_flip"]],33,selected)
 chosen+=balanced_pick([r for r in detail if not r["threshold_flip"] and not r["exact_agreement"]],10,selected)
 chosen+=balanced_pick([r for r in detail if r["exact_agreement"]],5,selected)
 chosen+=balanced_pick(detail,SAMPLE_SIZE-len(chosen),selected)
 assert len(chosen)==SAMPLE_SIZE
 blind=[]
 for i,r in enumerate(chosen,1):
  q=q_by_id[r["query_id"]]
  view=next(p for p in q["draft_perspectives"] if p["id"]==r["perspective_id"])
  c=case_by_id[r["case_id"]]
  blind.append({"review_id":f"V22R{i:03d}","query_id":r["query_id"],
   "reference_perspective":view["title"],"case_id":r["case_id"],
   "business_problem_query":q["business_problem_query"],
   "case_problem":c["problem"],"case_task":c["task"],"case_context":c["context"],
   "human_score_0_4":"","human_reason":"","reviewer_id":"","status":"UNJUDGED"})
 write_csv(OUT/"human_blind_review_50.csv",blind,list(blind[0]))
 report={
  "corpus_version":"v2.2.0","run_date":"2026-10-23",
  "status":"THREE_AI_DRAFT_PASSES_COMPLETE_NO_HUMAN_GOLD",
  "method":"3 fresh stateless API grading passes with same model, rubric and 13-case batch boundaries; no previous labels provided to API",
  "source_corpus_git_blob":"4761cbf5e9d41f4c75faa26a01023eb0efcada08",
  "model_requested":manifests[0]["model_requested"],
  "prompt_sha256":manifests[0]["prompt_sha256"],
  "counts":counts,"by_query":output,
  "human_sample_size":len(blind),
  "selection_rule":"2 new-case anchors, up to 33 grade≥3 threshold flip cases, 10 same-threshold grade disagreements, 5 stable controls, balanced by query, fill to 50, fixed SHA-based ties",
  "source_screened_new_cases_in_sample":2,
  "human_gold_count":0,
  "limitations":[
   "AI repeated ratings are not proof of factual correctness.",
   "Only 50 pilot human review candidates; not an adjudicated 2790-label Ground Truth.",
   "Dev cases selected after coverage gap assessment: do not claim model performance improvement.",
   "Large sample of correlated judgments: do not treat 2790 judgment slots as independent experimental units.",
   "No retrieval Recall@K, Strategy Coverage, human accuracy or held-out claims until independent GT."
  ],
  "artifacts":{
   "comparison":"three_pass_comparison.csv",
   "blind_review":"human_blind_review_50.csv",
   "full_repeats":"v22-repeat-V21D00x-p1..p3/ratings.csv + raw_batches"
  }
 }
 (OUT/"repeatability_report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 (OUT/"researcher_quick_report.md").write_text(
  "# AX v2.2 AI 반복채점 요약 (정답 인증 아님)\n\n"
  +f"- 대상: 93개 사례 × 10개 문제 × 관점 3개 = **2,790개**\n"
  +f"- 반복: **3회**, AI 점수 총 **8,370개**\n"
  +f"- 세 번 모두 같은 점수: **{exact:,}개 / 2,790개 ({100*exact/2790:.1f}%)**\n"
  +f"- 한 번이라도 다른 점수: **{disagreements:,}개**\n"
  +f"- 관련 사례(3–4점) 여부가 바뀐 경우: **{flips:,}개**\n"
  +f"- 사람이 먼저 검토할 블라인드 표본: **{len(blind)}개**\n"
  +"\n**주의:** 인간이 검증한 최종 정답은 0개다. 이 결과로 검색모델 정확도가 높아졌다고 주장하지 않는다.\n"
  +"\n세부 결과는 `repeatability_report.json`, 본인 평가표는 `human_blind_review_50.csv`.\n",
  encoding="utf-8")
 print(json.dumps({"complete":True,**counts,"human_blind_review":len(blind)},ensure_ascii=False))

if __name__=="__main__":
 analyze()
