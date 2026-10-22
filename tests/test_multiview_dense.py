import pytest

from ax_research.retrieval.multiview_dense import weighted_view_score


def test_weighted_view_score_equal_mean():
    score = weighted_view_score(
        0.9,
        0.6,
        0.3,
        {
            "business_problem": 1 / 3,
            "ax_target_task": 1 / 3,
            "business_context": 1 / 3,
        },
    )
    assert score == pytest.approx(0.6)


def test_weighted_view_score_normalizes_weights():
    score = weighted_view_score(
        0.9,
        0.6,
        0.3,
        {
            "business_problem": 2,
            "ax_target_task": 1,
            "business_context": 1,
        },
    )
    assert score == pytest.approx(0.675)


def test_weighted_view_score_rejects_nonpositive_total():
    with pytest.raises(ValueError):
        weighted_view_score(
            0.9,
            0.6,
            0.3,
            {
                "business_problem": 0,
                "ax_target_task": 0,
                "business_context": 0,
            },
        )
