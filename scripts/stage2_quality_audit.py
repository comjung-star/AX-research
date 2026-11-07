"""Stage2: source-integrity verification, 3 blinded judgments & unresolved queue.
One original judgment + 2 newly independent blinded repeated judgments (same OpenAI model).
Never claim three different providers, human gold or permanent final truth.
"""
import json,math,statistics,sys,hashlib
from collections import Counter,defaultdict
from pathlib import Path
from ax_research.heldout import read,write,jsonl,sha

ROOT=Path(__file__).resolve().parents[1]
CASES=ROOT/"docs/dense-bm25-candidates-2026-10-27/case_registry.json"
QUESTIONS=ROOT/"docs/validation-new20-20261107/questions.jsonl"
FIRST=ROOT/"docs/validation-new20-20261107/measured/labels_new20.json"
PRED=ROOT/"docs/validation-new20-20261107/measured/predictions_new20.json"

def status_norm(x):
    if x["status"]=="JUDGED" and type(x["grade"])==int and x["grade"] in range(4):
        return "JUDGED"
    if x["grade"] is None and x["status"] in ("ABSTAIN","UNJUDGED"):
        return x["status"]
    raise RuntimeError("Inconsistent grade/status")

def read_records(source,qids,caseids,origin,case_data):
    rows=source["records"]
    seen=set();result={}
    for x in rows:
        k=x["query_id"],x["case_id"]
        if k in seen or k[0] not in qids or k[1] not in caseids:
            raise RuntimeError("Unknown or duplicate grade "+origin)
        seen.add(k);status_norm(x)
        quote=x.get("task_quote") or ""
        if x["status"]=="JUDGED" and (not quote or quote not in case_data[k[1]]["task"]):
            raise RuntimeError("Judged Task quotation not verbatim: "+origin+" "+str(k))
        if quote and quote not in case_data[k[1]]["task"]:
            raise RuntimeError("Quote not in Task: "+origin+" "+str(k))
        result[k]=x
    return result

def salvage_paid_raw_output(folder,qid,records,case_data):
    """Re-extract fully valid JSON objects already returned and billed.

    Some Responses API outputs contain TWO output_text JSON messages; joining
    them is invalid, but one may contain a complete eight-case response.
    Never call a model, never infer absent grades, and never choose conflicting
    returned grades silently.
    """
    by={x["case_id"]:dict(x) for x in records}
    changed=[];conflicts=[]
    for path in sorted((folder/"api").glob(f"review_{qid}_r*_response.json")):
        data=read(path)
        if data.get("status")!="completed":continue
        candidates=defaultdict(list)
        for message in data.get("output",[]):
            for content in message.get("content",[]):
                if content.get("type")!="output_text" or not isinstance(content.get("text"),str):continue
                txt=content["text"].strip()
                # Accept a complete JSON object, or a complete first JSON
                # object followed by non-JSON noise, with provenance flagged.
                try:
                    obj=json.loads(txt)
                except (ValueError,TypeError):
                    try:
                        obj,_end=json.JSONDecoder().raw_decode(txt)
                    except (ValueError,TypeError):
                        continue
                if not isinstance(obj,dict) or not isinstance(obj.get("assessments"),list):continue
                for row in obj["assessments"]:
                    if not isinstance(row,dict) or row.get("query_id")!=qid:continue
                    cid=row.get("case_id")
                    if cid not in by or by[cid]["status"]!="UNJUDGED":continue
                    grade=row.get("grade");status=row.get("status")
                    if status!="JUDGED" or type(grade)!=int or grade not in (0,1,2,3):continue
                    quote=row.get("task_quote");reason=row.get("reason")
                    if not isinstance(quote,str) or not quote or quote not in case_data[cid]["task"]:continue
                    if not isinstance(reason,str) or not reason.strip():continue
                    candidates[cid].append(row)
        for cid,valid in candidates.items():
            grades={r["grade"] for r in valid}
            if len(grades)!=1:
                conflicts.append({"case_id":cid,"source":path.name,"returned_grades":sorted(grades)})
                continue
            old=by[cid]
            if old["status"]!="UNJUDGED":continue
            selected=valid[0]
            by[cid]={**old,"status":"JUDGED","grade":selected["grade"],
                "rationale":selected["reason"],"task_quote":selected["task_quote"],
                "recovery_note":"SALVAGED_VALID_JSON_FROM_ALREADY_PAID_RAW_RESPONSE",
                "raw_response_file":path.name}
            changed.append({"case_id":cid,"source":path.name})
    return list(by.values()),changed,conflicts

def main(restored,out):
    if out.exists():raise RuntimeError("No overwrite")
    out.mkdir(parents=True)
    cases=read(CASES)["cases"];qs={q["query_id"]:q["text"] for q in jsonl(QUESTIONS)}
    if len(cases)!=112 or len(qs)!=20:raise RuntimeError("Source inputs changed")
    keys={(q,c) for q in qs for c in cases}
    original=read_records(read(FIRST),set(qs),set(cases),"original",cases)
    if set(original)!=keys:raise RuntimeError("Original 2240 grades incomplete")
    voters={"original":original};usage=[];issues=[]
    for round_no in (2,3):
        rows=[]
        for q in sorted(qs):
            folder=restored/f"stage2-recovered-{q}-r{round_no}"
            path=folder/f"recovery_labels_{q}_r{round_no}.json"
            status=folder/f"recovery_status_{q}_r{round_no}.json"
            if not path.is_file() or not status.is_file():
                issues.append({"qid":q,"round":round_no,"issue":"MISSING_RECOVERED_ARTIFACT"})
                continue
            st=read(status);rr=read(path)["records"]
            if st["source_question_sha256"]!=sha(QUESTIONS) or st["source_case_sha256"]!=sha(CASES):
                raise RuntimeError("Blind reviewer input fingerprints differ")
            if st["prior_labels_and_ranks_not_read"] is not True or st["original_paid_responses_replayed"]!=0 or st["independent_Test_unread"] is not True:
                raise RuntimeError("Unsafe review provenance")
            if len({x["case_id"] for x in rr})!=len(rr) or any(x["query_id"]!=q or x["case_id"] not in cases for x in rr):
                raise RuntimeError("Duplicate/foreign recovered grades")
            # If an earlier recovery stopped at an incomplete paid response,
            # represent never-attempted later chunks as UNJUDGED, not guesses.
            missing=set(cases)-{x["case_id"] for x in rr}
            rr.extend({"query_id":q,"case_id":cid,"grade":None,"status":"UNJUDGED",
                "rationale":"No received label available; no paid replay",
                "task_quote":"","source":f"IndependentBlindReviewRound{round_no}",
                "recovery_note":"MISSING_AFTER_INTERRUPTED_RECOVERY"} for cid in sorted(missing))
            if len(rr)!=112:
                raise RuntimeError("Could not cover all case IDs even as explicit UNJUDGED")
            rr,salvaged,conflicts=salvage_paid_raw_output(folder,q,rr,cases)
            usage.append({"qid":q,"round":round_no,"usd":st["API_usage"]["conservative_spent_or_reserved_usd"],
                "new_requests_after_initial":st["additional_paid_calls_for_never_requested_batches"],
                "normalization_flags":st["normalization_audit_flags"],
                "unjudged_after_salvage":sum(x["status"]=="UNJUDGED" for x in rr),
                "salvaged_from_paid_raw_responses":salvaged,
                "raw_response_label_conflicts":conflicts})
            rows.extend(rr)
        source=read_records({"records":rows},set(qs),set(cases),f"review{round_no}",cases)
        voters[f"round{round_no}"]=source
        if set(source)!=keys:issues.append({"round":round_no,"issue":"NOT_ALL_2240_REVIEWED","count":len(source)})
    if issues:
        write(out/"incomplete_status.json",{"status":"STAGE2_INCOMPLETE","issues":issues,
            "reviewed_per_source":{k:len(v) for k,v in voters.items()},
            "cannot_claim_completed":True})
        raise RuntimeError("Cannot complete stage2 until 40 new blind review files are validated")
    analyzed=[];unresolved=[];strict=0;exact=0;binary_disagreed=0;resolved_majority=0;abstains=0
    per_question=defaultdict(lambda:Counter())
    majority_data=[]
    for q,c in sorted(keys):
        votes=[voters[n][q,c] for n in ("original","round2","round3")]
        gs=[v["grade"] if v["status"]=="JUDGED" else None for v in votes]
        klass=[int(x>=2) if x is not None else None for x in gs]
        rated=[x for x in gs if x is not None]
        if all(x is not None for x in klass) and len(set(klass))==1:strict+=1;per_question[q]["all_binary_same"]+=1
        if all(x is not None for x in gs) and len(set(gs))==1:exact+=1;per_question[q]["all_grade_same"]+=1
        if 0 in klass and 1 in klass:binary_disagreed+=1;per_question[q]["binary_disagreement"]+=1
        if any(x is None for x in gs):abstains+=1;per_question[q]["at_least_one_missing_or_abstain"]+=1
        counts=Counter(x for x in klass if x is not None)
        chosen=None
        if counts and counts.most_common(1)[0][1]>=2:
            winning_class=counts.most_common(1)[0][0]
            wg=[x for x in rated if int(x>=2)==winning_class]
            if len(wg)>=2:
                chosen=sorted(wg)[len(wg)//2] if len(wg)%2 else min(wg)
                resolved_majority+=1
        severe=not(all(x is not None for x in klass) and len(set(klass))==1)
        data={"query_id":q,"case_id":c,"original_grade":gs[0],"review2_grade":gs[1],"review3_grade":gs[2],
            "grades":gs,"binary_votes":klass,"exact_grade_3of3":len(rated)==3 and len(set(rated))==1,
            "unanimous_binary":len(rated)==3 and len(set(klass))==1,
            "provisional_majority_grade":chosen,"needs_independent_adjudication":severe,
            "old_review_reason":votes[0]["rationale"],
            "task_quote_first":votes[0]["task_quote"]}
        analyzed.append(data)
        if severe:unresolved.append(data)
        majority_data.append({"query_id":q,"case_id":c,"grade":chosen,
            "status":"JUDGED" if chosen is not None else "ABSTAIN",
            "rationale":"Triple AI blind review provisional majority; source not expert gold",
            "label_source":"AI-TRIPLE-PROVISIONAL",
            "source_review_flags":severe})
        per_question[q]["total"]+=1
        if chosen is not None and chosen>=2:per_question[q]["majority_relevant"]+=1
        if gs[0] is not None and gs[0]>=2:per_question[q]["original_relevant"]+=1
    write(out/"stage2_independent_grades_all.json",{"records":analyzed,
         "providers":["OpenAI GPT-6 Luna repeated three times; NOT three independent models"],
         "round2_3_blinded_to_recommendations_and_prior_labels":True})
    write(out/"stage2_disagreement_queue.json",{"records":unresolved,"human_gold":False,
         "status":"REQUIRES_INDEPENDENT_ADJUDICATION","count":len(unresolved)})
    write(out/"stage2_consensus_provisional.json",{"records":majority_data,"human_gold":False,
         "not_independent_providers":True,"majority_with_unresolved_flags":True})
    from scripts.validation20_compare import main as compare
    results={}
    for label,source in [("original",voters["original"]),("round2",voters["round2"]),("round3",voters["round3"])]:
        cleaned=[]
        for q,c in sorted(keys):
            x=source[q,c];cleaned.append({"query_id":q,"case_id":c,"grade":x["grade"],
                "status":"JUDGED" if x["status"]=="JUDGED" else "ABSTAIN"})
        sf=out/("analysis_ratings_"+label+".json")
        write(sf,{"records":cleaned})
        mf=out/("metrics_"+label+".json")
        compare(PRED,sf,mf)
        results[label]=read(mf)
    sf=out/"analysis_ratings_consensus.json"
    write(sf,{"records":majority_data})
    mf=out/"metrics_consensus_provisional.json"
    compare(PRED,sf,mf);results["consensus"]=read(mf)
    merged={
        "state":"STAGE2_THREE_BLIND_AI_PASSES_COMPLETE_WITH_UNRESOLVED_QUEUE",
        "graded_pairs":2240,"total_vote_slots":6720,
        "actual_JUDGED_votes":sum(v["status"]=="JUDGED" for source in voters.values() for v in source.values()),
        "abstained_or_missing_votes":sum(v["status"]!="JUDGED" for source in voters.values() for v in source.values()),
        "salvaged_from_paid_responses_count":sum(len(x["salvaged_from_paid_raw_responses"]) for x in usage),
        "three_rounds_same_provider":True,
        "no_human_or_three_distinct_model_consensus":True,"source_registry_cases":112,
        "cases_missing_proven_task":sum(not x["task"].strip() for x in cases.values()),
        "cases_missing_context":sum(not x["context"].strip() for x in cases.values()),
        "cases_missing_evidence_ids":sum(not x.get("evidence_ids") for x in cases.values()),
        "source_task_quotes_checked":True,
        "exact_grade_agreement_pairs":exact,"all_three_agree_on_binary_relevance":strict,
        "binary_disagreement_pairs":binary_disagreed,"any_abstain_or_unjudged_pairs":abstains,
        "majority_provisional_grade_pairs":resolved_majority,"needs_independent_adjudication_pairs":len(unresolved),
        "per_question":dict(per_question),"costs":usage,
        "metric_sensitivity":{k:{"evaluable":v["evaluable_query_count"],
            "F1@5":{s: v["model"][s]["F1@5"] for s in ("E","I2","I3")},
            "nDCG@10":{s:v["model"][s]["nDCG@10"] for s in ("E","I2","I3")}}
            for k,v in results.items()},
        "original_labels_sha256":sha(FIRST),"original_frozen_predictions_sha256":sha(PRED),
        "independent_Test_unread":True,"original_labels_untouched":True,
        "conclusion":"This is a completed automated three-vote quality audit, NOT a verified human gold standard."}
    write(out/"stage2_verification_summary.json",merged)
    flagged=[x for x in unresolved if x["query_id"] in ("VQ015","VQ019","VQ020","VQ006")]
    lines=["# AX 정답 데이터 3회 블라인드 평가 품질 점검",
        "","## 판단","기존 1회와 새로 실시한 2회의 독립 실행 채점은 완료. 모두 동일한 OpenAI 모델이어서 3종 LLM/전문가 정답은 아님.",
        "","- 전체 질문×사례: **2,240쌍**",f"- 총 평가 대상: **6,720칸** (실제 확정 판정 {merged['actual_JUDGED_votes']}건)",
        f"- 3회가 관련/비관련 판정을 모두 일치시킨 쌍: **{strict}/2240**",
        f"- 관련/비관련 판정이 불일치한 쌍: **{binary_disagreed}**",
        f"- 한 번 이상 보류 또는 미판정인 쌍: **{abstains}**",
        f"- 외부 독립 판정 재검토 필요 목록: **{len(unresolved)}쌍**",
        "","## 모델 점수 변화 가능성 (동일한 기존 검색 결과, 채점 기준만 변경)",
        "| 채점 | E F1@5 | I2 F1@5 | I3 F1@5 | 점수 계산 가능한 질문 |",
        "|---|---:|---:|---:|---:|"]
    for key,name in (("original","기존 AI 평가"),("round2","추가 2회차"),("round3","추가 3회차"),("consensus","임시 다수 의견")):
        m=merged["metric_sensitivity"][key]
        lines.append("| "+name+" | "+" | ".join(
            "평가 불가" if m["F1@5"][s] is None else f'{m["F1@5"][s]*100:.2f}%'
            for s in ("E","I2","I3"))+f' | {m["evaluable"]["E"]} |')
    lines.extend(["","## 유의 사항","동일 AI를 반복했으므로 다수 의견도 전문가 정답이 아니다. 보류와 의견 불일치는 추측으로 채우지 않았으며, 최종 독립 Test는 열거나 수정하지 않았다.",
        "","## 저장 파일","- stage2_verification_summary.json","- stage2_disagreement_queue.json","- stage2_independent_grades_all.json","- stage2_consensus_provisional.json","- metrics_original/round2/round3/consensus_provisional.json"])
    (out/"README.md").write_text("\n".join(lines)+"\n",encoding="utf8")
    print(json.dumps({"state":merged["state"],"three_agree":strict,
       "disagree":binary_disagreed,"any_missing_or_abstain":abstains,
       "review_needed":len(unresolved),"sensitivity":merged["metric_sensitivity"]},ensure_ascii=False,indent=2))

if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("stage2_quality_audit.py RECOVERED_ARTIFACT_DIR OUTPUT_DIR")
    main(Path(sys.argv[1]),Path(sys.argv[2]))
