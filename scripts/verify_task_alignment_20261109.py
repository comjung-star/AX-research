"""Independent feature reconstruction, nested-selection replay and metric check."""
from statistics import mean

import numpy as np

from ax_research.task_alignment import cosine, partition_request, replace_core
from ax_research.pairwise_ridge import unit
from scripts.task_alignment_20261109 import PREFIX, POOLS, VARIANTS, nested_variant, save, sha
from scripts.improvement_cycle import ROOT, read
from scripts.improvement_cycle2 import label_sets
from scripts.autonomous_trial2_mapping_replay import interval, metrics


def same(actual, expected):
    if actual is None or expected is None:
        assert actual is expected
    else:
        assert abs(actual - expected) < 1e-10, (actual, expected)


def main():
    inputs, prediction, evaluation = [read(PREFIX + s + '.json') for s in ('-inputs', '-predictions', '-evaluation')]
    assert all(sha(ROOT / p) == h for p, h in inputs['source_sha256'].items())
    assert prediction['input_sha256'] == sha(ROOT / (PREFIX + '-inputs.json'))
    assert evaluation['prediction_sha256'] == sha(ROOT / (PREFIX + '-predictions.json'))
    assert inputs['vectors_sha256'] == sha(ROOT / (PREFIX + '-vectors.npz'))
    assert prediction['training_labels_sha256'] == sha(ROOT / 'docs/ax-transfer-relevance-20261108/02_working_transfer_qrels_2240.json')
    with np.load(ROOT / (PREFIX + '-vectors.npz'), allow_pickle=False) as z:
        bank = dict(zip(z['texts'].tolist(), z['vectors']))
    cases = read('docs/literal-action-recovery-20261109/case_profiles.json')
    old_queries = read('.work-new20-runtime/original/predictions/evidence.json')['query_profiles']
    old_scores = read('docs/dense-preserved-candidates-20261108-predictions.json')['inputs']
    ids = inputs['ids']
    restored, retained, output_pairs = 0, 0, 0
    for q, row in inputs['inputs'].items():
        partition = inputs['partitions'][q]
        assert partition == partition_request(partition['source_text'])
        for span in partition['pieces'] + partition['output_hints']:
            assert partition['source_text'][span['start']:span['end']] == span['quote']
        assert not partition['fallback_used'] and partition['requested_text']
        raw = inputs['raw_field_scores'][q]
        for i, c in enumerate(ids):
            old, cp, active = old_queries[q]['fields'], cases[c]['fields'], inputs['active_profiles'][q]['fields']
            for field in ('action', 'object'):
                expected = cosine(old[field], cp[field], bank) if cases[c]['action_recovery']['changed'] else old_scores[q]['core'][c][field]
                same(raw['Recovered'][field][i], expected)
                same(raw['WorkAligned'][field][i], cosine(active[field], cp[field], bank))
            if cases[c]['action_recovery']['changed']:
                assert raw['Recovered']['action'][i] is not None
                restored += 1
            else:
                retained += 1
            expected_values = {'task': cosine(active['task'], cp['task'], bank),
                               'excluded_task': cosine(partition['excluded_text'], cp['task'], bank),
                               'output_task_proxy': cosine(partition['output_hint_text'], cp['task'], bank),
                               'explicit_output': cosine(partition['output_hint_text'], cp['output'], bank)}
            for field, value in expected_values.items():
                same(raw['WorkAligned'][field][i], value or 0.)
            same(raw['WorkAligned']['output_pair_present'][i], float(expected_values['explicit_output'] is not None))
            output_pairs += int(expected_values['explicit_output'] is not None)
        base = np.array(row['features'])
        np.testing.assert_allclose(row['variants']['Recovered'], replace_core(base, raw['Recovered']['action'], raw['Recovered']['object']), rtol=0, atol=1e-12)
        work = raw['WorkAligned']
        rebuilt = np.column_stack([replace_core(base, work['action'], work['object'], work['task']),
                    unit(work['excluded_task']), unit(work['output_task_proxy']), unit(work['explicit_output']), work['output_pair_present']])
        np.testing.assert_allclose(row['variants']['WorkAligned'], rebuilt, rtol=0, atol=1e-12)
    assert restored == 480 and retained == 1760
    # Refit/select using only the working labels; other versions are loaded later.
    working = read('docs/ax-transfer-relevance-20261108/02_working_transfer_qrels_2240.json')
    grades = {q: {} for q in inputs['inputs']}
    for r in working['records']:
        grades[r['query_id']][r['case_id']] = r['grade']
    lookup = {(r['query_id'], r['repeat'], r['system']): r['ranking'] for r in prediction['rankings']}
    assert len(lookup) == len(prediction['rankings']) == 660
    for variant in VARIANTS:
        ranks, models = nested_variant(inputs, grades, variant)
        assert models == prediction['models'][variant]
        held = []
        for m in models:
            train, test = set(m['training_queries']), set(m['test_queries'])
            assert len(train) == 16 and len(test) == 4 and not train & test
            held.extend(test)
            for choice in m['choices']:
                inner_held = []
                for split in choice['inner_splits']:
                    fit, val = set(split['training_queries']), set(split['validation_queries'])
                    assert len(fit) == 12 and len(val) == 4 and not fit & val
                    assert fit | val == train and not test & (fit | val)
                    inner_held.extend(val)
                assert set(inner_held) == train and len(inner_held) == 16
        assert len(held) == 20 and set(held) == set(inputs['inputs'])
        for r in ranks:
            assert r['ranking'] == lookup[r['query_id'], r['repeat'], r['system']]
            pool = r['system'][len(variant) + 1:]
            candidates = inputs['inputs'][r['query_id']]['pools'][str(r['repeat'])][pool]
            assert set(r['ranking'][:20]) == set(candidates)
            assert len(r['ranking']) == len(set(r['ranking'])) == 112
    legacy = read('docs/ranking-audit-20261109-predictions.json')['rankings']
    for r in legacy:
        assert lookup[r['query_id'], r['repeat'], r['system'].replace('Learned_', 'Legacy_')] == r['ranking']
    for version, labels in label_sets().items():
        result = evaluation['results'][version]
        for q, systems in result['per_query'].items():
            positive = sum(v >= 2 for v in labels[q].values())
            for system, values in systems.items():
                rows = []
                for repeat in (1, 2, 3):
                    rank = lookup[q, repeat, system]
                    m = metrics(rank, labels[q])
                    m['Recall@20'] = sum(labels[q][c] >= 2 for c in rank[:20]) / positive if positive else None
                    rows.append(m)
                for metric, expected in values.items():
                    same(mean(r[metric] for r in rows) if rows[0][metric] is not None else None, expected)
        for system, values in result['summary'].items():
            for metric, value in values.items():
                rows = [r[system][metric] for r in result['per_query'].values() if r[system][metric] is not None]
                same(mean(rows), value['mean'])
                assert len(rows) == value['queries']
        for method, comparisons in result['ablation_comparisons'].items():
            for baseline, values in comparisons.items():
                for metric, value in values.items():
                    differences = [r[method][metric] - r[baseline][metric] for r in result['per_query'].values() if r[method][metric] is not None]
                    same(mean(differences), value['delta'])
                    if baseline == 'Dense' and metric == 'F1@5':
                        assert interval(differences) == value['interval95']
    for method, decision in evaluation['decisions'].items():
        ok = True
        for version, result in evaluation['results'].items():
            values = result['ablation_comparisons'][method]['Dense']
            checks = {'f1_improves': values['F1@5']['delta'] > 0, 'ndcg_non_decreasing': values['nDCG@10']['delta'] >= -1e-12}
            assert checks == decision['checks'][version]
            ok = ok and all(checks.values())
        low = evaluation['results']['working_transfer']['ablation_comparisons'][method]['Dense']['F1@5']['interval95'][0]
        assert low == decision['working_f1_ci_lower']
        assert decision['decision'] == ('PROVISIONAL_DEV_ONLY' if ok and low > 0 else 'DO_NOT_ADOPT')
    save('-verification', {'state': 'PASS', 'source_hashes_match': True, 'vector_hash_matches': True,
                           'restored_action_cosine_pairs': restored, 'unchanged_case_cosine_pairs': retained,
                           'explicit_output_pairs': output_pairs, 'literal_query_spans_verified': True,
                           'nested_choices_weights_and360_rankings_reproduced': True,
                           'three_label_metrics_and_decisions_verified': True,
                           'paid_calls': 0, 'new40_read': False, 'test15_read': False,
                           'not_an_independent_test': True})
    print('PASS: field features, 480 restored action cosines, nested fits, 360 ranks, metrics and stop decisions')


if __name__ == '__main__':
    main()
