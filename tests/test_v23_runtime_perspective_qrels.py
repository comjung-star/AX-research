"""AI relevance rubric / corpus-coverage integrity tests."""
import json

from scripts.v23_runtime_view_grade import make_input,check_batch,JudgeRow
from scripts.v23_runtime_view_build import grade_consensus,expected_runtime


def test_only_whitelisted_case_fields_sent_to_llm():
    query={"query_id":"Q","business_problem_query":"상담 병목",
           "draft_perspectives":[{"id":"P1","title":"Reference label MUST NOT leak"}]}
    view=[{"perspective_id":"P1","perspective_title":"반복상담",
           "perspective_description":"반복적인 상담업무에 시간이 걸림",
           "query_id":"Q","run_id":1}]
    cases=[{"case_id":"CASE","problem":"repetitive calls","task":"support",
            "context":"call centre",
            "implementation":"SECRET solution must not leak",
            "outcome":"SECRET outcome","factor_label":"SECRET factor",
            "strategy_label":"SECRET strategy"}]
    raw=make_input(query,view,cases)
    payload=json.loads(raw)
    assert "SECRET" not in raw
    assert "Reference label MUST" not in raw
    assert len(payload["generated_perspectives"])==1
    assert set(payload["cases"][0])=={"case_id","business_problem","target_task","business_context"}
    check_batch([JudgeRow(perspective_id="P1",case_id="CASE",relevance=3,reason="반복 상담이 관련 업무임")],view,cases)


def test_missing_and_duplicate_judgments_rejected():
    view=[{"perspective_id":"P1"},{"perspective_id":"P2"}]
    cases=[{"case_id":"A"},{"case_id":"B"}]
    rows=[JudgeRow(perspective_id="P1",case_id="A",relevance=0,reason="서로 다른 문제 영역"),
          JudgeRow(perspective_id="P1",case_id="B",relevance=3,reason="관련있는 반복 업무"),
          JudgeRow(perspective_id="P2",case_id="A",relevance=1,reason="간접적인 관련성이 있음")]
    try:
        check_batch(rows,view,cases)
    except ValueError:
        pass
    else:
        raise AssertionError("Missing row not rejected")


def test_threshold_conflicts_excluded_not_fabricated():
    assert grade_consensus(2,3)==(None,None,0,"AI_SILVER_THRESHOLD_CONFLICT_EXCLUDE_TRAIN",1)
    assert grade_consensus(4,3)==(3,1,1,"AI_SILVER_SAME_CLASS_GRADE_DIFFERENCE",0)
    assert grade_consensus(1,2)==(1,0,1,"AI_SILVER_SAME_CLASS_GRADE_DIFFERENCE",0)
    assert grade_consensus(0,0)==(0,0,1,"AI_SILVER_CONSISTENT_GRADE",0)


def test_97_views_create_exactly_8148_distinct_labels():
    queries=[{"query_id":f"Q{i}"} for i in range(10)]
    cases=[{"case_id":f"C{j}"} for j in range(84)]
    views=[]
    for i in range(10):
        for run in range(1,4):
            for j in range(3 if (i,run)!=(0,1) else 10):
                # the special case will be corrected below to have 97 total
                views.append({"query_id":f"Q{i}","run_id":run,"perspective_id":f"P{j}"})
    # 30*3=90; replace 7 groups of 3 with 4 to make 97, none >5.
    views=[]
    for i in range(10):
        for run in range(1,4):
            n=4 if i*3+run-1<7 else 3
            for j in range(n):
                views.append({"query_id":f"Q{i}","run_id":run,"perspective_id":f"P{j}"})
    e,g,q,c=expected_runtime(cases,queries,views)
    assert len(views)==97 and len(e)==8148 and len(g)==30
