"""Fixed query-group held-out calibration; no paid services or fresh embeddings."""
import hashlib
import json
from collections import defaultdict
from statistics import mean

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from ax_research.action_aggregation import purpose_filter
from ax_research.functional_mapping import compare, extract
from scripts.improvement_cycle import ROOT, read
from scripts.improvement_cycle2 import evaluate, label_sets
from scripts.autonomous_trial2_mapping_replay import interval


def assign_folds(queries):
    ordered = sorted(queries, key=lambda query: hashlib.sha256(query.encode()).hexdigest())
    return {query: position % 5 for position, query in enumerate(ordered)}


def pairwise_training(features, labels, training_queries):
    differences, targets, weights = [], [], []
    for query in sorted(training_queries):
        positives = sorted(case for case, grade in labels[query].items() if grade >= 2)
        negatives = sorted(case for case, grade in labels[query].items() if grade < 2)
        count = len(positives) * len(negatives)
        if not count:
            continue
        for positive in positives:
            for negative in negatives:
                difference = features[query, positive] - features[query, negative]
                differences.extend((difference, -difference))
                targets.extend((1, 0))
                weights.extend((1 / (2 * count), 1 / (2 * count)))
    weights = np.asarray(weights)
    weights *= len(weights) / weights.sum()
    return np.asarray(differences), np.asarray(targets), weights


def main():
    destination = ROOT / 'docs/improvement-cycle4-20261108-results.json'
    if destination.exists():
        raise FileExistsError(destination)
    labels = label_sets()
    primary = labels['working_transfer']
    folds = assign_folds(primary)
    prior = read('docs/improvement-cycle2-20261108-results.json')
    rankings = [row for row in prior['rankings'] if row['system'] in ('E', 'Dense')]
    rules = read('configs/functional_mapping_20261028.json')
    config = read('configs/action_aggregation_20261102.json')
    cases = read('docs/query-case-functional-mapping-2026-10-28/stage2/case_profiles.json')
    filtered = {case: {role: purpose_filter(profile, config) for role, profile in roles.items()} for case, roles in cases.items()}
    questions = {row['query_id']: row['text'] for row in map(json.loads, (ROOT / 'docs/validation-new20-20261107/questions.jsonl').read_text(encoding='utf-8').splitlines())}
    runtime = '.work-new20-runtime/'
    whole = {(row['query_id'], row['case_id']): row for row in read(runtime + 'original/predictions/evidence.json')['records']}
    groups = defaultdict(list)
    for row in read(runtime + 'inference/paths.json')['paths']:
        if row['query_id'].startswith('E_'):
            groups[row['parent_query_id'], row['repeat'] - 6].append(row['query_id'])
    branches = {}
    with (ROOT / runtime / 'inference/branch_scores.jsonl').open(encoding='utf-8') as source:
        for line in source:
            row = json.loads(line)
            if row['path_id'].startswith('E_'):
                branches[row['path_id'], row['case_id']] = row
    features = {}
    names = ['original_dense', 'original_semantic', 'original_rule', 'branch_dense_max', 'branch_dense_mean', 'branch_dense_min',
             'branch_semantic_max', 'branch_semantic_mean', 'branch_semantic_min', 'branch_rule_max', 'branch_rule_mean', 'branch_rule_min']
    for query in sorted(primary):
        profile = purpose_filter(extract(questions[query], rules), config)
        for case in sorted(primary[query]):
            record = whole[query, case]
            original_grade = compare(profile, filtered[case])['mapping_grade']
            repeats = []
            for repeat in (1, 2, 3):
                evidence = [branches[path, case] for path in groups[query, repeat]]
                assert len(evidence) == 3
                values = [record['dense'], record['semantic']['score'], original_grade / 4]
                for branch_values in ([row['dense'] for row in evidence], [row['semantic']['score'] for row in evidence],
                                      [row['C1_rule']['mapping_grade'] / 4 for row in evidence]):
                    values.extend((max(branch_values), mean(branch_values), min(branch_values)))
                repeats.append(values)
            features[query, case] = np.mean(repeats, axis=0)
    audit = []
    for fold in range(5):
        training = sorted(query for query in primary if folds[query] != fold)
        heldout = sorted(query for query in primary if folds[query] == fold)
        assert not set(training) & set(heldout) and len(training) == 16 and len(heldout) == 4
        for name, width in [('linear_single', 3), ('linear_multi', len(names))]:
            scaler = StandardScaler().fit([features[query, case][:width] for query in training for case in sorted(primary[query])])
            transformed = {key: scaler.transform([value[:width]])[0] for key, value in features.items()}
            differences, targets, weights = pairwise_training(transformed, primary, training)
            estimator = LogisticRegression(C=1, fit_intercept=False, solver='liblinear', random_state=20261108, max_iter=1000)
            estimator.fit(differences, targets, sample_weight=weights)
            assert estimator.n_iter_[0] < 1000
            audit.append({'fold': fold, 'system': name, 'training_queries': training, 'heldout_queries': heldout,
                          'pair_rows': len(targets), 'feature_names': names[:width], 'coefficients': estimator.coef_[0].tolist(),
                          'scaler_mean': scaler.mean_.tolist(), 'scaler_scale': scaler.scale_.tolist()})
            for query in heldout:
                ids = sorted(primary[query])
                scores = estimator.decision_function([transformed[query, case] for case in ids])
                ranking = [ids[position] for position in sorted(range(len(ids)), key=lambda position: (-scores[position], ids[position]))]
                for repeat in (1, 2, 3):
                    rankings.append({'query_id': query, 'repeat': repeat, 'system': name, 'ranking': ranking})
    results = {name: evaluate(rankings, grades) for name, grades in labels.items()}
    for label, result in results.items():
        for metric in ('F1@5', 'nDCG@10'):
            eligible = [row for row in result['per_query'].values() if row['linear_multi'][metric] is not None]
            differences = [row['linear_multi'][metric] - row['linear_single'][metric] for row in eligible]
            result['summary']['linear_multi'][metric]['linear_single'] = {'delta': mean(differences), 'interval95': interval(differences)}
    inputs = ['docs/improvement-cycle4-20261108-protocol.md', 'configs/functional_mapping_20261028.json',
              runtime + 'inference/branch_scores.jsonl', runtime + 'original/predictions/evidence.json',
              'docs/ax-transfer-relevance-20261108/02_working_transfer_qrels_2240.json', 'scripts/improvement_cycle4.py']
    output = {'state': 'QUERY_GROUP_OUT_OF_FOLD_DEVELOPMENT', 'folds': folds, 'training_audit': audit,
              'results': results, 'rankings': rankings, 'paid_calls': 0, 'test_access': False,
              'input_sha256': {path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in inputs},
              'limitations': ['20 development queries already inspected; not an external independent test',
                              'Case registry shared between training and heldout queries', 'Working AI labels used for training',
                              'Linear score calibration is a diagnostic baseline, not the full neural architecture']}
    destination.write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    for label, result in results.items():
        for name, values in result['summary'].items():
            print(label, name, 'F1', round(values['F1@5']['mean'], 5), 'nDCG', round(values['nDCG@10']['mean'], 5))


if __name__ == '__main__':
    main()
