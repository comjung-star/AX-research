"""Recover original blind-review artifacts without repeating paid requests.

- Every saved RECEIVED output is re-evaluated from raw receipt.
- A response that had status JUDGED with null grade is preserved in the raw
  response, but marked ABSTAIN in *new recovery output* with explicit flag.
- Missing or corrupt responses become UNJUDGED; NEVER invent a grade.
- Only batches with no prior request/receipt may be newly requested.
- Original labels, source, Test, and models are never modified.
"""
import json,random,sys,hashlib
from pathlib import Path
from decimal import Decimal
from ax_research.heldout import read,write,jsonl,sha
from scripts import stage2_blind_repeat as grader
from scripts import validation123_api as api

ROOT=Path(__file__).resolve().parents[1]
MAX_RESERVE=Decimal(".040")

def row_from_received(qid,round_no,case,raw):
    g=raw.get("grade")
    status=raw.get("status")
    quote=raw.get("task_quote")
    reason=raw.get("reason")
    valid_quote=isinstance(quote,str) and 1<=len(quote)<=140 and quote in case["Task"]
    valid_reason=isinstance(reason,str) and bool(reason.strip())
    valid_grade=(status=="JUDGED" and type(g)==int and g in (0,1,2,3))
    abstained=(status=="ABSTAIN" and g is None)
    valid_id=raw.get("query_id")==qid and raw.get("case_id")==case["case_id"]
    if not valid_id:raise ValueError("Response mismatched case or question ID")
    if valid_quote and valid_reason and (valid_grade or abstained):
        return {"query_id":qid,"case_id":case["case_id"],"grade":g,
            "status":status,"rationale":reason,"task_quote":quote,
            "source":f"IndependentBlindReviewRound{round_no}","recovery_note":None}
    if status in ("JUDGED","ABSTAIN") and g is None and valid_quote and valid_reason:
        return {"query_id":qid,"case_id":case["case_id"],"grade":None,
            "status":"ABSTAIN","rationale":reason,"task_quote":quote,
            "source":f"IndependentBlindReviewRound{round_no}",
            "recovery_note":"RECEIVED_NULL_GRADE_AS_ABSTAIN_RAW_STATUS_PRESERVED"}
    return {"query_id":qid,"case_id":case["case_id"],"grade":None,
        "status":"UNJUDGED","rationale":"Received item could not pass strict evidence/grade schema; raw response preserved",
        "task_quote":quote if valid_quote else "",
        "source":f"IndependentBlindReviewRound{round_no}",
        "recovery_note":"INVALID_RECEIVED_PAYLOAD_UNJUDGED"}

def main(qid,round_no,folder):
    if round_no not in (2,3):raise ValueError("Unexpected round")
    qs={x["query_id"]:x["text"] for x in jsonl(grader.QUESTIONS)}
    cases=read(grader.CASES)["cases"]
    if len(qs)!=20 or len(cases)!=112 or qid not in qs:raise RuntimeError("Source registry mismatch")
    if not folder.is_dir():raise RuntimeError("Missing immutable original review artifact")
    grader.ROUND=round_no
    api.OUT=folder;api.body=grader.body;api.validate=grader.validate
    ids=sorted(cases)
    random.Random(int(qid[2:])*7919+round_no*100003).shuffle(ids)
    records=[];flags=[];new_calls=0
    try:
        for i in range(14):
            part=ids[i*8:(i+1)*8]
            grader.ACTIVE={"query_id":qid,"business_problem":qs[qid],
               "cases":[{"case_id":c,"Problem":cases[c]["problem"],"Task":cases[c]["task"],
                    "Context":cases[c]["context"]} for c in part]}
            name=f"review_{qid}_r{i+1}"
            saved=folder/"api/results"/(name+".json")
            receipt=folder/"api/attempts"/(name+".json")
            raw=folder/"api"/(name+"_response.json")
            rows=None
            if saved.exists():
                d=read(saved)["data"];grader.validate("review",qid,d)
                rows=d["assessments"]
            elif raw.exists():
                if not receipt.is_file():raise RuntimeError("Received output missing audit receipt "+name)
                data=read(raw)
                if data.get("status")!="completed":raise RuntimeError("Incomplete received response "+name)
                try:
                    d=json.loads("".join(c.get("text","") for x in data.get("output",[])
                        for c in x.get("content",[]) if c.get("type")=="output_text"))
                    got=d["assessments"]
                    if not isinstance(got,list):raise ValueError("Not a list")
                except (KeyError,TypeError,ValueError):
                    got=[]
                seen=set();mapped={}
                for record in got:
                    if not isinstance(record,dict):continue
                    cid=record.get("case_id")
                    if cid not in part or cid in seen:
                        flags.append({"batch":i+1,"case_id":cid,"issue":"unknown_or_duplicate_case_in_response"})
                        continue
                    seen.add(cid);mapped[cid]=record
                rows=[]
                for cid in part:
                    if cid in mapped:
                        converted=row_from_received(qid,round_no,grader.ACTIVE["cases"][part.index(cid)],mapped[cid])
                        rows.append(converted)
                        if converted["recovery_note"]:
                            flags.append({"batch":i+1,"case_id":cid,"issue":converted["recovery_note"]})
                    else:
                        rows.append({"query_id":qid,"case_id":cid,"grade":None,
                           "status":"UNJUDGED","rationale":"Missing in received response; no paid replay",
                           "task_quote":"","source":f"IndependentBlindReviewRound{round_no}",
                           "recovery_note":"MISSING_IN_RECEIVED_RESPONSE"})
                        flags.append({"batch":i+1,"case_id":cid,"issue":"MISSING_IN_RECEIVED_RESPONSE"})
                records.extend(rows)
                continue
            elif receipt.exists():
                flags.append({"batch":i+1,"issue":"reserved_or_failed_receipt_not_replayed"})
                for cid in part:
                    records.append({"query_id":qid,"case_id":cid,"grade":None,
                        "status":"UNJUDGED","rationale":"No safe response available; no replay",
                        "task_quote":"","source":f"IndependentBlindReviewRound{round_no}",
                        "recovery_note":"UNRESOLVED_PRIOR_REQUEST"})
                continue
            else:
                upper=Decimal(api.budget()["conservative_spent_or_reserved_usd"])+grader.request_reserve(grader.body("review",qid,i+1))
                if upper>MAX_RESERVE:raise RuntimeError("RECOVERY_QUERY_COST_CAP")
                try:
                    result=api.call("review",qid,i+1)
                    new_calls+=1
                    rows=result["data"]["assessments"]
                except RuntimeError as err:
                    # A newly attempted response can itself be malformed. Preserve
                    # its raw bytes/receipt; use valid items only and quarantine
                    # the rest. No paid retry.
                    flags.append({"batch":i+1,"issue":"NEW_REQUEST_UNRESOLVED","detail":str(err)[:120]})
                    got=[]
                    if raw.exists():
                        data=read(raw)
                        if data.get("status")=="completed":
                            try:
                                obj=json.loads("".join(c.get("text","") for x in data.get("output",[])
                                    for c in x.get("content",[]) if c.get("type")=="output_text"))
                                got=obj.get("assessments",[])
                            except (ValueError,TypeError,KeyError):
                                got=[]
                    validids={};seen=set()
                    for v in got if isinstance(got,list) else []:
                        if not isinstance(v,dict) or v.get("case_id") not in part:continue
                        cid=v["case_id"]
                        if cid in seen:continue
                        seen.add(cid);validids[cid]=v
                    for cid in part:
                        if cid in validids:
                            try:
                                resultrow=row_from_received(qid,round_no,
                                    grader.ACTIVE["cases"][part.index(cid)],validids[cid])
                                records.append(resultrow)
                                if resultrow["recovery_note"]:
                                    flags.append({"batch":i+1,"case_id":cid,"issue":resultrow["recovery_note"]})
                                continue
                            except (TypeError,ValueError,KeyError):
                                pass
                        records.append({"query_id":qid,"case_id":cid,"grade":None,
                             "status":"UNJUDGED","rationale":"Invalid newly received response; original preserved",
                             "task_quote":"","source":f"IndependentBlindReviewRound{round_no}",
                             "recovery_note":"NEW_RECEIVED_INVALID_NO_PAID_REPLAY"})
                    continue
            records.extend({"query_id":r["query_id"],"case_id":r["case_id"],
                "grade":r["grade"],"status":r["status"],"rationale":r["reason"],
                "task_quote":r["task_quote"],"source":f"IndependentBlindReviewRound{round_no}",
                "recovery_note":None} for r in rows)
    finally:
        write(folder/f"recovery_status_{qid}_r{round_no}.json",{
            "qid":qid,"round":round_no,"recovered_records":len(records),
            "distinct_cases":len({r["case_id"] for r in records}),
            "valid_and_abstain_count":sum(r["status"] in ("JUDGED","ABSTAIN") for r in records),
            "unjudged_count":sum(r["status"]=="UNJUDGED" for r in records),
            "abstain_count":sum(r["status"]=="ABSTAIN" for r in records),
            "additional_paid_calls_for_never_requested_batches":new_calls,
            "original_paid_responses_replayed":0,"normalization_audit_flags":flags,
            "source_question_sha256":sha(grader.QUESTIONS),
            "source_case_sha256":sha(grader.CASES),"API_usage":api.budget(),
            "prior_labels_and_ranks_not_read":True,"independent_Test_unread":True})
        if records:write(folder/f"recovery_labels_{qid}_r{round_no}.json",{"records":records})
    if len(records)!=112 or len({r["case_id"] for r in records})!=112:
        raise RuntimeError("Recovered records incomplete")
    print(json.dumps({"qid":qid,"round":round_no,"total":len(records),
       "needs_review":len(flags),"new_calls":new_calls},ensure_ascii=False))
if __name__=="__main__":
    if len(sys.argv)!=4:raise SystemExit("VQ001 ROUND ARCHIVE_FOLDER")
    main(sys.argv[1],int(sys.argv[2]),Path(sys.argv[3]).resolve())
