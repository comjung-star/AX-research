"""Local-only task alignment ablation with nested query validation and stop decision."""
import argparse
import hashlib
import json
import os
from pathlib import Path
from statistics import mean

import numpy as np

from ax_research.literal_action_recovery import recover_action_profile
from ax_research.pairwise_ridge import fit_pairwise, rank_pool, score, unit
from ax_research.task_alignment import cosine, partition_request, replace_core
from scripts.improvement_cycle import ROOT, read
from scripts.autonomous_trial2_mapping_replay import interval, metrics

PREFIX = 'docs/task-alignment-20261109'
MODEL = Path('C:/Users/iovek/OneDrive/문서/ChatGPT/AI공부/AX-prototype/.local/models/bge-m3')
VARIANTS = ('Recovered', 'WorkAligned')
POOLS = ('DensePool', 'TokenPool', 'PerspectivePool')


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def save(suffix, value):
    with (ROOT / (PREFIX + suffix + '.json')).open('x', encoding='utf-8') as target:
        target.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def prepare():
    if (ROOT / (PREFIX + '-inputs.json')).exists():
        raise FileExistsError('Frozen inputs already exist')
    prior = read('docs/ranking-audit-20261109-inputs.json')
    evidence = read('.work-new20-runtime/original/predictions/evidence.json')
    original = read('docs/dense-preserved-candidates-20261108-predictions.json')['inputs']
    cases = read('docs/literal-action-recovery-20261109/case_profiles.json')
    config = read('configs/semantic_mapping_20261028.json')
    guard = read('configs/functional_mapping_20261028.json')['negation_guard']
    recovery = read('configs/literal_action_recovery_20261109.json')
    questions = {r['query_id']: r['text'] for r in map(json.loads, (ROOT / 'docs/validation-new20-20261107/questions.jsonl').read_text(encoding='utf-8').splitlines())}
    partitions = {q: partition_request(text) for q, text in questions.items()}
    active = {q: recover_action_profile(p['requested_text'], config, guard, recovery) for q, p in partitions.items()}
    old_queries = evidence['query_profiles']
    texts = {value for profile in list(cases.values()) + list(old_queries.values()) + list(active.values()) for value in profile['fields'].values() if value}
    texts |= {p[f] for p in partitions.values() for f in ('excluded_text', 'output_hint_text') if p[f]}
    embeddings = {}
    banks = ['docs/query-case-semantic-mapping-2026-10-28/mapping/embeddings.npz', '.work-new20-runtime/inference/branch_vectors.npz']
    for path in banks:
        with np.load(ROOT / path, allow_pickle=False) as archive:
            for text, vector in zip(archive['texts'].tolist(), archive['vectors']):
                embeddings.setdefault(text, vector)
    missing = sorted(texts - set(embeddings))
    model_manifest = read('docs/query-case-semantic-mapping-2026-10-28/preregistration.json')['model_sha256']
    for name, value in model_manifest.items():
        assert sha(MODEL / name) == value, ('Frozen local model differs', name)
    print('LOCAL_ENCODING', len(missing), 'new field strings', flush=True)
    if missing:
        for key in ('HF_HUB_OFFLINE', 'TRANSFORMERS_OFFLINE', 'HF_HUB_DISABLE_TELEMETRY'):
            os.environ[key] = '1'
        import socket
        def blocked(*args, **kwargs):
            raise RuntimeError('Network disabled; local model only')
        socket.socket.connect = blocked
        socket.create_connection = blocked
        import torch
        from sentence_transformers import SentenceTransformer
        torch.set_num_threads(4)
        torch.manual_seed(20261028)
        torch.use_deterministic_algorithms(True)
        encoder = SentenceTransformer(str(MODEL), device='cpu', local_files_only=True)
        encoder.max_seq_length = 4096
        assert max(len(encoder.tokenizer.encode(text)) for text in missing) <= 4096
        vectors = encoder.encode(missing, batch_size=8, normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False)
        embeddings.update(zip(missing, vectors.astype(np.float32)))
        del encoder
    selected = sorted(texts)
    vectors = np.array([embeddings[t] for t in selected], dtype=np.float32)
    assert vectors.shape == (len(selected), 1024) and np.isfinite(vectors).all()
    assert np.allclose(np.linalg.norm(vectors, axis=1), 1, atol=1e-5)
    vector_path = ROOT / (PREFIX + '-vectors.npz')
    if vector_path.exists():
        raise FileExistsError(vector_path)
    np.savez_compressed(vector_path, texts=np.array(selected), vectors=vectors)
    ids, inputs, raw = prior['ids'], {}, {}
    for q, row in prior['inputs'].items():
        baseline = np.array(row['features'])
        original_a = [original[q]['core'][c]['action'] for c in ids]
        original_o = [original[q]['core'][c]['object'] for c in ids]
        recovered_a, recovered_o = [], []
        task_a, task_o, task_t, excluded, output_proxy, explicit_output, output_present = [], [], [], [], [], [], []
        for index, c in enumerate(ids):
            cp, old, qp = cases[c]['fields'], old_queries[q]['fields'], active[q]['fields']
            repaired = cases[c]['action_recovery']['changed']
            recovered_a.append(cosine(old['action'], cp['action'], embeddings) if repaired else original_a[index])
            recovered_o.append(cosine(old['object'], cp['object'], embeddings) if repaired else original_o[index])
            task_a.append(cosine(qp['action'], cp['action'], embeddings))
            task_o.append(cosine(qp['object'], cp['object'], embeddings))
            task_t.append(cosine(qp['task'], cp['task'], embeddings) or 0.)
            excluded.append(cosine(partitions[q]['excluded_text'], cp['task'], embeddings) or 0.)
            output_proxy.append(cosine(partitions[q]['output_hint_text'], cp['task'], embeddings) or 0.)
            output = cosine(partitions[q]['output_hint_text'], cp['output'], embeddings)
            explicit_output.append(output or 0.)
            output_present.append(float(output is not None))
        repaired_matrix = replace_core(baseline, recovered_a, recovered_o)
        work = replace_core(baseline, task_a, task_o, task_t)
        work = np.column_stack([work, unit(excluded), unit(output_proxy), unit(explicit_output), output_present])
        inputs[q] = {**row, 'variants': {'Recovered': repaired_matrix.tolist(), 'WorkAligned': work.tolist()}}
        raw[q] = {'Recovered': {'action': recovered_a, 'object': recovered_o},
                  'WorkAligned': {'action': task_a, 'object': task_o, 'task': task_t,
                                  'excluded_task': excluded, 'output_task_proxy': output_proxy,
                                  'explicit_output': explicit_output, 'output_pair_present': output_present}}
    sources = ['scripts/task_alignment_20261109.py', 'src/ax_research/task_alignment.py',
               'src/ax_research/pairwise_ridge.py', 'src/ax_research/literal_action_recovery.py',
               'docs/task-alignment-20261109-protocol.md', 'docs/ranking-audit-20261109-inputs.json',
               'docs/ranking-audit-20261109-predictions.json',
               'docs/literal-action-recovery-20261109/case_profiles.json',
               '.work-new20-runtime/original/predictions/evidence.json',
               'docs/dense-preserved-candidates-20261108-predictions.json',
               'configs/semantic_mapping_20261028.json', 'configs/functional_mapping_20261028.json',
               'configs/literal_action_recovery_20261109.json',
               'docs/validation-new20-20261107/questions.jsonl'] + banks
    save('-inputs', {'ids': ids, 'inputs': inputs, 'partitions': partitions, 'active_profiles': active,
                     'raw_field_scores': raw, 'outer_folds': prior['outer_folds'],
                     'feature_names': {'Recovered': prior['feature_names'], 'WorkAligned': prior['feature_names'] + ['excluded_task_similarity', 'output_task_proxy', 'explicit_output_similarity', 'output_pair_present']},
                     'model_sha256': model_manifest, 'vectors_sha256': sha(vector_path),
                     'source_sha256': {p: sha(ROOT / p) for p in sources}, 'newly_encoded_texts': len(missing),
                     'paid_calls': 0, 'qrels_read': False, 'new40_read': False, 'test15_read': False})
    print('PREPARED', len(inputs), 'queries', flush=True)


def nested_variant(saved, grades, variant):
    ids, data, folds = saved['ids'], saved['inputs'], saved['outer_folds']
    x = {q: np.array(row['variants'][variant]) for q, row in data.items()}
    y = {q: [grades[q][c] >= 2 for c in ids] for q in data}
    rankings, models = [], []
    for outer in range(5):
        train = sorted(q for q in data if folds[q] != outer)
        test = sorted(q for q in data if folds[q] == outer)
        choices = []
        for reg in (.1, 1., 10.):
            for alpha in (0., .5, 1.):
                validation, splits = [], []
                for inner in sorted(set(folds.values()) - {outer}):
                    fit, val = [q for q in train if folds[q] != inner], [q for q in train if folds[q] == inner]
                    assert not (set(fit) & set(val) or set(test) & (set(fit) | set(val)))
                    weights = fit_pairwise(x, y, fit, reg)
                    for q in val:
                        rank = rank_pool(ids, score(x[q], weights, alpha), data[q]['pools']['1']['DensePool'], data[q]['dense'])
                        validation.append(metrics(rank, grades[q]))
                    splits.append({'training_queries': fit, 'validation_queries': val})
                choices.append({'lambda': reg, 'learned_share': alpha, 'inner_splits': splits,
                                'validation': {m: mean(v[m] for v in validation if v[m] is not None) for m in ('F1@5', 'nDCG@10')}})
        chosen = max(choices, key=lambda c: (c['validation']['F1@5'], c['validation']['nDCG@10'], -c['learned_share'], c['lambda']))
        weights = fit_pairwise(x, y, train, chosen['lambda'])
        models.append({'outer_fold': outer, 'training_queries': train, 'test_queries': test,
                       'choice': chosen, 'choices': choices, 'weights': weights.tolist()})
        for q in test:
            for repeat in (1, 2, 3):
                for pool in POOLS:
                    rank = rank_pool(ids, score(x[q], weights, chosen['learned_share']), data[q]['pools'][str(repeat)][pool], data[q]['dense'])
                    rankings.append({'query_id': q, 'repeat': repeat, 'system': variant + '_' + pool, 'ranking': rank})
    return rankings, models


def infer():
    saved = read(PREFIX + '-inputs.json')
    assert all(sha(ROOT / p) == h for p, h in saved['source_sha256'].items())
    working = read('docs/ax-transfer-relevance-20261108/02_working_transfer_qrels_2240.json')
    grades = {q: {} for q in saved['inputs']}
    for row in working['records']:
        grades[row['query_id']][row['case_id']] = row['grade']
    prior = read('docs/ranking-audit-20261109-predictions.json')
    rankings = [{**r, 'system': r['system'].replace('Learned_', 'Legacy_')} for r in prior['rankings']]
    models = {}
    for variant in VARIANTS:
        generated, models[variant] = nested_variant(saved, grades, variant)
        rankings.extend(generated)
    assert len(rankings) == 660
    save('-predictions', {'rankings': rankings, 'models': models, 'input_sha256': sha(ROOT / (PREFIX + '-inputs.json')),
                         'training_labels_sha256': sha(ROOT / 'docs/ax-transfer-relevance-20261108/02_working_transfer_qrels_2240.json'),
                         'state': 'FROZEN_QUERY_NESTED_DEVELOPMENT_PREDICTIONS', 'paid_calls': 0,
                         'sensitivity_labels_read': False, 'new40_read': False, 'test15_read': False})
    print('FROZEN', len(rankings), 'rankings')


def evaluate():
    from scripts.improvement_cycle2 import evaluate as assess, label_sets
    predictions = read(PREFIX + '-predictions.json')
    assert predictions['input_sha256'] == sha(ROOT / (PREFIX + '-inputs.json'))
    results, decisions = {}, {}
    for version, grades in label_sets().items():
        result = assess(predictions['rankings'], grades)
        result['ablation_comparisons'] = {}
        for method in ('Recovered_PerspectivePool', 'WorkAligned_PerspectivePool'):
            result['ablation_comparisons'][method] = {}
            for baseline in ('Dense', 'Legacy_PerspectivePool', 'Recovered_PerspectivePool', method.split('_')[0] + '_DensePool', method.split('_')[0] + '_TokenPool'):
                result['ablation_comparisons'][method][baseline] = {}
                for metric in ('F1@5', 'nDCG@10'):
                    differences = [r[method][metric] - r[baseline][metric] for r in result['per_query'].values() if r[method][metric] is not None]
                    result['ablation_comparisons'][method][baseline][metric] = {'delta': mean(differences), 'interval95': interval(differences),
                        'queries_improved': sum(v > 1e-12 for v in differences), 'queries_harmed': sum(v < -1e-12 for v in differences)}
        results[version] = result
        print(version, {s: {m: round(v[m]['mean'], 6) for m in ('F1@5', 'nDCG@10')} for s, v in result['summary'].items()}, flush=True)
    for method in ('Recovered_PerspectivePool', 'WorkAligned_PerspectivePool'):
        checks = {version: {'f1_improves': r['ablation_comparisons'][method]['Dense']['F1@5']['delta'] > 0,
                             'ndcg_non_decreasing': r['ablation_comparisons'][method]['Dense']['nDCG@10']['delta'] >= -1e-12} for version, r in results.items()}
        low = results['working_transfer']['ablation_comparisons'][method]['Dense']['F1@5']['interval95'][0]
        decisions[method] = {'decision': 'PROVISIONAL_DEV_ONLY' if all(all(c.values()) for c in checks.values()) and low > 0 else 'DO_NOT_ADOPT',
                             'checks': checks, 'working_f1_ci_lower': low}
    save('-evaluation', {'results': results, 'decisions': decisions,
                         'prediction_sha256': sha(ROOT / (PREFIX + '-predictions.json')),
                         'state': 'STEPS_3_TO_6_COMPLETE', 'paid_calls': 0, 'labels_changed': False,
                         'limits': ['Previously observed development set, not independent test', 'AI Silver labels with partial464 review',
                                    'Same case database shared across folds', 'Bounded linguistic rules and weak output coverage',
                                    'Development bootstrap not selection/multiplicity adjusted']})
    print('DECISIONS', decisions, flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=['prepare', 'infer', 'evaluate'])
    globals()[parser.parse_args().phase]()
