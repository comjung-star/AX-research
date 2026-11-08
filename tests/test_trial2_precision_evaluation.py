import unittest

from ax_research.action_aggregation import compose
from scripts.autonomous_trial2_evaluate import evaluate


class PrecisionEvaluationTests(unittest.TestCase):
    def test_candidate_independence_preserves_branch_winner(self):
        score = compose(0, {'branch_one': 3, 'branch_two': 1}, .1,
                        {'branch_one': .6, 'branch_two': .9})
        self.assertEqual(score['rule_strength'], 3)
        self.assertEqual(score['rule_winner_paths'], ['branch_one'])
        self.assertEqual(set(score['allowed_paths']), {'branch_one', 'branch_two'})

    def test_repeats_do_not_become_independent_samples(self):
        records = [{'query_id': query, 'case_id': case, 'grade': 3 if query == 'positive' and case == 0 else 0}
                   for query in ('positive', 'zero') for case in range(20)]
        prediction = {'records': [{'query_id': query, 'repeat': repeat, 'policy': policy, 'ranking': list(range(20))}
                                  for query in ('positive', 'zero') for repeat in range(3)
                                  for policy in ('baseline', 'proposed')]}
        result = evaluate(prediction, records)['summary']
        self.assertEqual(result['F1@5']['queries'], 1)
        self.assertEqual(result['P@5']['queries'], 2)
        self.assertEqual(result['F1@5']['paired_bootstrap95'], [0, 0])
