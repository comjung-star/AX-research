"""GPT-only baseline 실행기.

GPT-only는 별도의 검색기(BM25/Dense)를 사용하지 않고,
LLM이 100개 AX Case의 Problem View를 직접 읽어서 상위 Case를 고르는 비교군입니다.
명세대로 Query별 3회 독립 실행하며, 각 Run을 따로 평가합니다.
"""

from __future__ import annotations

import csv
from dataclasses import asdict
from pathlib import Path
from typing import Protocol, Sequence

from .config import RQ1Config
from .data import AXCase, GoldRecord, RelevanceLabel, RetrievalQuery, index_by
from .evaluation import build_perspective_gold, evaluate_at_k
from .llm.schemas import GPTOnlyResponse


class GPTOnlyClient(Protocol):
    def gpt_only_rank(
        self, business_problem: str, cases: Sequence[AXCase], *, top_n: int
    ) -> GPTOnlyResponse: ...


def run_gpt_only(
    *,
    client: GPTOnlyClient,
    config: RQ1Config,
    cases: Sequence[AXCase],
    queries: Sequence[RetrievalQuery],
    labels: Sequence[RelevanceLabel],
    gold_records: Sequence[GoldRecord],
    output_dir: str | Path,
) -> tuple[Path, Path]:
    """GPT-only를 Query별 repeats회 실행하고 각 Run의 결과를 모두 저장한다."""
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    query_index = index_by(queries, "query_id")
    gold_index = index_by(gold_records, "query_id")
    case_index = index_by(cases, "case_id")

    # 평가 최대 K가 20이므로 출력도 Top-20으로 통제합니다.
    # 단, LLM은 100개 Case의 Problem View 전체를 읽고 판단합니다.
    max_k = max(config.evaluation_k)

    ranking_rows: list[dict[str, object]] = []
    metric_rows: list[dict[str, object]] = []

    for query_id in config.query_ids:
        query = query_index[query_id]
        gold = gold_index[query_id]
        perspective_gold = build_perspective_gold(
            labels, query_id=query_id, threshold=config.gold_threshold
        )

        for run_index in range(1, config.llm_repeats + 1):
            response = client.gpt_only_rank(
                query.business_problem_query, cases, top_n=max_k
            )
            ranked_ids = [row.case_id for row in response.ranked_cases]

            for rank, row in enumerate(response.ranked_cases, start=1):
                ranking_rows.append({
                    "experiment_id": config.experiment_id,
                    "system": "gpt_only",
                    "run_id": run_index,
                    "query_id": query_id,
                    "rank": rank,
                    "case_id": row.case_id,
                    "reason": row.reason,
                })

            for k in config.evaluation_k:
                metrics = evaluate_at_k(
                    ranked_case_ids=ranked_ids,
                    gold_case_ids=gold.gold_relevant_cases,
                    perspective_gold=perspective_gold,
                    case_index=case_index,
                    gold_strategies=gold.gold_strategy_set,
                    k=k,
                )
                metric_rows.append({
                    "experiment_id": config.experiment_id,
                    "system": "gpt_only",
                    "run_id": run_index,
                    "query_id": query_id,
                    **asdict(metrics),
                })

    ranking_path = output / "gpt_only_rankings.csv"
    metrics_path = output / "gpt_only_metrics.csv"
    _write_csv(ranking_path, ranking_rows)
    _write_csv(metrics_path, metric_rows)
    return ranking_path, metrics_path


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError(f"No rows to write: {path}")
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
