from copy import deepcopy
import unittest

from scripts.build_perspective_catalog_pilot_20261109 import REGISTRY, build, validate, quote
from scripts.improvement_cycle import read


class PerspectiveCatalogPilotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = read(REGISTRY)['cases']

    def test_supported_links_require_task_evidence_not_problem_only(self):
        catalog = build(self.cases)
        link = catalog['cards'][0]['links'][0]
        link['evidence'] = [e for e in link['evidence'] if e['field'] != 'task']
        with self.assertRaises(AssertionError):
            validate(catalog, self.cases)

    def test_nonliteral_source_cannot_pass(self):
        catalog = build(self.cases)
        catalog['cards'][0]['links'][0]['evidence'][0]['quote'] += ' (invented capability)'
        with self.assertRaises(AssertionError):
            validate(catalog, self.cases)
        with self.assertRaises(ValueError):
            quote(self.cases, 'AXALL_US_OMB_2025_02663', 'task', 'automatically approves policies')

    def test_ambiguous_evidence_is_not_silently_marked_query_relevant(self):
        catalog = build(self.cases)
        catalog['cards'][0]['links'][0]['query_relevance'] = 'ALWAYS_RELEVANT'
        with self.assertRaises(AssertionError):
            validate(catalog, self.cases)

    def test_duplicate_link_and_missing_boundary_review_rejected(self):
        catalog = build(self.cases)
        catalog['cards'][0]['links'].append(deepcopy(catalog['cards'][0]['links'][0]))
        with self.assertRaises(AssertionError):
            validate(catalog, self.cases)
        catalog = build(self.cases)
        catalog['pair_reviews'].pop()
        with self.assertRaises(AssertionError):
            validate(catalog, self.cases)

    def test_distinct_role_support_allows_many_to_many(self):
        catalog = build(self.cases)
        self.assertEqual(validate(catalog, self.cases), 93)
        role_cards = [c['id'] for c in catalog['cards'] if any(l['case_id'] == 'AXALL_US_OMB_2025_01754' and l['status'] == 'SUPPORTED_FOR_PILOT' for l in c['links'])]
        self.assertEqual(role_cards, ['P02', 'P03'])


if __name__ == '__main__':
    unittest.main()
