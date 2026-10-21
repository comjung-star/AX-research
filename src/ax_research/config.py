"""RQ1 실험 설정 로더.

YAML을 코드 곳곳에서 직접 읽지 않고 RQ1Config 한 객체로 변환합니다.
이렇게 해야 BM25 / Dense / GPT-only / Multi-Perspective가
정확히 같은 실험조건을 공유할 수 있습니다.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class RQ1Config:
    """RQ1 실행에 실제로 필요한 Frozen 설정값."""

    experiment_id: str
    query_ids: tuple[str, ...]
    evaluation_k: tuple[int, ...]
    gold_threshold: int
    dense_model: str
    normalize_embeddings: bool = True
    llm_model: str = "gpt-6-luna"
    llm_repeats: int = 3
    temperature: float = 0.5
    perspective_min: int = 2
    perspective_max: int = 5
    status: str = "FROZEN_FOR_IMPLEMENTATION"


def load_rq1_config(path: str | Path | None = None) -> RQ1Config:
    """Frozen v1.1 YAML을 읽어 RQ1Config로 변환합니다.

    path를 생략하면 현재 구현 기준인 v1.1 config를 사용합니다.
    """

    path = Path(path) if path is not None else (
        REPO_ROOT / "configs" / "experiment_rq1_v1.1.yaml"
    )

    with path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    status = raw["experiment"]["status"]
    if status != "FROZEN_FOR_IMPLEMENTATION":
        raise ValueError(
            "RQ1 runner는 Frozen config만 실행합니다. "
            f"현재 status={status}"
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
        temperature=float(raw["systems"]["gpt_only"]["temperature"]),
        perspective_min=int(
            raw["systems"]["multi_perspective_dense"]["perspective_min"]
        ),
        perspective_max=int(
            raw["systems"]["multi_perspective_dense"]["perspective_max"]
        ),
        status=status,
    )
