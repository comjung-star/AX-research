"""New Validation 20 genuine C/E/A execution by the historical frozen pipeline.
API budget is enforced by scripts.validation123_api and capped at USD2 per run.
Infer uses the identical baseline modules and BGE-M3 SHA frozen in 2026-11-07.

Stages:
  python scripts/validation20_full_run.py generate MODEL_DIR OUTPUT_DIR
  python scripts/validation20_full_run.py infer MODEL_DIR OUTPUT_DIR
  python scripts/validation20_full_run.py judge MODEL_DIR OUTPUT_DIR
  python scripts/validation20_full_run.py evaluate MODEL_DIR OUTPUT_DIR
"""
import hashlib,json,os,sys
from pathlib import Path
from ax_research.heldout import read,write,jsonl
from scripts import core_preservation_run as core
from scripts import validation123_api as api

ROOT=Path(__file__).resolve().parents[1]
QUESTIONS=ROOT/"docs/validation-new20-20261107/questions.jsonl"
PREREG=ROOT/"docs/core-preserved-three-views-2026-11-07/preregistration.json"

def digest(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024*1024),b""):h.update(chunk)
    return h.hexdigest()

def run(stage,model,out):
    if not model.is_dir():raise RuntimeError("Model directory not found")
    if not QUESTIONS.is_file():raise RuntimeError("Frozen 20 questions missing")
    qs=jsonl(QUESTIONS)
    if len(qs)!=20 or len({q["query_id"] for q in qs})!=20 or any(q["split"]!="NEW_VALIDATION_20" for q in qs):
        raise RuntimeError("Frozen new20 validation query mismatch")
    checks=read(PREREG)["environment"]["model"]
    for rel,expected in checks.items():
        path=model/rel
        if not path.is_file() or digest(path)!=expected:raise RuntimeError("Original BGE-M3 hash mismatch: "+rel)
    core.OUT=out;core.QUESTIONS=QUESTIONS;core.MODEL=model
    core.configure()
    if stage=="generate":
        if out.exists():raise RuntimeError("Experiment outputs already present. No silent replay.")
        out.mkdir(parents=True)
        write(out/"run_policy.json",{"new_validation_20":True,"frozen_case_corpus":112,
              "question_sha256":digest(QUESTIONS),"model_files":checks,"never_read_test":True,
              "API_budget_estimate_limit_usd":2,"generation_conditions":["B","C","X","E"],
              "repetitions":3,"ranking_hidden_during_judgment":True})
        core.generate()
        write(out/"generate_status.json",{"state":"SUCCESS","requests":240,
               "ledger":read(out/"api_ledger.json"),"model_verified":True})
    elif stage=="infer":
        if not (out/"generate_status.json").is_file():raise RuntimeError("Generation not confirmed")
        scratch=out.parent/"validation20-scratch"
        core.inference(scratch)
        pred=read(out/"predictions.json")
        if len(pred["case_ids"])!=112 or len(pred["query_ids"])!=20 or any(len(pred["systems"][c])!=(20 if c=="A" else 60) for c in ("A","C","E")):
            raise RuntimeError("Unexpected predictions scope")
        newpred={"case_ids":pred["case_ids"],"query_ids":pred["query_ids"],
               "systems":{s:[{"query_id":r["query_id"],"ranking":r["ranking"],
                    **({"repeat":r["repeat"]} if s!="A" else {})}
                   for r in pred["systems"][s]] for s in ("A","C","E")}}
        write(out/"predictions_new20.json",newpred)
        write(out/"infer_status.json",{"state":"SUCCESS","new20_only":True,
              "predictions_sha256":digest(out/"predictions_new20.json"),
              "old_test_read":False,"new_question_count":20,"case_count":112})
    elif stage=="judge":
        if not (out/"infer_status.json").is_file():raise RuntimeError("Predictions not sealed")
        core.judge()
        records=read(out/"labels.json")["records"]
        if len(records)!=2240 or len({(r["query_id"],r["case_id"]) for r in records})!=2240:
            raise RuntimeError("2,240 blind relevance outcomes required; never infer missing")
        write(out/"judge_status.json",{"state":"SUCCESS","total_pairs":len(records),
               "judged":sum(r["status"]=="JUDGED" for r in records),
               "abstained":sum(r["status"]=="ABSTAIN" for r in records),
               "unjudged":sum(r["status"]=="UNJUDGED" for r in records),
               "label_source":"single OpenAI model blind AI-Silver, not human gold or independent provider",
               "rankings_hidden":True,"API_ledger":read(out/"api_ledger.json")})
    elif stage=="evaluate":
        if not (out/"judge_status.json").is_file():raise RuntimeError("Blind judgments missing")
        if any(row["status"]=="UNJUDGED" for row in read(out/"labels.json")["records"]):
            write(out/"evaluation_status.json",{"state":"FULL_METRICS_BLOCKED_BY_INCOMPLETE_LABELS",
               "reason":"Blind API omitted cases; cannot pretend all 2,240 were judged",
               "no_result_fabrication":True})
            return
        import subprocess
        subprocess.run([sys.executable,str(ROOT/"scripts/validation20_compare.py"),
             str(out/"predictions_new20.json"),str(out/"labels.json"),str(out/"validated_metrics.json")],check=True)
        write(out/"evaluation_status.json",{"state":"NEW20_METRICS_READY",
               "single_ai_label_source":True,"not_independent_final_test":True,
               "metrics_sha256":digest(out/"validated_metrics.json")})
    else:raise ValueError("Unknown stage")
    print(json.dumps({"stage":stage,"output":str(out),"success":True},ensure_ascii=False),flush=True)

if __name__=="__main__":
    if len(sys.argv)!=4:raise SystemExit("Usage: validation20_full_run.py generate|infer|judge|evaluate MODEL_DIR OUT")
    run(sys.argv[1],Path(sys.argv[2]).resolve(),Path(sys.argv[3]).resolve())
