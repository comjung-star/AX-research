"""Refit nested choices and verify all new scores, ranks, metrics and stop checks."""
import hashlib
import json
from statistics import mean
import zipfile

import numpy as np

from ax_research.frozen_ensemble import mean_fold_scores
from ax_research.pairwise_ridge import rank_pool
from scripts.retrain_v2_20261109 import OUT, FAMILY, load, write
from scripts.task_alignment_20261109 import nested_variant, sha
from scripts.query_understanding_v2_experiment import OUT as V2OUT, frozen
from scripts.improvement_cycle import ROOT, read
from scripts.improvement_cycle2 import label_sets
from scripts.ai_pilot_evaluate import assemble_votes
from scripts.autonomous_trial2_mapping_replay import metrics, interval
from scripts.audit_retrain_v2_data import describe


def main():
    frozen()
    freeze, models, result = load('freeze.json'), load('models.json'), load('evaluation.json')
    assert all(sha(ROOT / p) == h for p, h in freeze['sources_sha256'].items())
    with zipfile.ZipFile(OUT / 'source-snapshot.zip') as archive:
        assert set(archive.namelist()) == set(freeze['sources_sha256'])
        for path, value in freeze['sources_sha256'].items():
            assert hashlib.sha256(archive.read(path)).hexdigest() == value
    current = {s: json.loads((V2OUT / (s + '-inputs.json')).read_text(encoding='utf-8')) for s in ('dev20', 'reuse40')}
    fit = models['fit_input']
    assert fit['outer_folds'] == freeze['outer_folds']
    assert fit['ids'] == current['dev20']['ids']
    for q, row in fit['inputs'].items():
        assert row['variants'][FAMILY] == current['dev20']['inputs'][q]['features']
        assert row['dense'] == current['dev20']['inputs'][q]['dense_order']
        assert row['pools'] == current['dev20']['inputs'][q]['pools']
    working_path = 'docs/ax-transfer-relevance-20261108/02_working_transfer_qrels_2240.json'
    assert models['training_labels_sha256'] == sha(ROOT / working_path)
    working = read(working_path)
    grades = {q: {} for q in fit['inputs']}
    for r in working['records']:
        grades[r['query_id']][r['case_id']] = r['grade']
    reproduced20, rebuilt_models = nested_variant(fit, grades, FAMILY)
    assert rebuilt_models == models['nested_models']
    seen = []
    for model in rebuilt_models:
        train, test = set(model['training_queries']), set(model['test_queries'])
        assert len(train) == 16 and len(test) == 4 and not train & test
        seen.extend(test)
        for choice in model['choices']:
            inner_seen = []
            for split in choice['inner_splits']:
                a, b = set(split['training_queries']), set(split['validation_queries'])
                assert len(a) == 12 and len(b) == 4 and not a & b
                assert a | b == train and not test & (a | b)
                inner_seen.extend(b)
            assert len(inner_seen) == 16 and set(inner_seen) == train
    assert len(seen) == 20 and set(seen) == set(fit['inputs'])
    flattened = [{'outer_fold': m['outer_fold'], 'weights': m['weights'], 'lambda': m['choice']['lambda'],
                  'learned_share': m['choice']['learned_share']} for m in rebuilt_models]
    assert flattened == models['transfer_ensemble']
    lookups = {}
    for scope in ('dev20', 'reuse40'):
        pred = load(scope + '-predictions.json')
        assert pred['models_sha256'] == sha(OUT / 'models.json')
        assert pred['source_features_sha256'] == sha(V2OUT / (scope + '-inputs.json'))
        assert result['prediction_sha256'][scope] == sha(OUT / (scope + '-predictions.json'))
        ranks = {(r['query_id'], r['repeat'], r['system']): r['ranking'] for r in pred['rankings']}
        assert len(ranks) == len(pred['rankings'])
        lookups[scope] = ranks
        original = json.loads((V2OUT / (scope + '-predictions.json')).read_text(encoding='utf-8'))
        for r in original['rankings']:
            assert ranks[r['query_id'], r['repeat'], r['system']] == r['ranking']
    for r in reproduced20:
        assert lookups['dev20'][r['query_id'], r['repeat'], r['system']] == r['ranking']
    scores = load('transfer-scores.json')
    count40 = 0
    for q, row in current['reuse40']['inputs'].items():
        values = mean_fold_scores(row['features'], flattened)
        np.testing.assert_allclose(values, scores[q], rtol=0, atol=1e-12)
        for repeat in (1, 2, 3):
            for pool, candidates in row['pools'][str(repeat)].items():
                rank = rank_pool(current['reuse40']['ids'], values, candidates, row['dense_order'])
                assert rank == lookups['reuse40'][q, repeat, FAMILY + '_' + pool]
                assert len(rank) == len(set(rank)) == 112 and set(rank[:20]) == set(candidates)
                count40 += 1
    votes, _ = assemble_votes()
    labels40 = {}
    for provider, records in votes.items():
        values = {}
        for (q, c), row in records.items():
            values.setdefault(q, {})[c] = row['grade']
        labels40[provider] = values
    labels20 = label_sets()
    for scope, group, labels in [('dev20', result['dev20'], labels20), ('reuse40', result['reuse40'], labels40), ('reuse40', result['common40'], labels40)]:
        ranks = lookups[scope]
        for version, r in group.items():
            g = labels[version]
            for q, systems in r['per_query'].items():
                positives = sum(v >= 2 for v in g[q].values())
                for system, values in systems.items():
                    rows = []
                    for repeat in (1, 2, 3):
                        rank = ranks[q, repeat, system]
                        m = metrics(rank, g[q])
                        m['Recall@20'] = sum(g[q][c] >= 2 for c in rank[:20]) / positives if positives else None
                        rows.append(m)
                    for metric, expected in values.items():
                        actual = mean(v[metric] for v in rows) if rows[0][metric] is not None else None
                        assert actual == expected or (actual is not None and expected is not None and abs(actual - expected) < 1e-12)
            for system, values in r['summary'].items():
                for metric, expected in values.items():
                    rows = [v[system][metric] for v in r['per_query'].values() if v[system][metric] is not None]
                    assert len(rows) == expected['queries'] and abs(mean(rows) - expected['mean']) < 1e-12
            for pair, values in r['comparisons'].items():
                method, baseline = pair.split(':')
                for metric, expected in values.items():
                    diffs = [v[method][metric] - v[baseline][metric] for v in r['per_query'].values() if v[method][metric] is not None]
                    assert abs(mean(diffs) - expected['delta']) < 1e-12
                    if baseline == 'V1_DensePool' and metric == 'F1@5':
                        assert interval(diffs) == expected['interval95']
    method = FAMILY + '_DensePool'
    def delta(r, base, metric):
        return r['comparisons'][method + ':' + base][metric]['delta']
    checks = {'dev': {v: {'f1_above_v1': delta(r, 'V1_DensePool', 'F1@5') > 0,
                          'f1_above_dense': delta(r, 'Dense', 'F1@5') > 0,
                          'ndcg_not_below_v1': delta(r, 'V1_DensePool', 'nDCG@10') >= -1e-12} for v, r in result['dev20'].items()},
              'matched40': {v: {'f1_not_below_v1': delta(r, 'V1_DensePool', 'F1@5') >= -1e-12,
                                'f1_not_below_dense': delta(r, 'Dense', 'F1@5') >= -1e-12,
                                'ndcg_not_below_v1': delta(r, 'V1_DensePool', 'nDCG@10') >= -1e-12} for v, r in result['common40'].items()}}
    assert checks == result['decision']['checks']
    low = result['dev20']['working_transfer']['comparisons'][method + ':V1_DensePool']['F1@5']['interval95'][0]
    success = all(all(r.values()) for group in checks.values() for r in group.values()) and low > 0
    assert result['decision']['status'] == ('PROVISIONAL_DEV_CANDIDATE' if success else 'DO_NOT_ADOPT_AND_AUDIT_DATA')
    audit = load('data-audit.json')
    for group, labels, scope in [('dev20', labels20, 'dev20'), ('reuse40', labels40, 'reuse40')]:
        for version, g in labels.items():
            assert describe(g, current[scope]['inputs']) == audit[group][version]
    matrix = dict.fromkeys(('both_positive', 'claude_only_positive', 'gemini_only_positive', 'both_negative'), 0)
    for q, values in labels40['claude'].items():
        for c, grade in values.items():
            a, b = grade >= 2, labels40['gemini'][q][c] >= 2
            matrix['both_positive' if a and b else 'claude_only_positive' if a else 'gemini_only_positive' if b else 'both_negative'] += 1
    assert matrix == audit['reuse40_binary_matrix']
    assert len(reproduced20) + count40 == 660
    write('verification.json', {'state': 'PASS', 'nested_hyperparameter_choices_and_weights_reproduced': True,
        'outer_and_inner_query_disjointness_verified': True, 'old_predictions_and_features_preserved': True,
        'new_rankings_reproduced': 660, 'transfer40_used_for_fit_or_selection': False,
        'all_metric_means_and_main_f1_intervals_verified': True, 'stop_decision_verified': True,
        'data_audit_counts_and_coverage_verified': True, 'paid_calls': 0, 'new_labels': 0,
        'test15_read': False, 'independent_test': False})
    print('PASS: nested refits,660 ranks,all metric means,stop decision,data audit')


if __name__ == '__main__':
    main()
