"""No AI score should be present on blinded review form."""
import ast
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
class V22AuditDesignTests(unittest.TestCase):
 def test_runner_and_analyzer_syntax(self):
  for p in ("scripts/v22_repeatability_grade.py","scripts/v22_repeatability_analyze.py"):
   ast.parse((ROOT/p).read_text(encoding="utf-8"))
 def test_no_solution_or_previous_gt_in_model_input(self):
  runner=(ROOT/"scripts/v22_repeatability_grade.py").read_text(encoding="utf-8")
  model=(ROOT/"scripts/v21_provisional_ai_ground_truth.py").read_text(encoding="utf-8")
  self.assertIn("v21.grade_batch(",runner)
  self.assertIn('"business_problem":c["problem"]',model)
  self.assertIn('"ax_target_task":c["task"]',model)
  self.assertIn('"business_context":c["context"]',model)
  self.assertNotIn('"solution":c[',model)
  self.assertNotIn('"implementation":c[',model)
 def test_blind_sample_excludes_ai_scores(self):
  analyzer=(ROOT/"scripts/v22_repeatability_analyze.py").read_text(encoding="utf-8")
  tree=ast.parse(analyzer)
  fields=None
  for node in ast.walk(tree):
   if isinstance(node,ast.Dict):
    keys=[k.value for k in node.keys if isinstance(k,ast.Constant) and isinstance(k.value,str)]
    if "review_id" in keys and "business_problem_query" in keys:
     fields=keys
  self.assertIsNotNone(fields)
  self.assertNotIn("pass1",fields)
  self.assertNotIn("pass2",fields)
  self.assertNotIn("pass3",fields)
  self.assertNotIn("median_score",fields)
if __name__=="__main__":
 unittest.main()
