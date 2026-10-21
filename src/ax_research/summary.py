"""RQ1 결과 요약.

LLM 기반 시스템은 Query별 3회 독립 실행하므로 좋은 Run 하나만 고르지 않습니다.
이 모듈은 모든 metric row를 사용해 system × K별 평균/최소/최대/표준편차를 만듭니다.
"""

from __future__ import annotations

import csv
import math
from collections import defaultdict
from pathlib import Path


METRIC_COLUMNS = (
    "recall",
    "perspective_coverage",
    "strategy_coverage",
)


def _mean(values: list[float]) -> float:
    return sum(values) / len(values)


def _pstdev(values: list[float]) -> float:
    if not values:
        raise ValueError("values must not be empty")
    m = _mean(values)
    return math.sqrt(sum((x - m) ** 2 for x in values) / len(values))


def summarize_metrics(
    metrics_csv: str | Path,
    output_csv: str | Path,
) -> Path:
    """Metric CSV를 system × K별 descriptive summary로 저장합니다."""

    with Path(metrics_csv).open(
        "r", encoding="utf-8-sig", newline=""
    ) as f:
        rows = list(csv.DictReader(f))

    if not rows:
        raise ValueError("metrics CSV is empty")

    grouped: dict[tuple[str, int], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[(row["system"], int(row["k"]))].append(row)

    output_rows: list[dict[str, object]] = []
    for (system, k), items in sorted(grouped.items()):
        out: dict[str, object] = {
            "system": system,
            "k": k,
            "row_count": len(items),
        }
        for metric in METRIC_COLUMNS:
            values = [float(row[metric]) for row in items]
            out[f"mean_{metric}"] = _mean(values)
            out[f"min_{metric}"] = min(values)
            out[f"max_{metric}"] = max(values)
            out[f"std_{metric}"] = _pstdev(values)
        output_rows.append(out)

    output = Path(output_csv)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(output_rows[0]))
        writer.writeheader()
        writer.writerows(output_rows)

    return output
