"""Serialize explicit solution-only strategy decisions and preserve prior seals."""
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
AUDIT = HERE.parent
REVIEWER = 'independent_ai_reviewer_A'
FIELDS = ['case_id', 'strategy_labels', 'decision', 'rationale', 'reviewer_id', 'input_sha256']

def verify_prior():
    seal = json.loads((HERE / 'pre_strategy_seal.json').read_text(encoding='utf-8'))
    for name, entry in seal['artifacts'].items():
        assert hashlib.sha256((AUDIT / name).read_bytes()).hexdigest() == entry['raw_output_sha256'], name
    return seal

prior = verify_prior()
raw = (AUDIT / 'strategy_blind_input.csv').read_bytes()
fingerprint = hashlib.sha256(raw).hexdigest()
assert fingerprint == '229958e97bce7d9178173d4e824acab8cbd603c737c267afe152d3dd1a456aa6'
source = list(csv.DictReader(raw.decode('utf-8-sig').splitlines()))
assert len(source) == len({r['case_id'] for r in source}) == 117
taxonomy_path = AUDIT.parent / 'v2_3' / 'strategy_taxonomy_v2_3.csv'
taxonomy_raw = taxonomy_path.read_bytes()
taxonomy = list(csv.DictReader(taxonomy_raw.decode('utf-8-sig').splitlines()))
full_ids = {int(r['strategy_id'].split('_', 1)[0][1:]): r['strategy_id'] for r in taxonomy}
assert set(full_ids) == set(range(1, 8))
rows, seen = [], set()
for line in (HERE / 'strategies.txt').read_text(encoding='utf-8').splitlines():
    if not line.strip() or line.startswith('#'):
        continue
    number, labels, reason = line.split('|', 2)
    n = int(number)
    assert 1 <= n <= 117 and n not in seen
    seen.add(n)
    ids = [full_ids[int(s)] for s in labels.split(',')] if labels != '-' else []
    assert len(ids) == len(set(ids)) and reason.strip() and '불확실성:' in reason
    rows.append(dict(zip(FIELDS, [source[n - 1]['case_id'], '|'.join(ids), 'LABEL' if ids else 'ABSTAIN', reason, REVIEWER, fingerprint])))
assert seen == set(range(1, 118)) and len(rows) == 117
path = AUDIT / 'strategy_pass_1.csv'
with path.open('w', encoding='utf-8', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=FIELDS)
    writer.writeheader()
    writer.writerows(rows)
with path.open(encoding='utf-8', newline='') as f:
    reader = csv.DictReader(f)
    assert reader.fieldnames == FIELDS
    delivered = list(reader)
assert len(delivered) == len({r['case_id'] for r in delivered}) == 117
assert {r['case_id'] for r in delivered} == {r['case_id'] for r in source}
valid = set(full_ids.values())
for r in delivered:
    assert r['reviewer_id'] == REVIEWER and r['input_sha256'] == fingerprint
    assert r['rationale'].strip() and '불확실성:' in r['rationale']
    ids = r['strategy_labels'].split('|') if r['strategy_labels'] else []
    assert len(ids) == len(set(ids)) and set(ids) <= valid
    assert (r['decision'] == 'LABEL' and ids) or (r['decision'] == 'ABSTAIN' and not ids)
verify_prior()
report = {
    'stage': 'INDEPENDENT_SOLUTION_ONLY_AI_STRATEGY_ANNOTATION_SEALED',
    'reviewer_id': REVIEWER,
    'rows': len(delivered),
    'unique_cases': len({r['case_id'] for r in delivered}),
    'input_raw_sha256': fingerprint,
    'taxonomy_raw_sha256': hashlib.sha256(taxonomy_raw).hexdigest(),
    'output_raw_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
    'decisions': dict(Counter(r['decision'] for r in delivered)),
    'abstention_case_ids': [r['case_id'] for r in delivered if r['decision'] == 'ABSTAIN'],
    'strategy_label_histogram': dict(sorted(Counter(label for r in delivered for label in r['strategy_labels'].split('|') if label).items())),
    'prior_five_artifacts_unchanged': True,
    'status': 'AI_ANNOTATION_NOT_HUMAN_GOLD_NOT_CAUSAL_CONFIRMATION_NOT_RESEARCHER_APPROVAL'
}
(HERE / 'strategy_seal.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
combined = {'prior_stages': prior, 'strategy': report}
(HERE / 'final_review_manifest.json').write_text(json.dumps(combined, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(report, ensure_ascii=False, indent=2))
