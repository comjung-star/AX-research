from ax_research.llm.schemas import Perspective
from ax_research.multi_perspective_runner import build_branch_query


def test_perspective_only_query_does_not_repeat_original_problem():
    p = Perspective(id="P1", title="데이터 분산", description="시스템별 데이터 단절")
    text = build_branch_query(
        business_problem="원문 업무문제",
        perspective=p,
        mode="perspective_only",
    )
    assert "원문 업무문제" not in text
    assert "데이터 분산" in text


def test_original_plus_perspective_keeps_both():
    p = Perspective(id="P1", title="데이터 분산", description="시스템별 데이터 단절")
    text = build_branch_query(
        business_problem="원문 업무문제",
        perspective=p,
        mode="original_plus_perspective",
    )
    assert "원문 업무문제" in text
    assert "데이터 분산" in text
