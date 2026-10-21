"""OpenAI Responses API를 이용한 공통 LLM client.

실제 API Key는 코드에 저장하지 않습니다.
OpenAI Python SDK는 OPENAI_API_KEY 환경변수를 자동으로 읽습니다.
"""

from __future__ import annotations

from typing import Sequence

from ..data import AXCase
from .prompts import (
    GPT_ONLY_SYSTEM_PROMPT,
    PERSPECTIVE_SYSTEM_PROMPT,
    gpt_only_user_prompt,
    perspective_user_prompt,
)
from .schemas import GPTOnlyResponse, Perspective, PerspectiveResponse


class RQ1OpenAIClient:
    def __init__(
        self,
        *,
        model: str,
        temperature: float,
        perspective_min: int,
        perspective_max: int,
    ) -> None:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError(
                "LLM 실행에는 openai Python SDK가 필요합니다. "
                "requirements-rq1.txt를 설치하세요."
            ) from exc

        self._client = OpenAI()
        self.model = model
        self.temperature = temperature
        self.perspective_min = perspective_min
        self.perspective_max = perspective_max

    def generate_perspectives(self, business_problem: str) -> list[Perspective]:
        """Business Problem 하나에서 2~5개의 동적 문제관점을 생성한다."""
        system_prompt = PERSPECTIVE_SYSTEM_PROMPT.format(
            min_p=self.perspective_min, max_p=self.perspective_max
        )
        response = self._client.responses.parse(
            model=self.model,
            temperature=self.temperature,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": perspective_user_prompt(business_problem)},
            ],
            text_format=PerspectiveResponse,
        )
        parsed = response.output_parsed
        if parsed is None:
            raise RuntimeError("Perspective generation returned no parsed output")

        perspectives = parsed.perspectives
        if not (self.perspective_min <= len(perspectives) <= self.perspective_max):
            raise ValueError(
                f"Perspective count out of range: {len(perspectives)} "
                f"(expected {self.perspective_min}..{self.perspective_max})"
            )
        return perspectives

    def gpt_only_rank(
        self,
        business_problem: str,
        cases: Sequence[AXCase],
        *,
        top_n: int,
    ) -> GPTOnlyResponse:
        """100개 Case Problem View를 LLM이 직접 읽고 상위 Case를 선택한다."""
        response = self._client.responses.parse(
            model=self.model,
            temperature=self.temperature,
            input=[
                {"role": "system", "content": GPT_ONLY_SYSTEM_PROMPT.format(top_n=top_n)},
                {"role": "user", "content": gpt_only_user_prompt(business_problem, list(cases))},
            ],
            text_format=GPTOnlyResponse,
        )
        parsed = response.output_parsed
        if parsed is None:
            raise RuntimeError("GPT-only ranking returned no parsed output")

        valid_ids = {case.case_id for case in cases}
        ids = [row.case_id for row in parsed.ranked_cases]
        if len(ids) != top_n:
            raise ValueError(f"GPT-only returned {len(ids)} cases; expected {top_n}")
        if len(set(ids)) != len(ids):
            raise ValueError("GPT-only returned duplicate case IDs")
        unknown = set(ids) - valid_ids
        if unknown:
            raise ValueError(f"GPT-only returned unknown case IDs: {sorted(unknown)}")
        return parsed
