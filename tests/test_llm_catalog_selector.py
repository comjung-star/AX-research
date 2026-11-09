import copy
import unittest

from ax_research.llm_catalog_selector import normalize, parse_response, request_body, span
from scripts.improvement_cycle import read


def sample():
    return {'decisions': [{'id': p, 'status': 'SELECTED' if p == 'P03' else 'NOT_SELECTED',
        'rationale': '질문의 요청 기준으로 판단', 'missing_information': [],
        'evidence': [{'kind': k, 'quote': q} for k, q in [('WORK', '대조'), ('OBJECT', '청구서'), ('REFERENCE', '계약')]] if p == 'P03' else []}
        for p in ('P01', 'P02', 'P03', 'P04')],
        'scope_status': 'MATCHED', 'unsupported_work': [], 'constraints': []}


class LLMCatalogSelectorTests(unittest.TestCase):
    question = '청구서 금액을 계약과 대조해주세요.'

    def test_literal_evidence_and_selected_ids(self):
        r = normalize(self.question, sample())
        self.assertEqual(r['selected_ids'], ['P03'])
        for d in r['decisions']:
            for e in d['evidence']:
                self.assertEqual(self.question[e['start']:e['end']], e['quote'])

    def test_fabricated_or_reworded_quotes_are_rejected(self):
        d = sample()
        d['decisions'][2]['evidence'][0]['quote'] = '계약 요율'
        with self.assertRaises(ValueError):
            normalize(self.question, d)

    def test_missing_reference_evidence_is_rejected(self):
        d = sample()
        d['decisions'][2]['evidence'].pop()
        with self.assertRaises(ValueError):
            normalize(self.question, d)

    def test_duplicate_or_unknown_perspectives_are_rejected(self):
        for value in ('P01', 'P99'):
            d = sample()
            d['decisions'][2]['id'] = value
            with self.assertRaises(ValueError):
                normalize(self.question, d)

    def test_state_and_decisions_cannot_disagree(self):
        d = sample()
        d['scope_status'] = 'UNSUPPORTED_BY_PILOT'
        with self.assertRaises(ValueError):
            normalize(self.question, d)

    def test_pending_requires_missing_information(self):
        d = sample()
        d['decisions'][2]['status'] = 'PENDING'
        d['scope_status'] = 'REVIEW_NEEDED'
        with self.assertRaises(ValueError):
            normalize(self.question, d)

    def test_repeated_quotes_preserve_all_locations(self):
        e = span('계약과 계약', '계약')
        self.assertEqual(e['occurrence_starts'], [0, 4])

    def test_request_excludes_case_links_and_expected_answers(self):
        config = read('configs/llm_catalog_selector_20261109.json')
        cards = read(config['source_catalog'])['cards']
        body = request_body(self.question, config, cards)
        text = body['messages'][0]['content']
        self.assertNotIn('case_id', text)
        self.assertNotIn('allowed_selected', text)
        self.assertNotIn('AXV2', text)
        self.assertNotIn('temperature', body)
        self.assertEqual(body['output_config']['effort'], 'high')
        reverse = request_body(self.question, config, cards, reverse=True)
        self.assertNotEqual(text, reverse['messages'][0]['content'])

    def test_truncated_responses_are_not_scored_as_success(self):
        with self.assertRaises(ValueError):
            parse_response(self.question, {'stop_reason': 'max_tokens', 'content': []})


if __name__ == '__main__':
    unittest.main()
