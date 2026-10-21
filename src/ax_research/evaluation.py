"""RQ1 공통 평가 지표.

용어를 쉽게 연결하면:
- Recall@K: 정답 사례를 상위 K개 안에서 얼마나 찾았나?
- Perspective Coverage@K: 정답 관점을 상위 K개 결과가 얼마나 빠짐없이 커버했나?
- Strategy Coverage@K: 검색된 사례를 통해 Gold Strategy를 얼마나 커버했나?

모든 모델이 이 파일의 함수를 공통으로 사용해야 비교가 공정합니다.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence

from .data import AXCase, RelevanceLabel


@dataclass(frozen=True)
class MetricsAtK:
    k: int
    recall: float
    perspective_coverage: float
    strategy_coverage: float


def _top_k_unique(case_ids: Sequence[str], k: int) -> list[str]:
    """랭킹 순서를 유지하면서 중복을 제거해 상위 K개의 Case ID만 남긴다."""
    seen: set[str] = set()
    result: list[str] = []
    for case_id in case_ids:
        if case_id in seen:
            continue
        seen.add(case_id)
        result.append(case_id)
        if len(result) >= k:
            break
    return result


def recall_at_k(ranked_case_ids: Sequence[str], gold_case_ids: Iterable[str], k: int) -> float:
    gold = set(gold_case_ids)
    if not gold:
        return 0.0
    retrieved = set(_top_k_unique(ranked_case_ids, k))
    return len(retrieved & gold) / len(gold)


def build_perspective_gold(
    labels: Iterable[RelevanceLabel],
    *,
    query_id: str,
    threshold: int = 3,
) -> dict[str, set[str]]:
    """한 Query의 Reference Perspective별 Gold Case 집합을 만든다."""
    result: dict[str, set[str]] = defaultdict(set)
    for label in labels:
        if label.query_id == query_id and label.relevance >= threshold:
            result[label.perspective_id].add(label.case_id)
    return dict(result)


def perspective_coverage_at_k(
    ranked_case_ids: Sequence[str],
    perspective_gold: Mapping[str, set[str]],
    k: int,
) -> float:
    """Reference Perspective 중 Top-K에서 1개 이상 관련 Case가 잡힌 비율."""
    if not perspective_gold:
        return 0.0
    retrieved = set(_top_k_unique(ranked_case_ids, k))
    covered = sum(1 for gold_cases in perspective_gold.values() if retrieved & gold_cases)
    return covered / len(perspective_gold)


def strategy_coverage_at_k(
    ranked_case_ids: Sequence[str],
    case_index: Mapping[str, AXCase],
    gold_strategies: Iterable[str],
    k: int,
) -> float:
    """Top-K 사례가 가진 Strategy label union이 Gold Strategy를 얼마나 포함하는지 계산."""
    gold = set(gold_strategies)
    if not gold:
        return 0.0

    retrieved_strategies: set[str] = set()
    for case_id in _top_k_unique(ranked_case_ids, k):
        case = case_index.get(case_id)
        if case is not None:
            retrieved_strategies.update(case.strategy)

    return len(retrieved_strategies & gold) / len(gold)


def unique_gold_recovery(
    baseline_case_ids: Sequence[str],
    proposed_case_ids: Sequence[str],
    gold_case_ids: Iterable[str],
    k: int,
) -> set[str]:
    """Baseline이 놓쳤지만 Proposed가 새로 찾은 Gold Case를 반환."""
    gold = set(gold_case_ids)
    baseline_hit = set(_top_k_unique(baseline_case_ids, k)) & gold
    proposed_hit = set(_top_k_unique(proposed_case_ids, k)) & gold
    return proposed_hit - baseline_hit


def evaluate_at_k(
    *,
    ranked_case_ids: Sequence[str],
    gold_case_ids: Iterable[str],
    perspective_gold: Mapping[str, set[str]],
    case_index: Mapping[str, AXCase],
    gold_strategies: Iterable[str],
    k: int,
) -> MetricsAtK:
    """세 핵심 지표를 한 번에 계산하는 공통 진입점."""
    return MetricsAtK(
        k=k,
        recall=recall_at_k(ranked_case_ids, gold_case_ids, k),
        perspective_coverage=perspective_coverage_at_k(ranked_case_ids, perspective_gold, k),
        strategy_coverage=strategy_coverage_at_k(ranked_case_ids, case_index, gold_strategies, k),
    )
