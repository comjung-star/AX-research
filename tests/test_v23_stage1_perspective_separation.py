"""Pure Stage1 view-separation evaluation checks (no external model)."""
from collections import OrderedDict

from scripts.v23_stage1_perspective_separation import relevant_union_and_coverage
from ax_research.selection import branch_balanced_unique

def test_global_budget_can_hide_branch_top10_relevant():
    # Three views retrieve a useful case at rank 4 in the last branch. Global Top5
    # can omit it even though it is relevant and retained by separate branch Top5.
    views=OrderedDict([
      ("P1",["A","B","C","D","E","F"]),
      ("P2",["A","C","B","E","F","D"]),
      ("P3",["A","Z","B","C","D","E"]),
    ])
    global5={cid for _,cid in branch_balanced_unique(views,5)}
    separate5=set().union(*(set(v[:5]) for v in views.values()))
    assert "Z" in separate5
    assert len(global5)==5
    assert global5 <= separate5
    assert len(separate5)>len(global5)

def test_duplicate_candidates_preserve_branch_provenance():
    views=OrderedDict([("P1",["A","B","C"]),("P2",["A","B","D"])])
    separated={pid:list(seq[:2]) for pid,seq in views.items()}
    assert separated["P1"][0] == separated["P2"][0] == "A"
    assert len(set().union(*(set(x) for x in separated.values())))==2
    assert len(separated)==2

def test_reference_silver_view_coverage_not_runtime_id_correspondence():
    # Runtime P1 / P2 names must never be assumed aligned with evaluation P1/P2.
    refs={"Q":{"P1":{"A","B"},"P2":{"C"},"P3":{"D"}}}
    recall,coverage,got,total=relevant_union_and_coverage({"A","D"},refs,"Q")
    assert total==4 and got==2
    assert recall==.5
    assert abs(coverage-2/3)<1e-12
