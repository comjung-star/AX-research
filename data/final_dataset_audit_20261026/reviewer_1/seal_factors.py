import hashlib
import json
from collections import Counter
from expand import HERE, AUDIT, factors

# Independent relevance artifacts must already be sealed, and remain byte-identical.
for seal_name, csv_name in [('dev_seal.json', 'relevance_pass_1.csv'), ('test_seal.json', 'test_relevance_pass_1.csv')]:
    seal = json.loads((HERE / seal_name).read_text(encoding='utf-8'))
    assert seal['output_raw_sha256'] == hashlib.sha256((AUDIT / csv_name).read_bytes()).hexdigest()
rows, fingerprint = factors()
report = {'stage': 'FACTORS_SEALED_AFTER_DEV_AND_TEST_BEFORE_DISAGREEMENTS_READ', 'count': len(rows), 'unique_cases': len({r['case_id'] for r in rows}), 'input_sha256': fingerprint, 'labels': sum(r['decision'] == 'LABEL' for r in rows), 'abstentions': sum(r['decision'] == 'ABSTAIN' for r in rows), 'label_histogram': dict(sorted(Counter(label for r in rows for label in r['factor_labels'].split('|') if label).items())), 'output_raw_sha256': hashlib.sha256((AUDIT / 'factor_pass_1.csv').read_bytes()).hexdigest()}
assert report['count'] == report['unique_cases'] == 117
(HERE / 'factor_seal.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(report, ensure_ascii=False, indent=2))
