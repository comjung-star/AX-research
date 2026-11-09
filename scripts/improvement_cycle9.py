"""Frozen-vector branch-preserving interaction with query-held-out evaluation."""
import hashlib
import json
from pathlib import Path

import numpy as np
import torch

from scripts.improvement_cycle import ROOT, read
from scripts.improvement_cycle2 import evaluate, label_sets
from scripts.improvement_cycle4 import assign_folds


class VectorInteraction(torch.nn.Module):
    def __init__(self, dimensions=1024):
        super().__init__()
        self.network = torch.nn.Sequential(torch.nn.Linear(dimensions * 4, 8), torch.nn.Tanh(),
                                           torch.nn.Dropout(.1), torch.nn.Linear(8, 1))

    def forward(self, query_vectors, case_views):
        case_count, view_count, dimensions = case_views.shape
        branch_count = len(query_vectors)
        query = query_vectors[None, :, None, :].expand(case_count, branch_count, view_count, dimensions)
        cases = case_views[:, None, :, :].expand_as(query)
        interaction = torch.cat([query, cases, query * cases, torch.abs(query - cases)], dim=-1)
        view_scores = self.network(interaction).squeeze(-1)
        branch_scores = view_scores.mean(dim=-1)
        if branch_count == 1:
            return branch_scores[:, 0], branch_scores, view_scores
        return .5 * branch_scores[:, 0] + .5 * branch_scores[:, 1:].max(dim=1).values, branch_scores, view_scores


def load_vectors(ids, queries):
    embeddings = {}
    for path in ['docs/query-case-semantic-mapping-2026-10-28/mapping/embeddings.npz',
                 'validation20-scratch/original/new_query_vectors.npz', '.work-new20-runtime/inference/branch_vectors.npz']:
        with np.load(ROOT / path, allow_pickle=False) as archive:
            embeddings.update(zip(archive['texts'].tolist(), archive['vectors']))
    with np.load(ROOT / 'docs/stage123-openai-triplicate-2026-10-27/embeddings.npz', allow_pickle=False) as archive:
        positions = {case: position for position, case in enumerate(archive['case_ids'].tolist())}
        case_views = torch.tensor(np.stack([[archive[view][positions[case]] for view in ('problem', 'task', 'context')] for case in ids]))
    questions = {row['query_id']: row['text'] for row in map(json.loads, (ROOT / 'docs/validation-new20-20261107/questions.jsonl').read_text(encoding='utf-8').splitlines())}
    grouped = {query: {} for query in queries}
    for row in read('.work-new20-runtime/inference/paths.json')['paths']:
        if row['query_id'].startswith('E_'):
            slot = int(row['query_id'].rsplit('_', 1)[1])
            grouped[row['parent_query_id']].setdefault(slot, []).append(embeddings[row['text']])
    vectors = {}
    for query in queries:
        branches = []
        assert sorted(grouped[query]) == [1, 2, 3]
        for slot in (1, 2, 3):
            assert len(grouped[query][slot]) == 3
            vector = np.mean(grouped[query][slot], axis=0)
            branches.append(vector / np.linalg.norm(vector))
        vectors[query] = torch.tensor(np.stack([embeddings[questions[query]], *branches]))
    return vectors, case_views


def main():
    destination = ROOT / 'docs/improvement-cycle9-20261108-results.json'
    model_directory = ROOT / 'docs/improvement-cycle9-20261108-models'
    if destination.exists() or model_directory.exists():
        raise FileExistsError('Cycle9 output already exists')
    torch.set_num_threads(2)
    labels = label_sets()
    primary = labels['working_transfer']
    ids = sorted(next(iter(primary.values())))
    vectors, cases = load_vectors(ids, primary)
    folds = assign_folds(primary)
    prior = read('docs/improvement-cycle8-20261108-results.json')
    rankings = [row for row in prior['rankings'] if row['system'] in ('E', 'Dense')]
    audit, evidence, model_states = [], [], {}
    for fold in range(5):
        training = sorted(query for query in primary if folds[query] != fold)
        heldout = sorted(query for query in primary if folds[query] == fold)
        assert not set(training) & set(heldout)
        pairs = {}
        for query in training:
            positives = [position for position, case in enumerate(ids) if all(version[query][case] >= 2 for version in labels.values())]
            negatives = [position for position, case in enumerate(ids) if all(version[query][case] < 2 for version in labels.values())]
            if positives and negatives:
                pairs[query] = (torch.tensor([positive for positive in positives for negative in negatives]),
                                torch.tensor([negative for positive in positives for negative in negatives]))
        for name, branch_count in [('vector_single', 1), ('vector_multi', 4)]:
            torch.manual_seed(20261108)
            model = VectorInteraction()
            optimizer = torch.optim.Adam(model.parameters(), lr=.001, weight_decay=.01)
            losses = []
            model.train()
            for epoch in range(24):
                optimizer.zero_grad()
                epoch_loss = 0.0
                for query, (positives, negatives) in pairs.items():
                    scores, _, _ = model(vectors[query][:branch_count], cases)
                    loss = torch.nn.functional.softplus(-(scores[positives] - scores[negatives])).mean() / len(pairs)
                    loss.backward()
                    epoch_loss += float(loss.detach())
                optimizer.step()
                if epoch in (0, 23):
                    losses.append(epoch_loss)
            audit.append({'fold': fold, 'system': name, 'training_queries': training, 'heldout_queries': heldout,
                          'pair_counts': {query: len(pair[0]) for query, pair in pairs.items()}, 'loss_first_last': losses})
            model_states[f'{name}_fold{fold}'] = {key: value.detach().clone() for key, value in model.state_dict().items()}
            model.eval()
            with torch.no_grad():
                for query in heldout:
                    scores, branch_scores, view_scores = model(vectors[query][:branch_count], cases)
                    ranking = [ids[position] for position in sorted(range(112), key=lambda position: (-float(scores[position]), ids[position]))]
                    evidence.append({'query_id': query, 'system': name, 'scores': scores.tolist(),
                                     'branch_scores': branch_scores.tolist(), 'case_view_scores': view_scores.tolist()})
                    for repeat in (1, 2, 3):
                        rankings.append({'query_id': query, 'repeat': repeat, 'system': name, 'ranking': ranking})
            print(json.dumps({'fold': fold, 'system': name, 'loss': losses}), flush=True)
    results = {name: evaluate(rankings, grades) for name, grades in labels.items()}
    model_directory.mkdir()
    for name, state in model_states.items():
        torch.save(state, model_directory / (name + '.pt'))
    inputs = ['scripts/improvement_cycle9.py', 'docs/improvement-cycle9-20261108-protocol.md',
              'docs/stage123-openai-triplicate-2026-10-27/embeddings.npz', 'validation20-scratch/original/new_query_vectors.npz',
              '.work-new20-runtime/inference/branch_vectors.npz']
    output = {'state': 'FROZEN_VECTOR_INTERACTION_QUERY_HELDOUT', 'results': results, 'rankings': rankings,
              'training_audit': audit, 'score_evidence': evidence, 'case_order': ids, 'paid_calls': 0, 'test_access': False,
              'input_sha256': {path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in inputs},
              'model_sha256': {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in model_directory.glob('*.pt')},
              'limitations': ['Previously inspected development queries, not fresh independent test', 'Cases shared across folds',
                              'Agreement across label versions is not independent gold', 'Generation repeat vectors averaged by fixed role']}
    destination.write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    for label, result in results.items():
        for name, values in result['summary'].items():
            print(label, name, 'F1', round(values['F1@5']['mean'], 5), 'nDCG', round(values['nDCG@10']['mean'], 5))


if __name__ == '__main__':
    main()
