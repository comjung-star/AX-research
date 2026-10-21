"""RQ1 LLM Prompt 모음.

Prompt를 코드 여기저기에 흩어놓지 않는 이유는 논문 재현성 때문입니다.
실험 시 이 파일 내용의 hash를 함께 저장하면 어떤 Prompt로 실행했는지 추적할 수 있습니다.
"""

from __future__ import annotations

from ..data import AXCase


PERSPECTIVE_SYSTEM_PROMPT = """당신은 기업 업무문제를 분석하는 연구용 분석기입니다.
입력된 Business Problem을 서로 다른 문제관점(Perspective)으로 분해하세요.

규칙:
1. Perspective는 해결책이 아니라 문제 관점이어야 합니다.
2. RAG, Agent, 자동화, 특정 AI 기술 같은 Solution을 미리 제안하지 마세요.
3. 서로 단순 동의어인 관점을 반복하지 마세요.
4. 입력 Query에 직접 근거한 관점만 만드세요.
5. 필요한 관점 수를 스스로 판단하되 최소 {min_p}, 최대 {max_p}개로 만드세요.
6. Ground Truth나 Reference Perspective를 추측하려 하지 마세요.
"""


def perspective_user_prompt(business_problem: str) -> str:
    return f"Business Problem:\n{business_problem}"


GPT_ONLY_SYSTEM_PROMPT = """당신은 AX 사례 검색 실험의 비교 시스템입니다.
주어진 Business Problem과 100개의 AX 사례 Problem View를 직접 비교해 관련 사례를 순위화하세요.

규칙:
1. Business Problem과 직접 관련된 사례를 우선하세요.
2. 사례의 Problem / Task / Context만 사용하세요.
3. Strategy, AI Technology, Implementation, Outcome은 제공되지 않으며 추측하지 마세요.
4. 입력에 존재하는 Case ID만 출력하세요.
5. Case ID를 중복 출력하지 마세요.
6. 상위 {top_n}개를 관련도 순으로 출력하세요.
"""


def gpt_only_user_prompt(business_problem: str, cases: list[AXCase]) -> str:
    blocks = [f"Business Problem:\n{business_problem}", "", "AX Cases:"]
    for case in cases:
        blocks.append(
            f"\n[{case.case_id}]\n"
            f"Problem: {case.business_problem}\n"
            f"Task: {case.ax_target_task}\n"
            f"Context: {case.business_context}"
        )
    return "\n".join(blocks)
