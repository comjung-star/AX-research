"""RQ1 Single-query baseline 실행기.

현재 지원:
- Single-query BM25
- Single-query Dense (BGE-M3)

실행 예:
    python -m ax_research.rq1_runner --system bm25
    python -m ax_research.rq1_runner --system dense

왜 공통 Runner를 쓰나?
---------------------
각 검색기가 자기 방식으로 평가값을 계산하면 비교가 불공정해질 수 있습니다.
그래서 검색결과만 각 retriever가 만들고,
Recall / Perspective Coverage / Strategy Coverage는 모두 동일 함수로 계산합니다.
"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any

from .config import load_rq1_config
from .data import (
    REPO_ROOT,
    load_cases,
    load_gold,
    load_queries,
    load_relevance_labels,
    relevant_cases_by_perspective,
)
from .evaluation import (
    perspective_coverage_at_k,
    recall_at_k,
    strategy_coverage_at_k,
)
from .retrieval import BM25Retriever, DenseRetriever


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    """dict row 목록을 CSV로 저장합니다."""

    if not rows:
        raise ValueError(f"No rows to write: {path}")

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _build_retriever(system: str, documents: dict[str, str], config: dict[str, Any]):
    """Frozen config에 맞는 검색기를 생성합니다."""

    if system == "bm25":
        return BM25Retriever(documents)

    if system == "dense":
        dense_config = config["systems"]["single_dense"]
        return DenseRetriever(
            documents,
            model_name=dense_config["model"],
            normalize_embeddings=dense_config["normalize_embeddings"],
        )

    raise ValueError(f"Unsupported system: {system}")


def run_single_query_baseline(
    system: str,
    output_dir: Path | None = None,
) -> Path:
    """10개 Dev Query에 Single-query baseline을 실행하고 결과를 저장합니다."""

    config = load_rq1_config()
    cases = load_cases()
    queries = load_queries()
    labels = load_relevance_labels()
    gold = load_gold()

    # 검색기는 Solution View를 볼 수 없습니다.
    documents = {
        case_id: case.problem_view_text()
        for case_id, case in cases.items()
    }

    retriever = _build_retriever(system, documents, config)

    k_values = list(config["evaluation"]["k"])
    max_k = max(k_values)
    threshold = int(config["evaluation"]["gold_relevance_threshold"])

    now = datetime.now(timezone.utc)
    experiment_id = config["experiment"]["id"]
    run_id = f"{system}_{now.strftime('%Y%m%dT%H%M%SZ')}"

    output_dir = output_dir or (
        REPO_ROOT / "experiments" / "rq1_retrieval" / "runs" / run_id
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    ranking_rows: list[dict[str, Any]] = []
    metric_rows: list[dict[str, Any]] = []

    for query_id in config["experiment"]["queries"]["ids"]:
        query = queries[query_id]

        # Primary RQ1은 Business Problem만 입력합니다.
        ranked = retriever.search(query.business_problem_query, top_k=max_k)
        ranked_ids = [item.case_id for item in ranked]

        for rank, item in enumerate(ranked, start=1):
            ranking_rows.append(
                {
                    "experiment_id": experiment_id,
                    "run_id": run_id,
                    "query_id": query_id,
                    "system": system,
                    "rank": rank,
                    "case_id": item.case_id,
                    "score": item.score,
                }
            )

        per_perspective = relevant_cases_by_perspective(
            labels,
            query_id=query_id,
            threshold=threshold,
        )
        query_gold = gold[query_id]

        for k in k_values:
            metric_rows.append(
                {
                    "experiment_id": experiment_id,
                    "run_id": run_id,
                    "query_id": query_id,
                    "system": system,
                    "k": k,
                    "recall": recall_at_k(
                        ranked_ids,
                        query_gold.gold_relevant_cases,
                        k,
                    ),
                    "perspective_coverage": perspective_coverage_at_k(
                        ranked_ids,
                        per_perspective,
                        k,
                    ),
                    "strategy_coverage": strategy_coverage_at_k(
                        ranked_ids,
                        cases,
                        query_gold.gold_strategy_set,
                        k,
                    ),
                }
            )

    _write_csv(output_dir / "rankings.csv", ranking_rows)
    _write_csv(output_dir / "metrics.csv", metric_rows)

    summary = {
        "experiment_id": experiment_id,
        "run_id": run_id,
        "system": system,
        "query_count": len(queries),
        "k": {},
    }

    for k in k_values:
        rows_at_k = [row for row in metric_rows if row["k"] == k]
        summary["k"][str(k)] = {
            "mean_recall": mean(row["recall"] for row in rows_at_k),
            "mean_perspective_coverage": mean(
                row["perspective_coverage"] for row in rows_at_k
            ),
            "mean_strategy_coverage": mean(
                row["strategy_coverage"] for row in rows_at_k
            ),
        }

    with (output_dir / "summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    return output_dir


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run RQ1 single-query retrieval baseline."
    )
    parser.add_argument(
        "--system",
        required=True,
        choices=("bm25", "dense"),
        help="실행할 baseline 검색기",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="결과 저장 위치. 생략하면 timestamp 기반 폴더를 사용합니다.",
    )
    args = parser.parse_args()

    result_dir = run_single_query_baseline(
        system=args.system,
        output_dir=args.output_dir,
    )
    print(f"RQ1 result saved to: {result_dir}")


if __name__ == "__main__":
    main()
