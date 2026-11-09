import unittest

import numpy as np

from ax_research.pairwise_ridge import fit_pairwise, rank_pool, score, unit


class PairwiseTests(unittest.TestCase):
    def test_holdout_labels_cannot_affect_fit(self):
        x = {'train': np.array([[0., 1.], [1., 0.]]), 'heldout': np.eye(2)}
        y = {'train': [True, False], 'heldout': [True, False]}
        first = fit_pairwise(x, y, ['train'], .1)
        y['heldout'] = [False, True]
        np.testing.assert_array_equal(first, fit_pairwise(x, y, ['train'], .1))
        self.assertGreater(first[1], first[0])

    def test_query_balance_is_invariant_to_duplicated_pairs(self):
        base = np.array([[1., 0.], [0., 1.]])
        x = {'a': base, 'b': base[:, ::-1]}
        y = {'a': [True, False], 'b': [True, False]}
        w = fit_pairwise(x, y, ['a', 'b'], 1.)
        x['a'] = np.repeat(base, 4, axis=0)
        y['a'] = [True] * 4 + [False] * 4
        np.testing.assert_allclose(w, fit_pairwise(x, y, ['a', 'b'], 1.))

    def test_zero_share_preserves_dense_in_pool(self):
        ids = [str(i) for i in range(25)]
        features = np.column_stack([np.arange(25., 0., -1), np.arange(25.)])
        values = score(features, np.array([0., 1.]), 0)
        pool = ids[:19] + [ids[-1]]
        result = rank_pool(ids, values, pool, ids)
        self.assertEqual(result[:20], pool)
        self.assertEqual(set(result), set(ids))

    def test_missing_training_signal_and_constant_features_stay_finite(self):
        np.testing.assert_array_equal(unit([2., 2.]), [0., 0.])
        w = fit_pairwise({'q': np.ones((2, 3))}, {'q': [False, False]}, ['q'], 1.)
        np.testing.assert_array_equal(w, np.zeros(3))


if __name__ == '__main__':
    unittest.main()
