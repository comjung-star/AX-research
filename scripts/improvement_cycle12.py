"""Late routing between frozen E and token candidates, held out by query."""
import hashlib
import json
from collections import defaultdict
from statistics import mean

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from ax_research.action_aggregation import purpose_filter
from ax_research.functional_mapping import extract
from scripts.improvement_cycle import ROOT, read
from scripts.improvement_cycle2 import evaluate, label_sets
from scripts.improvement_cycle4 import assign_folds
from scripts.improvement_cycle11 import BASE, ORIGINAL_CACHE
from scripts.autonomous_trial2_mapping_replay import metrics


def jaccard(first, second):
    return len(set(first) & set(second)) / len(set(first) | set(second))


def training_targets(training_queries, grades, ranks):
    targets = {}
    for query in training_queries:
        if any(value is None for value in grades[query].values()):
            continue
        scores = {name: [metrics(ranks[query, repeat, name], grades[query]) for repeat in (1, 2, 3)] for name in ('E', 'Token')}
        if scores['E'][0]['F1@5'] is None:
            continue
        differences = [mean(row[metric] for row in scores['E']) - mean(row[metric] for row in scores['Token']) for metric in ('F1@5', 'nDCG@10')]
        difference = next((value for value in differences if abs(value) > 1e-12), None)
        if difference is not None:
            targets[query] = int(difference > 0)
    return targets


def route(features, training_queries, heldout_queries, primary, ranks):
    assert not set(training_queries) & set(heldout_queries)
    targets = training_targets(training_queries, primary, ranks)
    assert targets and set(targets) <= set(training_queries)
    selected = sorted(targets)
    scaler = StandardScaler().fit([features[query] for query in selected])
    classes = sorted(set(targets.values()))
    model = None
    if len(classes) == 2:
        model = LogisticRegression(C=1, class_weight='balanced', solver='liblinear', random_state=20261108)
        model.fit(scaler.transform([features[query] for query in selected]), [targets[query] for query in selected])
    decisions = {}
    for query in heldout_queries:
        probability = float(model.predict_proba(scaler.transform([features[query]]))[0, list(model.classes_).index(1)]) if model is not None else float(classes[0])
        decisions[query] = {'probability_E': probability, 'method': 'E' if probability >= .5 else 'Token'}
    audit = {'training_queries': list(training_queries), 'heldout_queries': list(heldout_queries), 'targets': targets,
             'scaler_training_queries': selected, 'scaler_mean': scaler.mean_.tolist(), 'scaler_scale': scaler.scale_.tolist(),
             'coefficients': model.coef_.tolist() if model is not None else None,
             'intercept': model.intercept_.tolist() if model is not None else None, 'constant_class': classes[0] if len(classes) == 1 else None}
    return decisions, audit


def main():
    destination = ROOT / 'docs/improvement-cycle12-20261108-results.json'
    if destination.exists():
        raise FileExistsError(destination)
    new = read('docs/improvement-cycle10-20261108-results.json')
    old = read('docs/improvement-cycle11-20261108-results.json')
    rankings = []
    for source in (new, old):
        for row in source['rankings']:
            if row['system'] in ('E', 'Dense', 'token_hybrid_multi'):
                rankings.append({**row, 'system': 'Token' if row['system'] == 'token_hybrid_multi' else row['system']})
    ranks = {(row['query_id'], row['repeat'], row['system']): row['ranking'] for row in rankings}
    rules = read('configs/functional_mapping_20261028.json')
    config = read('configs/action_aggregation_20261102.json')
    cls = {}
    for path in [ROOT / 'docs/query-case-semantic-mapping-2026-10-28/mapping/embeddings.npz',
                 ROOT / 'validation20-scratch/original/new_query_vectors.npz', ROOT / '.work-new20-runtime/inference/branch_vectors.npz',
                 ORIGINAL_CACHE, ROOT / BASE / 'inference/branch_vectors.npz']:
        with np.load(path, allow_pickle=False) as archive:
            cls.update(zip(archive['texts'].tolist(), archive['vectors']))
    questions, groups, original_dense = {}, defaultdict(list), {}
    collections = {}
    for name, question_path, prefix in [('new20', 'docs/validation-new20-20261107/questions.jsonl', '.work-new20-runtime/'),
                                         ('CPD', BASE + 'questions.jsonl', BASE)]:
        for row in map(json.loads, (ROOT / question_path).read_text(encoding='utf-8').splitlines()):
            questions[row['query_id']] = row['text']
            collections[row['query_id']] = name
        for row in read(prefix + 'inference/paths.json')['paths']:
            if row['query_id'].startswith('E_'):
                groups[row['parent_query_id']].append(row)
        for row in read(prefix + 'original/predictions/evidence.json')['records']:
            original_dense.setdefault(row['query_id'], {})[row['case_id']] = row['dense']
    features = {}
    feature_names = ['function_count', 'action_family_count', 'log_text_length', 'core_retention', 'branch_cosine_mean',
                     'branch_cosine_std', 'E_Dense_jaccard', 'Token_Dense_jaccard', 'E_Token_jaccard',
                     'dense_top_gap', 'dense_top5_spread', 'dense_std']
    for query, text in questions.items():
        profile = purpose_filter(extract(text, rules), config)
        functions = set(profile['function_ids'])
        branch_functions = [set(purpose_filter(extract(row['text'], rules), config)['function_ids']) for row in groups[query]]
        similarity = [float(cls[text] @ cls[row['text']]) for row in groups[query]]
        agreement = [mean(jaccard(ranks[query, repeat, left][:5], ranks[query, repeat, right][:5]) for repeat in (1, 2, 3))
                     for left, right in [('E', 'Dense'), ('Token', 'Dense'), ('E', 'Token')]]
        dense = sorted(original_dense[query].values(), reverse=True)
        features[query] = [len(functions), len(profile['action_family_hits']), float(np.log1p(len(text))),
                           mean(len(functions & branch) / len(functions) if functions else 0 for branch in branch_functions),
                           mean(similarity), float(np.std(similarity)), *agreement,
                           dense[0] - dense[1], dense[0] - dense[4], float(np.std(dense))]
        assert len(features[query]) == len(feature_names)
    versions = label_sets()
    cpd = defaultdict(dict)
    for row in read(BASE + 'labels.json')['records']:
        cpd[row['query_id']][row['case_id']] = row['grade']
    primary = {**versions['working_transfer'], **cpd}
    assert len(primary) == 28
    folds = assign_folds(primary)
    decisions, audit = {}, []
    for fold in range(5):
        training = sorted(query for query in primary if folds[query] != fold)
        heldout = sorted(query for query in primary if folds[query] == fold)
        local, evidence = route(features, training, heldout, primary, ranks)
        decisions.update(local)
        audit.append({'fold': fold, **evidence})
    stress, stress_audit = {}, []
    for collection in ('new20', 'CPD'):
        training = sorted(query for query in primary if collections[query] != collection)
        heldout = sorted(query for query in primary if collections[query] == collection)
        local, evidence = route(features, training, heldout, primary, ranks)
        stress.update(local)
        stress_audit.append({'heldout_collection': collection, **evidence})
    for system, choices in [('Router', decisions), ('CollectionHeldoutRouter', stress)]:
        for query, decision in choices.items():
            for repeat in (1, 2, 3):
                rankings.append({'query_id': query, 'repeat': repeat, 'system': system, 'ranking': ranks[query, repeat, decision['method']]})
    results = {name: evaluate([row for row in rankings if row['query_id'] in grades], grades) for name, grades in versions.items()}
    complete_cpd = {query: grades for query, grades in cpd.items() if all(grade is not None for grade in grades.values())}
    results['CPD_complete6'] = evaluate([row for row in rankings if row['query_id'] in complete_cpd], complete_cpd)
    inputs = ['scripts/improvement_cycle12.py', 'docs/improvement-cycle12-20261108-protocol.md',
              'docs/improvement-cycle10-20261108-results.json', 'docs/improvement-cycle11-20261108-results.json']
    output = {'state': 'QUERY_HELDOUT_LATE_ROUTING_DEVELOPMENT', 'results': results, 'rankings': rankings, 'decisions': decisions,
              'training_audit': audit, 'collection_heldout_decisions': stress, 'collection_heldout_audit': stress_audit,
              'feature_names': feature_names, 'features': features, 'folds': folds, 'paid_calls': 0, 'test_access': False,
              'input_sha256': {path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in inputs},
              'limits': ['All queries previously inspected development data', 'Case registry shared',
                         'Collection identity excluded from features; text/style may still proxy collection',
                         'No gate grid or tuning to sensitivity labels']}
    destination.write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    for label, result in results.items():
        for name, values in result['summary'].items():
            print(label, name, 'F1', round(values['F1@5']['mean'], 5), 'nDCG', round(values['nDCG@10']['mean'], 5))


if __name__ == '__main__':
    main()
