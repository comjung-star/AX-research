"""Stage 3-1 Wald arithmetic and leakage-guard data validation tests."""
import math
import pytest

from ax_research.stage3_wald import analyze, bh_adjust, validate_cases


def test_balanced_table_has_null_association():
    records = (
        [("a"+str(i), {"F1"}, {"S1"}, "") for i in range(6)]
        + [("b"+str(i), {"F1"}, {"S2"}, "") for i in range(6)]
        + [("c"+str(i), {"F2"}, {"S1"}, "") for i in range(6)]
        + [("d"+str(i), {"F2"}, {"S2"}, "") for i in range(6)]
    )
    row = analyze(records, ["F1", "F2"], ["S1", "S2"], min_cell=5)[0]
    assert [row[k] for k in (
        "a_factor_and_strategy", "b_factor_no_strategy",
        "c_no_factor_strategy", "d_neither"
    )] == [6, 6, 6, 6]
    assert row["wald_eligible"] is True
    assert math.isclose(row["odds_ratio"], 1)
    assert math.isclose(row["wald_p"], 1)


def test_zero_cell_abstains_without_infinite_wald():
    records = [("c"+str(i), {"F1"}, {"S1"}, "") for i in range(8)]
    records += [("n"+str(i), {"F2"}, {"S2"}, "") for i in range(8)]
    row = analyze(records, ["F1", "F2"], ["S1", "S2"])[0]
    assert row["status"] == "SPARSE_ABSTAIN"
    assert row["wald_p"] == ""
    assert row["bh_q_all_pairs"] == ""


def test_bh_adjust_includes_all_planned_pairs():
    assert bh_adjust([0.01, 0.04, 1.0]) == pytest.approx([0.03, 0.06, 1.0])


def test_unknown_label_rejected():
    rows = [{"case_id": "AX0001", "root_cause_factor": "BAD",
             "strategy": "S1", "source": ""}]
    with pytest.raises(ValueError, match="Unknown"):
        validate_cases(rows, ["F1"], ["S1"])


def test_duplicate_case_rejected():
    rows = [{"case_id": "AX0001", "root_cause_factor": "F1",
             "strategy": "S1", "source": ""}] * 2
    with pytest.raises(ValueError, match="duplicate"):
        validate_cases(rows, ["F1"], ["S1"])
