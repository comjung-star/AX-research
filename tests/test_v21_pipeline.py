"""v2.1 freeze, retrieval-input leakage and evidence trace tests."""
import json
import unittest
from pathlib import Path

from scripts.v21_retrieval_smoke import branch_candidates, load_cases, problem_text

ROOT=Path(__file__).resolve().parents[1]


class V21Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases=load_cases()

    def test_frozen_91(self):
        self.assertEqual(len(self.cases),91)
        self.assertEqual(len({x["case_id"] for x in self.cases}),91)
        self.assertFalse(any(x["human_ground_truth_approved"] for x in self.cases))

    def test_no_solution_leakage(self):
        s=self.cases[0]
        t=problem_text(s)
        self.assertIn(s["problem"],t)
        self.assertIn(s["task"],t)
        self.assertIn(s["context"],t)
        self.assertNotIn("[SOLUTION]",t)
        self.assertNotIn("[OUTCOME]",t)

    def test_single_query_and_trace(self):
        result=branch_candidates(self.cases,[{"id":"P0","query":"Manual quotation production planning tasks"}],k=10)
        self.assertEqual(len(result["candidate_union"]),10)
        self.assertEqual(len(result["branch_rankings"]),1)
        self.assertTrue(all(x["no_factor_strategy_causality_claim"] for x in result["candidate_union"]))
        self.assertTrue(all(x["source_url"].startswith("https://") for x in result["candidate_union"]))

    def test_multibranch_keeps_paths(self):
        b=[{"id":"P1","query":"customer support knowledge retrieval"},
           {"id":"P2","query":"factory scheduling production plan changes"}]
        result=branch_candidates(self.cases,b,k=10)
        self.assertEqual(set(result["branch_rankings"]),{"P1","P2"})
        ids=[x["case_id"] for x in result["candidate_union"]]
        self.assertEqual(len(ids),len(set(ids)))
        self.assertTrue(all(x["branch_provenance"] for x in result["candidate_union"]))

    def test_v1_gold_not_transfer(self):
        old=(ROOT/"data/retrieval_gold_v0.1.csv").read_text(encoding="utf-8")
        self.assertIn("AX0001",old)
        case_ids={x["case_id"] for x in self.cases}
        self.assertFalse("AX0001" in case_ids)
        rel=(ROOT/"data/v2_1/dev_relevance_annotation_sheet_v2_1.csv").read_text(encoding="utf-8")
        self.assertIn("UNJUDGED",rel)
        self.assertNotIn("PILOT_GOLD_ADJUDICATED",rel)


if __name__ == "__main__":
    unittest.main()
