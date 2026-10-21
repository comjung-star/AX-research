"""RQ1 experiment config loader."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class RQ1Config:
    experiment_id: str
    query_ids: tuple[str, ...]
    evaluation_k: tuple[int, ...]
    gold_threshold: int
    dense_model: str
    normalize_embeddings: bool = True
    llm_model: str = "gpt-6-luna"
    llm_repeats: int = 3
    # gpt-6-luna rejects the temperature parameter. None means OMIT it.
    temperature: float | None = None
    perspective_min: int = 2
    perspective_max: int = 5
    branch_query_mode: str = "perspective_only"
    status: str = "FROZEN_FOR_IMPLEMENTATION"


def load_rq1_config(path: str | Path | None = None) -> RQ1Config:
    """Load the current frozen v1.3 config."""

    path = Path(path) if path is not None else (
        REPO_ROOT / "configs" / "experiment_rq1_v1.3.yaml"
    )

    with path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    status = raw["experiment"]["status"]
    if status != "FROZEN_FOR_IMPLEMENTATION":
        raise ValueError(f"RQ1 config must be frozen; status={status}")

    branch_mode = raw["systems"]["perspective_generator"]["branch_query_mode"]
    if branch_mode != "perspective_only":
        raise ValueError(
            "RQ1 v1.3 Primary branch query must be perspective_only; "
            f"got {branch_mode}"
        )

    raw_temperature = raw["systems"]["gpt_only"].get("temperature")
    temperature = (
        None if raw_temperature is None else float(raw_temperature)
    )

    return RQ1Config(
        experiment_id=raw["experiment"]["id"],
        query_ids=tuple(raw["experiment"]["queries"]["ids"]),
        evaluation_k=tuple(int(k) for k in raw["evaluation"]["k"]),
        gold_threshold=int(raw["evaluation"]["gold_relevance_threshold"]),
        dense_model=raw["systems"]["single_dense"]["model"],
        normalize_embeddings=bool(
            raw["systems"]["single_dense"]["normalize_embeddings"]
        ),
        llm_model=raw["systems"]["common_llm"]["model"],
        llm_repeats=int(raw["systems"]["gpt_only"]["repeats"]),
        temperature=temperature,
        perspective_min=int(
            raw["systems"]["multi_perspective_dense"]["perspective_min"]
        ),
        perspective_max=int(
            raw["systems"]["multi_perspective_dense"]["perspective_max"]
        ),
        branch_query_mode=branch_mode,
        status=status,
    )
