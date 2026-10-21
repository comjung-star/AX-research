"""OpenAI Structured Outputs에 사용할 응답 스키마."""

from pydantic import BaseModel, Field


class Perspective(BaseModel):
    id: str = Field(description="P1, P2처럼 실행 내에서 사용하는 관점 ID")
    title: str = Field(description="짧은 문제관점 이름")
    description: str = Field(description="Query에 근거한 문제관점 설명")


class PerspectiveResponse(BaseModel):
    perspectives: list[Perspective]


class GPTOnlyRankedCase(BaseModel):
    case_id: str
    reason: str = Field(description="왜 이 업무문제와 관련 있는지 짧은 근거")


class GPTOnlyResponse(BaseModel):
    ranked_cases: list[GPTOnlyRankedCase]
