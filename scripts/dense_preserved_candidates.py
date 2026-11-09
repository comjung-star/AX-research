"""Matched-budget candidate complement controls; DenseTop10 remains immutable."""
import hashlib
import json
from collections import defaultdict

import numpy as np
import torch

from ax_research.dense_preservation import preserve_dense_candidates
from ax_research.token_interaction import TokenInteractionRanker, normalize_scores
from ax_research.retrieval.bm25 import BM25Retriever
from scripts.improvement_cycle import ROOT, read


def main():
    destination = ROOT / 'docs/dense-preserved-candidates-20261108-predictions.json'
    if destination.exists():
        raise FileExistsError(destination)
    torch.set_num_threads(4)
    cases = read('docs/dense-bm25-candidates-2026-10-27/case_registry.json')['cases']
    ids = sorted(cases)
    def tokens(text):
        path = ROOT / '.work-cycle10-token-cache' / (hashlib.sha256(text.encode()).hexdigest() + '.npz')
        with np.load(path, allow_pickle=False) as archive:
            return archive['vectors'].astype(np.float32)
    matcher = TokenInteractionRanker({case: tokens(cases[case]['task']) for case in ids})
    sparse = BM25Retriever({case: '\n'.join(cases[case][field] for field in ('problem', 'task', 'context')) for case in ids})
    questions = {row['query_id']: row['text'] for row in map(json.loads, (ROOT / 'docs/validation-new20-20261107/questions.jsonl').read_text(encoding='utf-8').splitlines())}
    dense, core = defaultdict(dict), defaultdict(dict)
    for row in read('.work-new20-runtime/original/predictions/evidence.json')['records']:
        dense[row['query_id']][row['case_id']] = row['dense']
        core[row['query_id']][row['case_id']] = {field: row['semantic']['components'].get(field, {}).get('cosine') for field in ('action', 'object')}
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
    traces, inputs = [], {}
    for query, text in sorted(questions.items()):
        token_values = matcher.token_scores(tokens(text))
        token_map = dict(zip(ids, map(float, token_values)))
        dense_order = sorted(ids, key=lambda case: (-dense[query][case], case))
        hybrid = .5 * normalize_scores([dense[query][case] for case in ids]) + .5 * normalize_scores(token_values)
        hybrid_map = dict(zip(ids, map(float, hybrid)))
        token_order = sorted(ids, key=lambda case: (-hybrid_map[case], case))
        sparse_order = [row.case_id for row in sparse.search(text)]
        inputs[query] = {'dense': dense[query], 'token': token_map, 'core': core[query],
                         'query_token_order': token_order, 'sparse_order': sparse_order, 'branches': {}}
        for repeat in (1, 2, 3):
            branches = {path: sorted(ids, key=lambda case: (-branch_scores[path][case], case)) for path in groups[query, repeat]}
            inputs[query]['branches'][str(repeat)] = branches
            rankings.append({'query_id': query, 'repeat': repeat, 'system': 'Dense', 'ranking': dense_order})
            sources = {'QueryTokenCandidates': {'OriginalToken': token_order},
                       'QuerySparseCandidates': {'OriginalSparse': sparse_order},
                       'PerspectiveCandidates': branches}
            for system, branch_input in sources.items():
                result = preserve_dense_candidates(dense[query], token_map, core[query], branch_input)
                assert result['ranking'][:10] == dense_order[:10]
                rankings.append({'query_id': query, 'repeat': repeat, 'system': system, 'ranking': result['ranking']})
                traces.append({'query_id': query, 'repeat': repeat, 'system': system, **result})
    assert len(rankings) == 300 and len(traces) == 180
    paths = ['src/ax_research/dense_preservation.py', 'src/ax_research/retrieval/bm25.py',
             'docs/dense-preserved-candidates-20261108-protocol.md']
    output = {'state': 'CANDIDATE_COMPLEMENT_WITH_STRONG_SINGLE_QUERY_CONTROLS', 'rankings': rankings,
              'traces': traces, 'inputs': inputs, 'qrels_read': False, 'new40_pilot_read': False, 'paid_calls': 0,
              'search_depth_per_path': 20, 'candidate_budget': 20, 'output_budget': 5,
              'source_sha256': {path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in paths}}
    with destination.open('x', encoding='utf-8') as target:
        target.write(json.dumps(output, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'state': output['state'], 'rankings': len(rankings), 'traces': len(traces)}))


if __name__ == '__main__':
    main()
