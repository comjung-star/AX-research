import csv
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_v2_replacement_release import build
from validate_v2_replacements import validate


class ReplacementValidationTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        shutil.copytree(ROOT / "data/v2", self.root / "data/v2")
        for name in ("root_cause_factors_v1.csv", "strategy_taxonomy_v1.csv", "main_cases_v1.csv"):
            shutil.copyfile(ROOT / "data" / name, self.root / "data" / name)

    def edit(self, filename, change):
        path = self.root / "data/v2" / filename
        payload = json.loads(path.read_text(encoding="utf-8"))
        change(payload)
        path.write_text(json.dumps(payload), encoding="utf-8")

    def reject(self, key, value, message):
        self.edit("replacement_cases_v2.json", lambda data: data["cases"][0].update({key: value}))
        with self.assertRaisesRegex(ValueError, message):
            validate(self.root)

    def edit_taxonomy(self, change):
        path = self.root / "data/v2/strategy_taxonomy_v2.csv"
        with path.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            fields = reader.fieldnames
            rows = list(reader)
        change(rows)
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)

    def test_inventory_is_candidate_only(self):
        result = validate(self.root)
        self.assertEqual(result["active_candidates"], 101)
        self.assertEqual(result["replacement_workflows"], 40)
        self.assertEqual(result["replaced_parent_slots"], 29)
        self.assertEqual(result["replaced_split_slots"], 11)
        self.assertEqual(result["factor_abstentions"], 3)
        self.assertEqual(result["approved_frozen_cases"], 0)
        self.assertFalse(result["freeze_ready"])

    def test_freeze_is_not_self_approved(self):
        with self.assertRaisesRegex(ValueError, "FREEZE BLOCKED"):
            validate(self.root, freeze=True)

    def test_builder_is_deterministic(self):
        self.assertEqual(build(self.root), build(self.root))

    def test_administrative_substitution_is_not_parent_lineage(self):
        payload = build(self.root)
        for row in payload["replacement_ledger"]:
            self.assertEqual(row["relationship"], "ADMINISTRATIVE_SUBSTITUTION_NOT_EVIDENCE_LINEAGE")
        excluded = {row["replaced_id"] for row in payload["replacement_ledger"] if row["replaced_unit"] == "PARENT"}
        self.assertFalse(excluded & {row["parent_v1_case_id"] for row in payload["cases"]})

    def test_missing_deployment_evidence(self):
        self.reject("deployment_anchor", "", "Missing source passage")

    def test_missing_problem_evidence(self):
        self.reject("problem_anchor", "", "Missing source passage")

    def test_missing_outcome_qualification(self):
        self.reject("uncertainty", "", "Missing source passage")

    def test_pilot_outcome_is_not_production(self):
        self.reject("outcome_type", "PILOT", "silently promoted")

    def test_unknown_strategy(self):
        self.reject("strategy", "S99", "Unrecognized proposed label")

    def test_unknown_factor(self):
        self.reject("factor", "F99", "Unsupported factor")

    def test_abstention_requires_a_reason(self):
        self.reject("factor", "ABSTAIN", "Unsupported factor")

    def test_invalid_primary_source(self):
        self.reject("source", "http://example.com", "Invalid primary source")

    def test_unknown_parent(self):
        self.reject("parent_v1_case_id", "AX9999", "Unknown source-parent")

    def test_author_cannot_claim_approval(self):
        self.reject("second_reviewer_approved", True, "self-certify")

    def test_duplicate_workflow(self):
        def duplicate(data):
            data["cases"][1]["organization"] = data["cases"][0]["organization"]
            data["cases"][1]["task"] = data["cases"][0]["task"]
        self.edit("replacement_cases_v2.json", duplicate)
        with self.assertRaisesRegex(ValueError, "Duplicate replacement"):
            validate(self.root)

    def test_duplicate_id(self):
        self.reject("id", "AXV2N_0102", "40 distinct")

    def test_generated_corpus_edit_is_rejected(self):
        self.edit("active_candidate_corpus_v2.json", lambda data: data["cases"].pop())
        with self.assertRaisesRegex(ValueError, "stale or edited"):
            validate(self.root)

    def test_forged_ledger_is_rejected(self):
        self.edit("active_candidate_corpus_v2.json", lambda data: data["replacement_ledger"][0].update(replaced_id="AX0001"))
        with self.assertRaisesRegex(ValueError, "stale or edited"):
            validate(self.root)

    def test_legacy_strategy_rename_is_rejected(self):
        self.edit_taxonomy(lambda rows: rows[0].update(strategy_id="S1_RENAMED"))
        with self.assertRaisesRegex(ValueError, "silently renamed"):
            validate(self.root)

    def test_taxonomy_does_not_self_freeze(self):
        self.edit_taxonomy(lambda rows: rows[0].update(status="FROZEN"))
        with self.assertRaisesRegex(ValueError, "silently freeze"):
            validate(self.root)

    def test_taxonomy_requires_actual_workflow_evidence(self):
        self.edit_taxonomy(lambda rows: rows[-1].update(evidence_ids="AXV2N_0101|AXV2N_0102|AXV2N_0103"))
        with self.assertRaisesRegex(ValueError, "actual S7 workflows"):
            validate(self.root)

    def test_s7_requires_independent_organizations(self):
        def collapse(data):
            for row in data["cases"]:
                if row["strategy"] == "S7":
                    row["organization"] = "One organization"
        self.edit("replacement_cases_v2.json", collapse)
        with self.assertRaisesRegex(ValueError, "three organizations"):
            validate(self.root)

    def test_missing_source_inventory_is_rejected(self):
        path = self.root / "data/v2/replacement_source_access_v2.csv"
        rows = path.read_text(encoding="utf-8").splitlines()
        path.write_text("\n".join(rows[:-1]) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "access inventory"):
            validate(self.root)


if __name__ == "__main__":
    unittest.main()
