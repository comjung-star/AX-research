import unittest
import numpy as np
import torch

from scripts.improvement_cycle import read
from scripts.improvement_cycle3 import canonical_tokens, normalize_scores
from scripts.autonomous_trial2_mapping_replay import metrics
from scripts.improvement_cycle4 import assign_folds, pairwise_training
from scripts.improvement_cycle5 import bounded_scores
from scripts.improvement_cycle6 import fidelity_weights
from scripts.improvement_cycle9 import VectorInteraction
from scripts.improvement_cycle10 import token_scores
from scripts.improvement_cycle12 import route
from ax_research.token_interaction import TokenInteractionRanker


class ImprovementCycleTests(unittest.TestCase):
    def test_constant_sparse_scores_do_not_invent_evidence(self):
        self.assertEqual(normalize_scores([0, 0, 0]), [0, 0, 0])
        self.assertEqual(normalize_scores([-2, 0, 2]), [0, .5, 1])

    def test_bilingual_productions_share_canonical_function(self):
        rules = read('configs/functional_mapping_20261028.json')
        config = read('configs/action_aggregation_20261102.json')
        english = canonical_tokens('Extract data from documents', rules, config, executed=True)
        korean = canonical_tokens('문서에서 데이터를 추출한다', rules, config)
        self.assertIn('function_extract_fields', english)
        self.assertIn('function_extract_fields', korean)
        negated = canonical_tokens('We do not extract data from documents', rules, config, executed=True)
        self.assertNotIn('function_extract_fields', negated)

    def test_short_candidate_list_uses_all_case_ideal_gain(self):
        grades = {'first': 3, 'second': 2, 'third': 0}
        result = metrics(['second', 'third'], grades)
        self.assertAlmostEqual(result['F1@5'], 2 / 7)
        self.assertLess(result['nDCG@10'], 1)

    def test_fold_assignment_does_not_depend_on_input_order(self):
        queries = [f'query{position}' for position in range(20)]
        folds = assign_folds(queries)
        self.assertEqual(folds, assign_folds(reversed(queries)))
        self.assertEqual([sum(value == fold for value in folds.values()) for fold in range(5)], [4] * 5)

    def test_heldout_labels_cannot_enter_training_pairs(self):
        features = {('train', 'positive'): np.array([2., 1.]), ('train', 'negative'): np.array([1., 0.])}
        labels = {'train': {'positive': 2, 'negative': 0}, 'heldout': {'unreadable': 3}}
        differences, targets, weights = pairwise_training(features, labels, ['train'])
        np.testing.assert_equal(differences, [[1., 1.], [-1., -1.]])
        np.testing.assert_equal(targets, [1, 0])
        np.testing.assert_equal(weights, [1., 1.])

    def test_residual_cannot_override_dense_without_bound(self):
        dense = torch.tensor([.1, .4, .9])
        residual = torch.tensor([-1000., 0., 1000.])
        shifted = bounded_scores(dense, residual)
        self.assertTrue(torch.all(torch.abs(shifted - dense) <= .050001))
        self.assertEqual(float(shifted[1]), float(dense[1]))
        self.assertGreater(float(shifted[2]), float(shifted[0]))

    def test_fidelity_weights_are_normalized_and_ordered(self):
        weights = fidelity_weights([.8, .5, .2])
        self.assertAlmostEqual(float(weights.sum()), 1)
        self.assertTrue(weights[0] > weights[1] > weights[2] > 0)
        np.testing.assert_allclose(fidelity_weights([.4, .4, .4]), [1 / 3] * 3)

    def test_vector_interaction_retains_branch_and_case_views(self):
        torch.manual_seed(11)
        model = VectorInteraction(dimensions=4)
        model.eval()
        original = torch.randn(1, 4)
        cases = torch.randn(5, 3, 4)
        with torch.no_grad():
            single, _, _ = model(original, cases)
            pooled, branches, views = model(original.expand(4, 4), cases)
        self.assertEqual(tuple(branches.shape), (5, 4))
        self.assertEqual(tuple(views.shape), (5, 4, 3))
        torch.testing.assert_close(single, pooled)
        torch.testing.assert_close(branches, views.mean(dim=-1))

    def test_token_matching_keeps_case_boundaries(self):
        query = torch.tensor([[1., 0.], [0., 1.]])
        exact = torch.tensor([[1., 0.], [0., 1.]])
        partial = torch.tensor([[1., 0.]])
        opposite = torch.tensor([[-1., 0.]])
        self.assertEqual(token_scores(query, [exact, partial, opposite]), [1., .5, -.5])

    def test_router_cannot_read_heldout_grades_to_choose_method(self):
        features = {'left': [-1., 0.], 'right': [1., 0.], 'heldout': [.2, 0.]}
        grades = {'left': {'positive': 2, **{str(position): 0 for position in range(5)}},
                  'right': {'positive': 2, **{str(position): 0 for position in range(5)}}, 'heldout': object()}
        good = ['positive', '0', '1', '2', '3', '4']
        bad = ['0', '1', '2', '3', '4', 'positive']
        ranks = {(query, repeat, method): good if (query == 'left') == (method == 'E') else bad
                 for query in ('left', 'right') for repeat in (1, 2, 3) for method in ('E', 'Token')}
        first, first_audit = route(features, ['left', 'right'], ['heldout'], grades, ranks)
        grades['heldout'] = {'different': None}
        second, second_audit = route(features, ['left', 'right'], ['heldout'], grades, ranks)
        self.assertEqual(first, second)
        self.assertEqual(first_audit, second_audit)
        self.assertNotIn('heldout', first_audit['targets'])

    def test_reusable_ranker_rejects_registry_drift_and_invalid_vectors(self):
        ranker = TokenInteractionRanker({'first': np.array([[1., 0.]]), 'second': np.array([[0., 1.]])})
        with self.assertRaises(ValueError):
            ranker.rank([[1., 0.]], {'first': .5})
        with self.assertRaises(ValueError):
            ranker.rank([[1., 0., 0.]], {'first': .5, 'second': .2})
        with self.assertRaises(ValueError):
            ranker.rank([[float('nan'), 0.]], {'first': .5, 'second': .2})

    def test_identical_branch_cannot_change_original_scores(self):
        ranker = TokenInteractionRanker({'first': np.array([[1., 0.]]), 'second': np.array([[0., 1.]])})
        query = np.array([[1., 0.]])
        dense = {'first': .8, 'second': .2}
        original = ranker.rank(query, dense)
        repeated = ranker.rank(query, dense, {'same': {'tokens': query, 'dense_scores': dense, 'query_cosine': 1.}})
        self.assertEqual(original['ranking'], repeated['ranking'])
        self.assertEqual(original['scores'], repeated['scores'])
        self.assertEqual(repeated['branch_weights'], {'same': 1.})


if __name__ == '__main__':
    unittest.main()
