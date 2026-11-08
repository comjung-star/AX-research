import unittest

from scripts.autonomous_trial2_mapping_replay import handoff, metrics, restrict


class HandoffTests(unittest.TestCase):
    def test_unique_equal_budget_and_both_sources(self):
        dense = list(range(112))
        sparse = list(reversed(dense))
        candidates = handoff(dense, sparse)
        self.assertEqual(candidates[:4], [0, 111, 1, 110])
        self.assertEqual(len(set(candidates)), 20)

    def test_pointwise_sort_equals_restricted_order(self):
        cases = list(range(112))
        candidates = handoff(cases, list(reversed(cases)))
        score = {case: (case % 7, -case) for case in cases}
        full = sorted(cases, key=score.get)
        self.assertEqual(restrict(full, candidates), sorted(candidates, key=score.get))

    def test_registry_and_duplicate_rejection(self):
        with self.assertRaises(ValueError):
            handoff([1, 1], [1, 2], 2)
        with self.assertRaises(ValueError):
            handoff([1, 2], [1, 2, 2], 2)
        with self.assertRaises(ValueError):
            restrict([1, 2], [3])

    def test_zero_positive_and_known_metrics(self):
        self.assertIsNone(metrics(list(range(20)), dict.fromkeys(range(20), 0))['F1@5'])
        grades = {case: 3 if case == 0 else 0 for case in range(20)}
        self.assertAlmostEqual(metrics(list(range(20)), grades)['F1@5'], 1 / 3)
        self.assertEqual(metrics(list(range(20)), grades)['nDCG@10'], 1)
