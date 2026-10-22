"""Stage 2-3 Hybrid Retrieval Candidate Union CLI."""

from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from .config import load_rq1_config
from .data import load_cases, load_gold, load_relevance_labels
from .retrieval.bm25 import KiwiBM25Retriever
from .stage2_hybrid_runner import (
    run_stage2_hybrid_candidate_union,
    summarize_stage2_hybrid,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Stage 2-3 Hybrid Retrieval")
    parser.add_argument(
        "--config",
        default="configs/experiment_stage2_hybrid_v1.yaml",
    )
    parser.add_argument("--repo-root", default=".")
    parser.add_argument(
        "--output-dir",
        default="experiments/rq2_multiview/results/stage2_hybrid_v1",
    )
    args = parser.parse_args()

    root = Path(args.repo_root)
    with (root / args.config).open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    if config["experiment"]["status"] != "FROZEN_FOR_IMPLEMENTATION":
        raise ValueError("Stage 2-3 config must be frozen")
    if config["controls"]["rerun_llm"]:
        raise ValueError("Stage 2-3 must not rerun the LLM")
    if config["controls"]["use_stage2_gated_v1"]:
        raise ValueError("Stage 2-3 v1 must isolate Hybrid from failed Gate v1")

    rq1 = load_rq1_config(root / config["source"]["rq1_config"])
    cases = load_cases(root / "data/main_cases_v1.csv")
    labels = load_relevance_labels(
        root / "data/perspective_case_relevance_v0.1.csv"
    )
    gold = load_gold(root / "data/retrieval_gold_v0.1.csv")

    output = root / args.output_dir
    _, metrics_path = run_stage2_hybrid_candidate_union(
        experiment_id=config["experiment"]["id"],
        query_ids=rq1.query_ids,
        llm_repeats=rq1.llm_repeats,
        leg_k_values=[int(k) for k in config["candidate_union"]["leg_k"]],
        dense_multiplier=int(
            config["candidate_union"]["same_slot_dense_multiplier"]
        ),
        sparse_retriever=KiwiBM25Retriever(cases),
        cases=cases,
        labels=labels,
        gold_records=gold,
        dense_branch_csv=root
        / config["source"]["stage2_equal_branch_rankings"],
        gold_threshold=rq1.gold_threshold,
        output_dir=output,
    )
    summarize_stage2_hybrid(
        metrics_path,
        output / "stage2_hybrid_candidate_summary.csv",
    )


if __name__ == "__main__":
    main()
