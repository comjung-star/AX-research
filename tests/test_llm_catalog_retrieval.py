import copy
import unittest

from ax_research.llm_catalog_selector import normalize
from ax_research.llm_catalog_retrieval import adapt_selection, recommend_llm, recommend_from_selection
from ax_research.pilot_case_recommender import recommend_cases
from ax_research.pilot_perspective_selector import select_perspectives
from scripts.pilot_case_recommendation import inputs
from scripts.improvement_cycle import read


def scores(p, q, ids):
    return {c: .1 for c in ids}


def fixture(question, definitions, constraints=None):
    decisions = []
    for p in ('P01', 'P02', 'P03', 'P04'):
        evidence = [{'kind': kind, 'quote': quote} for kind, quote in definitions.get(p, [])]
        decisions.append({'id': p, 'status': 'SELECTED' if p in definitions else 'NOT_SELECTED',
            'rationale': '검사용 선택', 'evidence': evidence, 'missing_information': []})
    return normalize(question, {'decisions': decisions, 'scope_status': 'MATCHED' if definitions else 'UNSUPPORTED_BY_PILOT',
        'unsupported_work': [], 'constraints': constraints or []})


class LLMCatalogRetrievalTests(unittest.TestCase):
    def setUp(self):
        self.catalog, self.rules, self.profiles, self.registry = inputs()

    def run_llm(self, q, d):
        return recommend_llm(q, d, self.catalog, self.rules, self.profiles, self.registry, scores)

    def test_injected_rule_selection_exactly_reproduces_unchanged_core(self):
        questions = ['사내 규정을 검색해주세요.', '청구서에서 금액을 추출해주세요.',
            '청구서 금액을 계약과 대조해주세요.', '야간 문의가 누락돼 문의에 응대하고 싶습니다.',
            '청구서에서 금액을 추출하고 계약 기준과 대조해주세요.', '다음 달 수요를 예측해주세요.']
        for q in questions:
            sel = select_perspectives(q, self.catalog, self.rules)
            original = recommend_cases(q, self.catalog, self.rules, self.profiles, self.registry, scores)
            actual = recommend_from_selection(q, sel, self.catalog, self.rules, self.profiles, self.registry, scores)
            self.assertEqual(actual, original)

    def test_existing_saved_multiple_branches_preserve_provenance_and_budget(self):
        normalized = read('docs/llm-catalog-selector-20261109/normalized-selections.json')['D11']
        r = self.run_llm(normalized['question'], normalized)
        self.assertEqual(set(r['branches']), {'P01', 'P02', 'P03'})
        self.assertLessEqual(len(r['recommendations']), 5)
        self.assertEqual(len(r['recommendations']), len({c['case_id'] for c in r['recommendations']}))
        self.assertEqual({p for c in r['recommendations'] for p in c['perspective_ids']}, {'P01', 'P02', 'P03'})

    def test_pdf_and_night_conditions_do_not_cross_separate_tasks(self):
        normalized = read('docs/llm-catalog-selector-20261109/normalized-selections.json')['D12']
        r = self.run_llm(normalized['question'], normalized)
        self.assertIn('pdf', r['requirements_by_perspective']['P02']['inputs'])
        self.assertNotIn('night', r['requirements_by_perspective']['P02']['inputs'])
        self.assertIn('night', r['requirements_by_perspective']['P04']['inputs'])
        self.assertNotIn('pdf', r['requirements_by_perspective']['P04']['inputs'])
        self.assertEqual(len(r['branches']['P04']), 2)

    def test_ambiguous_single_clause_conditions_are_pending_not_propagated(self):
        q = '보험 청구서 PDF에서 항목을 추출하고 야간 고객 문의에 응답해주세요.'
        d = fixture(q, {'P02': [('WORK','항목을 추출'), ('OBJECT','보험 청구서 PDF')],
            'P04': [('WORK','문의에 응답'), ('OBJECT','고객 문의'), ('CAPACITY','야간')]})
        r = self.run_llm(q, d)
        self.assertFalse(r['recommendations'])
        self.assertTrue(r['perspective_selection']['adapter_review_required'])

    def test_same_case_two_views_is_deduplicated_with_both_routes(self):
        q = '의뢰 자료의 자유서술 항목을 구조화하고 필수 항목의 누락을 확인해주세요.'
        d = fixture(q, {'P02': [('WORK','구조화'), ('OBJECT','의뢰 자료')],
            'P03': [('WORK','누락을 확인'), ('OBJECT','의뢰 자료'), ('REFERENCE','필수 항목')]})
        r = self.run_llm(q, d)
        referral = [v for v in r['recommendations'] if v['case_id']=='AXALL_US_OMB_2025_01754']
        self.assertEqual(len(referral), 1)
        self.assertEqual(set(referral[0]['perspective_ids']), {'P02','P03'})

    def test_unknown_night_voice_conditions_still_reject_cases(self):
        q = '야간 음성 문의가 누락돼 고객 문의에 응대하고 싶습니다.'
        d = fixture(q, {'P04': [('WORK','문의에 응대'),('OBJECT','고객 문의'),('CAPACITY','야간 음성 문의가 누락')]})
        self.assertFalse(self.run_llm(q,d)['recommendations'])

    def test_unknown_read_only_still_rejects_cases(self):
        q = '읽기 전용으로 청구서 금액을 계약과 대조해주세요.'
        d = fixture(q, {'P03': [('WORK','대조'),('OBJECT','청구서 금액'),('REFERENCE','계약')]})
        self.assertFalse(self.run_llm(q,d)['recommendations'])

    def test_wrong_question_is_rejected(self):
        d = read('docs/llm-catalog-selector-20261109/normalized-selections.json')['D01']
        with self.assertRaises(ValueError):
            self.run_llm('다른 질문',d)

    def test_existing_parser_scope_conflict_stays_pending(self):
        q = '과거에는 문서를 검색했습니다.'
        d = fixture(q, {'P01':[('WORK','검색'),('OBJECT','문서')]})
        r = self.run_llm(q,d)
        self.assertFalse(r['recommendations'])
        self.assertTrue(r['perspective_selection']['adapter_review_required'])

    def test_new_comparison_keeps_empty_positive_answers_and_zero_positive_queries(self):
        from scripts.llm_catalog_retrieval_comparison_20261109 import assess, SYSTEMS
        predictions = {'q1': {'systems': {s: {'ranking': ['a'], 'candidates': ['a', 'b']} for s in SYSTEMS}},
            'q2': {'systems': {s: {'ranking': [], 'candidates': []} for s in SYSTEMS}}}
        predictions['q1']['systems']['E_LLMCatalog17'] = {'ranking': [], 'candidates': []}
        grades = {'q1': {'a': 3, 'b': 0}, 'q2': {'a': 0, 'b': 0}}
        r = assess(predictions, grades, ['a', 'b'])
        self.assertEqual(r['positive_questions'], 1)
        self.assertEqual(r['summary']['E_LLMCatalog17']['F1@5']['mean'], 0)
        self.assertEqual(r['summary']['E_LLMCatalog17']['output']['positive_but_empty'], 1)
        self.assertEqual(r['summary']['A_Dense17']['F1@5']['mean'], 1)
        self.assertEqual(r['contrasts']['E_LLMCatalog17:A_Dense17']['F1@5']['delta'], -1)
