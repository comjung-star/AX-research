"""Freeze된 YAML 실험설정을 읽는 모듈."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class RQ1Config:
    experiment_id: str
    query_ids: tuple[str, ...]
    evaluation_k: tuple[int, ...]
    gold_threshold: int
    dense_model: str
    common_llm_model: str = "gpt-5.6-luna"
    llm_repeats: int = 3
    llm_temperature: float = 0.5
    perspective_min: int = 2
    perspective_max: int = 5


def load_rq1_config(path: str | Path) -> RQ1Config:
    """configs/experiment_rq1_v1.yaml에서 실행값을 읽는다."""
    with Path(path).open("r", encoding="utf-8") as f:
        raw: dict[str, Any] = yaml.safe_load(f)

    systems = raw["systems"]
    return RQ1Config(
        experiment_id=raw["experiment"]["id"],
        query_ids=tuple(raw["experiment"]["queries"]["ids"]),
        evaluation_k=tuple(int(k) for k in raw["evaluation"]["k"]),
        gold_threshold=int(raw["evaluation"]["gold_relevance_threshold"]),
        dense_model=systems["single_dense"]["model"],
        common_llm_model=systems["common_llm"]["model"],
        llm_repeats=int(systems["gpt_only"]["repeats"]),
        llm_temperature=float(systems["gpt_only"]["temperature"]),
        perspective_min=int(systems["multi_perspective_bm25"]["perspective_min"]),
        perspective_max=int(systems["multi_perspective_bm25"]["perspective_max"]),
    )
