"""Offline summaries; never relabel failed output or contact providers."""
import itertools
from collections import Counter
from decimal import Decimal
from scripts import query_isolated_revalidation as run


def agreement(rows):
    complete = [r for r in rows if len(r["new_scores"]) == 3]
    n = len(complete)
    exact = sum(len(set(r["new_scores"].values())) == 1 for r in complete)
    binary = sum(len({s >= 3 for s in r["new_scores"].values()}) == 1 for r in complete)
    return {"denominator": n, "exact_grade_numerator": exact, "binary_numerator": binary,
            "exact_grade_rate": exact / n if n else None, "binary_rate": binary / n if n else None}


def summarize():
    plan = run.api.read_json(run.OUTPUT / "plan.json")
    old_root = run.ROOT / "docs/stage1-cost-pilot-2026-10-27/run-v2"
    old = {}
    for batch in run.api.read_json(old_root / "pilot_results.json"):
        for row in batch["ratings"]:
            old.setdefault(run.key_of(row), {})[batch["provider"]] = row["relevance_0_4"]
    flips = {run.key_of(r) for r in run.api.read_json(old_root / "pilot_disagreements.json") if r["threshold_flip"]}
    rows = {run.key_of(u): {**u, "old_scores": old[run.key_of(u)], "new_scores": {}, "new_reasons": {}, "ambiguities": {}}
            for job in plan["pilot_jobs"] for u in job["units"]}
    for provider in run.CONFIG["models"]:
        for path in (run.OUTPUT / "results" / provider).glob("pilot_*.json"):
            result = run.api.read_json(path)
            if not result["validation"]["valid"]:
                raise ValueError("Invalid output in accepted results")
            for r in result["validation"]["ratings"]:
                target = rows[run.key_of(r)]
                if provider in target["new_scores"]:
                    raise ValueError("Duplicate provider-target grade")
                target["new_scores"][provider] = r["score"]
                target["new_reasons"][provider] = r["reason"]
                target["ambiguities"][provider] = r["ambiguity"]
    values = list(rows.values())
    usage = {}
    for provider in run.CONFIG["models"]:
        paths = [p for base in (run.PREVIOUS_OUTPUT, run.PREVIOUS_OUTPUT / "format-v5", run.PREVIOUS_OUTPUT / "format-v6", run.PREVIOUS_OUTPUT / "format-v7", run.OUTPUT) for p in (base / "attempts" / provider).glob("pilot_*.json")]
        attempts = [run.api.read_json(p) for p in paths]
        usage[provider] = {
            "generation_attempts_recorded_not_cancelled": sum(a["state"] != "CANCELLED_BEFORE_DISPATCH" for a in attempts),
            "confirmed_generation_responses": sum(bool(a.get("usage")) for a in attempts),
            "actual_input_tokens": sum(a.get("usage", {}).get("actual_input_tokens", 0) for a in attempts),
            "actual_output_tokens_including_thinking": sum(a.get("usage", {}).get("actual_output_tokens_including_thinking", 0) for a in attempts),
            "usage_cost_usd": run.api.money(sum((Decimal(a.get("usage", {}).get("usage_cost_usd", "0")) for a in attempts), Decimal(0))),
            "actual_or_reserved_usd": run.api.money(sum((Decimal(a.get("usage", {}).get("usage_cost_usd", a["reserved_usd"])) for a in attempts), Decimal(0))),
            "unconfirmed_attempts": sum(not a.get("usage") and a["state"] != "CANCELLED_BEFORE_DISPATCH" for a in attempts),
            "accepted_grades": sum(provider in r["new_scores"] for r in values),
            "score_distribution": dict(sorted(Counter(r["new_scores"][provider] for r in values if provider in r["new_scores"]).items())),
        }
    pairwise = {}
    for a, b in itertools.combinations(run.CONFIG["models"], 2):
        paired = [r for r in values if a in r["new_scores"] and b in r["new_scores"]]
        pairwise[f"{a}:{b}"] = {"denominator": len(paired),
            "exact_grade_numerator": sum(r["new_scores"][a] == r["new_scores"][b] for r in paired),
            "binary_numerator": sum((r["new_scores"][a] >= 3) == (r["new_scores"][b] >= 3) for r in paired)}
    report = {"status": "PILOT_PENDING_GATE_REVIEW", "human_gold": False, "old_metrics_invalid_due_to_question_confusion": True,
              "all_40": agreement(values), "query_case_20": agreement([r for r in values if not r["perspective_id"]]),
              "reference_case_20": agreement([r for r in values if r["perspective_id"]]), "pairwise": pairwise,
              "usage": usage, "comparisons": values, "original_12_boundary_disagreements": [r for r in values if run.key_of(r) in flips],
              "current_binary_disagreements": [r for r in values if len(r["new_scores"]) == 3 and len({s >= 3 for s in r["new_scores"].values()}) > 1]}
    run.save(run.OUTPUT / "pilot_summary.json", report)
    return report


if __name__ == "__main__":
    import json
    result = summarize()
    print(json.dumps({k: result[k] for k in ("all_40", "query_case_20", "reference_case_20", "usage")}, ensure_ascii=False))
