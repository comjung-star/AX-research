from ax_research.llm.schemas import Perspective
from ax_research.multi_perspective_runner import (
    _duplicate_candidate_rate,
    build_branch_query,
)


def test_branch_query_is_perspective_only():
    p = Perspective(
        id="P1",
        title="데이터 분산",
        description="시스템별 데이터 단절",
    )
    text = build_branch_query(perspective=p)
    assert text == "데이터 분산\n시스템별 데이터 단절"


def test_duplicate_candidate_rate():
    branches = {
        "P1": ["A", "B", "C"],
        "P2": ["A", "D", "E"],
        "P3": ["B", "F", "G"],
    }
    # 총 9개 슬롯, unique 7개 -> 중복비율 2/9
    assert _duplicate_candidate_rate(branches, 3) == 2 / 9
