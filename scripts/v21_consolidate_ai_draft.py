#!/usr/bin/env python3
"""Validate and report the full blind v2.1 AI draft, never a human GT."""
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"data/v2_1"
DIR=BASE/"qa/ai_provisional_2026-10-23"

def read_csv(p):
    with p.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))

def write_csv(p,rows):
    with p.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]))
        w.writeheader();w.writerows(rows)

def main():
    cases=json.loads((BASE/"main_cases_v2_1.json").read_text())["cases"]
    qs=json.loads((BASE/"dev_query_candidates_v2_1.json").read_text())["queries"]
    assert len(cases)==91 and len(qs)==10
    cmap={c["case_id"]:c for c in cases}
    expected={(q["query_id"],p["id"],c["case_id"])
              for q in qs for p in q["draft_perspectives"] for c in cases}
    rows=[]
    for q in qs:
        qid=q["query_id"]
        paths=[p for p in DIR.glob("*/provisional_ai_relevance.csv") if p.parent.name.endswith(qid)]
        if len(paths)!=1:raise ValueError(f"Missing/duplicate {qid} batch {paths}")
        meta=json.loads((paths[0].parent/"ai_judgment_manifest.json").read_text())
        if meta["judgment_count"]!=273 or meta["cases_in_scope"]!=91 or meta["queries_in_scope"]!=1:
            raise ValueError(f"Incomplete {qid}")
        if meta["human_ground_truth"] or meta["human_approved_labels"] or meta["gold_eligible"]:
            raise ValueError("AI draft must not claim human validation")
        part=read_csv(paths[0])
        if len(part)!=273:raise ValueError(f"Wrong count {qid}")
        for row in part:
            if row["status"]!="AI_DRAFT_NOT_HUMAN_GT" or row["query_id"]!=qid:
                raise ValueError("Invalid label metadata")
            if row["provisional_relevance_0_4"] not in {"0","1","2","3","4"} or not row["evidence_reason"]:
                raise ValueError("Missing score/reason")
            c=cmap[row["case_id"]]
            inp=json.dumps({"problem":c["problem"],"task":c["task"],"context":c["context"]},
                           ensure_ascii=False,sort_keys=True)
            if hashlib.sha256(inp.encode()).hexdigest()!=row["case_input_sha256"]:
                raise ValueError("Case content mismatch")
        raw=list((paths[0].parent/"raw_batches").glob("*.json"))
        if len(raw)!=7:raise ValueError(f"Expected 7 raw prompts {qid}, got {len(raw)}")
        for p in raw:
            v=json.loads(p.read_text())["input_problem_only"]
            if set(v)!={"query_id","business_problem_query","reference_perspectives","cases"}:
                raise ValueError("Potential solution leak")
            if v["business_problem_query"]!=q["business_problem_query"]:
                raise ValueError("Query mismatch")
            if any(set(c)!={"case_id","business_problem","ax_target_task","business_context"} for c in v["cases"]):
                raise ValueError("Case solution leak")
        rows.extend(part)
    keys={(r["query_id"],r["perspective_id"],r["case_id"]) for r in rows}
    if len(rows)!=2730 or keys!=expected or len(keys)!=2730:
        raise ValueError(f"Wrong coverage: {len(rows)}/{len(keys)}/{len(expected)}")
    rows.sort(key=lambda r:(r["query_id"],r["perspective_id"],r["case_id"]))
    write_csv(DIR/"ai_draft_relevance_2730.csv",rows)
    dist=Counter(int(x["provisional_relevance_0_4"]) for x in rows)
    grouped=defaultdict(list)
    for x in rows:grouped[(x["query_id"],x["perspective_id"])].append(x)
    stats=[]
    for q in qs:
        for p in q["draft_perspectives"]:
            count=Counter(int(x["provisional_relevance_0_4"]) for x in grouped[(q["query_id"],p["id"])])
            stats.append(dict(query_id=q["query_id"],perspective_id=p["id"],
                              perspective_name=p["title"],score0=count[0],score1=count[1],
                              score2=count[2],score3=count[3],score4=count[4],
                              provisional_relevant=count[3]+count[4],status="AI_DRAFT_NOT_HUMAN_GT"))
    write_csv(DIR/"by_perspective_summary.csv",stats)
    reviews=[]
    for x in rows:
        reviews.append(dict(query_id=x["query_id"],perspective_id=x["perspective_id"],
                            case_id=x["case_id"],ai_draft_score=x["provisional_relevance_0_4"],
                            ai_reason=x["evidence_reason"],
                            independent_annotator_score="",annotator_reason="",annotator_id="",
                            independent_reviewer_score="",reviewer_reason="",reviewer_id="",
                            final_adjudicated_score="",adjudication_reason="",
                            human_status="UNREVIEWED",ai_response_id=x["response_id"]))
    write_csv(DIR/"human_adjudication_worksheet_2730.csv",reviews)
    border=[dict(priority="P1_BOUNDARY_2_3" if int(x["provisional_relevance_0_4"]) in (2,3)
                     else "P2_DIRECT_4",
                 query_id=x["query_id"],perspective_id=x["perspective_id"],
                 case_id=x["case_id"],ai_score=x["provisional_relevance_0_4"],
                 evidence=x["evidence_reason"],human_decision="")
            for x in rows if int(x["provisional_relevance_0_4"]) in (2,3,4)]
    if border:write_csv(DIR/"review_priority_queue.csv",border)
    empty=[s for s in stats if s["provisional_relevant"]==0]
    manifest=dict(version="v2.1.0",
          status="AI_DRAFT_COMPLETE_NO_HUMAN_GROUND_TRUTH",
          cases=91,queries=10,perspectives=30,judgments=2730,
          human_approved_labels=0,human_ground_truth=False,
          histogram={str(i):dist[i] for i in range(5)},
          score3_or_4=dist[3]+dist[4],threshold_2_or_3=dist[2]+dist[3],
          empty_gold_perspectives=[dict(query_id=x["query_id"],perspective_id=x["perspective_id"]) for x in empty],
          independent_human_review_required=2730,
          unique_response_ids=len({x["response_id"] for x in rows}),
          models=sorted({x["model_id"] for x in rows}),
          prompt_sha256=sorted({x["prompt_sha256"] for x in rows}),
          source_corpus_blob="c2f6899e4cbd3eb5e903fa84766f541684d4aa45",
          checks=["2730_coverage","raw_blind_prompts","case_sha","query_match","no_false_human_approval"],
          statement="For researcher approval AS PROVISIONAL AI DRAFT only; scientific GT requires independent human adjudication")
    (DIR/"v21_ai_draft_manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    report=["# AX v2.1 Ground Truth 예비평가 — 연구자 승인용 결과보고서",
            "","**평가 등급: AI 1차 예비정답 — 인간 검증 완료 Ground Truth 아님.**","",
            "## 개요","",
            "- 고정 실제 운영 AX 사례: 91건",
            "- 개발 평가 질의 10개, 문제관점 초안 30개, 총 2,730개 (질의·관점·사례) 판정",
            "- GPT-6 Luna, 0~4점, Problem / Task / Context만 제공한 Blind 판정",
            "- 이전 v1 Gold·구현·전략·성과·검색 결과는 AI에게 주지 않음",
            "- 각 항목의 판정 근거, 입력 SHA, 원본 응답 ID 저장","",
            "## 예비 점수 분포","","| 점수 | 건수 | 의미 |","|---:|---:|---|"]
    defs=["관련 없음","주변적","부분 관련","강한 관련","직접 관련"]
    for i in range(5):report.append(f"| {i} | {dist[i]} | {defs[i]} |")
    report.extend(["",f"- **잠정 관련 사례 평가(3~4점): {dist[3]+dist[4]}개** (중복 가능한 관점×사례 단위)",
                   f"- **2/3점 경계 검토: {dist[2]+dist[3]}개**",
                   f"- **인간 독립 검증 완료: 0개**","","## 개발 질의·관점별 현황","",
                   "| 질의 | 문제관점 초안 | 3~4점 | 2점 | 0~1점 |","|---|---|---:|---:|---:|"])
    for s in stats:
        report.append(f"| {s['query_id']} | {s['perspective_name']} | {s['provisional_relevant']} | {s['score2']} | {s['score0']+s['score1']} |")
    report.extend(["","## 특이사항 및 신뢰성 한계","",
                   f"- 잠정 관련 사례 0개인 관점: **{len(empty)}개**."])
    for s in empty:report.append(f"  - {s['query_id']} / {s['perspective_name']}")
    report.extend(["- 이 기록은 **단일 모델의 AI 예비평정**이므로 평가자 간 일치도나 사람의 독립 검증을 입증하지 못함.",
                   "- 점수와 근거를 AI가 작성했다는 사실을 밝히고, v2.1의 실제 Recall@K·Strategy Coverage 개선 증거로 사용하지 않음.",
                   "- 과거 Dev 질의 10건은 Held-out 최종 Test가 아님. 새 Test 질의/GT는 별도로 독립 구축해야 함.",
                   "",
                   "## 승인 시 참고할 원본·검토 문서","",
                   "1. ai_draft_relevance_2730.csv — 전체 예비 점수·판정 근거·모델 응답 이력",
                   "2. by_perspective_summary.csv — 질의별 점수 분포",
                   "3. review_priority_queue.csv — 우선 인간 검토 대상(2·3점 경계 및 4점)",
                   "4. human_adjudication_worksheet_2730.csv — 인간 독립평가와 합의를 위한 빈 입력칸",
                   "5. v21_ai_draft_manifest.json — 개수·모델·해시·유효성·검증 한계",
                   "6. 각 쿼리 폴더 raw_batches — AI가 실제로 받은 입력과 출력 원본",
                   "",
                   "## 연구자가 승인할 수 있는 범위","",
                   "**승인 가능:** 이 AI 예비정답지와 검토표를 독립 평가용 *초안*으로 채택한다. 91건 데이터셋은 그대로 유지한다.",
                   "",
                   "**별도 근거 없이는 승인 불가:** 인간 독립 검증 완료, 최종 검색 성능 입증, 논문용 Held-out Test 확정.",
                   "",
                   "### 후속 조치",
                   "인간 평가자가 전체 2,730개 점수의 실제 판정과 근거를 독립적으로 검토한 뒤 통합 Ground Truth를 고정할 수 있다. 우선 경계 사례를 집중 검토하되, 최종 GT 통과 요건은 전체 검토이다."])
    (DIR/"APPROVAL_REPORT.md").write_text("\n".join(report)+"\n",encoding="utf-8")
    print(json.dumps(manifest,ensure_ascii=False,indent=2))

if __name__=="__main__":main()
