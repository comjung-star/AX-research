import json
import unittest

from scripts.collect_ax_expansion import find_story_links, normalize_url, parse_story, source_key
from scripts.collect_ax_case_portals import SOURCES as CASE_PORTALS, extract_candidates, preserve_identity_url
from scripts.collect_ax_portals import SOURCES as DATASETS, normalize_eu, normalize_stage, normalize_us, parse_csv


class AXExpansionTests(unittest.TestCase):
    def test_invalid_embedded_urls_do_not_abort_collection(self):
        source = {"host": "example.com", "path_pattern": r"^/customers/[^/]+$"}
        links = find_story_links(b'<a href="https://[invalid">bad</a><a href="/customers/sample?tracking=1">Valid</a>', "https://example.com", source)
        self.assertEqual(links, {"https://example.com/customers/sample"})
        self.assertEqual(normalize_url("https://[invalid"), "")

    def test_tracking_and_language_aliases_are_not_counted_as_new_sources(self):
        self.assertEqual(normalize_url("https://example.com/story/?utm=1#top"), "https://example.com/story")
        self.assertEqual(source_key("https://www.microsoft.com/en/customers/story/12345-sample", "Microsoft"),
                         source_key("https://www.microsoft.com/ko-kr/customers/story/12345-other", "Microsoft"))

    def test_metadata_collection_is_not_marked_as_verified_case_or_success(self):
        payload = b'<html><head><meta property="og:title" content="Example AI document automation"><meta name="description" content="A short source description for review"></head><main><p>' + b'Artificial intelligence supports document processing in this customer story. ' * 6 + b'</p></main></html>'
        record = parse_story(payload, "https://example.com/customers/test")
        self.assertFalse(record["active_in_prototype"])
        self.assertEqual(record["outcome"], "UNKNOWN_REQUIRES_REVIEW")
        self.assertEqual(record["semantic_verification"], "NOT_HUMAN_VERIFIED_NOT_TRAINING_GOLD")
        self.assertLessEqual(record["source_quote_word_count"], 25)
        self.assertNotIn("<html>", json.dumps(record))

    def test_bad_csv_rows_are_quarantined_without_column_shift(self):
        header, valid, malformed = parse_csv(b"id,title,stage\n1,Example,Deployed\n2,Broken\n3,Next,Pilot\n")
        self.assertEqual(header, ["id", "title", "stage"])
        self.assertEqual(len(valid), 2)
        self.assertEqual(len(malformed), 1)
        self.assertEqual(valid[1][1]["title"], "Next")

    def test_reported_benefits_are_not_invented_as_verified_outcomes(self):
        row = {"use_case_name": "Example", "agency_name": "Agency", "development_stage": "Pre-deployment", "benefits": "Expected savings", "contact_email": "public-contact@example.com"}
        record = normalize_us(DATASETS[0], 2, row)
        self.assertEqual(record["development_stage"], "PRE_DEPLOYMENT")
        self.assertIn("Expected", record["reported_benefits"])
        self.assertIn("UNKNOWN", record["outcome"])
        self.assertFalse(record["active_in_prototype"])
        self.assertNotIn("public-contact@example.com", json.dumps(record))

    def test_non_ai_portal_records_and_unknown_stages_remain_explicit(self):
        record = normalize_eu(DATASETS[1], 2, {"Name": "Example", "Primary Technology": "Blockchain", " Status": "Planned"})
        self.assertEqual(record["ai_status"], "NON_AI_OR_UNCONFIRMED_TECHNOLOGY")
        self.assertEqual(record["development_stage"], "PLANNED")
        self.assertEqual(normalize_stage(""), "UNKNOWN")
        self.assertEqual(normalize_stage("Not in use"), "NOT_IN_USE")

    def test_portal_query_ids_are_preserved_as_distinct_records(self):
        first = preserve_identity_url("https://example.com/View.do?bcIdx=1&cbIdx=9&utm_source=test#top")
        second = preserve_identity_url("https://example.com/View.do?bcIdx=2&cbIdx=9")
        self.assertNotEqual(first, second)
        self.assertNotIn("utm_source", first)

    def test_korean_portal_public_case_links_are_extracted_without_login(self):
        nia = next(source for source in CASE_PORTALS if source["id"] == "NIA_AI_CASES")
        payload = b'''<a href="#view" onclick="doBbsFView('99953','29718','16010100','29718');return false;" title="Example case">Example</a>'''
        rows = extract_candidates(payload, nia["pages"][0], nia)
        self.assertEqual(len(rows), 1)
        self.assertIn("bcIdx=29718", rows[0]["url"])
        data_go = next(source for source in CASE_PORTALS if source["id"] == "DATA_GO_USE_CASES")
        rows = extract_candidates(b'''<a href="javascript:fn_view('123')"><strong>Example</strong></a>''', data_go["pages"][0], data_go)
        self.assertIn("prcuseCaseSn=123", rows[0]["url"])
        self.assertEqual(rows[0]["record_kind"], "DATA_APPLICATION_AI_NOT_ASSUMED")


if __name__ == "__main__":
    unittest.main()
