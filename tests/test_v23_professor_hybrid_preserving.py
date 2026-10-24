"""Unit checks for frozen-branch professor hybrid candidate retention."""
import unittest
from collections import OrderedDict

from scripts.v23_professor_hybrid_preserving import (
    CONFIGS, branch_balanced, interaction_features, rank_rrf, union_candidates,
)


class TestProfessorHybrid(unittest.TestCase):
    def setUp(self):
        self.dense = ["a", "b", "c", "d", "e", "f"]
        self.sparse = ["d", "e", "a", "f", "b", "c"]

    def test_preserve_not_replace(self):
        pool = union_candidates(self.dense, self.sparse, 3, 2)
        ids = {x["case_id"] for x in pool}
        self.assertEqual(ids, {"a", "b", "c", "d", "e"})
        self.assertEqual(len(pool), 5)
        self.assertEqual(next(x["source"] for x in pool if x["case_id"] == "a"), "DENSE")
        self.assertEqual(next(x["source"] for x in pool if x["case_id"] == "d"), "SPARSE")
        self.assertEqual(sum(x["source"] == "BOTH" for x in pool), 0)

    def test_both_source_and_budget(self):
        pool = union_candidates(self.dense, self.sparse, 4, 3)
        self.assertEqual(set(x["case_id"] for x in pool), set(self.dense[:4]) | set(self.sparse[:3]))
        self.assertEqual(next(x["source"] for x in pool if x["case_id"] == "d"), "BOTH")
        self.assertLessEqual(len(pool), 7)

    def test_replaced_dense_can_be_lost(self):
        replaced = {x["case_id"] for x in union_candidates(self.dense, self.sparse, 2, 2)}
        preserved = {x["case_id"] for x in union_candidates(self.dense, self.sparse, 4, 2)}
        self.assertNotIn("c", replaced)
        self.assertIn("c", preserved)
        self.assertEqual(preserved - replaced, {"c"})

    def test_no_gt_in_selection_rules(self):
        self.assertEqual(CONFIGS["preserve20_add20"], (20, 20))
        self.assertEqual(CONFIGS["dense40_equal_slots"], (40, 0))
        self.assertEqual(CONFIGS["preserve20_add10"], (20, 10))
        self.assertEqual(CONFIGS["dense30_equal_slots"], (30, 0))
        pool = union_candidates(self.dense, self.sparse, 4, 3)
        self.assertEqual(len(rank_rrf(pool)), len(pool))

    def test_unique_branch_order_and_empty(self):
        rankings = OrderedDict([("P1", ["a", "b", "c"]),
                                ("P2", ["a", "d", "e"]),
                                ("P3", ["d", "f", "b"])])
        self.assertEqual(branch_balanced(rankings, 6), ["a", "d", "f", "b", "e", "c"])
        self.assertEqual(branch_balanced(rankings, 0), [])
        self.assertEqual(branch_balanced(OrderedDict([("P1", []), ("P2", [])]), 10), [])

    def test_reject_nonidentical_corpus(self):
        with self.assertRaises(ValueError):
            union_candidates(["a", "b"], ["a", "c"], 1, 1)
        with self.assertRaises(ValueError):
            union_candidates(["a", "a"], ["a", "b"], 1, 1)

    def test_query_case_feature_dimensions(self):
        import numpy as np
        query = np.ones(48, dtype=np.float32)
        docs = np.zeros((5, 48), dtype=np.float32)
        arr = interaction_features(query, docs)
        self.assertEqual(arr.shape, (5, 192))
        self.assertTrue(np.all(arr[:, :48] == 1))
        self.assertTrue(np.all(arr[:, 48:144] == 0))
        self.assertTrue(np.all(arr[:, 144:] == 1))


if __name__ == "__main__":
    unittest.main()
