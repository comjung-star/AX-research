"""Trace frozen 20-query source-stage ranks (Dense, BM25, Hybrid, Original A).
No model/label/API modifications. predict() is the actual original heldout pipeline.
Usage: python scripts/new20_stage_trace.py MODEL_DIR SCRATCH_DIR OUTPUT_JSON
"""
import hashlib
import json
import sys
from pathlib import Path

from ax_research.heldout import jsonl, read, write
from scripts.heldout_run import predict, ROOT

QUESTIONS=ROOT/"docs/validation-new20-20261107/questions.jsonl"
FROZEN=ROOT/"docs/core-preserved-three-views-2026-11-07/preregistration.json"
SEALED=ROOT/"docs/validation-new20-20261107/measured/predictions_new20.json"

def hashfile(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as fp:
        for b in iter(lambda:fp.read(8*1024*1024),b""):
            h.update(b)
    return h.hexdigest()

def main(model,scratch,out):
    if scratch.exists() or out.exists():
        raise RuntimeError("No overwrite of diagnostic data")
    manifest=read(FROZEN)["environment"]
    for relative,want in manifest["model"].items():
        candidate=model/relative
        if not candidate.is_file() or hashfile(candidate)!=want:
            raise RuntimeError("Frozen BGE-M3 model hash differs: "+relative)
    qs=jsonl(QUESTIONS)
    if len(qs)!=20 or len({q["query_id"] for q in qs})!=20:
        raise RuntimeError("Wrong query cohort")
    prior=read(SEALED)
    if {q["query_id"] for q in qs}!=set(prior["query_ids"]):
        raise RuntimeError("New20 question IDs do not match original ranking seal")
    scratch.mkdir(parents=True,exist_ok=False)
    original=predict(qs,model,scratch)
    if original["case_ids"]!=prior["case_ids"]:
        raise RuntimeError("Different 112-case registry")
    # Original A from core_preservation_run is the corrected C1 mapping,
    # not the initial heldout_run.predict() raw C0 combined score.
    from ax_research.functional_mapping import extract, compare
    from ax_research.action_aggregation import purpose_filter
    from ax_research.semantic_mapping import combined_score
    rules=read(ROOT/"configs/functional_mapping_20261028.json")
    cfg=read(ROOT/"configs/action_aggregation_20261102.json")
    cp=read(ROOT/"docs/query-case-functional-mapping-2026-10-28/stage2/case_profiles.json")
    filtered={c:{role:purpose_filter(p,cfg) for role,p in roles.items()} for c,roles in cp.items()}
    records=read(scratch/"evidence.json")["records"]
    source={(x["query_id"],x["case_id"]):x for x in records}
    frozen_a={row["query_id"]:row["ranking"] for row in prior["systems"]["A"]}
    calc_a={}
    for q in original["query_ids"]:
        qp=purpose_filter(extract(next(x["text"] for x in qs if x["query_id"]==q),rules),cfg)
        values={c:combined_score(compare(qp,filtered[c])["mapping_grade"],source[q,c]["semantic"]["score"])
                for c in original["case_ids"]}
        calc_a[q]=sorted(values,key=lambda c:(-values[c],-source[q,c]["retrieval_tie"],c))
    if frozen_a!=calc_a:
        detail={q:next((i+1 for i,(a,b) in enumerate(zip(frozen_a[q],calc_a[q])) if a!=b),None)
                for q in frozen_a if frozen_a[q]!=calc_a[q]}
        raise RuntimeError("Recomputed corrected C1 original A does not match historic sealed A: "+repr(detail))
    ev=read(scratch/"evidence.json")["records"]
    by={(row["query_id"],row["case_id"]):row for row in ev}
    ids=original["case_ids"]
    stage={s:[] for s in ("Dense","BM25","Hybrid_RRF","Original_C0","Original_A")}
    ties=[]
    for q in original["query_ids"]:
        D=sorted(ids,key=lambda c:(-by[q,c]["dense"],c))
        B=sorted(ids,key=lambda c:(-by[q,c]["bm25"],c))
        H=sorted(ids,key=lambda c:(-by[q,c]["retrieval_tie"],c))
        A=calc_a[q]
        C0=next(row["ranking"] for row in original["systems"]["C"] if row["query_id"]==q)
        for name,ranking in (("Dense",D),("BM25",B),("Hybrid_RRF",H),("Original_C0",C0),("Original_A",A)):
            stage[name].append({"query_id":q,"ranking":ranking})
        ties.append({"query_id":q,
            "hybrid_score_consistency_checked":all(
                abs(by[q,c]["retrieval_tie"] -
                    ((1/(60+D.index(c)+1)+1/(60+B.index(c)+1))/2))<1e-14
                for c in ids)})
    if not all(x["hybrid_score_consistency_checked"] for x in ties):
        raise RuntimeError("Hybrid ties do not match original Dense+BM25 RRF")
    data={"scope":"NEW20_VALIDATION_DIAGNOSTIC_ONLY","questions":original["query_ids"],
          "case_ids":ids,"systems":stage,
          "provenance":{"original_predict_module":"scripts/heldout_run.py",
             "query_sha256":hashfile(QUESTIONS),
             "source_sealed_prediction_sha256":hashfile(SEALED),
             "model_sha256":manifest["model"],
             "labels_opened_before_trace":False,
             "independent_Test_opened":False,
             "API_calls":0,
             "Original_A_reproduced_exactly":True},
          "hybrid_check":ties}
    out.parent.mkdir(parents=True,exist_ok=True)
    write(out,data)
    print(json.dumps({"source_stage_ranks":"COMPLETE","queries":20,"cases":112,
        "original_A_exact_match":True,"API_calls":0,
        "sha256":hashfile(out)},ensure_ascii=False),flush=True)
if __name__=="__main__":
    if len(sys.argv)!=4:raise SystemExit("Usage: new20_stage_trace.py MODEL SCRATCH OUT")
    main(Path(sys.argv[1]).resolve(),Path(sys.argv[2]).resolve(),Path(sys.argv[3]).resolve())
