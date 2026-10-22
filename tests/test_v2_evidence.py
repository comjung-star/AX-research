import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("validate_v2_evidence", ROOT / "scripts/validate_v2_evidence.py")
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class EvidenceValidationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        shutil.copytree(ROOT / "data/v2", self.root / "data/v2")
        for name in ("root_cause_factors_v1.csv", "strategy_taxonomy_v1.csv"):
            shutil.copyfile(ROOT / "data" / name, self.root / "data" / name)

    def edit(self, filename, change):
        path = self.root / "data/v2" / filename
        data = json.loads(path.read_text(encoding="utf-8"))
        change(data)
        path.write_text(json.dumps(data), encoding="utf-8")

    def reject_case(self, key, value, message):
        self.edit("workflow_candidates_v2.json", lambda data: data["cases"][0].update({key: value}))
        with self.assertRaisesRegex(ValueError, message):
            VALIDATOR.validate(self.root)

    def test_current_evidence_has_all_split_dispositions(self):
        result = VALIDATOR.validate(self.root)
        self.assertEqual(result["split_dispositions"], 38)
        self.assertEqual(result["reconstructed_workflows"], 20)
        self.assertEqual(result["additional_parent_reconstructions"], 23)
        self.assertEqual(result["remaining_parent_screens"], 51)
        self.assertFalse(result["freeze_ready"])

    def test_freeze_refuses_incomplete_source_review(self):
        with self.assertRaisesRegex(ValueError, "FREEZE BLOCKED"):
            VALIDATOR.validate(self.root, freeze=True)

    def test_duplicate_split_rejected(self):
        self.edit("split_adjudications_v2.json", lambda data: data["decisions"].append(data["decisions"][0]))
        with self.assertRaisesRegex(ValueError, "exactly one"):
            VALIDATOR.validate(self.root)

    def test_missing_split_rejected(self):
        self.edit("split_adjudications_v2.json", lambda data: data["decisions"].pop())
        with self.assertRaisesRegex(ValueError, "exactly one"):
            VALIDATOR.validate(self.root)

    def test_duplicate_case_rejected(self):
        self.edit("workflow_candidates_v2.json", lambda data: data["cases"].append(data["cases"][0]))
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            VALIDATOR.validate(self.root)

    def test_pilot_parent_cannot_be_promoted(self):
        self.reject_case("parent_case_id", "AX0062", "Excluded or uncertain")

    def test_unknown_parent_rejected(self):
        self.reject_case("parent_case_id", "AX9999", "Unknown")

    def test_forged_lineage_rejected(self):
        self.reject_case("parent_case_id", "AX0016", "Child-parent mismatch")

    def test_missing_production_anchor_rejected(self):
        self.reject_case("production_anchor", "", "Incomplete workflow")

    def test_missing_problem_evidence_rejected(self):
        self.reject_case("problem_anchor", "", "Incomplete workflow")

    def test_invalid_taxonomy_label_rejected(self):
        self.reject_case("strategy", "S7_UNAPPROVED_IMAGE_GENERATION", "Invalid factor or strategy")

    def test_unknown_factor_rejected(self):
        self.reject_case("factor", "F99", "Invalid factor or strategy")

    def test_missing_mapping_reason_rejected(self):
        self.reject_case("mapping_rationale", "", "Incomplete workflow")

    def test_pilot_outcome_cannot_be_silently_classified_production(self):
        self.reject_case("outcome_type", "PILOT", "Unsupported outcome")

    def test_premature_approval_rejected(self):
        self.edit("workflow_candidates_v2.json", lambda data: data.update(status="FROZEN"))
        with self.assertRaisesRegex(ValueError, "Premature"):
            VALIDATOR.validate(self.root)

    def test_rejected_split_cannot_supply_candidate(self):
        self.edit("split_adjudications_v2.json", lambda data: next(row for row in data["decisions"] if row["draft_id"] == "AXV2D_0017_01").update(decision="EXCLUDE_PILOT"))
        with self.assertRaisesRegex(ValueError, "Rejected split promoted"):
            VALIDATOR.validate(self.root)

    def test_remaining_parent_screen_cannot_be_omitted(self):
        self.edit("remaining_parent_screening_v2.json", lambda data: data["parents"].pop())
        with self.assertRaisesRegex(ValueError, "screening coverage mismatch"):
            VALIDATOR.validate(self.root)

    def test_download_not_semantic_approval(self):
        self.edit("remaining_parent_screening_v2.json", lambda data: data["parents"][0].update(depth="SOURCE_APPROVED"))
        with self.assertRaisesRegex(ValueError, "Unknown screening depth"):
            VALIDATOR.validate(self.root)

    def test_invalid_parent_label_rejected(self):
        self.edit("parent_reconstructions_v2.json", lambda data: data["cases"][0].update(strategy="S99"))
        with self.assertRaisesRegex(ValueError, "Invalid reconstructed label"):
            VALIDATOR.validate(self.root)

    def test_missing_parent_implementation_rejected(self):
        self.edit("parent_reconstructions_v2.json", lambda data: data["cases"][0].update(implementation=""))
        with self.assertRaisesRegex(ValueError, "Incomplete parent reconstruction"):
            VALIDATOR.validate(self.root)

    def test_duplicate_parent_reconstruction_rejected(self):
        self.edit("parent_reconstructions_v2.json", lambda data: data["cases"].append(data["cases"][0]))
        with self.assertRaisesRegex(ValueError, "Duplicate parent reconstruction"):
            VALIDATOR.validate(self.root)


if __name__ == "__main__":
    unittest.main()
