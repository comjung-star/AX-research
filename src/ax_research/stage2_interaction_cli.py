"""Stage 2-4 Query-Case Interaction CLI."""

from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from .config import load_rq1_config
from .data import load_cases, load_gold, load_relevance_labels
from .stage2_interaction_runner import (
    run_stage2_interaction_loqo,
    summarize_stage2_interaction,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run Stage 2-4 Query-Case Interaction LOQO"
    )
    parser.add_argument(
        "--config",
        default="configs/experiment_stage2_interaction_v1.yaml",
    )
    parser.add_argument("--repo-root", default=".")
    parser.add_argument(
        "--output-dir",
        default="experiments/rq2_multiview/results/stage2_interaction_v1",
    )
    args = parser.parse_args()

    root = Path(args.repo_root)
    with (root / args.config).open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    if config["experiment"]["status"] != "FROZEN_FOR_IMPLEMENTATION":
        raise ValueError("Stage 2-4 config must be frozen")
    if config["training"]["validation"] != "leave_one_query_out":
        raise ValueError("Stage 2-4 requires leave_one_query_out")
    if config["controls"]["rerun_llm"]:
        raise ValueError("Stage 2-4 must not rerun the LLM")

    rq1 = load_rq1_config(root / config["source"]["rq1_config"])
    cases = load_cases(root / "data/main_cases_v1.csv")
    labels = load_relevance_labels(
        root / "data/perspective_case_relevance_v0.1.csv"
    )
    gold = load_gold(root / "data/retrieval_gold_v0.1.csv")

    source = config["source"]
    interaction = config["interaction"]
    training = config["training"]
    output = root / args.output_dir

    _, _, metrics_path, _ = run_stage2_interaction_loqo(
        experiment_id=config["experiment"]["id"],
        rq1_config=rq1,
        cases=cases,
        labels=labels,
        gold_records=gold,
        hybrid_candidate_csv=root / source["stage2_hybrid_candidates"],
        stage2_equal_branch_csv=root
        / "experiments/rq2_multiview/results/stage2_multiview_v1/"
        "stage2_multiview_equal_dense_branch_rankings.csv",
        leg_k_values=[int(v) for v in config["candidate_budgets"]["leg_k"]],
        model_name=interaction["encoder"],
        projection_dim=int(interaction["projection"]["dim"]),
        hidden_dim=int(interaction["mlp"]["hidden_dim"]),
        dropout=float(interaction["mlp"]["dropout"]),
        seed=int(training["seed"]),
        learning_rate=float(training["learning_rate"]),
        weight_decay=float(training["weight_decay"]),
        epochs=int(training["epochs"]),
        pairwise_scale=float(training["pairwise_scale"]),
        rrf_constant=int(config["baseline"]["rrf_constant"]),
        output_dir=output,
    )

    summarize_stage2_interaction(
        metrics_path,
        output / "stage2_interaction_summary.csv",
    )


if __name__ == "__main__":
    main()
