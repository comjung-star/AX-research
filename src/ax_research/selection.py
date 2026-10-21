"""Multi-Perspective 결과에서 최종 K개를 고르는 규칙.

Freeze된 v1 규칙은 branch-balanced unique selection입니다.
관점을 합쳐 하나의 점수로 재정렬하지 않고, 각 Perspective branch를 순환하며
고유 Case를 하나씩 가져옵니다.
"""

from __future__ import annotations

from collections import OrderedDict
from typing import Mapping, Sequence


def branch_balanced_unique(
    branch_rankings: Mapping[str, Sequence[str]],
    k: int,
) -> list[tuple[str, str]]:
    """각 branch를 round-robin으로 순회하며 K개의 unique case를 선택.

    반환값은 (perspective_id, case_id) 쌍입니다.
    이렇게 branch identity를 함께 보존해야 이후 분석에서
    어느 관점이 이 사례를 가져왔는가를 추적할 수 있습니다.
    """
    if k <= 0:
        return []

    rankings = OrderedDict((pid, list(cases)) for pid, cases in branch_rankings.items())
    cursor = {pid: 0 for pid in rankings}
    selected: list[tuple[str, str]] = []
    selected_cases: set[str] = set()

    while len(selected) < k:
        added_this_round = False

        for perspective_id, cases in rankings.items():
            while cursor[perspective_id] < len(cases):
                case_id = cases[cursor[perspective_id]]
                cursor[perspective_id] += 1
                if case_id in selected_cases:
                    continue

                selected.append((perspective_id, case_id))
                selected_cases.add(case_id)
                added_this_round = True
                break

            if len(selected) >= k:
                break

        if not added_this_round:
            break

    return selected
