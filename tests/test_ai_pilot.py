import json
import unittest

from scripts.claude_blind_questions import parse_output
from scripts.ai_pilot_review_v2 import parse_rows


class AIPilotTests(unittest.TestCase):
    def test_author_output_requires_all40unique_ids(self):
        rows = [{'query_id': f'IVQ{position:03d}', 'sector': 'sector', 'business_problem': f'업무 문제{position}',
                 'input': '입력', 'desired_output': '결과', 'constraints': ''} for position in range(1, 41)]
        response = {'content': [{'type': 'text', 'text': json.dumps({'questions': rows})}]}
        self.assertEqual(len(parse_output(response)), 40)
        rows.pop()
        with self.assertRaises(AssertionError):
            parse_output({'content': [{'type': 'text', 'text': json.dumps({'questions': rows})}]})

    def test_thinking_only_is_not_a_valid_grade_response(self):
        with self.assertRaises(ValueError):
            parse_rows({'content': [{'type': 'thinking', 'thinking': ''}]}, 'claude')

    def test_json_grades_preserve_explicit_zero_and_null(self):
        rows = [{'position': 0, 'grade': 0}, {'position': 1, 'grade': None}]
        raw = {'candidates': [{'content': {'parts': [{'text': json.dumps({'rows': rows})}]}}]}
        self.assertEqual(parse_rows(raw, 'gemini'), rows)


if __name__ == '__main__':
    unittest.main()
