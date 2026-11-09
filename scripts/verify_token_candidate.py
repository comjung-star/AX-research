"""Recompute every cycle10 candidate rank from sealed local token outputs."""
import hashlib
import json
from collections import defaultdict

import numpy as np
import torch

from scripts.improvement_cycle import ROOT, read
from scripts.improvement_cycle10 import CACHE, token_path, token_scores
from scripts.improvement_cycle3 import normalize_scores
from scripts.improvement_cycle6 import fidelity_weights
from scripts.improvement_cycle2 import evaluate, label_sets


def main():
    torch.set_num_threads(4)
    result = read('docs/improvement-cycle10-20261108-results.json')
    assert hashlib.sha256((ROOT / 'scripts/improvement_cycle10.py').read_bytes()).hexdigest() == result['script_sha256']
    assert hashlib.sha256((ROOT / 'docs/improvement-cycle10-20261108-protocol.md').read_bytes()).hexdigest() == result['protocol_sha256']
    cases = read('docs/dense-bm25-candidates-2026-10-27/case_registry.json')['cases']
    ids = sorted(cases)
    questions = {row['query_id']: row['text'] for row in map(json.loads, (ROOT / 'docs/validation-new20-20261107/questions.jsonl').read_text(encoding='utf-8').splitlines())}
    paths = [row for row in read('.work-new20-runtime/inference/paths.json')['paths'] if row['query_id'].startswith('E_')]
    texts = set(questions.values()) | {row['text'] for row in paths} | {case['task'] for case in cases.values()}
    assert sorted(hashlib.sha256(text.encode()).hexdigest() for text in texts) == result['cache_manifest']['input_text_sha256']
    vectors, cache_hashes = {}, {}
    for text in texts:
        path = token_path(text)
        cache_hashes[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
        with np.load(path, allow_pickle=False) as archive:
            vectors[text] = torch.tensor(archive['vectors'].astype(np.float32))
    assert len(cache_hashes) == 310
    center = torch.cat([vectors[cases[case]['task']] for case in ids]).mean(dim=0)
    raw = {text: torch.nn.functional.normalize(value, dim=1) for text, value in vectors.items()}
    centered = {text: torch.nn.functional.normalize(value - center, dim=1) for text, value in vectors.items()}
    centered_cases = [centered[cases[case]['task']] for case in ids]
    originals = {(row['query_id'], row['case_id']): row['dense'] for row in read('.work-new20-runtime/original/predictions/evidence.json')['records']}
    branches = {}
    with (ROOT / '.work-new20-runtime/inference/branch_scores.jsonl').open(encoding='utf-8') as source:
        for line in source:
            row = json.loads(line)
            if row['path_id'].startswith('E_'):
                branches[row['path_id'], row['case_id']] = row['dense']
    hybrid, recovered = {}, []
    evidence = {row['query_id']: row for row in result['score_evidence']}
    for query, text in list(questions.items()) + [(row['query_id'], row['text']) for row in paths]:
        scores = token_scores(centered[text], centered_cases)
        dense = [originals[query, case] if query in questions else branches[query, case] for case in ids]
        hybrid[query] = np.mean([normalize_scores(dense), normalize_scores(scores)], axis=0)
        np.testing.assert_allclose(scores, evidence[query]['centered_maxsim'], atol=1e-7)
        np.testing.assert_allclose(hybrid[query], evidence[query]['hybrid'], atol=1e-7)
        if query in questions:
            raw_scores = token_scores(raw[text], [raw[cases[case]['task']] for case in ids])
            for name, values in [('raw_token_single', raw_scores), ('centered_token_single', scores), ('token_hybrid_single', hybrid[query])]:
                ranking = [ids[position] for position in sorted(range(112), key=lambda position: (-values[position], ids[position]))]
                recovered.extend({'query_id': query, 'repeat': repeat, 'system': name, 'ranking': ranking} for repeat in (1, 2, 3))
    cls = {}
    for path in ['docs/query-case-semantic-mapping-2026-10-28/mapping/embeddings.npz', 'validation20-scratch/original/new_query_vectors.npz', '.work-new20-runtime/inference/branch_vectors.npz']:
        with np.load(ROOT / path, allow_pickle=False) as archive:
            cls.update(zip(archive['texts'].tolist(), archive['vectors']))
    groups = defaultdict(list)
    for row in paths:
        groups[row['parent_query_id'], row['repeat'] - 6].append(row)
    for (query, repeat), local in groups.items():
        weights = fidelity_weights([float(cls[questions[query]] @ cls[row['text']]) for row in local])
        scores = .5 * hybrid[query] + .5 * sum(weight * hybrid[row['query_id']] for weight, row in zip(weights, local))
        ranking = [ids[position] for position in sorted(range(112), key=lambda position: (-scores[position], ids[position]))]
        recovered.append({'query_id': query, 'repeat': repeat, 'system': 'token_hybrid_multi', 'ranking': ranking})
    saved = {(row['query_id'], row['repeat'], row['system']): row['ranking'] for row in result['rankings']}
    assert len(recovered) == 240
    for row in recovered:
        assert row['ranking'] == saved[row['query_id'], row['repeat'], row['system']]
    baselines = [row for row in result['rankings'] if row['system'] in ('E', 'Dense')]
    for label, grades in label_sets().items():
        recomputed = evaluate(baselines + recovered, grades)
        assert recomputed == result['results'][label]
    verification = {'state': 'ALL240_CANDIDATE_RANKINGS_AND_ALL3_LABEL_METRICS_REPRODUCED',
                    'local_cache_texts': len(cache_hashes), 'cache_sha256': cache_hashes,
                    'score_evidence_groups': len(evidence), 'qrels_loaded_only_for_metric_recalculation': True,
                    'paid_calls': 0, 'test_access': False, 'statistically_confirmed_gain': False}
    with (ROOT / 'docs/improvement-cycle10-20261108-verification.json').open('x', encoding='utf-8') as target:
        target.write(json.dumps(verification, indent=2) + '\n')
    print(json.dumps({key: value for key, value in verification.items() if key != 'cache_sha256'}))


if __name__ == '__main__':
    main()
