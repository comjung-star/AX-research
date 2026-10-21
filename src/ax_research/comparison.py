"""Single-query baseline과 Multi-Perspective 결과 비교 진단.

핵심 지표(Recall/Coverage)는 각 Runner에서 계산하고,
이 모듈은 'Multi-Perspective가 무엇을 새로 찾고 무엇을 잃었는지'를 봅니다.

특히 Unique Gold Recovery만 보면 좋아 보일 수 있으므로
반드시 gained / lost / net을 함께 기록합니다.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path
from typing import Iterable, Sequence

from .data import GoldRecord, index_by
from .evaluation import gold_delta_at_k


def _read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _baseline_rankings(
    rows: Iterable[dict[str, str]],
) -> dict[str, list[str]]:
    """Single baseline CSV를 query_id -> ranking으로 변환."""

    by_query: dict[str, list[tuple[int, str]]] = defaultdict(list)
    for row in rows:
        by_query[row["query_id"]].append(
            (int(row["rank"]), row["case_id"])
        )
    return {
        qid: [case_id for _, case_id in sorted(items)]
        for qid, items in by_query.items()
    }


def _mp_rankings(
    rows: Iterable[dict[str, str]],
) -> dict[tuple[str, int], list[str]]:
    """MP final ranking CSV를 (query_id, run_id) -> ranking으로 변환."""

    grouped: dict[tuple[str, int], list[tuple[int, str]]] = defaultdict(list)
    for row in rows:
        key = (row["query_id"], int(row["run_id"]))
        grouped[key].append(
            (int(row["final_rank"]), row["case_id"])
        )
    return {
        key: [case_id for _, case_id in sorted(items)]
        for key, items in grouped.items()
    }


def compare_gold_recovery(
    *,
    baseline_ranking_csv: str | Path,
    multi_perspective_final_ranking_csv: str | Path,
    gold_records: Sequence[GoldRecord],
    k_values: Sequence[int],
    output_csv: str | Path,
) -> Path:
    """Baseline vs MP의 Gold gained/lost/net을 Query × Run × K로 저장."""

    baseline = _baseline_rankings(_read_csv(baseline_ranking_csv))
    proposed = _mp_rankings(
        _read_csv(multi_perspective_final_ranking_csv)
    )
    gold_index = index_by(gold_records, "query_id")

    rows: list[dict[str, object]] = []

    for (query_id, run_id), proposed_ids in sorted(proposed.items()):
        if query_id not in baseline:
            raise KeyError(f"Missing baseline ranking for {query_id}")

        gold = gold_index[query_id]
        for k in k_values:
            delta = gold_delta_at_k(
                baseline[query_id],
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
    if not rows:
        raise ValueError("No comparison rows generated")

    with output.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    return output
