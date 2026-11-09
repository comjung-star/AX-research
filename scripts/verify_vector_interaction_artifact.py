"""Reload all saved cycle9 models and verify heldout predictions and provenance."""
import hashlib
import json

import numpy as np
import torch

from scripts.improvement_cycle import ROOT, read
from scripts.improvement_cycle9 import VectorInteraction, load_vectors


def main():
    torch.set_num_threads(2)
    artifact = read('docs/improvement-cycle9-20261108-results.json')
    for path, expected in artifact['input_sha256'].items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected, path
    ids = artifact['case_order']
    queries = sorted({query for row in artifact['training_audit'] for query in row['heldout_queries']})
    assert len(queries) == 20
    vectors, cases = load_vectors(ids, queries)
    records = {(row['query_id'], row['system']): row for row in artifact['score_evidence']}
    assert len(records) == 40
    verified = set()
    for row in artifact['training_audit']:
        assert not set(row['training_queries']) & set(row['heldout_queries'])
        assert set(row['pair_counts']) <= set(row['training_queries'])
        name = f"{row['system']}_fold{row['fold']}.pt"
        path = ROOT / 'docs/improvement-cycle9-20261108-models' / name
        assert hashlib.sha256(path.read_bytes()).hexdigest() == artifact['model_sha256'][name]
        model = VectorInteraction()
        model.load_state_dict(torch.load(path, map_location='cpu', weights_only=True))
        model.eval()
        with torch.no_grad():
            for query in row['heldout_queries']:
                key = (query, row['system'])
                assert key not in verified
                scores, branches, views = model(vectors[query][:1 if row['system'] == 'vector_single' else 4], cases)
                record = records[key]
                for actual, expected in [(scores, record['scores']), (branches, record['branch_scores']), (views, record['case_view_scores'])]:
                    np.testing.assert_allclose(actual.numpy(), expected, atol=1e-7, rtol=1e-6)
                ranking = [ids[position] for position in sorted(range(112), key=lambda position: (-float(scores[position]), ids[position]))]
                saved = [prediction['ranking'] for prediction in artifact['rankings']
                         if prediction['query_id'] == query and prediction['system'] == row['system']]
                assert len(saved) == 3 and all(value == ranking for value in saved)
                verified.add(key)
    assert len(verified) == 40
    result = {'state': 'ALL40_HELDOUT_MODEL_OUTPUTS_RELOADED_AND_REPRODUCED', 'models': 10,
              'queries': 20, 'systems': 2, 'raw_rankings_including_repeat_copies': 120,
              'model_and_input_hashes_verified': True, 'qrels_read_during_reload': False,
              'test_access': False, 'paid_calls': 0}
    destination = ROOT / 'docs/improvement-cycle9-20261108-verification.json'
    with destination.open('x', encoding='utf-8') as target:
        target.write(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
