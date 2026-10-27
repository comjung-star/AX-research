"""Regression guard: screened external examples must not enter frozen v2.1 GT/corpus."""
import csv
import json
import unittest
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "v2_1"
REGISTRY = DATA / "qa" / "external_coverage_gap_candidates_2026-10-23.csv"


class ExternalCoverageGapCandidateTest(unittest.TestCase):
    def test_external_cases_remain_separate_from_frozen_v21(self):
        manifest = json.loads((DATA / "release_manifest_v2_1.json").read_text(encoding="utf-8"))
        cases = json.loads((DATA / "main_cases_v2_1.json").read_text(encoding="utf-8"))["cases"]
        self.assertEqual(manifest["summary"]["included"], 91)
        self.assertEqual(manifest["summary"]["held"], 7)
        self.assertEqual(len(cases), 91)
        organizations = {c["organization"].casefold() for c in cases}
        with REGISTRY.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 3)
        self.assertEqual(len({r["candidate_id"] for r in rows}), 3)
        self.assertEqual({r["query_id"] for r in rows}, {"V21D006", "V21D009"})
        for row in rows:
            self.assertEqual(row["frozen_v2_1_member"], "NO")
            self.assertEqual(row["candidate_status"], "EXTERNAL_SCREENED_NOT_IN_FROZEN_91")
            self.assertNotIn(row["organization"].casefold(), organizations)
            self.assertEqual(urlparse(row["primary_provider_case_url"]).scheme, "https")
            self.assertTrue(row["problem_view"] and row["task_view"] and row["context_view"])
            self.assertNotIn("relevance_0_4", row)
        by_id = {row["candidate_id"]: row for row in rows}
        self.assertIn("on-prem", by_id["V21GAP009_JEJU_BANK"]["deployment_status_reported"].lower())
        self.assertIn("NOT established", by_id["V21GAP009_HOME_CREDIT"]["deployment_status_reported"])

    def test_empty_view_provisional_status_is_not_human_gt(self):
        p = DATA / "qa" / "ai_provisional_2026-10-23" / "by_perspective_summary.csv"
        with p.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        expected = {
            ("V21D006", "P1_CATALOG_ENRICHMENT_BURDEN"),
            ("V21D009", "P1_AI_SECURITY_COMPLIANCE_CONSTRAINT"),
        }
        found = {(r["query_id"], r["perspective_id"]) for r in rows
                 if (r["query_id"], r["perspective_id"]) in expected}
        self.assertEqual(found, expected)
        for r in rows:
            if (r["query_id"], r["perspective_id"]) in expected:
                self.assertEqual(r["provisional_relevant"], "0")
                self.assertEqual(r["score3"], "0")
                self.assertEqual(r["score4"], "0")
                self.assertEqual(r["status"], "AI_DRAFT_NOT_HUMAN_GT")


if __name__ == "__main__":
    unittest.main()
