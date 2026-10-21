"""Post-baseline diagnostic metrics for RQ1.

These metrics DO NOT replace the frozen primary metrics.
They were added after baseline validation revealed a ceiling effect in ordinary
Perspective Coverage@K.

Why?
- Perspective Coverage counts a perspective as covered when ANY relevant case
  for that perspective is retrieved.
- When reference perspectives share Gold cases, even a single-query baseline can
  reach 1.0 very quickly.
- Therefore we keep the primary metric unchanged and add stricter diagnostics.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Iterable, Mapping, Sequence

from .data import RelevanceLabel


def build_exclusive_perspective_gold(
    labels: Iterable[RelevanceLabel],
    *,
    query_id: str,
    threshold: int = 3,
) -> dict[str, set[str]]:
    """Return Gold cases that belong to one reference perspective only.

    Example:
        P1 = {A, B}
        P2 = {B, C}
        P3 = {B, D}

    Exclusive sets:
        P1 = {A}
        P2 = {C}
        P3 = {D}

    Shared case B is intentionally excluded from this diagnostic.
    """

    per_perspective: dict[str, set[str]] = defaultdict(set)
    for label in labels:
        if label.query_id == query_id and label.relevance >= threshold:
            per_perspective[label.perspective_id].add(label.case_id)

    result: dict[str, set[str]] = {}
    pids = list(per_perspective)

    for pid in pids:
        others: set[str] = set()
        for other in pids:
            if other != pid:
                others.update(per_perspective[other])
        result[pid] = per_perspective[pid] - others

    return result


def exclusive_perspective_coverage_at_k(
    ranked_case_ids: Sequence[str],
    exclusive_gold: Mapping[str, set[str]],
    k: int,
) -> float | None:
    """Coverage using perspective-exclusive Gold only.

    Perspectives with no exclusive Gold are excluded from the denominator.
    If no perspective has exclusive Gold, return None instead of pretending the
    diagnostic is 0 or 1.
    """

    eligible = [cases for cases in exclusive_gold.values() if cases]
    if not eligible:
        return None

    retrieved = set(ranked_case_ids[:k])
    covered = sum(1 for cases in eligible if retrieved & cases)
    return covered / len(eligible)


def mean_perspective_recall_at_k(
    ranked_case_ids: Sequence[str],
    perspective_gold: Mapping[str, set[str]],
    k: int,
) -> float | None:
    """Average per-perspective recall, a non-binary view of perspective recovery."""

    if not perspective_gold:
        return None

    retrieved = set(ranked_case_ids[:k])
    recalls = [
        len(retrieved & cases) / len(cases)
        for cases in perspective_gold.values()
        if cases
    ]
    if not recalls:
        return None
    return sum(recalls) / len(recalls)
