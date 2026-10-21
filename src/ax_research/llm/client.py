"""Common OpenAI Responses API client for RQ1.

API keys are never stored in source. The OpenAI SDK reads OPENAI_API_KEY.

Important v1.3 rule:
gpt-6-luna rejects the temperature parameter. When config.temperature is None,
this client OMITs that argument entirely rather than sending null.
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
        temperature: float | None,
        perspective_min: int,
        perspective_max: int,
    ) -> None:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError(
                "LLM execution requires the openai Python SDK."
            ) from exc

        self._client = OpenAI()
        self.model = model
        self.temperature = temperature
        self.perspective_min = perspective_min
        self.perspective_max = perspective_max

    def _sampling_args(self) -> dict[str, float]:
        """Return only API-supported sampling arguments.

        For v1.3 / gpt-6-luna this is intentionally empty.
        """

        if self.temperature is None:
            return {}
        return {"temperature": self.temperature}

    def generate_perspectives(self, business_problem: str) -> list[Perspective]:
        system_prompt = PERSPECTIVE_SYSTEM_PROMPT.format(
            min_p=self.perspective_min,
            max_p=self.perspective_max,
        )
        response = self._client.responses.parse(
            model=self.model,
            input=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": perspective_user_prompt(business_problem),
                },
            ],
            text_format=PerspectiveResponse,
            **self._sampling_args(),
        )
        parsed = response.output_parsed
        if parsed is None:
            raise RuntimeError("Perspective generation returned no parsed output")

        perspectives = parsed.perspectives
        if not (
            self.perspective_min
            <= len(perspectives)
            <= self.perspective_max
        ):
            raise ValueError(
                f"Perspective count out of range: {len(perspectives)}"
            )
        return perspectives

    def gpt_only_rank(
        self,
        business_problem: str,
        cases: Sequence[AXCase],
        *,
        top_n: int,
    ) -> GPTOnlyResponse:
        response = self._client.responses.parse(
            model=self.model,
            input=[
                {
                    "role": "system",
                    "content": GPT_ONLY_SYSTEM_PROMPT.format(top_n=top_n),
                },
                {
                    "role": "user",
                    "content": gpt_only_user_prompt(
                        business_problem, list(cases)
                    ),
                },
            ],
            text_format=GPTOnlyResponse,
            **self._sampling_args(),
        )
        parsed = response.output_parsed
        if parsed is None:
            raise RuntimeError("GPT-only ranking returned no parsed output")

        valid_ids = {case.case_id for case in cases}
        ids = [row.case_id for row in parsed.ranked_cases]

        if len(ids) != top_n:
            raise ValueError(
                f"GPT-only returned {len(ids)} cases; expected {top_n}"
            )
        if len(set(ids)) != len(ids):
            raise ValueError("GPT-only returned duplicate case IDs")

        unknown = set(ids) - valid_ids
        if unknown:
            raise ValueError(
                f"GPT-only returned unknown case IDs: {sorted(unknown)}"
            )
        return parsed
