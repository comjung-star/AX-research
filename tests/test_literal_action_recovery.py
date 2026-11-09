import json
from pathlib import Path
import unittest

from ax_research.literal_action_recovery import recover_action_profile
from ax_research.semantic_mapping import field_profile

ROOT = Path(__file__).resolve().parents[1]


def load(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8-sig'))


class LiteralActionRecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load('configs/semantic_mapping_20261028.json')
        cls.guard = load('configs/functional_mapping_20261028.json')['negation_guard']
        cls.rules = load('configs/literal_action_recovery_20261109.json')

    def parse(self, text, context=''):
        return recover_action_profile(text, self.config, self.guard, self.rules, executed=True, context=context)

    def test_multiple_actions_are_literal_and_removed_from_object(self):
        for text, expected in [('문의 응대 및 상담원 인계', ['응대', '인계']),
                               ('Prepare and submit journal entries under approval', ['Prepare', 'submit'])]:
            result = self.parse(text)
            self.assertEqual(result['fields']['action'].splitlines(), expected)
            for span in result['spans']['action']:
                self.assertEqual(text[span['start']:span['end']], span['quote'])
                self.assertNotIn(span['quote'], result['fields']['object'])

    def test_ambiguous_nouns_and_substrings_are_not_promoted(self):
        for text in ['Book title', 'Document title', 'Screen dimensions', '접수번호', '안내문', '조회수']:
            with self.subTest(text=text):
                self.assertEqual(self.parse(text)['fields']['action'], '')

    def test_task_cannot_be_invented_from_context(self):
        self.assertEqual(self.parse('UNKNOWN', context='고객 문의 응대')['fields']['action'], '')
        self.assertEqual(self.parse('')['fields']['action'], '')

    def test_negated_and_planned_clauses_stay_held(self):
        for text in ['Does not resolve customer inquiries', 'Plan to repair instructions in future', '고객 응대 도입 예정']:
            result = self.parse(text)
            self.assertEqual(result['fields']['action'], '')
            self.assertEqual(result['spans']['action'], [])
            self.assertFalse(any(result['fields'].values()))

    def test_existing_action_and_metadata_are_preserved(self):
        text = 'Detect equipment failure risks'
        old = field_profile(text, self.config, self.guard, executed=True)
        result = self.parse(text)
        for key, value in old.items():
            self.assertEqual(result[key], value)
        self.assertFalse(result['action_recovery']['changed'])

    def test_advice_keeps_source_word_without_inventing_synonym_or_output(self):
        result = self.parse('Give online home-improvement project advice')
        self.assertEqual(result['fields']['action'], 'advice')
        self.assertEqual(result['fields']['output'], '')
        self.assertFalse(result['action_recovery']['semantically_verified'])

    def test_partial_hold_does_not_block_supported_literal_action(self):
        result = self.parse('Does not create contacts; Repair incomplete instructions')
        self.assertEqual(result['fields']['action'], 'Repair')
        self.assertEqual(len(result['held_clauses']), 1)

    def test_unknown_action_is_not_forced_to_nonempty(self):
        self.assertEqual(self.parse('업무 현황')['action_recovery']['status'], 'UNKNOWN_NO_LITERAL_ACTION')


if __name__ == '__main__':
    unittest.main()
