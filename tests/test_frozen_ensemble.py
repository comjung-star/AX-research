import unittest
import numpy as np

from ax_research.frozen_ensemble import mean_fold_scores
from ax_research.pairwise_ridge import score


class FrozenEnsembleTests(unittest.TestCase):
    def test_arithmetic_mean_of_individual_normalized_scores(self):
        x = np.array([[.9, .1], [.4, .8], [.1, .2]])
        models = [{'weights': [float(i), 1.], 'learned_share': .5} for i in range(1, 6)]
        before = [dict(m) for m in models]
        expected = sum(score(x, np.array(m['weights']), .5) for m in models) / 5
        np.testing.assert_allclose(mean_fold_scores(x, models), expected)
        self.assertEqual(models, before)

    def test_five_models_and_exact_feature_dimensions_required(self):
        x = np.ones((3, 2))
        with self.assertRaises(ValueError):
            mean_fold_scores(x, [])
        with self.assertRaises(ValueError):
            mean_fold_scores(x, [{'weights': [1.], 'learned_share': .5}] * 5)


if __name__ == '__main__':
    unittest.main()
