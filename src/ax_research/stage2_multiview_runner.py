"""Stage 2-1 runner.

Stage 1 MP-Dense에서 실제 생성된 Perspective branch query를 그대로 replay하여
LLM sampling을 통제하고 Multi-view case representation의 효과만 측정합니다.
"""

from __future__ import annotations

import csv
from collections import OrderedDict
from dataclasses import asdict
from itertools import combinations
from pathlib import Path
from typing import Sequence

from .config import RQ1Config
from .data import AXCase, GoldRecord, RelevanceLabel, index_by
from .evaluation import build_perspective_gold, evaluate_at_k, gold_delta_at_k
from .retrieval.multiview_dense import MultiViewDenseRetriever
from .selection import branch_balanced_unique


def _read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def load_replayed_branches(
    path: str | Path,
) -> dict[tuple[str, int], list[dict[str, str]]]:
    """Stage 1 branch ranking에서 branch 정의를 한 번씩만 추출합니다."""

    grouped: dict[tuple[str, int], list[dict[str, str]]] = {}
    seen: set[tuple[str, int, str]] = set()

    for row in _read_csv(path):
        query_id = row["query_id"]
        run_id = int(row["run_id"])
        perspective_id = row["perspective_id"]
        branch_key = (query_id, run_id, perspective_id)
        if branch_key in seen:
            continue
        seen.add(branch_key)

        key = (query_id, run_id)
        grouped.setdefault(key, []).append(
            {
                "perspective_id": perspective_id,
                "perspective_title": row["perspective_title"],
                "perspective_description": row["perspective_description"],
                "branch_query_text": row["branch_query_text"],
            }
        )

    return grouped


def _jaccard(left: Sequence[str], right: Sequence[str]) -> float:
    a, b = set(left), set(right)
    union = a | b
    return 1.0 if not union else len(a & b) / len(union)


def _duplicate_candidate_rate(
    branch_rankings: dict[str, list[str]], local_k: int
) -> float:
    flattened = [
        case_id
        for ranking in branch_rankings.values()
        for case_id in ranking[:local_k]
    ]
    if not flattened:
        return 0.0
    return 1.0 - len(set(flattened)) / len(flattened)


def run_stage2_multiview_replay(
    *,
    experiment_id: str,
    retriever: MultiViewDenseRetriever,
    rq1_config: RQ1Config,
    cases: Sequence[AXCase],
    labels: Sequence[RelevanceLabel],
    gold_records: Sequence[GoldRecord],
    stage1_branch_csv: str | Path,
    output_dir: str | Path,
    system_name: str = "stage2_multiview_equal_dense",
) -> tuple[Path, Path, Path]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    replay = load_replayed_branches(stage1_branch_csv)
    gold_index = index_by(gold_records, "query_id")
    case_index = index_by(cases, "case_id")
    max_k = max(rq1_config.evaluation_k)

    branch_rows: list[dict[str, object]] = []
    final_rows: list[dict[str, object]] = []
    metric_rows: list[dict[str, object]] = []

    for query_id in rq1_config.query_ids:
        gold = gold_index[query_id]
        perspective_gold = build_perspective_gold(
            labels,
            query_id=query_id,
            threshold=rq1_config.gold_threshold,
        )

        for run_id in range(1, rq1_config.llm_repeats + 1):
            key = (query_id, run_id)
            if key not in replay:
                raise KeyError(f"Missing Stage 1 replay branches for {key}")

            branch_rankings: OrderedDict[str, list[str]] = OrderedDict()

            for branch in replay[key]:
                pid = branch["perspective_id"]
                query_text = branch["branch_query_text"]
                ranked = retriever.search(query_text, top_k=None)
                branch_rankings[pid] = [item.case_id for item in ranked]

                for local_rank, item in enumerate(ranked, start=1):
                    branch_rows.append(
                        {
                            "experiment_id": experiment_id,
                            "system": system_name,
                            "run_id": run_id,
                            "query_id": query_id,
                            "perspective_id": pid,
                            "perspective_title": branch["perspective_title"],
                            "perspective_description": branch[
                                "perspective_description"
                            ],
                            "branch_query_text": query_text,
                            "local_rank": local_rank,
                            "case_id": item.case_id,
                            "score": item.score,
                            "problem_score": item.problem_score,
                            "task_score": item.task_score,
                            "context_score": item.context_score,
                        }
                    )

            selected = branch_balanced_unique(branch_rankings, k=max_k)
            final_ids = [case_id for _, case_id in selected]

            for final_rank, (source_branch, case_id) in enumerate(
                selected, start=1
            ):
                final_rows.append(
                    {
                        "experiment_id": experiment_id,
                        "system": system_name,
                        "run_id": run_id,
                        "query_id": query_id,
                        "final_rank": final_rank,
                        "source_perspective_id": source_branch,
                        "case_id": case_id,
                    }
                )

            local_sets = {
                pid: ids[:max_k] for pid, ids in branch_rankings.items()
            }
            pair_scores = [
                _jaccard(local_sets[a], local_sets[b])
                for a, b in combinations(local_sets, 2)
            ]
            mean_jaccard = (
                sum(pair_scores) / len(pair_scores) if pair_scores else 1.0
            )
            duplicate_rate = _duplicate_candidate_rate(
                branch_rankings, local_k=max_k
            )

            for k in rq1_config.evaluation_k:
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
                        "experiment_id": experiment_id,
                        "system": system_name,
                        "run_id": run_id,
                        "query_id": query_id,
                        **asdict(metrics),
                        "generated_perspective_count": len(replay[key]),
                        "mean_branch_jaccard_at_max_k": mean_jaccard,
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


def compare_mp_gold_delta(
    *,
    stage1_final_csv: str | Path,
    stage2_final_csv: str | Path,
    gold_records: Sequence[GoldRecord],
    k_values: Sequence[int],
    output_csv: str | Path,
) -> Path:
    """동일 Query×Run끼리 Stage 1 MP-Dense와 Stage 2-1을 비교합니다."""

    def load(path: str | Path) -> dict[tuple[str, int], list[str]]:
        grouped: dict[tuple[str, int], list[tuple[int, str]]] = {}
        for row in _read_csv(path):
            key = (row["query_id"], int(row["run_id"]))
            grouped.setdefault(key, []).append(
                (int(row["final_rank"]), row["case_id"])
            )
        return {
            key: [case_id for _, case_id in sorted(items)]
            for key, items in grouped.items()
        }

    baseline = load(stage1_final_csv)
    proposed = load(stage2_final_csv)
    gold_index = index_by(gold_records, "query_id")

    rows: list[dict[str, object]] = []
    for key, proposed_ids in sorted(proposed.items()):
        if key not in baseline:
            raise KeyError(f"Missing Stage 1 final ranking for {key}")
        query_id, run_id = key
        gold = gold_index[query_id]

        for k in k_values:
            delta = gold_delta_at_k(
                baseline[key],
                proposed_ids,
                gold.gold_relevant_cases,
                k,
            )
            rows.append(
                {
                    "query_id": query_id,
                    "run_id": run_id,
                    "k": k,
                    "gained_gold_count": len(delta.gained),
                    "lost_gold_count": len(delta.lost),
                    "net_gold_change": delta.net,
                    "gained_gold_cases": "|".join(sorted(delta.gained)),
                    "lost_gold_cases": "|".join(sorted(delta.lost)),
                }
            )

    output = Path(output_csv)
    output.parent.mkdir(parents=True, exist_ok=True)
    _write_csv(output, rows)
    return output


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError(f"No rows to write: {path}")
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
