"""Bounded residual calibration with query-held-out hard-negative learning."""
import hashlib
import json
from collections import defaultdict
from statistics import mean

import numpy as np
import torch
from sklearn.preprocessing import StandardScaler

from ax_research.action_aggregation import purpose_filter
from ax_research.functional_mapping import compare, extract
from scripts.improvement_cycle import ROOT, read
from scripts.improvement_cycle2 import evaluate, label_sets
from scripts.improvement_cycle4 import assign_folds
from scripts.autonomous_trial2_mapping_replay import interval


def load_features(primary):
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
    return features


def bounded_scores(dense, residual):
    return dense + .05 * torch.tanh(residual)


def main():
    destination = ROOT / 'docs/improvement-cycle5-20261108-results.json'
    if destination.exists():
        raise FileExistsError(destination)
    torch.set_num_threads(1)
    torch.manual_seed(20261108)
    labels = label_sets()
    primary = labels['working_transfer']
    folds = assign_folds(primary)
    features = load_features(primary)
    prior = read('docs/improvement-cycle4-20261108-results.json')
    rankings = [row for row in prior['rankings'] if row['system'] in ('E', 'Dense', 'linear_multi')]
    audit = []
    for fold in range(5):
        training = sorted(query for query in primary if folds[query] != fold)
        heldout = sorted(query for query in primary if folds[query] == fold)
        assert not set(training) & set(heldout)
        for name, width in [('bounded_single', 3), ('bounded_multi', 12)]:
            scaler = StandardScaler().fit([features[query, case][:width] for query in training for case in sorted(primary[query])])
            matrices, dense, ids = {}, {}, {}
            for query in primary:
                ids[query] = sorted(primary[query])
                matrices[query] = torch.tensor(scaler.transform([features[query, case][:width] for case in ids[query]]), dtype=torch.float32)
                dense[query] = torch.tensor([features[query, case][0] for case in ids[query]], dtype=torch.float32)
            pairs = {}
            for query in training:
                positions = {case: position for position, case in enumerate(ids[query])}
                top = sorted(ids[query], key=lambda case: (-features[query, case][0], case))[:20]
                positives = [positions[case] for case in ids[query] if primary[query][case] >= 2]
                negatives = [positions[case] for case in top if primary[query][case] < 2]
                if positives and negatives:
                    pairs[query] = (torch.tensor([positive for positive in positives for negative in negatives]),
                                    torch.tensor([negative for positive in positives for negative in negatives]))
            model = torch.nn.Linear(width, 1)
            torch.nn.init.zeros_(model.weight)
            torch.nn.init.zeros_(model.bias)
            optimizer = torch.optim.Adam(model.parameters(), lr=.03)
            loss_history = []
            for epoch in range(200):
                optimizer.zero_grad()
                losses = []
                for query, (positive_positions, negative_positions) in pairs.items():
                    scores = bounded_scores(dense[query], model(matrices[query]).flatten())
                    losses.append(torch.nn.functional.softplus(-(scores[positive_positions] - scores[negative_positions]) / .05).mean())
                loss = torch.stack(losses).mean() + .01 * (model.weight.square().mean() + model.bias.square().mean())
                loss.backward()
                optimizer.step()
                if epoch in (0, 199):
                    loss_history.append(float(loss.detach()))
            audit.append({'fold': fold, 'system': name, 'training_queries': training, 'heldout_queries': heldout,
                          'pair_counts': {query: len(pair[0]) for query, pair in pairs.items()}, 'loss_first_last': loss_history,
                          'weights': model.weight.detach().tolist(), 'bias': model.bias.detach().tolist(),
                          'scaler_mean': scaler.mean_.tolist(), 'scaler_scale': scaler.scale_.tolist()})
            with torch.no_grad():
                for query in heldout:
                    scores = bounded_scores(dense[query], model(matrices[query]).flatten()).tolist()
                    assert max(abs(scores[position] - float(dense[query][position])) for position in range(112)) <= .050001
                    ranking = [ids[query][position] for position in sorted(range(112), key=lambda position: (-scores[position], ids[query][position]))]
                    for repeat in (1, 2, 3):
                        rankings.append({'query_id': query, 'repeat': repeat, 'system': name, 'ranking': ranking})
    results = {name: evaluate(rankings, grades) for name, grades in labels.items()}
    for result in results.values():
        for metric in ('F1@5', 'nDCG@10'):
            eligible = [row for row in result['per_query'].values() if row['bounded_multi'][metric] is not None]
            differences = [row['bounded_multi'][metric] - row['bounded_single'][metric] for row in eligible]
            result['summary']['bounded_multi'][metric]['bounded_single'] = {'delta': mean(differences), 'interval95': interval(differences)}
    inputs = ['scripts/improvement_cycle5.py', 'docs/improvement-cycle5-20261108-protocol.md',
              'docs/ax-transfer-relevance-20261108/02_working_transfer_qrels_2240.json']
    output = {'state': 'QUERY_HELDOUT_BOUNDED_RESIDUAL_DEVELOPMENT', 'folds': folds, 'audit': audit,
              'results': results, 'rankings': rankings, 'paid_calls': 0, 'test_access': False,
              'input_sha256': {path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in inputs},
              'limitations': ['Development queries previously inspected; external independent evaluation remains required',
                              'Cases shared across query folds', 'Sensitivity labels used only to evaluate same predictions']}
    destination.write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    for label, result in results.items():
        for name, values in result['summary'].items():
            print(label, name, 'F1', round(values['F1@5']['mean'], 5), 'nDCG', round(values['nDCG@10']['mean'], 5))


if __name__ == '__main__':
    main()
