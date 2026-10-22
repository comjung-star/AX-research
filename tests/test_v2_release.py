import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_v2_final_release import artifacts, build
from validate_v2_release import validate


class FinalReleaseTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        shutil.copytree(ROOT / "data/v2", self.root / "data/v2")
        for name in ("root_cause_factors_v1.csv", "main_cases_v1.csv"):
            shutil.copyfile(ROOT / "data" / name, self.root / "data" / name)

    def edit(self, filename, change):
        path = self.root / "data/v2" / filename
        payload = json.loads(path.read_text(encoding="utf-8"))
        change(payload)
        path.write_text(json.dumps(payload), encoding="utf-8")

    def reject(self, filename, change, message):
        self.edit(filename, change)
        with self.assertRaisesRegex(ValueError, message):
            validate(self.root, freeze=True)

    def refresh(self):
        for name, content in artifacts(self.root).items():
            (self.root / "data/v2" / name).write_text(content, encoding="utf-8")

    def test_release_freezes_data_not_human_ground_truth(self):
        result = validate(self.root, freeze=True)
        self.assertEqual(result["included_workflows"], 98)
        self.assertEqual(result["excluded_workflows"], 3)
        self.assertEqual(result["factor_abstentions"], 25)
        self.assertEqual(result["strategy_abstentions"], 2)
        self.assertEqual(result["supported_direct_mappings"], 68)
        self.assertTrue(result["freeze_valid"])
        self.assertFalse(result["human_ground_truth"])

    def test_generation_is_deterministic(self):
        self.assertEqual(artifacts(self.root), artifacts(self.root))

    def test_review_all_41_inherited_cases(self):
        records = json.loads((self.root / "data/v2/inherited_evidence_review_v2.json").read_text(encoding="utf-8"))["records"]
        self.assertEqual(len(records), 41)
        self.assertEqual(sum(row["decision"] == "INCLUDE" for row in records), 38)

    def test_known_source_failures_are_excluded(self):
        dataset, manifest = build(self.root)
        rejected = {row["case_id"] for row in dataset["dispositions"] if row["decision"] == "EXCLUDE"}
        self.assertEqual(rejected, {"AXV2H_0004_01", "AXV2H_0072_01", "AXV2P2_0046_01"})
        self.assertTrue(all(row["case_id"] not in rejected for row in dataset["cases"]))

    def test_missing_inherited_review(self):
        self.reject("inherited_evidence_review_v2.json", lambda data: data["records"].pop(), "Every inherited")

    def test_missing_source_passage(self):
        self.reject("inherited_evidence_review_v2.json", lambda data: data["records"][0].update(deployment_anchor=""), "source passage missing")

    def test_problem_edit_requires_new_blind_review(self):
        self.reject("inherited_evidence_review_v2.json", lambda data: data["records"][0].update(updates={"problem": "New problem"}), "Problem changed after blind review")

    def test_solution_edit_requires_new_review(self):
        self.reject("inherited_evidence_review_v2.json", lambda data: data["records"][0].update(updates={"implementation": "New implementation"}), "Solution changed after independent review")

    def test_task_edit_requires_new_review(self):
        self.reject("inherited_evidence_review_v2.json", lambda data: data["records"][0].update(updates={"task": "New task"}), "Solution changed after independent review")

    def test_missing_blind_response(self):
        self.reject("independent_label_review_v2.json", lambda data: data["sessions"][0]["result"]["records"].pop(), "Missing or duplicated")

    def test_duplicate_blind_response(self):
        def duplicate(data):
            rows = data["sessions"][0]["result"]["records"]
            rows.append(rows[0])
        self.reject("independent_label_review_v2.json", duplicate, "Missing or duplicated")

    def test_wrong_factor_reviewer_role(self):
        self.reject("independent_label_review_v2.json", lambda data: data["sessions"][0]["result"].update(reviewer_role="UNBLINDED"), "Wrong independent")

    def test_solution_information_cannot_enter_blind_packet(self):
        def leak(data):
            session = data["sessions"][0]
            prefix, text = session["submitted_prompt"].rsplit("\n", 1)
            packet = json.loads(text)
            packet[0]["implementation"] = "The answer must not be visible"
            session["submitted_prompt"] = prefix + "\n" + json.dumps(packet)
        self.reject("independent_label_review_v2.json", leak, "forbidden information")

    def test_independent_rationale_required(self):
        self.reject("independent_label_review_v2.json", lambda data: data["sessions"][0]["result"]["records"][0].update(rationale=""), "lacks rationale")

    def test_unknown_reviewed_factor(self):
        self.reject("independent_label_review_v2.json", lambda data: data["sessions"][0]["result"]["records"][0].update(factor="F99"), "Unknown reviewed label")

    def test_unknown_reviewed_strategy(self):
        self.reject("independent_label_review_v2.json", lambda data: data["sessions"][3]["result"]["records"][1].update(strategy="S99"), "Unknown reviewed label")

    def test_stale_mapping_input(self):
        def stale(data):
            session = data["sessions"][0]
            prefix, text = session["submitted_prompt"].rsplit("\n", 1)
            packet = json.loads(text)
            packet[0]["factor"] = "F09"
            session["submitted_prompt"] = prefix + "\n" + json.dumps(packet)
        self.reject("independent_mapping_review_v2.json", stale, "relation review is stale")

    def test_missing_mapping_review(self):
        self.reject("independent_mapping_review_v2.json", lambda data: data["sessions"][0]["result"]["records"].pop(), "Relation review coverage")

    def test_causal_promotion_not_allowed(self):
        self.reject("independent_mapping_review_v2.json", lambda data: data["sessions"][0]["result"]["records"][0].update(decision="CAUSALLY_PROVEN"), "Invalid or duplicated relation")

    def test_author_cannot_forge_human_gt(self):
        self.reject("main_cases_v2.json", lambda data: data["cases"][0].update(human_ground_truth_approved=True), "Stale or altered")

    def test_abstention_cannot_be_silently_filled(self):
        def force(data):
            next(row for row in data["cases"] if row["factor_label"] is None)["factor_label"] = "F01_REPETITIVE_MANUAL_WORK"
        self.reject("main_cases_v2.json", force, "Stale or altered")

    def test_exclusion_cannot_be_silently_promoted(self):
        self.reject("main_cases_v2.json", lambda data: next(row for row in data["dispositions"] if row["decision"] == "EXCLUDE").update(decision="INCLUDE"), "Stale or altered")

    def test_extra_direct_pair_rejected(self):
        def expand(data):
            row = next(row for row in data["cases"] if row["direct_mappings"])
            row["direct_mappings"].append(row["direct_mappings"][0])
        self.reject("main_cases_v2.json", expand, "Stale or altered")

    def test_reviewer_roles_need_separate_sessions(self):
        self.edit("independent_label_review_v2.json", lambda data: data["sessions"][3].update(session_id=data["sessions"][0]["session_id"]))
        self.refresh()
        with self.assertRaisesRegex(ValueError, "not isolated"):
            validate(self.root, freeze=True)

    def test_manifest_hash_mismatch(self):
        self.reject("release_manifest_v2.json", lambda data: data.update(dataset_canonical_sha256="0" * 64), "Stale or altered")

    def test_csv_is_part_of_validated_snapshot(self):
        path = self.root / "data/v2/main_cases_v2.csv"
        path.write_text(path.read_text(encoding="utf-8").replace("uncertainty", "hidden_note", 1), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Stale or altered"):
            validate(self.root, freeze=True)

    def test_s7_has_four_independent_operating_examples(self):
        dataset, manifest = build(self.root)
        creative = [row for row in dataset["cases"] if row["strategy_label"] == "S7_GENERATIVE_CONTENT_CREATION"]
        self.assertEqual(len({row["organization"] for row in creative}), 4)
        self.assertEqual(len({row["source_url"] for row in creative}), 4)

    def test_no_mapping_for_unclassified_factor(self):
        dataset, manifest = build(self.root)
        self.assertTrue(all(not row["direct_mappings"] for row in dataset["cases"] if row["factor_label"] is None))


if __name__ == "__main__":
    unittest.main()
