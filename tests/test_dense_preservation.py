import unittest

from ax_research.dense_preservation import preserve_dense, preserve_dense_core, preserve_dense_candidates


class DensePreservationTests(unittest.TestCase):
    def test_protected_head_and_equal_output_budget(self):
        dense = dict(zip('abcdef', [.9, .8, .7, .6, .5, .4]))
        token = dict(zip('abcdef', [.9, .8, .7, .1, .1, 1.]))
        result = preserve_dense(dense, token, budget=6)
        self.assertEqual(result['ranking'][:3], ['a', 'b', 'c'])
        self.assertIn('f', result['ranking'][:5])
        self.assertEqual(len(result['ranking'][:5]), 5)
        self.assertNotIn('a', result['lost_dense_top5'])

    def test_branch_can_supply_case_beyond_original_top20(self):
        ids = [f'case{position:02d}' for position in range(30)]
        dense = {case: 30 - position for position, case in enumerate(ids)}
        token = {case: float(case == ids[-1]) for case in ids}
        single = preserve_dense(dense, token)
        multi = preserve_dense(dense, token, {'separate_branch': list(reversed(ids))})
        self.assertNotIn(ids[-1], single['candidates'])
        self.assertIn(ids[-1], multi['candidates'])
        self.assertIn(ids[-1], multi['ranking'][:5])
        self.assertEqual(len(single['candidates']), len(multi['candidates']))

    def test_unsupported_branch_case_is_not_promoted(self):
        ids = [f'case{position:02d}' for position in range(30)]
        dense = {case: 30 - position for position, case in enumerate(ids)}
        token = dict.fromkeys(ids, 0.)
        result = preserve_dense(dense, token, {'branch': list(reversed(ids))})
        self.assertEqual(result['ranking'][:5], ids[:5])
        self.assertEqual(result['branch_candidates'], {})

    def test_invalid_branch_registry_is_rejected(self):
        dense = dict(zip('abcdef', range(6)))
        with self.assertRaises(ValueError):
            preserve_dense(dense, dense, {'branch': list('abcdee')}, budget=6)

    def test_core_gate_requires_both_action_and_object(self):
        dense = dict(zip('abcdef', [.9, .8, .7, .6, .5, .4]))
        token = dict(zip('abcdef', [.9, .8, .7, .1, .1, 1.]))
        core = {case: {'action': .5, 'object': .5} for case in dense}
        core['f'] = {'action': .9, 'object': .4}
        unchanged = preserve_dense_core(dense, token, core, budget=6)
        self.assertEqual(unchanged['ranking'], list('abcdef'))
        core['f']['object'] = .9
        supported = preserve_dense_core(dense, token, core, budget=6)
        self.assertEqual(supported['ranking'][:3], list('abc'))
        self.assertIn('f', supported['ranking'][:5])

    def test_unknown_core_falls_back_to_dense(self):
        dense = dict(zip('abcdef', [.9, .8, .7, .6, .5, .4]))
        token = dict(zip('abcdef', [0., 0., 0., 0., 0., 1.]))
        core = {case: {'action': None, 'object': .5} for case in dense}
        self.assertEqual(preserve_dense_core(dense, token, core, budget=6)['ranking'], list('abcdef'))

    def test_candidate_complement_cannot_change_top10(self):
        ids = [f'case{position:02d}' for position in range(30)]
        dense = {case: 30 - position for position, case in enumerate(ids)}
        token = {case: float(case == ids[-1]) for case in ids}
        core = {case: {'action': .9 if case == ids[-1] else .5, 'object': .9 if case == ids[-1] else .5} for case in ids}
        result = preserve_dense_candidates(dense, token, core, {'branch': list(reversed(ids))})
        self.assertEqual(result['ranking'][:10], ids[:10])
        self.assertIn(ids[-1], result['candidates'])
        self.assertNotIn(ids[-1], result['ranking'][:5])
        out_of_depth = preserve_dense_candidates(dense, token, core, {'branch': ids})
        self.assertNotIn(ids[-1], out_of_depth['candidates'])


if __name__ == '__main__':
    unittest.main()
