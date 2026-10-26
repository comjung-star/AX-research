"""Gated DEV comparison using existing BGE-M3/mean-view/BM25 definitions."""
import hashlib
import json
import os
from pathlib import Path

import numpy as np

from ax_research.retrieval.bm25 import BM25Retriever
from ax_research.selection import branch_balanced_unique
from scripts import query_isolated_revalidation as run


K_VALUES = (5, 10, 20)
CANDIDATE_OUTPUT_BUDGET = 20


def point_metrics(ranking, relevant, k):
    if len(ranking[:k]) != k or len(set(ranking[:k])) != k:
        raise ValueError("Candidate budget or unique ranking mismatch")
    tp = len(set(ranking[:k]) & relevant)
    total = len(relevant)
    return {"k":k,"true_positives":tp,"precision_denominator":k,"recall_denominator":total,
            "precision":tp/k,"recall":tp/total if total else None,
            "f1":2*tp/(k+total) if total else None,"query_hit":int(tp>0) if total else None}


def aggregate(query_results):
    out = {}
    for k in K_VALUES:
        cells = [r["metrics"][str(k)] for r in query_results]
        out[str(k)] = {"query_count":len(cells)}
        for name in ("precision","recall","f1","query_hit"):
            defined = [c[name] for c in cells if c[name] is not None]
            out[str(k)]["macro_"+name] = sum(defined)/len(defined) if defined else None
            out[str(k)][name+"_query_denominator"] = len(defined)
        out[str(k)]["true_positives_sum"] = sum(c["true_positives"] for c in cells)
        out[str(k)]["precision_denominator_sum"] = sum(c["precision_denominator"] for c in cells)
        out[str(k)]["recall_denominator_sum"] = sum(c["recall_denominator"] for c in cells)
        out[str(k)]["zero_relevant_queries"] = sum(c["recall_denominator"] == 0 for c in cells)
    return out


def load_approved_labels():
    gate = run.api.read_json(run.OUTPUT / "silver_release.json")
    if gate.get("approved") is not True or gate.get("unresolved_pairs") != 0 or gate.get("human_gold") is not False:
        raise ValueError("Definitive Stage2 needs a released AI Silver with zero unresolved pairs")
    records = run.api.read_json(run.OUTPUT / "stage1_silver.json")["records"]
    if len(records) != 1120 or len({(r["query_id"],r["case_id"]) for r in records}) != 1120:
        raise ValueError("Incomplete or duplicate qrels")
    if any(type(r.get("relevant")) is not bool for r in records):
        raise ValueError("Unjudged/disputed cannot become zero")
    labels = {}
    for r in records:
        labels.setdefault(r["query_id"],set())
        if r["relevant"]:
            labels[r["query_id"]].add(r["case_id"])
    return labels


def ranked_ids(case_ids, scores):
    return [case_ids[i] for i in sorted(range(len(case_ids)),key=lambda i:(-float(scores[i]),case_ids[i]))]


def create_encoder():
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    import torch
    from sentence_transformers import SentenceTransformer
    torch.set_num_threads(4)
    path = run.ROOT.parent / "AX-prototype/.local/models/bge-m3"
    if not (path/"pytorch_model.bin").exists():
        raise ValueError("Required existing local BGE-M3 unavailable; no substitute")
    encoder = SentenceTransformer(str(path),device="cpu",local_files_only=True)
    encoder.max_seq_length = 4096
    if encoder.get_sentence_embedding_dimension() != 1024:
        raise ValueError("Full BGE-M3 1024 dimensions required")
    return encoder


def input_texts(cases):
    single = ["\n".join(f"[{f.upper()}] {c[f]}" for f in ("problem","task","context")) for c in cases]
    views = {f:[f"[{f.upper()}] {c[f]}" for c in cases] for f in ("problem","task","context")}
    return single, views


def encode(encoder,texts):
    lengths = [len(encoder.tokenizer.encode(t)) for t in texts]
    if any(n>4096 for n in lengths):
        raise ValueError("Unequal truncation would invalidate comparison")
    result = encoder.encode(texts,batch_size=8,normalize_embeddings=True,convert_to_numpy=True,show_progress_bar=False).astype(np.float32)
    if result.shape != (len(texts),1024) or not np.isfinite(result).all():
        raise ValueError("Invalid BGE embeddings")
    return result, lengths


def stage2():
    labels = load_approved_labels()  # Always gate before model/ranking work.
    cases = sorted(run.api.read_csv(run.DATA / "dev_problem_views.csv"),key=lambda r:r["case_id"])
    queries = run.api.read_json(run.DATA / "dev_queries.json")["queries"]
    case_ids = [r["case_id"] for r in cases]
    single, views = input_texts(cases)
    encoder = create_encoder()
    matrices, token_lengths = {}, {}
    for name,texts in {"single":single,**views}.items():
        matrices[name], token_lengths[name] = encode(encoder,texts)
    qvectors, token_lengths["queries"] = encode(encoder,[r["query"] for r in queries])
    bm25 = BM25Retriever(dict(zip(case_ids,single,strict=True)))
    systems = {"A_single_dense":[],"B_three_view_dense":[],"BM25_auxiliary":[]}
    for q,qvec in zip(queries,qvectors,strict=True):
        scores = {"A_single_dense":matrices["single"]@qvec,
                  "B_three_view_dense":sum(matrices[v]@qvec for v in views)/3}
        rankings = {name:ranked_ids(case_ids,s)[:20] for name,s in scores.items()}
        rankings["BM25_auxiliary"] = [r.case_id for r in bm25.search(q["query"],top_k=20)]
        for name,ranking in rankings.items():
            systems[name].append({"query_id":q["query_id"],"candidate_count":len(ranking),"ranking":ranking,
                                  "metrics":{str(k):point_metrics(ranking,labels[q["query_id"]],k) for k in K_VALUES}})
    np.savez_compressed(run.OUTPUT/"stage2_embeddings.npz",case_ids=np.array(case_ids),query_ids=np.array([q["query_id"] for q in queries]),queries=qvectors,**matrices)
    out = {"status":"DEV_STAGE2_COMPLETE_AI_SILVER_ONLY","systems":systems,"aggregate":{name:aggregate(rows) for name,rows in systems.items()},
           "settings":{"model":"BAAI/bge-m3","dimensions":1024,"pooling":"CLS","normalize":True,"max_tokens":4096,"view_weights":[1/3]*3,
                       "corpus_candidate_universe":112,"final_unique_candidate_budget":20,"ranking_tie_break":"case_id_ascending","new_search_algorithms":False,"input_fields":["problem","task","context"]},
           "token_lengths":token_lengths,"human_gold":False,"test_run":False}
    run.save(run.OUTPUT/"stage2_results.json",out)
    return out


if __name__ == "__main__":
    import argparse
    p=argparse.ArgumentParser();p.add_argument("phase",choices=["stage2"]);p.parse_args()
    result=stage2();print(json.dumps(result["aggregate"]))
