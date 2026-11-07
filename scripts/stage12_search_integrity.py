"""Audit & repair preprocessing/retrieval using frozen NEW20 Validation, no API.
This script never edits original cases, old tokenizer, old qrels, or independent Test.
Usage: python scripts/stage12_search_integrity.py build OUTPUT_DIR
       python scripts/stage12_search_integrity.py score OUTPUT_DIR
"""
import hashlib, json, math, sys, statistics
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CASES=ROOT/"docs/dense-bm25-candidates-2026-10-27/case_registry.json"
OLD_BM=ROOT/"docs/dense-bm25-candidates-2026-10-27/bm25_corpus_statistics.json"
TRACE=ROOT/"docs/validation-new20-20261107/diagnosis/raw_search_stage_rankings.json"
PRED=ROOT/"docs/validation-new20-20261107/measured/predictions_new20.json"
QS=ROOT/"docs/validation-new20-20261107/questions.jsonl"
LABELS=ROOT/"docs/validation-new20-20261107/measured/labels_new20.json"
CODE=ROOT/"src/ax_research/retrieval/bm25.py"

def read(path):return json.loads(Path(path).read_text(encoding="utf-8-sig"))
def write(path,value):
    with Path(path).open("x",encoding="utf8") as f:json.dump(value,f,ensure_ascii=False,indent=2,allow_nan=False);f.write("\n")
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def score(rank,grades):
    positives=sum(v>=2 for v in grades.values())
    hits5=sum(grades[c]>=2 for c in rank[:5])
    gs=[grades[c] for c in rank[:10]]
    dcg=lambda a:sum((2**v-1)/math.log2(i+2) for i,v in enumerate(a))
    ideal=dcg(sorted(grades.values(),reverse=True)[:10])
    return {"P@5":hits5/5,"Recall@5":hits5/positives if positives else None,
       "F1@5":2*hits5/(5+positives) if positives else None,
       "nDCG@10":dcg(gs)/ideal if ideal else None}

def main(stage,dest):
    from kiwipiepy import Kiwi
    from rank_bm25 import BM25Okapi
    from ax_research.retrieval.bm25 import KiwiTokenizer
    from ax_research.retrieval.bm25_repaired import RepairedKiwiTokenizer
    if stage=="build":
        dest.mkdir(parents=True,exist_ok=False)
        cases=read(CASES)["cases"];q=[json.loads(x) for x in QS.read_text(encoding="utf8").splitlines() if x.strip()]
        trace=read(TRACE);pred=read(PRED);old=read(OLD_BM)
        ids=sorted(cases)
        if len(ids)!=112 or len(q)!=20 or ids!=trace["case_ids"] or ids!=pred["case_ids"] or len({x["query_id"] for x in q})!=20:
            raise ValueError("Frozen source cohort mismatch")
        if trace["provenance"]["Original_A_reproduced_exactly"] is not True:
            raise ValueError("Raw search trace is not independently reproducible")
        if any(not cases[c]["task"].strip() or not cases[c]["context"].strip() for c in ids):
            raise ValueError("Missing executed Task/Context evidence; quarantine")
        if any(len(row["ranking"])!=112 or len(set(row["ranking"]))!=112 for rows in trace["systems"].values() for row in rows):
            raise ValueError("Original search produced missing/duplicate case")
        if any(len(row["ranking"])!=112 or set(row["ranking"])!=set(ids) for rows in pred["systems"].values() for row in rows):
            raise ValueError("Multi-view system dropped/duplicated case")
        if any(len(pred["systems"][s])!=(20 if s=="A" else 60) for s in ("A","C","E")):
            raise ValueError("Expected A20/C60/E60 ranks")
        oldtok=KiwiTokenizer();newtok=RepairedKiwiTokenizer()
        et=newtok.tokenize("Detect equipment failure in 2026.")
        if not all(word in et for word in ("detect","equipment","failure","2026")):
            raise ValueError("Latin/number token-preservation regression")
        if "." in et:raise ValueError("Punctuation regression")
        korean=newtok.tokenize("설비 고장 위험 예측")
        if "설비" not in korean or "고장" not in korean:raise ValueError("Korean token regression")
        docs={c:"\n".join(f"[{k.upper()}] {cases[c][k]}" for k in ("problem","task","context")) for c in ids}
        oldtokens=[oldtok.tokenize(docs[c]) for c in ids]
        oldindex=BM25Okapi(oldtokens)
        if (oldindex.doc_len!=[old["document_lengths_by_case"][c] for c in ids] or
            oldindex.doc_freqs!=[old["document_frequencies_by_case"][c] for c in ids] or
            not math.isclose(oldindex.avgdl,old["average_document_length"],abs_tol=1e-10) or
            any(not math.isclose(v,old["idf"].get(k,float("nan")),rel_tol=1e-10,abs_tol=1e-9) for k,v in oldindex.idf.items())):
            raise RuntimeError("Legacy BM25 corpus cannot be reproduced: stop before measuring fix")
        tokens=[newtok.tokenize(docs[c]) for c in ids]
        if any(len(x)==0 for x in tokens):raise ValueError("Repaired BM25 still has empty case tokens")
        newindex=BM25Okapi(tokens)
        raw={s:{r["query_id"]:r["ranking"] for r in trace["systems"][s]} for s in trace["systems"]}
        w=60; data=[]; changed=0
        for query in q:
            qid=query["query_id"];qt=newtok.tokenize(query["text"])
            if not qt:raise ValueError("Empty query tokens")
            bm_scores=newindex.get_scores(qt)
            bm=sorted(ids,key=lambda c:(-float(bm_scores[ids.index(c)]),c))
            dense=raw["Dense"][qid]
            positionsD={c:i+1 for i,c in enumerate(dense)}
            positionsB={c:i+1 for i,c in enumerate(bm)}
            hr=sorted(ids,key=lambda c:(-.5/(w+positionsD[c])-.5/(w+positionsB[c]),c))
            previous=raw["BM25"][qid]
            changed+=bm!=previous
            data.append({"query_id":qid,"dense":dense,"legacy_BM25":previous,
                 "repaired_BM25":bm,"legacy_hybrid":raw["Hybrid_RRF"][qid],
                 "repaired_hybrid":hr,
                 "query_tokens":qt,
                 "english_document_positive_score_count":sum(float(bm_scores[i])>0 and
                       sum(ch.isascii() and ch.isalpha() for ch in cases[ids[i]]["task"])>10
                       for i in range(len(ids)))})
        info={"state":"PASSED","query_count":20,"case_count":112,
           "legacy_zero_length_count":sum(not v for v in oldtokens),
           "repaired_zero_length_count":sum(not v for v in tokens),
           "repaired_latin_token_included":True,"repaired_numeric_token_included":True,
           "legacy_stats_recomputed_exactly":True,"BM25_ranking_changed_queries":changed,
           "original_dense_unchanged":True,"original_A_exact_match":True,
           "original_C_E_not_modified":True,"queries_labels_unread_during_ranking":True,
           "frozen_inputs_sha256":{str(p.relative_to(ROOT)):sha(p) for p in (CASES,OLD_BM,TRACE,PRED,QS,CODE)},
           "repaired_tokenizer_sha256":sha(ROOT/"src/ax_research/retrieval/bm25_repaired.py"),
           "original_Test_read":False,"paid_API_calls":0,
           "observed_documents_with_english_task_but_empty_legacy_index":sum(
                len(oldtokens[i])==0 and sum(ch.isascii() and ch.isalpha() for ch in cases[ids[i]]["task"])>10
                for i in range(len(ids)))}
        write(dest/"stage1_preprocessing_audit.json",info)
        write(dest/"stage1_corrected_rankings.json",{"rows":data,"case_ids":ids,"labels_read":False,
            "original_predictions_unmodified":True,"scope":"diagnostic 20 Validation"})
        print(json.dumps(info,ensure_ascii=False,indent=2))
        return
    if stage=="score":
        if read(dest/"stage1_preprocessing_audit.json")["state"]!="PASSED":
            raise RuntimeError("Cannot score before integrity audit")
        preds=read(dest/"stage1_corrected_rankings.json")
        lab=read(LABELS)["records"]
        if len(lab)!=2240:raise ValueError("Labels changed")
        ids=set(preds["case_ids"]);qids={r["query_id"] for r in preds["rows"]}
        labels={}
        for x in lab:
            key=(x["query_id"],x["case_id"])
            if key in labels or x["case_id"] not in ids or x["query_id"] not in qids:
                raise RuntimeError("Duplicate/foreign grade")
            labels[key]=x["grade"] if x["status"]=="JUDGED" else None
        if len(labels)!=2240:raise RuntimeError("Incomplete 2240 pairs")
        metrics={s:[] for s in ("dense","legacy_BM25","repaired_BM25","legacy_hybrid","repaired_hybrid")}
        per=[]
        for row in preds["rows"]:
            q=row["query_id"];grades={c:labels[q,c] for c in ids}
            if any(g is None or type(g)!=int or not 0<=g<=3 for g in grades.values()):
                raise RuntimeError("Unjudged case; keep metrics undefined")
            rec={"query_id":q,"positive_count":sum(g>=2 for g in grades.values()),"systems":{}}
            for s in metrics:
                m=score(row[s],grades)
                rec["systems"][s]=m
                if m["F1@5"] is not None:metrics[s].append(m)
            per.append(rec)
        overview={s:{k:statistics.mean(r[k] for r in metrics[s]) for k in ("F1@5","nDCG@10","P@5","Recall@5")}
                  for s in metrics}
        v={"state":"PASSED","reference":"single-AI provisional labels only, NOT expert gold",
           "evaluable_questions":len(metrics["dense"]),"zero_positive_query_ids":[r["query_id"] for r in per if not r["positive_count"]],
           "summary":overview,"questions":per,
           "NOTE":"Comparison on already inspected Validation is diagnostic, not proof of independent improvement",
           "source_sha256":{name:sha(dest/name) for name in ("stage1_preprocessing_audit.json","stage1_corrected_rankings.json")}}
        write(dest/"stage1_corrected_diagnostic_metrics.json",v)
        print(json.dumps({k:v[k] for k in ("state","evaluable_questions","zero_positive_query_ids","summary")},ensure_ascii=False,indent=2))
        return
    raise SystemExit("Unknown stage")

if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("build|score OUTPUT_DIR")
    main(sys.argv[1],Path(sys.argv[2]))
