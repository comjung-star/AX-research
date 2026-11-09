import unittest

from ax_research.pilot_catalog_evaluation import metrics, paired_interval


class PilotCatalogEvaluationTests(unittest.TestCase):
    def test_abstention_does_not_hide_missed_positive(self):
        m = metrics([], [], {'a': 3, 'b': 0})
        self.assertEqual(m['F1@5'], 0)
        self.assertEqual(m['nDCG@5'], 0)
        self.assertEqual(m['P@5_slots'], 0)
        self.assertIsNone(m['emitted_precision'])
        self.assertTrue(m['positive_but_empty'])

    def test_actual_output_denominator_and_slots_are_distinct(self):
        m = metrics(['a'], ['a', 'b'], {'a': 3, 'b': 3, 'c': 0})
        self.assertAlmostEqual(m['F1@5'], 2 / 3)
        self.assertEqual(m['P@5_slots'], .2)
        self.assertEqual(m['emitted_precision'], 1)
        self.assertEqual(m['Recall@20_candidates'], 1)

    def test_zero_positive_does_not_create_perfect_score(self):
        m = metrics([], [], {'a': 0, 'b': 1})
        self.assertIsNone(m['F1@5'])
        self.assertIsNone(m['nDCG@5'])
        self.assertEqual(m['P@5_slots'], 0)

    def test_retrieval_and_final_output_recall_are_separate(self):
        m = metrics(['b'], ['b', 'a'], {'a': 2, 'b': 0})
        self.assertEqual(m['Recall@5'], 0)
        self.assertEqual(m['Recall@20_candidates'], 1)

    def test_invalid_sets_are_rejected(self):
        for ranking, candidates in [(['a', 'a'], ['a']), (['a'], []), (['x'], ['x'])]:
            with self.assertRaises(ValueError):
                metrics(ranking, candidates, {'a': 2})

    def test_bootstrap_is_paired_and_reproducible(self):
        self.assertEqual(paired_interval([.2, -.1, 0]), paired_interval([.2, -.1, 0]))
        self.assertEqual(paired_interval([0, 0])['interval95'], [0, 0])
        self.assertIsNone(paired_interval([])['delta'])


if __name__ == '__main__':
    unittest.main()
