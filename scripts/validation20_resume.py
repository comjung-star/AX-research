"""Resume preserved 240 B/C/X/E responses; run frozen new20 inference without API replay.

Usage:
  PYTHONPATH=src:. python scripts/validation20_resume.py restore MODEL_PATH RUN_DIR
  PYTHONPATH=src:. python scripts/validation20_resume.py infer MODEL_PATH RUN_DIR

RUN_DIR must be under the repository for historical core pipeline provenance paths.
The generator's source API responses come only from GitHub Actions run 42382127226.
"""
import hashlib, json, sys
from pathlib import Path

from ax_research.heldout import read, write, jsonl
from scripts import core_preservation_run as core
from scripts import validation123_api as api

ROOT=Path(__file__).resolve().parents[1]
QUESTIONS=ROOT/"docs/validation-new20-20261107/questions.jsonl"
PREREG=ROOT/"docs/core-preserved-three-views-2026-11-07/preregistration.json"
FIRST_RUN=42382127226

def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()

def check(model,out):
    if not out.is_relative_to(ROOT):raise RuntimeError("Use a new temporary in-repo folder to preserve source path provenance")
    if not model.is_dir():raise RuntimeError("No BGE-M3 model found")
    if len(jsonl(QUESTIONS))!=20:raise RuntimeError("Unexpected new20 question count")
    for rel,want in read(PREREG)["environment"]["model"].items():
        path=model/rel
        if not path.is_file() or sha(path)!=want:raise RuntimeError("Frozen BGE-M3 mismatch: "+rel)
    if not (out/"generate_status.json").is_file():raise RuntimeError("Previous generation result not restored")
    if read(out/"generate_status.json")["requests"]!=240:raise RuntimeError("Unexpected generated request count")
    attempts=sorted((out/"api/attempts").glob("*.json"))
    results=sorted((out/"api/results").glob("*.json"))
    if len(attempts)!=240 or len(results)!=240:raise RuntimeError("Expected 240 sealed generation receipts and results")
    for rec in attempts:
        item=read(rec);result=out/"api/results"/rec.name
        if item["state"]!="RECEIVED" or not result.exists():raise RuntimeError("Missing original received generation "+rec.name)
        got=read(result)
        if got["valid"] is not True or got["request_sha256"]!=item["request_sha256"]:raise RuntimeError("Generation request/response mismatch "+rec.name)
    core.OUT=out;core.QUESTIONS=QUESTIONS;core.MODEL=model;core.configure()

def run(stage,model,out):
    check(model,out)
    if stage=="restore":
        target=out/"preregistration.json"
        if target.exists():raise RuntimeError("Existing local pre-registration: no overwrite")
        prior=read(PREREG)
        prior["protected_sha256"]["docs/validation-new20-20261107/questions.jsonl"]=sha(QUESTIONS)
        prior["original_preregistration_source"]="docs/core-preserved-three-views-2026-11-07/preregistration.json"
        prior["question_scope"]="Validation20; do not access prior independent Test"
        prior["question_count"]=20
        prior["source_generation_workflow"]=FIRST_RUN
        write(target,prior)
        write(out/"resume_recovery.json",{
            "source_workflow_run":FIRST_RUN,"generation_responses_recovered":240,
            "paid_replays":0,"question_count":20,
            "old_independent_Test_read":False,"checkpoint_sha256":sha(target),
            "api_generation_ledger":read(out/"api_ledger.json")["estimated_usd"]})
        print(json.dumps(read(out/"resume_recovery.json"),ensure_ascii=False),flush=True)
    elif stage=="infer":
        if not (out/"resume_recovery.json").is_file():raise RuntimeError("Recovery preflight not complete")
        # Historical heldout freeze() calls "git show BASE:path" for inputs
        # that did not exist at that older commit; use the already sealed
        # preregistration SHA256 manifest instead. No ranking/model code changes.
        import importlib.metadata, platform, subprocess
        from scripts import heldout_run as legacy_runner
        historical=read(PREREG)["environment"]
        # The prior study ran on Windows; GitHub checkout converts CRLF text
        # into LF. Accept only byte-identical text after verified newline
        # normalization, never arbitrary drift.
        def checked_path_digest(path, expected):
            if not path.is_file():return False
            data=path.read_bytes()
            lf=data.replace(b"\r\n",b"\n")
            candidates=[data,lf,lf.replace(b"\n",b"\r\n")]
            return any(hashlib.sha256(v).hexdigest()==expected for v in candidates)
        protected={}
        for name, expected in historical["protected"].items():
            src=ROOT/name
            if not checked_path_digest(src,expected):
                raise RuntimeError("Original protected source differs from frozen content (even after CRLF normalization): "+name)
            protected[name]=expected
        for name,expected in historical["model"].items():
            if sha(model/name)!=expected:
                raise RuntimeError("Original model checksum drift: "+name)
        packages={}
        for name,expected in historical["packages"].items():
            actual=importlib.metadata.version(name)
            if actual!=expected:
                raise RuntimeError("Pinned runtime mismatch for "+name+" expected="+expected+" actual="+actual)
            packages[name]=actual
        # Recheck all inputs both before and after the actual multiview inference.
        def verified_freeze(model_path):
            for name,expected in protected.items():
                if not checked_path_digest(ROOT/name,expected):raise RuntimeError("Protected drift during inference: "+name)
            for name,expected in historical["model"].items():
                if sha(Path(model_path)/name)!=expected:raise RuntimeError("BGE-M3 drift during inference: "+name)
            return {"base":"sha256_preregistration_manifest","protected":protected,
                "model":historical["model"],"packages":packages,
                "adapter":historical.get("adapter",{}),
                "commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),
                "python":platform.python_version(),"platform":platform.platform(),
                "command":sys.argv,"model_path":str(model_path),
                "policy":historical.get("policy")}
        legacy_runner.freeze=verified_freeze
        scratch=out.parent/"validation20-scratch"
        core.inference(scratch)
        p=read(out/"predictions.json")
        if len(p["case_ids"])!=112 or len(p["query_ids"])!=20 or any(len(p["systems"][s])!=(20 if s=="A" else 60) for s in ("A","C","E")):raise RuntimeError("New20 prediction cardinality mismatch")
        result={"case_ids":p["case_ids"],"query_ids":p["query_ids"],
                "systems":{s:[{"query_id":r["query_id"],"ranking":r["ranking"],
                           **({"repeat":r["repeat"]} if s!="A" else {})}
                        for r in p["systems"][s]] for s in ("A","C","E")}}
        write(out/"predictions_new20.json",result)
        write(out/"infer_status.json",{
            "status":"SUCCESS","case_count":112,"query_count":20,
            "condition_counts":{"A":20,"C":60,"E":60},
            "source_generation_reused":240,"new_generation_api_calls":0,
            "old_independent_Test_read":False,
            "ranking_sha256":sha(out/"predictions_new20.json"),
            "prediction_seal_sha256":sha(out/"prediction_seal.json")})
        print(json.dumps(read(out/"infer_status.json"),ensure_ascii=False),flush=True)
    else:raise RuntimeError("Unexpected stage")

if __name__=="__main__":
    if len(sys.argv)!=4:raise SystemExit("restore|infer MODEL_DIR IN_REPO_RUN_DIR")
    run(sys.argv[1],Path(sys.argv[2]).resolve(),Path(sys.argv[3]).resolve())
