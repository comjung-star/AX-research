"""Run 20 genuine new-question original hybrid/functional/semantic rankings.
No API, no qrels, no independent Test. Requires original frozen BGE-M3 checkpoint.
python scripts/validation20_original_infer.py /tmp/bge-m3 /tmp/val20-original
"""
import hashlib
import json
import sys
from pathlib import Path
from ax_research.heldout import jsonl, read, write
from scripts.heldout_run import predict, ROOT

QUESTIONS = ROOT / "docs/validation-new20-20261107/questions.jsonl"
PREREG = ROOT / "docs/core-preserved-three-views-2026-11-07/preregistration.json"

def filehash(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as fp:
        for block in iter(lambda: fp.read(1024*1024), b""):
            h.update(block)
    return h.hexdigest()

def main():
    if len(sys.argv)!=3:
        raise SystemExit("Usage: validation20_original_infer.py model_dir output_dir")
    model=Path(sys.argv[1]).resolve()
    dest=Path(sys.argv[2]).resolve()
    if dest.exists():
        raise RuntimeError("Output directory already exists; never overwrite")
    expected=read(PREREG)["environment"]["model"]
    mismatches=[]
    for rel,digest in expected.items():
        f=model/rel
        if not f.is_file(): mismatches.append([rel,"missing"])
        elif filehash(f)!=digest: mismatches.append([rel,"SHA256 mismatch"])
    if mismatches:
        raise RuntimeError("Original frozen BGE-M3 checkpoint mismatch: "+repr(mismatches))
    qs=jsonl(QUESTIONS)
    if len(qs)!=20 or len({q["query_id"] for q in qs})!=20:
        raise RuntimeError("New validation question count or ID mismatch")
    if any(not q["query_id"].startswith("VQ") or q["split"]!="NEW_VALIDATION_20" for q in qs):
        raise RuntimeError("Unexpected question split")
    cases=read(ROOT/"docs/dense-bm25-candidates-2026-10-27/case_registry.json")["cases"]
    if len(cases)!=112:raise RuntimeError("Case count mismatch")
    dest.mkdir(parents=True)
    pred=predict(qs,model,dest)
    output={
      "case_ids":pred["case_ids"],"query_ids":pred["query_ids"],
      "systems":{"A":[{"query_id":row["query_id"],"ranking":row["ranking"]} for row in pred["systems"]["C"]]},
      "production_note":"The paper's original-query system A internally uses heldout predict's C1 combined_score.",
      "new_val20_only":True,"labels_read":False,"independent_test_read":False,
      "model_checkpoint_sha256":expected,"question_sha256":filehash(QUESTIONS)
    }
    write(dest/"fresh_original_A_20.json",output)
    write(dest/"status.json",{
      "state":"NEW20_ORIGINAL_SEARCH_COMPLETE","source_data_unchanged":True,
      "new_question_count":20,"case_count":112,"fresh_ranked_pairs":2240,
      "API_calls":0,"frozen_model_verified":True,"new_validation_only":True,
      "prediction_sha256":filehash(dest/"fresh_original_A_20.json")})
    print(json.dumps(read(dest/"status.json"),ensure_ascii=False,indent=2),flush=True)
if __name__=="__main__":main()
