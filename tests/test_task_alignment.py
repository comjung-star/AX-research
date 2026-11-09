import unittest

import numpy as np

from ax_research.task_alignment import cosine, partition_request, replace_core


class TaskAlignmentTests(unittest.TestCase):
    def test_requested_and_coordinated_exclusions_keep_scope(self):
        text = '사진에서 결함을 찾고 싶습니다. AI가 판정을 확정하거나 설비를 중지시키지는 않습니다.'
        parsed = partition_request(text)
        self.assertEqual(parsed['requested_text'], '사진에서 결함을 찾고 싶습니다')
        self.assertEqual(parsed['excluded_text'], 'AI가 판정을 확정하거나 설비를 중지시키지는 않습니다')
        for span in parsed['pieces'] + parsed['output_hints']:
            self.assertEqual(text[span['start']:span['end']], span['quote'])

    def test_mixed_guidance_and_no_control_separate(self):
        parsed = partition_request('매뉴얼을 안내하고 싶습니다. 안내만 제공하고 장비 제어 명령은 실행하지 않습니다.')
        self.assertIn('안내만 제공하고', parsed['requested_text'])
        self.assertNotIn('장비 제어', parsed['requested_text'])
        self.assertEqual(parsed['excluded_text'], '장비 제어 명령은 실행하지 않습니다')

    def test_human_approval_is_not_an_excluded_operation(self):
        parsed = partition_request('정비 위험을 알리고 싶습니다. 정비 작업은 사람이 승인합니다.')
        self.assertEqual(parsed['pieces'][-1]['role'], 'human_approval')
        self.assertEqual(parsed['excluded_text'], '')

    def test_unrecognized_requests_are_explicit_fallback(self):
        parsed = partition_request('보고서 검색. 자동 발송은 금지.')
        self.assertTrue(parsed['fallback_used'])
        self.assertEqual(parsed['requested_text'], '보고서 검색')
        self.assertEqual(parsed['excluded_text'], '자동 발송은 금지')

    def test_excluded_only_does_not_invent_positive_request(self):
        parsed = partition_request('자동 차단은 금지.')
        self.assertEqual(parsed['requested_text'], '')

    def test_result_hints_are_literal_and_are_not_case_outcomes(self):
        text = '출처와 근거를 붙인 검토 목록을 만들고 싶습니다.'
        parsed = partition_request(text)
        self.assertEqual([s['quote'] for s in parsed['output_hints']], ['출처', '근거', '목록'])
        for span in parsed['output_hints']:
            self.assertEqual(text[span['start']:span['end']], span['quote'])

    def test_cosine_missing_is_unknown_not_negative_evidence(self):
        bank = {'a': np.array([1., 0.]), 'b': np.array([-1., 0.])}
        self.assertIsNone(cosine('', 'a', bank))
        self.assertEqual(cosine('a', 'b', bank), -1.)

    def test_feature_replacement_preserves_dense_token_sparse(self):
        original = np.arange(30.).reshape(3, 10)
        updated = replace_core(original, [None, .2, .8], [.1, .4, .9], [.8, .4, .2])
        np.testing.assert_array_equal(updated[:, :3], original[:, :3])
        np.testing.assert_array_equal(original, np.arange(30.).reshape(3, 10))
        self.assertEqual(updated[0, 7], 0)
        self.assertEqual(updated[1, 7], 1)
        self.assertTrue(np.isfinite(updated).all())


if __name__ == '__main__':
    unittest.main()
