"""Archive the current development reference and audit existing failures; no fitting."""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
from statistics import mean
import zipfile

from scripts.improvement_cycle import ROOT, read
from scripts.improvement_cycle2 import label_sets

PREFIX = 'docs/task-alignment-20261109'
DEST = ROOT / 'docs/task-alignment-reference-20261109'
SYSTEM = 'WorkAligned_PerspectivePool'


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def write(name, value):
    with (DEST / name).open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def analyze(inputs, predictions, evaluation):
    labels = label_sets()
    questions = {q: p['source_text'] for q, p in inputs['partitions'].items()}
    cases = read('docs/dense-bm25-candidates-2026-10-27/case_registry.json')['cases']
    ranks = {(r['query_id'], r['repeat'], r['system']): r['ranking'] for r in predictions['rankings']}
    rows = []
    for q in sorted(questions):
        row = {'query_id': q, 'question': questions[q],
               'requested_text': inputs['partitions'][q]['requested_text'],
               'action_field': inputs['active_profiles'][q]['fields']['action'],
               'action_unknown': not bool(inputs['active_profiles'][q]['fields']['action']),
               'versions': {}}
        for version, grades in labels.items():
            per = evaluation['results'][version]['per_query'][q]
            delta = {m: per[SYSTEM][m] - per['Dense'][m] if per['Dense'][m] is not None else None
                     for m in ('F1@5', 'nDCG@10')}
            details = []
            positive = {c for c, grade in grades[q].items() if grade >= 2}
            for repeat in (1, 2, 3):
                old, new = ranks[q, repeat, 'Dense'], ranks[q, repeat, SYSTEM]
                candidates = set(new[:20])
                entered, left = set(new[:5]) - set(old[:5]), set(old[:5]) - set(new[:5])
                def describe(case):
                    return {'case_id': case, 'task': cases[case]['task'], 'grade': grades[q][case],
                            'old_rank': old.index(case) + 1, 'new_rank': new.index(case) + 1,
                            'in_candidate20': case in candidates}
                details.append({'repeat': repeat,
                    'entered_top5': [describe(c) for c in sorted(entered)],
                    'left_top5': [describe(c) for c in sorted(left)],
                    'positive_in_pool_below5': [describe(c) for c in new[5:20] if c in positive],
                    'positive_outside_pool': [describe(c) for c in new[20:] if c in positive],
                    'dense_positive_lost_from_top5': [describe(c) for c in old[:5] if c in positive and c not in new[:5]],
                    'dense_positive_lost_from_pool': [describe(c) for c in old[:20] if c in positive and c not in candidates]})
            row['versions'][version] = {'positive_count': len(positive), 'baseline': per['Dense'], 'reference': per[SYSTEM],
                'delta': delta, 'f1_harmed': delta['F1@5'] is not None and delta['F1@5'] < -1e-12,
                'ndcg_harmed': delta['nDCG@10'] is not None and delta['nDCG@10'] < -1e-12,
                'repeat_details': details}
        rows.append(row)
    harmed = {version: {kind: [r['query_id'] for r in rows if r['versions'][version][kind]]
                       for kind in ('f1_harmed', 'ndcg_harmed')} for version in labels}
    return {'state': 'EXISTING_PREDICTIONS_FAILURE_AUDIT_ONLY', 'reference_system': SYSTEM, 'rows': rows,
            'harmed_queries': harmed,
            'any_f1_harmed': [r['query_id'] for r in rows if any(v['f1_harmed'] for v in r['versions'].values())],
            'any_f1_or_ndcg_harmed': [r['query_id'] for r in rows if any(v['f1_harmed'] or v['ndcg_harmed'] for v in r['versions'].values())],
            'unknown_action_queries': [r['query_id'] for r in rows if r['action_unknown']],
            'interpretation': ['All grades are existing AI Silver, not newly adjudicated truth',
                               'Missing action does not prove it caused ranking failure',
                               'Grade versions change the meaning of some observed errors',
                               'Source-text observations are hypotheses about failure mechanism, not causal ablations'],
            'paid_calls': 0, 'new_model_fits': 0, 'new_predictions': 0, 'new40_read': False, 'test15_read': False}


def freeze():
    if DEST.exists():
        raise FileExistsError('Reference already exists; no overwrite')
    inputs, prediction, evaluation = [read(PREFIX + suffix + '.json') for suffix in ('-inputs', '-predictions', '-evaluation')]
    assert prediction['input_sha256'] == sha(ROOT / (PREFIX + '-inputs.json'))
    assert evaluation['prediction_sha256'] == sha(ROOT / (PREFIX + '-predictions.json'))
    assert all(sha(ROOT / path) == value for path, value in inputs['source_sha256'].items())
    assert inputs['vectors_sha256'] == sha(ROOT / (PREFIX + '-vectors.npz'))
    audit = analyze(inputs, prediction, evaluation)
    config = {'reference_id': 'work-aligned-dev-v1-20261109',
              'state': 'FROZEN_DEVELOPMENT_REFERENCE_NOT_DEPLOYED',
              'primary_system': SYSTEM,
              'comparison_systems': ['Dense', 'WorkAligned_DensePool', 'WorkAligned_TokenPool'],
              'candidate_budget': 20, 'output_budget': 5,
              'input_feature_names': inputs['feature_names']['WorkAligned'],
              'model_sha256': inputs['model_sha256'], 'outer_folds': inputs['outer_folds'],
              'fold_models': [{'outer_fold': m['outer_fold'], 'training_queries': m['training_queries'],
                               'heldout_queries': m['test_queries'], 'lambda': m['choice']['lambda'],
                               'learned_share': m['choice']['learned_share'], 'weights': m['weights']}
                              for m in prediction['models']['WorkAligned']],
              'training_recipe': {'lambdas': [.1, 1., 10.], 'learned_shares': [0., .5, 1.],
                                  'method': 'query-balanced pairwise ridge', 'selection': 'inner DensePool F1, then nDCG, then less learning, then larger lambda'},
              'decision': evaluation['decisions'][SYSTEM],
              'no_new_all20_fit': True,
              'next_evaluation_requires_separately_documented_fit_or_ensemble_policy': True,
              'limits': ['Five out-of-fold models preserved, not a newly trained deployment model',
                         'Shared case database and previously observed development queries',
                         'Fixed old candidate pools cannot be assumed available for new questions',
                         'Local encoder weights are fingerprinted, not duplicated in this archive',
                         'No retraining or new-question evaluation performed during this freeze']}
    DEST.mkdir()
    write('config.json', config)
    write('failure-audit.json', audit)
    sources = set(inputs['source_sha256'])
    for suffix in ('-inputs.json', '-vectors.npz', '-predictions.json', '-evaluation.json', '-verification.json', '-protocol.md', '-report.ko.md'):
        sources.add(PREFIX + suffix)
    sources.update(['scripts/verify_task_alignment_20261109.py', 'scripts/freeze_task_alignment_reference_20261109.py',
        'scripts/improvement_cycle.py', 'scripts/improvement_cycle2.py', 'scripts/autonomous_trial2_mapping_replay.py',
        'src/ax_research/semantic_mapping.py', 'src/ax_research/functional_mapping.py', 'src/ax_research/action_aggregation.py',
        'src/ax_research/retrieval/bm25.py', 'docs/dense-bm25-candidates-2026-10-27/case_registry.json',
        'docs/ax-transfer-relevance-20261108/02_working_transfer_qrels_2240.json',
        'docs/validation-new20-20261107/measured/labels_new20.json',
        'docs/autonomous-improvement-20261108/19_independent_adjudication_and_stop_decision.json',
        'docs/query-case-semantic-mapping-2026-10-28/preregistration.json',
        'docs/query-case-semantic-mapping-2026-10-28/mapping/case_profiles.json',
        'docs/task-alignment-reference-20261109/config.json', 'docs/task-alignment-reference-20261109/failure-audit.json'])
    files = {path: {'sha256': sha(ROOT / path), 'bytes': (ROOT / path).stat().st_size} for path in sorted(sources)}
    archive = DEST / 'snapshot.zip'
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED) as target:
        for path in files:
            target.write(ROOT / path, arcname=path)
    packages = {name: importlib.metadata.version(name) for name in ('numpy', 'torch', 'sentence-transformers', 'transformers', 'kiwipiepy', 'rank-bm25')}
    write('manifest.json', {'reference_id': config['reference_id'], 'snapshot_files': files,
                            'archive_sha256': sha(archive), 'archive_bytes': archive.stat().st_size,
                            'packages': packages, 'scope': 'Existing local sources, rules, data, vectors, folds, weights and results',
                            'human_gold_created': False, 'paid_calls': 0, 'new_fits': 0,
                            'new40_read': False, 'test15_read': False})
    print('FROZEN', len(files), 'files;', round(archive.stat().st_size / 1024 / 1024, 2), 'MiB')


def verify():
    manifest = json.loads((DEST / 'manifest.json').read_text(encoding='utf-8'))
    assert sha(DEST / 'snapshot.zip') == manifest['archive_sha256']
    with zipfile.ZipFile(DEST / 'snapshot.zip') as archive:
        assert set(archive.namelist()) == set(manifest['snapshot_files'])
        for path, info in manifest['snapshot_files'].items():
            raw = archive.read(path)
            assert len(raw) == info['bytes'] and hashlib.sha256(raw).hexdigest() == info['sha256']
            assert sha(ROOT / path) == info['sha256'], ('Current source drift', path)
    inputs, prediction, evaluation = [read(PREFIX + suffix + '.json') for suffix in ('-inputs', '-predictions', '-evaluation')]
    audit = analyze(inputs, prediction, evaluation)
    assert audit == json.loads((DEST / 'failure-audit.json').read_text(encoding='utf-8'))
    config = json.loads((DEST / 'config.json').read_text(encoding='utf-8'))
    assert config['decision'] == evaluation['decisions'][SYSTEM]
    for m, original in zip(config['fold_models'], prediction['models']['WorkAligned']):
        assert m['weights'] == original['weights']
        assert m['lambda'] == original['choice']['lambda'] and m['learned_share'] == original['choice']['learned_share']
    for version, result in evaluation['results'].items():
        for metric in ('F1@5', 'nDCG@10'):
            deltas = [r['versions'][version]['delta'][metric] for r in audit['rows'] if r['versions'][version]['delta'][metric] is not None]
            expected = result['ablation_comparisons'][SYSTEM]['Dense'][metric]['delta']
            assert abs(mean(deltas) - expected) < 1e-12
    write('verification.json', {'state': 'PASS', 'snapshot_file_count': len(manifest['snapshot_files']),
                               'archive_and_current_source_hashes_match': True, 'fold_models_unchanged': True,
                               'all20_query_failure_rows_reproduced': True, 'harmed_queries': audit['harmed_queries'],
                               'any_f1_harmed': audit['any_f1_harmed'],
                               'any_f1_or_ndcg_harmed': audit['any_f1_or_ndcg_harmed'],
                               'unknown_action_queries': audit['unknown_action_queries'],
                               'new_fits': 0, 'new_predictions': 0, 'paid_calls': 0})
    print('PASS', len(manifest['snapshot_files']), 'snapshot files; all20 failure rows; unchanged fold weights and metrics')
    print('F1_harmed', audit['any_f1_harmed'], 'any_metric_harmed', audit['any_f1_or_ndcg_harmed'], 'unknown_actions', audit['unknown_action_queries'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=['freeze', 'verify'])
    globals()[parser.parse_args().phase]()
