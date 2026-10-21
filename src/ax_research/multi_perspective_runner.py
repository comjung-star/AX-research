"""Multi-Perspective Retrieval 공통 실행기.

RQ1 v1.2 Primary 규칙:
- LLM은 Original Business Problem만 보고 Perspective 2~5개를 생성합니다.
- 실제 BM25/Dense branch 검색에는 생성된 Perspective text만 사용합니다.
- Original Business Problem을 각 branch 검색문장에 다시 붙이지 않습니다.
- branch ranking을 점수로 합치지 않습니다.
- 최종 Top-K는 branch-balanced unique 방식으로 선택합니다.
"""

from __future__ import annotations

import csv
from dataclasses import asdict
from itertools import combinations
from pathlib import Path
from typing import Protocol, Sequence

from .config import RQ1Config
from .data import AXCase, GoldRecord, RelevanceLabel, RetrievalQuery, index_by
from .evaluation import build_perspective_gold, evaluate_at_k
from .llm.schemas import Perspective
from .selection import branch_balanced_unique


class SearchResult(Protocol):
    case_id: str
    score: float


class Retriever(Protocol):
    def search(
        self, query: str, top_k: int | None = None
    ) -> Sequence[SearchResult]: ...


class PerspectiveClient(Protocol):
    def generate_perspectives(
        self, business_problem: str
    ) -> list[Perspective]: ...


def build_branch_query(*, perspective: Perspective) -> str:
    """v1.2 규칙대로 Perspective 자체만 검색문장으로 만듭니다."""

    return f"{perspective.title}\n{perspective.description}"


def _jaccard(left: Sequence[str], right: Sequence[str]) -> float:
    a, b = set(left), set(right)
    union = a | b
    return 1.0 if not union else len(a & b) / len(union)


def _duplicate_candidate_rate(
    branch_rankings: dict[str, list[str]],
    local_k: int,
) -> float:
    """branch Top-N 전체 후보 중 중복이 차지하는 비율.

    예: 3개 branch × Top-20 = 60개 슬롯인데 unique case가 40개라면
    duplicate rate = 1 - 40/60 = 0.333...
    """

    flattened = [
        case_id
        for ranking in branch_rankings.values()
        for case_id in ranking[:local_k]
    ]
    if not flattened:
        return 0.0
    return 1.0 - (len(set(flattened)) / len(flattened))


def run_multi_perspective(
    *,
    system_name: str,
    client: PerspectiveClient,
    retriever: Retriever,
    config: RQ1Config,
    cases: Sequence[AXCase],
    queries: Sequence[RetrievalQuery],
    labels: Sequence[RelevanceLabel],
    gold_records: Sequence[GoldRecord],
    output_dir: str | Path,
) -> tuple[Path, Path, Path]:
    """Multi-Perspective를 Query별 3회 실행하고 결과/평가를 저장합니다."""

    if config.branch_query_mode != "perspective_only":
        raise ValueError(
            "RQ1 v1.2 Primary 실행은 perspective_only만 허용합니다."
        )

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    query_index = index_by(queries, "query_id")
    gold_index = index_by(gold_records, "query_id")
    case_index = index_by(cases, "case_id")
    max_k = max(config.evaluation_k)

    branch_rows: list[dict[str, object]] = []
    final_rows: list[dict[str, object]] = []
    metric_rows: list[dict[str, object]] = []

    for query_id in config.query_ids:
        query = query_index[query_id]
        gold = gold_index[query_id]
        perspective_gold = build_perspective_gold(
            labels,
            query_id=query_id,
            threshold=config.gold_threshold,
        )

        for run_index in range(1, config.llm_repeats + 1):
            perspectives = client.generate_perspectives(
                query.business_problem_query
            )

            branch_rankings: dict[str, list[str]] = {}

            for perspective in perspectives:
                branch_query = build_branch_query(
                    perspective=perspective,
                )
                ranked = list(retriever.search(branch_query, top_k=None))
                branch_rankings[perspective.id] = [
                    item.case_id for item in ranked
                ]

                for local_rank, item in enumerate(ranked, start=1):
                    branch_rows.append(
                        {
                            "experiment_id": config.experiment_id,
                            "system": system_name,
                            "run_id": run_index,
                            "query_id": query_id,
                            "llm_model": config.llm_model,
                            "temperature": config.temperature,
                            "branch_query_mode": config.branch_query_mode,
                            "perspective_id": perspective.id,
                            "perspective_title": perspective.title,
                            "perspective_description": perspective.description,
                            "branch_query_text": branch_query,
                            "local_rank": local_rank,
                            "case_id": item.case_id,
                            "score": item.score,
                        }
                    )

            selected = branch_balanced_unique(
                branch_rankings,
                k=max_k,
            )
            final_ids = [case_id for _, case_id in selected]

            for final_rank, (source_branch, case_id) in enumerate(
                selected, start=1
            ):
                final_rows.append(
                    {
                        "experiment_id": config.experiment_id,
                        "system": system_name,
                        "run_id": run_index,
                        "query_id": query_id,
                        "branch_query_mode": config.branch_query_mode,
                        "final_rank": final_rank,
                        "source_perspective_id": source_branch,
                        "case_id": case_id,
                    }
                )

            local_sets = {
                pid: ids[:max_k]
                for pid, ids in branch_rankings.items()
            }
            pair_scores = [
                _jaccard(local_sets[a], local_sets[b])
                for a, b in combinations(local_sets, 2)
            ]
            mean_branch_jaccard = (
                sum(pair_scores) / len(pair_scores)
                if pair_scores
                else 1.0
            )
            duplicate_rate = _duplicate_candidate_rate(
                branch_rankings,
                local_k=max_k,
            )

            for k in config.evaluation_k:
                metrics = evaluate_at_k(
                    ranked_case_ids=final_ids,
                    gold_case_ids=gold.gold_relevant_cases,
                    perspective_gold=perspective_gold,
                    case_index=case_index,
                    gold_strategies=gold.gold_strategy_set,
                    k=k,
                )
                metric_rows.append(
                    {
                        "experiment_id": config.experiment_id,
                        "system": system_name,
                        "run_id": run_index,
                        "query_id": query_id,
                        **asdict(metrics),
                        "generated_perspective_count": len(perspectives),
                        "mean_branch_jaccard_at_max_k": mean_branch_jaccard,
                        "duplicate_candidate_rate_at_max_k": duplicate_rate,
                    }
                )

    branch_path = output / f"{system_name}_branch_rankings.csv"
    final_path = output / f"{system_name}_final_rankings.csv"
    metrics_path = output / f"{system_name}_metrics.csv"

    _write_csv(branch_path, branch_rows)
    _write_csv(final_path, final_rows)
    _write_csv(metrics_path, metric_rows)

    return branch_path, final_path, metrics_path


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError(f"No rows to write: {path}")

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
