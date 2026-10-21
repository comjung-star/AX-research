from ax_research.data import AXCase
from ax_research.llm.prompts import gpt_only_user_prompt, perspective_user_prompt


def test_perspective_prompt_contains_only_business_problem():
    text = perspective_user_prompt("데이터가 분산되어 있다")
    assert "데이터가 분산되어 있다" in text
    assert "Goal" not in text
    assert "Context" not in text


def test_gpt_only_prompt_contains_problem_view_not_strategy():
    case = AXCase(
        case_id="AX0001",
        business_problem="문제",
        ax_target_task="업무",
        business_context="환경",
        strategy=("S1_SECRET_STRATEGY",),
    )
    text = gpt_only_user_prompt("질의", [case])
    assert "AX0001" in text
    assert "문제" in text and "업무" in text and "환경" in text
    assert "S1_SECRET_STRATEGY" not in text
