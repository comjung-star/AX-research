"""Stage 2-1 Multi-view Dense experiment CLI."""

from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from .config import load_rq1_config
from .data import load_cases, load_gold, load_relevance_labels
from .retrieval.multiview_dense import MultiViewDenseRetriever
from .stage2_multiview_runner import (
    compare_mp_gold_delta,
    run_stage2_multiview_replay,
)
from .summary import summarize_metrics


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run Stage 2-1 Multi-view Dense replay experiment"
    )
    parser.add_argument(
        "--config",
        default="configs/experiment_stage2_multiview_v1.yaml",
    )
    parser.add_argument("--repo-root", default=".")
    parser.add_argument(
        "--output-dir",
        default="experiments/rq2_multiview/results/stage2_multiview_v1",
    )
    args = parser.parse_args()

    root = Path(args.repo_root)
    with (root / args.config).open("r", encoding="utf-8") as f:
        stage2 = yaml.safe_load(f)

    if stage2["experiment"]["status"] != "FROZEN_FOR_IMPLEMENTATION":
        raise ValueError("Stage 2 config must be frozen")
    if stage2["multiview"]["fusion"]["method"] != "equal_mean":
        raise ValueError("Stage 2-1 requires equal_mean fusion")
    if not stage2["controls"]["replay_stage1_generated_perspectives"]:
        raise ValueError("Stage 2-1 must replay Stage 1 perspectives")
    if stage2["controls"]["rerun_llm"]:
        raise ValueError("Stage 2-1 must not rerun the LLM")

    source = stage2["source"]
    rq1 = load_rq1_config(root / source["rq1_config"])
    cases = load_cases(root / "data/main_cases_v1.csv")
    labels = load_relevance_labels(
        root / "data/perspective_case_relevance_v0.1.csv"
    )
    gold = load_gold(root / "data/retrieval_gold_v0.1.csv")

    weights = stage2["multiview"]["fusion"]["weights"]
    retriever = MultiViewDenseRetriever(
        cases,
        model_name=stage2["multiview"]["encoder"],
        normalize_embeddings=bool(
            stage2["multiview"]["normalize_embeddings"]
        ),
        weights=weights,
    )

    output = root / args.output_dir
    _, final_path, metrics_path = run_stage2_multiview_replay(
        experiment_id=stage2["experiment"]["id"],
        retriever=retriever,
        rq1_config=rq1,
        cases=cases,
        labels=labels,
        gold_records=gold,
        stage1_branch_csv=root / source[
            "stage1_mp_dense_branch_rankings"
        ],
        output_dir=output,
    )

    summarize_metrics(
        metrics_path,
        output / "stage2_multiview_equal_dense_summary.csv",
    )
    compare_mp_gold_delta(
        stage1_final_csv=root / source["stage1_mp_dense_final_rankings"],
        stage2_final_csv=final_path,
        gold_records=gold,
        k_values=rq1.evaluation_k,
        output_csv=output
        / "stage2_multiview_equal_dense_gold_delta_vs_stage1_mp_dense.csv",
    )


if __name__ == "__main__":
    main()
