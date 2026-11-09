import unittest

from ax_research.pilot_case_recommender import recommend_cases
from scripts.pilot_case_recommendation import inputs, recommend


def fixed_scores(perspective, question, ids):
    return {case: 0.1 for case in ids}


class PilotCaseRecommendationTests(unittest.TestCase):
    def run_question(self, text, k=5):
        return recommend(text, scorer=fixed_scores, max_results=k)

    def test_only_supported_links_can_enter_the_candidate_pool(self):
        result = self.run_question('사내 규정에서 필요한 근거를 검색해주세요.')
        ids = {r['case_id'] for r in result['recommendations']}
        self.assertEqual(ids, {'AXALL_US_OMB_2025_02663', 'AXV2N_0110', 'AXV2P2_0010_01'})
        self.assertNotIn('AXV24_f27ca1e6fb82', ids)

    def test_night_support_is_not_inherited_from_the_perspective(self):
        result = self.run_question('야간 문의가 누락돼 고객 문의에 응대하고 싶습니다.')
        self.assertEqual({r['case_id'] for r in result['recommendations']}, {'AXV24_df5d48fedff4', 'AXV2H_0001_01'})
        self.assertTrue(result['condition_confirmation_queue'])

    def test_night_and_voice_unknown_yields_no_recommendation(self):
        result = self.run_question('야간 음성 문의가 누락돼 고객 문의에 응대하고 싶습니다.')
        self.assertTrue(result['perspective_selection']['selected'])
        self.assertFalse(result['recommendations'])
        self.assertEqual(result['state'], 'NO_SOURCE_SUPPORTED_CASE_FOR_REQUIRED_CONDITIONS')

    def test_voice_only_has_one_explicit_supported_reference(self):
        result = self.run_question('고객 음성 문의가 몰려 대기가 깁니다. 문의에 응답하고 싶습니다.')
        self.assertEqual([r['case_id'] for r in result['recommendations']], ['AXV24_71def85d86bd'])

    def test_same_case_is_deduplicated_and_keeps_both_perspective_paths(self):
        result = self.run_question('의뢰 자료의 자유서술 항목을 구조화하고 필수 항목의 누락을 확인해주세요.')
        rows = [r for r in result['recommendations'] if r['case_id'] == 'AXALL_US_OMB_2025_01754']
        self.assertEqual(len(rows), 1)
        self.assertEqual(set(rows[0]['perspective_ids']), {'P02', 'P03'})
        self.assertEqual(len({r['case_id'] for r in result['recommendations']}), len(result['recommendations']))

    def test_direct_object_and_reference_scope_precedes_transfer_candidates(self):
        result = self.run_question('운송 청구서 금액을 계약 요율과 대조해주세요.')
        first = result['recommendations'][0]
        self.assertEqual(first['case_id'], 'AXV2P2_0011_01')
        self.assertEqual(first['relationship'], 'DIRECT_WORK_TYPE_CANDIDATE')
        self.assertTrue(any(r['relationship'] == 'FUNCTIONAL_TRANSFER_CANDIDATE' for r in result['recommendations']))

    def test_unknown_requested_fields_are_not_promised(self):
        result = self.run_question('보험 청구서 PDF에서 고객명과 계좌번호를 추출해주세요.')
        first = result['recommendations'][0]
        self.assertEqual(first['case_id'], 'AXV24_bc6444cc1b61')
        self.assertTrue({'고객명', '계좌번호'} <= set(first['routes'][0]['unverified_fields']))
        self.assertFalse(first['routes'][0]['confirmed_query_answer'])

    def test_unknown_read_only_condition_is_not_certified(self):
        result = self.run_question('읽기 전용으로 청구서 금액을 계약과 대조해주세요.')
        self.assertFalse(result['recommendations'])

    def test_input_and_availability_conditions_stay_with_their_branches(self):
        result = self.run_question('보험 청구서 PDF에서 정보를 추출해주세요. 야간 문의가 누락돼 고객 문의에 응대하고 싶습니다.')
        self.assertEqual(result['requirements_by_perspective']['P02']['inputs'], ['pdf'])
        self.assertEqual(result['requirements_by_perspective']['P04']['inputs'], ['night'])
        represented = {p for r in result['recommendations'] for p in r['perspective_ids']}
        self.assertEqual(represented, {'P02', 'P04'})

    def test_outside_business_hours_is_not_assumed_for_every_night_case(self):
        result = self.run_question('영업시간 외 문의가 누락돼 고객 문의에 응대하고 싶습니다.')
        self.assertEqual([r['case_id'] for r in result['recommendations']], ['AXV2H_0001_01'])

    def test_no_card_no_case_and_no_score_call(self):
        def forbidden(*args):
            raise AssertionError('Scorer must not run')
        result = recommend('다음 달 상품 수요를 예측해주세요.', scorer=forbidden)
        self.assertFalse(result['recommendations'])
        self.assertEqual(result['state'], 'UNSUPPORTED_BY_PILOT')

    def test_auto_modify_is_partial_reference_support_not_execution(self):
        result = self.run_question('청구서 금액을 계약과 대조하고 자동 수정해주세요.')
        self.assertEqual(result['state'], 'PARTIAL_REFERENCE_SUPPORT')
        self.assertFalse(result['automatic_execution_performed'])
        self.assertTrue(result['perspective_selection']['outside_work'])

    def test_budget_and_literal_evidence(self):
        question = '청구서에서 금액을 뽑고 계약 금액과 비교해주세요.'
        result = self.run_question(question, 2)
        self.assertLessEqual(len(result['recommendations']), 2)
        represented = {p for r in result['recommendations'] for p in r['perspective_ids']}
        self.assertEqual(represented, {'P02', 'P03'})
        _, _, _, registry = inputs()
        for row in result['recommendations']:
            for route in row['routes']:
                for e in route['source_evidence']:
                    self.assertEqual(registry[row['case_id']][e['field']][e['start']:e['end']], e['quote'])
                for e in route['query_evidence']:
                    self.assertEqual(question[e['start']:e['end']], e['quote'])

    def test_invalid_budget_rejected(self):
        catalog, rules, profiles, registry = inputs()
        with self.assertRaises(ValueError):
            recommend_cases('문서를 검색해주세요.', catalog, rules, profiles, registry, fixed_scores, max_results=21)


if __name__ == '__main__':
    unittest.main()
