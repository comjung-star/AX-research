"""Frozen five-step development audit, query-nested evaluation, zero API calls."""
import argparse
import hashlib
import json
from statistics import mean

import numpy as np

from ax_research.pairwise_ridge import fit_pairwise, rank_pool, score, unit
from ax_research.retrieval.bm25 import BM25Retriever
from scripts.improvement_cycle import ROOT, read
from scripts.autonomous_trial2_mapping_replay import interval, metrics

PREFIX = 'docs/ranking-audit-20261109'
FEATURES = ['dense', 'original_token', 'bm25', 'action', 'object', 'core_min',
            'core_product', 'action_present', 'object_present', 'task_cosine']


def digest(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def save(suffix, value):
    path = ROOT / (PREFIX + suffix + '.json')
    with path.open('x', encoding='utf-8') as target:
        target.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def prepare():
    previous = read('docs/dense-preserved-candidates-20261108-predictions.json')
    cases = read('docs/dense-bm25-candidates-2026-10-27/case_registry.json')['cases']
    ids = sorted(cases)
    texts = {r['query_id']: r['text'] for r in map(json.loads, (ROOT / 'docs/validation-new20-20261107/questions.jsonl').read_text(encoding='utf-8').splitlines())}
    sparse = BM25Retriever({c: '\n'.join(cases[c][f] for f in ('problem', 'task', 'context')) for c in ids})
    evidence = {(r['query_id'], r['case_id']): r for r in read('.work-new20-runtime/original/predictions/evidence.json')['records']}
    traces = {(r['query_id'], r['repeat'], r['system']): r['candidates'] for r in previous['traces']}
    inputs, missing = {}, {}
    for q, data in sorted(previous['inputs'].items()):
        bm25 = {r.case_id: r.score for r in sparse.search(texts[q])}
        action = [data['core'][c]['action'] for c in ids]
        obj = [data['core'][c]['object'] for c in ids]
        present_a = np.array([v is not None for v in action], dtype=float)
        present_o = np.array([v is not None for v in obj], dtype=float)
        a, o = np.array([v or 0 for v in action]), np.array([v or 0 for v in obj])
        columns = [unit([data['dense'][c] for c in ids]), unit([data['token'][c] for c in ids]),
                   unit([bm25[c] for c in ids]), unit(a), unit(o),
                   unit(np.minimum(a, o) * present_a * present_o), unit(a * o * present_a * present_o),
                   present_a, present_o,
                   unit([evidence[q, c]['semantic']['components']['task']['cosine'] for c in ids])]
        dense = sorted(ids, key=lambda c: (-data['dense'][c], c))
        pools = {str(r): {'DensePool': dense[:20],
                         'TokenPool': traces[q, r, 'QueryTokenCandidates'],
                         'PerspectivePool': traces[q, r, 'PerspectiveCandidates']} for r in (1, 2, 3)}
        inputs[q] = {'features': np.column_stack(columns).tolist(), 'dense': dense, 'pools': pools}
        missing[q] = {'action_missing': int(len(ids) - present_a.sum()), 'object_missing': int(len(ids) - present_o.sum())}
    sources = ['src/ax_research/pairwise_ridge.py', 'scripts/ranking_audit_20261109.py',
               'src/ax_research/retrieval/bm25.py', 'docs/ranking-audit-20261109-protocol.md',
               'docs/dense-preserved-candidates-20261108-predictions.json',
               '.work-new20-runtime/original/predictions/evidence.json',
               'docs/dense-bm25-candidates-2026-10-27/case_registry.json',
               'docs/validation-new20-20261107/questions.jsonl']
    save('-inputs', {'ids': ids, 'feature_names': FEATURES, 'inputs': inputs, 'missing': missing,
                     'outer_folds': {q: i % 5 for i, q in enumerate(sorted(inputs))},
                     'source_sha256': {p: digest(p) for p in sources}, 'paid_calls': 0,
                     'qrels_read': False, 'new40_read': False, 'test15_read': False})
    print('PREPARED', len(inputs), 'queries', len(ids), 'cases')


def infer():
    saved = read(PREFIX + '-inputs.json')
    assert all(digest(p) == h for p, h in saved['source_sha256'].items())
    ids, data, folds = saved['ids'], saved['inputs'], saved['outer_folds']
    features = {q: np.array(row['features']) for q, row in data.items()}
    # Only working labels are available to model selection. Other versions are not loaded.
    raw = read('docs/ax-transfer-relevance-20261108/02_working_transfer_qrels_2240.json')
    grades = {q: {} for q in data}
    for r in raw['records']:
        grades[r['query_id']][r['case_id']] = r['grade']
    labels = {q: [grades[q][c] >= 2 for c in ids] for q in data}
    settings = [(reg, alpha) for reg in (.1, 1., 10.) for alpha in (0., .5, 1.)]
    records, models = [], []
    for outer in range(5):
        train, test = sorted(q for q in data if folds[q] != outer), sorted(q for q in data if folds[q] == outer)
        choices = []
        for reg, alpha in settings:
            validation, inner_audit = [], []
            for inner in sorted(set(folds.values()) - {outer}):
                fit_queries = [q for q in train if folds[q] != inner]
                val_queries = [q for q in train if folds[q] == inner]
                assert not (set(fit_queries) & set(val_queries) or set(test) & (set(fit_queries) | set(val_queries)))
                weights = fit_pairwise(features, labels, fit_queries, reg)
                for q in val_queries:
                    ranking = rank_pool(ids, score(features[q], weights, alpha), data[q]['pools']['1']['DensePool'], data[q]['dense'])
                    validation.append(metrics(ranking, grades[q]))
                inner_audit.append({'training_queries': fit_queries, 'validation_queries': val_queries})
            aggregate = {m: mean(v[m] for v in validation if v[m] is not None) for m in ('F1@5', 'nDCG@10')}
            choices.append({'lambda': reg, 'learned_share': alpha, 'validation': aggregate, 'inner_splits': inner_audit})
        chosen = max(choices, key=lambda c: (c['validation']['F1@5'], c['validation']['nDCG@10'], -c['learned_share'], c['lambda']))
        weights = fit_pairwise(features, labels, train, chosen['lambda'])
        models.append({'outer_fold': outer, 'training_queries': train, 'test_queries': test,
                       'choice': chosen, 'choices': choices, 'weights': weights.tolist()})
        for q in test:
            values = score(features[q], weights, chosen['learned_share'])
            for repeat in (1, 2, 3):
                records.append({'query_id': q, 'repeat': repeat, 'system': 'Dense', 'ranking': data[q]['dense']})
                for pool, candidates in data[q]['pools'][str(repeat)].items():
                    records.append({'query_id': q, 'repeat': repeat, 'system': 'Learned_' + pool,
                                    'ranking': rank_pool(ids, values, candidates, data[q]['dense'])})
    historical = read('docs/validation-new20-20261107/measured/predictions_new20.json')
    records += [{**r, 'system': 'E'} for r in historical['systems']['E']]
    save('-predictions', {'rankings': records, 'models': models, 'input_sha256': digest(PREFIX + '-inputs.json'),
                          'training_labels_sha256': digest('docs/ax-transfer-relevance-20261108/02_working_transfer_qrels_2240.json'),
                          'state': 'FROZEN_NESTED_QUERY_OOF_DEVELOPMENT', 'paid_calls': 0,
                          'new40_read': False, 'test15_read': False, 'sensitivity_labels_read': False})
    print('FROZEN', len(records), 'rankings')
    print('choices', [(m['outer_fold'], m['choice']['lambda'], m['choice']['learned_share']) for m in models])


def evaluate():
    from scripts.improvement_cycle2 import evaluate as assess, label_sets
    saved, inputs = read(PREFIX + '-predictions.json'), read(PREFIX + '-inputs.json')
    assert saved['input_sha256'] == digest(PREFIX + '-inputs.json')
    ids, data = inputs['ids'], inputs['inputs']
    results, diagnostic = {}, {}
    for version, grades in label_sets().items():
        result = assess(saved['rankings'], grades)
        per = result['per_query']
        comparisons = {}
        for method in ('Learned_DensePool', 'Learned_TokenPool', 'Learned_PerspectivePool'):
            comparisons[method] = {}
            for baseline in ('Dense', 'Learned_DensePool', 'Learned_TokenPool'):
                comparisons[method][baseline] = {}
                for metric in ('F1@5', 'nDCG@10'):
                    delta = [r[method][metric] - r[baseline][metric] for r in per.values() if r[method][metric] is not None]
                    comparisons[method][baseline][metric] = {'delta': mean(delta), 'interval95': interval(delta),
                                                            'queries_improved': sum(v > 1e-12 for v in delta),
                                                            'queries_harmed': sum(v < -1e-12 for v in delta)}
        result['comparisons'] = comparisons
        failures = []
        for q, d in sorted(data.items()):
            top = d['dense'][:5]
            failures.append({'query_id': q, 'positive_count': sum(v >= 2 for v in grades[q].values()),
                'top5_negative': [c for c in top if grades[q][c] < 2],
                'positive_dense_rank6_20': [c for c in d['dense'][5:20] if grades[q][c] >= 2],
                'positive_outside_dense20': [c for c in d['dense'][20:] if grades[q][c] >= 2],
                'candidate_oracle': {pool: mean(metrics(sorted(candidates, key=lambda c: (-grades[q][c], c)), grades[q])['F1@5'] or 0
                    for candidates in [d['pools'][str(r)][pool] for r in (1, 2, 3)])
                    if any(v >= 2 for v in grades[q].values()) else None
                    for pool in ('DensePool', 'TokenPool', 'PerspectivePool')}})
        diagnostic[version] = failures
        results[version] = result
        print(version, {s: {m: round(v[m]['mean'], 6) for m in ('F1@5', 'nDCG@10', 'Recall@20')} for s, v in result['summary'].items()})
    decisions = {}
    for method in ('Learned_DensePool', 'Learned_TokenPool', 'Learned_PerspectivePool'):
        checks = {v: {'f1_improves': r['comparisons'][method]['Dense']['F1@5']['delta'] > 0,
                      'ndcg_non_decreasing': r['comparisons'][method]['Dense']['nDCG@10']['delta'] >= -1e-12}
                  for v, r in results.items()}
        lower = results['working_transfer']['comparisons'][method]['Dense']['F1@5']['interval95'][0]
        accepted = all(all(c.values()) for c in checks.values()) and lower > 0
        decisions[method] = {'decision': 'PROVISIONAL_DEV_ONLY' if accepted else 'DO_NOT_ADOPT',
                             'checks': checks, 'working_f1_ci_lower': lower}
    save('-evaluation', {'results': results, 'diagnostics': diagnostic, 'decisions': decisions,
                         'prediction_sha256': digest(PREFIX + '-predictions.json'), 'paid_calls': 0,
                         'labels_changed': False, 'state': 'FIVE_STEP_DEVELOPMENT_AUDIT_COMPLETE',
                         'limits': ['Previously inspected development queries, not independent test',
                                    'AI Silver labels; three versions are not independent replications',
                                    'Same case corpus shared across folds', 'Condition/negation semantics not newly modeled',
                                    'Bootstrap intervals descriptive, not selection/multiplicity adjusted']})
    print('DECISIONS', decisions)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=['prepare', 'infer', 'evaluate'])
    globals()[parser.parse_args().phase]()
