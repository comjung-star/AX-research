"""Single-query baseline을 공통 방식으로 실행하는 RQ1 Runner.

이 Runner는 검색 모델의 종류와 무관하게 다음 순서를 고정합니다.
1. Freeze된 Case / Query / Gold를 읽는다.
2. Query는 Business Problem만 검색기에 전달한다.
3. 검색 결과 ranking을 저장한다.
4. 동일한 evaluation.py로 @5/@10/@20을 계산한다.
5. ranking.csv와 metrics.csv를 기록한다.
"""

from __future__ import annotations

import csv
from dataclasses import asdict
from pathlib import Path
from typing import Protocol, Sequence

from .config import RQ1Config
from .data import AXCase, GoldRecord, RelevanceLabel, RetrievalQuery, index_by
from .evaluation import build_perspective_gold, evaluate_at_k


class SearchResult(Protocol):
    case_id: str
    score: float


class Retriever(Protocol):
    def search(self, query: str, top_k: int | None = None) -> Sequence[SearchResult]: ...


def run_single_query_baseline(
    *,
    system_name: str,
    retriever: Retriever,
    config: RQ1Config,
    cases: Sequence[AXCase],
    queries: Sequence[RetrievalQuery],
    labels: Sequence[RelevanceLabel],
    gold_records: Sequence[GoldRecord],
    output_dir: str | Path,
) -> tuple[Path, Path]:
    """하나의 Single-query baseline을 전체 Dev Query에 실행한다."""
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    query_index = index_by(queries, "query_id")
    gold_index = index_by(gold_records, "query_id")
    case_index = index_by(cases, "case_id")

    ranking_rows: list[dict[str, object]] = []
    metric_rows: list[dict[str, object]] = []

    for query_id in config.query_ids:
        query = query_index[query_id]
        gold = gold_index[query_id]

        # v1 명세에 따라 Goal/Context가 아니라 Business Problem만 입력합니다.
        ranked = list(retriever.search(query.business_problem_query, top_k=None))
        ranked_ids = [item.case_id for item in ranked]

        for rank, item in enumerate(ranked, start=1):
            ranking_rows.append({
                "experiment_id": config.experiment_id,
                "system": system_name,
                "query_id": query_id,
                "rank": rank,
                "case_id": item.case_id,
                "score": item.score,
            })

        perspective_gold = build_perspective_gold(
            labels, query_id=query_id, threshold=config.gold_threshold
        )

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
                "system": system_name,
                "query_id": query_id,
                **asdict(metrics),
            })

    ranking_path = output / f"{system_name}_rankings.csv"
    metrics_path = output / f"{system_name}_metrics.csv"
    _write_csv(ranking_path, ranking_rows)
    _write_csv(metrics_path, metric_rows)
    return ranking_path, metrics_path


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    """결과 CSV를 UTF-8로 저장한다."""
    if not rows:
        raise ValueError(f"No rows to write: {path}")
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
