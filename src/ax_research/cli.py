"""RQ1 Stage 1 실행 CLI.

Primary v1.2 실행은 config에 Freeze된 조건을 그대로 사용합니다.

예시
----
Single BM25:
    python -m ax_research.cli bm25

Single Dense:
    python -m ax_research.cli dense

GPT-only:
    python -m ax_research.cli gpt-only

Multi-Perspective BM25:
    python -m ax_research.cli mp-bm25

Multi-Perspective Dense:
    python -m ax_research.cli mp-dense

LLM 시스템은 OPENAI_API_KEY 환경변수가 필요합니다.
API Key는 Git에 저장하지 않습니다.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from .config import load_rq1_config
from .data import load_cases, load_gold, load_queries, load_relevance_labels
from .gpt_only_runner import run_gpt_only
from .llm.client import RQ1OpenAIClient
from .multi_perspective_runner import run_multi_perspective
from .retrieval.bm25 import KiwiBM25Retriever
from .retrieval.dense import BGEM3DenseRetriever
from .runner import run_single_query_baseline


def _llm_client(config):
    """GPT-only와 Perspective Generator가 공유하는 동일 LLM client."""

    return RQ1OpenAIClient(
        model=config.llm_model,
        temperature=config.temperature,
        perspective_min=config.perspective_min,
        perspective_max=config.perspective_max,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run RQ1 Stage 1 experiment")
    parser.add_argument(
        "system",
        choices=["bm25", "dense", "gpt-only", "mp-bm25", "mp-dense"],
    )
    parser.add_argument(
        "--config",
        default="configs/experiment_rq1_v1.2.yaml",
        help="Frozen experiment config",
    )
    parser.add_argument("--repo-root", default=".")
    parser.add_argument(
        "--output-dir",
        default="experiments/rq1_retrieval/results",
    )
    args = parser.parse_args()

    root = Path(args.repo_root)
    config = load_rq1_config(root / args.config)

    cases = load_cases(root / "data/main_cases_v1.csv")
    queries = load_queries(root / "data/retrieval_queries_v0.1.csv")
    labels = load_relevance_labels(
        root / "data/perspective_case_relevance_v0.1.csv"
    )
    gold = load_gold(root / "data/retrieval_gold_v0.1.csv")
    output = root / args.output_dir

    if args.system == "bm25":
        run_single_query_baseline(
            system_name="single_bm25",
            retriever=KiwiBM25Retriever(cases),
            config=config,
            cases=cases,
            queries=queries,
            labels=labels,
            gold_records=gold,
            output_dir=output,
        )
        return

    if args.system == "dense":
        run_single_query_baseline(
            system_name="single_dense",
            retriever=BGEM3DenseRetriever(
                cases,
                model_name=config.dense_model,
                normalize_embeddings=config.normalize_embeddings,
            ),
            config=config,
            cases=cases,
            queries=queries,
            labels=labels,
            gold_records=gold,
            output_dir=output,
        )
        return

    client = _llm_client(config)

    if args.system == "gpt-only":
        run_gpt_only(
            client=client,
            config=config,
            cases=cases,
            queries=queries,
            labels=labels,
            gold_records=gold,
            output_dir=output,
        )
        return

    if args.system == "mp-bm25":
        retriever = KiwiBM25Retriever(cases)
        system_name = "multi_perspective_bm25"
    else:
        retriever = BGEM3DenseRetriever(
            cases,
            model_name=config.dense_model,
            normalize_embeddings=config.normalize_embeddings,
        )
        system_name = "multi_perspective_dense"

    run_multi_perspective(
        system_name=system_name,
        client=client,
        retriever=retriever,
        config=config,
        cases=cases,
        queries=queries,
        labels=labels,
        gold_records=gold,
        output_dir=output,
    )


if __name__ == "__main__":
    main()
