"""Full union → Top-M controls and invariant checks, independent of Silver labels."""
import unittest

from scripts.v23_full_union_topm import full_union, select_top_m, rerank


class FullUnionTopMTests(unittest.TestCase):
    def setUp(self):
        self.ids = [f"CASE{i:02d}" for i in range(84)]
        # Distinct sparse ordering, only the first 24 have positive lexical evidence.
        self.sparse = [(cid, (24-i)/10.0 if i<24 else 0.0)
                       for i,cid in enumerate(reversed(self.ids))]
        self.union = full_union(self.ids, self.sparse)

    def test_exact_union_all_cases_before_m(self):
        self.assertEqual(len(self.union), 84)
        self.assertEqual({v["case_id"] for v in self.union}, set(self.ids))
        self.assertEqual(sum(v["sparse_hit"] for v in self.union), 24)
        self.assertTrue(all(v["bm25_score"]<=0 for v in self.union if not v["sparse_hit"]))

    def test_zero_sparse_score_no_rrf_contribution(self):
        by_id={r["case_id"]:r for r in self.union}
        for r in self.union:
            if not r["sparse_hit"]:
                self.assertAlmostEqual(r["rrf_score"],1/(60+r["dense_rank"]))
            else:
                self.assertGreater(r["rrf_score"],1/(60+r["dense_rank"]))
        self.assertEqual(by_id[self.ids[-1]]["source"],"BOTH")
        self.assertEqual(by_id[self.ids[0]]["source"],"DENSE")

    def test_all_m_all_methods_and_no_duplicates(self):
        for m in (10,20,40,60,84):
            for method in ("rrf","interleave","dense"):
                chosen=select_top_m(self.union,method,m)
                self.assertEqual(len(chosen),m)
                self.assertEqual(len({r["case_id"] for r in chosen}),m)
                self.assertTrue({r["case_id"] for r in chosen} <= set(self.ids))
                if m==84:
                    self.assertEqual({r["case_id"] for r in chosen},set(self.ids))

    def test_dense_same_m_matches_original_dense_prefix(self):
        for m in (10,20,40,60,84):
            chosen=select_top_m(self.union,"dense",m)
            self.assertEqual([r["case_id"] for r in chosen],self.ids[:m])

    def test_rrf_or_interleave_does_not_hardcode_dense_slots(self):
        d={r["case_id"] for r in select_top_m(self.union,"dense",20)}
        r={r["case_id"] for r in select_top_m(self.union,"rrf",20)}
        i={r["case_id"] for r in select_top_m(self.union,"interleave",20)}
        # Both hybrids can admit cases unavailable to Dense Top20.
        self.assertTrue(r-d)
        self.assertTrue(i-d)
        self.assertTrue({r["case_id"] for r in select_top_m(self.union,"rrf",84)}>=d)

    def test_invalid_m_or_ranks(self):
        with self.assertRaises(ValueError):
            select_top_m(self.union,"rrf",0)
        with self.assertRaises(ValueError):
            select_top_m(self.union,"rrf",85)
        with self.assertRaises(ValueError):
            select_top_m(self.union,"wrong",20)
        with self.assertRaises(ValueError):
            full_union(self.ids, self.sparse[:10])

    def test_mlp_and_rrf_rerank_same_pool(self):
        import numpy as np
        chosen=select_top_m(self.union,"interleave",40)
        idx={cid:i for i,cid in enumerate(self.ids)}
        scores=np.linspace(-2,2,84)
        a=rerank(chosen,"rrf",scores,idx)
        b=rerank(chosen,"mlp",scores,idx)
        self.assertEqual(set(a),set(b))
        self.assertEqual(len(a),40)


if __name__=="__main__":
    unittest.main()
