"""Stage 3-2A: read-only retrieval perspective provenance reconstruction.

RRF is used ONLY as a fixed diagnostic reference; this is not a search model
or a recommendation model. Do not use relevance/Gold labels to build traces.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path


FIELDS = [
    "query_id", "run_id", "leg_k", "final_rank", "case_id",
    "selected_perspective_id", "perspective_id",
    "is_selected_perspective", "retriever_source", "dense_rank", "sparse_rank",
]


def read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def reconstruct(
    rankings: list[dict[str, str]],
    candidate_rows: list[dict[str, str]],
    case_ids: set[str],
    query_ids: set[str],
    *,
    runs: tuple[str, ...] = ("1", "2", "3"),
    top_k: int = 10,
    leg_k: str = "10",
) -> tuple[list[dict[str, object]], dict[str, object]]:
    """Preserve every matching (perspective, retriever) record for ranked cases.

    The unit of Top-K is (query, run, case); trace expansion must never
    inflate the number of ranked cases or Strategy Coverage denominator.
    """
    if not query_ids or not case_ids or not runs or top_k < 1:
        raise ValueError("Empty freeze inputs or invalid top_k")
    selected = [
        row for row in rankings
        if row["system"] == "stage2_same_pool_rrf"
        and row["leg_k"] == str(leg_k)
        and 1 <= int(row["final_rank"]) <= top_k
    ]
    groups: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in selected:
        query, run, cid = row["query_id"], row["run_id"], row["case_id"]
        if query not in query_ids or run not in runs or cid not in case_ids:
            raise ValueError(f"Unknown query/run/case in ranking: {query}/{run}/{cid}")
        groups[(query, run)].append(row)
    expected_groups = {(q, r) for q in query_ids for r in runs}
    if set(groups) != expected_groups:
        raise ValueError("Ranking Query/Run groups do not match frozen Dev")
    for group, rows in groups.items():
        ranks = [int(row["final_rank"]) for row in rows]
        cases = [row["case_id"] for row in rows]
        if sorted(ranks) != list(range(1, top_k + 1)) or len(set(cases)) != top_k:
            raise ValueError(f"Rank or Case duplicated/missing in group {group}")

    candidate_map: dict[tuple[str, str, str], dict[str, dict[str, str]]] = defaultdict(dict)
    for row in candidate_rows:
        if row["leg_k"] != str(leg_k):
            continue
        query, run, cid, pid = (
            row["query_id"], row["run_id"], row["case_id"], row["perspective_id"]
        )
        if not pid or row["source"] not in {"dense", "sparse", "both"}:
            raise ValueError(f"Invalid candidate source/perspective: {query}/{run}/{cid}")
        key = (query, run, cid)
        if pid in candidate_map[key]:
            raise ValueError(f"Duplicate (Query, Run, Case, Perspective): {key}/{pid}")
        candidate_map[key][pid] = row

    output: list[dict[str, object]] = []
    multi = 0
    for (query, run), rows in sorted(groups.items()):
        for row in sorted(rows, key=lambda v: int(v["final_rank"])):
            cid = row["case_id"]
            perspective = row["source_perspective_id"]
            matches = candidate_map.get((query, run, cid), {})
            if not matches or perspective not in matches:
                raise ValueError(
                    f"Candidate provenance/selected perspective missing: {query}/{run}/{cid}/{perspective}"
                )
            multi += len(matches) > 1
            for pid, record in sorted(matches.items()):
                output.append({
                    "query_id": query,
                    "run_id": run,
                    "leg_k": str(leg_k),
                    "final_rank": int(row["final_rank"]),
                    "case_id": cid,
                    "selected_perspective_id": perspective,
                    "perspective_id": pid,
                    "is_selected_perspective": pid == perspective,
                    "retriever_source": record["source"],
                    "dense_rank": record["dense_rank"],
                    "sparse_rank": record["sparse_rank"],
                })
    n_cases = len(selected)
    summary = {
        "status": "DEV_READ_ONLY_PROVENANCE_DIAGNOSTIC",
        "ranking_system": "stage2_same_pool_rrf_REFERENCE_ONLY_NOT_PROPOSED_MODEL",
        "leg_k": str(leg_k),
        "top_k": top_k,
        "queries": len(query_ids),
        "runs_per_query": len(runs),
        "query_run_groups": len(groups),
        "ranked_case_occurrences": n_cases,
        "perspective_case_links": len(output),
        "extra_perspective_links": len(output) - n_cases,
        "multi_perspective_case_occurrences": multi,
        "multi_perspective_case_rate": multi / n_cases,
        "missing_ranked_case_provenance": 0,
        "selected_perspective_retained": n_cases,
        "link_count_by_perspective": {
            pid: sum(r["perspective_id"] == pid for r in output)
            for pid in sorted({str(r["perspective_id"]) for r in output})
        },
        "interpretation": (
            "An audit of existing retrieval paths, not an improvement "
            "in recall, recommendation, or strategy coverage."
        ),
    }
    return output, summary


def run(
    rankings_file: str | Path,
    candidates_file: str | Path,
    cases_file: str | Path,
    queries_file: str | Path,
    output_dir: str | Path,
) -> dict[str, object]:
    cases = read_csv(cases_file)
    queries = read_csv(queries_file)
    case_ids = {r["case_id"] for r in cases}
    query_ids = {r["query_id"] for r in queries}
    if len(case_ids) != len(cases) or len(query_ids) != len(queries):
        raise ValueError("Duplicate frozen Case or Query ID")
    rows, summary = reconstruct(
        read_csv(rankings_file), read_csv(candidates_file), case_ids, query_ids
    )
    dest = Path(output_dir)
    dest.mkdir(parents=True, exist_ok=True)
    with (dest / "stage3_perspective_case_trace.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    (dest / "stage3_perspective_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--rankings",
        default="experiments/rq2_multiview/results/stage2_interaction_v1/stage2_interaction_final_rankings.csv",
    )
    parser.add_argument(
        "--candidates",
        default="experiments/rq2_multiview/results/stage2_hybrid_v1/stage2_hybrid_candidate_provenance.csv",
    )
    parser.add_argument("--cases", default="data/main_cases_v1.csv")
    parser.add_argument("--queries", default="data/retrieval_queries_v0.1.csv")
    parser.add_argument(
        "--output-dir",
        default="experiments/rq3_evidence/results/stage3_provenance_v1",
    )
    args = parser.parse_args()
    print(json.dumps(
        run(args.rankings, args.candidates, args.cases, args.queries, args.output_dir),
        ensure_ascii=False, indent=2,
    ))


if __name__ == "__main__":
    main()
