"""Separate-view vector evidence and small query-held-out neural scorers."""
import hashlib
import json
from collections import defaultdict

import numpy as np
import torch
from sklearn.preprocessing import StandardScaler

from scripts.improvement_cycle import ROOT, read
from scripts.improvement_cycle2 import evaluate, label_sets
from scripts.improvement_cycle4 import assign_folds


def fidelity_weights(similarity):
    logits = np.asarray(similarity) / .1
    weights = np.exp(logits - np.max(logits))
    return weights / weights.sum()


def main():
    destination = ROOT / 'docs/improvement-cycle6-20261108-results.json'
    if destination.exists():
        raise FileExistsError(destination)
    torch.set_num_threads(1)
    labels = label_sets()
    primary = labels['working_transfer']
    ids = sorted(next(iter(primary.values())))
    cache_paths = ['docs/query-case-semantic-mapping-2026-10-28/mapping/embeddings.npz',
                   'validation20-scratch/original/new_query_vectors.npz', '.work-new20-runtime/inference/branch_vectors.npz']
    embeddings = {}
    for path in cache_paths:
        with np.load(ROOT / path, allow_pickle=False) as archive:
            for text, vector in zip(archive['texts'].tolist(), archive['vectors']):
                if text in embeddings:
                    np.testing.assert_allclose(vector, embeddings[text], atol=1e-5)
                embeddings[text] = vector
    dense_archive = np.load(ROOT / 'docs/stage123-openai-triplicate-2026-10-27/embeddings.npz', allow_pickle=False)
    case_positions = {case: position for position, case in enumerate(dense_archive['case_ids'].tolist())}
    views = {view: np.asarray([dense_archive[view][case_positions[case]] for case in ids]) for view in ('single', 'problem', 'task', 'context')}
    questions = {row['query_id']: row['text'] for row in map(json.loads, (ROOT / 'docs/validation-new20-20261107/questions.jsonl').read_text(encoding='utf-8').splitlines())}
    groups = defaultdict(list)
    for row in read('.work-new20-runtime/inference/paths.json')['paths']:
        if row['query_id'].startswith('E_'):
            groups[row['parent_query_id'], row['repeat'] - 6].append(row)
    original = {(row['query_id'], row['case_id']): row['dense'] for row in read('.work-new20-runtime/original/predictions/evidence.json')['records']}
    branch_dense = {}
    with (ROOT / '.work-new20-runtime/inference/branch_scores.jsonl').open(encoding='utf-8') as source:
        for line in source:
            row = json.loads(line)
            if row['path_id'].startswith('E_'):
                branch_dense[row['path_id'], row['case_id']] = row['dense']
    prior = read('docs/improvement-cycle4-20261108-results.json')
    rankings = [row for row in prior['rankings'] if row['system'] in ('E', 'Dense')]
    features, branch_audit = {}, []
    for query in sorted(primary):
        vector = embeddings[questions[query]]
        dense = views['single'] @ vector
        np.testing.assert_allclose(dense, [original[query, case] for case in ids], atol=1e-6)
        original_views = np.stack([views[view] @ vector for view in ('problem', 'task', 'context')], axis=1)
        repeated_features = []
        for repeat in (1, 2, 3):
            paths = sorted(groups[query, repeat], key=lambda row: row['query_id'])
            assert len(paths) == 3
            branch_vectors = np.stack([embeddings[row['text']] for row in paths])
            reproduced = views['single'] @ branch_vectors.T
            expected = [[branch_dense[path['query_id'], case] for path in paths] for case in ids]
            np.testing.assert_allclose(reproduced, expected, atol=1e-6)
            similarities = branch_vectors @ vector
            weights = fidelity_weights(similarities)
            branch_views = np.stack([views[view] @ branch_vectors.T for view in ('problem', 'task', 'context')], axis=2)
            weighted = np.einsum('bpv,p->bv', branch_views, weights)
            values = {'task_single': original_views[:, 1], 'views_single': original_views.mean(axis=1),
                      'views_mean_multi': .5 * original_views.mean(axis=1) + .5 * branch_views.mean(axis=(1, 2)),
                      'task_max_multi': .5 * original_views[:, 1] + .5 * branch_views[:, :, 1].max(axis=1),
                      'task_fidelity_multi': .5 * original_views[:, 1] + .5 * weighted[:, 1]}
            for name, scores in values.items():
                ranking = [ids[position] for position in sorted(range(112), key=lambda position: (-scores[position], ids[position]))]
                rankings.append({'query_id': query, 'repeat': repeat, 'system': name, 'ranking': ranking})
            statistics = np.concatenate([branch_views.max(axis=1), branch_views.mean(axis=1), branch_views.min(axis=1), weighted], axis=1)
            repeated_features.append(np.concatenate([dense[:, None], original_views, statistics], axis=1))
            branch_audit.append({'query_id': query, 'repeat': repeat, 'paths': [row['query_id'] for row in paths],
                                 'query_branch_cosine': similarities.tolist(), 'weights': weights.tolist(),
                                 'branch_case_view_scores': branch_views.tolist()})
        features[query] = np.mean(repeated_features, axis=0)
        assert features[query].shape == (112, 16)
    folds = assign_folds(primary)
    training_audit = []
    for fold in range(5):
        training = sorted(query for query in primary if folds[query] != fold)
        heldout = sorted(query for query in primary if folds[query] == fold)
        assert not set(training) & set(heldout)
        for name, width in [('neural_single', 4), ('neural_multi', 16)]:
            torch.manual_seed(20261108)
            scaler = StandardScaler().fit(np.concatenate([features[query][:, :width] for query in training]))
            matrices = {query: torch.tensor(scaler.transform(values[:, :width]), dtype=torch.float32) for query, values in features.items()}
            pairs = {}
            for query in training:
                top = sorted(range(112), key=lambda position: (-features[query][position, 0], ids[position]))[:20]
                positives = [position for position, case in enumerate(ids) if primary[query][case] >= 2]
                negatives = [position for position in top if primary[query][ids[position]] < 2]
                if positives and negatives:
                    pairs[query] = (torch.tensor([positive for positive in positives for negative in negatives]),
                                    torch.tensor([negative for positive in positives for negative in negatives]))
            model = torch.nn.Sequential(torch.nn.Linear(width, 8), torch.nn.Tanh(), torch.nn.Linear(8, 1))
            torch.nn.init.zeros_(model[-1].bias)
            optimizer = torch.optim.Adam(model.parameters(), lr=.01, weight_decay=.01)
            losses = []
            for epoch in range(100):
                optimizer.zero_grad()
                query_losses = []
                for query, (positives, negatives) in pairs.items():
                    scores = model(matrices[query]).flatten()
                    query_losses.append(torch.nn.functional.softplus(-(scores[positives] - scores[negatives])).mean())
                loss = torch.stack(query_losses).mean()
                loss.backward()
                optimizer.step()
                if epoch in (0, 99):
                    losses.append(float(loss.detach()))
            training_audit.append({'fold': fold, 'system': name, 'training_queries': training, 'heldout_queries': heldout,
                                   'loss_first_last': losses, 'state_dict': {key: value.detach().tolist() for key, value in model.state_dict().items()},
                                   'scaler_mean': scaler.mean_.tolist(), 'scaler_scale': scaler.scale_.tolist()})
            with torch.no_grad():
                for query in heldout:
                    scores = model(matrices[query]).flatten().tolist()
                    ranking = [ids[position] for position in sorted(range(112), key=lambda position: (-scores[position], ids[position]))]
                    for repeat in (1, 2, 3):
                        rankings.append({'query_id': query, 'repeat': repeat, 'system': name, 'ranking': ranking})
    results = {name: evaluate(rankings, grades) for name, grades in labels.items()}
    inputs = cache_paths + ['docs/stage123-openai-triplicate-2026-10-27/embeddings.npz', 'scripts/improvement_cycle6.py', 'docs/improvement-cycle6-20261108-protocol.md']
    output = {'state': 'SEPARATE_CASE_VIEW_AND_QUERY_HELDOUT_NEURAL_DEVELOPMENT', 'rankings': rankings, 'results': results,
              'folds': folds, 'training_audit': training_audit, 'branch_audit': branch_audit, 'case_order': ids,
              'paid_calls': 0, 'test_access': False, 'dense_reproduction_queries': 20, 'dense_reproduction_branches': 180,
              'input_sha256': {path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in inputs},
              'limits': ['Repeatedly inspected development queries; no independent-test claim', 'Shared cases across query folds',
                         'Neural model consumes view similarity features, not full raw-vector interaction']}
    destination.write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    for label, result in results.items():
        for name, values in result['summary'].items():
            print(label, name, 'F1', round(values['F1@5']['mean'], 5), 'nDCG', round(values['nDCG@10']['mean'], 5))


if __name__ == '__main__':
    main()
