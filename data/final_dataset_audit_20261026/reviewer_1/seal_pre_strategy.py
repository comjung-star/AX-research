import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
AUDIT = HERE.parent
ITEMS = [('relevance_pass_1.csv', 3510, 'dev_seal.json'), ('test_relevance_pass_1.csv', 3510, 'test_seal.json'), ('factor_pass_1.csv', 117, 'factor_seal.json'), ('reviewer_1/dev_adjudication_proposals.csv', 513, None), ('reviewer_1/test_adjudication_proposals.csv', 262, None)]
report = {'stage': 'ALL_OWNED_BLIND_AND_ADJUDICATION_STAGES_SEALED_BEFORE_STRATEGY_EXPOSURE', 'artifacts': {}}
for name, expected, seal_name in ITEMS:
    path = AUDIT / name
    raw_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    with path.open(encoding='utf-8', newline='') as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == expected and all(r['rationale'].strip() for r in rows)
    if 'relevance_0_4' in rows[0]:
        assert all(r['relevance_0_4'] in {'0', '1', '2', '3', '4'} for r in rows)
        assert len({(r['query_id'], r['perspective_id'], r['case_id']) for r in rows}) == expected
    else:
        assert len({r['case_id'] for r in rows}) == expected
    if seal_name:
        assert raw_hash == json.loads((HERE / seal_name).read_text(encoding='utf-8'))['output_raw_sha256']
    entry = {'rows': len(rows), 'raw_output_sha256': raw_hash, 'input_sha256_values': sorted({r['input_sha256'] for r in rows})}
    if 'relevance_0_4' in rows[0]:
        entry['score_histogram'] = dict(sorted(Counter(int(r['relevance_0_4']) for r in rows).items()))
    else:
        entry['decisions'] = dict(Counter(r['decision'] for r in rows))
    report['artifacts'][name] = entry
(HERE / 'pre_strategy_seal.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(report, ensure_ascii=False, indent=2))
