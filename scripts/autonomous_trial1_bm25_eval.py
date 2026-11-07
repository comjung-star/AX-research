"""Trial 1: reproduce frozen old BM25 before comparing new tokenizer.
Development-only. Never opens independent Test. No LLM or network calls.
"""
from __future__ import annotations
import hashlib
import json
import math
import os
from collections import defaultdict
from pathlib import Path

from kiwipiepy import Kiwi
from rank_bm25 import BM25Okapi

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "trial1_bm25_result.json"
CASES = ROOT / "docs/dense-bm25-candidates-2026-10-27/case_registry.json"
STATS = ROOT / "docs/dense-bm25-candidates-2026-10-27/bm25_corpus_statistics.json"
QUESTIONS = ROOT / "docs/validation-new20-20261107/questions.jsonl"
RANKS = ROOT / "docs/validation-new20-20261107/diagnosis/raw_search_stage_rankings.json"
LABELS = ROOT / "docs/ax-transfer-relevance-20261108/02_working_transfer_qrels_2240.json"
PUNCT = {"SF", "SP", "SS", "SSO", "SSC", "SE", "SO", "SW"}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def score_metrics(ranking, positive):
    if not positive:
        return None
    hits = len(set(ranking[:5]) & positive)
    precision = hits / 5
    recall = hits / len(positive)
    f1 = 2 * precision * recall / (precision + recall) if hits else 0.0
    ideal = sum(1 / math.log2(i + 2) for i in range(min(10, len(positive))))
    dcg = sum(1 / math.log2(i + 2) for i, cid in enumerate(ranking[:10]) if cid in positive)
    return {"F1_at_5": f1, "Recall_at_5": recall, "nDCG_at_10": dcg / ideal}


def main():
    if OUT.exists():
        raise RuntimeError("Do not overwrite prior trial result")
    cases = json.loads(CASES.read_text())["cases"]
    stats = json.loads(STATS.read_text())
    ranks = json.loads(RANKS.read_text())
    labels = json.loads(LABELS.read_text())["records"]
    questions = [json.loads(line) for line in QUESTIONS.read_text().splitlines() if line.strip()]
    ids = stats["case_order"]
    assert len(ids) == 112 and set(ids) == set(cases)
    assert len(questions) == 20 and len(labels) == 2240
    assert len({q["query_id"] for q in questions}) == 20
    kiwi = Kiwi()

    def tokens(text, old):
        return [x.form.strip().lower() for x in kiwi.tokenize(text)
                if x.form.strip() and (not x.tag.startswith("S") if old else x.tag not in PUNCT)]

    def case_text(c):
        return "[PROBLEM] " + c["problem"] + "\n[TASK] " + c["task"] + "\n[CONTEXT] " + c["context"]

    corpus_old = [tokens(case_text(cases[cid]), True) for cid in ids]
    old_lengths = {cid: len(v) for cid, v in zip(ids, corpus_old)}
    mismatches = {cid: [old_lengths[cid], stats["document_lengths_by_case"][cid]]
                  for cid in ids if old_lengths[cid] != stats["document_lengths_by_case"][cid]}
    if mismatches:
        result = {"state": "STOPPED_BASELINE_REPRODUCTION_FAILED", "mismatches": mismatches,
                  "input_sha256": {p.name: digest(p) for p in (CASES, STATS, QUESTIONS, RANKS, LABELS)},
                  "trial_count_increment": False, "paid_api_usd": 0}
        OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2))
        print(json.dumps({"state": result["state"], "mismatch_count": len(mismatches)}))
        return

    old_model = BM25Okapi(corpus_old, k1=stats["k1"], b=stats["b"], epsilon=stats["epsilon"])
    baseline = {row["query_id"]: row["ranking"] for row in ranks["systems"]["BM25"]}
    old_order = {}
    for q in questions:
        qid = q["query_id"]
        scores = old_model.get_scores(tokens(q["text"], True))
        old_order[qid] = sorted(ids, key=lambda cid: (-float(scores[ids.index(cid)]), cid))
    rank_mismatches = {qid: next((i + 1 for i, (a, b) in enumerate(zip(old_order[qid], baseline[qid])) if a != b), None)
                       for qid in old_order if old_order[qid] != baseline[qid]}
    if rank_mismatches:
        result = {"state": "STOPPED_OLD_RANK_REPRODUCTION_FAILED", "rank_mismatches": rank_mismatches,
                  "trial_count_increment": False, "paid_api_usd": 0}
        OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2))
        print(json.dumps(result))
        return

    corpus_new = [tokens(case_text(cases[cid]), False) for cid in ids]
    new_model = BM25Okapi(corpus_new, k1=stats["k1"], b=stats["b"], epsilon=stats["epsilon"])
    positive = defaultdict(set)
    for row in labels:
        if row["grade"] >= 2:
            positive[row["query_id"]].add(row["case_id"])
    dense = {row["query_id"]: row["ranking"] for row in ranks["systems"]["Dense"]}
    results = []
    for q in questions:
        qid = q["query_id"]
        new_scores = new_model.get_scores(tokens(q["text"], False))
        new_order = sorted(ids, key=lambda cid: (-float(new_scores[ids.index(cid)]), cid))
        dense_order = dense[qid]
        dr = {cid: i + 1 for i, cid in enumerate(dense_order)}
        br = {cid: i + 1 for i, cid in enumerate(new_order)}
        hybrid = sorted(ids, key=lambda cid: (-(1/(60+dr[cid])+1/(60+br[cid]))/2, cid))
        results.append({"query_id": qid, "positive_count": len(positive[qid]),
                        "old_BM25": score_metrics(old_order[qid], positive[qid]),
                        "new_BM25": score_metrics(new_order, positive[qid]),
                        "old_hybrid": score_metrics(
                            next(row["ranking"] for row in ranks["systems"]["Hybrid_RRF"] if row["query_id"] == qid), positive[qid]),
                        "new_hybrid": score_metrics(hybrid, positive[qid]),
                        "new_BM25_top20": new_order[:20], "new_hybrid_top20": hybrid[:20]})
    metrics = {}
    for system in ("old_BM25", "new_BM25", "old_hybrid", "new_hybrid"):
        valid = [row[system] for row in results if row[system] is not None]
        metrics[system] = {key: sum(row[key] for row in valid)/len(valid)
                           for key in ("F1_at_5", "Recall_at_5", "nDCG_at_10")}
    result = {"state": "DEVELOPMENT_DIAGNOSTIC_COMPLETE", "trial_count_increment": True,
              "source":"fixed 20 validation questions, 112 cases, provisional labels, not independent Test",
              "not_final_multiview_performance": True, "old_baseline_reproduced": True,
              "empty_old": sum(not row for row in corpus_old), "empty_new": sum(not row for row in corpus_new),
              "metrics": metrics, "per_query": results,
              "input_sha256": {p.name: digest(p) for p in (CASES, STATS, QUESTIONS, RANKS, LABELS)},
              "paid_api_usd": 0}
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2))
    print(json.dumps({"state": result["state"], "empty_old": result["empty_old"],
                      "empty_new": result["empty_new"], "metrics": metrics}))


if __name__ == "__main__":
    main()
