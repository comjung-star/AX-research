"""RQ1 YAML config loader."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .data import REPO_ROOT


def load_rq1_config(path: Path | None = None) -> dict[str, Any]:
    """Frozen RQ1 YAML 설정을 읽습니다."""

    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError(
            "Config를 읽으려면 'PyYAML' 패키지가 필요합니다."
        ) from exc

    path = path or REPO_ROOT / "configs" / "experiment_rq1_v1.yaml"
    with path.open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    if config["experiment"]["status"] != "FROZEN_FOR_IMPLEMENTATION":
        raise ValueError(
            "RQ1 runner는 frozen config만 실행합니다. "
            f"현재 상태={config['experiment']['status']}"
        )

    return config
