#!/usr/bin/env python3
"""Turn three frozen-v2.3 BLIND AI ratings into fully traceable DEV SILVER qrels.

This is AI consensus, not human adjudicated Gold. No v2.2 scores are imported.
"""
import csv, hashlib, json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"data/v2_3"
OUT=BASE/"ground_truth"
CASES=json.loads((BASE/"main_cases_v2_3.json").read_text(encoding="utf-8"))
QS=json.loads((BASE/"dev_query_candidates_v2_3.json").read_text(encoding="utf-8"))["queries"]
CASEMAP={c["case_id"]:c for c in CASES["cases"]}
QMAP={q["query_id"]:q for q in QS}
EXPECTED={(q["query_id"],p["id"],cid) for q in QS for p in q["draft_perspectives"] for cid in CASEMAP}
assert len(CASEMAP)==84 and len(QMAP)==10 and len(EXPECTED)==2520
assert CASES["status"]=="FROZEN_SOURCE_ADJUDICATED_NOT_GROUND_TRUTH"

def read_csv(path):
    with path.open(encoding="utf-8",newline="") as f:return list(csv.DictReader(f))

def write_csv(path,rows,fields):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore");w.writeheader();w.writerows(rows)

scores={}
manifests=[]
for pid in (1,2,3):
    run={}
    for qid in sorted(QMAP):
        p=OUT/f"v23-gt-{qid}-p{pid}"
        manifest=json.loads((p/"manifest.json").read_text(encoding="utf-8"))
        rs=read_csv(p/"ratings.csv")
        assert manifest["pass_id"]==pid and manifest["query_id"]==qid
        assert manifest["corpus_git_blob"]=="1705888f3338b219d3715fe4422641865c3075e2"
        assert manifest["previous_scores_supplied_to_model"] is False
        assert manifest["judgments"]==252 and len(rs)==252
        manifests.append(manifest)
        for x in rs:
            key=(x["query_id"],x["perspective_id"],x["case_id"])
            assert key in EXPECTED and key not in run and x["status"]=="V23_AI_BLIND_DRAFT_NOT_HUMAN_GOLD"
            score=int(x["provisional_relevance_0_4"])
            assert 0<=score<=4 and x["evidence_reason"].strip()
            run[key]=x
    assert set(run)==EXPECTED
    scores[pid]=run
assert len({x["prompt_sha256"] for x in manifests})==1
assert len({x["model_requested"] for x in manifests})==1

labels=[]
human_review=[]
for key in sorted(EXPECTED):
    q,p,c=key
    ss=[int(scores[i][key]["provisional_relevance_0_4"]) for i in (1,2,3)]
    median=sorted(ss)[1]
    flips=len({v>=3 for v in ss})>1
    exact=len(set(ss))==1
    near=max(ss)-min(ss)>=2
    chosen=next(i for i in (1,2,3) if ss[i-1]==median)
    evidence=scores[chosen][key]["evidence_reason"]
    status="AI_SILVER_UNANIMOUS" if exact else ("AI_SILVER_RELEVANCE_DISPUTE" if flips else "AI_SILVER_GRADE_DISPUTE")
    case=CASEMAP[c]
    row=dict(query_id=q,perspective_id=p,case_id=c,
             relevance_0_4=median,gold_relevant_flag=int(median>=3),
             judgment_status=status,provenance="AI_THREE_PASS_MEDIAN_NOT_HUMAN_GOLD",
             score_pass1=ss[0],score_pass2=ss[1],score_pass3=ss[2],
             exact_agreement=int(exact),threshold_flip=int(flips),
             needs_researcher_review=int(flips or near),
             evidence_reason=evidence,
             evidence_basis="QUERY_PERSPECTIVE_CASE_PROBLEM_TASK_CONTEXT_ONLY",
             judge_model=scores[chosen][key]["model_id"],
             response_id=scores[chosen][key]["response_id"],
             query_source="data/v2_3/dev_query_candidates_v2_3.json",
             corpus_source="data/v2_3/main_cases_v2_3.json",
             human_approved="FALSE")
    labels.append(row)
    if flips or near:
        human_review.append({
            "query_id":q,"perspective_id":p,"case_id":c,
            "business_problem_query":QMAP[q]["business_problem_query"],
            "perspective_title":next(v["title"] for v in QMAP[q]["draft_perspectives"] if v["id"]==p),
            "case_problem":case["problem"],"case_task":case["task"],"case_context":case["context"],
            "blind_human_score_0_4":"","reviewer_id":"","status":"UNJUDGED_HUMAN_REVIEW_OPTIONAL"
        })

labels_fields=["query_id","perspective_id","case_id","relevance_0_4","gold_relevant_flag",
    "judgment_status","provenance","score_pass1","score_pass2","score_pass3",
    "exact_agreement","threshold_flip","needs_researcher_review","evidence_reason",
    "evidence_basis","judge_model","response_id","query_source","corpus_source","human_approved"]
write_csv(OUT/"silver_dev_qrels_2520.csv",labels,labels_fields)
write_csv(OUT/"optional_blind_researcher_review.csv",human_review,
 ["query_id","perspective_id","case_id","business_problem_query","perspective_title",
  "case_problem","case_task","case_context","blind_human_score_0_4","reviewer_id","status"])
counts=Counter(x["relevance_0_4"] for x in labels)
by_qp=defaultdict(list)
for x in labels:by_qp[(x["query_id"],x["perspective_id"])].append(x)
perspectives=[]
for (q,p),v in sorted(by_qp.items()):
    strong=[x for x in v if x["gold_relevant_flag"]]
    perspectives.append({"query_id":q,"perspective_id":p,"n_candidates":len(v),
        "silver_relevant_count":len(strong),
        "relevant_ids":"|".join(x["case_id"] for x in strong),
        "unanimously_positive_count":sum(x["score_pass1"]>=3 and x["score_pass2"]>=3 and x["score_pass3"]>=3 for x in strong),
        "threshold_disagreements":sum(x["threshold_flip"] for x in v),
        "answerable_by_ai_silver":bool(strong),
        "status":"AI_SILVER_QUERY_PERSPECTIVE_NOT_HUMAN_GOLD"})
write_csv(OUT/"perspective_answerability.csv",perspectives,
 ["query_id","perspective_id","n_candidates","silver_relevant_count","relevant_ids",
  "unanimously_positive_count","threshold_disagreements","answerable_by_ai_silver","status"])
strategy_candidates=[]
for q in QS:
    relevant={r["case_id"] for r in labels if r["query_id"]==q["query_id"] and r["gold_relevant_flag"]}
    union=sorted({s for cid in relevant for s in CASEMAP[cid]["strategy_labels"]})
    strategy_candidates.append({"query_id":q["query_id"],"suggested_strategy_set":"|".join(union),
       "candidate_positive_case_count":len(relevant),
       "status":"AI_SILVER_DERIVED_FROM_RELEVANT_CASE_STRATEGY_NOT_INDEPENDENT_GOLD",
       "human_approved":"FALSE"})
write_csv(OUT/"strategy_set_candidates.csv",strategy_candidates,
 ["query_id","suggested_strategy_set","candidate_positive_case_count","status","human_approved"])

# Human pilot is a DIFFERENT v2.2 snapshot; benchmark only, never auto-merged.
old_pilot=ROOT/"data/v2_2/qa/researcher_first_pass_2026-10-23/researcher_first_pass_50.csv"
human=[]
for r in read_csv(old_pilot):
    present=r["case_id"] in CASEMAP
    matching=[x for x in labels if x["query_id"]==r["query_id"] and x["case_id"]==r["case_id"]
              and next((p for p in QMAP[x["query_id"]]["draft_perspectives"] if p["id"]==x["perspective_id"]),{}).get("title")==r["reference_perspective"]]
    if present:
        assert len(matching)==1
        x=matching[0]
        changed=any(CASEMAP[r["case_id"]][k]!=r["case_"+k] for k in ("problem","task","context"))
        v23score=x["relevance_0_4"]
        disagree=int((int(r["human_score_0_4"])>=3)!=(int(v23score)>=3))
    else:
        assert not matching
        changed=False
        v23score=""
        disagree=""
    human.append({"review_id":r["review_id"],"query_id":r["query_id"],
        "case_id":r["case_id"],"reference_perspective":r["reference_perspective"],
        "v22_researcher_score_0_4":r["human_score_0_4"],
        "v23_ai_silver_score":v23score,"v23_included":int(present),
        "input_changed_between_versions":int(changed),
        "disagreement_3point_threshold":disagree,
        "status":"HISTORIC_RESEARCHER_PILOT_COMPARISON_NOT_V23_GOLD"})
write_csv(OUT/"legacy_human_pilot_comparison.csv",human,
 ["review_id","query_id","case_id","reference_perspective","v22_researcher_score_0_4",
 "v23_ai_silver_score","v23_included","input_changed_between_versions",
 "disagreement_3point_threshold","status"])

meta={"name":"AX_V23_AI_SILVER_DEV_QRELS","created_at_utc":datetime.now(timezone.utc).isoformat(),
 "dataset_version":"2.3.0","corpus_git_blob_sha":"1705888f3338b219d3715fe4422641865c3075e2",
 "status":"COMPLETE_AI_ONLY_SILVER_2520_NOT_HUMAN_GROUND_TRUTH",
 "method":"3 independent blind API re-ratings of frozen 84-case Problem/Task/Context, median with full disagreement flags",
 "sources":{"input_corpus":"data/v2_3/main_cases_v2_3.json",
    "dev_queries":"data/v2_3/dev_query_candidates_v2_3.json",
    "judge_script":"scripts/v23_gt_grade.py",
    "judge_prompt":"scripts/v21_provisional_ai_ground_truth.py::SYSTEM",
    "raw_runs":"ground_truth/v23-gt-V21D001..010-p1..p3"},
 "counts":{"cases":84,"dev_questions":10,"dev_perspectives":30,"judgments":len(labels),
    "ai_api_grades":len(labels)*3,"all_passes_exact":sum(x["exact_agreement"] for x in labels),
    "threshold_flips":sum(x["threshold_flip"] for x in labels),
    "optional_review_queue":len(human_review),"v22_human_pilot_count":len(human),
    "v22_human_pilot_v23_included":sum(x["v23_included"] for x in human),
    "v22_human_vs_v23_ai_binary_disagree":sum(int(x["disagreement_3point_threshold"]) for x in human if x["v23_included"]),
    "human_approved_v23":0,"silver_score_histogram":{str(k):v for k,v in sorted(counts.items())},
    "empty_silver_perspectives":sum(not p["answerable_by_ai_silver"] for p in perspectives)},
 "model_requested":manifests[0]["model_requested"],
 "model_ids_observed":sorted({r["model_id"] for pid in scores for r in scores[pid].values()}),
 "prompt_sha256":manifests[0]["prompt_sha256"],
 "cautions":["No human reviewed v2.3 qrels; do not call this validated Gold.",
  "Median and repeated outputs do not establish factual correctness.",
  "v2.2 human 50 were chosen for disagreement; comparator is not representative.",
  "v2.3 corpus taxonomy and extra cases selected using prior Dev coverage; Dev estimates are not held-out Test.",
  "Threshold-flip cases cannot be silently declared unambiguous positives or negatives.",
  "Reference perspectives are draft and for evaluation only; never passed into retrieval model.",
  "Strategy set union is a dependent candidate, not independently adjudicated query strategy Gold."]}
(OUT/"silver_release_manifest.json").write_text(json.dumps(meta,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
report=f"""# AX v2.3 개발용 AI-Silver 평가정답(후보) — 자동검증 결과
**상태: AI-only SILVER; 인간 Ground Truth 아님.** 코퍼스 84개 × Dev 질문 10 × 관점 3 = **2520개**를 새 동결본 기준으로 독립 3회 블라인드 채점했음.

- 실제 AI 점수: **7560개**, 2520키 전수 중복·누락 없음.
- 완전 동일 점수: **{meta['counts']['all_passes_exact']}개**
- '관련 있음' 기준 3점 이상 뒤집힘: **{meta['counts']['threshold_flips']}개**
- 점수 분포: **{meta['counts']['silver_score_histogram']}**
- 우선 인간 검토 후보(상충/큰 점수차): **{meta['counts']['optional_review_queue']}개**
- 이전 v2.2 연구자 50개와 동일한 코퍼스/관점이라는 가정 없이 **비교 진단만** 보존.
- Silver 기준 양성 0개 관점: **{meta['counts']['empty_silver_perspectives']}개**; 없는 관련 사례를 임의 만들어 채우지 않음.

각 평가행은 3회 점수, 중앙값, AI판정 이유, 모델 응답 ID, 인간 승인 아님 표식을 가짐. 질문별 Strategy Set은 대응 사례의 전략을 합쳐 만든 후보라 인간·독립 정답으로 주장할 수 없음.

**논문:** 개발 진행을 위한 'LLM-assisted silver relevance labels'로 기술 가능. 사람의 독립 판정으로 인정되는 'Gold Ground Truth'라고 기재하거나 이 데이터의 자체 성능을 최종 Test 품질로 주장하면 안 됨.
"""
(OUT/"README.md").write_text(report,encoding="utf-8")
assert len(labels)==2520 and len(perspectives)==30 and len(strategy_candidates)==10 and len(human)==50
print(json.dumps(meta["counts"],ensure_ascii=False),flush=True)
