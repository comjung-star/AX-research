"""Assemble blinded 20x112 qrels and sealed new20 rank predictions.

All inputs must come from authentic GitHub Actions artifacts, never from past 8 Dev ranks.
Only calculates full metrics for wholly judged cases, handling abstentions explicitly.
"""
import json,subprocess,sys,hashlib
from pathlib import Path
from decimal import Decimal

ROOT=Path(__file__).resolve().parents[1]
QUESTIONS=ROOT/"docs/validation-new20-20261107/questions.jsonl"
CASES=ROOT/"docs/dense-bm25-candidates-2026-10-27/case_registry.json"
def load(p):return json.loads(Path(p).read_text(encoding="utf8"))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,obj):Path(p).write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf8")
def main(pred_path,grade_dir,out):
    out.mkdir(parents=True,exist_ok=False)
    questions={r["query_id"]:r["text"] for r in (json.loads(t) for t in QUESTIONS.read_text(encoding="utf8").splitlines() if t.strip())}
    cases=load(CASES)["cases"]
    issues=[];records=[];spent=Decimal(0)
    if len(questions)!=20 or len(cases)!=112:raise RuntimeError("Registry cardinality changed")
    pred=load(pred_path)
    if len(pred["query_ids"])!=20 or len(pred["case_ids"])!=112 or set(pred["case_ids"])!=set(cases):
        raise RuntimeError("Predictions are not from new20 and same case registry")
    for q in sorted(questions):
        f=grade_dir/("labels_"+q+".json")
        status=grade_dir/("status_"+q+".json")
        if not f.exists() or not status.exists():
            issues.append({"question":q,"reason":"missing grader files"});continue
        s=load(status)
        if s.get("blind_predictions_not_accessed") is not True or s.get("input_question_sha256")!=sha(QUESTIONS) or s.get("corpus_sha256")!=sha(CASES):
            issues.append({"question":q,"reason":"question/corpus or blind audit mismatch"});continue
        c=Decimal(s.get("API_consumption",{}).get("conservative_spent_or_reserved_usd","0"))
        if c>Decimal(".09"):issues.append({"question":q,"reason":"cost cap violated"});continue
        spent+=c
        items=load(f)["records"]
        if len(items)!=112 or {r["case_id"] for r in items}!=set(cases) or any(r["query_id"]!=q for r in items):
            issues.append({"question":q,"reason":"incomplete or duplicate cases"});continue
        if any((r["status"]=="JUDGED" and (type(r["grade"])!=int or r["grade"] not in range(4))) or
               (r["status"]=="ABSTAIN" and r["grade"] is not None) or
               r["status"] not in ("JUDGED","ABSTAIN") for r in items):
            issues.append({"question":q,"reason":"invalid grades/status"});continue
        records.extend(items)
    status={"scope":"new20 Validation (not independent Test)","questions":len(questions),"case_count":len(cases),
         "received_labels":len(records),"expected_labels":2240,
         "questions_with_complete_case_id_coverage":len(records)//112,
         "issues":issues,"source":"one AI model evaluated blind to model rankings, not human gold",
         "grading_conservative_spent_or_reserved_usd":str(spent),
         "prior_generation_conservative_usd":"0.056714375",
         "total_conservative_cap_usd":"2.00",
         "total_conservative_spent_or_reserved_usd":str(spent+Decimal("0.056714375")),
         "no_old_independent_Test_access":True}
    if spent+Decimal("0.056714375")>2:issues.append({"reason":"overall cost cap exceeded"})
    if issues:
        status["state"]="EVALUATION_BLOCKED_PARTIAL_GRADING"
        write(out/"assembly_status.json",status)
        if records:write(out/"available_blind_labels.json",{"records":records})
        print(json.dumps(status,ensure_ascii=False,indent=2));return
    write(out/"labels_new20.json",{"records":records,"human_gold":False,"rankings_blinded":True})
    cmd=[sys.executable,str(ROOT/"scripts/validation20_compare.py"),str(pred_path),str(out/"labels_new20.json"),str(out/"validated_metrics.json")]
    subprocess.run(cmd,check=True)
    metrics=load(out/"validated_metrics.json")
    status["state"]="NEW20_VALIDATION_SCORED"
    status["evaluable_question_count"]=metrics["evaluable_query_count"]
    status["model_metrics"]=metrics["model"]
    status["question_deltas_vs_E"]=metrics["paired_differences_vs_E"]
    status["predictions_sha256"]=sha(pred_path)
    status["blind_labels_sha256"]=sha(out/"labels_new20.json")
    status["score_sha256"]=sha(out/"validated_metrics.json")
    write(out/"assembly_status.json",status)
    print(json.dumps(status,ensure_ascii=False,indent=2))
if __name__=="__main__":
    if len(sys.argv)!=4:raise SystemExit("validation20_aggregate.py PREDICTIONS BLIND_RESULTS_FOLDER OUTPUT_DIR")
    main(Path(sys.argv[1]),Path(sys.argv[2]),Path(sys.argv[3]))
