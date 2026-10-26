"""Independent scores and held disagreements; no automatic majority labels."""
from collections import Counter, defaultdict
from decimal import Decimal
from scripts import query_isolated_revalidation as run


def summarize():
    plan = run.api.read_json(run.OUTPUT / "plan.json")
    rows = {run.key_of(u): {"query_id": u["query_id"], "case_id": u["case_id"], "perspective_id": "", "scores": {}, "reasons": {}, "ambiguities": {}, "source_response_files": {}}
            for job in plan["stage1_jobs"] for u in job["units"]}
    usage, distribution = {}, {}
    for provider in run.CONFIG["models"]:
        for path in (run.OUTPUT / "results" / provider).glob("stage1_*.json"):
            response = run.api.read_json(path)
            if not response["validation"]["valid"]:
                raise ValueError("Invalid response cannot enter Stage1 summary")
            for r in response["validation"]["ratings"]:
                target = rows[run.key_of(r)]
                if provider in target["scores"]:
                    raise ValueError("Duplicate independent grade")
                target["scores"][provider] = r["score"]
                target["reasons"][provider] = r["reason"]
                target["ambiguities"][provider] = r["ambiguity"]
                target["source_response_files"][provider] = str(path.relative_to(run.ROOT)).replace("\\", "/")
        attempts = [run.api.read_json(p) for p in (run.OUTPUT / "attempts" / provider).glob("stage1_*.json")]
        usage[provider] = {"confirmed_input_tokens": sum(a.get("usage", {}).get("actual_input_tokens",0) for a in attempts),
                           "confirmed_output_tokens": sum(a.get("usage", {}).get("actual_output_tokens_including_thinking",0) for a in attempts),
                           "confirmed_usage_cost_usd": run.api.money(sum((Decimal(a.get("usage", {}).get("usage_cost_usd", "0")) for a in attempts), Decimal(0))),
                           "unconfirmed_generation_attempts": sum(not a.get("usage") and a["state"] != "CANCELLED_BEFORE_DISPATCH" for a in attempts)}
        distribution[provider] = dict(sorted(Counter(r["scores"][provider] for r in rows.values() if provider in r["scores"]).items()))
    complete, disputes, per_query = [], [], defaultdict(Counter)
    for row in rows.values():
        if len(row["scores"]) < 3:
            row["status"] = "INCOMPLETE_INDEPENDENT_JUDGMENTS"
            row["relevant"] = None
            continue
        complete.append(row)
        binary = {s >= 3 for s in row["scores"].values()}
        if len(binary) == 1:
            row["status"] = "UNANIMOUS_BINARY_SILVER_CANDIDATE_PENDING_RELEASE_REVIEW"
            row["candidate_relevant"] = next(iter(binary))
        else:
            row["status"] = "BOUNDARY_DISAGREEMENT_NOT_MAJORITY_APPROVED"
            row["candidate_relevant"] = None
            disputes.append(row)
        row["relevant"] = None
        per_query[row["query_id"]]["complete_pairs"] += 1
        per_query[row["query_id"]][row["status"]] += 1
    out = {"status": "ALL_3360_SCORES_COLLECTED_SILVER_RELEASE_PENDING" if len(complete) == 1120 else "INCOMPLETE_STAGE1",
           "expected_pairs":1120,"expected_scores":3360,"received_valid_scores": sum(len(r["scores"]) for r in rows.values()),
           "complete_three_judge_pairs":len(complete),"exact_grade_agreement_numerator":sum(len(set(r["scores"].values()))==1 for r in complete),
           "binary_agreement_numerator":len(complete)-len(disputes),"agreement_denominator":len(complete),
           "boundary_disagreements":disputes,"per_query":dict(per_query),"model_score_distributions":distribution,
           "stage1_only_usage":usage,"records":list(rows.values()),"human_gold":False,"human_validation_count":0,
           "silver_released":False,"stage2_run":False,"stage3_run":False,"stage4_sealed":True}
    run.save(run.OUTPUT / "stage1_summary.json", out)
    return out


if __name__ == "__main__":
    import json
    result = summarize()
    print(json.dumps({k:result[k] for k in ("status","received_valid_scores","complete_three_judge_pairs","binary_agreement_numerator","stage1_only_usage")},ensure_ascii=False))
