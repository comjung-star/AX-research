"""Offline replay of frozen candidate predictions; no labels or model calls."""
import hashlib
import json
from pathlib import Path

from ax_research.dense_preservation import preserve_dense_candidates


def main():
    root = Path(__file__).resolve().parents[1]
    path = root / 'docs/dense-preserved-candidates-20261108-predictions.json'
    saved = json.loads(path.read_text(encoding='utf-8'))
    for name, digest in saved['source_sha256'].items():
        assert hashlib.sha256((root / name).read_bytes()).hexdigest() == digest, name
    rankings = {(r['query_id'], r['repeat'], r['system']): r['ranking'] for r in saved['rankings']}
    for trace in saved['traces']:
        query, repeat, system = trace['query_id'], trace['repeat'], trace['system']
        data = saved['inputs'][query]
        sources = {'QueryTokenCandidates': {'OriginalToken': data['query_token_order']},
                   'QuerySparseCandidates': {'OriginalSparse': data['sparse_order']},
                   'PerspectiveCandidates': data['branches'][str(repeat)]}
        replay = preserve_dense_candidates(data['dense'], data['token'], data['core'], sources[system])
        assert all(replay[key] == trace[key] for key in replay), (query, repeat, system)
        assert replay['ranking'] == rankings[query, repeat, system]
        assert replay['ranking'][:10] == rankings[query, repeat, 'Dense'][:10]
        assert len(set(replay['candidates'])) == 20
        assert set(replay['ranking']) == set(data['dense']) and len(replay['ranking']) == 112
        assert all(row['path_rank'] <= 20 for row in replay['candidate_admissions'])
    snapshots = {}
    for artifact, snapshot in [('dense-preserved-20261108-predictions.json', 'dense_preservation_v1.py'),
                               ('dense-preserved-core-20261108-predictions.json', 'dense_preservation_v2.py')]:
        manifest = json.loads((root / 'docs' / artifact).read_text(encoding='utf-8'))
        snapshots[snapshot] = hashlib.sha256((root / 'src/ax_research' / snapshot).read_bytes()).hexdigest() == manifest['source_sha256']['src/ax_research/dense_preservation.py']
        assert snapshots[snapshot]
    evaluation = json.loads((root / 'docs/dense-preserved-candidates-20261108-evaluation.json').read_text(encoding='utf-8'))
    assert evaluation['prediction_sha256'] == hashlib.sha256(path.read_bytes()).hexdigest()
    result = {'state': 'PASS', 'traces_reproduced': len(saved['traces']), 'source_hashes_match': True,
              'historical_source_snapshots_match': snapshots, 'dense_top10_preserved': True,
              'candidate_budget': 20, 'source_depth': 20, 'paid_calls': 0,
              'new40_read': False, 'qrels_read': False}
    destination = root / 'docs/dense-preserved-candidates-20261108-verification.json'
    destination.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
