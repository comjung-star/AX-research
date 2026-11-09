"""Replay fixed transfer features, pools, scores, rankings and provider metrics."""
import json
from statistics import mean

import numpy as np

from ax_research.dense_preservation import preserve_dense_candidates
from ax_research.frozen_ensemble import mean_fold_scores
from ax_research.pairwise_ridge import rank_pool
from ax_research.task_alignment import partition_request
from scripts.improvement_cycle import ROOT, read
from scripts.task_alignment_20261109 import sha
from scripts.transfer40_work_aligned_20261109 import OUT, REFERENCE, POOLS, build_features, write
from scripts.ai_pilot_evaluate import assemble_votes
from scripts.autonomous_trial2_mapping_replay import metrics, interval


def main():
    load = lambda name: json.loads((OUT / name).read_text(encoding='utf-8'))
    inputs, predictions, evaluation = map(load, ('inputs.json', 'predictions.json', 'evaluation.json'))
    for key in ('source_sha256', 'token_cache_sha256', 'runtime_sha256'):
        assert all(sha(ROOT / path) == expected for path, expected in inputs[key].items()), key
    assert sha(OUT / 'vectors.npz') == inputs['vectors_sha256']
    assert sha(OUT / 'inputs.json') == predictions['input_sha256']
    assert sha(OUT / 'predictions.json') == evaluation['prediction_sha256']
    assert all(sha(ROOT / path) == h for path, h in evaluation['label_sha256'].items())
    config = json.loads((REFERENCE / 'config.json').read_text(encoding='utf-8'))
    cases = read('docs/literal-action-recovery-20261109/case_profiles.json')
    with np.load(OUT / 'vectors.npz', allow_pickle=False) as z:
        bank = dict(zip(z['texts'].tolist(), z['vectors']))
    ids = inputs['ids']
    ranks = {(r['query_id'], r['repeat'], r['system']): r['ranking'] for r in predictions['rankings']}
    assert len(ranks) == 840 and len(inputs['inputs']) == 40
    traces = {(r['query_id'], r['repeat'], r['pool']): r for r in inputs['traces']}
    for q, row in inputs['inputs'].items():
        partition = inputs['partitions'][q]
        assert partition == partition_request(partition['source_text'])
        for span in partition['pieces'] + partition['output_hints']:
            assert partition['source_text'][span['start']:span['end']] == span['quote']
        rebuilt = build_features(ids, row['dense'], row['token'], row['sparse'], inputs['profiles'][q], partition, cases, bank)
        np.testing.assert_allclose(rebuilt, row['features'], rtol=0, atol=1e-12)
        scores = mean_fold_scores(rebuilt, config['fold_models'])
        np.testing.assert_allclose(scores, row['scores'], rtol=0, atol=1e-12)
        assert row['dense_order'] == sorted(ids, key=lambda c: (-row['dense'][c], c))
        assert row['sparse_order'] == sorted(ids, key=lambda c: (-row['sparse'][c], c))
        for repeat in (1, 2, 3):
            assert ranks[q, repeat, 'Dense'] == row['dense_order']
            assert ranks[q, repeat, 'BM25'] == row['sparse_order']
            sources = {'TokenPool': {'OriginalToken': row['token_order']},
                       'SparsePool': {'OriginalSparse': row['sparse_order']},
                       'PerspectivePool': row['branches'][str(repeat)]}
            for pool, source in sources.items():
                replay = preserve_dense_candidates(row['dense'], row['token'], row['core'], source)
                assert all(replay[key] == traces[q, repeat, pool][key] for key in replay)
                assert replay['candidates'] == row['pools'][str(repeat)][pool]
                assert all(v['path_rank'] <= 20 for v in replay['candidate_admissions'])
            for pool in POOLS:
                candidates = row['pools'][str(repeat)][pool]
                assert len(set(candidates)) == 20 and set(row['dense_order'][:10]) <= set(candidates)
                rank = rank_pool(ids, scores, candidates, row['dense_order'])
                assert rank == ranks[q, repeat, 'Aligned_' + pool]
                assert set(rank[:20]) == set(candidates) and len(rank) == len(set(rank)) == 112
    votes, _ = assemble_votes()
    for provider, records in votes.items():
        grades = {q: {c: records[q, c]['grade'] for c in ids} for q in inputs['inputs']}
        for scope in ('results', 'common_results'):
            result = evaluation[scope][provider]
            for q, systems in result['per_query'].items():
                positive = sum(g >= 2 for g in grades[q].values())
                for system, values in systems.items():
                    repeats = []
                    for repeat in (1, 2, 3):
                        rank = ranks[q, repeat, system]
                        m = metrics(rank, grades[q])
                        m['Recall@20'] = sum(grades[q][c] >= 2 for c in rank[:20]) / positive if positive else None
                        repeats.append(m)
                    for metric, value in values.items():
                        actual = mean(r[metric] for r in repeats) if repeats[0][metric] is not None else None
                        assert actual == value or (actual is not None and value is not None and abs(actual - value) < 1e-12)
            for system, values in result['summary'].items():
                for metric, value in values.items():
                    rows = [r[system][metric] for r in result['per_query'].values() if r[system][metric] is not None]
                    assert len(rows) == value['queries'] and abs(mean(rows) - value['mean']) < 1e-12
            for baseline, values in result['perspective_contrasts'].items():
                for metric, value in values.items():
                    diffs = [r['Aligned_PerspectivePool'][metric] - r[baseline][metric] for r in result['per_query'].values() if r[baseline][metric] is not None]
                    assert abs(mean(diffs) - value['delta']) < 1e-12
                    if baseline in ('Dense', 'Aligned_TokenPool') and metric == 'F1@5':
                        assert interval(diffs) == value['interval95']
        for row in evaluation['candidate_accounting'][provider]['rows']:
            q, repeat = row['query_id'], row['repeat']
            positive = {c for c, g in grades[q].items() if g >= 2}
            pools = {p: set(ranks[q, repeat, 'Aligned_' + p][:20]) for p in POOLS}
            assert row['new_positive_vs_dense_pool'] == sorted((pools['PerspectivePool'] - pools['DensePool']) & positive)
            assert row['lost_positive_vs_dense_pool'] == sorted((pools['DensePool'] - pools['PerspectivePool']) & positive)
            assert row['new_positive_absent_both_token_sparse'] == sorted((pools['PerspectivePool'] - pools['TokenPool'] - pools['SparsePool']) & positive)
    write('verification.json', {'state': 'PASS', 'source_vector_token_runtime_and_label_hashes_match': True,
        'feature_matrices_reproduced': 40, 'candidate_traces_reproduced': 360, 'ensemble_rankings_reproduced': 480,
        'provider_and_matched_cohort_metric_means_verified': True, 'main_f1_intervals_reproduced': True,
        'candidate_positive_accounting_verified': True, 'new_training': False, 'paid_calls': 0,
        'test15_read': False, 'independent_final_test': False})
    print('PASS: 40 feature matrices, 360 candidate traces, 480 ensemble rankings, both provider/cohort metrics')


if __name__ == '__main__':
    main()
