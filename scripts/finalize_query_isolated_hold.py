"""Reproduce offline audit tables and conservative interruption accounting."""
import hashlib
import json
from collections import Counter
from decimal import Decimal

from scripts import query_isolated_revalidation as run
from scripts.summarize_query_isolated_pilot import summarize as pilot_summary
from scripts.summarize_query_isolated_stage1 import summarize as stage1_summary


def text_file(path,content):
    if any(secret and secret in content for secret in (run.api.read_key(s["key_env"]) for s in run.api.CONFIG["models"].values())):
        raise ValueError("Sensitive value rejected")
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(content,encoding="utf-8")


def finish():
    pilot=pilot_summary(); full=stage1_summary()
    versions=[run.PREVIOUS_OUTPUT]+[run.PREVIOUS_OUTPUT/f"format-v{n}" for n in (4,5,6,7,8)]
    report={"status":"METHOD_RELIABILITY_HOLD","account_balance_queried":False,"automatic_topup":False,
            "prices_usd_per_million":{"openai":{"input":"0.10","output":"0.50"},"gemini":{"input":"0.30","output":"2.50"},"claude":{"input":"1.00","output":"5.00"}},
            "price_sources":["https://developers.openai.com/api/docs/models/gpt-6-luna","https://ai.google.dev/gemini-api/docs/pricing","https://platform.claude.com/docs/en/models/haiku-4-5/overview"],
            "providers":{},"interrupted_reservations":[],"version_audit":{}}
    for provider in run.CONFIG["models"]:
        attempts=[]
        for version in versions:
            records=[]
            for path in (version/"attempts"/provider).glob("*.json"):
                a=run.api.read_json(path);records.append(a);attempts.append(a)
                if a["state"]=="RESERVED":
                    report["interrupted_reservations"].append({"provider":provider,"file":str(path.relative_to(run.ROOT)).replace("\\","/"),"reserved_usd":a["reserved_usd"],"status":"UNKNOWN_DISPATCH_AND_BILLING_KEEP_FULL_RESERVATION_NO_AUTOMATIC_REPLAY"})
            report["version_audit"].setdefault(str(version.relative_to(run.ROOT)).replace("\\","/"),{})[provider]={"confirmed_responses":sum(bool(a.get("usage")) for a in records),"cost_usd":run.api.money(sum((Decimal(a.get("usage",{}).get("usage_cost_usd","0")) for a in records),Decimal(0))),"format_errors":dict(Counter(e for a in records for e in a.get("validation",{}).get("format_errors",[])))}
        actual=sum((Decimal(a.get("usage",{}).get("usage_cost_usd","0")) for a in attempts),Decimal(0))
        conservative=sum((Decimal(a.get("usage",{}).get("usage_cost_usd",a["reserved_usd"])) for a in attempts),Decimal(0))
        report["providers"][provider]={"confirmed_input_tokens":sum(a.get("usage",{}).get("actual_input_tokens",0) for a in attempts),"confirmed_output_tokens":sum(a.get("usage",{}).get("actual_output_tokens_including_thinking",0) for a in attempts),"confirmed_generation_responses":sum(bool(a.get("usage")) for a in attempts),"confirmed_cost_usd":run.api.money(actual),"actual_plus_uncertain_reserved_usd":run.api.money(conservative),"uncertain_reserved_usd":run.api.money(conservative-actual),"pilot_all_revisions_cost_usd":pilot["usage"][provider]["usage_cost_usd"],"stage1_confirmed_cost_usd":full["stage1_only_usage"][provider]["confirmed_usage_cost_usd"]}
    claude_bound=Decimal(report["providers"]["claude"]["actual_plus_uncertain_reserved_usd"])+Decimal(run.CONFIG["claude_prior_known_usage_usd"])
    report["claude_initial_credit_reported_usd"]="5.00"
    report["claude_prior_known_usage_usd"]=run.CONFIG["claude_prior_known_usage_usd"]
    report["claude_prior_plus_this_work_conservative_usd"]=run.api.money(claude_bound)
    report["claude_bookkeeping_credit_remaining_lower_bound_usd"]=run.api.money(Decimal("5")-claude_bound)
    report["claude_after_safety_buffer_available_lower_bound_usd"]=run.api.money(Decimal("4.5")-claude_bound)
    report["stage3_generation_calls"]=0
    report["total_confirmed_cost_usd"]=run.api.money(sum((Decimal(p["confirmed_cost_usd"]) for p in report["providers"].values()),Decimal(0)))
    report["total_actual_plus_uncertain_reserved_usd"]=run.api.money(sum((Decimal(p["actual_plus_uncertain_reserved_usd"]) for p in report["providers"].values()),Decimal(0)))
    run.save(run.OUTPUT/"pipeline_cost_report.json",report)
    plan=run.api.read_json(run.OUTPUT/"plan.json")
    manifest=[]
    for job in plan["pilot_jobs"]+plan["stage1_jobs"]+plan["stage3_count_jobs"]:
        for provider in run.CONFIG["models"]:
            hashes={name:hashlib.sha256(json.dumps(run.request_body(provider,job,counting),ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()).hexdigest() for name,counting in (("count_request_body_sha256",True),("generation_request_body_sha256",False))}
            manifest.append({"provider":provider,"job_id":job["job_id"],"phase":job["phase"],"prompt_sha256":job["prompt_sha256"],**hashes})
    run.save(run.OUTPUT/"request_manifest.json",{"scope":"V8_CANONICAL_REQUEST_BODIES_NO_HEADERS_OR_KEYS; stage3 generation hashes describe unexecuted plans","requests":manifest})
    for rel,expected in plan["input_sha256"].items():
        if hashlib.sha256((run.ROOT/rel).read_bytes()).hexdigest()!=expected:
            raise ValueError("Frozen input changed")
    headers=["# 동일40쌍 원점수 비교\n","GPT / Gemini / Claude 순서. 과거 v2는 질문 혼동이 발견된 무효 파일럿이므로 정확도 개선의 기준 정답이 아니다. 새 v8 점수도 최종 Silver 미승인이다. O=원질문, R=참조관점.\n","|질문|범위/관점|사례|기존|수정 v8|새 관련 여부 일치|","|---|---|---|---|---|---|"]
    def line(r):
        old="/".join(str(r["old_scores"][p]) for p in run.CONFIG["models"])
        new="/".join(str(r["new_scores"][p]) for p in run.CONFIG["models"])
        same=len({s>=3 for s in r["new_scores"].values()})==1
        return f"|{r['query_id']}|{r['perspective_id'] or 'O'}|{r['case_id']}|{old}|{new}|{'일치' if same else '불일치·미승인'}|"
    text_file(run.OUTPUT/"comparison40.md","\n".join(headers+[line(r) for r in pilot["comparisons"]])+"\n")
    text_file(run.OUTPUT/"original12.md","\n".join(["# 과거 경계 불일치12건의 변경\n","수정 후 11건은 관련 여부가 같아졌고 1건은 남았다. 일치가 정답 승인이나 정확성을 뜻하지 않는다.\n"]+headers[2:]+[line(r) for r in pilot["original_12_boundary_disagreements"]])+"\n")
    case_map={r["case_id"]:r for r in run.api.read_csv(run.DATA/"dev_problem_views.csv")}
    chosen={"AXV24_bc6444cc1b61":"RULE_ADHERENCE_FAILURE_SHARED_MANUAL_CAPACITY_IS_NOT_DIRECT_INQUIRY_TASK","AXV2P2_0048_01":"UNSTATED_SUPPORT_BENEFIT_AND_TECHNOLOGY_IN_REASON; SCORE4_NOT_SUPPORTED_BY_INPUT","AXV2H_0002_01":"DIRECT_TASK_VS_SUPPORTING_SUMMARIZATION_BOUNDARY","AXV2N_0130":"DIRECT_INQUIRY_VS_SUPPORT_ADMINISTRATION_BOUNDARY","AXV2N_0138":"RECIPIENT_ROLE_TASK_EQUIVALENCE_NORMAL_DISAGREEMENT"}
    findings=[]
    for row in full["records"]:
        if row["query_id"]=="V21D001" and row["case_id"] in chosen:
            findings.append({**row,"classification":chosen[row["case_id"]],"input_ptc":{f:case_map[row["case_id"]][f] for f in ("problem","task","context")},"agent_analysis_not_human_gold":True,"corrected_grade_assigned":False})
    run.save(run.OUTPUT/"methodology_findings.json",{"status":"HOLD_NO_LABEL_REPAIRS_OR_MAJORITY_APPROVAL","examples":findings,"all_other_disagreements":len(full["boundary_disagreements"]),"full_semantic_review_of_all_872_scores_completed":False})
    run.save(run.OUTPUT/"final_status.json",{"status":"METHOD_RELIABILITY_HOLD","pilot":"COMPLETE_40_PAIRS_120_RAW_GRADES","stage1":"INCOMPLETE_872_OF_3360_RAW_GRADES_NO_APPROVED_SILVER","stage2":"NOT_EXECUTED_PREPARED_CODE_ONLY","stage3":"NOT_EXECUTED_ZERO_DYNAMIC_GENERATION_CALLS","stage4":"SEALED_NOT_EXECUTED","human_gold":False,"approved_silver_pairs":0,"new_api_calls_allowed":False,"frozen_input_hashes_unchanged":True})
    return report


if __name__=="__main__":
    r=finish();print(json.dumps({k:r[k] for k in ("total_confirmed_cost_usd","total_actual_plus_uncertain_reserved_usd","claude_bookkeeping_credit_remaining_lower_bound_usd")},ensure_ascii=False))
