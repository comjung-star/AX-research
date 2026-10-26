import csv
import json
import hashlib
from collections import Counter
from expand import AUDIT, HERE, DOC, FIELDS, JSON_HASH, expand_query, write_csv

rows = [r for n in range(1, 11) for r in expand_query(n)]
keys = {(r['query_id'], r['perspective_id'], r['case_id']) for r in rows}
expected = {(q['query_id'], p['id'], c['case_id']) for q in DOC['queries'] for p in q['reference_perspectives'] for c in DOC['cases']}
assert len(rows) == len(keys) == 3510 and keys == expected
write_csv(AUDIT / 'relevance_pass_1.csv', FIELDS, rows)
with (AUDIT / 'relevance_pass_1.csv').open(encoding='utf-8', newline='') as f:
    delivered = list(csv.DictReader(f))
assert len(delivered) == 3510 and all(r['rationale'].strip() and r['relevance_0_4'] in '01234' for r in delivered)
report = {'stage': 'DEV_RELEVANCE_SEALED_BEFORE_TEST_INPUT_READ_AND_FACTOR_AUTHORING', 'count': len(rows), 'unique_pairs': len(keys), 'input_sha256': JSON_HASH, 'histogram': dict(sorted(Counter(r['relevance_0_4'] for r in rows).items())), 'output_raw_sha256': hashlib.sha256((AUDIT / 'relevance_pass_1.csv').read_bytes()).hexdigest()}
(HERE / 'dev_seal.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(report, ensure_ascii=False))
