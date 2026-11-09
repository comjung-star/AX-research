"""Replay nested selection, training, held-out rankings and all reported means."""
from statistics import mean

import numpy as np

from ax_research.pairwise_ridge import fit_pairwise, rank_pool, score
from scripts.ranking_audit_20261109 import PREFIX, digest, save
from scripts.improvement_cycle import read
from scripts.improvement_cycle2 import label_sets
from scripts.autonomous_trial2_mapping_replay import metrics


def main():
    inputs = read(PREFIX + '-inputs.json')
    predictions = read(PREFIX + '-predictions.json')
    evaluation = read(PREFIX + '-evaluation.json')
    assert all(digest(p) == h for p, h in inputs['source_sha256'].items())
    assert predictions['input_sha256'] == digest(PREFIX + '-inputs.json')
    assert predictions['training_labels_sha256'] == digest('docs/ax-transfer-relevance-20261108/02_working_transfer_qrels_2240.json')
    assert evaluation['prediction_sha256'] == digest(PREFIX + '-predictions.json')
    grades = label_sets()
    ids, data = inputs['ids'], inputs['inputs']
    x = {q: np.array(row['features']) for q, row in data.items()}
    y = {q: [grades['working_transfer'][q][c] >= 2 for c in ids] for q in data}
    lookup = {(r['query_id'], r['repeat'], r['system']): r['ranking'] for r in predictions['rankings']}
    assert len(lookup) == len(predictions['rankings']) == 300
    seen, reproduced = [], 0
    for model in predictions['models']:
        train, test = model['training_queries'], model['test_queries']
        assert len(train) == 16 and len(test) == 4 and not set(train) & set(test)
        assert set(train) | set(test) == set(data)
        assert all(inputs['outer_folds'][q] == model['outer_fold'] for q in test)
        seen.extend(test)
        for choice in model['choices']:
            validation, seen_inner = [], []
            for split in choice['inner_splits']:
                fit, val = split['training_queries'], split['validation_queries']
                assert len(fit) == 12 and len(val) == 4 and not set(fit) & set(val)
                assert set(fit) | set(val) == set(train) and not set(test) & (set(fit) | set(val))
                seen_inner.extend(val)
                weights = fit_pairwise(x, y, fit, choice['lambda'])
                for q in val:
                    rank = rank_pool(ids, score(x[q], weights, choice['learned_share']), data[q]['pools']['1']['DensePool'], data[q]['dense'])
                    validation.append(metrics(rank, grades['working_transfer'][q]))
            assert sorted(seen_inner) == sorted(train)
            for metric in ('F1@5', 'nDCG@10'):
                actual = mean(r[metric] for r in validation if r[metric] is not None)
                assert abs(actual - choice['validation'][metric]) < 1e-12
        chosen = max(model['choices'], key=lambda c: (c['validation']['F1@5'], c['validation']['nDCG@10'], -c['learned_share'], c['lambda']))
        assert chosen == model['choice']
        w = fit_pairwise(x, y, train, chosen['lambda'])
        np.testing.assert_allclose(w, model['weights'], rtol=0, atol=1e-12)
        for q in test:
            for repeat in (1, 2, 3):
                assert lookup[q, repeat, 'Dense'] == data[q]['dense']
                for pool, candidates in data[q]['pools'][str(repeat)].items():
                    rank = rank_pool(ids, score(x[q], w, chosen['learned_share']), candidates, data[q]['dense'])
                    assert rank == lookup[q, repeat, 'Learned_' + pool]
                    assert set(rank[:20]) == set(candidates)
                    assert len(rank) == len(set(rank)) == 112
                    reproduced += 1
    assert sorted(seen) == sorted(data)
    for version, labels in grades.items():
        result = evaluation['results'][version]
        for q, systems in result['per_query'].items():
            for system, values in systems.items():
                repeats = []
                for repeat in (1, 2, 3):
                    rank = lookup[q, repeat, system]
                    m = metrics(rank, labels[q])
                    positive = sum(v >= 2 for v in labels[q].values())
                    m['Recall@20'] = sum(labels[q][c] >= 2 for c in rank[:20]) / positive if positive else None
                    repeats.append(m)
                for metric, expected in values.items():
                    actual = mean(r[metric] for r in repeats) if repeats[0][metric] is not None else None
                    assert actual == expected or (actual is not None and expected is not None and abs(actual - expected) < 1e-12)
        for system, values in result['summary'].items():
            for metric, value in values.items():
                actual = [r[system][metric] for r in result['per_query'].values() if r[system][metric] is not None]
                assert len(actual) == value['queries'] and abs(mean(actual) - value['mean']) < 1e-12
    profiles = read('docs/query-case-semantic-mapping-2026-10-28/mapping/case_profiles.json')
    index = inputs['feature_names'].index('action_present')
    missing = {c for c in ids if not profiles[c]['fields']['action']}
    assert len(missing) == 24
    assert all({c for c, f in zip(ids, row['features']) if not f[index]} == missing for row in data.values())
    save('-verification', {'state': 'PASS', 'source_hashes_match': True, 'outer_folds': 5,
                           'outer_test_queries_each_used_once': 20, 'inner_query_separation_checked': True,
                           'nested_selection_and_weights_reproduced': True, 'learned_rankings_reproduced': reproduced,
                           'all_three_label_metric_means_recomputed': True,
                           'action_missing_source_cases': len(missing), 'action_missing_pairs': 24 * 20,
                           'semantic_profile_sha256': digest('docs/query-case-semantic-mapping-2026-10-28/mapping/case_profiles.json'),
                           'paid_calls': 0, 'new40_read': False, 'test15_read': False,
                           'not_an_independent_final_test': True})
    print('PASS: nested selection, 180 learned ranks, three-label metric means, 24 source action omissions')


if __name__ == '__main__':
    main()
