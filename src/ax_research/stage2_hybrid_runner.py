"""Stage 2-3 Dense + Sparse Candidate Union experiment.

이 단계는 최종 순위를 만들기보다 Candidate Pool의 회수율을 검증합니다.
Stage 2-1 Multi-view Equal Dense branch ranking을 재사용하고 같은 Perspective
query로 Kiwi BM25를 실행한 뒤, 동일 retrieval slot budget의 Dense-only와
Query-level candidate recall을 비교합니다.
"""

from __future__ import annotations

import csv
from collections import OrderedDict
from pathlib import Path
from typing import Mapping, Protocol, Sequence

from .data import AXCase, GoldRecord, RelevanceLabel, index_by
from .evaluation import build_perspective_gold


class SearchResult(Protocol):
    case_id: str
    score: float


class Retriever(Protocol):
    def search(self, query: str, top_k: int | None = None) -> Sequence[SearchResult]: ...


def _read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError(f"No rows to write: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def load_dense_branch_rankings(
    path: str | Path,
) -> OrderedDict[tuple[str, int, str], dict[str, object]]:
    grouped: OrderedDict[tuple[str, int, str], list[dict[str, str]]] = OrderedDict()
    for row in _read_csv(path):
        key = (row["query_id"], int(row["run_id"]), row["perspective_id"])
        grouped.setdefault(key, []).append(row)

    result: OrderedDict[tuple[str, int, str], dict[str, object]] = OrderedDict()
    for key, rows in grouped.items():
        ordered = sorted(rows, key=lambda row: int(row["local_rank"]))
        first = ordered[0]
        result[key] = {
            "query_id": key[0],
            "run_id": key[1],
            "perspective_id": key[2],
            "perspective_title": first["perspective_title"],
            "perspective_description": first["perspective_description"],
            "branch_query_text": first["branch_query_text"],
            "dense_ids": [row["case_id"] for row in ordered],
        }

    if not result:
        raise ValueError(f"No dense branch rankings found: {path}")
    return result


def candidate_recall(candidate_ids: set[str], gold_ids: set[str]) -> float:
    if not gold_ids:
        return 0.0
    return len(candidate_ids & gold_ids) / len(gold_ids)


def candidate_perspective_coverage(
    candidate_ids: set[str],
    perspective_gold: Mapping[str, set[str]],
) -> float:
    if not perspective_gold:
        return 0.0
    covered = sum(1 for gold_ids in perspective_gold.values() if candidate_ids & gold_ids)
    return covered / len(perspective_gold)


def candidate_strategy_coverage(
    candidate_ids: set[str],
    *,
    case_index: Mapping[str, AXCase],
    gold_strategies: set[str],
) -> float:
    if not gold_strategies:
        return 0.0
    retrieved: set[str] = set()
    for case_id in candidate_ids:
        case = case_index.get(case_id)
        if case is not None:
            retrieved.update(case.strategy)
    return len(retrieved & gold_strategies) / len(gold_strategies)


def run_stage2_hybrid_candidate_union(
    *,
    experiment_id: str,
    query_ids: Sequence[str],
    llm_repeats: int,
    leg_k_values: Sequence[int],
    dense_multiplier: int,
    sparse_retriever: Retriever,
    cases: Sequence[AXCase],
    labels: Sequence[RelevanceLabel],
    gold_records: Sequence[GoldRecord],
    dense_branch_csv: str | Path,
    gold_threshold: int,
    output_dir: str | Path,
) -> tuple[Path, Path]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    dense_branches = load_dense_branch_rankings(dense_branch_csv)
    gold_index = index_by(gold_records, "query_id")
    case_index = index_by(cases, "case_id")

    sparse_cache: dict[tuple[str, int, str], list[str]] = {}
    candidate_rows: list[dict[str, object]] = []
    metric_rows: list[dict[str, object]] = []

    max_sparse_k = max(leg_k_values)
    for key, branch in dense_branches.items():
        sparse_cache[key] = [
            item.case_id
            for item in sparse_retriever.search(
                str(branch["branch_query_text"]),
                top_k=max_sparse_k,
            )
        ]

    for query_id in query_ids:
        gold = gold_index[query_id]
        gold_ids = set(gold.gold_relevant_cases)
        gold_strategies = set(gold.gold_strategy_set)
        perspective_gold = build_perspective_gold(
            labels,
            query_id=query_id,
            threshold=gold_threshold,
        )

        for run_id in range(1, llm_repeats + 1):
            branch_keys = [
                key for key in dense_branches
                if key[0] == query_id and key[1] == run_id
            ]
            if not branch_keys:
                raise KeyError(f"Missing dense branches for {(query_id, run_id)}")

            for leg_k in leg_k_values:
                dense_same_depth = leg_k * dense_multiplier
                hybrid_candidates: set[str] = set()
                dense_same_slot_candidates: set[str] = set()
                gained_from_sparse: set[str] = set()
                overlap_counts: list[int] = []
                jaccards: list[float] = []

                for key in branch_keys:
                    branch = dense_branches[key]
                    dense_ids = list(branch["dense_ids"])
                    sparse_ids = sparse_cache[key]

                    dense_leg = dense_ids[:leg_k]
                    sparse_leg = sparse_ids[:leg_k]
                    dense_same = dense_ids[:dense_same_depth]

                    dense_set = set(dense_leg)
                    sparse_set = set(sparse_leg)
                    branch_union = dense_set | sparse_set

                    hybrid_candidates.update(branch_union)
                    dense_same_slot_candidates.update(dense_same)
                    gained_from_sparse.update(sparse_set - dense_set)

                    overlap = len(dense_set & sparse_set)
                    union_size = len(branch_union)
                    overlap_counts.append(overlap)
                    jaccards.append(overlap / union_size if union_size else 1.0)

                    dense_rank = {cid: rank for rank, cid in enumerate(dense_leg, start=1)}
                    sparse_rank = {cid: rank for rank, cid in enumerate(sparse_leg, start=1)}
                    for case_id in sorted(branch_union):
                        in_dense = case_id in dense_set
                        in_sparse = case_id in sparse_set
                        source = "both" if in_dense and in_sparse else ("dense" if in_dense else "sparse")
                        candidate_rows.append(
                            {
                                "experiment_id": experiment_id,
                                "query_id": query_id,
                                "run_id": run_id,
                                "perspective_id": branch["perspective_id"],
                                "leg_k": leg_k,
                                "case_id": case_id,
                                "source": source,
                                "dense_rank": dense_rank.get(case_id, ""),
                                "sparse_rank": sparse_rank.get(case_id, ""),
                                "is_gold": int(case_id in gold_ids),
                            }
                        )

                hybrid_hit = hybrid_candidates & gold_ids
                dense_hit = dense_same_slot_candidates & gold_ids
                gained_gold = hybrid_hit - dense_hit
                lost_gold = dense_hit - hybrid_hit

                metric_rows.append(
                    {
                        "experiment_id": experiment_id,
                        "query_id": query_id,
                        "run_id": run_id,
                        "leg_k": leg_k,
                        "retrieval_slots_per_branch": leg_k * 2,
                        "generated_perspective_count": len(branch_keys),
                        "hybrid_unique_candidate_count": len(hybrid_candidates),
                        "dense_same_slot_unique_candidate_count": len(dense_same_slot_candidates),
                        "hybrid_candidate_recall": candidate_recall(hybrid_candidates, gold_ids),
                        "dense_same_slot_candidate_recall": candidate_recall(
                            dense_same_slot_candidates, gold_ids
                        ),
                        "recall_delta": candidate_recall(hybrid_candidates, gold_ids)
                        - candidate_recall(dense_same_slot_candidates, gold_ids),
                        "hybrid_perspective_coverage": candidate_perspective_coverage(
                            hybrid_candidates, perspective_gold
                        ),
                        "dense_same_slot_perspective_coverage": candidate_perspective_coverage(
                            dense_same_slot_candidates, perspective_gold
                        ),
                        "hybrid_strategy_coverage": candidate_strategy_coverage(
                            hybrid_candidates,
                            case_index=case_index,
                            gold_strategies=gold_strategies,
                        ),
                        "dense_same_slot_strategy_coverage": candidate_strategy_coverage(
                            dense_same_slot_candidates,
                            case_index=case_index,
                            gold_strategies=gold_strategies,
                        ),
                        "gained_gold_count": len(gained_gold),
                        "lost_gold_count": len(lost_gold),
                        "net_gold_change": len(gained_gold) - len(lost_gold),
                        "gained_gold_cases": "|".join(sorted(gained_gold)),
                        "lost_gold_cases": "|".join(sorted(lost_gold)),
                        "sparse_unique_additions_before_cross_branch_dedup": len(
                            gained_from_sparse
                        ),
                        "mean_dense_sparse_overlap_per_branch": sum(overlap_counts)
                        / len(overlap_counts),
                        "mean_dense_sparse_jaccard_per_branch": sum(jaccards)
                        / len(jaccards),
                    }
                )

    candidates_path = output / "stage2_hybrid_candidate_provenance.csv"
    metrics_path = output / "stage2_hybrid_candidate_metrics.csv"
    _write_csv(candidates_path, candidate_rows)
    _write_csv(metrics_path, metric_rows)
    return candidates_path, metrics_path


def summarize_stage2_hybrid(
    metrics_csv: str | Path,
    output_csv: str | Path,
) -> Path:
    rows = _read_csv(metrics_csv)
    if not rows:
        raise ValueError("Hybrid metrics CSV is empty")

    output_rows: list[dict[str, object]] = []
    for leg_k in sorted({int(row["leg_k"]) for row in rows}):
        items = [row for row in rows if int(row["leg_k"]) == leg_k]

        def mean(column: str) -> float:
            values = [float(row[column]) for row in items]
            return sum(values) / len(values)

        output_rows.append(
            {
                "leg_k": leg_k,
                "retrieval_slots_per_branch": leg_k * 2,
                "row_count": len(items),
                "mean_hybrid_candidate_recall": mean("hybrid_candidate_recall"),
                "mean_dense_same_slot_candidate_recall": mean(
                    "dense_same_slot_candidate_recall"
                ),
                "mean_recall_delta": mean("recall_delta"),
                "mean_hybrid_unique_candidate_count": mean(
                    "hybrid_unique_candidate_count"
                ),
                "mean_dense_same_slot_unique_candidate_count": mean(
                    "dense_same_slot_unique_candidate_count"
                ),
                "total_gained_gold": sum(int(row["gained_gold_count"]) for row in items),
                "total_lost_gold": sum(int(row["lost_gold_count"]) for row in items),
                "total_net_gold_change": sum(int(row["net_gold_change"]) for row in items),
                "mean_dense_sparse_jaccard_per_branch": mean(
                    "mean_dense_sparse_jaccard_per_branch"
                ),
            }
        )

    output = Path(output_csv)
    _write_csv(output, output_rows)
    return output
