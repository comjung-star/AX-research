"""Synthetic unit test only: verifies empty-perspective metrics, NOT real GT."""
import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import v21_evaluate


class UnanswerablePerspectivePolicyTest(unittest.TestCase):
    def test_empty_reference_views_are_reported_not_counted_as_retrieval_misses(self):
        with tempfile.TemporaryDirectory() as tmp:
            data=Path(tmp)
            cases=[{"case_id":f"TEST_{n:03d}"} for n in range(91)]
            (data/"main_cases_v2_1.json").write_text(
                json.dumps({"cases":cases}),encoding="utf-8")
            queries=[
                {"query_id":f"Q{i+1}", "draft_perspectives":[
                    {"id":"P1"},{"id":"P2"},{"id":"P3"}]} for i in range(10)
            ]
            (data/"dev_query_candidates_v2_1.json").write_text(
                json.dumps({"queries":queries}),encoding="utf-8")
            labels=data/"synthetic_labels.csv"
            with labels.open("w",newline="",encoding="utf-8") as f:
                w=csv.DictWriter(f,fieldnames=[
                    "query_id","perspective_id","case_id","relevance_0_4",
                    "annotator_id","reviewer_id","evidence_reason","status"])
                w.writeheader()
                for q in queries:
                    for p in q["draft_perspectives"]:
                        for c in cases:
                            w.writerow({
                                "query_id":q["query_id"],"perspective_id":p["id"],
                                "case_id":c["case_id"],
                                "relevance_0_4":4 if p["id"]=="P1" and c==cases[0] else 0,
                                "annotator_id":"SYNTHETIC_TEST_ANNOTATOR",
                                "reviewer_id":"SYNTHETIC_TEST_REVIEWER",
                                "evidence_reason":"synthetic assertion only",
                                "status":"ADJUDICATED"})
            ranks=[]
            for q in queries:
                p=data/(q["query_id"]+".json")
                p.write_text(json.dumps({
                    "query_id":q["query_id"],
                    "candidate_union":[{"case_id":cases[0]["case_id"]}]}),encoding="utf-8")
                ranks.append(p)
            with patch.object(v21_evaluate,"DATA",data):
                result=v21_evaluate.evaluate(labels,ranks,k=1)
            self.assertEqual(result["mean_recall"],1.0)
            self.assertEqual(result["mean_perspective_coverage"],1.0)
            self.assertEqual(result["n_unanswerable_perspectives"],20)
            self.assertEqual(result["per_query"][0]["unanswerable_perspective_ids"],["P2","P3"])
            self.assertEqual(result["per_query"][0]["answerable_perspective_count"],1)

    def test_unjudged_original_gt_still_blocked(self):
        sheet=Path(__file__).resolve().parents[1]/"data/v2_1/dev_relevance_annotation_sheet_v2_1.csv"
        with self.assertRaisesRegex(ValueError,"Ground Truth NOT READY"):
            v21_evaluate.evaluate(sheet,[],k=10)


if __name__=="__main__":
    unittest.main()
