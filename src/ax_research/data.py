"""RQ1 실험용 공통 Data Loader.

모든 비교 시스템이 같은 파일을 같은 규칙으로 읽도록 한 곳에서 관리합니다.
Primary RQ1에서는 Query의 goal/context가 아니라 business_problem_query만
검색 입력으로 사용합니다.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class AXCase:
    """검색 대상 AX 사례 한 건."""

    case_id: str
    business_problem: str
    ax_target_task: str
    business_context: str
    strategy: tuple[str, ...]

    def problem_view_text(self) -> str:
        """Retrieval에 허용된 Problem View만 직렬화합니다."""

        return (
            f"[PROBLEM] {self.business_problem}\n"
            f"[TASK] {self.ax_target_task}\n"
            f"[CONTEXT] {self.business_context}"
        )


@dataclass(frozen=True)
class RetrievalQuery:
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
    return tuple(x.strip() for x in (value or "").split("|") if x.strip())


def load_cases(path: str | Path | None = None) -> list[AXCase]:
    """main_cases_v1.csv를 읽습니다."""

    path = Path(path) if path is not None else REPO_ROOT / "data" / "main_cases_v1.csv"
    rows: list[AXCase] = []

    with path.open("r", encoding="utf-8-sig", newline="") as f:
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


def load_queries(path: str | Path | None = None) -> list[RetrievalQuery]:
    """Dev Query를 읽습니다."""

    path = Path(path) if path is not None else (
        REPO_ROOT / "data" / "retrieval_queries_v0.1.csv"
    )
    rows: list[RetrievalQuery] = []

    with path.open("r", encoding="utf-8-sig", newline="") as f:
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


def load_relevance_labels(path: str | Path | None = None) -> list[RelevanceLabel]:
    """Perspective × Case relevance 0~4 라벨을 읽습니다."""

    path = Path(path) if path is not None else (
        REPO_ROOT / "data" / "perspective_case_relevance_v0.1.csv"
    )
    rows: list[RelevanceLabel] = []

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            score = int(row["relevance_0_4"])
            if not 0 <= score <= 4:
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


def load_gold(path: str | Path | None = None) -> list[GoldRecord]:
    """Query 단위 확정 Gold를 읽습니다."""

    path = Path(path) if path is not None else (
        REPO_ROOT / "data" / "retrieval_gold_v0.1.csv"
    )
    rows: list[GoldRecord] = []

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            rows.append(
                GoldRecord(
                    query_id=row["query_id"].strip(),
                    gold_perspectives=_split_pipe(row.get("gold_perspectives", "")),
                    gold_relevant_cases=_split_pipe(
                        row.get("gold_relevant_cases", "")
                    ),
                    gold_strategy_set=_split_pipe(row.get("gold_strategy_set", "")),
                    adjudication_status=row.get(
                        "adjudication_status", ""
                    ).strip(),
                )
            )

    return rows


def index_by(items: Iterable, attr: str) -> dict[str, object]:
    """dataclass 목록을 ID 기반 dict로 바꾸는 공통 helper."""

    result: dict[str, object] = {}
    for item in items:
        key = getattr(item, attr)
        if key in result:
            raise ValueError(f"Duplicate {attr}: {key}")
        result[key] = item
    return result
