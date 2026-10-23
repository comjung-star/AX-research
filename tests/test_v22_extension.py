"""v2.2 adds two source-screened cases without mutating v2.1 or inventing Gold."""
import csv
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
V21=ROOT/"data/v2_1"
V22=ROOT/"data/v2_2"

class DatasetV22ExtensionTest(unittest.TestCase):
    def test_retains_all_original_91_unchanged(self):
        old=json.loads((V21/"main_cases_v2_1.json").read_text(encoding="utf-8"))["cases"]
        new=json.loads((V22/"main_cases_v2_2.json").read_text(encoding="utf-8"))["cases"]
        self.assertEqual(len(old),91)
        self.assertEqual(len(new),93)
        self.assertEqual(old,new[:91])
        self.assertEqual(len({x["case_id"] for x in new}),93)
        self.assertEqual(len({x["sampling_group_id"] for x in new}),65)
        self.assertNotIn("Home Credit Bank", {x["organization"] for x in new})
        self.assertEqual({x["organization"] for x in new[91:]},{"Wayfair","Jeju Bank"})

    def test_new_case_labels_not_promoted(self):
        entries=json.loads((V22/"main_cases_v2_2.json").read_text(encoding="utf-8"))["cases"][91:]
        for c in entries:
            self.assertIsNone(c["factor_label"])
            self.assertIsNone(c["strategy_label"])
            self.assertIsNone(c["factor_review"])
            self.assertIsNone(c["strategy_review"])
            self.assertFalse(c["human_ground_truth_approved"])
            self.assertEqual(c["direct_mappings"], [])
            self.assertEqual(c["mapping_review"]["decision"],"NOT_REVIEWED")
            self.assertTrue(c["evidence"]["deployment_anchor"])
            self.assertTrue(c["source_url"].startswith("https://"))
        self.assertEqual(entries[1]["outcome_5class"],"UNKNOWN")

    def test_gt_starts_unjudged_for_93(self):
        with (V22/"dev_relevance_annotation_sheet_v2_2.csv").open(encoding="utf-8",newline="") as f:
            rows=list(csv.DictReader(f))
        self.assertEqual(len(rows),2790)
        self.assertEqual(len({(r["query_id"],r["perspective_id"],r["case_id"]) for r in rows}),2790)
        for r in rows:
            self.assertEqual(r["status"],"UNJUDGED")
            self.assertEqual(r["relevance_0_4"],"")
            self.assertEqual(r["annotator_id"],"")
            self.assertEqual(r["reviewer_id"],"")
        with (V22/"dev_strategy_annotation_sheet_v2_2.csv").open(encoding="utf-8",newline="") as f:
            s=list(csv.DictReader(f))
        self.assertEqual(len(s),10)
        self.assertTrue(all(x["status"]=="UNJUDGED" for x in s))

    def test_new_case_csv_and_source_index_ids_agree(self):
        with (V22/"main_cases_v2_2.csv").open(encoding="utf-8",newline="") as f:
            main=list(csv.DictReader(f))
        with (V22/"source_evidence_index_v2_2.csv").open(encoding="utf-8",newline="") as f:
            index=list(csv.DictReader(f))
        expect={x["case_id"] for x in json.loads((V22/"main_cases_v2_2.json").read_text(encoding="utf-8"))["cases"]}
        self.assertEqual({x["case_id"] for x in main},expect)
        self.assertEqual({x["case_id"] for x in index},expect)
        self.assertEqual(len(main),93)
        self.assertEqual(len(index),93)

if __name__=="__main__":
    unittest.main()
