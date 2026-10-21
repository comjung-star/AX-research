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


def load_rq1_config(path: str | Path) -> RQ1Config:
    """configs/experiment_rq1_v1.yaml에서 현재 구현에 필요한 값만 읽는다."""
    with Path(path).open("r", encoding="utf-8") as f:
        raw: dict[str, Any] = yaml.safe_load(f)

    return RQ1Config(
        experiment_id=raw["experiment"]["id"],
        query_ids=tuple(raw["experiment"]["queries"]["ids"]),
        evaluation_k=tuple(int(k) for k in raw["evaluation"]["k"]),
        gold_threshold=int(raw["evaluation"]["gold_relevance_threshold"]),
        dense_model=raw["systems"]["single_dense"]["model"],
    )
