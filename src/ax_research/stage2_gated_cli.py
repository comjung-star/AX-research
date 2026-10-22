"""Stage 2-2 Query-Conditioned Gated Fusion CLI."""

from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from .config import load_rq1_config
from .data import load_cases, load_gold, load_relevance_labels
from .stage2_gated_runner import run_stage2_gated_loqo
from .stage2_multiview_runner import compare_mp_gold_delta
from .summary import summarize_metrics


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Stage 2-2 gated fusion LOQO")
    parser.add_argument("--config", default="configs/experiment_stage2_gated_v1.yaml")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--output-dir", default="experiments/rq2_multiview/results/stage2_gated_v1")
    args = parser.parse_args()

    root = Path(args.repo_root)
    with (root / args.config).open("r", encoding="utf-8") as f:
        stage2 = yaml.safe_load(f)

    if stage2["experiment"]["status"] != "FROZEN_FOR_IMPLEMENTATION":
        raise ValueError("Stage 2-2 config must be frozen")
    if stage2["gate"]["validation"] != "leave_one_query_out":
        raise ValueError("Stage 2-2 v1 requires leave_one_query_out")
    if stage2["controls"]["rerun_llm"]:
        raise ValueError("Stage 2-2 must not rerun the LLM")

    source = stage2["source"]
    training = stage2["training"]
    rq1 = load_rq1_config(root / source["rq1_config"])
    cases = load_cases(root / "data/main_cases_v1.csv")
    labels = load_relevance_labels(root / "data/perspective_case_relevance_v0.1.csv")
    gold = load_gold(root / "data/retrieval_gold_v0.1.csv")

    output = root / args.output_dir
    _, _, final_path, metrics_path = run_stage2_gated_loqo(
        experiment_id=stage2["experiment"]["id"],
        rq1_config=rq1,
        cases=cases,
        labels=labels,
        gold_records=gold,
        stage2_equal_branch_csv=root / source["stage2_equal_branch_rankings"],
        model_name=stage2["gate"]["encoder"],
        anchors=stage2["gate"]["anchors"],
        seed=int(training["seed"]),
        learning_rate=float(training["learning_rate"]),
        weight_decay=float(training["weight_decay"]),
        epochs=int(training["epochs"]),
        pairwise_scale=float(training["pairwise_scale"]),
        output_dir=output,
    )

    summarize_metrics(metrics_path, output / "stage2_query_conditioned_gated_dense_summary.csv")
    compare_mp_gold_delta(
        stage1_final_csv=root / source["stage2_equal_final_rankings"],
        stage2_final_csv=final_path,
        gold_records=gold,
        k_values=rq1.evaluation_k,
        output_csv=output / "stage2_gated_gold_delta_vs_stage2_equal.csv",
    )
    compare_mp_gold_delta(
        stage1_final_csv=root / source["stage1_mp_dense_final_rankings"],
        stage2_final_csv=final_path,
        gold_records=gold,
        k_values=rq1.evaluation_k,
        output_csv=output / "stage2_gated_gold_delta_vs_stage1_mp_dense.csv",
    )


if __name__ == "__main__":
    main()
