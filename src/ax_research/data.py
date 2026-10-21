"""RQ1 실험용 데이터 로더.

왜 별도 Data Loader를 두는가?
---------------------------
BM25, Dense, GPT-only, Multi-Perspective가 서로 다른 방식으로 파일을 읽으면
같은 데이터셋을 사용한다고 해도 미묘하게 입력이 달라질 수 있습니다.
그래서 모든 실험이 이 모듈을 통해 동일한 Query / Case / Ground Truth를 읽도록 합니다.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class AXCase:
    """검색 대상 AX 사례 1건.

    Retrieval에는 Problem View만 사용합니다.
    Strategy는 검색 입력이 아니라 Strategy Coverage 평가에만 사용합니다.
    """

    case_id: str
    business_problem: str
    ax_target_task: str
    business_context: str
    strategy: tuple[str, ...]

    def problem_view_text(self) -> str:
        """Freeze된 명세대로 Problem/Task/Context를 하나의 검색 문서로 직렬화."""
        return (
            f"[PROBLEM] {self.business_problem}\n"
            f"[TASK] {self.ax_target_task}\n"
            f"[CONTEXT] {self.business_context}"
        )


@dataclass(frozen=True)
class RetrievalQuery:
    """RQ1에서 사용하는 Dev Query 1건.

    Primary RQ1 입력은 business_problem_query만 사용합니다.
    goal/context는 CSV에 존재하지만 첫 실험 검색입력에는 넣지 않습니다.
    """

    query_id: str
    business_problem_query: str
    goal: str
    context: str
    draft_perspectives: str
    status: str


@dataclass(frozen=True)
class RelevanceLabel:
    query_id: str
    perspective_id: str
    case_id: str
    relevance: int


@dataclass(frozen=True)
class GoldRecord:
    query_id: str
    gold_perspectives: tuple[str, ...]
    gold_relevant_cases: tuple[str, ...]
    gold_strategy_set: tuple[str, ...]
    adjudication_status: str


def _split_pipe(value: str) -> tuple[str, ...]:
    """CSV의 A|B|C 형태 multi-label을 안전하게 tuple로 변환."""
    return tuple(x.strip() for x in (value or "").split("|") if x.strip())


def load_cases(path: str | Path) -> list[AXCase]:
    """main_cases_v1.csv를 읽는다."""
    rows: list[AXCase] = []
    with Path(path).open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            rows.append(
                AXCase(
                    case_id=row["case_id"].strip(),
                    business_problem=row["business_problem"].strip(),
                    ax_target_task=row["ax_target_task"].strip(),
                    business_context=row["business_context"].strip(),
                    strategy=_split_pipe(row.get("strategy", "")),
                )
            )
    return rows


def load_queries(path: str | Path) -> list[RetrievalQuery]:
    """retrieval_queries_v0.1.csv를 읽는다."""
    rows: list[RetrievalQuery] = []
    with Path(path).open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            rows.append(
                RetrievalQuery(
                    query_id=row["query_id"].strip(),
                    business_problem_query=row["business_problem_query"].strip(),
                    goal=row.get("goal", "").strip(),
                    context=row.get("context", "").strip(),
                    draft_perspectives=row.get("draft_perspectives", "").strip(),
                    status=row.get("status", "").strip(),
                )
            )
    return rows


def load_relevance_labels(path: str | Path) -> list[RelevanceLabel]:
    """Perspective x Case 관련도(0~4)를 읽는다."""
    rows: list[RelevanceLabel] = []
    with Path(path).open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            score = int(row["relevance_0_4"])
            if score < 0 or score > 4:
                raise ValueError(f"Invalid relevance score: {score}")
            rows.append(
                RelevanceLabel(
                    query_id=row["query_id"].strip(),
                    perspective_id=row["perspective_id"].strip(),
                    case_id=row["case_id"].strip(),
                    relevance=score,
                )
            )
    return rows


def load_gold(path: str | Path) -> list[GoldRecord]:
    """Query 단위 Gold union / Strategy set을 읽는다."""
    rows: list[GoldRecord] = []
    with Path(path).open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            rows.append(
                GoldRecord(
                    query_id=row["query_id"].strip(),
                    gold_perspectives=_split_pipe(row.get("gold_perspectives", "")),
                    gold_relevant_cases=_split_pipe(row.get("gold_relevant_cases", "")),
                    gold_strategy_set=_split_pipe(row.get("gold_strategy_set", "")),
                    adjudication_status=row.get("adjudication_status", "").strip(),
                )
            )
    return rows


def index_by(items: Iterable, attr: str) -> dict[str, object]:
    """작은 Dev 데이터셋에서 ID 기반 접근을 간단히 하기 위한 공통 helper."""
    result: dict[str, object] = {}
    for item in items:
        key = getattr(item, attr)
        if key in result:
            raise ValueError(f"Duplicate {attr}: {key}")
        result[key] = item
    return result
