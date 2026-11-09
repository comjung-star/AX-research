"""Replay contract gate, sixty query parses and fixed-weight ranking ablations."""
import json
from statistics import mean
import zipfile
import hashlib

import numpy as np

from ax_research.query_understanding_v2 import understand
from ax_research.frozen_ensemble import mean_fold_scores
from ax_research.pairwise_ridge import rank_pool, score
from scripts.query_understanding_v2_experiment import OUT, load, write, frozen
from scripts.check_query_understanding_v2 import check_contracts
from scripts.transfer40_work_aligned_20261109 import build_features
from scripts.task_alignment_20261109 import sha
from scripts.improvement_cycle import ROOT, read
from scripts.improvement_cycle2 import label_sets
from scripts.ai_pilot_evaluate import assemble_votes
from scripts.autonomous_trial2_mapping_replay import metrics, interval


def main():
    freeze = frozen()
    assert check_contracts() == load('extraction-gate.json')
    with zipfile.ZipFile(OUT / 'source-snapshot.zip') as archive:
        assert set(archive.namelist()) == set(freeze['source_sha256'])
        for path, digest in freeze['source_sha256'].items():
            assert hashlib.sha256(archive.read(path)).hexdigest() == digest
    old_manifest = read('docs/task-alignment-reference-20261109/manifest.json')
    assert all(sha(ROOT / p) == value['sha256'] for p, value in old_manifest['snapshot_files'].items())
    inference = load('inference.json')
    assert inference['vectors_sha256'] == sha(OUT / 'vectors.npz')
    assert all(sha(ROOT / p) == h for p, h in inference['banks_sha256'].items())
    cfg = read('configs/semantic_mapping_20261028.json')
    models = read('docs/task-alignment-reference-20261109/config.json')
    cases = read('docs/literal-action-recovery-20261109/case_profiles.json')
    with np.load(OUT / 'vectors.npz', allow_pickle=False) as z:
        bank = dict(zip(z['texts'].tolist(), z['vectors']))
    evaluation = load('evaluation.json')
    data, lookups, parse_stats = {}, {}, {}
    replayed = 0
    for scope in ('dev20', 'reuse40'):
        inputs, pred = load(scope + '-inputs.json'), load(scope + '-predictions.json')
        data[scope] = inputs
        assert pred['input_sha256'] == sha(OUT / (scope + '-inputs.json'))
        assert pred['freeze_sha256'] == sha(OUT / 'freeze.json')
        assert evaluation['prediction_sha256'][scope] == sha(OUT / (scope + '-predictions.json'))
        old_path = 'docs/task-alignment-20261109-inputs.json' if scope == 'dev20' else 'docs/transfer40-work-aligned-20261109/inputs.json'
        old_pred_path = 'docs/task-alignment-20261109-predictions.json' if scope == 'dev20' else 'docs/transfer40-work-aligned-20261109/predictions.json'
        assert inputs['source_inputs_sha256'] == sha(ROOT / old_path)
        assert pred['source_prediction_sha256'] == sha(ROOT / old_pred_path)
        old = read(old_path)
        ranks = {(r['query_id'], r['repeat'], r['system']): r['ranking'] for r in pred['rankings']}
        assert len(ranks) == len(pred['rankings'])
        lookups[scope] = ranks
        ids = inputs['ids']
        for q, row in inputs['inputs'].items():
            partition, profile = understand(inputs['partitions'][q]['source_text'], cfg)
            assert partition == inputs['partitions'][q] and profile == inputs['profiles'][q]
            features = build_features(ids, *row['maps'], profile, partition, cases, bank)
            np.testing.assert_allclose(features, row['features'], rtol=0, atol=1e-12)
            before = old['inputs'][q]['features']
            np.testing.assert_allclose(features[:, :3], np.array(before)[:, :3], rtol=0, atol=1e-12)
            if scope == 'dev20':
                model = next(m for m in models['fold_models'] if m['outer_fold'] == old['outer_folds'][q])
                assert q in model['heldout_queries'] and q not in model['training_queries']
                values = score(features, np.array(model['weights']), model['learned_share'])
            else:
                values = mean_fold_scores(features, models['fold_models'])
            np.testing.assert_allclose(values, row['scores'], rtol=0, atol=1e-12)
            assert row['pools'] == old['inputs'][q]['pools']
            for repeat in (1, 2, 3):
                for pool, candidates in row['pools'][str(repeat)].items():
                    rank = rank_pool(ids, values, candidates, row['dense_order'])
                    assert rank == ranks[q, repeat, 'V2_' + pool]
                    assert set(rank[:20]) == set(candidates) and len(rank) == len(set(rank)) == 112
                    replayed += 1
        for r in read(old_pred_path)['rankings']:
            prefix = 'WorkAligned_' if scope == 'dev20' else 'Aligned_'
            name = r['system'].replace(prefix, 'V1_', 1) if r['system'].startswith(prefix) else r['system']
            if name.startswith('V1_') or name in ('Dense', 'BM25', 'E'):
                assert ranks[r['query_id'], r['repeat'], name] == r['ranking']
        parse_stats[scope] = {'queries': len(inputs['inputs']),
                             'empty_action': [q for q, p in inputs['profiles'].items() if not p['fields']['action']],
                             'unknown_request': [q for q, p in inputs['partitions'].items() if p['request_unknown']]}
    votes, _ = assemble_votes()
    reuse = {}
    for provider, rows in votes.items():
        grades = {}
        for (q, c), row in rows.items():
            grades.setdefault(q, {})[c] = row['grade']
        reuse[provider] = grades
    scopes = [('dev20', evaluation['dev20'], label_sets()), ('reuse40', evaluation['reuse40'], reuse),
              ('reuse40', evaluation['common40'], reuse)]
    for scope, results, labels in scopes:
        ranks = lookups[scope]
        for version, result in results.items():
            grades = labels[version]
            for q, systems in result['per_query'].items():
                positive = sum(v >= 2 for v in grades[q].values())
                for system, values in systems.items():
                    rows = []
                    for repeat in (1, 2, 3):
                        rank = ranks[q, repeat, system]
                        row = metrics(rank, grades[q])
                        row['Recall@20'] = sum(grades[q][c] >= 2 for c in rank[:20]) / positive if positive else None
                        rows.append(row)
                    for metric, expected in values.items():
                        actual = mean(r[metric] for r in rows) if rows[0][metric] is not None else None
                        assert actual == expected or (actual is not None and expected is not None and abs(actual - expected) < 1e-12)
            for system, values in result['summary'].items():
                for metric, expected in values.items():
                    rows = [r[system][metric] for r in result['per_query'].values() if r[system][metric] is not None]
                    assert len(rows) == expected['queries'] and abs(mean(rows) - expected['mean']) < 1e-12
            for pair, values in result['comparisons'].items():
                method, baseline = pair.split(':')
                for metric, value in values.items():
                    differences = [r[method][metric] - r[baseline][metric] for r in result['per_query'].values() if r[method][metric] is not None]
                    assert abs(mean(differences) - value['delta']) < 1e-12
                    if pair == 'V2_DensePool:V1_DensePool' and metric == 'F1@5':
                        assert interval(differences) == value['interval95']
    assert replayed == 660
    write('verification.json', {'state': 'PASS', 'contract_gate_cases': 20, 'snapshot_hashes_match': True,
        'frozen_v1_reference_files_unchanged': True, 'query_parses_reproduced': 60, 'new_rankings_reproduced': replayed,
        'candidate_pools_and_nonsemantic_features_unchanged': True, 'v1_baseline_predictions_unchanged': True,
        'all_datasets_provider_cohorts_metric_means_verified': True, 'main_v2_vs_v1_f1_intervals_verified': True,
        'parse_stats': parse_stats, 'paid_calls': 0, 'new_training': False, 'independent_test': False})
    print('PASS: gate20, parses60, rankings660, unchanged models/pools/v1, all metric means')


if __name__ == '__main__':
    main()
