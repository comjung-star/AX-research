#!/usr/bin/env python3
"""AX v2.1 case-corpus retrieval and evidence-trace smoke runner.

The CHAR_NGRAM backend is a dependency-free wiring diagnostic ONLY.
Optional production-aligned backends: 'bm25' (Kiwi) and 'bge-m3' dense.
This script does not create GT, fabricate perspectives, estimate causality or
claim model quality without independent relevance judgments.
"""
from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "data/v2_1/main_cases_v2_1.json"
QUERIES = ROOT / "data/v2_1/dev_query_candidates_v2_1.json"


def load_cases(path: Path = CORPUS) -> list[dict[str, Any]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    assert raw["dataset_release"] == "2.1.0"
    cases = raw["cases"]
    assert len(cases) == 91
    assert len({c["case_id"] for c in cases}) == 91
    assert all(c["corpus_status"] == "FROZEN_SOURCE_QA_ELIGIBLE" for c in cases)
    return cases


def problem_text(case: dict[str, Any]) -> str:
    """Strict Problem, Task, Context serialization; never leak solution."""
    return (
        f"[PROBLEM] {case['problem']}\n"
        f"[TASK] {case['task']}\n"
        f"[CONTEXT] {case['context']}"
    )


def char_ngrams(text: str) -> Counter[str]:
    chars = re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", text.lower())).strip()
    out: Counter[str] = Counter()
    for size in (2, 3):
        for i in range(max(0, len(chars) - size + 1)):
            x = chars[i:i+size]
            if x.strip():
                out[x] += 1
    return out


def char_tfidf_ranking(
    cases: list[dict[str, Any]], query: str
) -> list[tuple[str, float]]:
    corpus = {c["case_id"]: char_ngrams(problem_text(c)) for c in cases}
    df: Counter[str] = Counter()
    for doc in corpus.values():
        df.update(doc.keys())
    n = len(corpus)
    idf = {token: math.log((n + 1)/(freq + 1)) + 1 for token, freq in df.items()}

    def vector(doc: Counter[str]) -> dict[str, float]:
        return {k: (1 + math.log(v)) * idf[k] for k, v in doc.items() if k in idf}

    qv = vector(char_ngrams(query))
    qn = math.sqrt(sum(v*v for v in qv.values()))
    scores = []
    for case_id, doc in corpus.items():
        dv = vector(doc)
        dn = math.sqrt(sum(v*v for v in dv.values()))
        score = sum(v*dv.get(k, 0) for k, v in qv.items()) / max(1e-12, qn*dn)
        scores.append((case_id, score))
    return sorted(scores, key=lambda p: (-p[1], p[0]))


def retrieve(
    cases: list[dict[str, Any]], query: str, backend: str = "char_ngram"
) -> list[tuple[str, float]]:
    if backend == "char_ngram":
        return char_tfidf_ranking(cases, query)
    docs = {c["case_id"]: problem_text(c) for c in cases}
    if backend == "bm25":
        from ax_research.retrieval.bm25 import BM25Retriever
        ranks = BM25Retriever(docs).search(query)
    elif backend == "bge-m3":
        from ax_research.retrieval.dense import DenseRetriever
        ranks = DenseRetriever(docs, model_name="BAAI/bge-m3").search(query)
    else:
        raise ValueError(f"Unknown backend: {backend}")
    return [(r.case_id, r.score) for r in ranks]


def load_query(query_id: str) -> str:
    queries = json.loads(QUERIES.read_text(encoding="utf-8"))["queries"]
    for query in queries:
        if query["query_id"] == query_id:
            return query["business_problem_query"]
    raise ValueError(f"Unknown Dev query: {query_id}")


def branch_candidates(
    cases: list[dict[str, Any]],
    branches: list[dict[str, str]],
    *,
    backend: str = "char_ngram",
    k: int = 10,
) -> dict[str, Any]:
    """Keep each runtime branch's ranking, then union; NEVER RRF or gold input."""
    if not branches or k < 1:
        raise ValueError("At least one real query branch and positive k are required")
    ids = [str(x["id"]) for x in branches]
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate runtime branch IDs")
    lookup = {c["case_id"]: c for c in cases}
    seen: dict[str, dict[str, Any]] = {}
    branch_rankings: dict[str, list[dict[str, Any]]] = {}
    for branch in branches:
        qtext = branch["query"].strip()
        if not qtext:
            raise ValueError("Empty runtime query")
        ranked = retrieve(cases, qtext, backend=backend)
        entries = []
        for rank, (cid, score) in enumerate(ranked[:k], start=1):
            entries.append({"rank":rank,"case_id":cid,"score":score})
            if cid not in seen:
                seen[cid] = {"score":score,"branches":[]}
            else:
                seen[cid]["score"] = max(seen[cid]["score"], score)
            seen[cid]["branches"].append({"branch":branch["id"],"rank":rank,"score":score})
        branch_rankings[branch["id"]] = entries
    ranked_union = sorted(seen.items(), key=lambda r: (-r[1]["score"], r[0]))[:k]
    selected = []
    for rank, (cid, attrs) in enumerate(ranked_union, start=1):
        case = lookup[cid]
        mappings = [
            {"factor":pair["factor"], "strategy":pair["strategy"],
             "source_url":case["source_url"], "rationale":pair["rationale"]}
            for pair in case["direct_mappings"]
            if pair.get("kind") == "APPLICABILITY_NOT_CAUSAL"
        ]
        selected.append({
            "rank":rank, "case_id":cid, "organization":case["organization"],
            "problem":case["problem"],"task":case["task"],
            "source_url":case["source_url"],"sampling_group_id":case["sampling_group_id"],
            "branch_provenance":attrs["branches"],
            "factor_label":case["factor_label"],
            "strategy_label":case["strategy_label"],
            "verified_applicability_evidence":mappings,
            "no_factor_strategy_causality_claim":True,
        })
    return {"dataset_version":"2.1.0","backend":backend,
            "diagnostic_only":True,
            "no_ground_truth_or_accuracy_claim":True,
            "branch_rankings":branch_rankings,"candidate_union":selected}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend", choices=["char_ngram","bm25","bge-m3"],
                        default="char_ngram")
    parser.add_argument("--query-id", default="V21D001")
    parser.add_argument("--query-text")
    parser.add_argument("--runtime-perspectives-json",
                        help="JSON array of {id, query} produced at runtime, NOT gold")
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--output")
    args = parser.parse_args()
    cases = load_cases()
    if args.runtime_perspectives_json:
        branches = json.loads(Path(args.runtime_perspectives_json).read_text(encoding="utf-8"))
        if not isinstance(branches, list):
            raise ValueError("Runtime branches must be a JSON array")
    else:
        query = args.query_text or load_query(args.query_id)
        branches = [{"id":"P0_SINGLE_QUERY","query":query}]
    report = branch_candidates(cases, branches, backend=args.backend, k=args.top_k)
    report["query_id"] = args.query_id if not args.query_text else "CUSTOM_QUERY"
    raw = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        path=Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(raw,encoding="utf-8")
        print(f"Wrote {path}; {len(report['candidate_union'])} cases; no GT metric")
    else:
        print(raw)


if __name__ == "__main__":
    main()
