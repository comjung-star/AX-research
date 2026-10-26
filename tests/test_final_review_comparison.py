import pytest

from scripts.compare_final_reviews import agreement_statistics


def test_perfect_agreement_has_no_threshold_flips():
    report = agreement_statistics([(0, 0), (1, 1), (3, 3), (4, 4)])
    assert report["exact_agreement"] == report["cohen_kappa"] == report["linear_weighted_kappa"] == 1
    assert report["threshold_flip_count"] == 0


def test_grade_disagreement_does_not_disappear_when_binary_labels_agree():
    report = agreement_statistics([(0, 1), (1, 0), (3, 4), (4, 3)])
    assert report["exact_agreement"] == 0
    assert report["threshold_agreement"] == 1
    assert report["linear_weighted_kappa"] < 1


def test_threshold_flips_are_counted_individually():
    report = agreement_statistics([(2, 3), (4, 1), (0, 0)])
    assert report["threshold_flip_count"] == 2
    assert report["threshold_agreement"] == pytest.approx(1 / 3)


def test_empty_agreement_cannot_be_called_perfect():
    with pytest.raises(ValueError):
        agreement_statistics([])
