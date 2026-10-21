"""RQ1 Single-query baseline 실행용 CLI.

예시:
    PYTHONPATH=src python -m ax_research.cli bm25
    PYTHONPATH=src python -m ax_research.cli dense
"""

from __future__ import annotations

import argparse
from pathlib import Path

from .config import load_rq1_config
from .data import load_cases, load_gold, load_queries, load_relevance_labels
from .retrieval.bm25 import KiwiBM25Retriever
from .retrieval.dense import BGEM3DenseRetriever
from .runner import run_single_query_baseline


def main() -> None:
    parser = argparse.ArgumentParser(description="Run RQ1 single-query baseline")
    parser.add_argument("system", choices=["bm25", "dense"])
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--output-dir", default="experiments/rq1_retrieval/results")
    args = parser.parse_args()

    root = Path(args.repo_root)
    config = load_rq1_config(root / "configs/experiment_rq1_v1.yaml")
    cases = load_cases(root / "data/main_cases_v1.csv")
    queries = load_queries(root / "data/retrieval_queries_v0.1.csv")
    labels = load_relevance_labels(root / "data/perspective_case_relevance_v0.1.csv")
    gold = load_gold(root / "data/retrieval_gold_v0.1.csv")

    if args.system == "bm25":
        retriever = KiwiBM25Retriever(cases)
        system_name = "single_bm25"
    else:
        retriever = BGEM3DenseRetriever(cases, model_name=config.dense_model)
        system_name = "single_dense"

    ranking_path, metrics_path = run_single_query_baseline(
        system_name=system_name,
        retriever=retriever,
        config=config,
        cases=cases,
        queries=queries,
        labels=labels,
        gold_records=gold,
        output_dir=root / args.output_dir,
    )

    print(f"Ranking saved: {ranking_path}")
    print(f"Metrics saved: {metrics_path}")


if __name__ == "__main__":
    main()
