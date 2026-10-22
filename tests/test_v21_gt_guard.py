"""The v2.1 evaluator must refuse incomplete/legacy/made-up Ground Truth."""
import unittest
from pathlib import Path
from scripts.v21_evaluate import evaluate

ROOT=Path(__file__).resolve().parents[1]

class GTReadinessTest(unittest.TestCase):
    def test_unjudged_refuses_metric(self):
        sheet=ROOT/"data/v2_1/dev_relevance_annotation_sheet_v2_1.csv"
        with self.assertRaisesRegex(ValueError,"Ground Truth NOT READY"):
            evaluate(sheet, [], k=10)

if __name__=="__main__":
    unittest.main()
