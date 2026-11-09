"""Reused forty-query pilot, fixed five-model score mean, no training or paid calls."""
import argparse
from collections import defaultdict
import hashlib
import json
import os
from statistics import mean

import numpy as np

from ax_research.dense_preservation import preserve_dense_candidates
from ax_research.frozen_ensemble import mean_fold_scores
from ax_research.literal_action_recovery import recover_action_profile
from ax_research.pairwise_ridge import rank_pool, unit
from ax_research.retrieval.bm25 import BM25Retriever
from ax_research.task_alignment import cosine, partition_request, replace_core
from ax_research.token_interaction import TokenInteractionRanker
from scripts.improvement_cycle import ROOT, read
from scripts.task_alignment_20261109 import MODEL, sha
from scripts.autonomous_trial2_mapping_replay import interval, metrics

OUT = ROOT / 'docs/transfer40-work-aligned-20261109'
PILOT = ROOT / 'docs/independent-validation-20261108/ai_pilot'
REFERENCE = ROOT / 'docs/task-alignment-reference-20261109'
POOLS = ('DensePool', 'TokenPool', 'SparsePool', 'PerspectivePool')


def write(name, data):
    with (OUT / name).open('x', encoding='utf-8') as target:
        target.write(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def build_features(ids, dense, token, sparse, profile, partition, cases, bank):
    a = [cosine(profile['fields']['action'], cases[c]['fields']['action'], bank) for c in ids]
    o = [cosine(profile['fields']['object'], cases[c]['fields']['object'], bank) for c in ids]
    task = [cosine(profile['fields']['task'], cases[c]['fields']['task'], bank) or 0. for c in ids]
    base = np.zeros((len(ids), 10))
    for column, values in enumerate((dense, token, sparse)):
        base[:, column] = unit([values[c] for c in ids])
    work = replace_core(base, a, o, task)
    excluded = [cosine(partition['excluded_text'], cases[c]['fields']['task'], bank) or 0. for c in ids]
    proxy = [cosine(partition['output_hint_text'], cases[c]['fields']['task'], bank) or 0. for c in ids]
    output = [cosine(partition['output_hint_text'], cases[c]['fields']['output'], bank) for c in ids]
    features = np.column_stack([work, unit(excluded), unit(proxy), unit([v or 0. for v in output]), [float(v is not None) for v in output]])
    return features


def infer():
    if OUT.exists():
        raise FileExistsError('Transfer output already exists')
    config = json.loads((REFERENCE / 'config.json').read_text(encoding='utf-8'))
    manifest = json.loads((REFERENCE / 'manifest.json').read_text(encoding='utf-8'))
    assert all(sha(ROOT / p) == item['sha256'] for p, item in manifest['snapshot_files'].items())
    assert sha(REFERENCE / 'snapshot.zip') == manifest['archive_sha256']
    OUT.mkdir()
    accesses = []
    import sys
    def audit(event, args):
        if event == 'open' and isinstance(args[0], (str, bytes)):
            value = str(args[0]).replace('\\', '/').lower()
            if any(piece in value for piece in ('blind_review', 'ai_consensus.json', 'labels_new20', 'qrels', '.ax-heldout', 'heldout-final-resume')) or value.endswith('/ai_pilot/evaluation.json'):
                raise RuntimeError('Relevance or final test read forbidden during transfer inference')
            if value.endswith(('.json', '.jsonl', '.npz')):
                accesses.append(str(args[0]))
    sys.addaudithook(audit)
    import socket
    def blocked(*args, **kwargs):
        raise RuntimeError('Offline transfer only')
    socket.socket.connect = blocked
    socket.create_connection = blocked
    import torch
    torch.set_num_threads(4)
    rows = [json.loads(s) for s in (PILOT / 'questions.jsonl').read_text(encoding='utf-8').splitlines()]
    questions = {r['query_id']: r['text'] for r in rows}
    registry = read('docs/dense-bm25-candidates-2026-10-27/case_registry.json')['cases']
    ids = sorted(registry)
    cases = read('docs/literal-action-recovery-20261109/case_profiles.json')
    cfg, guard = read('configs/semantic_mapping_20261028.json'), read('configs/functional_mapping_20261028.json')['negation_guard']
    recovery = read('configs/literal_action_recovery_20261109.json')
    partitions = {q: partition_request(text) for q, text in questions.items()}
    profiles = {q: recover_action_profile(part['requested_text'], cfg, guard, recovery) for q, part in partitions.items()}
    texts = {value for p in list(cases.values()) + list(profiles.values()) for value in p['fields'].values() if value}
    texts |= {p[field] for p in partitions.values() for field in ('excluded_text', 'output_hint_text') if p[field]}
    banks = ['docs/query-case-semantic-mapping-2026-10-28/mapping/embeddings.npz', '.work-ai-pilot-inference/new_query_vectors.npz', 'docs/task-alignment-20261109-vectors.npz']
    bank = {}
    for path in banks:
        with np.load(ROOT / path, allow_pickle=False) as z:
            for text, vector in zip(z['texts'].tolist(), z['vectors']):
                bank.setdefault(text, vector)
    missing = sorted(texts - set(bank))
    assert all(sha(MODEL / p) == value for p, value in config['model_sha256'].items())
    print('LOCAL_ENCODING', len(missing), 'new strings', flush=True)
    if missing:
        for key in ('HF_HUB_OFFLINE', 'TRANSFORMERS_OFFLINE', 'HF_HUB_DISABLE_TELEMETRY'):
            os.environ[key] = '1'
        from sentence_transformers import SentenceTransformer
        torch.manual_seed(20261028)
        torch.use_deterministic_algorithms(True)
        encoder = SentenceTransformer(str(MODEL), device='cpu', local_files_only=True)
        encoder.max_seq_length = 4096
        assert max(len(encoder.tokenizer.encode(t)) for t in missing) <= 4096
        vectors = encoder.encode(missing, batch_size=8, normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False)
        bank.update(zip(missing, vectors.astype(np.float32)))
        del encoder
    selected = sorted(texts)
    saved_vectors = np.array([bank[t] for t in selected], dtype=np.float32)
    assert saved_vectors.shape == (len(selected), 1024) and np.isfinite(saved_vectors).all()
    assert np.allclose(np.linalg.norm(saved_vectors, axis=1), 1, atol=1e-5)
    np.savez_compressed(OUT / 'vectors.npz', texts=np.array(selected), vectors=saved_vectors)
    print('READING_CACHED_EVIDENCE', flush=True)
    evidence = read('.work-ai-pilot-inference/evidence.json')
    dense, core = defaultdict(dict), defaultdict(dict)
    for row in evidence['records']:
        q, c = row['query_id'], row['case_id']
        dense[q][c] = row['dense']
        if q in questions:
            parts = row['semantic']['components']
            core[q][c] = {f: parts.get(f, {}).get('cosine') for f in ('action', 'object')}
    del evidence
    cache = ROOT / '.work-ai-pilot-token-cache'
    token_hashes = {}
    def tokens(text):
        path = cache / (hashlib.sha256(text.encode('utf-8')).hexdigest() + '.npz')
        token_hashes[path.relative_to(ROOT).as_posix()] = sha(path)
        with np.load(path, allow_pickle=False) as z:
            return z['vectors'].astype(np.float32)
    matcher = TokenInteractionRanker({c: tokens(registry[c]['task']) for c in ids})
    sparse = BM25Retriever({c: '\n'.join(registry[c][f] for f in ('problem', 'task', 'context')) for c in ids})
    historical = json.loads((PILOT / 'predictions.json').read_text(encoding='utf-8'))
    predictions = [r for r in historical['rankings'] if r['system'] == 'E']
    inputs, traces, slot_counts, runtime_hashes = {}, [], [], {}
    for q, text in sorted(questions.items()):
        raw_token = matcher.token_scores(tokens(text))
        token = dict(zip(ids, map(float, raw_token)))
        sparse_map = {r.case_id: r.score for r in sparse.search(text)}
        dense_order = sorted(ids, key=lambda c: (-dense[q][c], c))
        token_hybrid = .5 * unit([dense[q][c] for c in ids]) + .5 * unit(raw_token)
        hybrid_map = dict(zip(ids, map(float, token_hybrid)))
        token_order = sorted(ids, key=lambda c: (-hybrid_map[c], c))
        sparse_order = sorted(ids, key=lambda c: (-sparse_map[c], c))
        features = build_features(ids, dense[q], token, sparse_map, profiles[q], partitions[q], cases, bank)
        scores = mean_fold_scores(features, config['fold_models'])
        inputs[q] = {'features': features.tolist(), 'scores': scores.tolist(), 'dense': dense[q], 'token': token,
                     'sparse': sparse_map, 'core': core[q], 'dense_order': dense_order, 'token_order': token_order,
                     'sparse_order': sparse_order, 'branches': {}, 'pools': {}}
        for repeat in (1, 2, 3):
            path = PILOT / 'runtime/api/results' / f'E_{q}_r{repeat}.json'
            runtime_hashes[path.relative_to(ROOT).as_posix()] = sha(path)
            views = json.loads(path.read_text(encoding='utf-8'))['data']['perspectives']
            branches = {}
            for index, view in enumerate(views, 1):
                slot_counts.append({'query_id': q, 'repeat': repeat, 'slot': index, 'status': view['status']})
                if view['status'] == 'MISSING':
                    continue
                key = f'E_{q}_r{repeat}_{index}'
                assert len(dense[key]) == 112
                branches[key] = sorted(ids, key=lambda c: (-dense[key][c], c))
            inputs[q]['branches'][str(repeat)] = branches
            inputs[q]['pools'][str(repeat)] = {'DensePool': dense_order[:20]}
            predictions.extend([{'query_id': q, 'repeat': repeat, 'system': 'Dense', 'ranking': dense_order},
                                {'query_id': q, 'repeat': repeat, 'system': 'BM25', 'ranking': sparse_order}])
            sources = {'TokenPool': {'OriginalToken': token_order}, 'SparsePool': {'OriginalSparse': sparse_order}, 'PerspectivePool': branches}
            for pool, source in sources.items():
                result = preserve_dense_candidates(dense[q], token, core[q], source)
                inputs[q]['pools'][str(repeat)][pool] = result['candidates']
                traces.append({'query_id': q, 'repeat': repeat, 'pool': pool, **result})
            for pool, candidates in inputs[q]['pools'][str(repeat)].items():
                predictions.append({'query_id': q, 'repeat': repeat, 'system': 'Aligned_' + pool,
                                    'ranking': rank_pool(ids, scores, candidates, dense_order)})
    assert len(predictions) == 840
    sources = ['docs/transfer40-work-aligned-20261109-protocol.md', 'scripts/transfer40_work_aligned_20261109.py',
               'src/ax_research/frozen_ensemble.py', 'src/ax_research/dense_preservation.py',
               'src/ax_research/token_interaction.py', 'src/ax_research/task_alignment.py',
               'src/ax_research/literal_action_recovery.py', 'src/ax_research/pairwise_ridge.py',
               'src/ax_research/semantic_mapping.py', 'src/ax_research/retrieval/bm25.py',
               'docs/literal-action-recovery-20261109/case_profiles.json', 'configs/literal_action_recovery_20261109.json',
               'configs/semantic_mapping_20261028.json', 'configs/functional_mapping_20261028.json',
               'docs/task-alignment-reference-20261109/config.json', 'docs/task-alignment-reference-20261109/manifest.json',
               'docs/independent-validation-20261108/ai_pilot/questions.jsonl',
               'docs/independent-validation-20261108/ai_pilot/predictions.json',
               'docs/dense-bm25-candidates-2026-10-27/case_registry.json', '.work-ai-pilot-inference/evidence.json'] + banks
    write('inputs.json', {'ids': ids, 'inputs': inputs, 'traces': traces, 'profiles': profiles, 'partitions': partitions,
        'runtime_slots': slot_counts, 'newly_encoded_strings': len(missing), 'source_sha256': {p: sha(ROOT / p) for p in sources},
        'token_cache_sha256': token_hashes, 'runtime_sha256': runtime_hashes, 'vectors_sha256': sha(OUT / 'vectors.npz'),
        'model_sha256': config['model_sha256'], 'paid_calls': 0, 'new_training': False, 'review_labels_read': False})
    write('predictions.json', {'state': 'FROZEN_FIVE_MODEL_MEAN_REUSED40', 'rankings': predictions,
        'input_sha256': sha(OUT / 'inputs.json'), 'paid_calls': 0, 'new_training': False, 'review_labels_read': False,
        'test15_read': False, 'accesses': sorted(set(accesses))})
    print('SEALED', len(predictions), 'rankings', flush=True)


def assess(rankings, grades):
    from scripts.improvement_cycle2 import evaluate
    result = evaluate(rankings, grades)
    contrasts = {}
    for baseline in ('Dense', 'BM25', 'Aligned_DensePool', 'Aligned_TokenPool', 'Aligned_SparsePool'):
        contrasts[baseline] = {}
        for metric in ('F1@5', 'nDCG@10', 'Recall@20'):
            differences = [r['Aligned_PerspectivePool'][metric] - r[baseline][metric] for r in result['per_query'].values() if r[baseline][metric] is not None]
            contrasts[baseline][metric] = {'delta': mean(differences), 'interval95': interval(differences),
                'queries_improved': sum(v > 1e-12 for v in differences), 'queries_harmed': sum(v < -1e-12 for v in differences)}
    result['perspective_contrasts'] = contrasts
    return result


def evaluate():
    from scripts.ai_pilot_evaluate import assemble_votes
    prediction = json.loads((OUT / 'predictions.json').read_text(encoding='utf-8'))
    assert prediction['input_sha256'] == sha(OUT / 'inputs.json')
    votes, consensus = assemble_votes()
    labels = {}
    for provider, records in votes.items():
        labels[provider] = defaultdict(dict)
        for (q, c), row in records.items():
            assert row['status'] == 'JUDGED' and row['grade'] is not None
            labels[provider][q][c] = row['grade']
        assert len(labels[provider]) == 40 and all(len(v) == 112 for v in labels[provider].values())
    positive = {p: {q for q, g in labels[p].items() if any(v >= 2 for v in g.values())} for p in labels}
    common = sorted(set.intersection(*positive.values()))
    results, common_results, accounting = {}, {}, {}
    rankings = prediction['rankings']
    lookup = {(r['query_id'], r['repeat'], r['system']): r['ranking'] for r in rankings}
    for provider, grades in labels.items():
        result = assess(rankings, grades)
        results[provider] = result
        common_grades = {q: grades[q] for q in common}
        common_results[provider] = assess([r for r in rankings if r['query_id'] in common], common_grades)
        rows = []
        for q, g in grades.items():
            pos = {c for c, value in g.items() if value >= 2}
            for repeat in (1, 2, 3):
                sets = {name: set(lookup[q, repeat, 'Aligned_' + name][:20]) for name in POOLS}
                rows.append({'query_id': q, 'repeat': repeat,
                    'new_positive_vs_dense_pool': sorted((sets['PerspectivePool'] - sets['DensePool']) & pos),
                    'lost_positive_vs_dense_pool': sorted((sets['DensePool'] - sets['PerspectivePool']) & pos),
                    'new_positive_absent_both_token_sparse': sorted((sets['PerspectivePool'] - sets['TokenPool'] - sets['SparsePool']) & pos)})
        accounting[provider] = {'rows': rows, 'unique_query_case_counts': {
            name: len({(r['query_id'], c) for r in rows for c in r[name]}) for name in
            ('new_positive_vs_dense_pool', 'lost_positive_vs_dense_pool', 'new_positive_absent_both_token_sparse')}}
        print(provider, {s: {m: round(v[m]['mean'], 6) for m in ('F1@5', 'nDCG@10', 'Recall@20')} for s, v in result['summary'].items()}, flush=True)
    judged = sum(r['grade'] is not None for r in consensus)
    label_paths = sorted(list((PILOT / 'blind_review_v2').glob('*_validated.json')) + list((PILOT / 'blind_review_429_recovery').glob('*_validated.json')))
    write('evaluation.json', {'state': 'STEPS_3_AND4_REUSED40_COMPLETE', 'results': results, 'common_positive_queries': common,
        'common_results': common_results, 'candidate_accounting': accounting,
        'positive_query_counts': {p: len(qs) for p, qs in positive.items()},
        'consensus_judged_pairs': judged, 'consensus_abstain_pairs': len(consensus) - judged,
        'prediction_sha256': sha(OUT / 'predictions.json'), 'label_sha256': {p.relative_to(ROOT).as_posix(): sha(p) for p in label_paths},
        'paid_calls': 0, 'new_training': False, 'labels_changed': False, 'human_gold': False,
        'independent_final_test': False, 'test15_read': False,
        'limits': ['Previously inspected 40 AI-authored queries; reuse confirmation only',
                   'Provider-positive cohorts differ; use matched common cohort too',
                   'Two AI providers are not human truth; partial agreement not full Gold',
                   'Fixed ensemble policy, no new fitting; not the prior OOF single-model estimand',
                   'Bootstrap not adjusted for development selection or multiplicity']})
    print('EVALUATED matched_positive_queries', len(common), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=['infer', 'evaluate'])
    globals()[parser.parse_args().phase]()
