import pytest
from scripts import query_isolated_retrieval as r


def test_metrics_publish_numerators_and_full_relevant_denominator():
    m=r.point_metrics(["a","b","x","y","z"],{"a","b","c"},5)
    assert m["true_positives"]==2
    assert m["precision_denominator"]==5
    assert m["recall_denominator"]==3
    assert m["precision"]==.4
    assert m["recall"]==pytest.approx(2/3)
    assert m["f1"]==.5


def test_no_positive_query_is_preserved_with_explicit_macro_denominators():
    rows=[]
    for relevant in ({"c0"},set()):
        ranking=[f"c{i}" for i in range(20)]
        rows.append({"metrics":{str(k):r.point_metrics(ranking,relevant,k) for k in r.K_VALUES}})
    out=r.aggregate(rows)["5"]
    assert out["precision_query_denominator"]==2
    assert out["recall_query_denominator"]==1
    assert out["f1_query_denominator"]==1
    assert out["zero_relevant_queries"]==1


def test_unresolved_silver_prevents_any_model_or_ranking_work(tmp_path,monkeypatch):
    monkeypatch.setattr(r.run,"OUTPUT",tmp_path)
    (tmp_path/"silver_release.json").write_text('{"approved":false,"unresolved_pairs":1,"human_gold":false}',encoding="utf-8")
    monkeypatch.setattr(r,"create_encoder",lambda:pytest.fail("Model must not start before Silver gate"))
    with pytest.raises(ValueError,match="zero unresolved"):
        r.stage2()


def test_same_ptc_information_no_outcome_or_implementation_enters_any_view():
    single,views=r.input_texts([{"problem":"P","task":"T","context":"C","implementation":"SECRET_IMPL","outcome":"SECRET_OUTCOME"}])
    assert single==["[PROBLEM] P\n[TASK] T\n[CONTEXT] C"]
    assert views=={"problem":["[PROBLEM] P"],"task":["[TASK] T"],"context":["[CONTEXT] C"]}


def test_duplicate_or_under_budget_rankings_are_refused():
    with pytest.raises(ValueError,match="budget"):
        r.point_metrics(["a"]*5,{"a"},5)
