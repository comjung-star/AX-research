from ax_research.selection import branch_balanced_unique


def test_branch_balanced_unique_preserves_branches_and_skips_duplicates():
    branches = {
        "P1": ["A", "B", "C"],
        "P2": ["A", "D", "E"],
        "P3": ["B", "F", "G"],
    }
    selected = branch_balanced_unique(branches, k=6)
    assert selected == [
        ("P1", "A"),
        ("P2", "D"),
        ("P3", "B"),
        ("P1", "C"),
        ("P2", "E"),
        ("P3", "F"),
    ]


def test_branch_balanced_unique_stops_when_candidates_exhausted():
    selected = branch_balanced_unique({"P1": ["A"], "P2": ["A"]}, k=5)
    assert selected == [("P1", "A")]
