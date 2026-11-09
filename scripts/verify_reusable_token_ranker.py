"""Verify the reusable label-free ranker against both frozen experiments."""
import json
from collections import defaultdict

import numpy as np
import torch

from ax_research.token_interaction import TokenInteractionRanker
from scripts.improvement_cycle import ROOT, read
from scripts.improvement_cycle11 import BASE, ORIGINAL_CACHE
from scripts.improvement_cycle10 import digest


def verify(source, prefix, questions_path, cache_directory, original_cache):
    artifact = read(source)
    cases = read('docs/dense-bm25-candidates-2026-10-27/case_registry.json')['cases']
    def tokens(text):
        import hashlib
        path = ROOT / cache_directory / (hashlib.sha256(text.encode()).hexdigest() + '.npz')
        with np.load(path, allow_pickle=False) as archive:
            return archive['vectors'].astype(np.float32)
    ranker = TokenInteractionRanker({case: tokens(value['task']) for case, value in cases.items()})
    questions = {row['query_id']: row['text'] for row in map(json.loads, (ROOT / questions_path).read_text(encoding='utf-8').splitlines())}
    original = defaultdict(dict)
    for row in read(prefix + 'original/predictions/evidence.json')['records']:
        original[row['query_id']][row['case_id']] = row['dense']
    branches = defaultdict(dict)
    with (ROOT / prefix / 'inference/branch_scores.jsonl').open(encoding='utf-8') as source_file:
        for line in source_file:
            row = json.loads(line)
            if row['path_id'].startswith('E_'):
                branches[row['path_id']][row['case_id']] = row['dense']
    cls = {}
    for path in [ROOT / 'docs/query-case-semantic-mapping-2026-10-28/mapping/embeddings.npz', original_cache, ROOT / prefix / 'inference/branch_vectors.npz']:
        with np.load(path, allow_pickle=False) as archive:
            cls.update(zip(archive['texts'].tolist(), archive['vectors']))
    grouped = defaultdict(list)
    for row in read(prefix + 'inference/paths.json')['paths']:
        if row['query_id'].startswith('E_'):
            grouped[row['parent_query_id'], row['repeat'] - 6].append(row)
    expected = {(row['query_id'], row['repeat']): row['ranking'] for row in artifact['rankings'] if row['system'] == 'token_hybrid_multi'}
    for (query, repeat), paths in grouped.items():
        evidence = {row['query_id']: {'tokens': tokens(row['text']), 'dense_scores': branches[row['query_id']],
                                      'query_cosine': float(cls[questions[query]] @ cls[row['text']])} for row in paths}
        result = ranker.rank(tokens(questions[query]), original[query], evidence)
        assert result['ranking'] == expected[query, repeat], (query, repeat)
    return len(grouped)


def main():
    torch.set_num_threads(4)
    new = verify('docs/improvement-cycle10-20261108-results.json', '.work-new20-runtime/',
                 'docs/validation-new20-20261107/questions.jsonl', '.work-cycle10-token-cache',
                 ROOT / 'validation20-scratch/original/new_query_vectors.npz')
    old = verify('docs/improvement-cycle11-20261108-results.json', BASE, BASE + 'questions.jsonl',
                 '.work-cycle11-token-cache', ORIGINAL_CACHE)
    assert new == 60 and old == 24
    result = {'state': 'REUSABLE_RANKER_REPRODUCES_ALL84_QUERY_REPEAT_RANKINGS', 'new20': new, 'CPD8': old,
              'qrels_read': False, 'paid_calls': 0, 'test_access': False,
              'module_sha256': digest(ROOT / 'src/ax_research/token_interaction.py')}
    with (ROOT / 'docs/reusable-token-ranker-verification.json').open('x', encoding='utf-8') as target:
        target.write(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
