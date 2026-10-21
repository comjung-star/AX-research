"""Multi-Perspective Retrieval 공통 실행기.

중요:
- LLM은 Business Problem만 보고 Perspective 2~5개를 생성합니다.
- 각 Perspective는 독립 branch로 검색합니다.
- branch ranking을 점수로 합치지 않습니다.
- 최종 Top-K는 branch-balanced unique 방식으로만 선택합니다.

현재 구현은 두 branch query 형식을 모두 지원합니다.
실제 Dev 실험을 실행하기 전에 어느 형식을 Primary로 쓸지 확정하면 됩니다.

1) perspective_only
   생성된 Perspective title + description만 검색
2) original_plus_perspective
   원 Business Problem + 생성 Perspective를 함께 검색
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


def build_branch_query(
    *,
    business_problem: str,
    perspective: Perspective,
    mode: str,
) -> str:
    """Perspective branch가 실제 Retriever에 넣을 검색문장을 만듭니다."""

    perspective_text = f"{perspective.title}\n{perspective.description}"

    if mode == "perspective_only":
        return perspective_text

    if mode == "original_plus_perspective":
        return (
            f"[ORIGINAL PROBLEM] {business_problem}\n"
            f"[PERSPECTIVE] {perspective_text}"
        )

    raise ValueError(
        "branch_query_mode must be 'perspective_only' or "
        "'original_plus_perspective'"
    )


def _jaccard(left: Sequence[str], right: Sequence[str]) -> float:
    a, b = set(left), set(right)
    union = a | b
    return 1.0 if not union else len(a & b) / len(union)


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
    branch_query_mode: str,
) -> tuple[Path, Path, Path]:
    """Multi-Perspective를 Query별 3회 실행하고 결과/평가를 저장합니다."""

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
                    business_problem=query.business_problem_query,
                    perspective=perspective,
                    mode=branch_query_mode,
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
                            "branch_query_mode": branch_query_mode,
                            "perspective_id": perspective.id,
                            "perspective_title": perspective.title,
                            "perspective_description": perspective.description,
                            "local_rank": local_rank,
                            "case_id": item.case_id,
                            "score": item.score,
                        }
                    )

            # max K까지 한 번 선택합니다.
            # branch-balanced selection은 prefix-consistent라
            # 이 결과의 앞 5/10/20개를 각각 @5/@10/@20으로 평가할 수 있습니다.
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
                        "branch_query_mode": branch_query_mode,
                        "final_rank": final_rank,
                        "source_perspective_id": source_branch,
                        "case_id": case_id,
                    }
                )

            # branch들이 실제로 다른 결과를 내는지 확인하기 위한 평균 Jaccard.
            local_sets = {
                pid: ids[:max_k] for pid, ids in branch_rankings.items()
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
                        "branch_query_mode": branch_query_mode,
                        **asdict(metrics),
                        "generated_perspective_count": len(perspectives),
                        "mean_branch_jaccard_at_max_k": mean_branch_jaccard,
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
