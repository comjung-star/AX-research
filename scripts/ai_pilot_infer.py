"""Frozen four-system offline pilot inference; no review labels are read."""
import hashlib
import json
import socket
from collections import defaultdict
from fractions import Fraction

import numpy as np
import torch

from ax_research.action_aggregation import compose, purpose_filter
from ax_research.functional_mapping import compare, extract
from ax_research.retrieval.bm25 import KiwiTokenizer
from ax_research.token_interaction import TokenInteractionRanker
from scripts.claude_blind_questions import OUT, save
from scripts.improvement_cycle import ROOT, read
from scripts import improvement_cycle10 as token
from scripts.heldout_run import predict

SCRATCH = ROOT / '.work-ai-pilot-inference'


def historical_tokenize(self, text):
    values = []
    for item in self._kiwi.tokenize(text):
        form = item.form.strip().lower()
        if form and not item.tag.startswith('S'):
            values.append(form)
    return values


def main():
    destination = OUT / 'predictions.json'
    if destination.exists() or SCRATCH.exists():
        raise FileExistsError('Pilot inference already exists; do not overwrite')
    status = read('docs/independent-validation-20261108/ai_pilot/runtime/execution.json')
    assert status['complete_query_repeat_groups'] == 120, 'Incomplete frozen runtime views'
    freeze = read('docs/independent-validation-20261108/source_freeze.json')
    for path, expected in freeze['sha256'].items():
        assert token.digest(ROOT / path) == expected, path
    queries = [json.loads(line) for line in (OUT / 'questions.jsonl').read_text(encoding='utf-8').splitlines()]
    groups, paths, slots = defaultdict(list), [], []
    for query in queries:
        for repeat in (1, 2, 3):
            data = json.loads((OUT / 'runtime/api/results' / f"E_{query['query_id']}_r{repeat}.json").read_text(encoding='utf-8'))['data']
            for position, view in enumerate(data['perspectives'], 1):
                slots.append({'query_id': query['query_id'], 'repeat': repeat, 'slot': position, 'status': view['status']})
                if view['status'] == 'MISSING':
                    continue
                row = {'query_id': f"E_{query['query_id']}_r{repeat}_{position}", 'text': view['title'] + '\n' + view['description'],
                       'parent_query_id': query['query_id'], 'repeat': repeat}
                paths.append(row)
                groups[query['query_id'], repeat].append(row)
    SCRATCH.mkdir()
    accesses = []
    def guard(event, args):
        if event == 'open' and isinstance(args[0], (str, bytes)):
            path = str(args[0]).replace('\\', '/').lower()
            if any(part in path for part in ('blind_review', '/labels', '/qrels', 'heldout-final-resume', '.ax-heldout')):
                raise RuntimeError('Relevance/test input forbidden during offline inference')
            if path.endswith(('.json', '.jsonl', '.npz')):
                accesses.append(str(args[0]))
    import sys
    sys.addaudithook(guard)
    def blocked(*args, **kwargs):
        raise RuntimeError('No network during offline inference')
    socket.socket.connect = blocked
    socket.create_connection = blocked
    original_tokenize = KiwiTokenizer.tokenize
    try:
        KiwiTokenizer.tokenize = historical_tokenize
        raw = predict(queries + paths, token.MODEL, SCRATCH)
    finally:
        KiwiTokenizer.tokenize = original_tokenize
    ids = raw['case_ids']
    evidence = json.loads((SCRATCH / 'evidence.json').read_text(encoding='utf-8'))
    by_pair = {(row['query_id'], row['case_id']): row for row in evidence['records']}
    rules = read('configs/functional_mapping_20261028.json')
    config = read('configs/action_aggregation_20261102.json')
    profiles = read('docs/query-case-functional-mapping-2026-10-28/stage2/case_profiles.json')
    filtered = {case: {role: purpose_filter(value, config) for role, value in parts.items()} for case, parts in profiles.items()}
    query_profiles = {row['query_id']: purpose_filter(extract(row['text'], rules), config) for row in queries + paths}
    cls = {}
    for path in [ROOT / 'docs/query-case-semantic-mapping-2026-10-28/mapping/embeddings.npz', SCRATCH / 'new_query_vectors.npz']:
        with np.load(path, allow_pickle=False) as archive:
            cls.update(zip(archive['texts'].tolist(), archive['vectors']))
    rankings = []
    for query in queries:
        query_id = query['query_id']
        dense = {case: by_pair[query_id, case]['dense'] for case in ids}
        dense_ranking = sorted(ids, key=lambda case: (-dense[case], case))
        for repeat in (1, 2, 3):
            views = groups[query_id, repeat]
            scores, ties = {}, {}
            for case in ids:
                whole = by_pair[query_id, case]
                branch_rules = {view['query_id']: compare(query_profiles[view['query_id']], filtered[case])['mapping_grade'] for view in views}
                branch_semantics = {view['query_id']: by_pair[view['query_id'], case]['semantic']['score'] for view in views}
                scores[case] = compose(compare(query_profiles[query_id], filtered[case])['mapping_grade'], branch_rules,
                                       whole['semantic']['score'], branch_semantics)['score']
                values = []
                for view in views:
                    view_id = view['query_id']
                    dense_order = sorted(ids, key=lambda item: (-by_pair[view_id, item]['dense'], item))
                    sparse_order = sorted(ids, key=lambda item: (-by_pair[view_id, item]['bm25'], item))
                    values.append((Fraction(1, 60 + dense_order.index(case) + 1) + Fraction(1, 60 + sparse_order.index(case) + 1)) / 2)
                ties[case] = sum(values, Fraction()) / len(values) if values else Fraction(str(whole['retrieval_tie']))
            rankings.extend([{'query_id': query_id, 'repeat': repeat, 'system': 'Dense', 'ranking': dense_ranking},
                             {'query_id': query_id, 'repeat': repeat, 'system': 'E', 'ranking': sorted(ids, key=lambda case: (-scores[case], -ties[case], case))}])
    cases = read('docs/dense-bm25-candidates-2026-10-27/case_registry.json')['cases']
    token.CACHE = ROOT / '.work-ai-pilot-token-cache'
    texts = sorted({row['text'] for row in queries + paths} | {case['task'] for case in cases.values()})
    vectors, manifest = token.encode(texts)
    torch.set_num_threads(4)
    ranker = TokenInteractionRanker({case: vectors[cases[case]['task']].numpy() for case in ids})
    for query in queries:
        query_id = query['query_id']
        dense = {case: by_pair[query_id, case]['dense'] for case in ids}
        single = ranker.rank(vectors[query['text']].numpy(), dense)
        for repeat in (1, 2, 3):
            branches = {view['query_id']: {'tokens': vectors[view['text']].numpy(),
                         'dense_scores': {case: by_pair[view['query_id'], case]['dense'] for case in ids},
                         'query_cosine': float(cls[query['text']] @ cls[view['text']])} for view in groups[query_id, repeat]}
            multi = ranker.rank(vectors[query['text']].numpy(), dense, branches)
            rankings.extend([{'query_id': query_id, 'repeat': repeat, 'system': 'TokenSingle', 'ranking': single['ranking']},
                             {'query_id': query_id, 'repeat': repeat, 'system': 'TokenMulti', 'ranking': multi['ranking']}])
    assert len(rankings) == 480
    save(destination, {'state': 'FOUR_FROZEN_SYSTEMS_NEW_AI_PILOT', 'rankings': rankings, 'case_ids': ids,
         'questions': 40, 'repeats': 3, 'runtime_slots': slots, 'token_manifest': manifest,
         'paid_calls_during_inference': 0, 'relevance_inputs_opened': False, 'test15_opened': False,
         'question_sha256': token.digest(OUT / 'questions.jsonl'), 'script_sha256': token.digest(ROOT / 'scripts/ai_pilot_infer.py'),
         'accesses': sorted(set(accesses))})
    print(json.dumps({'state': 'PILOT_PREDICTIONS_SEALED', 'rankings': len(rankings), 'paths': len(paths)}))


if __name__ == '__main__':
    main()
