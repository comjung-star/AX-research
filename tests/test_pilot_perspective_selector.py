from copy import deepcopy
import json
import unittest

from ax_research.pilot_perspective_selector import select_perspectives
from scripts.improvement_cycle import read
from scripts.pilot_perspective_selection import CATALOG, RULES, check_contracts


class PilotPerspectiveSelectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = read(CATALOG)
        cls.rules = read(RULES)

    def test_development_contracts_and_paraphrase_stability(self):
        result = check_contracts()
        self.assertTrue(result['passed'], [(r['id'], r['errors']) for r in result['rows'] if not r['passed']])
        self.assertEqual(result['cases'], 33)
        self.assertEqual(result['paraphrase_groups'], 4)
        self.assertTrue(result['paraphrase_selection_stable'])

    def test_holds_are_never_used_to_justify_selection(self):
        catalog = deepcopy(self.catalog)
        for link in next(c for c in catalog['cards'] if c['id'] == 'P02')['links']:
            link['status'] = 'HOLD'
        result = select_perspectives('청구서 금액을 추출해주세요.', catalog, self.rules)
        self.assertFalse(result['selected'])
        self.assertIn('P02', [r['id'] for r in result['review_needed']])

    def test_selector_does_not_mutate_catalog_or_return_case_rankings(self):
        catalog = deepcopy(self.catalog)
        before = deepcopy(catalog)
        result = select_perspectives('사내 규정에서 조치 절차를 검색해주세요.', catalog, self.rules)
        self.assertEqual(catalog, before)
        result['selected'][0]['next_stage_conditions'].append('client note')
        self.assertEqual(catalog, before)
        self.assertFalse(result['case_recommendations_generated'])
        self.assertNotIn('case_id', json.dumps(result))
        self.assertNotIn('ranking', result)

    def test_all_selected_cards_have_work_and_object_evidence(self):
        for row in check_contracts()['rows']:
            for chosen in row['result']['selected']:
                kinds = {e['kind'] for e in chosen['evidence']}
                self.assertTrue({'work', 'object'} <= kinds)
                if chosen['id'] == 'P03':
                    self.assertIn('reference', kinds)
                if chosen['id'] == 'P04':
                    self.assertIn('capacity', kinds)

    def test_no_unstated_problem_burden_is_invented(self):
        result = select_perspectives('문서에서 항목을 추출해주세요.', self.catalog, self.rules)
        self.assertEqual([r['id'] for r in result['selected']], ['P02'])
        self.assertFalse(result['selected'][0]['problem_burden_explicit'])

    def test_empty_input_and_catalog_mismatch_are_rejected(self):
        with self.assertRaises(ValueError):
            select_perspectives('', self.catalog, self.rules)
        bad = deepcopy(self.catalog)
        bad['version'] = 'unknown-version'
        with self.assertRaises(ValueError):
            select_perspectives('문서를 검색해주세요.', bad, self.rules)


if __name__ == '__main__':
    unittest.main()
