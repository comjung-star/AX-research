import unittest

from ax_research.query_understanding_v2 import understand
from scripts.check_query_understanding_v2 import check_contracts
from scripts.improvement_cycle import read


class QueryUnderstandingV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = read('configs/semantic_mapping_20261028.json')

    def test_contract_suite_passes_without_relevance_scores(self):
        result = check_contracts()
        self.assertTrue(result['passed'])
        self.assertEqual(result['cases'], 20)
        self.assertFalse(result['relevance_scores_read'])

    def test_request_variations_keep_same_core_action_and_object_evidence(self):
        variants = ['우편물 기록을 비교한 목록을 만들고 싶습니다.',
                    '우편물 기록을 비교한 목록이 필요합니다.',
                    '우편물 기록을 비교해 목록으로 정리해 주세요.']
        for text in variants:
            partition, profile = understand(text, self.cfg)
            self.assertIn('비교', profile['fields']['action'].splitlines())
            self.assertIn('우편물 기록', profile['fields']['object'])
            self.assertIn('목록', partition['output_hint_text'])

    def test_adding_prohibition_does_not_change_positive_request(self):
        text = '문서 변경 목록이 필요합니다.'
        first, _ = understand(text, self.cfg)
        second, _ = understand(text + ' 원문 파일은 삭제하지 마세요.', self.cfg)
        self.assertEqual(first['requested_text'], second['requested_text'])
        self.assertIn('삭제하지 마세요', second['excluded_text'])

    def test_no_background_fallback_and_no_invented_actions(self):
        partition, profile = understand('업무 기록 현황.', self.cfg)
        self.assertTrue(partition['request_unknown'])
        self.assertFalse(partition['fallback_used'])
        self.assertFalse(any(profile['fields'].values()))

    def test_identifier_remains_complete_in_object(self):
        _, profile = understand('거래처 식별자를 비교해 목록을 만들고 싶습니다.', self.cfg)
        self.assertNotIn('식별', profile['fields']['action'].splitlines())
        self.assertIn('식별자', profile['fields']['object'])


if __name__ == '__main__':
    unittest.main()
