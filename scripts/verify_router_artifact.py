"""Re-fit frozen router folds and verify label exclusion and selected rankings."""
import hashlib
import json
from collections import defaultdict

import numpy as np

from scripts.improvement_cycle import ROOT, read
from scripts.improvement_cycle2 import evaluate, label_sets
from scripts.improvement_cycle11 import BASE
from scripts.improvement_cycle12 import route


def main():
    artifact = read('docs/improvement-cycle12-20261108-results.json')
    for path, checksum in artifact['input_sha256'].items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == checksum, path
    versions = label_sets()
    cpd = defaultdict(dict)
    for row in read(BASE + 'labels.json')['records']:
        cpd[row['query_id']][row['case_id']] = row['grade']
    primary = {**versions['working_transfer'], **cpd}
    ranks = {(row['query_id'], row['repeat'], row['system']): row['ranking'] for row in artifact['rankings']}
    total = 0
    for system, audit_key, decisions_key in [('Router', 'training_audit', 'decisions'),
                                             ('CollectionHeldoutRouter', 'collection_heldout_audit', 'collection_heldout_decisions')]:
        recovered = {}
        for audit in artifact[audit_key]:
            decisions, current = route(artifact['features'], audit['training_queries'], audit['heldout_queries'], primary, ranks)
            assert current['targets'] == audit['targets']
            assert not set(audit['scaler_training_queries']) & set(audit['heldout_queries'])
            assert set(audit['targets']) <= set(audit['training_queries'])
            for query, decision in decisions.items():
                assert query not in recovered
                expected = artifact[decisions_key][query]
                assert decision['method'] == expected['method']
                np.testing.assert_allclose(decision['probability_E'], expected['probability_E'], atol=1e-12)
                for repeat in (1, 2, 3):
                    assert ranks[query, repeat, system] == ranks[query, repeat, decision['method']]
                recovered[query] = decision
        assert len(recovered) == 28
        total += len(recovered)
    for name, grades in versions.items():
        result = evaluate([row for row in artifact['rankings'] if row['query_id'] in grades], grades)
        assert result == artifact['results'][name]
    complete = {query: grades for query, grades in cpd.items() if all(value is not None for value in grades.values())}
    assert evaluate([row for row in artifact['rankings'] if row['query_id'] in complete], complete) == artifact['results']['CPD_complete6']
    result = {'state': 'ALL_ROUTER_FOLDS_DECISIONS_AND_METRICS_REPRODUCED', 'decisions': total,
              'router_rankings': total * 3, 'heldout_labels_excluded_from_training': True,
              'source_identity_excluded_from_features': True, 'paid_calls': 0, 'test_access': False,
              'router_promoted': False}
    with (ROOT / 'docs/improvement-cycle12-20261108-verification.json').open('x', encoding='utf-8') as target:
        target.write(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
