"""One bounded nested retraining run on frozen v2 features, then audit decision."""
import argparse
import json
from statistics import mean
import zipfile

import numpy as np

from ax_research.frozen_ensemble import mean_fold_scores
from ax_research.pairwise_ridge import rank_pool
from scripts.improvement_cycle import ROOT, read
from scripts.task_alignment_20261109 import nested_variant, sha
from scripts.query_understanding_v2_experiment import OUT as V2OUT, frozen as v2_frozen
from scripts.autonomous_trial2_mapping_replay import interval

OUT = ROOT / 'docs/retrain-v2-20261109'
FAMILY = 'RetrainedV2'


def write(name, value):
    with (OUT / name).open('x', encoding='utf-8') as target:
        target.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def load(name):
    return json.loads((OUT / name).read_text(encoding='utf-8'))


def train():
    if OUT.exists():
        raise FileExistsError(OUT)
    v2_frozen()
    data20, data40 = [json.loads((V2OUT / (s + '-inputs.json')).read_text(encoding='utf-8')) for s in ('dev20', 'reuse40')]
    prior20 = read('docs/task-alignment-20261109-inputs.json')
    sources = ['docs/retrain-v2-20261109-protocol.md', 'scripts/retrain_v2_20261109.py',
        'scripts/task_alignment_20261109.py', 'src/ax_research/pairwise_ridge.py', 'src/ax_research/frozen_ensemble.py',
        'docs/query-understanding-v2-20261109/freeze.json',
        'docs/query-understanding-v2-20261109/dev20-inputs.json', 'docs/query-understanding-v2-20261109/reuse40-inputs.json',
        'docs/query-understanding-v2-20261109/dev20-predictions.json', 'docs/query-understanding-v2-20261109/reuse40-predictions.json',
        'docs/task-alignment-20261109-inputs.json',
        'docs/ax-transfer-relevance-20261108/02_working_transfer_qrels_2240.json']
    OUT.mkdir()
    write('freeze.json', {'sources_sha256': {p: sha(ROOT / p) for p in sources}, 'v2_features_fixed': True,
        'outer_folds': prior20['outer_folds'], 'lambda_grid': [.1, 1., 10.], 'learned_share_grid': [0., .5, 1.],
        'policy': 'working labels only; nested query folds; same five-model score mean for reuse40',
        'paid_calls': 0, 'test15_read': False})
    with zipfile.ZipFile(OUT / 'source-snapshot.zip', 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sources:
            archive.write(ROOT / path, arcname=path)
    working = read('docs/ax-transfer-relevance-20261108/02_working_transfer_qrels_2240.json')
    grades = {q: {} for q in data20['inputs']}
    for row in working['records']:
        grades[row['query_id']][row['case_id']] = row['grade']
    fit_input = {'ids': data20['ids'], 'outer_folds': prior20['outer_folds'], 'inputs': {
        q: {'variants': {FAMILY: row['features']}, 'dense': row['dense_order'], 'pools': row['pools']}
        for q, row in data20['inputs'].items()}}
    new20, models = nested_variant(fit_input, grades, FAMILY)
    flattened = [{'outer_fold': m['outer_fold'], 'weights': m['weights'], 'lambda': m['choice']['lambda'],
                  'learned_share': m['choice']['learned_share']} for m in models]
    base20, base40 = [json.loads((V2OUT / (s + '-predictions.json')).read_text(encoding='utf-8'))['rankings'] for s in ('dev20', 'reuse40')]
    predictions40 = list(base40)
    scores40 = {}
    for q, row in data40['inputs'].items():
        values = mean_fold_scores(np.array(row['features']), flattened)
        scores40[q] = values.tolist()
        for repeat in (1, 2, 3):
            for pool, candidates in row['pools'][str(repeat)].items():
                predictions40.append({'query_id': q, 'repeat': repeat, 'system': FAMILY + '_' + pool,
                    'ranking': rank_pool(data40['ids'], values, candidates, row['dense_order'])})
    assert len(base20 + new20) == 660 and len(predictions40) == 1800
    write('models.json', {'nested_models': models, 'transfer_ensemble': flattened, 'fit_input': fit_input,
        'training_labels_sha256': sha(ROOT / sources[-1]), 'newly_trained_family': 'pairwise ridge',
        'large_encoder_training': False, 'reuse40_used_for_fit_or_selection': False})
    for scope, rankings in [('dev20', base20 + new20), ('reuse40', predictions40)]:
        write(scope + '-predictions.json', {'rankings': rankings, 'models_sha256': sha(OUT / 'models.json'),
            'source_features_sha256': sha(V2OUT / (scope + '-inputs.json')), 'paid_calls': 0,
            'scope': 'NESTED_QUERY_OOF' if scope == 'dev20' else 'PREVIOUSLY_SEEN40_FIXED_MEAN',
            'sensitivity_labels_read': False, 'test15_read': False})
    write('transfer-scores.json', scores40)
    print('TRAINED_AND_SEALED', [(m['outer_fold'], m['choice']['lambda'], m['choice']['learned_share']) for m in models], flush=True)


def assess(rankings, grades):
    from scripts.improvement_cycle2 import evaluate
    result = evaluate(rankings, grades)
    method = FAMILY + '_DensePool'
    perspective = FAMILY + '_PerspectivePool'
    pairs = [(method, b) for b in ('Dense', 'V1_DensePool', 'V2_DensePool')]
    pairs += [(perspective, b) for b in (method, FAMILY + '_TokenPool')]
    if any(r['system'] == FAMILY + '_SparsePool' for r in rankings):
        pairs.append((perspective, FAMILY + '_SparsePool'))
    result['comparisons'] = {}
    for current, baseline in pairs:
        result['comparisons'][current + ':' + baseline] = {}
        for metric in ('F1@5', 'nDCG@10'):
            diffs = [r[current][metric] - r[baseline][metric] for r in result['per_query'].values() if r[current][metric] is not None]
            result['comparisons'][current + ':' + baseline][metric] = {'delta': mean(diffs), 'interval95': interval(diffs),
                'improved': sum(v > 1e-12 for v in diffs), 'harmed': sum(v < -1e-12 for v in diffs)}
    return result


def evaluate():
    from scripts.improvement_cycle2 import label_sets
    from scripts.ai_pilot_evaluate import assemble_votes
    freeze = load('freeze.json')
    assert all(sha(ROOT / p) == h for p, h in freeze['sources_sha256'].items())
    pred20, pred40 = load('dev20-predictions.json'), load('reuse40-predictions.json')
    assert all(p['models_sha256'] == sha(OUT / 'models.json') for p in (pred20, pred40))
    dev = {}
    for name, grades in label_sets().items():
        dev[name] = assess(pred20['rankings'], grades)
        print('dev20', name, {s: round(v['F1@5']['mean'], 6) for s, v in dev[name]['summary'].items() if s in ('Dense', 'V1_DensePool', 'V2_DensePool', FAMILY + '_DensePool', FAMILY + '_PerspectivePool')}, flush=True)
    votes, _ = assemble_votes()
    labels = {}
    for provider, rows in votes.items():
        grades = {}
        for (q, c), row in rows.items():
            assert row['status'] == 'JUDGED' and row['grade'] is not None
            grades.setdefault(q, {})[c] = row['grade']
        labels[provider] = grades
    common = sorted(set.intersection(*[{q for q, g in values.items() if any(v >= 2 for v in g.values())} for values in labels.values()]))
    reuse, matched = {}, {}
    for provider, grades in labels.items():
        reuse[provider] = assess(pred40['rankings'], grades)
        matched[provider] = assess([r for r in pred40['rankings'] if r['query_id'] in common], {q: grades[q] for q in common})
        print('reuse40', provider, {s: round(v['F1@5']['mean'], 6) for s, v in reuse[provider]['summary'].items() if s in ('Dense', 'V1_DensePool', 'V2_DensePool', FAMILY + '_DensePool', FAMILY + '_PerspectivePool')}, flush=True)
    method = FAMILY + '_DensePool'
    def diff(result, baseline, metric):
        return result['comparisons'][method + ':' + baseline][metric]['delta']
    checks = {'dev': {v: {'f1_above_v1': diff(r, 'V1_DensePool', 'F1@5') > 0,
                           'f1_above_dense': diff(r, 'Dense', 'F1@5') > 0,
                           'ndcg_not_below_v1': diff(r, 'V1_DensePool', 'nDCG@10') >= -1e-12} for v, r in dev.items()},
              'matched40': {v: {'f1_not_below_v1': diff(r, 'V1_DensePool', 'F1@5') >= -1e-12,
                                 'f1_not_below_dense': diff(r, 'Dense', 'F1@5') >= -1e-12,
                                 'ndcg_not_below_v1': diff(r, 'V1_DensePool', 'nDCG@10') >= -1e-12} for v, r in matched.items()}}
    low = dev['working_transfer']['comparisons'][method + ':V1_DensePool']['F1@5']['interval95'][0]
    passed = all(all(row.values()) for group in checks.values() for row in group.values()) and low > 0
    write('evaluation.json', {'dev20': dev, 'reuse40': reuse, 'common40': matched, 'common_questions': common,
        'decision': {'checks': checks, 'working_vs_v1_f1_ci_lower': low,
                     'status': 'PROVISIONAL_DEV_CANDIDATE' if passed else 'DO_NOT_ADOPT_AND_AUDIT_DATA'},
        'prediction_sha256': {s: sha(OUT / (s + '-predictions.json')) for s in ('dev20', 'reuse40')},
        'paid_calls': 0, 'training_queries': 20, 'reuse40_training_queries': 0, 'new_labels': 0,
        'independent_test': False, 'test15_read': False,
        'limits': ['Previously observed development and reused datasets', 'Same case DB across folds',
                   'AI Silver and partial review, not human Gold', 'Bootstrap not adjusted for development selection/multiplicity']})
    print('DECISION', 'PROVISIONAL_DEV_CANDIDATE' if passed else 'DO_NOT_ADOPT_AND_AUDIT_DATA', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=['train', 'evaluate'])
    globals()[parser.parse_args().phase]()
