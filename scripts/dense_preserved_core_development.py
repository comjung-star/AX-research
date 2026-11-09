"""Predict Dense-preserved development comparisons before reading frozen labels."""
import hashlib
import json
from collections import defaultdict

import numpy as np
import torch

from ax_research.dense_preservation import preserve_dense_core
from ax_research.token_interaction import TokenInteractionRanker
from scripts.improvement_cycle import ROOT, read

DESTINATION = ROOT / 'docs/dense-preserved-core-20261108-predictions.json'


def main():
    if DESTINATION.exists():
        raise FileExistsError(DESTINATION)
    torch.set_num_threads(4)
    registry = read('docs/dense-bm25-candidates-2026-10-27/case_registry.json')['cases']
    ids = sorted(registry)
    def tokens(text):
        path = ROOT / '.work-cycle10-token-cache' / (hashlib.sha256(text.encode()).hexdigest() + '.npz')
        with np.load(path, allow_pickle=False) as archive:
            return archive['vectors'].astype(np.float32)
    matcher = TokenInteractionRanker({case: tokens(row['task']) for case, row in registry.items()})
    questions = {row['query_id']: row['text'] for row in map(json.loads, (ROOT / 'docs/validation-new20-20261107/questions.jsonl').read_text(encoding='utf-8').splitlines())}
    dense = defaultdict(dict)
    core_similarity = defaultdict(dict)
    for row in read('.work-new20-runtime/original/predictions/evidence.json')['records']:
        dense[row['query_id']][row['case_id']] = row['dense']
        core_similarity[row['query_id']][row['case_id']] = {field: row['semantic']['components'].get(field, {}).get('cosine') for field in ('action', 'object')}
    branch_scores = defaultdict(dict)
    with (ROOT / '.work-new20-runtime/inference/branch_scores.jsonl').open(encoding='utf-8') as source:
        for line in source:
            row = json.loads(line)
            if row['path_id'].startswith('E_'):
                branch_scores[row['path_id']][row['case_id']] = row['dense']
    groups = defaultdict(list)
    for row in read('.work-new20-runtime/inference/paths.json')['paths']:
        if row['query_id'].startswith('E_'):
            groups[row['parent_query_id'], row['repeat'] - 6].append(row['query_id'])
    historical = read('docs/validation-new20-20261107/measured/predictions_new20.json')
    rankings = [{**row, 'system': 'E'} for row in historical['systems']['E']]
    traces = []
    for query, text in sorted(questions.items()):
        original_tokens = dict(zip(matcher.case_ids, map(float, matcher.token_scores(tokens(text)))))
        baseline = sorted(ids, key=lambda case: (-dense[query][case], case))
        original = preserve_dense_core(dense[query], original_tokens, core_similarity[query])
        for repeat in (1, 2, 3):
            branches = {path: sorted(ids, key=lambda case: (-branch_scores[path][case], case)) for path in groups[query, repeat]}
            multi = preserve_dense_core(dense[query], original_tokens, core_similarity[query], branches)
            assert original['ranking'][:3] == multi['ranking'][:3] == baseline[:3]
            rankings.extend([{'query_id': query, 'repeat': repeat, 'system': 'Dense', 'ranking': baseline},
                             {'query_id': query, 'repeat': repeat, 'system': 'ProtectedToken', 'ranking': original['ranking']},
                             {'query_id': query, 'repeat': repeat, 'system': 'ProtectedPerspectiveToken', 'ranking': multi['ranking']}])
            traces.extend([{'query_id': query, 'repeat': repeat, 'system': name, **result}
                           for name, result in [('ProtectedToken', original), ('ProtectedPerspectiveToken', multi)]])
    assert len(rankings) == 240 and len(traces) == 120
    sources = ['src/ax_research/dense_preservation.py', 'src/ax_research/token_interaction.py',
               'docs/dense-preserved-core-20261108-protocol.md', 'docs/validation-new20-20261107/questions.jsonl',
               '.work-new20-runtime/original/predictions/evidence.json', '.work-new20-runtime/inference/branch_scores.jsonl']
    output = {'state': 'DENSE_PRESERVED_DEV_PREDICTIONS_SEALED', 'rankings': rankings, 'traces': traces,
              'branch_rankings': {path: sorted(ids, key=lambda case: (-values[case], case)) for path, values in branch_scores.items()},
              'qrels_read': False, 'new40_pilot_read': False, 'paid_calls': 0,
              'protected_count': 3, 'candidate_budget': 20, 'output_budget': 5,
              'source_sha256': {path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in sources}}
    with DESTINATION.open('x', encoding='utf-8') as target:
        target.write(json.dumps(output, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'state': output['state'], 'rankings': len(rankings), 'traces': len(traces)}))


if __name__ == '__main__':
    main()
