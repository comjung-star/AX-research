"""Stage 3-1 offline Root Cause ↔ Strategy Wald association diagnostics.

This module does not infer Root Cause from Solution View and does not make
recommendations. It analyzes existing, frozen case-level multi-labels only.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path


def read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def split_labels(value: str) -> set[str]:
    return {part.strip() for part in value.split("|") if part.strip()}


def validate_cases(
    cases: list[dict[str, str]],
    factors: list[str],
    strategies: list[str],
) -> list[tuple[str, set[str], set[str], str]]:
    if not cases:
        raise ValueError("No cases")
    factor_set, strategy_set = set(factors), set(strategies)
    if len(factor_set) != len(factors) or len(strategy_set) != len(strategies):
        raise ValueError("Duplicate taxonomy ID")
    seen: set[str] = set()
    prepared: list[tuple[str, set[str], set[str], str]] = []
    for row in cases:
        case_id = row["case_id"].strip()
        if not case_id or case_id in seen:
            raise ValueError(f"Missing or duplicate Case ID: {case_id}")
        seen.add(case_id)
        root_factors = split_labels(row["root_cause_factor"])
        case_strategies = split_labels(row["strategy"])
        if not root_factors or not case_strategies:
            raise ValueError(f"Missing factor or strategy labels: {case_id}")
        if root_factors - factor_set or case_strategies - strategy_set:
            raise ValueError(f"Unknown factor/strategy label: {case_id}")
        prepared.append(
            (case_id, root_factors, case_strategies, row.get("source", ""))
        )
    return prepared


def bh_adjust(pvalues: list[float]) -> list[float]:
    """Benjamini-Hochberg q-values; caller includes all planned comparisons."""
    n = len(pvalues)
    if not n:
        return []
    order = sorted(range(n), key=lambda i: (pvalues[i], i))
    output = [1.0] * n
    running = 1.0
    for rank in range(n, 0, -1):
        i = order[rank - 1]
        running = min(running, pvalues[i] * n / rank)
        output[i] = running
    return output


def analyze(
    cases: list[tuple[str, set[str], set[str], str]],
    factors: list[str],
    strategies: list[str],
    min_cell: int = 5,
) -> list[dict[str, object]]:
    """2x2 unconditional log-odds Wald test (univariate logistic equivalent).

    A cell below min_cell is excluded from Wald interpretation (no imputation).
    """
    if min_cell < 1:
        raise ValueError("min_cell must be positive")
    rows: list[dict[str, object]] = []
    provisional_pvalues: list[float] = []
    for factor in factors:
        for strategy in strategies:
            a = b = c = d = 0
            for _, fs, ss, _ in cases:
                x, y = factor in fs, strategy in ss
                if x and y:
                    a += 1
                elif x:
                    b += 1
                elif y:
                    c += 1
                else:
                    d += 1
            eligible = min(a, b, c, d) >= min_cell
            entry: dict[str, object] = {
                "factor_id": factor,
                "strategy_id": strategy,
                "n": len(cases),
                "a_factor_and_strategy": a,
                "b_factor_no_strategy": b,
                "c_no_factor_strategy": c,
                "d_neither": d,
                "min_cell": min(a, b, c, d),
                "wald_eligible": eligible,
                "status": "WALD_DESCRIPTIVE" if eligible else "SPARSE_ABSTAIN",
                "beta": "",
                "odds_ratio": "",
                "se_beta": "",
                "wald_z": "",
                "wald_p": "",
                "or_ci95_low": "",
                "or_ci95_high": "",
            }
            p = 1.0
            if eligible:
                beta = math.log(a * d / (b * c))
                se = math.sqrt(1 / a + 1 / b + 1 / c + 1 / d)
                z = beta / se
                p = math.erfc(abs(z) / math.sqrt(2))
                entry.update(
                    beta=beta,
                    odds_ratio=math.exp(beta),
                    se_beta=se,
                    wald_z=z,
                    wald_p=p,
                    or_ci95_low=math.exp(beta - 1.96 * se),
                    or_ci95_high=math.exp(beta + 1.96 * se),
                )
            provisional_pvalues.append(p)  # p=1 for untestable pair in BH family
            rows.append(entry)
    for row, q in zip(rows, bh_adjust(provisional_pvalues)):
        row["bh_q_all_pairs"] = q if row["wald_eligible"] else ""
    return rows


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError("No output rows")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def run(
    case_csv: str | Path,
    factor_csv: str | Path,
    strategy_csv: str | Path,
    output_dir: str | Path,
    min_cell: int = 5,
) -> dict[str, object]:
    cases_raw = read_csv(case_csv)
    factors = [r["factor_id"].strip() for r in read_csv(factor_csv)]
    strategies = [r["strategy_id"].strip() for r in read_csv(strategy_csv)]
    if not factors or not strategies:
        raise ValueError("Empty taxonomy")
    cases = validate_cases(cases_raw, factors, strategies)
    pairs = analyze(cases, factors, strategies, min_cell=min_cell)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    write_csv(output / "stage3_wald_pairs.csv", pairs)
    links = [
        {
            "case_id": cid,
            "factor_id": factor,
            "strategy_id": strategy,
            "source": source,
        }
        for cid, fs, ss, source in cases
        for factor in sorted(fs)
        for strategy in sorted(ss)
    ]
    write_csv(output / "stage3_case_factor_strategy_links.csv", links)
    eligible = [p for p in pairs if p["wald_eligible"]]
    summary = {
        "status": "DEV_OFFLINE_DESCRIPTIVE_NOT_RECOMMENDATION",
        "cases": len(cases),
        "factors": len(factors),
        "strategies": len(strategies),
        "pairs": len(pairs),
        "wald_eligible": len(eligible),
        "sparse_abstain": len(pairs) - len(eligible),
        "bh_q_lt_0_05": sum(p["bh_q_all_pairs"] < 0.05 for p in eligible),
        "min_cell_required": min_cell,
        "interpretation": (
            "Unadjusted univariate associations only; no causal inference, "
            "no strategy selection, no held-out performance claim."
        ),
    }
    (output / "stage3_wald_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", default="data/main_cases_v1.csv")
    parser.add_argument("--factors", default="data/root_cause_factors_v1.csv")
    parser.add_argument("--strategies", default="data/strategy_taxonomy_v1.csv")
    parser.add_argument("--output-dir", default="experiments/rq3_evidence/results/stage3_wald_v1")
    parser.add_argument("--min-cell", type=int, default=5)
    args = parser.parse_args()
    result = run(args.cases, args.factors, args.strategies, args.output_dir, args.min_cell)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
