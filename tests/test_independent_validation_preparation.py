import csv
import unittest

from scripts.plan_independent_validation import OUT, required_pairs
from scripts.check_independent_inputs import check, normalize_question


class IndependentValidationPreparationTests(unittest.TestCase):
    def test_variance_and_effect_change_planning_size(self):
        reference = required_pairs(.1, .05)
        self.assertGreater(required_pairs(.2, .05), reference * 3)
        self.assertGreater(required_pairs(.1, .025), reference * 3)
        with self.assertRaises(ValueError):
            required_pairs(.1, 0)

    def test_normalization_catches_formatting_only_changes(self):
        self.assertEqual(normalize_question('ＡＢＣ 업무, 확인!'), normalize_question('abc업무확인'))

    def test_blank_author_slots_are_not_collected_questions(self):
        status = check()
        self.assertEqual(status['actual_new_queries'], 0)
        self.assertFalse(status['inference_executed'])
        self.assertTrue(status['source_freeze_matches'])

    def test_review_forms_are_complete_and_ungraded(self):
        for reviewer in ('A', 'B'):
            with (OUT / 'review' / f'reviewer_{reviewer}_to_fill.csv').open(encoding='utf-8-sig', newline='') as source:
                rows = list(csv.DictReader(source))
            self.assertEqual(len(rows), 4480)
            self.assertEqual(len({(row['query_id'], row['case_id']) for row in rows}), 4480)
            self.assertTrue(all(not row['grade_0_to_3'] and not row['reviewer_id'] for row in rows))


if __name__ == '__main__':
    unittest.main()
